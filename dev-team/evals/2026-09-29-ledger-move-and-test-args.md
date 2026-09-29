# A ledger entry moved into its section file keeps its first commit; PLR0913 off for tests

**Tested against:** uncommitted, see the working-tree diff on branch `gate-fixes` (on `5ef4b86`): `skills/status/scripts/status.py`, `pyproject-lint-config.toml` · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/fixtures/state-cases` (53 cases, 1 new), `evals/fixtures/hook-events` (66, 1 changed) · **Baseline:** `5ef4b86` · **Pass rate:** 53/53 and 66/66; the new state case fails on the baseline

## What was tested

Both came up while planning the quant repo's one-time fixes.

1. **Moving an entry must not re-open anything.**
   - `entry_rev` dated an entry by the first commit adding its heading to the entry's own file.
   - Splitting a pre-split `docs/deviations.md` into section files would therefore date every moved entry at the move.
   - An open `spec-change:design` that a design rewrite had answered (answered means the design was committed after the entry) would look unanswered again. In the quant repo, yahoo, identity and prices would have gone back to DESIGN.
   - The fix: `entry_rev` searches every ledger path, so the first add, before the move, is the date.
2. **PLR0913 is off for tests.**
   - All nine PLR0913 hits in the quant repo's edgar intent tests are pytest functions. A parametrized test takes one argument per name, and a fixture factory takes its fixtures.
   - Capping those at five forces contorted fixtures, and project-structure's limit is about a function's design.
   - The rule stays on for source.

## Method

- **`ledger-moved`:** an open `spec-change:design` in the pre-split file, the design rewritten after it, then a commit moving the entry to `docs/deviations/data/ingest.md`. Expected: TEST (answered), not DESIGN.
- **`fmt-no-config`:** now asserts E501 and no PLR0913 on an intent test with six arguments. It still fails on 1.0.0's hook, whose defaults report neither.
- **Baseline:** the new state case was run against `5ef4b86`'s `status.py`.

## Results

| Case | `5ef4b86` | Now |
|---|---|---|
| `ledger-moved` | FAIL: DESIGN, `open data/ingest — … — spec-change:design` (the move re-opened it) | PASS: TEST |
| state-cases, the other 52 | 52/52 | 52/52 |
| hook-events | 66/66 | 66/66 (`fmt-no-config` expectation changed) |
| contracts | 36/36 | 36/36 |

## Verdict

Both hold. The quant repo's ledger can be split without re-opening a section.
