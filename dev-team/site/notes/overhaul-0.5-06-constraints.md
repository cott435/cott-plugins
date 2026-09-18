# 06 — `docs/constraints.md` and `/dev-team:set-constraints`

Phase 6. A project-configurable quality bar with numbers and commands behind it. The
reviewer's checklist is thorough but has no threshold it can fail a section on; this adds
the one document that carries thresholds, and makes three readers run its commands.

`docs/constraints.md` may **tighten** `project-structure` §2's limits and add checks; it
never loosens anything the knowledge skills fix. Where it conflicts, the constraints file
is wrong and `review-plan` item 7 says so.

## The document — `skills/set-constraints/references/constraints-template.md`

This file is the owner of every heading below; `contracts.yml` names it. The shape:

```markdown
# Constraints

Set: <date> by /dev-team:set-constraints. Tightens `project-structure` §2; never loosens it.
Every command is run from the repo root inside the workspace environment (`uv run …`).
`<pkg>` in a command is substituted per package by whoever runs it.

## Floor
Always enforced. Not configurable; listed so the commands are in one place.

| check | threshold | command | scope |
|---|---|---|---|
| tests pass | 0 failures | `uv run pytest packages/<pkg>` | package |
| import direction | 0 violations | `uv run lint-imports` | repo |
| lint | 0 errors | `uv run ruff check` | repo |
| format | clean | `uv run ruff format --check` | repo |
| docs build | strict | `uv run mkdocs build --strict` | repo |

## Enforced
Configured thresholds. A row here is a gate: FAIL is a CRITICAL review finding and a
blocker for finalize-package.

| dimension | threshold | command | scope |
|---|---|---|---|
| line coverage | ≥ 80 % | `uv run pytest packages/<pkg> --cov=<pkg> --cov-fail-under=80 -q` | package |
| types | mypy strict, 0 errors | `uv run mypy --strict packages/<pkg>/src` | package |
| docstring coverage | ≥ 95 % | `uv run interrogate -f 95 packages/<pkg>/src` | package |

## Measured
Recorded, not yet enforced. A row moves to Enforced by editing this file; the reviewer
reports the current value and does not fail on it.

| dimension | current | target | command | scope |
|---|---|---|---|---|

## Guarded
The bar itself. Any of these appearing in a diff is a CRITICAL finding unless the
Exceptions table pardons that path for that check:

- a new `# noqa`, `# type: ignore`, `# pragma: no cover`
- a new `@pytest.mark.skip` or `@pytest.mark.xfail` whose reason does not cite a `D<n>`
- a deleted or weakened assertion in an existing test
- a threshold in this file edited down, or a command here edited to exclude paths
- a `project-structure` §2 limit exceeded with a comment saying "temporary"

## Exceptions

