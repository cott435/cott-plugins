# dev-team remake — progress

Branch `dev-team-remake`. One row per phase of `remake-00-overview.md`. `run-phase` reads
this file first, does the first row that is not `done`, and fills the row in the same commit
as the phase. The Commit cell holds `(phase N)` until the next chat resolves it to a SHA.

Status values: `todo` · `in progress` (uncommitted paths listed under Notes) · `done`.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00 | in progress | (phase 0) | | The notes, sets and ledger are committed. Still to run, from the design's Platform facts table (`assumed` rows), each logged with `log-eval` and written back to `plugin-anatomy` as a *noticed:* line: **PF-1** `SubagentStop` exit 2 prevents the subagent from stopping and its stderr reaches it (a stub `dev-team:implementer` under a scratch hook that exits 2 once then 0; the transcript shows a second turn after the stderr). **PF-2** the loop guard: a marker file lets the stop through; a counter under `${CLAUDE_PLUGIN_DATA}` keyed by `agent_id` persists across the same agent's stop attempts; `stop_hook_active` is present in the input. **PF-3** main-thread parallel Agent calls in one message run concurrently and all return as that message's results (two `dev-team:designer` spawns writing to a scratch dir). **PF-4** `ls ${CLAUDE_PLUGIN_ROOT}/skills` from an agent body lists the plugin's skills and a colliding project skill is reported. **PF-5** two parallel agents committing collide on `.git/index.lock` and the retry rule (2 s, up to 10) lands both commits. If PF-1 is false, phase 2 cannot be built as designed: stop and tell the user. Mark this row `done` when all five are logged. |
| 1 | 01 | todo | | | |
| 2 | 02 | todo | | | Needs PF-1 and PF-2 logged |
| 3 | 03 | todo | | | |
| 4 | 04 | todo | | | |
| 5 | 05 | todo | | | |
| 6 | 06 | todo | | | |
| 7 | 07 | todo | | | |
| 8 | 08 | todo | | | |
| 9 | 09 | todo | | | May pair with 10 |
| 10 | 10 | todo | | | May pair with 9 |
| 11 | 11 | todo | | | Ends with the bump proposal in chat (minor, `0.7.0`); `bump-version` runs only on a yes |

## Standing facts

- Run every phase in Claude Code from the repo root with the plugin loaded from its working
  copy (`claude --plugin-dir ./dev-team`) and `plugin-dev` installed.
- Every phase: edits → the plugin's own rules (`CLAUDE.md`'s three-file rule until phase 10,
  two-file rule after) → `check-contracts` → `build-site` → the phase's `## Evals` table run
  with `run-evals` (stopping for review when a row is behavioral) and logged with `log-eval` →
  one commit `dev-team remake (phase N): …` → this file, in that commit.
- Deviations from a note go under a `## Deviations` heading at the end of that note, in the
  same commit.
- Consistency, not releasability, at each boundary before phase 11 (overview).
