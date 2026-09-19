# `docs/constraints.md` — template

The one shape `/dev-team:set-constraints` writes. Every heading from **Floor** down is read by
name — by the reviewer, the implementer, the tester, `status.py` and `workspace-scaffold` — so
keep them exactly. Table rows are parsed by header name, loosely: a `command` column and a
`scope` column are what every reader needs. `<pkg>` in a command is substituted per package by
whoever runs it; a `repo` row runs once, a `package` row once per package.

The Enforced thresholds below are the defaults `set-constraints` proposes; the user's answers
replace them. Floor and Guarded are written verbatim. Exceptions starts empty.

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
| line coverage | ≥ 80 % | `uv run pytest packages/<pkg> --cov=packages/<pkg>/src --cov-fail-under=80 -q` | package |
| types | mypy strict, 0 errors | `uv run mypy --strict packages/<pkg>/src` | package |
| docstring coverage | ≥ 95 % | `uv run interrogate -I -i -f 95 packages/<pkg>/src` | package |

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

## What each heading is for

The headings readers cite, and who runs what under each:

1. **Floor** — the checks every package clears whatever the user answered. The implementer
   (step 8), the reviewer (axis 0), `status.py --gate` and CI run every row.
2. **Enforced** — the configured thresholds, run by the same four. A FAIL is a CRITICAL review
   finding and a finalize-gate failure. The tester reads the coverage row only to size its
   suite.
3. **Measured** — reported by the reviewer, never failed on; `status.py` does not run it.
4. **Guarded** — what the reviewer greps each review diff for. A hit is CRITICAL
   `bar lowered: <item> at <file:line>`.
5. **Exceptions** — the only pardon for a Guarded hit or an Enforced FAIL, per path and check,
   until its expiry date. An expired row pardons nothing.

## Filling it

- **The commands name paths, not import names.** `--cov=packages/<pkg>/src` rather than
  `--cov=<pkg>`: coverage reads a bare name as a directory when one exists at the root, and a
  repo with a `data/` directory beside a `data` package measures the wrong thing at 0 %.
  `interrogate -I -i` skips `__init__.py` modules and `__init__` methods: `project-structure`
  keeps nested `__init__.py` files empty, and `python-style-guide` documents constructor
  arguments in the class docstring, so neither is a missing docstring.
- **An answer of "none"** for coverage, types or docstrings removes that Enforced row. For
  coverage, "none — measure only" moves the row to Measured instead, with `current` left `—`
  until the first reviewer run reports it and `target` `—`.
- **Type strictness "default"** is `uv run mypy packages/<pkg>/src` with threshold
  `mypy default, 0 errors`.
- **A Measured row the user adds** (a performance budget) names a command that prints the
  value — typically one pipeline run under `time` — and a `target`. With no command, it is not
  a row: a number nothing measures is an aspiration.
- **Exceptions** are added by the user, one row per path and check, each with a reason and an
  expiry date no more than 90 days out. `set-constraints` never writes one on its own.
