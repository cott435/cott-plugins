# Audit fixes 1–3 and 9: the gate stops blocking on other sections' intent tests, one record per section, the post-gate return, empty nested `__init__.py`

**Tested against:** uncommitted, see the working-tree diff on branch `gate-fixes` (on `656286e`): `hooks/gate_on_stop.py`, `hooks/format_on_edit.py`, `pyproject-lint-config.toml`, `agents/implementer.md`, `agents/reviewer.md`, `agents/tester.md`, `skills/run-package/SKILL.md`, `skills/pair/SKILL.md` · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/fixtures/hook-events` (mechanical, 59 cases; 7 new, 5 changed) · **Baseline:** 1.0.0's hooks (`656286e`) · **Pass rate:** 59/59 vs the new cases failing on 1.0.0

## What was tested

These are the four fixes the audit of the quant run asked for (`2026-09-28-audit-run-package-1493ed56.md`, errors E1, E2, E3, E9).

1. **The gate no longer blocks on other sections' intent tests.**
   - A check that fails only in intent-test files the run did not touch is `ELSEWHERE`, not `FAIL`.
   - The format hook lints with the plugin's lint block until the repo has its own, so testers meet the real rules from their first file.
2. **Every post-gate return says it must be re-sent through the hand-back.** This covers the implementer text and the gate's messages. The last retry says so, and names the `let through` line.
3. **One gate record per section**, `.dev-team/gate/<pkg>/<section>.txt`, instead of a single `.dev-team/gate.txt`.
9. **Empty nested `__init__.py` files no longer trip D104.** A package's top-level `__init__.py` keeps the rule.

## Method

- **Harness.** `evals/fixtures/hook-events/check.py` gained a `prior` setup: files committed before the run's commit, so they are in the repo but not in the run's diff. The gate's record is now read from the per-section path.
- **New cases:**
  - `gate-elsewhere`: an untouched intent test with a lint error → pass with ELSEWHERE. Another section's record is left alone, and no `gate.txt` is written.
  - `gate-elsewhere-touched`: the same file, but in the run's diff → FAIL.
  - `gate-elsewhere-mixed`: plus an error in the run's own code → FAIL.
  - `gate-elsewhere-format`: an unformatted untouched intent test → ELSEWHERE.
  - `fmt-no-config`: a tester's file in a repo with no ruff config → PLR0913 and E501 reported.
  - `fmt-repo-config`: the repo's own config wins.
  - `fmt-empty-init` / `fmt-top-init`: the nested one passes, the top-level one still fails D104.
- **Changed cases:**
  - The attempt-1/2/3 cases assert the new hand-back and record-path text.
  - `fmt-fixable`'s module gained a docstring, because the real rules now apply where ruff's defaults did not.
  - Three cases' `absent` lists moved from `gate.txt` to `.dev-team/gate`.
- **Baseline runs.** Each new case was run against 1.0.0's hook or lint block, swapped in and then restored.
- **Replay on real data.** I cloned the quant repo (session 1493ed56, "Project architecture migration") into the scratchpad and synced it offline.
  - At `a89312f`, U14's calendar commit, `gate_on_stop.py --report --base a89312f~1` ran with the 1.0.0 hook and with the new one.
  - At `75e2090`, the edgar tester's commit, edgar's intent tests were linted with ruff's defaults and with the plugin's lint block.
- **Eval sets.** The reviewer set's four prompts and three fixture records moved to `.dev-team/gate/data/clean.txt`, and the hooks set's two mentions to `.dev-team/gate/data/ingest.txt`. Both sets validate.
- **Not run:** a behavioral implementer run testing fix 2's re-sent hand-back. It is prose plus hook text; the cases check the text.

## Results

| Case | 1.0.0 | Now |
|---|---|---|
| hook-events, 52 existing cases | 51/51 before | 52/52 (5 updated) |
| `gate-elsewhere` | FAIL: exit 2, no ELSEWHERE | PASS |
| `gate-elsewhere-touched` | FAIL (no per-section record) | PASS: still FAIL on the touched file |
| `gate-elsewhere-mixed` | FAIL (no per-section record) | PASS: FAIL on `loader.py` |
| `gate-elsewhere-format` | FAIL: exit 2 | PASS |
| `fmt-no-config` | FAIL: defaults pass the file | PASS |
| `fmt-repo-config` | PASS | PASS |
| `fmt-empty-init` | FAIL: D104 | PASS |
| `fmt-top-init` | — | PASS: D104 kept |
| Replay, U14 at `a89312f` | `result: fail (3 failures)` on edgar's and marketparquet's intent tests | `result: pass (3 failing checks elsewhere)`, naming both directories; 118/118 calendar intent tests pass |
| Replay, edgar tester at `75e2090` (no root pyproject) | ruff defaults: 0 errors | plugin block: 44 (34 E501, 9 PLR0913, 1 I001), the 44 that later held every implementer |
| contracts | 36/36 | 36/36 |

## Verdict

Fixes 1, 3 and 9 hold: mechanically on the fixture, and on the real repo for 1. On the quant run, the calendar implementer would have passed its first attempt instead of burning three. The edgar tester would have been shown all 44 errors as it wrote them.

Fix 2 is text only and is not yet proven behaviorally. The platform fact it rests on is now in `plugin-anatomy`'s `agents.md`, proven by the audit log. Rerun an audit on the next real `run-package` to confirm that implementers re-send the hand-back.
