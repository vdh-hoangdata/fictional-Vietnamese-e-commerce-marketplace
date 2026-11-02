"""Business validation over canonical records; source defects are reported separately."""
import json
import sqlite3
from pathlib import Path

from src.business_rules.finance import TRANSITIONS
from src.exporters.files import read_table
from src.models.schema import NUMERIC_KINDS, TABLES
from src.utils.core import CUTOFF, checksum, json_text, parse
from src.utils.scratch import scratch_directory


CHECKS = {
    "category_hierarchy": "SELECT c.category_id FROM categories c LEFT JOIN categories p ON p.category_id=c.parent_category_id WHERE c.category_level NOT IN (1,2) OR (c.category_level=1 AND c.parent_category_id IS NOT NULL) OR (c.category_level=2 AND (p.category_id IS NULL OR p.category_level<>1))",
    "customer_address_ownership": "SELECT o.order_id FROM orders o JOIN customer_addresses a ON a.address_id=o.address_id WHERE a.customer_id<>o.customer_id",
    "default_addresses": "SELECT customer_id FROM customer_addresses GROUP BY customer_id HAVING SUM(is_default)<>1",
    "registration_chronology": "SELECT o.order_id FROM orders o JOIN customers c ON c.customer_id=o.customer_id WHERE o.ordered_at<c.registered_at OR (c.inactive_at IS NOT NULL AND o.ordered_at>=c.inactive_at)",
    "product_availability": "SELECT i.order_item_id FROM order_items i JOIN orders o USING(order_id) JOIN products p USING(product_id) WHERE o.ordered_at<p.launched_at OR (p.discontinued_at IS NOT NULL AND o.ordered_at>=p.discontinued_at) OR i.seller_id<>p.seller_id",
    "price_intervals": "SELECT price_history_id FROM (SELECT *,LAG(effective_to) OVER(PARTITION BY product_id ORDER BY effective_from) prior_end FROM product_price_history) WHERE effective_from>=effective_to OR (prior_end IS NOT NULL AND prior_end<>effective_from) OR listed_price<=0 OR promotional_price>listed_price OR promotional_price<0",
    "historical_selling_price": "SELECT i.order_item_id FROM order_items i JOIN orders o USING(order_id) LEFT JOIN product_price_history p ON p.product_id=i.product_id AND o.ordered_at>=p.effective_from AND o.ordered_at<p.effective_to GROUP BY i.order_item_id HAVING COUNT(p.price_history_id)<>1 OR MIN(COALESCE(p.promotional_price,p.listed_price))<>i.unit_price",
    "item_financials": "SELECT order_item_id FROM order_items WHERE quantity<=0 OR unit_price<0 OR item_gmv<>quantity*unit_price OR line_discount<0 OR allocated_order_discount<0 OR item_amount<>item_gmv-line_discount-allocated_order_discount OR item_amount<0",
    "order_financials": "SELECT o.order_id FROM orders o LEFT JOIN (SELECT order_id,SUM(item_gmv) g,SUM(line_discount) l,SUM(allocated_order_discount) d,SUM(item_amount) n FROM order_items GROUP BY order_id) i USING(order_id) WHERE i.g IS NULL OR o.item_gmv<>i.g OR o.line_discount<>i.l OR o.order_discount<>i.d OR o.total_payable<>i.n+o.shipping_fee OR o.currency<>'VND'",
    "discount_reconciliation": "SELECT o.order_id FROM orders o LEFT JOIN (SELECT order_id,SUM(discount_amount) d FROM order_discounts GROUP BY order_id) d USING(order_id) WHERE o.order_discount<>COALESCE(d.d,0)",
    "coupon_eligibility": "SELECT d.order_discount_id FROM order_discounts d JOIN orders o USING(order_id) JOIN coupons c USING(coupon_id) WHERE o.ordered_at<c.starts_at OR o.ordered_at>=c.ends_at OR o.item_gmv-o.line_discount<c.minimum_spend OR d.discount_amount<>MIN(c.maximum_discount,(o.item_gmv-o.line_discount)*c.discount_value/100) OR (c.category_id IS NOT NULL AND EXISTS(SELECT 1 FROM order_items i JOIN products p USING(product_id) JOIN categories k ON k.category_id=p.category_id WHERE i.order_id=o.order_id AND k.parent_category_id<>c.category_id))",
    "coupon_redemption_limit": "SELECT c.coupon_id FROM coupons c JOIN order_discounts d USING(coupon_id) GROUP BY c.coupon_id HAVING COUNT(*)>c.redemption_limit",
    "payment_reconciliation": "SELECT p.payment_id FROM payments p JOIN orders o USING(order_id) WHERE p.amount<>o.total_payable OR p.amount<0 OR (p.status='captured' AND p.captured_at IS NULL) OR (p.status<>'captured' AND p.captured_at IS NOT NULL) OR p.attempted_at<o.ordered_at OR p.captured_at<p.attempted_at OR p.authorized_at<p.attempted_at OR (p.authorized_at IS NOT NULL AND p.captured_at<p.authorized_at)",
    "unique_collected_payment": "SELECT order_id FROM payments WHERE status='captured' GROUP BY order_id HAVING COUNT(*)>1",
    "payment_attempt_sequence": "SELECT order_id FROM payments GROUP BY order_id HAVING MIN(attempt_number)<>1 OR MAX(attempt_number)<>COUNT(*) OR COUNT(DISTINCT attempt_number)<>COUNT(*)",
    "cod_settlement_chronology": "SELECT p.payment_id FROM payments p LEFT JOIN (SELECT order_id,MAX(delivered_at) d, SUM(CASE WHEN status<>'delivered' THEN 1 ELSE 0 END) unfinished FROM shipments GROUP BY order_id) s USING(order_id) WHERE p.method='cod' AND p.status='captured' AND (s.d IS NULL OR s.unfinished<>0 OR p.captured_at<=s.d)",
    "refund_limits": "SELECT p.payment_id FROM payments p JOIN refunds r USING(payment_id) GROUP BY p.payment_id HAVING p.status<>'captured' OR SUM(r.requested_amount)>p.amount OR SUM(r.refunded_amount)>p.amount",
    "refund_chronology": "SELECT r.refund_id FROM refunds r JOIN payments p USING(payment_id) WHERE r.order_id<>p.order_id OR r.requested_at<p.captured_at OR r.refunded_at<r.requested_at OR r.refunded_amount<0 OR r.refunded_amount>r.requested_amount OR (r.status='completed' AND (r.refunded_amount<>r.requested_amount OR r.refunded_at IS NULL)) OR (r.status<>'completed' AND (r.refunded_amount<>0 OR r.refunded_at IS NOT NULL))",
    "refund_return_value": "SELECT f.refund_id FROM refunds f JOIN returns r USING(return_id) JOIN order_items i USING(order_item_id) WHERE f.order_id<>r.order_id OR r.status<>'received' OR f.requested_amount<>i.item_amount*r.requested_quantity/i.quantity OR f.requested_at<r.received_at",
    "return_eligibility": "SELECT r.return_id FROM returns r JOIN order_items i USING(order_item_id) JOIN orders o ON o.order_id=r.order_id LEFT JOIN (SELECT order_id,MAX(delivered_at) delivered FROM shipments GROUP BY order_id) s ON s.order_id=o.order_id WHERE r.order_id<>i.order_id OR o.status<>'delivered' OR r.requested_quantity<=0 OR r.requested_quantity>i.quantity OR s.delivered IS NULL OR r.requested_at<s.delivered OR r.received_at<r.requested_at OR (r.status='received' AND r.received_at IS NULL)",
    "return_quantity_limits": "SELECT i.order_item_id FROM order_items i JOIN returns r USING(order_item_id) GROUP BY i.order_item_id HAVING SUM(r.requested_quantity)>i.quantity",
    "inventory_balances": "SELECT movement_id FROM (SELECT movement_id,SUM(quantity_delta) OVER(PARTITION BY product_id,warehouse_id ORDER BY event_at,movement_id ROWS UNBOUNDED PRECEDING) h,SUM(reserved_delta) OVER(PARTITION BY product_id,warehouse_id ORDER BY event_at,movement_id ROWS UNBOUNDED PRECEDING) r FROM inventory_movements) WHERE h<0 OR r<0 OR h-r<0",
    "inventory_movement_semantics": "SELECT movement_id FROM inventory_movements WHERE (movement_type IN ('receiving','return_restock') AND (quantity_delta<=0 OR reserved_delta<>0)) OR (movement_type='adjustment' AND (quantity_delta=0 OR reserved_delta<>0)) OR (movement_type='reservation' AND (quantity_delta<>0 OR reserved_delta<=0)) OR (movement_type='fulfillment' AND (quantity_delta>=0 OR quantity_delta<>reserved_delta)) OR (movement_type='cancellation_release' AND (quantity_delta<>0 OR reserved_delta>=0))",
    "inventory_item_references": "SELECT m.movement_id FROM inventory_movements m LEFT JOIN order_items i ON m.reference_id=i.order_item_id WHERE m.reference_type='order_item' AND (i.order_item_id IS NULL OR m.product_id<>i.product_id OR ABS(COALESCE(NULLIF(m.quantity_delta,0),m.reserved_delta))<>i.quantity)",
    "inventory_product_references": "SELECT m.movement_id FROM inventory_movements m LEFT JOIN products p ON p.product_id=m.reference_id WHERE m.reference_type='product' AND (p.product_id IS NULL OR m.product_id<>p.product_id)",
    "inventory_return_references": "SELECT m.movement_id FROM inventory_movements m LEFT JOIN returns r ON r.return_id=m.reference_id LEFT JOIN order_items i ON i.order_item_id=r.order_item_id WHERE m.reference_type='return' AND (r.return_id IS NULL OR i.product_id<>m.product_id OR m.quantity_delta<>r.requested_quantity OR r.status<>'received' OR m.event_at<r.received_at)",
    "inventory_warehouse_ownership": "SELECT m.movement_id FROM inventory_movements m JOIN products p USING(product_id) JOIN sellers s USING(seller_id) WHERE m.warehouse_id<>s.warehouse_id",
    "terminal_order_reservations": "SELECT i.order_item_id FROM order_items i JOIN orders o USING(order_id) JOIN inventory_movements m ON m.reference_type='order_item' AND m.reference_id=i.order_item_id WHERE o.status IN ('cancelled','payment_failed','payment_abandoned','delivered','delivery_failed') GROUP BY i.order_item_id HAVING SUM(m.reserved_delta)<>0",
    "inventory_fulfillment_reconciliation": "SELECT i.order_item_id FROM order_items i LEFT JOIN (SELECT reference_id,SUM(-quantity_delta) q FROM inventory_movements WHERE movement_type='fulfillment' GROUP BY reference_id) m ON m.reference_id=i.order_item_id LEFT JOIN shipment_items si USING(order_item_id) LEFT JOIN shipments s USING(shipment_id) WHERE COALESCE(m.q,0)<>CASE WHEN s.shipped_at IS NOT NULL THEN i.quantity ELSE 0 END",
    "shipment_chronology": "SELECT s.shipment_id FROM shipments s JOIN orders o USING(order_id) WHERE s.created_at<o.ordered_at OR s.shipped_at<s.created_at OR s.delivered_at<s.shipped_at OR s.closed_at<s.shipped_at OR (s.status='delivered' AND s.delivered_at IS NULL) OR (s.shipped_at IS NOT NULL AND s.expected_delivery_at<>strftime('%Y-%m-%dT%H:%M:%SZ',s.shipped_at,'+'||s.sla_days||' days'))",
    "shipment_item_ownership": "SELECT si.shipment_item_id FROM shipment_items si JOIN shipments s USING(shipment_id) JOIN order_items i USING(order_item_id) WHERE s.order_id<>i.order_id OR s.seller_id<>i.seller_id OR si.quantity<>i.quantity",
    "unique_shipment_assignment": "SELECT order_item_id FROM shipment_items GROUP BY order_item_id HAVING COUNT(*)<>1",
    "shipment_sequence": "SELECT shipment_id FROM shipment_events GROUP BY shipment_id HAVING MIN(event_sequence)<>1 OR MAX(event_sequence)<>COUNT(*) OR COUNT(DISTINCT event_sequence)<>COUNT(*)",
    "shipment_event_chronology": "SELECT shipment_event_id FROM (SELECT *,LAG(event_at) OVER(PARTITION BY shipment_id ORDER BY event_sequence) prior_time FROM shipment_events) WHERE event_at<prior_time",
    "campaign_dates": "SELECT campaign_id FROM marketing_campaigns WHERE starts_at>=ends_at OR budget<0",
    "campaign_spend": "SELECT d.spend_id FROM marketing_spend_daily d JOIN marketing_campaigns c USING(campaign_id) WHERE d.spend_date<date(c.starts_at,'+7 hours') OR d.spend_date>=date(c.ends_at,'+7 hours') OR d.spend_amount<0 OR d.clicks>d.impressions OR d.clicks<0 OR d.channel<>c.channel",
    "campaign_budget": "SELECT c.campaign_id FROM marketing_campaigns c JOIN marketing_spend_daily d USING(campaign_id) GROUP BY c.campaign_id HAVING SUM(d.spend_amount)>c.budget",
    "order_campaign_dates": "SELECT o.order_id FROM orders o JOIN marketing_campaigns c USING(campaign_id) WHERE o.ordered_at<c.starts_at OR o.ordered_at>=c.ends_at",
    "web_campaign_dates": "SELECT e.event_id FROM web_events e JOIN marketing_campaigns c USING(campaign_id) WHERE e.event_at<c.starts_at OR e.event_at>=c.ends_at",
    "web_registration": "SELECT e.event_id FROM web_events e JOIN customers c USING(customer_id) WHERE e.event_at<c.registered_at",
    "purchase_linkage": "SELECT e.event_id FROM web_events e LEFT JOIN orders o ON o.order_id=json_extract(e.properties,'$.order_id') WHERE e.event_type='purchase' AND (o.order_id IS NULL OR e.customer_id<>o.customer_id OR e.event_at<o.ordered_at OR json_extract(e.properties,'$.value_vnd')<>o.total_payable OR o.status IN ('payment_failed','payment_abandoned','created'))",
    "review_eligibility": "SELECT r.review_id FROM reviews r JOIN order_items i USING(order_item_id) JOIN orders o USING(order_id) LEFT JOIN (SELECT order_id,MAX(delivered_at) delivered FROM shipments GROUP BY order_id) s USING(order_id) WHERE r.product_id<>i.product_id OR r.customer_id<>o.customer_id OR o.status<>'delivered' OR s.delivered IS NULL OR r.reviewed_at<s.delivered OR r.rating NOT BETWEEN 1 AND 5",
    "support_chronology": "SELECT t.ticket_id FROM support_tickets t JOIN customers c USING(customer_id) LEFT JOIN orders o USING(order_id) WHERE t.created_at<c.registered_at OR (t.order_id IS NOT NULL AND (o.customer_id<>t.customer_id OR t.created_at<o.ordered_at)) OR t.first_response_at<t.created_at OR t.resolved_at<t.first_response_at OR (t.status='resolved' AND t.resolved_at IS NULL)",
    "order_status_snapshot": "SELECT o.order_id FROM orders o LEFT JOIN (SELECT order_id,new_status,ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY event_at DESC,status_event_id DESC) n FROM order_status_history) h ON h.order_id=o.order_id AND h.n=1 WHERE h.new_status IS NULL OR o.status<>h.new_status",
    "status_history_chain": "SELECT status_event_id FROM (SELECT *,LAG(new_status) OVER(PARTITION BY order_id ORDER BY event_at,status_event_id) actual_previous FROM order_status_history) WHERE previous_status IS NOT actual_previous",
}


