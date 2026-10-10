# `plugin-anatomy` — the driver as the shape of every workflow: two new behavioral evals, working tree vs `350892c`

**Tested against:** uncommitted — see working-tree diff, on `350892c` (`skills/plugin-anatomy/SKILL.md`, `skills/plugin-anatomy/references/composition.md`, `references/edge-cases.md`) · model: executors and graders on `claude-sonnet-5-5` (`S init`'s default, recorded in the manifest) · 2026-10-10
**Set:** `evals/sets/plugin-anatomy.json` evals 11, 12 · **Iteration:** `evals/workspace/plugin-anatomy/iteration-1` · **Baseline:** `350892c` · **Pass rate:** 13/14 (92.9%) vs 13/14 (92.9%)

## What was tested

That with the driver moved to the front of `plugin-anatomy` — a **What a plugin is for**
section in `SKILL.md` before the routing questions, and `references/composition.md` rewritten
around the driver's loop, the ledger and the hooks that hold a run — a model asked to design
a multi-step workflow (eval 11), or to fix an orchestrating skill that reads its own plan
(eval 12), answers with a thin driver in the main thread, a script that prints where the run
stands, a script-written ledger and plugin hooks. And that the baseline, which already had
the driver as the last section of `composition.md` and one paragraph in `SKILL.md`, does
this less completely.

## Method

Real runs through `eval_workspace.py run`: one executor per configuration per eval (4
headless sessions) and one grader per run, all on Sonnet 5.5, one sample each. Both evals are
new in this change (`added_in: driver shape`), so nothing was reused. `with_skill` read the
working tree; `old_skill` read the snapshot at `350892c`. Mechanical checks first:
`contract_sweep.py` 15/15, `eval_workspace.py validate` on both set files exit 0,
`build_site.py` 71 pages exit 0.

Two things about what the working-tree executors read. Both opened `SKILL.md` at 17:49:37–38
and `composition.md` and `edge-cases.md` right after (their `session.jsonl`); `SKILL.md` was
edited once more at 17:49:47, while they ran: routing question 4 gained "keep a run going"
beside "need the user", and the intro paragraph was rewrapped. So the run is of the working
tree without that one sentence. And eval 12's fifth expectation was tightened after the run,
on its grader's remark (below); the grades here are against the earlier wording.

Cost: executors 950,113 tokens, $1.16; graders 831,334 tokens, $0.63; wall time 57 s.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 11 `workflow-designed-driver-first`, working tree | a driver-first design, all 8 expectations | 8/8. Opens by classing the workflow with **How much driver a workflow needs** ("the whole shape"); a typed driver with `disable-model-invocation`, three agents with closed return statuses, one script with `next`, `slice`, `finish` and `wait`, a written ledger in the project with `finish` as its one writer, three scoped plugin hooks (`SubagentStop`, `PreToolUse` by `agent_type`, `Stop`), a revision cap of 2, resume in a new chat | ✅ |
| 11, baseline `350892c` | the same | 7/8. Failed only "at least one must-hold rule is a plugin hook in `hooks/hooks.json`": the design had the driver, the script and the ledger and named no hook | — |
| 12 `driver-reads-the-plan`, working tree | all 6 expectations | 5/6. Names three anti-patterns by their headings (a driver that reads the plan, a driver that does the work, a ledger written by hand), moves next, the completeness check and the tick into `plan.py next` and `plan.py finish`, adds a `SubagentStop` gate and batches of 20. Failed expectation 1: it wrote "Reads plan.md (grows with 60 papers, re-read every turn)", which puts the growth on the plan and never says the driver's own context is the cost | ❌ |
| 12, baseline `350892c` | the same | 6/6. Said outright "its context grows every loop, and every wake re-reads it"; otherwise the same three script moves, with a hook offered only as an "if" | — |

Graders on the expectations: eval 11's first passes on a design where "the driver spawns the
agents" is implied by the loop rather than stated (left as it is: the loop line names the
spawn); eval 12's fifth passed on "path + status" alone without saying the driver acts on
the status, so it now reads "starts with a status from a closed list … and the answer says
the driver acts on that status".

## Verdict

The claim held in part, and the two evals do not separate the versions by count: 13/14 each.

What changed is visible in the answers, not the totals. With the working tree both answers
are built from the shape — the loop, the ledger's one writer, a hook per "must", the size
table, resume from files — and cite the new sections by name; the baseline reached the
driver, the script and the ledger from the one section it had, and left hooks out of the
design (eval 11) or optional (eval 12). That is the one expectation only the baseline
failed.

The one expectation only the working tree failed is a real gap in that answer and not a
grading accident: a reader of it would move the plan into a script without learning that the
driver's context is what they are paying for. The skill states it in three places
(`SKILL.md` rule 1, **What the driver holds**, the new `edge-cases.md` row), so this is one
sample compressing its diagnosis, and nothing was changed in the skill for it. One sample
per side cannot say more; if the rate matters, rerun eval 12 with three runs a side.

Not tested: the two new should-trigger queries and the one should-not in
`plugin-anatomy.trigger.json` (no trigger loop was run on the widened description), and
`design-plugin` with its two new lines about the driver (its set was not rerun).
