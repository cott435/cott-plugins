---
name: set-constraints
description: Write or revise docs/constraints.md — the project's enforced quality bar (coverage, types, docstrings, and the floor every package clears) — by interviewing you with a default for every question. Runs in your conversation. Use once after shape-brief and before the first review, or whenever a threshold should change.
argument-hint: ""
disable-model-invocation: true
---

Write the project's quality bar with the user, as `docs/constraints.md`.

Like `/dev-team:shape-brief`, this runs **in the main conversation**, because it asks — only
the main conversation can. It writes one file. The reviewer, the implementer, the tester,
`status.py` and CI each run that file's commands; none of them ever edits it, so it holds
exactly the bar the user chose.

Before anything else, read `references/constraint-driven-development.md` — the method this
skill follows: detect before you ask, a default for every question, guard the bar itself,
ratchet when there is no number. Read `references/constraints-template.md` before writing; its
headings are what every reader parses.

## Boundaries

- **Write only** `docs/constraints.md`. No installs, no `pyproject.toml` edits, no CI edits:
  the implementer's scaffold step adds the dev dependencies and CI commands the file names.
- **Tighten, never loosen.** The file may add checks and tighten `project-structure` §2's
  limits; it never relaxes anything a knowledge skill fixes. A request to relax one is refused
  in one line naming the skill that fixes it.
- **Branch rule.** The run ends in a commit, so `git-workflow-and-versioning` §Project
  convention's **Branch** rule applies: on `main`/`master` or outside a git repository, stop
  with its blocker text before asking anything. The **Baseline** rule exempts this file, so a
  dirty tree elsewhere is not a blocker — but only this file is staged.

## 1. Detect before you ask

Read, when present, and say in two lines what you found:

- the root `pyproject.toml` — `[tool.ruff]`, `[tool.mypy]`, `[tool.coverage]`,
  `[tool.interrogate]`, and the dev dependency group;
- `docs/architecture.md` **Toolchain** — the test, lint and docs commands the repo contract
  states;
- `docs/constraints.md` — if it exists, this is **revision mode**: show its current Enforced
  and Measured tables and ask only about what the user wants to change.

A value the repo already sets (a `fail_under` in `[tool.coverage.report]`, `strict = true` in
`[tool.mypy]`) becomes that question's default instead of the template's.

## 2. Four questions

One `AskUserQuestion` call, four questions, the default first and marked *(Recommended)*:

1. **Coverage floor** — `80 %` · `90 %` · `none — measure only`.
2. **Type strictness** — `mypy --strict` · `mypy default` · `none`.
3. **Docstring coverage** — `95 %` · `80 %` · `none`.
4. **Measured** — anything to record without enforcing: `none` · `a runtime budget per
   pipeline, in seconds`. A budget needs the pipeline and the number; ask for them in one
   follow-up line only if picked.

Stop at four. "I don't know" is a complete answer: it takes the default.

## 3. Write

`docs/constraints.md` from `references/constraints-template.md`, with the `Set:` line dated
today. **Floor** and **Guarded** verbatim. **Enforced** with the answers substituted into
threshold and command, following the template's **Filling it** rules for a `none`.
**Measured** with any row question 4 produced. **Exceptions** empty on a first write; in
revision mode, kept exactly as it was.

In revision mode, a threshold the user lowers is theirs to lower — it is the agent lowering it
that **Guarded** exists to catch — but say in one line that every section reviewed under the
old value is not re-reviewed by this change.

## 4. Say what it costs

One line: the dev dependencies the first section's scaffold will add for the Enforced
commands (`pytest-cov`, `mypy`, `interrogate`, per `workspace-scaffold` §5), or that they are
already present.

## 5. Commit

Per `git-workflow-and-versioning` §Project convention: stage `docs/constraints.md` only, scope
`docs`, summary `docs: set constraints (coverage <n>, mypy <mode>, docstrings <n>)`, trailer
`Dev-Team-Run: set-constraints`.

## Return

Three lines at most: the file and whether it was new or revised; the Enforced rows as
`<dimension> <threshold>`; the next command — `/dev-team:plan-repo` when no
`docs/architecture.md` exists, otherwise whichever command the user was about to run.
