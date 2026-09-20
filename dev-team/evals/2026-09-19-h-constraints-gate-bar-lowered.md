# H — the finalize gate runs `docs/constraints.md` rows; the reviewer flags a lowered bar

**Tested against:** uncommitted — see working-tree diff (phase 6 of the 0.5 overhaul, on top of
`ba0b83e`): `skills/set-constraints/` (new), `agents/reviewer.md`, `agents/implementer.md`,
`agents/tester.md`, `skills/status/scripts/status.py`, `skills/status/SKILL.md`,
`skills/workspace-scaffold/SKILL.md`, `contracts.yml`, `evals/fixtures/two-package/docs/constraints.md`
· model: `claude-sonnet-5` (the CLI default in the headless run; every agent on `inherit`, and the
run's `modelUsage` shows only `claude-sonnet-5`); `claude-opus-5` ran the checks · 2026-09-19

## What was tested

Note 09 eval H, per note 06 §Steps 5:

- **Mechanical:** `status.py --gate` on the fixture, with a constraints file whose coverage floor
  is above the fixture's real coverage, fails with exactly one `constraint … FAIL` line.
- **Behavioral:** a section diff carrying one new `# type: ignore` yields one CRITICAL
  `bar lowered`.

Carried into this phase from earlier notes and run with it: eval C's grep over the fourth
vendored file (note 01), eval E's order-of-authority script after the constraints item was
inserted in both lists (progress row 3), and a planted violation for each new `contracts.yml`
claim.

## Method

**Setup.** `reset.sh` (with constraints) into the scratchpad as `eval-h`, branch `build`.
`docs/architecture.md`, `docs/decisions.md`, `docs/packages/data/` and `packages/` came from
eval F's final commit (a built `data/ingest`: reader, errors, 15 unit tests, 23 intent tests,
README). A uv workspace root was added: dev group `pytest pytest-cov ruff import-linter mkdocs
mypy interrogate`, a one-layer import contract, a minimal `mkdocs.yml`. `ruff format` and
`ruff check --fix` were applied once. The whole setup is one commit. The fixture's
`docs/constraints.md` was rewritten to the new template shape in this phase.

Running every row by hand on that commit showed two defects in the note's template commands.
Both were fixed before the gate runs (Results rows 1–2).

**Mechanical.** `python3 status.py data --gate` on three states:

1. the template floor, 80 %, as a control;
2. a commit raising the floor to 99 % (real coverage is 94 %);
3. `docs/constraints.md` removed from the index.

`git status` was checked after each run. No model cost.

**Behavioral.** The 99 % commit was reverted. A hand-written approving review
`docs/reviews/2026-09-19-data-ingest.md` with `Commit:` at that HEAD was committed, so the next
review is diff-scoped. Then one commit was seeded, trailer `Dev-Team-Run: implement-section
data/ingest`: `_parse_int(raw: str | None, …)` returning `int(raw)  # type: ignore[arg-type]`.
The ignore is one mypy needs, because `--strict` would flag an unused one as a types FAIL.
After the seed, all 8 rows pass (`status.py`: `8 enforced, 0 failing`). Then one real headless
run: `claude -p "/dev-team:review-section data/ingest" --plugin-dir <abs>/dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`. The evidence is the
fork's transcript (`agentType: dev-team:reviewer`), its report and its commit. Cost $0.52.

**Carried checks.**

- Eval C: `grep -nE 'npm|jest|describe\(|it\(|eslint|@ts-ignore|CONSTRAINTS\.md'` over the four
  vendored files.
- Eval E: the extraction script from its Method.
- `contract_sweep.py` on the real files, then on a scratch copy with the template's
  `4. **Guarded**` renamed and a `CONSTRAINTS.md` line appended to `reviewer.md`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| setup — `--cov=<pkg>` as the note wrote it | coverage of the `data` package | **0.00 %**. The fixture has a root `data/` directory, and coverage read `data` as that path | ❌ → fixed: `--cov=packages/<pkg>/src` |
