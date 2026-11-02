import json
import shutil
from dataclasses import asdict
from pathlib import Path

from src.anomaly_injection.export import export_sources
from src.exporters.cdc import CDCWriter
from src.exporters.files import CanonicalSink, file_manifest
from src.generators.simulation import Simulation
from src.utils.core import CUTOFF, json_text, stamp


def generate(settings, progress=print):
    settings.validate()
    root = Path(settings.output).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise FileExistsError(f"Refusing to overwrite nonempty destination: {root}. Choose a new --output path.")
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifests").mkdir()
    incomplete = root / "GENERATION_INCOMPLETE"
    incomplete.write_text("Do not use until generation.json is complete.\n", encoding="utf-8")
    sink = CanonicalSink(root, settings.chunk_rows)
    cdc = CDCWriter(root, settings)
    progress(f"Simulating {settings.counts['orders']:,} orders ({settings.size}, seed={settings.seed}) ...")
    try:
        metrics = Simulation(sink, cdc, settings).run()
    finally:
        sink.close()
        cdc.close()
    progress("Exporting source-system snapshots with controlled imperfections ...")
    raw_counts = export_sources(root, settings)
    if settings.keep_ground_truth:
        notes = {
            "periods": settings.incidents,
            "effects": {"payment_outage": "PayLotus ewallet first-attempt failure 70%, fewer successful retries; payment tickets and abandoned sessions",
                       "carrier_disruption": "MekongParcel extra 4-9 days; failed attempts and delay tickets",
                       "inventory_shortage": "Electronics order shortage cancellations and reduced reservation/fulfillment",
                       "margin_campaign": "Higher spend/demand, 22% dedicated coupon, more abandoned traffic; product margin is only a proxy",
                       "quality_issue": "Beauty purchases: 40% return probability, poorer reviews, quality support tickets"},
            "realized_counts": metrics,
        }
        (root / "instructor" / "incidents.json").write_text(json_text(notes) + "\n", encoding="utf-8")
    # Only remove artifacts created in this invocation, inside the verified destination.
    if settings.omit_reference:
        reference = (root / "reference" / "canonical").resolve()
        if reference.parent.parent != root or reference.name != "canonical":
            raise ValueError("Unexpected reference path")
        shutil.rmtree(reference)
    progress("Computing file counts and SHA-256 checksums ...")
    files = file_manifest(root)
    manifest = dict(format_version=1, generator_version="1.0.0", seed=settings.seed, size=settings.size,
                    profile=settings.profile, snapshot_cutoff=stamp(CUTOFF), timestamp_convention="UTC, seconds; reporting UTC+07:00",
                    canonical_rows=sink.counts, raw_rows=raw_counts, files=files,
                    total_data_bytes=sum(item["bytes"] for item in files), canonical_reference_retained=not settings.omit_reference,
                    configuration={k: v for k, v in asdict(settings).items() if k not in {"output", "incidents"}},
                    incidents_configured=True, simulated_business_counts=metrics)
    # Exact incident dates stay in author config and optional instructor output, outside learner README.
    (root / "manifests" / "generation.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    incomplete.unlink()
    return manifest
