# <plugin> <slug> — progress

Branch `<plugin>-<slug>`. One row per phase of `<slug>-00-overview.md`. `run-phase` reads
this file first, does the first row that is not `done`, and fills the row in the same
commit as the phase. The Commit cell holds `(phase N)` until the next chat resolves it to a
SHA.

Status values: `todo` · `in progress` (uncommitted paths listed under Notes) · `done`.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00 | <done; or in progress when the design assumed facts> | (phase 0) | | <the platform-fact evals still to run, from the design's assumed facts; or "none: phase 0 is plan-phases' commit"> |
| 1 | 01 | todo | | | |
| N | 0N | todo | | | Ends with the bump proposal in chat; `bump-version` runs only on a yes |

## Standing facts

- Run every phase in Claude Code from the repo root with the plugin loaded from its working
  copy (`claude --plugin-dir ./<plugin>`) and `plugin-dev` installed.
- Every phase: edits → the plugin's own rules → `check-contracts` → `build-site` → the
  phase's `## Evals` table run with `run-evals` (stopping for review when a row is
  behavioral) and logged with `log-eval` → one commit `<plugin> <slug> (phase N): …` → this
  file, in that commit.
- Deviations from a note go under a `## Deviations` heading at the end of that note, in the
  same commit.
