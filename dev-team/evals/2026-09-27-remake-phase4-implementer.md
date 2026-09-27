# remake phase 4 — implementer

**Tested against:** uncommitted — see working-tree diff, on `6d928e5` (`agents/implementer.md`, `skills/git-workflow-and-versioning/SKILL.md`, `skills/workspace-scaffold/SKILL.md`, `contracts.yml`) · model: `claude-sonnet-5` for every executor and grader (`site/notes/CLAUDE.md`) · 2026-09-27
**Set:** `evals/sets/implementer.json` evals 1–10 · **Iteration:** `evals/workspace/implementer/iteration-1` · **Baseline:** `6d928e5` (`old_skill`) · **Pass rate:** 93.0% vs 80.7% overall; evals 1–8 91.7% vs 91.7%; evals 9–10 100% vs 35.7% · **Blind:** not run (overall rates 12 points apart)

## What was tested

- **4.1** — does `check-contracts` pass on the rewritten implementer, the new §Project convention and
  the re-pointed claims, and does a planted `git add -A` in `agents/implementer.md` fail the staging claim?
- **4.2** — does the rewrite keep the 2026-09-16 security-review behavior (evals 1–8, regression)?
- **4.3** — does the implementer log an unimplementable internal design clause as one `proposed`
  `deviation` entry cited by heading (eval 9)? Does it meet an unrecorded contract/README
  contradiction on a consumed signature with an open `spec-change:contract` entry, the `.dev-team/stop`
  marker and `Result: spec-change`, editing nothing it does not own (eval 10)?
- **4.4** — does the agent register when the plugin loads from its working copy?

## Method

- **4.1** `python3 ../plugin-dev/scripts/contract_sweep.py` on the working tree; then the same on a
  scratch copy with `Run \`git add -A\` first.` planted in the implementer's **Commit** section.
- **4.4** `claude --plugin-dir ./dev-team -p "List the agents you have from dev-team, one name per
  line, nothing else"` from the repo root.
- **4.2/4.3** `run-evals`: one executor per eval and configuration, 20 in one message, each a
  general-purpose subagent given the agent file (proxy: the agent's `tools:` and `skills:` are not
  reproduced; a skill "invoked" means its `SKILL.md` was read). `with_skill` read the working tree,
  `old_skill` the snapshot at `6d928e5`; plugin skills were read from the working tree in both. The
  executor prompt named the eval's `eval_metadata.json` for the prompt text, not an inline copy. No hook
  ran, so no stop gate. One grader per run (skill-creator's `grader.md`). One run per configuration.
  About 2.9M executor tokens and 2.1M grader tokens.

## Results

| Row | Case | Expected | Observed | Pass |
|---|---|---|---|---|
| 4.1 | sweep | all PASS | 30/30 | yes |
| 4.1 | planted `git add -A` | staging claim FAILs | `FAIL no agent or skill stages everything agents/implementer.md:567` | yes |
| 4.4 | load | `implementer` listed | 8 agents, `implementer` among them | yes |
| 4.2 | eval 1 auth/login | with ≥ old | 5/5 vs 4/5 (old: a timing side-channel under a "cannot enumerate" README claim) | yes |
| 4.2 | eval 2 data/ingest | | 5/5 vs 5/5 | yes |
| 4.2 | eval 3 models/loader | | 4/5 vs 4/5 (with: a recorded `grep` whose output does not reproduce; old: an error message that interpolates payload data under a "fixed strings" claim) | tie |
| 4.2 | eval 4 export endpoint | | 5/5 vs 5/5 | yes |
| 4.2 | eval 5 resample | | 3/4 vs 3/4 (with: expectation 2, see below; old: a four-sentence verdict against a three-sentence cap) | tie |
| 4.2 | eval 6 format | | 3/4 vs 4/4 (with: expectation 2, see below) | no |
| 4.2 | eval 7 shared/types | | 4/4 vs 4/4 | yes |
| 4.2 | eval 8 indicators | | 4/4 vs 4/4 | yes |
| 4.2 | evals 1–8 | ≥ 87.5% and ≥ old | 33/36 = 91.7% vs 33/36 = 91.7% | yes |
| 4.3 | eval 9 clean deviation | with every expectation; old fails the `proposed` entry | 7/7 vs 3/7 (old: no `docs/deviations.md`, deviation restated in README item 7) | yes |
| 4.3 | eval 10 storage spec-change | with every expectation; old fails the marker | 7/7 vs 2/7 (old: adapted to `CleanResult`, a README "Deviation", `Result: done`, no marker) | yes |

**Expectation 2 of evals 5–8** ("security-review's SKILL.md body was never opened"). Three executors read
the file past its frontmatter while orienting, before their Security step: `with_skill` evals 5 and 6
and `old_skill` eval 6. The two `with_skill` runs said so in their transcripts and failed. The
`old_skill` run said so only in its hand-back message and passed, since graders see the transcript and
outputs, not the tool calls. The Security step's wording is identical in both versions. So the eval 6
gap (and eval 5's matching miss) measures executor candor, not the target. The expectation was reworded
to what is observable — no body-only content in `transcript.md` or `outputs/` — and the set's `note`
says so. Both `with_skill` transcripts name "1. Secrets Management", so neither verdict changes and
nothing was rerun.

Graders' other critiques, not acted on (none calls an expectation vacuous):
- The evals 5–8 sentence cap is brittle.
- Evals 1–4 expectation 4 polices security claims only. A false plain `ruff check` result sat beside
  true ones in eval 4 `with_skill`, and a lint claim needing `--select B` in eval 1 `with_skill`.
- Evals 9 and 10 share one cause across four expectations on the baseline.
- Eval 10's "plus whatever code was built" is unexercised when the run stops before code.

## Verdict

- All four rows hold.
- **4.2**: 91.7% on evals 1–8, above the 87.5% of 2026-09-20 and equal to the baseline in this run. The
  one eval where the baseline scored higher is the expectation-2 measurement artifact above.
- **4.3**: every expectation passes for the rewrite. The baseline has no ledger and no marker, and fails
  both, as the bar requires.
- The consumed-side rule behaved as the note intends: the rewrite stopped at step 5 before any storage
  code, where the baseline built against the README.
