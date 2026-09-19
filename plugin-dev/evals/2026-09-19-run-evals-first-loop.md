# `run-evals` — first use of the loop: workspace helper checks, and `plan-phases` 0.8 against 0.7.0 reproduced through it

**Tested against:** uncommitted — see working-tree diff (`skills/run-evals/`, `contracts.yml`; branch `plugin-dev-0.9-evals` at `c76777a`). Target `skills/plan-phases/SKILL.md` at `c76777a`; baseline `plugin-dev-v0.7.0` (`25a018f`) · skill-creator from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · model: `claude-opus-5` (executors and graders are general-purpose subagents) · 2026-09-19

**Set:** `evals/sets/plan-phases.json` · **Evals:** 1, 2, 3 · **Iteration:** `evals/workspace/plan-phases/iteration-1` (gitignored) · **Baseline:** `old_skill` at `25a018f` · **Pass rate:** with_skill 45/48 (94%), old_skill 12/48 (25%)

## What was tested

That `run-evals`, followed exactly as written on its first use, runs a behavioral eval end to
end on skill-creator's grader, benchmark and viewer, and reproduces the result the same
three briefs got by hand in `2026-09-19-plan-phases-compose-layers.md` (47/48 vs 12/48). Plus
the mechanical checks on its helper and its contract.

## Method

- **Contract** — `contract_sweep.py` on the bundle; then two planted defects: `` `smoke` ``
  added to SKILL.md's kinds line (the note's check), and `**platform-fact**` unbolded in
  `eval-kinds.md`'s list. Both reverted.
- **P1-M1** — `eval_workspace.py validate evals/sets/plan-phases.json`; `init`, and after
  P1-B1's grading, `aggregate_benchmark` on the iteration.
- **P1-M2** — a copy of the set with eval 2's `expectations` emptied and eval 3's `kind` set
  to `smoke`, validated, then deleted.
- **P1-B1** — `init . plan-phases --evals 1,2,3 --baseline plugin-dev-v0.7.0`; six executors
  spawned in one message with SKILL.md's executor prompt verbatim; `timing` from each
  completion notice; one grader per run with the grader prompt verbatim plus one added
  sentence (below); `finalize`; `aggregate_benchmark`; the viewer. One run per
  configuration. Cost: executors 505k tokens (with_skill 288k, old_skill 216k), graders
  ~412k — ~0.92M in all.

## Results

| Check | Expected | Observed | Pass |
|---|---|---|---|
| contracts, real bundle | 4/4 PASS incl. the new claim | 4/4 PASS — "5 names across 1 readers, all owned" | yes |
| planted `` `smoke` `` in SKILL.md | new claim FAILs naming the line | **still PASS** — a `cites` list is literal in `contracts.yml`; the checker never reads SKILL.md for it, and a reader `span` only parses capitalised `**Bold**` names | **no** |
| `platform-fact` unbolded in eval-kinds.md | new claim FAILs | FAIL "skills/run-evals/SKILL.md names 'platform-fact'", exit 1 | yes |
| P1-M1 validate | exit 0 | exit 0 (also `run-phase.json`) | yes |
| P1-M1 aggregate | non-zero pass rate for both configs | with_skill 94.0%, old_skill 25.0% | yes |
| P1-M2 | exit 1 naming both | `eval 2: behavioral eval has no expectations`; `eval 3: kind 'smoke' is not one of …`; exit 1 | yes |
| P1-B1 with_skill | ≥ 90% | 45/48 = 94% (15/16 each brief) | yes |
| P1-B1 old_skill | ≤ 40% | 12/48 = 25% (trading 3, papers 5, support 4) | yes |

P1-B1 per brief (with / old): trading 15/16 vs 3/16, papers 15/16 vs 5/16, support 15/16 vs
4/16. All three with_skill misses are the same expectation, "Core stands without
suggestions": the release phase depends on "all above" (or "5, 6 if accepted"), which takes
in the suggestion phases; on trading, a suggested reviewer also appends to a core file. The
0.8.0 hand run's one miss was different (a missing "must cite" rule) — one run each, so
this is the same skill landing on a different weak spot, not a regression.

Timing (benchmark): with_skill 253 s / 96k tokens, old_skill 120 s / 72k tokens per run.

Found while running the loop, fixed in this change:

- The grader copies `timing` into `grading.json` (as `grader.md` says), which hides
  `timing.json` from `aggregate_benchmark`'s token count — tokens read 0 or
  `output_chars`. Added `eval_workspace.py finalize <iteration>`, which drops the copy;
  the benchmark then read 72k / 96k correctly.
- `aggregate_benchmark`'s delta is `configs[0] − configs[1]` alphabetically, so against
  `old_skill` it prints −0.69 for a +0.69 improvement. Documented; read the rows.
- The served viewer rendered empty (no prompt, no outputs; console `SyntaxError: Invalid or
  unexpected token`): `generate_review.py` inlines outputs into a `<script>` with
  `json.dumps`, and each with_skill run's `proposal.html` contains `</script>`. Added
  `eval_workspace.py review`, which runs the viewer unmodified with `</` escaped; it then
  rendered all 6 runs. The E0.4 static file has the same defect in its content — it was
  generated, which is what E0.4 asked, but would render empty too.
- The set's expectations name `chat.md`, which the verbatim executor prompt never asks for
  (the final message goes in `transcript.md`). Every grader was told one extra sentence:
  grade the chat expectation against the final message at the end of `transcript.md`.

Grader critique of the expectations (loop step 7), not yet applied to the set:

- "no ```mermaid fence in chat" and "chart ≤ ~25 nodes" pass for a baseline that produced
  no page at all — tie them to `proposal.html`.
- "Core stands without suggestions" should name its two leak patterns (a core phase
  depending on a suggestion phase, even conditionally; a suggestion writing to or into a
  file a core component reads).
- "Chart and table agree" should run both ways.
- Nothing checks that the run interviewed in rounds and stopped at the approval point
  without writing to the repo (all six did).

## Verdict

Held on every pass bar: the loop ran end to end as written, and reproduced 0.8.0's result
(94% vs 25%, against 98% vs 25% by hand). One check did not hold: the note's planted
`smoke` defect cannot fail the `headings` claim as the checker works today — see the note's
Deviations. The set's `chat.md` mismatch and the grader's critique are left for the set's
owner (phase 3 edits `plan-phases.json`'s wording rules); the note said this phase
validates the set and does not edit it. User review of the viewer: done; the user approved the
commit. "Submit All Reviews" produced no `feedback.json` (no POST reached the server), so no
written comments were acted on.
