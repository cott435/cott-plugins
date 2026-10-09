# Gap answers go to the edit list when there is one

**Tested against:** uncommitted — see working-tree diff over `f579768` (`skills/plan-phases/SKILL.md`, `templates/review/edits.md`, `templates/phases/design.md`) · model: Opus 5.5 (by hand, no executor) · 2026-10-09

## What was tested

With a design and an edit list in one plan folder, `plan-phases` writes a gap answer into one
**Decisions taken** table, the edit list's, and the three files that say where answers go agree.

## Method

Mechanical, by hand: the contract sweep; a read of the three changed passages side by side;
`edits.py show` on the toy `fix` list, to confirm a decision row with the item in its Items cell
prints beside that item. No behavioral run: the change is where one sentence sends a row.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `contract_sweep.py` | all pass | 15/15 | yes |
| plan-phases, edits template, design template | each names the edit list as the home when both exist, the design's table kept as approved | as expected | yes |
| `edits.py show fix-edits.md E-002` | prints D-01's row after the item | "D-01: … Items: E-002 …" | yes |

## Verdict

Held. Not run: `plan-phases` eval 2 (`gap-asked-not-guessed`), which has a design only and is
unaffected by this sentence's edit-list branch.
