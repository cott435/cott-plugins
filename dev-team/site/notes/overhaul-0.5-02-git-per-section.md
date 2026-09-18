# 02 — Commit per section

Phase 2. Every agent run that writes files ends by committing exactly those files. The unit
of review becomes a commit range instead of "the files on disk at review time", and
`status.py` derives "reviewed since build" from commits instead of mtimes.

## The one copy of the rule

`skills/git-workflow-and-versioning/SKILL.md` §**Project convention** holds the rules
below verbatim. Agents say "commit per `git-workflow-and-versioning` §Project convention"
and, if the skill is not preloaded into them, invoke it with the Skill tool at that step.
The rules are not restated in any agent body. `contracts.yml` gains a `headings` contract
with this section as owner and every agent that cites it as a reader.

### §Project convention (content)

**Branch.** Agents never create, switch or delete branches. A run that would commit refuses
to start when the current branch is `main` or `master` (`git branch --show-current`), or when
the directory is not a git repository. Blocker text: *on `<branch>`; create a feature branch
and re-run* / *not a git repository; `git init`, create a branch, and re-run*.

**Baseline.** Before writing anything, `git status --porcelain` must be empty except for
modifications to `docs/decisions.md`, `docs/brief.md` and `docs/constraints.md` — the three
files the user edits by hand between runs. Anything else is a blocker listing the paths:
*uncommitted changes outside the user-edited files: <paths>; commit or stash them and
re-run*. The exemption exists so answering a decision never requires a commit first; the
run that consumes the answer commits the file.

**Staging.** Stage by explicit path — the paths the run wrote, which are the paths its
return message lists. Never `git add -A`, `git add .`, or `git commit -a`. A file the run
did not write is never staged, even if it is modified; that is the baseline rule's job.

**Message.** First line `<scope>: <imperative summary>`, at most 72 characters, where
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

Body: blank line, then one trailer per line and nothing else:

```
Dev-Team-Run: <skill name> <argument as typed>
Plan: <slug>                       (only when a plan slug is set)
```

The trailer is what lets any tool find a run's commit without parsing the summary.

**Hygiene.** The run's own verification (its test command, `lint-imports`, `ruff check`) has
already passed before the commit step — the commit step never runs them again. If a
pre-commit hook rejects the commit, fix what it names and retry once; a second rejection is a
blocker quoting the hook output.

