---
name: workspace-scaffold
description: The skeleton files a new repository or package starts from — root and package pyproject.toml for a uv workspace, the import-linter contracts that enforce dependency direction, mkdocs.yml, and the CI commands. Invoke when planning a repo's Toolchain section, at run-package's SCAFFOLD step (the implementer builds the workspace root and a package skeleton before any tester runs), or when building a package's surface section. Values come from docs/architecture.md and the package contract's Sections table; this skill supplies the shapes.
---

# Workspace scaffold

The shapes a repo starts from. Kept out of the always-loaded path because only two runs ever
need them: the architect writing the repo contract's **Toolchain** section, and the implementer
— at `/dev-team:run-package`'s SCAFFOLD step, which builds the workspace root and a package's
skeleton before any tester runs, or building a package's `surface` section. Everything repo-specific — package names, dependency order, env prefixes — comes from
`docs/architecture.md`, and a package's section order from the **Sections** table of
`docs/packages/<pkg>/contract.md`; copy shapes from here and values from there.

The lint thresholds are **not** here. They live in `${CLAUDE_PLUGIN_ROOT}/pyproject-lint-config.toml`, which
is merged into the root `pyproject.toml` verbatim; a second copy would drift.

## 1. Root `pyproject.toml` (workspace)

```toml
[project]
name = "<repo>"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
# one line per package, so members resolve each other from the workspace, not PyPI
data = { workspace = true }
analysis = { workspace = true }

[dependency-groups]
dev = ["pytest", "pytest-mock", "ruff", "pylint", "import-linter", "mkdocs-material", "mkdocstrings[python]"]

[tool.pytest.ini_options]
# every package ships its own `tests` tree, so two of them collide on module name
# (`tests.integration.test_cli`) as soon as a run collects more than one package.
addopts = "--import-mode=importlib"

# --- merge ${CLAUDE_PLUGIN_ROOT}/pyproject-lint-config.toml here: [tool.ruff*], [tool.pylint*] ---

# --- import-linter: copy the block from docs/architecture.md § Dependency graph ---
[tool.importlinter]
root_packages = []          # grown by the scaffold step as packages are first built
```

When `docs/constraints.md` exists, the `dev` group also carries what its **Floor** and
**Enforced** commands run that the list above lacks — `pytest-cov` for `--cov`, `mypy`,
`interrogate`. The SCAFFOLD step adds them; nobody else edits this file for them.

The root is itself a workspace member (uv requires it), so it needs a `[project]` table even
though it holds no code. One lockfile, one virtual environment, shared by every package.

The `addopts` line is not optional once a second package exists: under pytest's default
`prepend` import mode a bare `uv run pytest` from the root fails collection with
`ModuleNotFoundError: No module named 'tests.<...>'`, while each package still passes on its
own — so the failure shows up only in CI or a full-repo run.

## 2. Package `pyproject.toml`

```toml
[project]
name = "<pkg>"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2",
    "pydantic-settings>=2",
    "loguru",
    # upstream packages by name; resolved from the workspace via the root's [tool.uv.sources]
]

[project.scripts]
# <pkg>-<verb> = "<pkg>.cli:<function>"   — added by the surface section's implementer; the module
#                                          must live inside src/<pkg>/ or the entry point cannot resolve

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<pkg>"]
```

Nothing about lint, import-linter, or docs goes here — the root owns those.

## 3. import-linter contracts

Three kinds of contract, all in the root `pyproject.toml`. `layers` lists **highest first**;
indirect import chains count; a layer that does not exist yet fails the check unless it is
wrapped `(pkg)`, which is why the scaffold step adds packages as they are built rather than
listing the whole target up front. A wrapped layer that does exist is enforced exactly like an
unwrapped one, so leaving a built section wrapped loses nothing but the typo check
[proven: evals/2026-09-29-2.2-platform-facts.md]. Packages must be importable — run inside the workspace
environment.

