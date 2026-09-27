# remake phase 5 — reviewer

**Tested against:** uncommitted — see working-tree diff, on `a4be52e` (`agents/reviewer.md`, `contracts.yml`) · model: `claude-sonnet-5` for every executor, `claude-haiku-4-5` for every grader (`site/notes/CLAUDE.md`, as amended at the start of this phase) · 2026-09-27
**Set:** `evals/sets/reviewer.json` evals 1–4 · **Iteration:** `evals/workspace/reviewer/iteration-1` (evals 1–4) · `evals/workspace/reviewer/iteration-2` (evals 1, 2, `with_skill` only; `old_skill` copied from iteration 1) · **Baseline:** `a4be52e` (`old_skill`) · `evals/workspace/reviewer/iteration-3` (eval 2, `with_skill` only) · **Pass rate:** iteration 1 95.5% vs 45.5% (mean per eval); iteration 2, evals 1–2: 86% vs 41%; iteration 3, eval 2: 73% vs 55% · **Blind:** not run (rates 50 points apart)

## What was tested

- **5.1** — does `check-contracts` pass with the new review-report claim counted, and does a
  planted `cites: ['Carried on']` fail it?
- **5.2** — does the rewritten reviewer write one report named `-r<n>-<letter>` in the
  template's shape, with a full Coverage table in round 1 (eval 1), a diff-scoped round 2 with
  **Carried**, `Convergence:` and an out-of-diff finding demoted to a `— noted` backlog line
  (eval 2), a `spec-change` verdict with a `spec-change:contract` entry when the contract is the
  wrong document (eval 3), and a `defer` run that moves the standing CRITICALs to the backlog
  and approves (eval 4) — all without running a command?
- **5.3** — does the agent register when the plugin loads from its working copy?

## Method

- **5.1** `python3 ../plugin-dev/scripts/contract_sweep.py` on the working tree; then with the
  review-report claim's reviewer cites changed to include `Carried on`; then, as a second probe,
  with `**Floor**` bolded inside the reviewer's order-of-authority span. Each plant reverted.
- **5.2** `run-evals`, one run per configuration. Proxy runs: a general-purpose subagent given
  `agents/reviewer.md` (or the `a4be52e` snapshot's) and the eval prompt, so the preloaded
  skills are not loaded. The harness supplies every command's result and forbids running any.
  Executors on Sonnet, graders on Haiku. Two grader summaries were arithmetically wrong (eval 1
  with_skill counted 10 expectations of 11; eval 1 old_skill claimed 4 passes of 3 marked true)
  and were recomputed from their own expectation arrays; one grader wrote
  `execution_metrics: null`, set to `{}` so the aggregator runs.

## Results

**5.1**

| Case | Expected | Observed | Pass |
|---|---|---|---|
| working tree | all PASS | 31/31 | ✓ |
| planted `Carried on` | review-report claim FAILs | `FAIL … agents/reviewer.md names 'Carried on'`, 30/31 | ✓ |
| planted `**Floor**` in the authority span | order-of-authority claim FAILs | `FAIL … agents/reviewer.md names 'Floor'`, 30/31 | ✓ |

**5.2, iteration 1**

| Eval | with_skill | old_skill | with_skill misses |
|---|---|---|---|
| 1 round-1 conformance | 10/11 | 3/11 | an eighth `## Deviations` heading in the report |
| 2 round-2 full | 10/11 | 6/11 | three backlog lines appended where one was expected: the new calendar.py finding plus two WARNINGs round 1 had already raised |
| 3 spec-change | 7/7 | 3/8 | — |
| 4 defer | 8/8 | 5/8 | — |

`old_skill` fails the report file name (evals 1, 3: `2026-09-27-data-clean.md`) and the
`Focus:` line (evals 1, 3). It does not fail the no-command rule: the harness forbids every
command for both configurations, so the baseline could not show it. Watch: eval 2's
`with_skill` executor ran `status.py --rounds` once against the plugin checkout, then discarded
the output for the supplied fact. Expectation 9's command list does not name `status.py`, so
it passed. The new body's **Report** section invited the check ("the command is right").

**Set correction between iterations** (user's yes): `status.py` added to the forbidden-command
list of every no-command expectation (evals 1–4). Under it, iteration 1's eval-2 `with_skill`
run fails expectation 9. Evals 1, 3 and 4 `with_skill` never ran it (their transcripts only quote
the supplied fact), so their verdicts stand.

**The one fix** (`agents/reviewer.md`): no heading beyond the template's seven; the round-2+
backlog takes only WARNINGs **Severity** demoted (outside `Diff:`, raised by no previous report);
`Round:` taken as given, `status.py --rounds` only when the prompt has no `Round:` line.

**5.2, iteration 2** (evals 1 and 2, `with_skill` only)

| Eval | with_skill | Misses |
|---|---|---|
| 1 round-1 conformance | 11/11 | — |
| 2 round-2 full | 8/11 | no calendar.py weekend fill found, so no WARNING (exp 5) and no backlog line for it; one other demoted finding went to the backlog (exp 6). The `fill_gaps` finding is `unfixed` under **Carried**, but **CRITICAL** is `- none` and the commit reads `(0 critical)`: exp 4 regraded FAIL by the phase chat, since the grader passed it on the Carried line alone |

Eval 2 ran no command this time. It reported both round-1 WARNINGs again under **WARNING** and
did not backlog them, as the fix intended.

**Second fix** (user's call, after the bar was missed): **Focus: full** step 2 says an
`unfixed` prior finding also stands as a line under **CRITICAL**, worded the same.

**5.2, iteration 3** (eval 2, `with_skill` only): 8/11. `fill_gaps` is under **CRITICAL**,
commit `review data/clean: r2-s: request changes (1 critical)`, `Convergence: 1 prior unfixed, 0
new`, no command run. The three misses (exp 5, 6, 11) are one miss: calendar.py's weekend fill
not found, so no WARNING, no backlog line and no `docs/followups.md` to stage. The transcript
says it looked for out-of-diff findings and found none. Across three round-2 runs the finding
was made once.

**5.3**

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `claude --plugin-dir ./dev-team -p "List the agents…"`, `claude-sonnet-5` | `dev-team:reviewer` listed | eight agents listed, `dev-team:reviewer` among them | ✓ |

## Verdict

5.1 and 5.3 hold. 5.2 missed its bar and was committed on the user's yes. Evals 1, 3 and 4
pass every expectation (eval 1 after the first fix). Eval 2's empty-**CRITICAL** defect is fixed
(iteration 3). What remains is the out-of-diff calendar.py finding, made in 1 of 3 round-2 runs.
The round-2 rule scopes judgment to the diff, so an untouched defect that round 1 missed is found
by chance. Recorded in the note's Deviations.
