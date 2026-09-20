---
name: git-workflow-and-versioning
description: Structures git workflow practices — atomic commits, descriptive messages, save points, pre-commit hygiene. Preloaded into the implementer; invoked by every other agent that commits, at the moment it checks the branch and commits. §Project convention is the commit rule every agent follows.
license: agent-skills by Addy Osmani, MIT. Complete terms in LICENSE.
user-invocable: false
---

# Git Workflow and Versioning

## Overview

Git is your safety net. Treat commits as save points, branches as sandboxes, and history as
documentation. With AI agents generating code at high speed, disciplined version control is
the mechanism that keeps changes manageable, reviewable, and reversible.

## Project convention

Every dev-team run that writes files ends by committing exactly those files. These rules are
the one copy; agents cite this section and do not restate it. Where anything below this
section disagrees, this section wins.

1. **Branch** — Agents never create, switch or delete branches. A run that would commit refuses
   to start when the current branch is `main` or `master` (`git branch --show-current`), or when
   the directory is not a git repository. Blocker text: *on `<branch>`; create a feature branch
   and re-run* / *not a git repository; `git init`, create a branch, and re-run*.

2. **Baseline** — Before writing anything, `git status --porcelain` must be empty except for
   modifications to `docs/decisions.md`, `docs/brief.md` and `docs/constraints.md` — the three
   files the user edits by hand between runs — and anything under `.claude/agent-memory/`,
   which agents write as they go and nobody stages but the user. Anything else is a blocker listing the paths:
   *uncommitted changes outside the user-edited files: <paths>; commit or stash them and
   re-run*. The exemption exists so answering a decision never requires a commit first; the
   run that consumes the answer commits the file.

3. **Staging** — Stage by explicit path — the paths the run wrote, which are the paths its
   return message lists. Never `git add -A`, `git add .`, or `git commit -a`. A file the run
   did not write is never staged, even if it is modified; that is the baseline rule's job.

4. **Message** — First line `<scope>: <imperative summary>`, at most 72 characters, where
   `<scope>` is one of:

   | Run | `<scope>` | Example |
   |---|---|---|
   | `implement-section` | `<pkg>/<section>` | `data/ingest: parse polygon aggregates into Bar rows` |
   | `finalize-package` | `<pkg>/surface` | `data/surface: lazy re-exports, load_bars pipeline, cli` |
   | `test-section` (intent) | `<pkg>/<section>` | `data/ingest: 14 intent tests from design` |
   | `test-section` (reconcile) | `<pkg>/<section>` | `data/ingest: reconcile 2 intent tests with deviations` |
   | `review-section` / `review-package` / `review-plan` | `review <pkg>/<section>` / `review <pkg>/surface` / `review <pkg>/plan` | `review data/ingest: request changes (2 critical)` |
   | `plan-repo` / `plan-package` / `plan-change` / `sync-plan` / `sync-design` / `map-project` | `plan <target>` | `plan data: contract, spine design (ingest), integration` |
   | `extract-legacy` | `legacy` | `legacy: inventory of ../old-repo` |
   | `finalize-project` | `docs` | `docs: package READMEs, api pages, root README` |
   | `set-constraints` | `docs` | `docs: set constraints (coverage 80, mypy strict, docstrings 95)` |

   Body: blank line, then one trailer per line and nothing else:

   ```
   Dev-Team-Run: <skill name> <argument as typed>
   Plan: <slug>                       (only when a plan slug is set)
   ```

   The trailer is what lets any tool find a run's commit without parsing the summary.

5. **Hygiene** — The run's own verification (its test command, `lint-imports`, `ruff check`) has
   already passed before the commit step — the commit step never runs them again. If a
   pre-commit hook rejects the commit, fix what it names and retry once; a second rejection is a
   blocker quoting the hook output.

