# remake phase 2 — hooks: ruff on edit, the implementer stop gate, the per-role write guard

**Tested against:** uncommitted — see working-tree diff (on `6d005fb`; `hooks/hooks.json`, `hooks/format_on_edit.py`, `hooks/gate_on_stop.py`, `hooks/guard_writes.py`, `contracts.yml`, `evals/fixtures/hook-events/`) · model: `claude-opus-5-5` (mechanical rows, executors and graders); the nested `claude -p` sessions ran `claude-sonnet-5` (Claude Code 2.1.270) · 2026-09-27
**Set:** `evals/sets/hooks.json` evals 1, 2 (row 2.3) · **Iteration:** `evals/workspace/hooks/iteration-1` (evals 1, 2), `evals/workspace/hooks/iteration-2` (eval 1, after two fixes) · **Baseline:** none (`hooks/` deleted from the scratch copy) · **Pass rate:** iteration 1 100% vs 44%; iteration 2 100% vs 57% · rows 2.1, 2.2, 2.4 are mechanical and load, with no set

## What was tested

Four rows from `site/notes/remake-02-hooks.md` § Evals:

- **2.1** Does each script decide correctly on every path in the note's case table, including
  malformed input?
- **2.2** Are the three hooks registered when the plugin loads from its working copy?
- **2.3** Do the format hook and the stop gate fire in a real session inside a dev-team repo,
  and stay silent outside one?
- **2.4** Does the new `forbid` claim (every hook matcher and `agent_type` names a shipped
  agent) fail on a planted misspelling?

## Method

- **2.1** `python3 evals/fixtures/hook-events/check.py`. Each of the 47 recorded events is
  piped into its script as `hooks.json` runs it (`python3 <script>`), with
  `CLAUDE_PLUGIN_ROOT` set to the plugin and `CLAUDE_PLUGIN_DATA` set to a temp dir. The gate
  cases run in a fresh repo from `build.py`. That repo has one built section, a proposed
  deviation, and a trailer commit. The case table in the note has 38 rows once the ×8 rows are
  expanded. The fixture adds 9 more: an expired Exceptions row, a lowered threshold, a diff
  with no section, a top-level file before the surface design exists, an out-of-scope `cwd`
  for the guard, agent memory, and three role carve-outs. ruff 0.12.0, pytest 8.4.2, Python
  3.13.9. No API cost.
- **2.4** The plugin and `plugin-dev` were copied to the scratch directory, and
  `dev-team:implementor` was planted in two places: the `SubagentStop` matcher in
  `hooks/hooks.json` and `AGENT` in `hooks/gate_on_stop.py`. Then
  `contract_sweep.py --quiet` was run on the copy, and the full sweep on the working tree.
- **2.3** Run with `run-evals`. Iteration 1 had four executors: eval 1 and eval 2, each with
  `hooks/` kept and with `hooks/` deleted. Each executor copied the plugin to a scratch
  directory and swapped the matched agent for a stub. It built an in-scope repo and an
  out-of-scope repo with `evals/sets/files/hooks/build.sh`, and ran a real
  `claude -p --plugin-dir` session in each one. One skill-creator grader per run. Iteration 2
  reran eval 1 in both configurations on the fixed format hook, with the set's tightened
  expectations (see Verdict). Executor cost ≈ 69k–95k tokens per run, plus the nested
  sessions.
- **2.2** Proven headlessly rather than by an interactive `/hooks` listing (Deviation in the
  note). A `claude -p` session loaded the plugin with `--plugin-dir`, ran in a scratch repo
  built by `evals/sets/files/hooks/build.sh` with `--debug-file` and
  `--include-hook-events`, and was asked to Write one file.

## Results

