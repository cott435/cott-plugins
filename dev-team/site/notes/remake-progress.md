# dev-team remake — progress

Branch `dev-team-remake`. One row per phase of `remake-00-overview.md`. `run-phase` reads
this file first, does the first row that is not `done`, and fills the row in the same commit
as the phase. The Commit cell holds `(phase N)` until the next chat resolves it to a SHA.

Status values: `todo` · `in progress` (uncommitted paths listed under Notes) · `done`.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00 | done | 8641af4 · 17823d2 | `2026-09-27-remake-platform-facts.md` (platform-fact runs in a scratch copy; no `run-evals` iteration) | PF-1–PF-4 hold as assumed. **PF-5 is false as stated**: a plain `git commit` holds no lock while its hooks run, so concurrent agents sweep each other's staged files into one commit and no error is raised. The fix, proven: `git add <paths>` then `git commit -m … -- <paths>`, which holds the lock, so the 2 s × 10 retry applies. See the overview's `## Deviations`. PF-1 finding: after a gate retry, the parent receives only the subagent's last turn. *noticed: write back to plugin-anatomy* (`hooks.md`): `SubagentStop` exit 2 continues the subagent and feeds the stderr in as `Stop hook feedback:` [proven]; `stop_hook_active` present on `SubagentStop` (false, then true on retries) [proven]; the full `SubagentStop` input key list, including `last_assistant_message` and `agent_transcript_path`; `${CLAUDE_PLUGIN_DATA}` for a `--plugin-dir` plugin is `~/.claude/plugins/data/<name>-inline/` and persists across sessions; the parent's Agent result is the last turn only; `agents.md`: main-thread parallel Agent calls with `run_in_background: false` in one message run concurrently and return together [proven]. |
| 1 | 01 | done | (phase 1) | `2026-09-27-remake-phase1-state-and-templates.md` (mechanical and load rows only; no `run-evals` iteration) | 36/36 state cases; 28/28 contracts. Four Deviations are in the note: eval 1.4's `next:` bar was checked on `status data`, since `--repo` has no `next:`; the probe-doc re-open rule ignores other sections' `## <pkg>/<section>` entries; the fixture has 36 cases with macros; and the status SKILL.md keeps one Floor/Enforced sentence for the existing claim. Every flag (`--run-gate`, `--rounds`, `--surface`, `--repo`) prints only its own output, with no package report. `status.py` also exports `clause_key(text)`, which matches a `Design §<n> <item>` docstring to a `Clause:`, plus `decisions()`, `open_spec_changes()`, `change_files()`, `package_table()`, `next_command()`, `run_gate()` and `surface_check()`. *noticed:* stale mentions of `--gate`/`--plan-gate` remain in `agents/implementer.md`, `set-constraints` references, `finalize-package`, `site/flow.md`, `site/workflows/new-repo.md` and `README.md`, each owned by a later phase. `package-contract.md` still says contract deviations go in the integration doc (phase 6), and that `plan-package` probes every source before designers (phase 3/6). |
| 2 | 02 | todo | | | PF-1 and PF-2 are logged and hold. From phase 0: the gate's exit-2 text must tell the agent to end with its full return message again, starting `Result:`, because the parent receives only the last turn. The gate's `git commit --amend --no-edit` must name its paths (`-- <paths>`), or it sweeps in files another agent has staged. The hook should delete `attempts-<agent_id>` when it lets a stop through, because the data dir persists across sessions. From phase 1: `status.py` exposes `clause_key()`, which the ledger-tolerance check can use for its docstring↔`Clause:` match. The constraints-headings claim still lists `skills/status/SKILL.md` as a reader, and its closing sentence cites Floor/Enforced. Re-point that reader to the hook, or drop it, when the hook lands. |
| 3 | 03 | todo | | | |
| 4 | 04 | todo | | | From phase 0 (PF-5 false as stated): the lock-retry rule is not enough on its own. §Project convention must also require `git commit -m … -- <paths>` (and `--amend --no-edit -- <paths>`). A plain `git commit` after `git add` sweeps in a parallel agent's staged files, and raises no lock error to retry on. The implementer's step 13 must restate the full return message after a gate retry. |
| 5 | 05 | todo | | | |
| 6 | 06 | todo | | | |
| 7 | 07 | todo | | | |
| 8 | 08 | todo | | | From phase 0: after a stop-gate retry, an implementer's Agent result is its last turn only. The driver's branch on the first line relies on phase 4's restate rule. |
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
