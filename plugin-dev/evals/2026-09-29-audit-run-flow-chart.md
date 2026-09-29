# audit-run flow chart: waves, lanes, review outcomes, on a fixture and a 105-agent run

**Tested against:** uncommitted, see the working-tree diff on branch `audit-run` (on `482d74a`): `skills/audit-run/scripts/flow.py`, `trace.py`, `evals/fixtures/audit-run/make_session.py` · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/sets/audit-run.json` evals 1, 3 · **Iteration:** none, run by hand · **Baseline:** none · **Pass rate:** eval 1 6/6, eval 3 6/6

## What was tested

`trace.py build` now also writes `flow.html` and a **Flow** section in `run.md`. The claim is that they show:
- which agents ran in parallel, meaning they were spawned in one message;
- which agents ran in series;
- where the driver stopped to ask the user;
- each section's runs and review rounds;
- each review's verdict and counts.

## Method

- **Eval 3: mechanical.** A new fixture session, `flow-session`, has a known shape:
  - W1 runs two writers in parallel;
  - W2 is a review requesting changes, with 1 critical;
  - then a question to the user, answered "Fix it";
  - W3 is the fix;
  - W4 is a review approving at round 2.

  Six checks cover the Flow text and the HTML.
- **Negative run.** One writer's spawn was moved to its own message in a copy of the fixture. Eval 3 must fail, and it did (E1, E3, E5 FAIL).
- **Eval 1** was re-run to confirm the planted-defect trace is unchanged.
- **Real run.** The quant session `1493ed56` ("Project architecture migration"), rebuilt this morning, has grown to 105 agents. The chart was checked in the browser pane at 800 px width, in dark mode.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 3 · waves | W1 ∥ 2, then three → 1 | yes | ✅ |
| 3 · reviews | U03 request changes 1 crit, U05 approve | yes | ✅ |
| 3 · band | question between W2 and W3, with "Fix it" | yes | ✅ |
| 3 · lanes | a/x 4 runs, 2 rounds, reviews in order; a/y 1 run | yes | ✅ |
| 3 · html | headers, ∥ 2, ✗ changes 1C 2W, ✓ approve, band | yes | ✅ |
| 3 · issues table | U03 listed, U05 not | yes | ✅ |
| 3 · negative | split wave fails | E1, E3, E5 FAIL | ✅ |
| 1 · all | unchanged | 6/6 | ✅ |
| Real run | legible chart | 57 waves, 19 parallel (widest 10), 15 sections, 5 stops for the user; the identity loop reads r1 → regenerate → r2 → redesign → test → implement → r3 in one column | ✅ |

## Found on the real run, fixed before these results

- `1 crit` was read from "round-1 CRITICAL". Counts now need a bare number, preferably beside the warnings.
- U27's `Result: blocked` showed as `approve`, because its text said it would approve. A blocked or stopped result now wins over the verdict.
- The question bands showed the harness's preamble instead of the answer. The answer is now pulled from `"question"="answer"`.
- Columns in first-appearance order put the first implementer off-screen. Columns now follow the widest wave: the plan's order, as the designers ran.
- On a 2830×4246 chart, the section headers and wave labels scrolled away. Both are now sticky.

## Verdict

Holds. Not tested: a plugin whose returns carry no `Verdict:` line (the chart then has no review colours), and light mode.
