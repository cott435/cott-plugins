# Constraints
Updated: 2026-09-18

The bars every section is held to. Written by hand for the eval fixture; phase 6 of the 0.5
overhaul defines the template `/dev-team:set-constraints` writes, and this file is re-shaped
to it then.

| Constraint | Bar | Check | Enforced |
|---|---|---|---|
| Test coverage | 80% line coverage per package | `uv run pytest --cov=<pkg> --cov-fail-under=80` | yes |
| Types | `mypy --strict` clean | `uv run mypy --strict packages/<pkg>/src` | yes |
| Docstrings | 95% docstring coverage | `uv run interrogate --fail-under 95 packages/<pkg>/src` | yes |
