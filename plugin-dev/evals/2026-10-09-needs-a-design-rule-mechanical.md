# One rule for "Needs a design", stated alike everywhere

**Tested against:** uncommitted — see working-tree diff over `ae49093` (`README.md`, `skills/review-plugin/SKILL.md`, `skills/review-plugin/references/reconcile-prompt.md`, `templates/review/edits.md`, `skills/design-plugin/SKILL.md`, `site/workflows/review-sweep.md`) · model: Opus 5.5 (by hand, no executor) · 2026-10-09

## What was tested

That every file saying when a review item goes to `design-plugin` states the same rule (a new
workflow, a new agent with its own loop, or a new file two workflows meet at; a hook, script
flag or record file inside an existing loop stays an edit), that the empty case leads straight
to `plan-phases`, and that the README no longer offers `design-plugin` for any "change too big
for one chat".

## Method

Mechanical: the contract sweep; a whitespace-normalized grep for the two rule phrases in each
of the six files; a grep for the retired README wording. No behavioral run: wording only.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `contract_sweep.py` | all pass | 15/15 | yes |
| three-part rule in README, review-plugin, reconcile prompt, edits template, design-plugin, review-sweep page | 6 of 6 | 6 of 6 | yes |
| "hook, script flag or record file … is an edit" | the five files that decide or place items | 5 of 5 (design-plugin only designs what is listed) | yes |
| "change too big for one chat" in README | 0 | 0 | yes |

## Verdict

Held. Not run: review-plugin eval 1 (its toy sweep has no Needs-a-design case either way).
