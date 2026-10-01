# Fixture — `entry-point`

Mechanical cases for `skills/status/scripts/entry_point.py`, the script an implementer runs
under `locked.py deps` to add one line under `[project.entry-points."<group>"]` in its
package `pyproject.toml`. Written for phase 4 of 2.4 (`site/notes/2.4-04-entry-points-and-guards.md`).

```
python3 evals/fixtures/entry-point/check.py    # every case; exit 1 names each failure
```

`check.py` builds one temporary repo: `docs/architecture.md` with the Packages row
`core | packages/core`, `docs/packages/core/contract.md` with `testing` and `surface` rows,
`packages/core/pyproject.toml` in `workspace-scaffold` §2's shape (one comment line inside
`dependencies` and a `[project.scripts]` table), and `packages/core/src/core/testing/plugin.py`
with the `__init__.py` files that make `core` and `core.testing` modules. It runs the script
directly, with no lock and no `uv.lock` (so no `uv sync`), the cases in order against the same
file.

| Case | Arguments | Expected |
|---|---|---|
| `new-table` | `core pytest11 core_testing core.testing.plugin` | exit 0; the file parses and holds the entry; the comment line and `[project.scripts]` are byte for byte as before; the new table sits after `[project.scripts]`, one blank line either side |
| `second-name` | then `core pytest11 other core.testing.plugin` | both names in one table |
| `replace` | then `core pytest11 core_testing core.testing.plugin:hook` | one `core_testing` line, the new target |
| `unchanged` | the same again | exit 0, `entry point unchanged`, the file's bytes unchanged |
| `dotted-name` | `core pt.migrations core.testing core.testing` | header `[project.entry-points."pt.migrations"]`, key `"core.testing"` |
| `outside-package` | `core pytest11 x other.plugin` | exit 2, the file unchanged |
| `missing-module` | `core pytest11 x core.nothere` | exit 2, the file unchanged |
| `console-scripts` | `core console_scripts x core.testing.plugin` | exit 2, the file unchanged |

Needs Python 3.11 or later (`tomllib`); nothing else.