def load_database(db, folder, errors):
    for name, table in TABLES.items():
        fields = ",".join(f'"{c.name}" {"INTEGER" if c.kind in NUMERIC_KINDS else "TEXT"}' for c in table.columns)
        db.execute(f'CREATE TABLE "{name}" ({fields})')
        batch = []
        for row in read_table(folder, name):
            values = []
            for column in table.columns:
                value = row[column.name]
                if value is None and not column.nullable:
                    errors.append(dict(check=f"required:{name}.{column.name}", sample=row[table.pk]))
                if value is not None and column.kind == "timestamp":
                    parsed = parse(value)
                    if parsed.utcoffset().total_seconds() != 0:
                        errors.append(dict(check=f"utc:{name}.{column.name}", sample=row[table.pk]))
                    # Validity boundaries and SLA promises are allowed after cutoff.
                    if column.name not in {"effective_to", "ends_at", "expected_delivery_at"} and parsed > CUTOFF:
                        errors.append(dict(check=f"cutoff:{name}.{column.name}", sample=row[table.pk]))
                values.append(json_text(value) if isinstance(value, (dict, list)) else value)
            batch.append(values)
            if len(batch) >= 2000:
                db.executemany(f'INSERT INTO "{name}" VALUES ({",".join("?" for _ in table.columns)})', batch)
                batch.clear()
        if batch:
            db.executemany(f'INSERT INTO "{name}" VALUES ({",".join("?" for _ in table.columns)})', batch)
        indexed = {table.pk} | {c.name for c in table.columns if c.foreign_key}
        for field in indexed:
            db.execute(f'CREATE INDEX "idx_{name}_{field}" ON "{name}"("{field}")')
    db.commit()


