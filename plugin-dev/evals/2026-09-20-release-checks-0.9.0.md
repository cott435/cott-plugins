# Release checks for 0.9.0 — contracts, set validation, and the bundle's load check

**Tested against:** uncommitted — see working-tree diff (`README.md`, `CLAUDE.md`, `CHANGELOG.md`, `site/workflows/*.md`, `skills/run-phase/SKILL.md`) · model: `claude-opus-5` · Claude Code `claude --plugin-dir` · 2026-09-20
**Set:** `evals/sets/*.json` and `*.trigger.json` in `plugin-dev` and `dev-team` · **Iteration:** — (mechanical) · **Baseline:** — · **Pass rate:** P7-M1 held; P7-L1 held in substance, bar's wording missed

## What was tested

P7-M1 and P7-L1 of `site/notes/0.9-evals-07-release.md`. **P7-M1:** `check-contracts` is all
PASS and `eval_workspace.py validate` exits 0 on every committed set in both plugins.
**P7-L1:** the branch's bundle loads and its skills register.

## Method

Real runs. `contract_sweep.py` from `plugin-dev/`; `validate` over the eight `plugin-dev`
sets and the three `dev-team` sets in one invocation each. Because a checker that cannot
fail is worth nothing (this plugin's own `CLAUDE.md`), `validate` was also given two planted
defects — a behavioral eval with `expectations` removed, and a trigger query with
`should_trigger` removed — to confirm the exit 0 is meaningful. For P7-L1, `claude
--plugin-dir ./plugin-dev -p` from the repo root, with the installed 0.8.0 bundle as a
control, plus a direct invocation of each typed skill.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `check-contracts` on `plugin-dev` | all PASS | 4/4 — bare commands, README skills table (8 names), site.yml order (2 typed), eval-kinds (10 names, 2 readers) | ✅ |
| `validate` on `plugin-dev/evals/sets/*.json` + `*.trigger.json` | exit 0 | exit 0, silent, 8 files | ✅ |
| `validate` on `dev-team/evals/sets/*.json` | exit 0 | exit 0, 3 files | ✅ |
| *negative control:* set with `expectations` removed | exit 1 | exit 1 — `eval 1: missing 'expectations'`, `behavioral eval has no expectations` | ✅ |
| *negative control:* trigger query with `should_trigger` removed | exit 1 | exit 1 — `query 1: 'should_trigger' must be true or false` | ✅ |
| `check-contracts` after the `run-phase` edit | still 4/4 | 4/4 | ✅ |
| `build-site` after the `run-phase` edit | builds | 24 pages · 3 workflows · 3 workflow skills · 8 knowledge · 9 notes | ✅ |
| P7-L1: `-p "List the skills you have from plugin-dev"` | names all eight | names **six** — the six automatic ones, incl. `run-evals` | ⚠️ see below |
| *control:* same prompt against installed 0.8.0 (7 skills, 2 typed) | — | names five — the five automatic ones | ✅ |
| P7-L1: `/plugin-dev:run-phase nosuchslug` from the repo root | loads, refuses | loaded; refused — "No `.claude-plugin/plugin.json` in the current directory" | ✅ |
| P7-L1: `/plugin-dev:plan-phases` with no args | loads, asks for mode | loaded; asked change-vs-new and for the slug | ✅ |

## Verdict

P7-M1 held, and the negative controls make the two exit-0s worth something rather than being
a tool that cannot fail.

**P7-L1 held in substance; its pass bar as written cannot be met.** The bar says the listing
"names all eight". `claude -p` lists six: `plan-phases` and `run-phase` carry
`disable-model-invocation: true`, and `-p` omits typed skills from the model's skill list.
The control settles that this is platform behaviour and not a 0.9 registration failure —
0.8.0 has seven skills with the same two typed, and the identical prompt lists exactly its
five automatic ones. Both typed skills were then invoked directly against the branch copy
and both loaded and behaved correctly. All eight register; the bar should have said "names
all six automatic skills, and both typed skills invoke" — recorded as a Deviation in note 07.

The listing is also the load check for the phase's one new skill: `run-evals` appears, which
is what the 0.9 bundle adds.