| path or glob | check | reason | expires |
|---|---|---|---|
```

Rows are parsed by header names, loosely (`table_rows` in `status.py` already matches
this way): a `command` column and a `scope` column are what every reader needs. The
thresholds in Enforced are the defaults `set-constraints` proposes; the user's answers
replace them.

## `skills/set-constraints/SKILL.md`

```yaml
---
name: set-constraints
description: Write or revise docs/constraints.md — the project's enforced quality bar (coverage, types, docstrings, and the floor every package clears) — by interviewing you with a default for every question. Runs in your conversation. Use once after shape-brief and before the first review, or whenever a threshold should change.
argument-hint: ""
disable-model-invocation: true
---
```

No `context: fork`: like `shape-brief`, it asks questions, and only the main conversation
can. Body:

1. **Detect before you ask** (from the vendored reference): read the root `pyproject.toml`
   for `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`, `[tool.interrogate]`; read
   `docs/constraints.md` if it exists (revision mode: show the current Enforced table and
   ask only what changes); read `docs/architecture.md` **Toolchain** if it exists.
2. **Four questions**, one `AskUserQuestion` call, each with the default pre-selected:
   coverage floor (80 / 90 / none-measure-only); type strictness (`--strict` / default /
   none); docstring coverage (95 / 80 / none); anything to add to Measured (perf budget
   per pipeline in seconds; a bundle-free "none" default).
3. **Write** `docs/constraints.md` from the template with the answers; Floor verbatim;
   Guarded verbatim; Exceptions empty.
4. Say in one line what changed for the implementer (dev dependencies the first section
   will add — `pytest-cov`, `mypy`, `interrogate` — per `workspace-scaffold`).
5. Commit `docs/constraints.md` per §Project convention, scope `docs`, summary
   `docs: set constraints (coverage <n>, mypy <mode>, docstrings <n>)`.

Nothing else: no installs, no config edits — the implementer's scaffold step owns those.

## Readers and what they run

| Reader | When | What | On FAIL |
|---|---|---|---|
| implementer, step 8 | after its own tests | every Floor and Enforced row: `repo` rows once, `package` rows with its package | fix in its own code; a failure it cannot fix without lowering a threshold is a blocker quoting the row — it never edits `docs/constraints.md` |
| implementer, step 1 (scaffold) | first section of the repo / package | add the dev dependencies the Enforced commands need to the root `pyproject.toml` `[dependency-groups] dev`; add every Floor and Enforced command to the CI workflow `workspace-scaffold` §4 emits | — |
| reviewer, section and package modes | as **axis 0**, before spec conformance | runs every applicable Floor and Enforced row; greps the review diff for every Guarded item, checking Exceptions | a Floor/Enforced FAIL is CRITICAL quoting the row; a Guarded hit is CRITICAL `bar lowered: <item> at <file:line>` |
| reviewer, plan mode | item 7 | reads the coverage floor; flags an empty §7 Tests | WARNING |
| tester | intent mode | reads the coverage floor so the intent suite is sized to contribute to it, not to satisfy it alone | — |
| `status.py --gate <pkg>` | finalize gate | runs every applicable Floor and Enforced row (subprocess, shell=False, from the repo root, 10-minute timeout per row) | one FAIL line per row: `<pkg>: constraint <dimension> FAIL (<command>)` |
| `status.py` package report | always | a line `constraints: <n> enforced, <k> failing | no docs/constraints.md` | — |
| `workspace-scaffold` §4 | CI commands | when `docs/constraints.md` exists, CI runs its Floor and Enforced rows instead of the skill's fixed list; otherwise the fixed list | — |

The reviewer never edits `docs/constraints.md`. Only `set-constraints` and the user do —
which is why the baseline rule exempts it.

## Order of authority

`docs/constraints.md` is inserted at the top of both lists (implementer and reviewer),
scoped to *the checks it names*. It does not override a contract's content; it binds the
verification of every section.

## Three-file rule, contracts, site

- `reserved-skill-names`: `set-constraints` (workflow).
- README: Contents tree; §Which skill to run gains *quality bar not written
  down → /dev-team:set-constraints*; the `docs/` layout gains `constraints.md`.
- `site.yml`: `set-constraints` after `shape-brief`.
- The vendored `references/constraint-driven-development.md`, its adaptation per note 01,
  and the skill's `LICENSE` are created in this phase.
- `contracts.yml` `headings`: owner `skills/set-constraints/references/constraints-template.md`,
  `owner_span: ['## Floor', null]`, readers `agents/reviewer.md` (`cites: ['Floor',
  'Enforced', 'Guarded', 'Exceptions']`), `agents/implementer.md` (`cites: ['Floor',
  'Enforced']`), `skills/status/SKILL.md` (`cites: ['Floor', 'Enforced']`),
  `skills/workspace-scaffold/SKILL.md` (`cites: ['Floor', 'Enforced']`).
- `contracts.yml` `forbid`: `pattern: 'CONSTRAINTS\.md'`, `files: ['agents/*.md',
  'skills/**/*.md', 'README.md']` — the file is `docs/constraints.md` here; the upstream
  name must not leak from the vendored reference. `unless: ['upstream writes
  `CONSTRAINTS.md`']` for the Provenance line. `files:` keeps `site/notes/` (this design
  set) out of scope.

## Steps

1. Template file; `set-constraints` body.
2. Implementer steps 1 and 8; reviewer axis 0; tester one line; `workspace-scaffold` §4
   sentence; both order-of-authority lists.
3. `status.py`: `constraints_rows(pkg) -> list[(dimension, command, scope)]`,
   `run_constraint(...) -> bool`, the gate lines, the report line.
4. Three-file rule; `contracts.yml`; `check-contracts`; `build-site`.
5. Evals (note 09 §H): mechanical — `status.py --gate` on the fixture with a constraints
   file whose coverage floor is set above the fixture's real coverage fails with exactly
   one constraint line; behavioral — a section diff carrying one new `# type: ignore`
   yields one CRITICAL `bar lowered`. Log both.
6. Commit: `dev-team 0.5 (phase 6): docs/constraints.md, set-constraints, constraints axis`.

## Done when

The two evals are logged; `check-contracts` proves the four readers cite headings the
template owns; `grep -r CONSTRAINTS.md` across the bundle hits only the Provenance line.
