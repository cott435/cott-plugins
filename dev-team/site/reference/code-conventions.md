# Code conventions

Knowledge is scoped **by role**, through each agent's `skills:` frontmatter, the only
mechanism in Claude Code that scopes by agent, and through the skills an agent's procedure
invokes or reads from. [The flow](../flow.md) has the table of which agent uses which skill,
and when.

`git-workflow-and-versioning` §Project convention is the
one copy of the commit rule every agent follows: the run gate, staging by explicit path
(`git add <paths>` then `git commit -m … -- <paths>`), `<scope>: <summary>` with one
`Dev-Team-Run:` trailer, one commit per run, and a retry on `.git/index.lock`.
`test-driven-development` is preloaded for the tester and the implementer: the tester writes
to its RED step, and the implementer uses its Prove-It pattern on review findings that are
bugs. `security-review` goes to the implementer on its triggers, to
reviewer B in round 1, and to a round-2+ reviewer when the diff hits a trigger. The last three
skills are vendored from `addyosmani/agent-skills` (MIT) and adapted to this stack.

Three conventions in `python-style-guide` are marked *Project convention*:

- **`__init__.py`.** The top-level `__init__.py` of a package exposes *only the names a
  consumer outside the package needs*, resolved lazily (PEP 562) so `import data` costs
  nothing until a name is touched. The `surface` section writes it, and nothing else. Every
  nested one is empty. Inside a package, import from the defining module; from another
  package, import from its top level only. import-linter enforces the second.
- **Docstrings on everything.** Google style, `Args:` without types, `Examples:` in doctest
  form on public entry points. The docs build runs strict in CI — that is the docstring-rot
  catch. A summary line says what the function changes outside itself.
- **Function shape.** Phases inside a function are fine, each with a one-line purpose comment;
  a helper is extracted only when the jump buys something. A limit is met with a seam: no
  `**options` bag, no packed tuple, no three-statement helper with one caller. Every call on a
  main path names its target, and a pipeline reads as its steps (`references/pipelines.md`).

**CLI commands live in `src/<pkg>/cli.py`**, one function per command, registered under
`[project.scripts]`, with no `scripts/` directory — an entry point must be importable from the
installed package (`project-structure` §1).

**Enforced, not intended.** Dependency direction between packages, "consumers import the top
level only", and section layering inside a package are import-linter contracts in the root
`pyproject.toml`, derived from the Sections table's `depends on`. CI runs the same
`docs/constraints.md` rows the stop gate runs. Merge `pyproject-lint-config.toml` into the root
`pyproject.toml`; it ships beside this README so there is one copy. The lint block caps
positional parameters (`PLR0917`; keyword-only ones are free) and requires ruff 0.16.0 or
later. The stop gate also runs `status.py --shape`: a run that adds a trivial single-use helper
or an options bag does not pass.

This plugin ships no rule: Claude Code loads path-scoped rules only from `.claude/rules/`. For
your own interactive work, write a `.claude/rules/python-standards.md` in the repo you are
building that points at `project-structure` and `python-style-guide`.
