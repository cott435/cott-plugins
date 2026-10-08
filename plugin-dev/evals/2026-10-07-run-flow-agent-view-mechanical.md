# run-flow phase 2 — `trace.py view`, `--branch`, the per-session and cross-session agent pages, and audit-run evals 3 and 4 with the flow session's new id

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `86c7637`): `skills/run-flow/scripts/trace.py`, `skills/run-flow/scripts/flow.py`, `evals/fixtures/audit-run/make_session.py`, `evals/sets/audit-run.json` · model: none (scripts, checked by script) · 2026-10-07
**Set:** `evals/sets/audit-run.json` evals 3, 4 (M2.3); M2.1 and M2.2 are rows of `site/notes/0.16-audit-ledger-02-agent-view.md` **Evals** with no set · **Iteration:** none, run in the phase chat · **Baseline:** none; for the extra regression check, `HEAD:plugin-dev/skills/run-flow/scripts/{trace,flow}.py` (`86c7637`) · **Pass rate:** M2.1 10/10 · M2.2 4/4 · M2.3 13/13

## What was tested

That `trace.py view` builds each named session into its own `<id8>/` workspace and writes one
cross-session page listing every run of one agent type in time order, each row linking to a
unit page that exists; that `--branch` selects sessions by their git branch and fails cleanly
on no match; that `find` shows each session's branch; that every `build` now writes
`agents/<role>.html` and a `mode` on each unit; and that audit-run's flow-chart and find evals
still pass now that the fixture's flow session has its own id (`0f10d17f…`) and branch (`flow`).

## Method

- A fresh `mktemp -d` per run, `make_session.py $TMP`, then the note's commands as written,
  with `AUDIT_RUN_PROJECTS=$TMP`.
- A checker script parsed the view and agent pages' tables (headers, rows, links) and resolved
  every link on disk. A second ran `audit-run.json` eval 3's prompt verbatim (new path) and
  eval 4's steps, checking each expectation.
- Beyond the pass bar:
  - **Regression.** HEAD's `trace.py` and `flow.py` built both fixture sessions beside the
    working tree's. `diff -r`, excluding `*.json`, `*.html` and `agents/`, found the auditors'
    files (`run.md`, `units/*.md`, `driver/`) identical. `index.json` differs only by the
    added top-level `title` and the per-unit `mode`.
  - **The design's slice.** `build ca48b249 --plugin dev-team` on the real session wrote
    `agents/profiler.html` with U01 `profile`, U04 `verify`, U06 `profile`, U08 `verify`, in
    that order. The output went to the scratchpad.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M2.1 exit | `view … --sessions 0a0d17f0-…fixt,0f10d17f` exits 0 | exit 0; prints the page path, then `0a0d17f0 · Ship the toy file · feature · 1 unit of writer` and `0f10d17f · (untitled) · flow · 3 units of writer` | ✅ |
| M2.1 page | `$TMP/audit/views/writer-2026-10-07.html` | written | ✅ |
| M2.1 columns | Session … Returned, the note's 12, in order | exact | ✅ |
| M2.1 rows | 4 writer rows: `0a0d17f0` U01; `0f10d17f` U01, U02, U04, in time order | exact; starts 10:00, 11:01, 11:01, 11:09 | ✅ |
| M2.1 links | every unit link resolves | 8 links (unit and session), all exist | ✅ |
| M2.1 link form | `../<id8>/units/U<nn>.html` | yes | ✅ |
| M2.1 Mode | `—` on every row | yes | ✅ |
| M2.1 agent pages | `0f10d17f/agents/writer.html`, `agents/reviewer.html` | both; writer 3 rows (U01, U02, U04), reviewer 2 (U03, U05), links resolve; `flow.html` links both under **By agent type** | ✅ |
| M2.1 mode key | every `0f10d17f/index.json` unit has `mode` | yes | ✅ |
| M2.2 branch | `--branch 'fl*'` builds only `0f10d17f`, 2 reviewer rows | only `0f10d17f/` (plus `views/`); U03, U05 | ✅ |
| M2.2 no match | `--branch nomatch` exits 1, `no session of toy on a branch matching nomatch` | exactly that; nothing written | ✅ |
| M2.2 find | `feature` and `flow` beside the projects | `/tmp/toy-project · flow · …`, `/tmp/toy-project · feature · …` (×2, the chat and its fork) | ✅ |
| M2.3 eval 3 | 6 expectations | 6/6 (+ the command exits 0) | ✅ |
| M2.3 eval 4 | 6 expectations | 6/6 | ✅ |
| Regression | auditors' files identical to HEAD's | identical for both fixture sessions | ✅ |

## Verdict

Held. The view and both kinds of agent page are right on the fixture and on the real
ca48b249 session: its profiler page is the design's smallest slice. The trace files the
auditors read are unchanged.
