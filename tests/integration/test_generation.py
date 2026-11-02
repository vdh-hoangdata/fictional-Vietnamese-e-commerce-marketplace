import json
from pathlib import Path
import pytest

from src.config.settings import Settings
from src.anomaly_injection.export import METADATA
from src.exporters.files import file_manifest, read_table, table_files
from src.generators.project import generate
from src.models.schema import TABLES
from src.utils.core import checksum
from src.validators.checks import validate_dataset


def test_successful_end_to_end(report):
    assert report["ok"], report["generator_errors"]
    assert len(report["business_checks"]) >= 100
    assert report["canonical_rows"]["orders"] == 900


def test_deterministic_data_and_domain_separation(work_dir):
    scale = dict(orders=100, customers=30, products=24, sellers=6)
    outputs = []
    for suffix, profile in [("a", "realistic"), ("b", "realistic"), ("c", "challenging")]:
        folder = work_dir / suffix
        manifest = generate(Settings(output=folder, seed=17, size="small", profile=profile, scale=scale), progress=lambda _: None)
        outputs.append((folder, manifest))
    assert outputs[0][1] == outputs[1][1]
    for name in TABLES:
        left = table_files(outputs[0][0] / "reference" / "canonical", name)
        right = table_files(outputs[2][0] / "reference" / "canonical", name)
        assert [checksum(p) for p in left] == [checksum(p) for p in right]
    assert validate_dataset(outputs[0][0])["ok"]


def test_never_overwrites_existing_data(dataset):
    with pytest.raises(FileExistsError):
        generate(Settings(output=dataset), progress=lambda _: None)


def test_business_primary_keys(dataset):
    for name, table in TABLES.items():
        keys = [row[table.pk] for row in read_table(dataset / "reference" / "canonical", name)]
        assert len(keys) == len(set(keys)), name


def test_all_relationships_and_chronology(report):
    checks = report["business_checks"]
    names = [key for key in checks if key.startswith("foreign_key:") or "chronology" in key]
    assert len(names) > 30
    assert all(checks[name] == 0 for name in names)


def test_historical_prices_and_product_availability(report):
    assert report["business_checks"]["historical_selling_price"] == 0
    assert report["business_checks"]["price_intervals"] == 0
    assert report["business_checks"]["product_availability"] == 0


def test_lifecycles_and_cutoff(report):
    assert report["business_checks"]["lifecycle_transitions"] == 0
    assert report["business_checks"]["status_history_chain"] == 0
    assert report["business_checks"]["order_status_snapshot"] == 0


def test_inventory_balances_and_fulfillment(report):
    assert report["business_checks"]["inventory_balances"] == 0
    assert report["business_checks"]["inventory_movement_semantics"] == 0
    assert report["business_checks"]["inventory_fulfillment_reconciliation"] == 0
    for name in ("inventory_product_references", "inventory_return_references", "inventory_warehouse_ownership", "terminal_order_reservations"):
        assert report["business_checks"][name] == 0


def test_shipments_and_tracking(report):
    for name in ("shipment_chronology", "shipment_item_ownership", "shipment_sequence", "shipment_event_chronology"):
        assert report["business_checks"][name] == 0


def test_campaigns_and_review_eligibility(report):
    for name in ("campaign_dates", "campaign_spend", "campaign_budget", "order_campaign_dates", "web_campaign_dates", "review_eligibility", "registration_chronology"):
        assert report["business_checks"][name] == 0


def test_cdc_reconstructs_all_targets_despite_replays(report):
    cdc = report["cdc"]
    expected = sum(report["canonical_rows"][table] for table in ("orders", "payments", "shipments", "products"))
    assert cdc["reconstructed_keys"] == expected
    assert cdc["identical_replays"] > 0
    assert cdc["events"] > expected * 2


def test_cdc_intermediate_payment_states_are_temporal(dataset):
    pending, authorized, captured = 0, 0, 0
    for file in (dataset / "cdc").glob("*.jsonl"):
        with file.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event["table"] != "payments":
                    continue
                row = event["payload"]
                if event["source_version"] == 1 and row["method"] != "cod":
                    pending += 1
                    assert row["status"] == "pending"
                    assert row["authorized_at"] is None and row["captured_at"] is None
                if row["status"] == "authorized":
                    authorized += 1
                    assert row["authorized_at"] <= event["changed_at"]
                if row["status"] == "captured":
                    captured += 1
                    assert row["captured_at"] <= event["changed_at"]
    assert pending and authorized and captured


def test_manifest_hashes_and_actual_row_counts(dataset):
    manifest = json.loads((dataset / "manifests" / "generation.json").read_text(encoding="utf-8"))
    assert manifest["files"] == file_manifest(dataset)
    for name in TABLES:
        assert sum(1 for _ in read_table(dataset / "reference" / "canonical", name)) == manifest["canonical_rows"][name]


def test_chunked_large_facts(dataset):
    files = table_files(dataset / "reference" / "canonical", "web_events")
    assert len(files) > 1
    assert all(sum(1 for _ in p.open(encoding="utf-8")) <= 400 for p in files)


