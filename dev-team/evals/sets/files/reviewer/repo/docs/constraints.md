# Constraints

Set by `/dev-team:set-constraints` on 2026-09-20. The stop hook, `status.py --run-gate` and CI
run the same rows.

## Floor

| dimension | command | scope | threshold |
|---|---|---|---|
| lint | `uv run ruff check packages/<pkg>` | package | 0 errors |
| format | `uv run ruff format --check packages/<pkg>` | package | 0 files would be reformatted |

## Enforced

| dimension | command | scope | threshold |
|---|---|---|---|
| unit tests | `uv run pytest packages/<pkg>/tests/unit -q` | package | 0 failures |
| intent tests | `uv run pytest packages/<pkg>/tests/intent -q` | package | 0 failures |
| coverage | `uv run pytest packages/<pkg> --cov=packages/<pkg>/src --cov-report=term` | package | ≥ 85% |

## Measured

| dimension | command | scope | threshold |
|---|---|---|---|
| complexity | `uv run radon cc packages/<pkg>/src -s -a` | package | report |
| module size | `wc -l packages/<pkg>/src/**/*.py` | package | report |

## Guarded

- an added `# noqa`, `# type: ignore` or `# pragma: no cover`
- an added `@pytest.mark.skip` or `xfail` whose reason cites no `D<n>`
- a removed `assert` or `pytest.raises` in a test file that stayed
- a change to this file that lowers a threshold or narrows a command

## Exceptions

| path | check | reason | expires |
|---|---|---|---|
| — | — | — | — |
