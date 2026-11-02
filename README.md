# VietCommerce practice data

A fictional Vietnamese marketplace operating from 2024-01-01 to 2025-12-31.
All people, contacts, merchants and street addresses are synthetic. Monetary
amounts are integer VND. Operational timestamps are UTC; reporting uses UTC+07:00
(Asia/Ho_Chi_Minh). Province labels describe historical reporting regions, not a
current administrative directory.

```powershell
python generate.py --size small --seed 42 --output ./data/sample
python validate.py --input ./data/sample
python -m pytest -q
python generate.py --size medium --seed 42 --output ./data/medium
```

The default preset is MEDIUM (100,000 orders). LARGE produces 1,000,000 orders.
Use `--profile clean|realistic|challenging`, `--config configs/example.json`,
`--chunk-rows 100000`, and `--keep-ground-truth` as needed. An output directory
must be empty or absent; regeneration requires a new destination. No existing
files are overwritten. The generator uses the standard library only; pytest is
the sole development dependency.

Start with [the business overview](docs/BUSINESS_OVERVIEW.md),
[the data dictionary](docs/DATA_DICTIONARY.md), and
[financial and lifecycle rules](docs/BUSINESS_RULES.md).
The raw source data is intentionally imperfect. `reference/canonical/` is an
instructor/testing reference, not a student cleansing solution. Keep this folder
and `instructor/` out of a learner distribution. `--omit-reference` excludes the
canonical files after generation; full business validation then requires a
separately retained reference. Aggregate injection counts in the manifest reveal
no affected business keys. CDC is a separate change stream, not additional sales.

Learners implement their own Bronze/Silver/Gold pipelines. See
[DA exercises](docs/DA_PRACTICE.md), [DE exercises](docs/DE_PRACTICE.md), and
[SQL Server import guidance](docs/SQL_SERVER_IMPORT_GUIDE.md).
SQL scripts are supplied for local execution; the generator never connects to a
database server.

The completed run's table counts, validation evidence and limitations are in
[the engineering execution report](docs/EXECUTION_REPORT.md).
