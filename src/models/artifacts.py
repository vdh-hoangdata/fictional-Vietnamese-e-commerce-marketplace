"""Generate reviewable schema artifacts from the same field contract as the data."""
from dataclasses import asdict
from pathlib import Path

from src.exporters.files import read_table
from src.models.schema import TABLES
from src.utils.core import json_text


def write_schema_artifacts(project, sample=None):
    project = Path(project)
    docs, sql = project / "docs", project / "sql"
    docs.mkdir(exist_ok=True)
    sql.mkdir(exist_ok=True)
    dictionary = ["# Data dictionary", "", "Generated from `src/models/schema.py`. All IDs are positive integer business keys.",
                  "Money uses integer VND, with zero allowed. Timestamp fields are UTC ISO-8601 at second precision;",
                  "dates explicitly called reporting dates use Vietnam local time. Empty CSV fields mean SQL NULL.",
                  "JSON properties remain nested in JSONL and are JSON text in CSV/SQL. Source metadata is described below.", ""]
    erd = ["# Entity relationships", "", "Each section of the dictionary states the grain. Solid mandatory FK references have",
           "one parent; nullable FK columns have zero or one parent. Parent-to-child counts are 0..N",
           "unless the business rules constrain them (one default address; at most one captured payment).", "", "```mermaid", "erDiagram"]
    ddl = ["-- SQL Server 2017+; run 01 first, then select VietCommerce. No server connection is made by Python.", "USE [VietCommerce];", "GO"]
    staging = ["USE [VietCommerce];", "GO", "IF SCHEMA_ID('staging') IS NULL EXEC('CREATE SCHEMA staging');", "GO"]
    constraints = ["USE [VietCommerce];", "GO"]
    registry = {}
    for name, table in TABLES.items():
        first = next(read_table(sample, name), {}) if sample else {}
        dictionary += [f"## {name}", "", f"Grain: {table.grain}. Source: `{table.source}`. Primary key: `{table.pk}`.", "",
                       "| Column | SQL type | Nullable | Key | Meaning / constraints | Example | Unit / time |",
                       "|---|---|---|---|---|---|---|"]
        sql_fields, staging_fields = [], []
        erd.append(f"    {name} {{")
        for column in table.columns:
            key = "PK" if column.name == table.pk else (f"FK {column.foreign_key}" if column.foreign_key else "—")
            example = first.get(column.name)
            if isinstance(example, (dict, list)):
                example = json_text(example)
            if example is None:
                example = "NULL" if column.nullable else {"timestamp": "2024-01-01T00:00:00Z", "date": "2024-01-01", "text": "synthetic", "long": "synthetic", "json": "{}"}.get(column.kind, 1)
            unit = "VND" if column.kind == "money" else "UTC" if column.kind == "timestamp" else "VN date" if column.kind == "date" else "units" if column.name in {"quantity", "quantity_delta", "reserved_delta", "requested_quantity"} else "—"
            meaning = column.meaning + ("; required" if not column.nullable else "; NULL is permitted")
            dictionary.append(f"| {column.name} | {column.sql_type} | {'yes' if column.nullable else 'no'} | {key} | {meaning} | `{str(example).replace('|', '/').replace('`', '')}` | {unit} |")
            sql_fields.append(f"    [{column.name}] {column.sql_type} {'NULL' if column.nullable else 'NOT NULL'}")
            staging_fields.append(f"    [{column.name}] NVARCHAR(MAX) NULL")
            erd.append(f"        {column.kind} {column.name}{' PK' if key == 'PK' else ' FK' if column.foreign_key else ''}")
            if column.foreign_key:
                parent, target = column.foreign_key.split(".")
                constraints.append(f"ALTER TABLE dbo.[{name}] ADD CONSTRAINT [FK_{name}_{column.name}] FOREIGN KEY ([{column.name}]) REFERENCES dbo.[{parent}]([{target}]);")
                constraints.append(f"CREATE NONCLUSTERED INDEX [IX_{name}_{column.name}] ON dbo.[{name}]([{column.name}]);")
        erd.append("    }")
        for column in table.columns:
            if column.foreign_key:
                parent = column.foreign_key.split(".")[0]
                erd.append(f'    {parent} {"|o" if column.nullable else "||"}--o{{ {name} : "{column.name}"')
        sql_fields.append(f"    CONSTRAINT [PK_{name}] PRIMARY KEY CLUSTERED ([{table.pk}])")
        ddl.append(f"CREATE TABLE dbo.[{name}] (\n" + ",\n".join(sql_fields) + "\n);\nGO")
        staging_fields += [f"    [{field}] NVARCHAR(MAX) NULL" for field in ("_ingested_at", "_batch_id", "_source_version")]
        staging_fields += ["    [staging_row_id] BIGINT IDENTITY(1,1) NOT NULL", "    [loaded_at] DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME()"]
        staging.append(f"CREATE TABLE staging.[{name}] (\n" + ",\n".join(staging_fields) + "\n);\nGO")
        registry[name] = dict(source=table.source, grain=table.grain, primary_key=table.pk, columns=[asdict(c) for c in table.columns])
        dictionary.append("")
    dictionary += ["## Source envelope", "", "Every raw record also carries `_ingested_at` (UTC ingestion timestamp), `_batch_id` (source extraction identifier),",
                   "and `_source_version` (integer record revision, 1 initially, 2 for a corrected snapshot).",
                   "These fields are transport metadata, not business keys. Staging permits duplicate business keys.",
                   "A correction outranks the original by source version; duplicate transport records can repeat the same version.",
                   "Different null encodings are not injected; all CSV sources consistently use an empty field.", "",
                   "| Column (all raw tables) | Type | Nullable | Meaning / constraint | Example | Unit | Key | Source |",
                   "|---|---|---|---|---|---|---|---|",
                   "| _ingested_at | DATETIME2(0) | no | Transport receipt; can follow the business cutoff | 2026-01-01T02:00:00Z | UTC | none | owning system |",
                   "| _batch_id | NVARCHAR(200) | no | Extraction identifier; not a business-event date | ecommerce_app:20260101:00001 | none | none | owning system |",
                   "| _source_version | INT | no | Positive snapshot revision; highest version wins | 1 | revision | part of revision identity | owning system |", "",
                   "## Nested JSON contract", "", "Product attributes have required synthetic string keys model, color and size; examples are S1, blue and M.",
                   "The web_analytics properties object has the following conditional fields. Fields not applicable to an event are absent, not zero.", "",
                   "| Path within properties | Type | Presence | Meaning / constraint | Example | Unit / key |",
                   "|---|---|---|---|---|---|",
                   "| page.path | string | every event | Synthetic navigation path | /checkout | none |",
                   "| context.locale | string | every event | vi-VN locale | vi-VN | none |",
                   "| context.currency | string | every event | Reporting currency | VND | currency |",
                   "| query | string | search | Synthetic search phrase | ao | none |",
                   "| quantity | integer | add_to_cart/remove_from_cart | Instrumented cart units, positive | 1 | units |",
                   "| order_id | BIGINT | purchase | Required real order reference; event customer must match | 1 | FK orders.order_id |",
                   "| value_vnd | BIGINT | purchase | Order total payable, including shipping | 300000 | VND |",
                   "| instrumentation_latency_ms | string numeric | optional raw anomaly | Illustrative inconsistent numeric encoding | 125 | milliseconds |", ""]
    erd += ["```", "", "`inventory_movements.reference_id` is a documented polymorphic reference to products, order_items or returns.",
            "`web_events.properties.order_id` is a semi-structured purchase reference, validated separately."]
    constraints += ["CREATE NONCLUSTERED INDEX IX_orders_ordered_at ON dbo.orders(ordered_at) INCLUDE(customer_id,status,total_payable);",
                    "CREATE NONCLUSTERED INDEX IX_inventory_time ON dbo.inventory_movements(product_id,warehouse_id,event_at,movement_id);",
                    "CREATE NONCLUSTERED INDEX IX_price_interval ON dbo.product_price_history(product_id,effective_from,effective_to);",
                    "CREATE UNIQUE INDEX UX_payment_attempt ON dbo.payments(order_id,attempt_number);",
                    "CREATE UNIQUE INDEX UX_captured_order ON dbo.payments(order_id) WHERE status=N'captured';",
                    "CREATE UNIQUE INDEX UX_spend_campaign_day ON dbo.marketing_spend_daily(campaign_id,spend_date);",
                    "CREATE UNIQUE INDEX UX_product_price_start ON dbo.product_price_history(product_id,effective_from);",
                    "CREATE UNIQUE INDEX UX_customer_default_address ON dbo.customer_addresses(customer_id) WHERE is_default=1;",
                    "CREATE UNIQUE INDEX UX_order_sku ON dbo.order_items(order_id,product_id);",
                    "CREATE UNIQUE INDEX UX_parcel_item_assignment ON dbo.shipment_items(order_item_id);",
                    "CREATE UNIQUE INDEX UX_return_line ON dbo.[returns](order_item_id);",
                    "CREATE UNIQUE INDEX UX_review_line ON dbo.reviews(order_item_id);",
                    "ALTER TABLE dbo.order_items ADD CONSTRAINT CK_order_item_money CHECK(quantity>0 AND item_gmv=quantity*unit_price AND item_amount=item_gmv-line_discount-allocated_order_discount AND item_amount>=0);",
                    "ALTER TABLE dbo.orders ADD CONSTRAINT CK_order_total CHECK(total_payable=item_gmv-line_discount-order_discount+shipping_fee AND currency=N'VND');",
                    "ALTER TABLE dbo.refunds ADD CONSTRAINT CK_refund_amount CHECK(refunded_amount>=0 AND refunded_amount<=requested_amount);",
                    "ALTER TABLE dbo.reviews ADD CONSTRAINT CK_review_rating CHECK(rating BETWEEN 1 AND 5);"]
    (docs / "DATA_DICTIONARY.md").write_text("\n".join(dictionary), encoding="utf-8")
    (docs / "ERD.md").write_text("\n".join(erd), encoding="utf-8")
    (project / "configs" / "schema.json").write_text(json_text(registry) + "\n", encoding="utf-8")
    (sql / "02_create_tables.sql").write_text("\n".join(ddl) + "\n", encoding="utf-8")
    (sql / "03_constraints_indexes.sql").write_text("\n".join(constraints) + "\n", encoding="utf-8")
    (sql / "04_staging_tables.sql").write_text("\n".join(staging) + "\n", encoding="utf-8")
