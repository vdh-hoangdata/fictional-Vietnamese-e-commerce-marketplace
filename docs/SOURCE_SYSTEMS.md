# Source ownership and transport

| Source | Tables |
|---|---|
| customer_crm | customers, customer_addresses |
| product_catalog | sellers, categories, products, product_price_history |
| ecommerce_app | orders, order_items, order_status_history, coupons, order_discounts, returns |
| payment_gateway | payments, refunds |
| warehouse_erp | warehouses, inventory_movements |
| logistics_provider | shipments, shipment_items, shipment_events |
| marketing_platform | marketing_campaigns, marketing_spend_daily |
| web_analytics | web_events (JSONL) |
| customer_support | reviews, support_tickets |

Identifiers and snake_case field names are identical across systems: no hidden
mapping is needed. CSV is UTF-8 without BOM, comma-delimited, double-quote escaped,
LF terminated, with a header. Empty CSV fields denote NULL. JSONL uses JSON null
and nested objects. UTC timestamps include Z; the marketing spend date uses the
Vietnam local calendar. SQL imports must preserve this distinction. Local time
conversion is fixed +07:00 throughout the observation period.

The reference has exactly one row per documented grain. Raw snapshots may carry
duplicate ingestion records and corrected revisions. All sources include
`_ingested_at`, `_batch_id`, `_source_version`; the batch identifies extraction,
not an event date. Event/ledger ingestion follows the business instant; mutable
snapshots are extracted at the observation boundary. Transport can continue into
January 2026 even though observed business events end in December 2025.

Files roll at `--chunk-rows` (default 100,000). The first file is `orders.csv`,
then `orders.part00002.csv`, etc. Read all parts, including the first; no date
partition pruning is implied. SMALL normally creates one file per source table.
The JSONL streams follow the same part convention. Do not concatenate CSV headers
into data rows.

`reference/canonical` is instructor material. `raw` contains the learner inputs.
`manifests/generation.json` lists SHA-256, bytes and actual row counts for each
data file. `quality_injection.json` contains aggregate trial rates and realized
counts. Exact affected keys require optional instructor ground truth.

## CDC contract

`cdc/changes*.jsonl` carries full after-images for orders, payments, shipments and
products. Each event contains change_id, table, business_key, operation,
source_version, changed_at, ingested_at, reason and payload. Key namespace is
`(table,business_key)`; revision namespace adds source_version. Event versions
are contiguous per key and authoritative over arrival order. Replays retain the
same change_id and payload but can have a later ingestion timestamp. The file
order is a bounded simulation of transport arrival, not a globally sorted
ingestion log. To model a transport clock, sort ingestion timestamps yourself.

Replay from an empty target, INSERT at version 1, then retain the highest version
per key. The resulting four tables equal the documented canonical snapshots.
History queries use changed_at and source_version, not ingestion time. Business
corrections include delayed campaign-link reconciliation. No DELETE operation is
emitted: records are retained for financial audit, and product discontinuation
is an UPDATE to is_active=0 with discontinued_at. Consumers must not interpret
that update as a physical delete. Master inserts may precede 2024, providing the
opening baseline. Updates never extend beyond the business cutoff; ingestion can.

This feed is a practice contract rather than a vendor-specific Debezium log.
