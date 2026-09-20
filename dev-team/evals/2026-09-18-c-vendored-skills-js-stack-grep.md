# C — vendored skills carry no JS-stack text

**Tested against:** uncommitted — see working-tree diff (phase 1 of the 0.5 overhaul; the three
files below are new in that commit) · upstream `addyosmani/agent-skills` at `c004a74` · model:
`claude-opus-5` (ran the grep; no agent involved) · 2026-09-18

Files under test:

- `skills/test-driven-development/SKILL.md`
- `skills/debugging-and-error-recovery/SKILL.md`
- `skills/git-workflow-and-versioning/SKILL.md`

The fourth vendored file, `skills/set-constraints/references/constraint-driven-development.md`,
does not exist until phase 6; this eval is re-run over it then (note 09 §C).

## What was tested

Note 09 eval C: no skill vendored from `agent-skills` still carries JavaScript-stack text or
the upstream constraints file name — the pattern
`npm|jest|describe\(|it\(|eslint|@ts-ignore|CONSTRAINTS\.md` hits only `## Provenance` lines,
if anything.

## Method

Mechanical. `grep -nE` with the pattern above over each of the three adapted files, and again
with `-i` so `Jest`/`NPM` capitalizations are caught too. Positive control: the same `grep -cE`
over the upstream originals at `c004a74`, to show the pattern fires on the text the adaptation
was supposed to remove. No model cost.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `test-driven-development` (adapted) | 0 hits outside Provenance | 0 hits anywhere (case-sensitive and `-i`) | ✓ |
| `debugging-and-error-recovery` (adapted) | 0 hits outside Provenance | 0 hits anywhere (case-sensitive and `-i`) | ✓ |
| `git-workflow-and-versioning` (adapted) | 0 hits outside Provenance | 0 hits anywhere (case-sensitive and `-i`) | ✓ |
| control: upstream `test-driven-development` | > 0 | 24 lines | ✓ |
| control: upstream `debugging-and-error-recovery` | > 0 | 12 lines | ✓ |
| control: upstream `git-workflow-and-versioning` | > 0 | 3 lines | ✓ |
| control: upstream `constraint-driven-development` (phase 6's source) | > 0 | 25 lines | ✓ |

## Verdict

Holds: zero hits in all three adapted files, and the controls show the pattern would have
caught the upstream text. `check-contracts` passed 9/9 in the same working tree (all three
`names_listed` claims include the new directories: 24 skills listed). Re-run in phase 6 with
the fourth file added.