def test_controlled_anomalies_are_source_only(dataset, report):
    conditions = report["intended_source_conditions"]["applied_counts"]
    assert sum(conditions.values()) > 0
    manifest = json.loads((dataset / "manifests" / "generation.json").read_text(encoding="utf-8"))
    assert manifest["raw_rows"]["orders"] > manifest["canonical_rows"]["orders"]
    for file in (dataset / "raw").rglob("*.csv"):
        name = file.name.split(".")[0]
        with file.open(encoding="utf-8") as handle:
            assert set(handle.readline().strip().split(",")) == {c.name for c in TABLES[name].columns} | set(METADATA)
    assert (dataset / "instructor" / "anomaly_ground_truth.jsonl").exists()
    assert report["generator_errors"] == []


def test_clean_profile_and_optional_reference(work_dir):
    folder = work_dir / "clean"
    result = generate(Settings(output=folder, profile="clean", omit_reference=True,
                              scale=dict(orders=50, customers=20, products=18, sellers=6)), progress=lambda _: None)
    quality = json.loads((folder / "manifests" / "quality_injection.json").read_text())
    assert quality["applied_counts"] == {}
    assert result["raw_rows"] == result["canonical_rows"]
    assert not (folder / "reference" / "canonical").exists()
    assert not (folder / "instructor").exists()
    assert not validate_dataset(folder)["full_validation_available"]


def test_business_distributions_enable_analysis(report, database):
    d = report["distributions"]
    assert len(d["monthly_orders"]) == 24
    assert max(v for _, v in d["monthly_orders"]) > min(v for _, v in d["monthly_orders"]) * 1.5
    assert d["repeat_customers"] > 0 and d["customers_with_one_order"] > 0
    assert d["partial_returns"] > 0 and d["late_deliveries"] > 0
    assert d["failed_payment_attempts"] > 0 and d["anonymous_events"] > 0
    counts = [r[0] for r in database.execute("SELECT COUNT(*) n FROM orders GROUP BY customer_id ORDER BY n DESC")]
    assert sum(counts[:max(1, len(counts)//5)]) > .4 * sum(counts)
    assert d["top_product_units"][0][1] > database.execute("SELECT SUM(quantity)*1.0/COUNT(DISTINCT product_id) FROM order_items").fetchone()[0] * 3


def test_instructor_incidents_have_cross_domain_effects(dataset, database):
    notes = json.loads((dataset / "instructor" / "incidents.json").read_text())
    assert len(notes["periods"]) == 5
    assert database.execute("SELECT COUNT(*) FROM returns WHERE reason='quality'").fetchone()[0] > 0
    assert database.execute("SELECT COUNT(*) FROM support_tickets WHERE issue_category='delivery_delay'").fetchone()[0] > 0


def test_supplier_shortage_propagates_to_ledger_and_orders(work_dir):
    settings = Settings(output=work_dir / "supplier-hold", profile="clean",
                        scale=dict(orders=120, customers=30, products=24, sellers=6))
    # Extend exposure in this focused test; the standard 14-day incident may have
    # zero observations in a tiny test sample. Business rules stay identical.
    settings.incidents["inventory_shortage"] = ["2024-01-01", "2025-12-30"]
    generate(settings, progress=lambda _: None)
    ledger = list(read_table(settings.output / "reference" / "canonical", "inventory_movements"))
    statuses = list(read_table(settings.output / "reference" / "canonical", "order_status_history"))
    assert any(r["reason"] == "supplier_hold_quarantine" and r["quantity_delta"] < 0 for r in ledger)
    assert any(r["reason"] == "supplier_hold_released" and r["quantity_delta"] > 0 for r in ledger)
    assert any(r["change_reason"] == "inventory_shortage" and r["new_status"] == "cancelled" for r in statuses)
    assert validate_dataset(settings.output)["ok"]


def test_schema_artifacts_cover_all_tables():
    schema = json.loads(Path("configs/schema.json").read_text(encoding="utf-8"))
    assert set(schema) == set(TABLES)
    ddl = Path("sql/02_create_tables.sql").read_text()
    assert ddl.count("CREATE TABLE dbo.") == len(TABLES)
    assert "DATETIME2(0)" in ddl and "NVARCHAR(MAX)" in ddl
    assert "AUTO_INCREMENT" not in ddl and "DOUBLE PRECISION" not in ddl


def test_sql_fk_targets_and_initialization_order():
    constraints = Path("sql/03_constraints_indexes.sql").read_text()
    for table in TABLES.values():
        for column in table.columns:
            if column.foreign_key:
                target, field = column.foreign_key.split(".")
                assert field in {c.name for c in TABLES[target].columns}
                assert f"REFERENCES dbo.[{target}]([{field}])" in constraints
    assert "WHERE status=N'captured'" in constraints
    assert "UX_spend_campaign_day" in constraints
    staging = Path("sql/04_staging_tables.sql").read_text()
    assert staging.count("CREATE TABLE staging.") == len(TABLES)
    assert "SYSUTCDATETIME()" in staging
