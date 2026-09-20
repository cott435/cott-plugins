# Trigger rates rerun on the finished branch — and what a rerun of an unchanged description measures

**Tested against:** the five automatic skills' descriptions as of `29b317b` (`check-contracts`, `build-site`, `new-plugin` unchanged since; `log-eval` last touched `2f256ed`, `run-evals` `2f256ed`) · skill-creator `run_eval.py` from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · model: `claude-opus-5` · 2026-09-20
**Set:** `evals/sets/{log-eval,build-site,check-contracts,new-plugin,run-evals}.trigger.json` (20 queries each) · **Iteration:** `evals/workspace/trigger-p7/` (gitignored) · **Baseline:** phase 2's rates (`2026-09-19-trigger-rates-automatic-skills.md`) · **Trigger rate:** 1.00 · 1.00 · 0.90 · 1.00 · 0.95 — four of five within 0.05 of phase 2

## What was tested

P7-T1 of `site/notes/0.9-evals-07-release.md`: each automatic skill's held-out trigger
accuracy is within 0.05 of its phase-2 result. Measurement only — the note says this phase
does not optimize, so `run_eval` was run and `run_loop` was not, and no description was
changed.

## Method

Real runs, the method phase 2 established: a scratch project in the session scratchpad with
its own `.claude/` and `{"enabledPlugins": {"plugin-dev@cott-plugins": false}}`, each skill
in turn, `--num-workers 1 --runs-per-query 3 --model claude-opus-5`, all 20 queries (no
holdout, since nothing is being optimized). Run serially in the background while the
behavioral executors were still going, which is why it took ~25 minutes rather than ~12.

## Results

| Skill | Phase 2 | Phase 7 | Δ | Within 0.05 | should / should-not |
|---|---|---|---|---|---|
| `log-eval` | 0.95 | **1.00** | +0.05 | ✅ | 10/10 · 10/10 |
| `build-site` | 1.00 | **1.00** | 0.00 | ✅ | 10/10 · 10/10 |
| `check-contracts` | 1.00 | **0.90** | −0.10 | ❌ | 8/10 · 10/10 |
| `new-plugin` | 1.00 | **1.00** | 0.00 | ✅ | 10/10 · 10/10 |
| `run-evals` | 0.90 | **0.95** | +0.05 | ✅ | 9/10 · 10/10 |

`check-contracts`' two misses, both should-trigger:

- "I added a skill to plugin-dev but I'm not sure README's skills table is updated — is
  there a check for that in the bundle?" — 0/3.
- "after editing the log-eval skill, check the plugin's contracts and tell me which
  file:line fails" — 1/3.

`run-evals`' one miss: "the phase note says to run P3-B1 on plan-phases; run it and stop for
my review" — 0/3.

## Verdict

Four of five held. `check-contracts` missed the bar, **and it is not a regression.**
`git diff 29b317b HEAD -- skills/check-contracts/SKILL.md` is empty: the description is
byte-identical to the one that scored 20/20 in phase 2, measured with the same set, the same
method and the same model. All ten should-not-trigger queries still pass, so nothing widened
and the guard holds. Both misses are from the pair that scored 0/3 *before* phase 2's hand
rewrite — the historically fragile queries, which sit near the decision boundary and fall
either side of it between runs.

**The finding is about the instrument, not the plugin.** At `--runs-per-query 3` a
20-query trigger rate moves ~0.10 between identical runs, so P7-T1's "within 0.05" band is
tighter than the measurement's own repeatability: the bar can fail on sampling alone, as it
did here. Recorded as a Deviation in note 07. The honest options for a future bar are more
runs per query (cost scales linearly — 3→9 runs is ~900 `claude -p` calls for five skills)
or a band wide enough to admit the noise, around ±0.10; a third is to score only the
should-not half strictly, since the guard is what the scoping clause exists to protect and
it has never moved.

No description was changed by this phase.
