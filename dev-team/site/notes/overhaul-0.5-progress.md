# dev-team 0.5 overhaul — progress

Branch `dev-team-0.5-overhaul`. One row per phase of `overhaul-0.5-00-overview.md`. The
chat that finishes a phase fills in its row and commits it with the phase; the next chat
reads this file first and starts at the first row that is not `done`.

Status values: `todo` · `in progress` (list what is uncommitted under Notes) · `done`.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00, 09 | done | 3127526 (design set); see phase-0 eval commit | `evals/2026-09-18-platform-facts.md` | Resolved `subagent_type` form: **`dev-team:<agent>`** — bare `reviewer` errors. `${CLAUDE_PLUGIN_ROOT}` is substituted in skill and agent bodies. |
| 1 | 01 | todo | | | |
| 2 | 02 | todo | | | Build `evals/fixtures/two-package/` first (note 09) — every later eval uses it |
| 3 | 03 | todo | | | |
| 4 | 04 | todo | | | |
| 5 | 05 | todo | | | |
| 6 | 06 | todo | | | |
| 7 | 07 | todo | | | |
| 8 | 08 | todo | | | |
| 9 | 09 | todo | | | Ends with the bump proposal in chat; `bump-version` runs only on a yes |

## Standing facts

- Run everything in Claude Code from the repo root with `--plugin-dir ./dev-team` and
  `plugin-dev` installed. Commits made from a Cowork session leave `.git/*.lock` files that
  must be moved out by hand (`_to_delete/git-locks/` holds the first batch).
- Every phase: edits → three-file rule → `check-contracts` → `build-site` → the phase's
  evals logged with `log-eval` → one commit `dev-team 0.5 (phase N): …` → this file.
- Deviations from a note are recorded in that note under a final `## Deviations` heading
  (what the note said, what was done, why), in the same commit.
