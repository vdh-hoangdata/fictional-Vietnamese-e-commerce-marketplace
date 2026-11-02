from collections import Counter
from datetime import timedelta

from src.exporters.files import ChunkWriter, read_table
from src.models.schema import TABLES
from src.utils.core import END, json_text, parse, rng, stamp

BASE_RATES = {
    "missing_optional": 0.015, "duplicate_ingestion": 0.008,
    "text_formatting": 0.015, "delayed_ingestion": 0.015,
    "malformed_attribute": 0.002, "status_mismatch": 0.004,
    "missing_attribution": 0.04, "string_numeric_json": 0.015,
    "corrected_record": 0.006,
}
METADATA = ["_ingested_at", "_batch_id", "_source_version"]


def export_sources(root, settings):
    multiplier = {"clean": 0, "realistic": 1, "challenging": 3}[settings.profile]
    rates = {key: min(0.5, value * multiplier) for key, value in BASE_RATES.items()}
    truth = ChunkWriter(root / "instructor", "anomaly_ground_truth", jsonl=True,
                        chunk_rows=settings.chunk_rows) if settings.keep_ground_truth else None
    counts, raw_counts = Counter(), {}
    for name, table in TABLES.items():
        random = rng(settings.seed, f"source:{name}")
        writer = ChunkWriter(root / "raw" / table.source, name,
                             [c.name for c in table.columns] + METADATA, settings.chunk_rows, name == "web_events")
        buffer = []
        for index, canonical in enumerate(read_table(root / "reference" / "canonical", name)):
            row, issues = dict(canonical), []
            anchor = parse(row.get("event_at")) if name in {"web_events", "shipment_events", "order_status_history", "inventory_movements"} else END
            ingested = anchor + timedelta(seconds=random.randint(30, 3600))
            if random.random() < rates["delayed_ingestion"]:
                ingested += timedelta(days=random.randint(2, 7))
                issues.append("delayed_ingestion")
            row.update(_ingested_at=stamp(ingested), _batch_id=f"{table.source}:20260101:{index // settings.chunk_rows + 1:05d}", _source_version=1)
            optional = [c.name for c in table.columns if c.nullable and c.kind in {"text", "json"} and row[c.name] is not None]
            if optional and random.random() < rates["missing_optional"]:
                row[random.choice(optional)] = None
                issues.append("missing_optional")
            text = [c.name for c in table.columns if c.kind == "text" and row[c.name] and c.name not in {"session_id", "anonymous_visitor_id"}]
            if text and random.random() < rates["text_formatting"]:
                key = random.choice(text)
                row[key] = f" {row[key].upper()} "
                issues.append("text_formatting")
            numeric = [c.name for c in table.columns if c.kind in {"money", "int"} and row[c.name] is not None]
            if numeric and random.random() < rates["malformed_attribute"]:
                row[random.choice(numeric)] = "not_available"
                issues.append("malformed_attribute")
            if name in {"orders", "shipments"} and random.random() < rates["status_mismatch"]:
                row["status"] = "processing" if name == "orders" else "in_transit"
                issues.append("status_mismatch")
            if row.get("campaign_id") is not None and random.random() < rates["missing_attribution"]:
                row["campaign_id"] = None
                issues.append("missing_attribution")
            if name == "web_events" and random.random() < rates["string_numeric_json"]:
                row["properties"] = dict(row["properties"], instrumentation_latency_ms="125")
                issues.append("string_numeric_json")
            correction = random.random() < rates["corrected_record"] and bool(text)
            if correction:
                row[text[0]] = "UNKNOWN_SOURCE_VALUE"
                issues.append("corrected_record")
            buffer.append(row)
            if random.random() < rates["duplicate_ingestion"]:
                buffer.append(dict(row))
                issues.append("duplicate_ingestion")
            if correction:
                fixed = dict(canonical, _ingested_at=stamp(ingested + timedelta(days=8)),
                             _batch_id=row["_batch_id"], _source_version=2)
                buffer.append(fixed)
            for issue in issues:
                counts[f"{name}.{issue}"] += 1
                if truth:
                    truth.write(dict(table=name, business_key=canonical[table.pk], issue=issue,
                                     original=canonical, source_version=1))
            if len(buffer) >= 64:
                if multiplier:
                    random.shuffle(buffer)
                for buffered in buffer:
                    writer.write(buffered)
                buffer.clear()
        if multiplier:
            random.shuffle(buffer)
        for buffered in buffer:
            writer.write(buffered)
        writer.close()
        raw_counts[name] = writer.total
    if truth:
        truth.close()
    manifest = dict(profile=settings.profile, selection_rates=rates, applied_counts=dict(sorted(counts.items())),
                    notes="Rates are independent eligible-row trials; null optional fields are not intrinsically defects. "
                          "Clean retains ordinary late business processes. Non-clean arrivals shuffle within 64-row buffers. "
                          "No primary/foreign business key is replaced. Nullable attribution may be absent.")
    (root / "manifests" / "quality_injection.json").write_text(json_text(manifest) + "\n", encoding="utf-8")
    return raw_counts
