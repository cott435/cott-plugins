# Constraints

Set: 2026-09-19 by /dev-team:set-constraints. Tightens `project-structure` §2; never loosens it.
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
