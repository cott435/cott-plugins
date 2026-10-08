# run-flow phase 1 — the moved trace scripts, the unit JSON and pages, the audit-run regressions, the bundle checks, and the skill's load

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `039fddf`): `skills/run-flow/scripts/trace.py`, `skills/run-flow/scripts/flow.py` (moved from `skills/audit-run/scripts/`), `skills/run-flow/SKILL.md`, `skills/audit-run/SKILL.md`, `evals/sets/audit-run.json` · model: none for M1.1–M1.4 (scripts); `claude -p` on the session default (`claude-opus-5-5`) for L1.1 · 2026-10-07
**Set:** `evals/sets/audit-run.json` evals 1, 3, 4 (M1.3); the rest are rows of `site/notes/0.16-audit-ledger-01-run-flow.md` **Evals** with no set · **Iteration:** none, run by hand in the phase chat · **Baseline:** for M1.2, `HEAD:plugin-dev/skills/audit-run/scripts/trace.py` (`039fddf`) · **Pass rate:** M1.1 7/7 · M1.2 4/4 files identical · M1.3 18/18 · M1.4 8/8 claims PASS, grep see below · L1.1 pass

## What was tested

That `trace.py build`, moved to `skills/run-flow/scripts/`, writes a full-step `units/U<nn>.json`
numbered exactly as the clipped `units/U<nn>.md`, that `flow.py` renders `units/U<nn>.html` from
it and links every box to it, that the auditors' files are byte-for-byte what the old script
wrote, that `audit-run`'s mechanical evals still pass with the new path, that the bundle's
contracts hold, and that `run-flow` registers when the plugin loads from its working copy.

## Method

- **M1.1.** `make_session.py $TMP` into a fresh `mktemp -d`, then `trace.py build` on the planted
  session; a script checked `units/U01.json`, `units/U01.html`, `flow.html` and `index.json`.
- **M1.2.** The committed `trace.py` and `flow.py` from `HEAD` copied to a temp directory and run
  on the same fixture; `diff` on `units/U01.md`, `units/U01.system.md`, `driver/seg-1.md` and
  `run.md`. Also run, beyond the pass bar: the flow fixture, the fork (`f0a0d17f`), and the real
  12-unit dev-team session `ca48b249` (`diff -r` excluding `*.json`/`*.html`), and on `ca48b249`
  every unit's `step_count` against its `.md` (0 mismatches; commit messages and files came from
  the project, e.g. U07's `365df53` with 13 files).
- **M1.3.** The three prompts of `audit-run.json` evals 1, 3, 4 run as written (new path), and
  each expectation checked by a script.
- **M1.4.** `python3 scripts/contract_sweep.py`, and the step-5 grep.
- **L1.1.** `claude --plugin-dir ./plugin-dev -p "List the skills you have from plugin-dev"` from
  the repo root.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M1.1 build | exits 0 | exit 0 | ✅ |
| M1.1 step count | `step_count` = lines starting `` - `U01.S `` | 8 = 8 | ✅ |
| M1.1 ids | `U01.S1…U01.S8` in order | yes | ✅ |
| M1.1 Write | whole `content` | `write.content` = input content, `a\n` | ✅ |
| M1.1 pytest | `output` has `1 failed, 3 passed` | yes | ✅ |
| M1.1 pages | `U01.html` has `1 failed, 3 passed` and `Returned`; `flow.html` has `href="units/U01.html"` | yes, both | ✅ |
| M1.1 index | U01 has `json` and `step_count` | `units/U01.json`, 8 | ✅ |
| M1.2 | `U01.md`, `seg-1.md`, `run.md` identical to HEAD's | identical (and `U01.system.md`, the flow session, the fork, and `ca48b249`) | ✅ |
| M1.3 eval 1 | 6 expectations | 6/6 | ✅ |
| M1.3 eval 3 | 6 expectations | 6/6 | ✅ |
| M1.3 eval 4 | 6 expectations | 6/6 | ✅ |
| M1.4 contracts | all PASS | 8/8 PASS, README table 13 names | ✅ |
| M1.4 grep | prints nothing | prints two lines, both historical (below) | ⚠ |
| L1.1 | names `run-flow` | listed `run-flow` ("Draws a workflow run's flow chart … with each agent's full record clickable") | ✅ |

**The grep.** As written, the note's filters (`grep -v '^./evals/20'` …) assume GNU grep's `./`
prefix; macOS grep prints paths without it, so nothing was filtered. With the prefix stripped
first, it prints two lines: `evals/sets/files/run-auditor/{prior-issues,no-prior-issues}.md:22`,
"(Before phase 1 of 0.16-audit-ledger the script was `skills/audit-run/scripts/trace.py`; this
set runs from phase 7, where it has moved.)" — phase 0's harness files, saying where the script
*was*. Not edited: outside this phase's Files, and true as history. A Deviation in the note.

## Verdict

Held. The move changed nothing an auditor reads, and every unit now has its full record and a
page. The only open item is the grep's two historical lines, recorded as a Deviation.
