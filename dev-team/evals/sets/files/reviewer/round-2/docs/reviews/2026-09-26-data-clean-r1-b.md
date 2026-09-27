# Review — data/clean — round 1 — correctness
Scope: packages/data/src/data/clean/, packages/data/tests/unit/clean/, packages/data/tests/intent/clean/, design/clean.md §4 §6 §8, .dev-team/gate.txt
Commit: 7c2e4b1
Verdict: request changes
Round: 1
Focus: correctness

## CRITICAL

- packages/data/src/data/clean/rules.py:44 — `fill_gaps` forward-fills all four price columns from the previous row, so a filled bar shows the previous day's `open`, `high` and `low` — a range that never traded; design §4 step 4 says `open`, `high`, `low` and `close` all equal the previous bar's `close` — a wrong result on the main path (every gap row) — set every price column of a gap row to the previous `close`.

## WARNING

- packages/data/src/data/clean/rules.py:30 — `fill_gaps` has no docstring line for what a filled row holds; the reader has to know design §4 step 4.
- packages/data/tests/intent/clean/test_workflow.py:25 — `test_gap_row_carries_previous_close` asserts `close` and `volume` only; `open`, `high`, `low` on a filled row are untested, which is how the finding above passed the gate.

## SUGGESTION

- MEASURED complexity `uv run radon cc packages/data/src -s -a` — clean: max B (6) clean_bars, average A (3.2)
- MEASURED module size `wc -l packages/data/src/**/*.py` — clean/api.py 48, clean/rules.py 52, clean/calendar.py 10, clean/errors.py 14

## Coverage

- none

## Carried

- none

## Spec-change

- none

## Deferred

- none
