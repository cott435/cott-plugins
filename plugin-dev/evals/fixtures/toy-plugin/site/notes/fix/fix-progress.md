# toy fix — progress

Branch `toy-fix`. One row per phase of `fix-00-overview.md`. `run-phase` reads this file
first, does the first row that is not `done`, and fills the row in the same commit as the
phase. The Commit cell holds `(phase N)` until the next chat resolves it to a SHA.

Status values: `todo` · `in progress` (uncommitted paths listed under Notes) · `done`.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00 | done | fixture | — | none: phase 0 is plan-phases' commit |
| 1 | 01 | done | fixture | — | E-001 landed: greet now has `## Input` and `## Output` headings |
| 2 | 02 | todo | | | |
| 3 | 03 | todo | | | |

## Standing facts

- Every phase: its note (written by `run-phase` when the phase starts, unless it exists) →
  edits → the plugin's own rules → `check-contracts` → `build-site` → the phase's `## Evals`
  table run with `run-evals` and logged with `log-eval` → one commit
  `toy fix (phase N): …` → this file, in that commit.
