# Two routes to `plan-phases`: `design-plugin` by workflow, `revise-plugin` by agent and skill, and `fix-issues` routed by a script

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-planning-routes` over `894e4f7` (`skills/revise-plugin/` renamed from `skills/review-plugin/`, `skills/design-plugin/`, `skills/fix-issues/SKILL.md`, `skills/audit-run/SKILL.md`, `scripts/issues.py`, `templates/phases/design.md`) · model: none for the mechanical cases; executors and graders on `claude-sonnet-5-5` (`S init`'s default, recorded in each manifest) · 2026-10-10
**Set:** `evals/fixtures/issues/check.py` (20 cases) · `evals/sets/fix-issues.json` eval 3 · `evals/sets/design-plugin.json` evals 5, 6 · `evals/sets/revise-plugin.json` eval 1 · **Iteration:** `evals/workspace/{fix-issues,design-plugin,revise-plugin}/iteration-1` · **Baseline:** none, not run (working tree only) · **Pass rate:** fixture 20/20; fix-issues 7/7; design-plugin 18/19; revise-plugin 9/10

## What was tested

Four claims about the planning skills after the change:

1. `issues.py route` gives a selection of audited issues to `fix-issues` (exit 0) or to
   `revise-plugin` (exit 3) on fixed numbers: more than six issues, more than three issues
   across more than three roles, or an issue that recurred after two fixes.
2. `fix-issues`, typed on a selection the script gives to `revise-plugin`, prints the route
   line and the command and stops, with no plan, no worktree and no edit.
3. `design-plugin`, typed on a change that adds and redraws no workflow, says it is not a
   design and names the other skill before any round; and a design it does write names each
   workflow's driver, where the run stands, each agent's returns and what holds it.
4. `revise-plugin`, the renamed `review-plugin`, still runs its toy sweep end to end.

## Method

Mechanical, no model: `python3 evals/fixtures/issues/check.py` builds a throwaway plugin and
calls `issues.py` as a chat would; its nine new cases cover each route rule on both sides of
its limit, an unknown id, and an empty selection. The thresholds were first tried on
`dev-team`'s real ledger (78 issues): the open and recurred set is 38 issues over 8 roles,
one audit's issues are 28 over 7, and two issues that name four roles between them route to
`fix-issues`. Also run on the edited bundle: `contract_sweep.py` 15/15,
`evals/fixtures/phases/check.py` 56/56, `eval_workspace.py validate` on every set exit 0,
`build_site.py` 71 pages exit 0.

Behavioral, real runs through `eval_workspace.py run`, working tree only, one executor and
one grader per eval, all on Sonnet 5.5, one sample each. No baseline ran: fix-issues 3 and
design-plugin 6 are new and their point is the new behavior; design-plugin 5 and
revise-plugin 1 are regression rows. Nothing under `skills/`, `scripts/` or `templates/` was
edited while the runs were in flight.

Cost: executors 2,562,909 tokens, $2.37; graders 1,204,745 tokens, $0.92; the longest run
269 s.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `issues.py route`, fixture | each rule exits 3 past its limit and 0 at it; one issue naming four roles is `fix-issues`'; an unknown id exits 1 | 9/9 new cases, 20/20 in all | ✅ |
| fix-issues 3 `route-large-selection` | nine open issues over five roles: the table, `issues.py route --status open,recurred`, the `route: revise-plugin` line, the command, a stop | 7/7. No issue file opened after the route call, no question, no branch, no `issues.py fix` | ✅ |
| design-plugin 6 `not-a-workflow-goes-to-revise` | read the toy plugin, say the change is not a design, name the other skill, stop | 6/6. "This is not a design. Nothing is being added or redrawn": named `fix-issues` for the two issues and `revise-plugin` as "the next size up"; no round, no page, no branch | ✅ |
| design-plugin 5 `trading-through-writeup`, the 12 earlier expectations | unchanged from before | 12/12 | ✅ |
| design-plugin 5, the new expectation: every workflow has Driver, Where the run stands, Returns and Held by lines | all four lines in each of three workflows, Returns covering every agent spawned | Driver, Where the run stands (`run.py next <workflow>`, `research/ledger.tsv`) and Held by (`SubagentStop` running `run.py check`) in all three. `portfolio-review`'s Returns lists `position-checker` and `ranker` and leaves out `filing-reader` and `news-scout`, which it also spawns | ❌ |
| revise-plugin 1 `toy-sweep-finds-planted-contradiction`, expectations 2–10 | the review plan, one message per wave, findings checked, the edit list checked with `--decided` and `--findings`, the planted contradiction as an item, no plugin file edited, three kinds of commit, `plan-phases` named | 9/9 | ✅ |
| revise-plugin 1, expectation 1: a goal question asked, the units shown as a table and approved, before any spawn | as worded | Failed as worded. A headless session has no question tool: the executor recorded both questions in `outputs/interview.md` with the sheet's answers, before the first spawn, and wrote the units in its transcript as one line; the plan's Units table is there (expectation 2) | ❌ |

## Verdict

Claims 1, 2 and the first half of 3 held. The second half of 3 held in part, and 4 held
apart from an expectation that could not pass in this harness.

- **design-plugin 5.** The design template asked for returns "for each agent the driver
  spawns", and one workflow of three listed only the agents new to it. The template line now
  reads "one entry for every agent in this workflow's chart, an agent another workflow also
  spawns included". Not rerun.
- **revise-plugin 1, expectation 1.** Its 2026-10-09 run passed it with Agent-tool
  executors; a headless executor can only record a question, and the grader said so. The
  expectation now asserts what a run leaves: both questions in `interview.md` with the
  sheet's answers, before the first spawn, and the units as a table in the review plan. Not
  rerun against the new wording. Nothing in it is about the rename: the nine expectations
  about what the skill does passed under the new name.
- **fix-issues 3.** Its grader noted that "unchanged from the fixture" rested on the
  executor's word; the sheet now asks for `git status --porcelain` in `outputs/` and the
  expectation reads it. Not rerun.

Not tested: `fix-issues … --here` going on to plan a selection the script gave away;
`revise-plugin <slug> issues run:<id8>` resolving a selection through `issues.py list`
(setup step 4); `audit-run`'s last step printing the route line (its evals 5 and 6 were not
rerun); design-plugin 1 with its new driver-in-the-chart expectation.
