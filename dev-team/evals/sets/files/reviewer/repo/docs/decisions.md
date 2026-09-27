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