| setup — `interrogate -f 95` as the note wrote it | pass on documented code | **87.5 %**. The empty nested `ingest/__init__.py` (which `project-structure` requires) and `IngestError.__init__` (the style guide documents args in the class docstring) count as missed | ❌ → fixed: `interrogate -I -i -f 95` |
| mech 1 — floor 80 | 0 constraint lines | `constraints: 8 enforced, 0 failing`. Finalize gate FAIL only on the non-constraint reasons (no surface, unreviewed, 2 unbuilt) | ✅ |
| mech 2 — floor 99 | exactly 1 constraint line | `constraints: 8 enforced, 1 failing`; one line `data: constraint line coverage FAIL (uv run pytest packages/data --cov=packages/data/src --cov-fail-under=99 -q)`; exit 1 | ✅ |
| mech 3 — no file | `no docs/constraints.md` | `constraints: no docs/constraints.md` | ✅ |
| mech — tree after each run | clean | clean. Tool caches went to a temp dir | ✅ |
| behav — `bar lowered` CRITICAL | exactly 1, at the seeded line | 1: *bar lowered: `# type: ignore[arg-type]` at packages/data/src/data/ingest/reader.py:138*, citing **Guarded** and the empty **Exceptions**. The eval-F-era ignore at `_parse_side` was **not** flagged: it is outside the diff | ✅ |
| behav — other CRITICALs | none from axis 0 | 2 more, both real defects in the seed rather than the axis: `int(None)` raises `TypeError`, which the `except ValueError` doesn't catch; and the signature change is unrecorded in README item 7. No constraint FAIL was raised because none failed | ✅ (seeding, see below) |
| behav — rows run | all 8 | 7. `pytest`, `mypy --strict`, coverage (the new path), `interrogate -I -i`, `lint-imports`, `ruff check`, `mkdocs build --strict`. **`ruff format --check` was not run** | ⚠️ watch |
| behav — diff scoping | diff since the previous `Commit:` | `824147d..HEAD`; report `-2` beside today's; `Carried: none` | ✅ |
| behav — commit and follow-ups | 1 commit, report + `followups.md`, trailer | `review data/ingest: request changes (3 critical)`, `Dev-Team-Run: review-section data/ingest`; 3 follow-ups, one per CRITICAL | ✅ |
| eval C, fourth file | hits only on the Provenance line | 1 hit, `constraint-driven-development.md:173`, the Provenance line (`upstream writes CONSTRAINTS.md`). The other three files: 0 | ✅ |
| eval E script | lists equal | 7 = 7, equal, `docs/constraints.md` first in both | ✅ |
| contracts, real files | all pass | 21/21 | ✅ |
| control — template `Guarded` renamed | FAIL | `FAIL … reviewer.md names 'Guarded'` | ✅ |
| control — `CONSTRAINTS.md` in `reviewer.md` | FAIL | `FAIL … agents/reviewer.md:329` | ✅ |

## Verdict

Holds. The gate prints exactly one constraint line for one failing row and none for a passing
file. The reviewer's axis 0 raised exactly one `bar lowered` CRITICAL for the one new
suppression. It ignored the pre-existing one outside the diff, and it ran the constraint
commands before the checklist.

The eval found two real defects in the note's template commands. As written, both would have
failed every package in this plugin's own layout. They are fixed in the template and the
fixture, and recorded in note 06 §Deviations. The gate runs above use the fixed commands. The
behavioral review picked the new coverage path up from the file.

The two extra CRITICALs are a seeding choice, not an axis-0 miss. A `str | None` widening
that feeds `int()` is a bug, and it is an unrecorded deviation. A cleaner seed would be a
recorded, harmless change. The count that the claim is about, `bar lowered`, is exactly 1.

Watch in phase 9: the reviewer ran 7 of 8 rows and skipped `ruff format --check`. It chained
the rows in one Bash call rather than iterating the table. If eval K shows the same, the axis-0
wording should require one result line per row in the report.