```toml
[tool.importlinter]
root_packages = ["analysis", "data"]            # every package built so far

# 1. Package dependency direction — from docs/architecture.md, highest first.
[[tool.importlinter.contracts]]
name = "package dependency direction"
type = "layers"
layers = ["ml", "analysis", "data"]

# 2. Consumers use the public surface only — one per shipped package: forbidden_modules is
#    every row of the package contract's Sections table but `surface`, as <pkg>.<section>;
#    source_modules is every package whose `depends on` names this one. Written by the
#    implementer of the package's `surface` section.
[[tool.importlinter.contracts]]
name = "data: consumers import the top level only"
type = "forbidden"
source_modules = ["analysis", "ml"]
forbidden_modules = ["data.ingest", "data.clean", "data.audit", "data.storage"]

# 3. Section layering inside a package — derived from the Sections table's `depends on`
#    column, the `surface` row left out: a section sits above every section it depends on.
#    `|` separates sections that may not import each other; a section not built yet is
#    wrapped `(name)` so the contract passes before it exists.
[[tool.importlinter.contracts]]
name = "data: section layering"
type = "layers"
containers = ["data"]
layers = ["storage", "audit | clean", "ingest"]
```

`pipelines` and `configs` are container-level modules, not layers, so a pipeline that imports
every section is legal. `lint-imports` is the command; it exits non-zero on any broken contract.

**Growing the block.** The SCAFFOLD step adds the package to
`root_packages` and to contract 1 in the position `docs/architecture.md` gives, and adds
contract 3 for that package with every section of the Sections table placed by its `depends
on`, every one wrapped `(name)` since none is built yet; each section's implementer unwraps its
own name.
The implementer of the package's `surface` section adds contract 2, once every other section
is built. A scaffolded package has code — its `__init__.py` — so it is importable and listed.

## 4. `mkdocs.yml`

```yaml
site_name: <repo>
docs_dir: docs                       # the planning docs; API pages go under docs/api/
exclude_docs: |
  plans/**                           # proposal history stays out of the site
  sources/*.json                     # probe samples and statistics are data, not pages
  sources/*.py                       # and so are the probe and profile programs beside them
theme:
  name: material
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [packages/*/src]     # uv workspace layout
          options:
            docstring_style: google
            merge_init_into_class: true
            show_source: false
nav:
  - Architecture: architecture.md
  - Decisions: decisions.md
  - API: []                           # each surface section appends "- <pkg>: api/<pkg>.md"
                                      # Home: index.md is added by the documenter with the page
```

The site must build strict from the first scaffold onward, so the `nav` only ever names
files that exist: the scaffold step writes a nav with `Architecture` and `Decisions` and no
`docs/index.md` — nothing under `docs/` but the ledgers, `interface.md` and `docs/api/` is the
implementer's to write, so the home page waits for the documenter; each package's `surface`
section adds `docs/api/<pkg>.md` (one `::: <module>` block per providing module in
`interface.md`, plus `::: <pkg>.cli` and the pipeline modules) and its `API` nav entry;
`/dev-team:finalize-project` writes `index.md`, adds `Home` and keeps the nav in sync. Cross-references in docstrings use `` [`name`][pkg.module.name] ``;
`mkdocs build --strict` turns an unresolved one, or a nav entry with no file, into a build
failure — which is the point.

## 5. CI commands

Run in the workspace environment, from the root:

```
uv sync --all-packages
uv run ruff check && uv run ruff format --check
uv run pylint --disable=all --enable=C0302,R0904 packages/*/src
uv run lint-imports
uv run --package <pkg> pytest packages/<pkg>/tests          # one package
uv run pytest packages/*/tests                              # everything
uv run mkdocs build --strict
```

These are the commands the repo contract's Toolchain section states, and the ones the stop
gate runs when a repo has no `docs/constraints.md`.

When `docs/constraints.md` exists, CI runs its **Floor** and **Enforced** rows instead of the
fixed list above — `repo` rows once, `package` rows once per package with `<pkg>`
substituted — after `uv sync --all-packages`, plus the `pylint` size check, which the Floor
does not carry. They are the same rows the implementer's stop gate runs before every
implementer may finish, so a section the gate let through is one CI passes. Without that
file, the list above is the CI.
