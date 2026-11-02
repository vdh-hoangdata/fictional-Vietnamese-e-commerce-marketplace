"""Build an execution report from real manifests, validation reports and JUnit XML."""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def execution_report(small, medium, junit, destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Report already exists: {destination}")
    runs = []
    for folder in (Path(small), Path(medium)):
        manifest = json.loads((folder / "manifests" / "generation.json").read_text(encoding="utf-8"))
        validation = json.loads((folder / "manifests" / "validation.json").read_text(encoding="utf-8"))
        runs.append((folder, manifest, validation))
    suite = ET.parse(junit).getroot()
    suites = [suite] if suite.tag == "testsuite" else list(suite.findall("testsuite"))
    tests = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    lines = ["# Engineering execution report", "", "Recorded from the generated manifests, validator JSON and actual pytest JUnit results.", "",
             "## Deliverables", "", "24 relational/event datasets: the 23 requested domains plus shipment_items for normalized split parcels.",
             "Each run includes canonical snapshots, nine imperfect source-system exports, a four-entity CDC stream,",
             "aggregate quality manifests, and optional instructor ground truth (enabled for these runs).", "", "```text",
             "dataset/", "  generate.py, validate.py, pyproject.toml, requirements.txt, README.md",
             "  configs/       example parameters and machine-readable field schema",
             "  src/           config, models, generators, business_rules, exporters,",
             "                 anomaly_injection, validators, utils",
             "  tests/         unit, integration, reconciliation",
             "  sql/           six SQL Server initialization/import/check scripts",
             "  docs/          business, field dictionary, Mermaid ERD, source contracts,",
             "                 quality/generation/import guides, 34 DA and 24 DE exercises",
             "  data/sample/   executed SMALL run",
             "  data/medium/   executed MEDIUM run",
             "    raw/<system>/, reference/canonical/, cdc/, manifests/, instructor/", "```", "",
             "## Canonical row counts", "", "| Dataset | SMALL | MEDIUM |", "|---|---:|---:|"]
    for table, count in runs[0][1]["canonical_rows"].items():
        lines.append(f"| {table} | {count:,} | {runs[1][1]['canonical_rows'][table]:,} |")
    lines += ["", "Counts above represent business grains; raw revisions/replays can add ingestion rows.", "", "## Execution evidence", "",
              "| Measure | SMALL | MEDIUM |", "|---|---:|---:|"]
    metrics = [
        ("Data bytes (CSV/JSONL, including references and instructor records)", lambda m, v: f"{m['total_data_bytes']:,}"),
        ("Data files", lambda m, v: str(len(m["files"]))),
        ("Business/PK/FK checks", lambda m, v: str(len(v["business_checks"]))),
        ("Canonical generator errors", lambda m, v: str(len(v["generator_errors"]))),
        ("Validation", lambda m, v: "PASS" if v["ok"] else "FAIL"),
        ("CDC records", lambda m, v: f"{v['cdc']['events']:,}"),
        ("Identical CDC replays", lambda m, v: f"{v['cdc']['identical_replays']:,}"),
        ("Reconstructed CDC business keys", lambda m, v: f"{v['cdc']['reconstructed_keys']:,}"),
        ("Intended source conditions (overlapping trials, not bad-row count)", lambda m, v: f"{sum(v['intended_source_conditions']['applied_counts'].values()):,}"),
        ("Repeat customers", lambda m, v: f"{v['distributions']['repeat_customers']:,}"),
        ("Customers with exactly one placed order", lambda m, v: f"{v['distributions']['customers_with_one_order']:,}"),
        ("Failed payment attempts", lambda m, v: f"{v['distributions']['failed_payment_attempts']:,}"),
        ("Late delivered parcels", lambda m, v: f"{v['distributions']['late_deliveries']:,}"),
        ("Partial item returns", lambda m, v: f"{v['distributions']['partial_returns']:,}"),
    ]
    for title, format_value in metrics:
        lines.append(f"| {title} | " + " | ".join(format_value(m, v) for _, m, v in runs) + " |")
    lines += ["", f"Pytest: **{tests-failures-skipped} passed, {failures} failures/errors, {skipped} skipped**.",
              "Evidence: `data/test-results.xml` and each run's `manifests/validation.json`.",
              "Checks include full intermediate payment CDC chronology and latest-state reconstruction despite replays and shuffled arrival.",
              "Mutation tests prove that header discrepancies and negative inventory are detected without automatic repair.", "",
              "## Supported configurations", "", "SMALL 5,000 orders; MEDIUM (default) 100,000; LARGE 1,000,000.",
              "Profiles: clean, realistic (default), challenging. Configurable seed, destination, rates, incident windows,",
              "anonymous traffic and file chunk size; optional instructor ground truth and canonical-reference omission.",
              "Python 3.11+, standard-library runtime. Only pytest is required for development. Runtime here used Python 3.13.", "",
              "## Regenerate and test", "", "Use absent or empty destinations; existing data/reports are refused.", "", "```powershell",
              "python generate.py --size small --seed 42 --output ./data/sample --keep-ground-truth",
              "python validate.py --input ./data/sample",
              "python generate.py --size medium --seed 42 --output ./data/medium --keep-ground-truth",
              "python validate.py --input ./data/medium",
              "python generate.py --size large --seed 42 --output ./data/large --chunk-rows 100000",
              "python -m pytest -q --junitxml=data/test-results.xml", "```", "",
              "## SQL Server and learning", "", "Run sql/01 then 02 and 04 in a fresh instance; land raw files as text in staging, preserving all parts and metadata.",
              "Build your own cleansing/deduplication pipeline before loading typed tables, then run 03 and 06.",
              "Use the Import Wizard or the reviewed BULK INSERT template in 05; JSONL needs line-based JSON ingestion.",
              "See [SQL_SERVER_IMPORT_GUIDE.md](SQL_SERVER_IMPORT_GUIDE.md) for exact conventions and dependency order.",
              "First DA exercise: compare monthly GMV and collected cash (#1). First DE exercise: immutable raw ingestion with manifest verification (#1).", "",
              "## Known limitations", "", "LARGE is implemented but was not generated in this execution. No SQL Server instance was contacted;",
              "T-SQL artifacts were checked structurally and remain unexecuted against SQL Server.",
              "The synthetic scenario is illustrative, not a fitted economic or geographic model. Reporting regions are coarse historical labels;",
              "districts/postcodes are intentionally unknown. Seasonal demand is a modeling approximation.",
              "Ledger on-hand means sellable stock, so supplier quarantine appears as a signed adjustment with a later release receipt.",
              "Business work after the cutoff is right-censored. Observed campaign credit is incomplete and not causal.",
              "Product cost is modeled, but taxes, seller payout, platform revenue and fully costed profit are not.",
              "CSV and JSONL are supported; optional Parquet was not implemented. The complete student ETL is intentionally not supplied.",
              "Keep `reference/` and `instructor/` out of learner packages. Generated data is ignored by Git by default.", ""]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--small", type=Path, default=Path("data/sample"))
    parser.add_argument("--medium", type=Path, default=Path("data/medium"))
    parser.add_argument("--junit", type=Path, default=Path("data/test-results.xml"))
    parser.add_argument("--output", type=Path, default=Path("docs/EXECUTION_REPORT.md"))
    args = parser.parse_args()
    execution_report(args.small, args.medium, args.junit, args.output)
