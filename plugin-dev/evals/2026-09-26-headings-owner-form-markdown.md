# `headings` gains `owner_form: markdown`, so the design template owns the design's section list

**Tested against:** uncommitted — see working-tree diff on branch `phase0-and-design-template` (from `73013a4`) · Claude Code 2.1.270 · model: `claude-opus-5-5` · 2026-09-26
**Set:** none (mechanical) · **Iteration:** none · **Baseline:** n/a · **Pass rate:** n/a

## What was tested

`design-plugin`'s `SKILL.md` listed the design's eleven sections and `templates/phases/design.md`
repeated them as headings. The list was dropped from the skill, and the template became the
owner of the `headings` claim that `plan-phases` reads against. For that, the shared
`contract_sweep.py` learned to read a template's own `##` headings (`owner_form: markdown`),
skipping fenced code. The claim must still pass on the real bundle and fail on each defect.

## Method

`python3 scripts/contract_sweep.py .` on the working tree, then four temp copies:
(1) `## Build order` renamed to `## Build plan` in the template; (2) that copy plus a
`## Build order` line inside a fenced block appended to the template; (3) the default,
numbered-bold form broken instead, by renaming `**mechanical**` in `eval-kinds.md`;
(4) every `## ` in the template demoted to `### `.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Real bundle | 7/7 | 7/7 | ✅ |
| (1) renamed section | FAIL naming the reader | `skills/plan-phases/SKILL.md names 'Build order'` | ✅ |
| (2) name only inside a fence | still FAIL | same FAIL; the fenced heading is not counted | ✅ |
| (3) default form | FAIL, unchanged behavior | `…run-evals/SKILL.md names 'mechanical'; …plan-phases/SKILL.md names 'mechanical'` | ✅ |
| (4) no `##` headings | FAIL, not a silent pass | `templates/phases/design.md: no \`##\` headings found in the owner span` | ✅ |

## Verdict

Held. The design's sections now live in one file, and the claim follows that file.
