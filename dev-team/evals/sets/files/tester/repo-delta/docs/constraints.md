# Constraints

Set: 2026-09-21 by /dev-team:set-constraints. Tightens `project-structure` §2; never loosens it.
Every command runs from the package root with `src` on `PYTHONPATH`. `<pkg>` is substituted by
whoever runs it.

## Floor
Always enforced.

| check | threshold | command | scope |
|---|---|---|---|
| tests pass | 0 failures | `PYTHONPATH=src python -m pytest tests -q` | package |
| lint | 0 errors | `ruff check .` | repo |
| format | clean | `ruff format --check .` | repo |

## Enforced

| dimension | threshold | command | scope |
|---|---|---|---|
| line coverage | ≥ 80 % | `PYTHONPATH=src python -m pytest tests --cov=src --cov-fail-under=80 -q` | package |

## Measured

| dimension | current | target | command | scope |
|---|---|---|---|---|

## Guarded

- a new `# noqa`, `# type: ignore`, `# pragma: no cover`
- a new `@pytest.mark.skip` or `@pytest.mark.xfail` whose reason does not cite a `D<n>`
- a deleted or weakened assertion in an existing test
- a threshold in this file edited down

## Exceptions

| path or glob | check | reason | expires |
|---|---|---|---|
