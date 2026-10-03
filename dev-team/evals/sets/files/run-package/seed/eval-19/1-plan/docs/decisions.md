# Decisions

One entry per question. `Status: decided` is written only by the user, or by the driver
relaying the user's answer.

## D1 — How many rows may a profile of `stage:rawtrades` pull when the export is not on disk?
Scope: data/clean
Raised by: /dev-team:plan-package data (interview)
Recommendation: 500 rows — the export is a local file of about 400 rows, read whole in under a second (`docs/sources/trades.md`, **Cost and time of a full pass**), so a pull costs nothing.
Assumption if unanswered: 500 rows
Decision: 500 rows.
Status: decided