def run_sql_checks(db, errors):
    results = {}
    queries = dict(CHECKS)
    for name, table in TABLES.items():
        queries[f"primary_key:{name}"] = f'SELECT "{table.pk}" FROM "{name}" GROUP BY "{table.pk}" HAVING COUNT(*)<>1'
        for column in table.columns:
            if column.foreign_key:
                target, key = column.foreign_key.split(".")
                queries[f"foreign_key:{name}.{column.name}"] = f'SELECT s."{table.pk}" FROM "{name}" s LEFT JOIN "{target}" t ON s."{column.name}"=t."{key}" WHERE s."{column.name}" IS NOT NULL AND t."{key}" IS NULL'
    allowed = " OR ".join(f"(previous_status {'IS NULL' if previous is None else '=' + repr(previous)} AND new_status IN ({','.join(repr(v) for v in sorted(values))}))" for previous, values in TRANSITIONS.items())
    queries["lifecycle_transitions"] = f"SELECT status_event_id FROM order_status_history WHERE NOT ({allowed})"
    for name, query in queries.items():
        count = 0
        samples = []
        for row in db.execute(query):
            count += 1
            if len(samples) < 5:
                samples.append(row[0])
        results[name] = count
        if count:
            errors.append(dict(check=name, violations=count, samples=samples))
    return results


