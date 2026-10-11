# The split by file and the notes written with the plan — `edits.py split`, `phases.py notes-check`, a brief beside a note

**Tested against:** uncommitted — see working-tree diff, on `ac200a3` (3.0.0) with `87ab5ea` cherry-picked (`scripts/edits.py`, `scripts/phases.py`, `skills/plan-phases/`, `skills/run-phase/SKILL.md`, `templates/phases/`, `contracts.yml`, `site/site.yml`) · model: none · 2026-10-10
**Set:** `python3 evals/fixtures/phases/check.py` (71 cases, 14 of them new) · **Iteration:** none · **Baseline:** none · **Pass rate:** 71/71 cases; the real plan's split, briefs and note check as below

## What was tested

Why a 38-phase plan built in series took 20 to 45 minutes a phase when each phase's spec was
two sentences, and whether the planning that opened every phase can be done once, side by
side, before any phase runs. Read from the determinism plan's edit list, overview and
transcripts (phases 20–23, sessions `740962f9` and `c7937d09`): every phase note recorded 12
to 16 decisions its agent took itself; one phase's items named 28 fixture cases and its agent
wrote 97; the dependency graph the plan declared was 10 levels deep for 38 phases, with up to
10 phases in one level that collided on the hub files (`agents/implementer.md` in 20 phases,
`status.py` in 19).

1. `edits.py split`: items in dependency levels from `depends:`; the items of a level that
   cite one region of a file not shared in one phase; small clusters packed to a cap (a hook
   or script item weighs 3, any other 1); a cluster over the cap cut into a sequence; each
   phase depending on the owners of what its items depend on; the Level column the planning
   wave.
2. `edits.py coverage` with a Level column: no region of a file not shared owned by two
   phases of one level; the overview's `**Shared files:**` line read.
3. `phases.py notes-check`: every note there with the template's sections in order, its Evals
   rows the overview's for the phase unchanged, no two notes of one level listing a file not
   shared.
4. `phases.py brief` beside a note that exists: the note named as the plan, the items block
   dropped unless `--items`; the other phases on the phase's files listed before and after.
5. The skills, templates, contracts and flow block agree with each other.

## Method

No model. `check.py` builds a third toy repo: a six-item edit list with `depends:` lines, two
prose items on neighbouring lines of one file, one on the shared README, three hook items on
one file; an overview with Level and Files columns and a `**Shared files:**` line; a ledger;
notes written in the template's shape and then broken one way at a time. Then the commands
on dev-team's real determinism plan at `86ce32c` (phase 28 done), from a worktree, with the
plugin's own shared files named: `split` at four caps, `brief --phase 25` (a note exists) and
`--phase 30` (none), `notes-check`.

## Results

| Case | Result | Pass |
|---|---|---|
| `split` on the toy list | 3 phases in 2 levels: `E-001, E-003` (prose, 2) and `E-004, E-005, E-006` (the hook items on one file, 9) side by side at level 0; `E-002` at level 1 depending on 1 | yes |
| `split --cap 6` | the hook cluster cut: `E-004, E-005` at level 0, `E-006` at level 1 depending on it, `E-002` at level 2; 4 phases in 3 levels | yes |
| `split --cap 2` | an item over the cap on its own is warned, not dropped | yes |
| `coverage` on the toy overview | ok; phase 4 moved to level 0 beside phase 1 (both on `skills/hello/SKILL.md:5`): `FAIL phases 1 and 4 are both level 0 and both own …`; the file named on `**Shared files:**`: ok again | yes |
| `notes-check` | no notes: one line each, exit 1; a loosened pass bar and a note missing Steps: two FAILs, nothing else; two level-0 notes listing one file: FAIL, the shared README not; all whole: `ok: 4 notes checked`; an Evals row the overview lacks: FAIL | yes |
| `brief --phase 1` beside a note | names the note as the plan, prints no items, lists phase 4 on its file under After, none under Before; `--items` prints them | yes |
| `brief` with no note | says so and prints the items with their lines, as before; the other phases on its files listed | yes |
| the 57 earlier cases | unchanged | yes |
| the determinism list: `split --shared 'evals/fixtures/*/README.md' --shared tests/test_scripts.py` | 33 phases in 15 levels, the widest level 7 phases, at cap 9; 26 in 12 at cap 12; 22 in 11 at cap 15; 47 in 20 at cap 6. The hand-written plan: 38 phases, run as 38 levels. 86 of 152 items declare no `depends:`; their largest cluster by exact region overlap weighs 43 (the closed-form returns, by role) and is cut into 9 phases in sequence, which is how the hand plan laid it out too | yes |
| the determinism list, `--near 30` | 3 clusters at level 0, one of weight 89: proximity, not overlap, chained the hub files; the default is 0 | yes |
| the determinism plan: `brief --phase 25` (its note exists, one item) | 30 KB, naming the note and the earlier and later phases on its files; `--items` 35 KB; `--phase 30` (no note, five items) 89 KB with the items | yes |
| the determinism plan: `notes-check` | `not ok: 29 notes checked, 92 problems`: 8 notes missing (30–37); 83 Evals rows that are not the overview's or are missing from a note, nearly all in phases 2 and 5–18, whose rows the overview renumbered after they were written (`5fbac89`), and phases 21–22's `R*.c`, amended on `bb1239e`; one cell differing (phase 17's Set evals); no section out of order | yes: every line true, and every one a change made to the overview after the note |
| `check-contracts`, the flow check, `build-site` | 15/15; all passed; clean | yes |

## Conclusion

Held, for what a script can show: the split by file is computable from the list's own
fields, the one-owner rule is checkable before and after the notes are written, and a phase
whose note exists reads a brief without the items block (30 KB for phase 25, against 89 KB
for a five-item phase with no note). The phase count does not fall much
at the same cap (33 against 38): the plan's weight is its weight. What falls is the planning
inside each phase, moved to 15 waves of planners run side by side, and the eight minutes of
reading each phase spent finding its own lines.

Not tested: `plan-phases` itself on this version — its three behavioral evals were rewritten
for the notes and not run; a planner's note against a real phase; the unify agent;
`run-phase` building from a note it did not write. All of that is unproven until a plan is
planned on 3.1. The cap of 9 is phase 23's weight, chosen because that phase took 23 minutes
with its planning included; the right cap for a phase that only builds is unknown.
