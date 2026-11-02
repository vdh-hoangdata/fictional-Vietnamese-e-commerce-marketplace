# Business behavior, defects and unknowns

Canonical records express the business simulation. A second pass exports raw
source records and injects eligible non-key imperfections using a separate
deterministic stream per table. Neither source anomalies nor CDC transport
replays modify the canonical reference. No primary or foreign key is replaced.

| Condition | Realistic selection rate | Interpretation |
|---|---:|---|
| Missing populated optional text | 1.5% | Missingness may be legitimate; no mandatory business key is removed |
| Duplicate ingestion | 0.8% | Same business record and envelope repeated |
| Whitespace / uppercase | 1.5% | Normalize text only with a field-aware policy |
| Delayed ingestion | 1.5% | Additional 2–7 days after ordinary source latency |
| Malformed non-key numeric attribute | 0.2% | `not_available` requires quarantine/TRY_CONVERT |
| Operational status mismatch | 0.4% | Orders/shipments can disagree with related business evidence |
| Missing populated campaign link | 4.0% | Attribution is unknown, not zero paid influence |
| JSON string numeric | 1.5% | Instrumentation latency encoded as a string |
| Corrected source record | 0.6% | Original source text replaced with UNKNOWN_SOURCE_VALUE, corrected revision 2 arrives eight days later |

These are independent Bernoulli trials over eligible records, not exact global
fractions. A row may receive several conditions. Challenging triples the rates
(capped at 50%); clean sets all injection rates to zero. Optional NULLs, business
payment failures, zero refunded amounts on pending refunds, right-censored
deliveries and late COD settlements remain valid in all profiles. Anonymous and
cross-device sessions are valid identity limitations.

Non-clean export buffers shuffle up to 64 rows, allowing late and out-of-order
arrival. This is not a claim of global time sorting. Histories and CDC must use
business sequence/version. Clean sources still have ordinary extraction latency,
and CDC always has realistic replays/delays independently of raw anomaly profile.

The aggregate manifest records selected injections, including missingness and
transport conditions that are not necessarily defects. Do not use its total as a
count of bad business records. Optional `--keep-ground-truth` writes affected
business keys and original values under `instructor/`; exclude that directory
from student distribution. The normal exports carry no issue label or answer.

`validate.py` checks canonical integrity, file hashes and CDC reconstruction. It
reports known source conditions separately and never silently repairs records.
It deliberately does not perform the student's raw cleansing/ETL. Validation
without a canonical reference returns INCOMPLETE rather than a false pass.