**One commit per run.** A run never makes two commits. Mid-run "save points" from the
vendored skill are `git stash`-free and commit-free here: the run is the unit of work, and a
partial run that stops on a blocker leaves its files uncommitted for the user to inspect
(the next run's baseline rule will name them).

## What each agent stages

| Agent / mode | Paths |
|---|---|
| implementer, section | the section's source directory; `tests/unit/<section>/`; fixtures it added under `tests/fixtures/`; the section README; `docs/followups.md`; `docs/decisions.md`; root `.gitignore`; on a first section: root `pyproject.toml`, `packages/<pkg>/pyproject.toml`, `uv.lock`, `mkdocs.yml`, `docs/index.md` |
| implementer, surface | `src/<pkg>/__init__.py`, `pipelines/`, `cli.py`, `packages/<pkg>/pyproject.toml`, root `pyproject.toml`, `uv.lock`, `packages/<pkg>/tests/` files it wrote, `docs/api/<pkg>.md`, `mkdocs.yml`, `docs/packages/<pkg>/interface.md`, `docs/decisions.md`, `docs/followups.md` |
| tester | `tests/intent/<section>/`; fixtures it copied under `tests/fixtures/`; `docs/followups.md` (reconcile mode only) |
| reviewer | its report; `docs/followups.md` |
| architect | every path under `docs/` its return message lists as written or modified, including files its designers and researchers wrote this run (they do not commit; they return, the architect commits) |
| curator | `docs/legacy/inventory.md`; `.claude/skills/<name>/` for each researcher it spawned in extract mode |
| documenter | the READMEs and `docs/api/*.md` it wrote, `docs/index.md`, root `README.md` |
| designer, researcher | nothing — layer-2 agents return to the architect or curator, which commits |

## Reviewer: the diff is the unit

`reviewer.md` §Inputs gains:

> Record `Commit: <git rev-parse HEAD>` as the second line of your report, under `Scope:`.
> Find the previous report for this scope (`docs/reviews/*-<pkg>-<section>.md`, newest by
> date, excluding today's) and read its `Commit:` line. If one exists, review
> `git diff <that sha>..HEAD -- <section source path> <tests/unit/<section>> <tests/intent/<section>>`
> as the primary object and the full section as context; a finding from the previous report
> that the diff does not touch is re-listed under a **Carried** heading, not re-derived. If no
> previous report exists, or it has no `Commit:` line, review the full section.

The report header becomes:

```
# Review — <pkg>/<section> — <date>
Scope: <what you read>
Commit: <sha>
Verdict: approve | approve with fixes | request changes
```

`## Carried` is added between `## SPEC GAPS` and the end, present only on a re-review.

## `status.py` changes

- Replace `last_change(path)` with `last_commit(*paths) -> str | None`:
  `git log -1 --format=%H -- <paths>`; `None` when not a repo or no commit touches them.
- Add `review_commit(stem) -> str | None`: the `^Commit:\s*([0-9a-f]{7,40})` line of the
  newest review file for `stem`.
- A section is **reviewed** iff `review_commit(f"{pkg}-{sec}")` is not `None` and equals
  `last_commit(section_path, tests/unit/<sec>, tests/intent/<sec>)`. A section whose source
  has uncommitted changes (`git status --porcelain -- <paths>` non-empty) prints
  `uncommitted` in the reviewed column and fails the gate with
  `<pkg>/<sec>: uncommitted changes`.
- The `reviewed-since-build` column prints `✓ <date> <verdict> @<sha[:7]>` or
  `· <date or —> <verdict> @<sha[:7] or —>`.
- The package review row (`surface:`) uses the same rule over the surface paths.
- The 0.4 mtime path is removed, not kept as a fallback: a review with no `Commit:` line is
  stale by definition (CHANGELOG breaking item 3).

## Agent edits, by file

| File | Edit |
|---|---|
| `agents/implementer.md` | §Blocking rules: add **Not on a branch** and **Dirty tree** (wording from §Project convention). §Procedure: new step 13 **Commit** — *per `git-workflow-and-versioning` §Project convention; stage the paths in your return message's "Files created / modified" list plus the docs files you edited.* Return message gains a line: `Commit: <sha>`. Surface mode: the same step at its end. `skills:` frontmatter gains `git-workflow-and-versioning`. |
| `agents/reviewer.md` | §Inputs paragraph above; §Output header; new **Commit** step after the follow-ups append: invoke `git-workflow-and-versioning`, commit report + `docs/followups.md`. Return gains `Commit: <sha>`. |
| `agents/architect.md` | §Hard rules: *Bash is read-only except for `git add <paths>` and `git commit` at the end of a run.* §Final return message: add `Commit: <sha>`. New §**Commit** before §Memory: the branch, baseline and staging rules by reference; the paths are the return message's list. Applies to every scope. |
| `agents/curator.md`, `agents/documenter.md` | a **Commit** paragraph, same shape, listing their paths. |
| `agents/designer.md`, `agents/researcher.md` | one line: *You do not commit; the agent that spawned you does.* |
| `skills/implement-section/SKILL.md`, `finalize-package`, `review-section`, `review-package`, `plan-*`, `sync-plan`, `map-project`, `extract-legacy`, `finalize-project` | no text change — the rule lives in the agent; the skill's **Steps** last item already says "return your summary", which now includes the commit. |
| `skills/status/scripts/status.py` | as above. |
| `skills/status/SKILL.md` | the paragraph defining *reviewed* is rewritten to the commit rule. |
| `skills/git-workflow-and-versioning/SKILL.md` | §Project convention written. |
| `contracts.yml` | `headings`: owner `skills/git-workflow-and-versioning/SKILL.md`, `owner_span: ['## Project convention', null]`, readers: every agent file above, `cites: ['Project convention']`. `forbid`: `pattern: 'git add -A|git add \.|git commit -a\b'`, `files: ['agents/*.md', 'skills/**/*.md']`, `unless: ['Never `git add -A`']` — scoped with `files:` so this design note, which quotes the pattern, is not a finding. |
| `README.md` | §Gotchas: the worktree bullet notes that runs now commit, so worktree merges are commit merges. §One-time setup: new item — *the repo you build in is a git repository on a feature branch; agents refuse `main`.* |

## Steps

1. Write §Project convention.
2. `status.py`: implement `last_commit`, `review_commit`, the reviewed rule, the
   `uncommitted` state; run it against `evals/fixtures/two-package/` (note 09) at three
   states — never committed, committed and unreviewed, reviewed — and check the column.
3. Agent edits per the table; reviewer header; `contracts.yml`.
4. `check-contracts`, `build-site`.
5. Evals (note 09 §D): mechanical — the `status.py` three-state check; behavioral — one
   `implement-section` run on the fixture, then `git show --stat HEAD` lists exactly the
   staged-paths set and the message carries the `Dev-Team-Run:` trailer. Log both.
6. Commit: `dev-team 0.5 (phase 2): every run commits what it wrote; review by commit range`.

## Done when

`status.py` has no `st_mtime` reference; the reviewer's template has `Commit:`; every
agent file that commits cites §Project convention and `check-contracts` proves it; the two
evals are logged.
