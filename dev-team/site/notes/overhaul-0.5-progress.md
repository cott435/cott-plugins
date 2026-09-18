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
| 3 | 03 | done | the `(phase 3)` commit (`git log --grep="(phase 3)"`) | `evals/2026-09-18-e-order-of-authority-sync-design.md` | Both authority lists have six items. Phase 6 adds `docs/constraints.md` to **both** at the top, and must re-run eval E's mechanical script (the script is in the eval log's Method). `check-contracts` can't see backticked-path items, so the script is the real check. The reviewer's item 1 already names rule (d), "intent test failing with no follow-up", for phase 4. `review-package` now ends at `/dev-team:sync-design`, so phase 8's driver runs it last. Watch in phase 9: sync-design wrote a `Note:` paragraph outside its template, and the reviewer may file a missing listed test as a second CRITICAL beside an unrecorded deviation. Deviations in note 03. |
| 4 | 04 | done | the `(phase 4)` commit (`git log --grep="(phase 4)"`) | `evals/2026-09-18-f-tester-intent-reconcile.md` | Eight agents; `test-section` forks `dev-team:tester`. The tester's `docs/constraints.md` input row is left for phase 6. `test-section` already has the `run-package` `Section:`/`Plan:` paragraph, so phase 8 should match its wording. `status.py` intent column: `uv run` only with a `uv.lock`, else `python3 -m pytest`, from the root, with no bytecode (the first version dirtied the tree). `site/workflows/new-repo.md` loop already has `test-section`; phase 9 still rewrites it for spine-first. Watch in phase 9: the reconcile run checked the baseline after editing; the tester lists the package tree with `find`, which shows section file names; agents put prose in the commit body beside the trailer (pre-existing); untracked `__pycache__/` never tripped the baseline rule. Deviations in note 04. |
| 5 | 05 | done | the `(phase 5)` commit (`git log --grep="(phase 5)"`) | `evals/2026-09-18-g-review-plan-replan-gate.md` | `review-plan` forks `dev-team:reviewer`; `status.py --plan-gate <pkg>` exists, and so does the `plan:` line. Phase 7's **Spine** item: `spine_only()` matches a `**Spine**` item or a `# Spine` heading and reads `spine only` anywhere before the next numbered bold item or heading, so write the status on a line inside that item. Phase 8's driver: the plan gate already fails on an uncommitted `docs/packages/<pkg>/` edit, on an open `D` with no assumption scoped repo/pkg/pkg-section, and on an open `<pkg>/plan` finding. Same-day re-reviews are `-2`, `-3` (reviewer Output, `latest_review`). A `plan-package` re-run whose designs are all current and has no findings commits nothing and skips step 8 (eval G run 1b). Watch in phase 9: a re-delegated designer also fixes things no finding named ("non-follow-up alignment"); integration §6 isn't refreshed when only one design is re-delegated; commit bodies still carry prose. Deviations in note 05. |
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