def replay_cdc(db, root, errors):
    db.execute("CREATE TABLE cdc_latest(table_name TEXT,business_key INTEGER,version INTEGER,payload TEXT,PRIMARY KEY(table_name,business_key))")
    db.execute("CREATE TABLE cdc_versions(table_name TEXT,business_key INTEGER,version INTEGER,changed_at TEXT,payload TEXT,PRIMARY KEY(table_name,business_key,version))")
    count, replayed = 0, 0
    for path in sorted((root / "cdc").glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                count += 1
                table, key, version = event["table"], event["business_key"], event["source_version"]
                payload = json_text(event["payload"])
                if table not in {"orders", "payments", "shipments", "products"} or event["operation"] not in {"INSERT", "UPDATE"}:
                    errors.append(dict(check="cdc_contract", sample=event["change_id"]))
                    continue
                if event["operation"] != ("INSERT" if version == 1 else "UPDATE") or parse(event["ingested_at"]) < parse(event["changed_at"]):
                    errors.append(dict(check="cdc_sequence_or_ingestion", sample=event["change_id"]))
                if table == "payments":
                    image = event["payload"]
                    if (image["status"] == "authorized" and not image["authorized_at"]) or (image["status"] == "captured" and not image["captured_at"]) or any(image[field] and image[field] > event["changed_at"] for field in ("authorized_at", "captured_at")):
                        errors.append(dict(check="cdc_payment_state_chronology", sample=event["change_id"]))
                old = db.execute("SELECT payload FROM cdc_versions WHERE table_name=? AND business_key=? AND version=?", (table, key, version)).fetchone()
                if old:
                    replayed += 1
                    if old[0] != payload:
                        errors.append(dict(check="cdc_conflicting_replay", sample=event["change_id"]))
                else:
                    db.execute("INSERT INTO cdc_versions VALUES(?,?,?,?,?)", (table, key, version, event["changed_at"], payload))
                db.execute("INSERT INTO cdc_latest VALUES(?,?,?,?) ON CONFLICT(table_name,business_key) DO UPDATE SET version=excluded.version,payload=excluded.payload WHERE excluded.version>version", (table, key, version, payload))
    for table in ("orders", "payments", "shipments", "products"):
        for row in read_table(root / "reference" / "canonical", table):
            stored = db.execute("SELECT payload FROM cdc_latest WHERE table_name=? AND business_key=?", (table, row[TABLES[table].pk])).fetchone()
            if not stored or stored[0] != json_text(row):
                errors.append(dict(check="cdc_target_snapshot", table=table, sample=row[TABLES[table].pk]))
    bad = db.execute("SELECT table_name,business_key FROM cdc_versions GROUP BY table_name,business_key HAVING MIN(version)<>1 OR MAX(version)<>COUNT(*)").fetchall()
    if bad:
        errors.append(dict(check="cdc_version_gaps", violations=len(bad), samples=bad[:5]))
    chronology = db.execute("SELECT COUNT(*) FROM (SELECT changed_at,LAG(changed_at) OVER(PARTITION BY table_name,business_key ORDER BY version) prior FROM cdc_versions) WHERE changed_at<prior").fetchone()[0]
    if chronology:
        errors.append(dict(check="cdc_business_chronology", violations=chronology))
    return dict(events=count, identical_replays=replayed, reconstructed_keys=db.execute("SELECT COUNT(*) FROM cdc_latest").fetchone()[0])


def distributions(db):
    def rows(query):
        return [list(row) for row in db.execute(query)]
    return dict(
        monthly_orders=rows("SELECT strftime('%Y-%m',ordered_at,'+7 hours'),COUNT(*) FROM orders GROUP BY 1"),
        order_statuses=rows("SELECT status,COUNT(*) FROM orders GROUP BY status"),
        repeat_customers=db.execute("SELECT COUNT(*) FROM (SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*)>1)").fetchone()[0],
        customers_with_one_order=db.execute("SELECT COUNT(*) FROM (SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*)=1)").fetchone()[0],
        top_product_units=rows("SELECT product_id,SUM(quantity) n FROM order_items GROUP BY product_id ORDER BY n DESC LIMIT 10"),
        failed_payment_attempts=db.execute("SELECT COUNT(*) FROM payments WHERE status='failed'").fetchone()[0],
        late_deliveries=db.execute("SELECT COUNT(*) FROM shipments WHERE delivered_at>expected_delivery_at").fetchone()[0],
        partial_returns=db.execute("SELECT COUNT(*) FROM returns r JOIN order_items i USING(order_item_id) WHERE r.requested_quantity<i.quantity").fetchone()[0],
        unattributed_orders=db.execute("SELECT COUNT(*) FROM orders WHERE campaign_id IS NULL").fetchone()[0],
        anonymous_events=db.execute("SELECT COUNT(*) FROM web_events WHERE customer_id IS NULL").fetchone()[0],
        campaign_daily_orders=rows("SELECT date(ordered_at,'+7 hours'),COUNT(*),SUM(CASE WHEN campaign_id IS NOT NULL THEN 1 ELSE 0 END) FROM orders GROUP BY 1"),
    )


def validate_dataset(root, check_files=True):
    root = Path(root)
    errors, results = [], {}
    manifest = json.loads((root / "manifests" / "generation.json").read_text(encoding="utf-8"))
    quality = json.loads((root / "manifests" / "quality_injection.json").read_text(encoding="utf-8"))
    if check_files:
        for item in manifest["files"]:
            path = root / item["path"]
            if not path.exists() or path.stat().st_size != item["bytes"] or checksum(path) != item["sha256"]:
                errors.append(dict(check="manifest_checksum", file=item["path"]))
    if not (root / "reference" / "canonical").is_dir():
        return dict(ok=False, generator_errors=errors, full_validation_available=False,
                    limitation="Canonical reference omitted; only checksums were checked, business correctness is unverified.",
                    intended_source_conditions=quality)
    # Keep the scratch DB inside the explicitly writable dataset destination.
    with scratch_directory(root, prefix=".validation-") as temporary:
        db = sqlite3.connect(str(Path(temporary) / "checks.sqlite"))
        try:
            db.execute("PRAGMA journal_mode=OFF")
            db.execute("PRAGMA synchronous=OFF")
            db.execute("PRAGMA cache_size=-32000")
            db.execute("PRAGMA temp_store=FILE")
            load_database(db, root / "reference" / "canonical", errors)
            results = run_sql_checks(db, errors)
            actual = {name: db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in TABLES}
            if actual != manifest["canonical_rows"]:
                errors.append(dict(check="manifest_row_counts", actual=actual))
            cdc = replay_cdc(db, root, errors)
            distribution = distributions(db)
        finally:
            db.close()
    return dict(ok=not errors, full_validation_available=True, generator_errors=errors,
                business_checks=results, canonical_rows=actual, cdc=cdc, distributions=distribution,
                intended_source_conditions=quality,
                sql_server="DDL and checks supplied; no SQL Server execution performed")