6. **One commit per run** — A run never makes two commits. Mid-run "save points" from the
   Save Point Pattern below are `git stash`-free and commit-free here: the run is the unit of
   work, and a partial run that stops on a blocker leaves its files uncommitted for the user to
   inspect (the next run's baseline rule will name them).

## Core Principles

### 1. Commit Early, Commit Often

Each successful increment gets its own commit. Don't accumulate large uncommitted changes.

```
Work pattern:
  Implement slice → Test → Verify → Commit → Next slice

Not this:
  Implement everything → Hope it works → Giant commit
```

Commits are save points. If the next change breaks something, you can revert to the last
known-good state instantly.

### 2. Atomic Commits

Each commit does one logical thing:

```
# Good: each commit is self-contained
git log --oneline
a1b2c3d Add page parser for the orders API with pagination
d4e5f6g Add orders store with upsert on order_id
h7i8j9k Wire parser into the ingest pipeline and CLI command
m1n2o3p Add parser tests against the probe sample

# Bad: everything mixed together
git log --oneline
x1y2z3a Add orders ingest, fix config, bump deps, refactor utils
```

### 3. Descriptive Messages

Commit messages explain the *why*, not just the *what*:

```
# Good: explains intent
feat: validate order totals at parse time

Rejects negative and non-numeric totals before they reach the store.
Uses the pydantic model the design names, consistent with the other
parsers in ingest/.

# Bad: describes what's obvious from the diff
update parsers.py
```

**Format:**
```
<type>: <short description>

<optional body explaining why, not what>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `refactor` — Code change that neither fixes a bug nor adds a feature
- `test` — Adding or updating tests
- `docs` — Documentation only
- `chore` — Tooling, dependencies, config

Where §Project convention sets a message format, it wins over this one.

### 4. Keep Concerns Separate

Don't combine formatting changes with behavior changes. Don't combine refactors with
features. Each type of change should be a separate commit:

```
# Good: separate concerns
git commit -m "refactor: extract date parsing to a shared helper"
git commit -m "feat: accept ISO week dates in the orders parser"

# Bad: mixed concerns
git commit -m "refactor date parsing and add ISO week dates"
```

**Separate refactoring from feature work.** A refactoring change and a feature change are two
different changes — commit them separately. This makes each change easier to review, revert,
and understand in history. Small cleanups (renaming a variable) can be included in a feature
commit.

### 5. Size Your Changes

Target ~100 lines per commit. Changes over ~1000 lines should be split.

```
~100 lines  → Easy to review, easy to revert
~300 lines  → Acceptable for a single logical change
~1000 lines → Split into smaller changes
```

## The Save Point Pattern

```
Agent starts work
    │
    ├── Makes a change
    │   ├── Test passes? → Commit → Continue
    │   └── Test fails? → Revert to last commit → Investigate
    │
    ├── Makes another change
    │   ├── Test passes? → Commit → Continue
    │   └── Test fails? → Revert to last commit → Investigate
    │
    └── Feature complete → All commits form a clean history
```

This pattern means you never lose more than one increment of work. If an agent goes off the
rails, `git restore` on the files it touched takes you back to the last successful state —
never a `git reset --hard` over a tree that holds someone else's uncommitted work.

## Pre-Commit Hygiene

Before every commit:

```bash
# 1. Check what you're about to commit
git diff --staged

# 2. Ensure no secrets
git diff --staged | grep -i "password\|secret\|api_key\|token"

# 3. Lint and format
uv run ruff check
uv run ruff format --check

# 4. Run tests
uv run pytest

# 5. Check the dependency contracts
uv run lint-imports
```

Automate this with a `pre-commit` hook if the repo has one configured; the commands are the
same.

## Handling Generated Files

- **Commit generated files** only if the project expects them (`uv.lock` — always)
- **Don't commit** build output (`dist/`, `site/` from `mkdocs build`), caches
  (`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`), the virtualenv
  (`.venv/`), environment files (`.env`), or IDE config (`.vscode/settings.json` unless shared)
- **Have a `.gitignore`** that covers: `.venv/`, `__pycache__/`, `*.pyc`, `dist/`, `.env`,
  `.env.*`, `*.pem`, and the tool caches above

## Using Git for Debugging

```bash
# Find which commit introduced a bug
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
git bisect run uv run pytest tests/unit/ingest/test_parsers.py -x

# View what changed recently
git log --oneline -20
git diff HEAD~5..HEAD -- src/

# Find who last changed a specific line
git blame src/data/ingest/parsers.py

# Search commit messages for a keyword
git log --grep="validation" --oneline
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll commit when the feature is done" | One giant commit is impossible to review, debug, or revert. Commit each slice. |
| "The message doesn't matter" | Messages are documentation. Future you (and future agents) will need to understand what changed and why. |
| "I'll squash it all later" | Squashing destroys the development narrative. Prefer clean incremental commits from the start. |
| "I'll split this change later" | Large changes are harder to review, riskier to ship, and harder to revert. Split before committing, not after. |
| "I don't need a .gitignore" | Until `.env` with production secrets gets committed. Set it up immediately. |

## Red Flags

- Large uncommitted changes accumulating
- Commit messages like "fix", "update", "misc"
- Formatting changes mixed with behavior changes
- No `.gitignore` in the project
- Committing `.venv/`, `.env`, caches, or build artifacts
- Force-pushing to shared branches

## Verification

For every commit:

- [ ] Commit does one logical thing
- [ ] Message explains the why, follows the format above (or §Project convention's)
- [ ] Tests pass before committing
- [ ] No secrets in the diff
- [ ] No formatting-only changes mixed with behavior changes
- [ ] `.gitignore` covers standard exclusions

## Provenance

Upstream `addyosmani/agent-skills` `skills/git-workflow-and-versioning/SKILL.md` at `c004a74`.
Dropped: When to Use, Trunk-Based Development, Branching Strategy and Branch Naming, Working
with Worktrees, Change Summaries, Release & Versioning, and the release rows of the
Rationalizations, Red Flags and Verification lists. Rewritten: every command and example to
`uv`/`ruff`/`pytest`/`lint-imports`. Added: §Project convention, the dev-team commit rule.
