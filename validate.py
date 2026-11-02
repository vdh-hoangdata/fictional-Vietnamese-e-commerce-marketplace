import argparse
import json
import sqlite3
import sys
from pathlib import Path

from src.validators.checks import validate_dataset


def main():
    parser = argparse.ArgumentParser(description="Validate canonical business logic, CDC target state, and file integrity")
    parser.add_argument("--input", type=Path, default=Path("data"))
    parser.add_argument("--report", type=Path, help="Optional JSON report destination (must not already exist)")
    args = parser.parse_args()
    if args.report and args.report.exists():
        print(f"Refusing to overwrite existing report: {args.report}", file=sys.stderr)
        return 1
    try:
        report = validate_dataset(args.input)
    except (ValueError, OSError, KeyError, sqlite3.Error) as error:
        print(f"Validation could not complete: {error}", file=sys.stderr)
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validation: {'PASS' if report['ok'] else 'FAIL / INCOMPLETE'}")
    print(f"Canonical generator errors: {len(report['generator_errors'])}")
    print(f"Known source conditions (not canonical defects): {sum(report['intended_source_conditions']['applied_counts'].values()):,}")
    if report.get("cdc"):
        print(f"CDC: {report['cdc']['events']:,} records, {report['cdc']['identical_replays']:,} identical replays")
    for error in report["generator_errors"][:15]:
        print(json.dumps(error, ensure_ascii=False))
    if report.get("limitation"):
        print(report["limitation"])
    print("SQL Server scripts have not been executed against a SQL Server instance.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
