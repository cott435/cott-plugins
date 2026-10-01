# Decisions

## D1 — What makes two bars duplicates of each other?

Scope: data/clean
Raised by: OQ-data-clean-1
Recommendation: the same `(symbol, timestamp)` pair; the vendor sometimes returns a bar twice
within one response, and two symbols legitimately share every timestamp.
Assumption if unanswered: the same `(symbol, timestamp)` pair.
Decision: the same `(symbol, timestamp)` pair. Two rows for one symbol and one day are one bar.
Status: decided
Applied: data/clean

## D2 — Should a gap-filled bar be flagged for downstream consumers?

Scope: data/clean
Raised by: OQ-data-clean-2
Recommendation: no flag column now; `features` has not asked for one and a new column changes
the BarFrame shape.
Assumption if unanswered: no flag column; filled rows are distinguishable only by `volume == 0`.
Decision:
Status: open

## D3 — Does the `daily` pipeline land one parquet file per symbol, or one per run?

Scope: data/surface
Raised by: OQ-data-surface-1
Recommendation: one file per symbol; `features` reads one symbol at a time, and a symbol that
was skipped then leaves the others readable.
Assumption if unanswered: one file per symbol, `DATA_LANDING_DIR/<run_date>/<symbol>.parquet`.
Decision:
Status: open
