# Decisions

One entry per question. `Status: decided` is written only by the user, or by the driver
relaying the user's answer.

## D1 — Does `ingest` pass the two exact-duplicate rows through, or reject them at load?
Scope: data/ingest
Raised by: /dev-team:plan-package data (interview)
Recommendation: pass them through unchanged; `clean` owns deduplication (brief: `clean trades`).
Assumption if unanswered: none
Decision:
Status: open
