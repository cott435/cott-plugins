# Constraints

Set: 2026-09-20 by /dev-team:set-constraints. Tightens `project-structure` §2; never loosens it.
Every command is run from the repo root. `<pkg>` in a command is substituted per package by
whoever runs it. These rows pass in a bare checkout with `ruff` on `PATH`, so a gate failure
in this fixture comes from the intent suite and nothing else.

## Floor
Always enforced. Not configurable; listed so the commands are in one place.

| check | threshold | command | scope |
|---|---|---|---|
| lint | 0 errors | `ruff check packages/<pkg>` | package |
| format | clean | `ruff format --check packages/<pkg>` | package |

## Enforced
Configured thresholds. A row here is a gate.

| dimension | threshold | command | scope |
|---|---|---|---|

## Measured
Recorded, not yet enforced.

| dimension | current | target | command | scope |
|---|---|---|---|---|

## Guarded
The bar itself. Any of these appearing in a diff is a CRITICAL finding unless the
Exceptions table pardons that path for that check:

- a new `# noqa`, `# type: ignore`, `# pragma: no cover`
- a new `@pytest.mark.skip` or `@pytest.mark.xfail` whose reason does not cite a `D<n>`
- a deleted or weakened assertion in an existing test
- a threshold in this file edited down, or a command here edited to exclude paths

## Exceptions

| path or glob | check | reason | expires |
|---|---|---|---|
