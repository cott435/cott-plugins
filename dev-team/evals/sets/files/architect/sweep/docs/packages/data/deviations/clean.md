# Deviations — data/clean

## data/clean — 2026-09-27 — spec-change:design — 1

Clause: design §5 sort_by_ts
Said: "Per contract §3."
Found: contract §3 calls `sort_by_ts` "a stable ascending sort", and design §7 asks for one intent test per interface row, but no design item says which of two records with equal `ts` comes first — `packages/data/tests/intent/clean/test_dedupe.py` (as of the entry) has no tie-order test the design can back
Why: the tester cannot write the tie-order test from a design item that does not state the order
Status: open
Raised by: tester — run-package data
Resolved by: —
