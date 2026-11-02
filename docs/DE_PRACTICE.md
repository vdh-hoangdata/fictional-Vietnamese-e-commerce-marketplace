# Data engineering practice

Build the pipelines independently. The generator and validator are reference
infrastructure, not a completed student ETL. Do not use canonical data or optional
instructor ground truth as your Silver input. Every exercise needs a reproducible
run command and observable evidence.

| # | Engineering request | Stakeholder | Input / scope | Expected deliverable | Difficulty | Common pitfall |
|---|---|---|---|---|---|---|
| 1 | Land all source files without losing lineage | Platform lead | raw, generation manifest | Immutable Bronze files with ingestion audit and hash verification | Beginner | Reading only the first chunk or ingesting CSV headers as records |
| 2 | Validate source envelopes and schemas | Data governance | schema.json, all sources | Required/optional/type compatibility report | Beginner | Failing every nullable field or coercing invalid numerics to zero |
| 3 | Load text-based SQL Server staging | DBA | CSV parts, staging DDL | Repeatable import with source-file lineage | Beginner | Wizard auto-detection silently changes VND values |
| 4 | Parse nested behavioral JSON | Product data lead | web_events | Bronze parser with preserved original payload and quarantine | Beginner | Flattening loses nested properties or malformed originals |
| 5 | Distinguish event time and ingestion time | Data architect | source metadata | UTC contract plus Vietnam reporting-date demonstration | Beginner | Shifting an already local marketing date twice |
| 6 | Produce a source-to-table inventory | Governance | source systems, schema, manifest | Catalog with grains, PKs, FKs, nullability and owner | Beginner | Treating payment attempts as one row per order |
| 7 | Deduplicate ingestion and select corrected revisions | Analytics engineer | raw snapshots and envelopes | Silver latest-version tables with repeat-run evidence | Intermediate | Choosing file order or ingestion timestamp over source version |
| 8 | Quarantine malformed attributes without discarding valid keys | Quality engineer | challenging raw | Field-level reject ledger and recoverable policy | Intermediate | Dropping an entire financial order because a display field is malformed |
| 9 | Implement an idempotent CDC upsert | Pipeline owner | CDC orders/payments/shipments/products | Highest-version target and replay test | Intermediate | Replayed attempts create duplicate revenue |
| 10 | Reconstruct historical states | Compliance analyst | changed_at, source_version | As-of snapshots for several business instants | Intermediate | Arrival order differs from business chronology |
| 11 | Create product SCD Type 2 dimensions | Warehouse architect | products CDC, price history | Non-overlapping dimension history with surrogate keys | Intermediate | Price-history grain and catalog-state grain are different |
| 12 | Model fact orders, lines, payments and returns | BI architect | cleansed sales and finance | Dimensional design and declared grains | Intermediate | A single wide fact multiplies payments by items and parcels |
| 13 | Build a Gold daily cash mart | Finance data owner | captures/refunds | Reconciled daily local cash measures | Intermediate | Pending refunds are not cash outflows |
| 14 | Build a funnel mart with anonymous sessions | Product analytics | events, orders | Session-level funnel with explicit identity coverage | Intermediate | Device IDs are assumed to be people |
| 15 | Test business and referential invariants | Data quality owner | Silver model | Automated uniqueness, chronology, finance and eligibility tests | Intermediate | Expected dirty raw conditions are mislabeled generator bugs |
| 16 | Handle late dimensions and facts | Platform lead | source latency, CDC | Watermark/lookback strategy with demonstrated late arrivals | Intermediate | One maximum event-time watermark loses delayed records |
| 17 | Reconcile inventory reservations and physical stock | Warehouse data owner | inventory ledger, shipments, lines | Ordered balance mart with nonnegative invariants | Advanced | Summing reservations into physical consumption |
| 18 | Recover after a partial pipeline failure | Operations | chunked raw and CDC | Checkpoint/restart simulation preserving exactly-once logical results | Advanced | Checkpoint advances before target transaction commits |
| 19 | Apply historical corrections without double recognition | Controller | source revision 2, CDC corrections | Bitemporal or audited correction design | Advanced | Corrected attribution changes financial amounts accidentally |
| 20 | Partition facts for incremental processing | Platform engineering | LARGE configuration | Partition/pruning plan and bounded-memory benchmark | Advanced | Hundreds of tiny partitions hurt more than they help |
| 21 | Detect status disagreements between systems | Service reliability | orders, shipments, payments, histories | Reconciliation rules with ambiguous-state queue | Advanced | Treating valid in-flight COD differences as defects |
| 22 | Add a data contract evolution policy | Governance | schema registry, JSON properties | Compatible/additive/breaking change scenarios and tests | Advanced | A new optional JSON property breaks ingestion |
| 23 | Prove full financial reconciliation after replay | Finance engineering | snapshots, CDC, refunds, discounts | Automated control totals across two independently built paths | Advanced | Subtracting header and allocated coupons twice |
| 24 | Package a learner-safe dataset release | Training lead | raw, manifests, reference, instructor | Reproducible distribution that excludes answers and per-row labels | Intermediate | Shipping the canonical reference as student input |

Recommended first exercise: #1. Compare ingested row counts and SHA-256 values
with the supplied file manifest before implementing transformations.