| Row | Case | Expected | Observed | Pass |
|---|---|---|---|---|
| 2.1 | 6 `fmt-*` | out of scope untouched and silent; clean file unchanged; unused import removed; undefined name exit 2 naming the file; malformed exit 0 | as expected, e.g. `dev-team format hook: ruff check left these in packages/data/src/data/ingest/extra.py:` then `F821` | ✅ |
| 2.1 | 17 `gate-*` | per the note's table: marker, pass, tolerated, attempts 1/2/3, guarded, exception, constraints fail, measured, surface, malformed, out of scope; plus expired exception, lowered threshold, no section, surface before its design | 17/17. `TOLERATED intent tests/intent/ingest/test_loader.py::test_load_trades_price_is_float (data/ingest — 2026-09-27 — deviation)`. The counter goes 1 → 2 → absent. `FAIL guarded # noqa at packages/data/src/data/ingest/loader.py:3`. `FAIL surface: surface: FAIL \| - Trade: in interface.md Public names, not in README Public: yes rows …` | ✅ |
| 2.1 | 24 `guard-*` | one allowed and one refused path per role (×8); main thread, outside `cwd`, malformed, out-of-scope `cwd`; memory, implementer `interface.md`, implementer `docs/architecture.md`, architect `deviations.md` | 24/24 | ✅ |
| 2.1 | all | `check.py` exits 0 | `47/47 pass`, exit 0 | ✅ |
| 2.4 | plant | the claim FAILs on `dev-team:implementor` | `FAIL every hook matcher and agent_type names an agent this plugin ships  hooks/hooks.json:14, hooks/gate_on_stop.py:50`, `28/29 pass`, exit 1 | ✅ |
| 2.4 | clean | the claim PASSes without the plant | `29/29 pass` on the working tree, the new claim `0 matches` | ✅ |
| 2.3 | eval 1 · iteration 1 · with hooks | in scope: formatted, import gone, exit-2 text naming F821 reaches the model; out of scope: byte-identical, silent | 6/6. The relayed report carries `dev-team format hook: ruff check left these in packages/data/tests/intent/ingest/test_parse.py:` and `F821 Undefined name \`parse_row\``; out of scope, 0 hits for `hook`. The executor found a defect: the in-scope file starts with two blank lines and fails `ruff format --check` | ✅ (defect) |
| 2.3 | eval 1 · iteration 1 · without | nothing fires | 3/6: the out-of-scope controls pass, the in-scope file is untouched | — |
| 2.3 | eval 2 · iteration 1 · with hooks | stops 1 and 2 refused on the red intent test; released at stop 3; silent out of scope | 8/8. Two `Stop hook feedback` blocks (`attempt 1 of 3`, then `attempt 2 of 3` with `debugging-and-error-recovery`), relayed `done (stop 3)`. `gate.txt` shows attempt 3, PASS for lint, format and the green test, and one `FAIL intent …::test_load_trades_rejects_missing_field`. Out of scope: `done (stop 1)`, no `.dev-team` | ✅ |
| 2.3 | eval 2 · iteration 1 · without | nothing fires | 3/8 | — |
| 2.3 | eval 1 · iteration 2 · with hooks | as above, plus the file fully formatted and the Write carrying the original bytes | 7/7. The in-scope file starts `def test_parse_row():` and `ruff format --check` reports it already formatted. The grader found a second defect: the reported `5:12` was stale, since the final format moves the call to line 3 | ✅ (defect) |
| 2.3 | eval 1 · iteration 2 · without | nothing fires | 4/7: the controls pass, the in-scope checks fail | — |
| 2.2 | load | the three events have one dev-team hook each | Debug log: `Read hooks.json for plugin dev-team (enabled=true)`, `Loading hooks from plugin: dev-team` (the only plugin that loaded hooks), `Registered 3 hooks`. The stream shows `PreToolUse:Write` and `PostToolUse:Write` each `hook_started` and then `hook_response` with `exit_code: 0` on the main thread's Write; both scripts correctly treat the main thread as out of scope. `SubagentStop` fired in the real sessions of 2.3 eval 2 | ✅ |

## Verdict

Rows 2.1, 2.2 and 2.4 hold. `hooks/hooks.json` parses, and every `args` path exists under `hooks/`.

Row 2.3 holds: 100% with the hooks against 44% (iteration 1) and 57% (iteration 2) without.
The format hook fires only in scope. The gate refuses a red intent test twice and then lets
the stop through, and it is silent outside a dev-team repo. Two defects came out of the
behavioral runs, and both were fixed in `hooks/format_on_edit.py`:

1. The file was left unformatted after `check --fix`. Fixed by a second `ruff format`, and
   rerun as iteration 2.
2. The reported line numbers were stale. Fixed by a final `ruff check`, and pinned by the
   `fmt-unfixable` case. No set expectation reads line numbers, so the behavioral runs were
   not repeated for it.

The fixture reran at 47/47 after both fixes, and the sweep at 29/29.

Set corrections (`run-evals` step 7), made from the graders' critiques:

- **Eval 1.** Expectation 3 now asserts the fully formatted file; the old wording passed a
  file that fails `ruff format --check`. Expectation 4 also requires `import os` to be gone,
  since the old wording passed any file nothing touched. A new expectation says the Write
  carried the original bytes.
- **Eval 2.** Expectation 5 now requires that `gate.txt` exists with the one FAIL and the
  PASS lines, since its negative half passed when the gate never ran. Expectation 6 now
  pins exactly two refusals, and puts the attempt-3 text in `gate.txt`, because the exit-0
  stderr never reaches the agent (observed).

The eval-1 rewrite changed iteration 1's with-hooks verdict, so eval 1 was rerun as
iteration 2. The eval-2 rewrite changed no verdict.

Platform observations for `plugin-anatomy`'s `hooks.md` (not written back here; the ledger
records it as noticed):

- The stderr of a `SubagentStop` hook that exits 0 reaches neither the subagent nor the
  parent's stream.
- The stderr of a `PostToolUse` hook that exits 2 arrives in the model's tool result as
  `PostToolUse:Write hook blocking error …`.
