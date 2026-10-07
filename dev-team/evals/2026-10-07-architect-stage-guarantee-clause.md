# Architect — a marked row ends with a guarantee, and the stage line names its standards

**Tested against:** uncommitted — see working-tree diff of `skills/planning-templates/references/package-contract.md` (the `source` paragraph), `README.md` (**Data-heavy sections**), `site/workflows/add-package.md` and `site/workflows/new-repo.md` on branch `dev-team-2.8-audit-fixes` (base `d2fa85d`, dev-team 2.8.0); `agents/architect.md` unchanged since `8af9221` · model: `claude-sonnet-5-5` (executors, graders and comparators) · 2026-10-07
**Set:** `evals/sets/architect.json` evals 1, 10 · **Iteration:** `evals/workspace/architect/iteration-1` · **Baseline:** `d2fa85d` (dev-team 2.8.0, the committed tree) · **Pass rate:** eval 1 100% (8/8) vs 100% (8/8); eval 10 90.9% (10/11) vs 81.8% (9/11) · **Blind:** new preferred 2/2

## What was tested

That an architect given the new `stage` paragraph writes (a) a `guarantees …` clause at the end of the marked row's `responsibility` cell, stating what is true of the section's output and naming no treatment, and (b) a `judged against <standards>` field in the `stage:<token>` **Package conventions** line, between `lands at` and `pull cap`; and that nothing else in a contract write changed.

## Method

Real runs, not a proxy: one executor per configuration per eval (`with_skill` = the working tree, `old_skill` = `git archive` of `d2fa85d` minus `evals/`), each a general-purpose subagent given the executor prompt of `run-evals`, the eval's prompt and its scripted-answer harness. One run per cell, so no variance estimate. One grader per run, and, because eval 1 passed everything on both sides and eval 10's rates are 9 points apart, one blind comparator per eval over `outputs/` only. All agents on `sonnet` (Sonnet 5.5). Held constant: fixture, harness, prompt, model. Varied: the template and README text the executor read from its own plugin root. `agents/architect.md` is the same file in both configurations.

Eval 10 gained two expectations in this change (set edit, `note_guarantee`): the `clean` row's `responsibility` ends in a `guarantees` clause with none of `repair`, `drop`, `quarantine`, `discard`, `flag` used as a treatment; and the stage line holds a `judged against` field that names a standard. Eval 1 is unchanged and tests that an ordinary contract write did not regress. Eval 7's baseline is `dev-team-v2.5.0`, so it cannot share an iteration with these two and was not run.

Cost, from the completion notices: 4 executors 110k–121k tokens each, 115–191 s; 4 graders 69k–77k; 2 comparators 69k–72k.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Eval 1, new template | the 2.8.0 contract write unchanged | 8/8 | pass |
| Eval 1, baseline | same | 8/8 | pass |
| Eval 10, new template, 4 of 11 (stage line shape) | one `stage:` line: what the data is, `lands at`, `pull cap <n> <unit>, D<n>` | `pull cap 5,000 requests (the full universe over 2016–2025, 2,000 a day on the Research plan), D1`: a parenthetical sits between the unit and `, D1` | **fail** |
| Eval 10, new template, 5 of 11 (guarantee clause) | `responsibility` ends `guarantees …`, no treatment | "guarantees every bar it hands on passes every check and every failing row is kept with its reason" | pass |
| Eval 10, new template, 6 of 11 (`judged against`) | field between `lands at` and `pull cap` naming a standard | names the brief's clean-and-validate clauses and `docs/sources/barfeed.md` | pass |
| Eval 10, baseline, 5 of 11 | same as above | `responsibility` ends "a failing row is set aside with its reason in a rejects file beside the clean bars and the run goes on; defines `Bar`": a treatment, no `guarantees` | **fail** (expected) |
| Eval 10, baseline, 6 of 11 | same as above | the line goes from `lands at …` straight to `pull cap 2,000 requests, D1` | **fail** (expected) |
| Eval 10, the other 8 of 11, both configurations | skeleton, marking, D1 shape, no agent call, return | held in both | pass |
| Blind, eval 1 | — | new template won, 9.7 vs 8.7: `clean` returns a `CleanResult` that `storage` takes, rejects stored in a table, the surface row has an interface block, the cap is tied to the probe. Margin small, and nothing in the change explains it | new |
| Blind, eval 10 | — | new template won, 9.4 vs 7.7: the two fields above; a second decision (D2, resuming a 3-day pull) that follows from the quota | new |

## Verdict

The claim held: the new template produced the guarantee clause and the `judged against` field, the 2.8.0 template produced neither, and nothing else in the contract changed enough to fail an expectation. Eval 1 shows no regression in an ordinary write.

What this does not show:

- **One run per cell.** The eval 10 gap is two expectations in one run each. A rerun could land either side of them, so it is evidence the template works, not a rate.
- **The one failure on the new side is expectation 4**, written in 2.7 and not changed here: the parenthetical before `, D1`. It tracks the template's literal `pull cap <n> <unit>, D<n>` and nothing in the plugin parses the line, so it is cosmetic; the expectation is left strict and was not loosened to turn it green. The baseline passed it, so this is a one-sample difference, not a shown regression.
- **The new side added `DATA_CLEAN_DIR`**, a setting the baseline's own D2 flagged as a repo-contract change. The comparator could not check it. The harness answers do not cover it.
- **Grader notes on the set, not acted on:** eval 1 expectation 3 passes when `storage` also lists `ingest`; the architect's transcripts are prose summaries, so "no Agent call" rests on the executor's account plus the absence of files; eval 1 has no check that **Call paths** frames resolve to an interface or pipeline entry. None of these is about this change.
- **Not run:** eval 7 (`dev-team-v2.5.0` baseline), the other seven evals of the set, and any run against a real contract such as `quant-rebuild`'s `identity` row.
