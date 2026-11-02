# Generate and reproduce

Use Python 3.11 or later. Runtime needs no installed packages. To run the tests:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

```powershell
python generate.py --size small --seed 42 --output ./data/sample --keep-ground-truth
python validate.py --input ./data/sample --report ./data/sample/manifests/validation.json
python generate.py --size medium --seed 42 --output ./data/medium --keep-ground-truth
python validate.py --input ./data/medium --report ./data/medium/manifests/validation.json
python generate.py --size large --seed 42 --output ./data/large --chunk-rows 100000
python generate.py --size small --seed 7 --output ./data/clean7 --profile clean
python generate.py --size small --seed 7 --output ./data/hard7 --profile challenging --config configs/example.json
```

Destinations must be absent or empty. Existing data and reports are refused.
Use a fresh output name for reruns; no unsafe overwrite flag is offered. An
interrupted generation leaves `GENERATION_INCOMPLETE`; do not ingest that run.
Validation is a separate command and returns nonzero on actual defects or when
business validation is unavailable. Reports are optional, separate artifacts,
not covered by the data-file manifest. Generation does not print fabricated
validation results.

Presets: SMALL 5,000 orders / 1,400 customers / 240 products / 18 sellers;
MEDIUM 100,000 / 20,000 / 3,000 / 100; LARGE 1,000,000 / 200,000 / 30,000 / 1,000.
Order lines average about 2.4 per order; other fact counts follow simulated
outcomes. The output includes canonical, raw and CDC, so size can considerably
exceed a single relational snapshot. Budget several GB for MEDIUM and tens of GB
for LARGE plus disk-backed validation indexes. Run SMALL before scaling.

Configuration JSON can override return_rate, cancellation_rate,
payment_failure_rate, anonymous_sessions_per_order, chunk_rows and all five
incident windows. CLI --chunk-rows takes precedence. Unsupported keys and invalid
rates/dates fail before output creation. `--omit-reference` removes only the
canonical files created in that run after source export; retain a separate
reference when full validation is required. Exact incident periods are author
configuration, not learner README content.

SHA-256-derived random seeds isolate daily demand, master dimensions, order
selection, payments, logistics, experience, behavior, CDC transport and source
export streams. Adding a new table should use a new named stream. Reproducibility
is promised for the same code, configuration, Python minor version and seed;
changing business model code or volumes can change downstream relationships.
IDs are stable within that contract, not across different presets.

Fact/event rows are written incrementally. The demand sampler holds a bounded
one-integer-per-order date sample briefly (tens of MB at LARGE),
then releases it. Memory otherwise scales with master entities and the small
time-ordered inventory queue, not cumulative facts or events. Source export uses
64-row buffers; CDC uses 128. Validation indexes records in a disposable SQLite
file with a 32 MB page cache and disk-backed sort space. Scratch folders are
created under the dataset destination and deleted after use. The generator is
single-process; no GPU, external API, live customer data or database is used.

Regenerate schema artifacts after an intentional schema change:

```powershell
python -c "from pathlib import Path; from src.models.artifacts import write_schema_artifacts; write_schema_artifacts(Path('.'), Path('data/sample/reference/canonical'))"
```
