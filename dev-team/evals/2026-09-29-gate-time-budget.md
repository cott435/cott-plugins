# The gate's time budget: package-wide rows that run out of time are TIMEOUT, not FAIL

**Tested against:** uncommitted, see the working-tree diff on branch `gate-fixes` (on `ff5776a`): `hooks/gate_on_stop.py`, `agents/implementer.md`, `agents/reviewer.md`, README · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/fixtures/hook-events` (66 cases, 2 new) · **Baseline:** `ff5776a` · **Pass rate:** 66/66; both new cases fail on the baseline

## What was tested

A whole-package health check of the quant repo, run with the fixed gate at `e80ef80`, found that the Toolchain's two package-wide `pytest` commands no longer finish inside the gate's 240 s per command. A timed-out command names no file, so it could never be `ELSEWHERE`. It stayed a FAIL that nothing the implementer edits could fix. The priceaudit implementer (session `5976c083`, U04) spent all three attempts on it, alongside the edgar lint.

Two hazards follow from this:
- Two 240 s timeouts plus the rest of the checks sit at the edge of the hook's own 600 s timeout in `hooks.json`.
- Past that timeout, Claude Code kills the hook.

The claim now tested:
- The section's own checks (intent suite, Guarded, surface) run first and still block.
- The package-wide rows then share a budget below the hook's timeout: `DEV_TEAM_GATE_BUDGET`, default 540 s, with each row at most `DEV_TEAM_GATE_TIMEOUT`, default 240 s.
- A row that runs out of time, or never starts, is `TIMEOUT` and does not block.

## Method

- **`gate-timeout`:** a constraints row that sleeps 30 s under a 2 s per-row limit gives `TIMEOUT … did not finish in 2s`, exit 0, `result: pass (1 check out of time)`.
- **`gate-budget`:** the same row under a 6 s budget leaves a later row `not run: the gate's 6s budget was spent`.
- **Harness:** gained an `env` key.
- **Baseline:** both cases were run against `ff5776a`'s gate.
- **Replay:** `gate_on_stop.py --report --base eae786b~1` at `e80ef80` in the scratchpad clone of the quant repo (priceaudit's implementer diff), timed.

## Results

| Case | `ff5776a` | Now |
|---|---|---|
| `gate-timeout` | FAIL (exit 2 on the timeout) | PASS |
| `gate-budget` | FAIL | PASS |
| hook-events, the other 64 | 64/64 | 64/64 (two result-line wordings updated) |
| Replay, priceaudit at `e80ef80` | the run itself: 3 attempts, let through, about 60 min | `result: pass (1 check failing elsewhere; 2 checks out of time)`, 196/196 intent tests, 499 s end to end, under the hook's 600 s |
| state-cases / contracts | 52/52 / 36/36 | 52/52 / 36/36 |

## Verdict

Holds. Each attempt still spends about 8 minutes on two package suites that cannot finish. The repo can fix that by giving `docs/constraints.md` (via `/dev-team:set-constraints`) one scoped test row instead of the Toolchain's two duplicate package-wide commands. That is advice for the repo, not a plugin change.
