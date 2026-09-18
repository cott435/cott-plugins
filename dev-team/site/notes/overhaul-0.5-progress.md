# dev-team 0.5 overhaul — progress

Branch `dev-team-0.5-overhaul`. One row per phase of `overhaul-0.5-00-overview.md`. The
chat that finishes a phase fills in its row and commits it with the phase; the next chat
reads this file first and starts at the first row that is not `done`.

Status values: `todo` · `in progress` (list what is uncommitted under Notes) · `done`.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00, 09 | done | 3127526 (design set), f69b58b (evals A, B) | `evals/2026-09-18-platform-facts.md` | Resolved `subagent_type` form: **`dev-team:<agent>`** — bare `reviewer` errors. `${CLAUDE_PLUGIN_ROOT}` is substituted in skill and agent bodies. |
| 1 | 01 | done | 1b5b5f9 | `evals/2026-09-18-c-vendored-skills-js-stack-grep.md` | Upstream SHA `c004a74` (in each `.skillfish.json`). `git-workflow-and-versioning` §Project convention is a one-line placeholder for phase 2 to fill. README knowledge-scope rows for the three are all `—` until phases 2/4 wire them into agents — fill the cells then. Re-run eval C over the fourth file in phase 6. Deviations in note 01. |
| 2 | 02 | done | the `(phase 2)` commit (`git log --grep="(phase 2)"`) — includes the parallel session's foreground fan-out fix | `evals/2026-09-18-d-commit-per-run.md`, `evals/2026-09-18-d2-foreground-fanout.md` | **Skills now fork `agent: dev-team:<name>`; before this, every forked agent ran as general-purpose (d2).** Re-check whether the per-skill "commit, then return" steps are still needed (note 02 §Deviations). Fixture built (`evals/fixtures/two-package/`, `reset.sh [--no-constraints] [dest]`; set `git config user.name/email` in the copy before headless runs). Forked skills now end "commit, then return" — the note's "no skill change" failed eval D. Headless `plan-package` now finishes (d2). Reviewer commit and `Commit:` line not yet exercised live. Deviations in note 02. |
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
