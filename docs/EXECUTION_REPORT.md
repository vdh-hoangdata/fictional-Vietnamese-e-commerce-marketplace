# Engineering execution report

Recorded from the generated manifests, validator JSON and actual pytest JUnit results.

## Deliverables

24 relational/event datasets: the 23 requested domains plus shipment_items for normalized split parcels.
Each run includes canonical snapshots, nine imperfect source-system exports, a four-entity CDC stream,
aggregate quality manifests, and optional instructor ground truth (enabled for these runs).

```text
dataset/
  generate.py, validate.py, pyproject.toml, requirements.txt, README.md
  configs/       example parameters and machine-readable field schema
  src/           config, models, generators, business_rules, exporters,
                 anomaly_injection, validators, utils
  tests/         unit, integration, reconciliation
  sql/           six SQL Server initialization/import/check scripts
  docs/          business, field dictionary, Mermaid ERD, source contracts,
                 quality/generation/import guides, 34 DA and 24 DE exercises
  data/sample/   executed SMALL run
  data/medium/   executed MEDIUM run
    raw/<system>/, reference/canonical/, cdc/, manifests/, instructor/
```

## Canonical row counts

| Dataset | SMALL | MEDIUM |
|---|---:|---:|
| customers | 1,400 | 20,000 |
| customer_addresses | 1,751 | 24,509 |
| sellers | 18 | 100 |
| categories | 18 | 18 |
| products | 240 | 3,000 |
| product_price_history | 853 | 10,728 |
| orders | 5,000 | 100,000 |
| order_items | 12,037 | 241,353 |
| order_status_history | 24,402 | 487,429 |
| coupons | 32 | 32 |
| order_discounts | 1,039 | 21,139 |
| payments | 5,138 | 103,115 |
| refunds | 793 | 16,381 |
| warehouses | 6 | 6 |
| inventory_movements | 24,739 | 495,796 |
| shipments | 10,662 | 222,122 |
| shipment_items | 11,254 | 224,384 |
| shipment_events | 44,618 | 928,705 |
| returns | 685 | 13,611 |
| marketing_campaigns | 32 | 32 |
| marketing_spend_daily | 809 | 809 |
| web_events | 47,759 | 951,952 |
| reviews | 2,339 | 46,690 |
| support_tickets | 1,434 | 29,351 |

Counts above represent business grains; raw revisions/replays can add ingestion rows.

## Execution evidence

| Measure | SMALL | MEDIUM |
|---|---:|---:|
| Data bytes (CSV/JSONL, including references and instructor records) | 115,209,719 | 2,354,048,835 |
| Data files | 50 | 137 |
| Business/PK/FK checks | 110 | 110 |
| Canonical generator errors | 0 | 0 |
| Validation | PASS | PASS |
| CDC records | 83,467 | 1,703,824 |
| Identical CDC replays | 1,078 | 20,309 |
| Reconstructed CDC business keys | 21,040 | 428,237 |
| Intended source conditions (overlapping trials, not bad-row count) | 10,508 | 207,923 |
| Repeat customers | 718 | 12,782 |
| Customers with exactly one placed order | 315 | 3,596 |
| Failed payment attempts | 209 | 4,513 |
| Late delivered parcels | 1,266 | 26,461 |
| Partial item returns | 131 | 2,107 |

Pytest: **48 passed, 0 failures/errors, 0 skipped**.
Evidence: `data/test-results.xml` and each run's `manifests/validation.json`.
Checks include full intermediate payment CDC chronology and latest-state reconstruction despite replays and shuffled arrival.
Mutation tests prove that header discrepancies and negative inventory are detected without automatic repair.

## Supported configurations

SMALL 5,000 orders; MEDIUM (default) 100,000; LARGE 1,000,000.
Profiles: clean, realistic (default), challenging. Configurable seed, destination, rates, incident windows,
anonymous traffic and file chunk size; optional instructor ground truth and canonical-reference omission.
Python 3.11+, standard-library runtime. Only pytest is required for development. Runtime here used Python 3.13.

## Regenerate and test

Use absent or empty destinations; existing data/reports are refused.

```powershell
python generate.py --size small --seed 42 --output ./data/sample --keep-ground-truth
python validate.py --input ./data/sample
python generate.py --size medium --seed 42 --output ./data/medium --keep-ground-truth
python validate.py --input ./data/medium
python generate.py --size large --seed 42 --output ./data/large --chunk-rows 100000
python -m pytest -q --junitxml=data/test-results.xml
```

## SQL Server and learning

Run sql/01 then 02 and 04 in a fresh instance; land raw files as text in staging, preserving all parts and metadata.
Build your own cleansing/deduplication pipeline before loading typed tables, then run 03 and 06.
Use the Import Wizard or the reviewed BULK INSERT template in 05; JSONL needs line-based JSON ingestion.
See [SQL_SERVER_IMPORT_GUIDE.md](SQL_SERVER_IMPORT_GUIDE.md) for exact conventions and dependency order.
First DA exercise: compare monthly GMV and collected cash (#1). First DE exercise: immutable raw ingestion with manifest verification (#1).

## Known limitations

LARGE is implemented but was not generated in this execution. No SQL Server instance was contacted;
T-SQL artifacts were checked structurally and remain unexecuted against SQL Server.
The synthetic scenario is illustrative, not a fitted economic or geographic model. Reporting regions are coarse historical labels;
districts/postcodes are intentionally unknown. Seasonal demand is a modeling approximation.
Ledger on-hand means sellable stock, so supplier quarantine appears as a signed adjustment with a later release receipt.
Business work after the cutoff is right-censored. Observed campaign credit is incomplete and not causal.
Product cost is modeled, but taxes, seller payout, platform revenue and fully costed profit are not.
CSV and JSONL are supported; optional Parquet was not implemented. The complete student ETL is intentionally not supplied.
Keep `reference/` and `instructor/` out of learner packages. Generated data is ignored by Git by default.
