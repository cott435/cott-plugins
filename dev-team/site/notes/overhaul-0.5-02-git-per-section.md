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

## Deviations

- **Reviewed rule: "no commit since", not "equals".** The note defined *reviewed* as
  `review_commit == last_commit(paths)`. The review's `Commit:` is `HEAD` at review time, which
  is ahead of the section's last commit whenever anything else was committed in between —
  implement `ingest`, implement `clean`, review `ingest` — so under equality that section could
  never read as reviewed. `status.py` instead checks that the `Commit:` sha is in `HEAD`'s
  history and that `git log <sha>..HEAD -- <paths>` is empty. Eval D state 3 is that case.
- **No separate `review_commit()`.** `latest_review()` returns the `Commit:` sha beside date
  and verdict, and one `freshness()` gives the state for both the section rows and the
  `surface:` row; a second reader of the same file would have been dead code.
- **Surface paths** — left undefined by the note — are `src/<pkg>/__init__.py`, `pipelines/`,
  `pipelines.py`, `cli.py` and `cli/`.
- **§Project convention is a numbered list** (`1. **Branch** — …`) under a two-sentence
  preamble, wording otherwise as the note gives it except "from the vendored skill" → "from the
  Save Point Pattern below". `check-contracts`' heading parser owns only numbered bolded items.
- **The `headings` contract uses reader `span`s, not `cites: ['Project convention']`.** `cites`
  asserts a name without reading the reader's file, so it could not prove an agent cites the
  section. Each reader's span starts at its `§Project convention` citation — a missing citation
  is a missing marker, a FAIL — and the bolded rule names inside it (**Branch**, **Baseline**)
  must be ones the section numbers. Negative controls are in the eval D log.
- **The reviewer and the architect check Branch and Baseline before they start**, not only
  commit at the end; the note gave the implementer the blocking rules and the others only a
  commit step, but every run that commits needs a clean start or it stages someone else's
  work by omission.
- **The architect commits when it stops** for questions or access. Its stop writes
  `docs/decisions.md` stubs and often `docs/assessment.md`; left uncommitted, the latter would
  fail the next run's baseline.
- **The researcher commits only on `Commit: yes`, which only `/dev-team:probe-source` sets.**
  "Nothing — the spawner commits" left a direct probe's `docs/sources/*` uncommitted, and the
  next run's baseline would refuse it. A first wording ("run directly by probe-source") was
  misread in eval D run 1 by a researcher the architect spawned, which committed its own probe;
  the explicit marker replaced it.
- **The forked skills' last step now says "commit, then return"** — `plan-repo`,
  `plan-package`, `plan-change`, `sync-plan`, `map-project`, `implement-section`,
  `review-section`, `review-package`, `finalize-package`, `finalize-project`,
  `extract-legacy`, `probe-source` — each naming its `Dev-Team-Run:` trailer with
  `$ARGUMENTS`. The note said the skills needed no text change because the rule lives in the
  agent; eval D run 1 showed otherwise: the architect followed `plan-repo`'s numbered steps to
  "Return" and never reached its own **Commit** section. The architect's Hard rules also gained
  a bullet naming the start check and the final commit.
- **Baseline exempts `.claude/agent-memory/`.** Every agent has `memory: project` and writes
  there as it goes (eval D run 1: the researcher wrote after its commit), so without the
  exemption every run would fail the next one's baseline. Agents never stage it.
- **Implementer, outside the table:** step 7's "Commit-sized chunks" became "Small chunks … a
  save point, not a commit"; surface mode's precondition on review freshness, which still
  described the 0.4 date/mtime rule, now states the commit rule; surface mode gains its commit
  as step 9 of **Build**.
- **Workflows.** `site/workflows/new-repo.md`, `rebuild-from-legacy.md` and
  `adopt-existing-repo.md` gain one paragraph: the repo must be on a feature branch before the
  first forked run. The root `CLAUDE.md` asks for affected workflows to be updated with the
  skills; phase 9 still rewrites `new-repo.md`.
- **README knowledge-scope row** for `git-workflow-and-versioning` filled (phase 1 left it `—`):
  ✓ implementer; invoked by architect, reviewer, documenter, researcher (direct probes); the
  curator, which has no column, is named under the table.

### Included from a parallel session: the foreground fan-out fix

Eval D's headless `plan-package` never finished. That was filed as a separate task, and a
second session fixed it in the same working tree. It is committed with this phase because it
shares files with it (`architect.md`, `curator.md`, `contracts.yml`). Evidence:
`evals/2026-09-18-d2-foreground-fanout.md`. The change:

- **`agent: dev-team:<name>` in all 12 forked skills.** This is the root cause. A bare
  `agent: architect` gives no error: the fork runs as general-purpose, without the agent's
  prompt, so none of its rules apply unless it happens to `Read` its own agent file.
- **`run_in_background: false`** on every `Agent` call from the architect and the curator,
  as a Hard rule. The spawn sites point to it. Fan-outs stay parallel: one batch goes in one
  message. The "continuing after backgrounded designers" paragraph is replaced, because a fork
  never receives those notifications.
- **`contracts.yml`** gains `every forked skill names its agent with the plugin prefix` and
  `no forked run waits on a background notification`. 13/13 pass.

This bears on the deviation above that made each forked skill's last step "commit, then
return". Eval D's architect ran as general-purpose, so its **Commit** section was never loaded.
The skill-step wording may now be redundant with the agents' own sections. It is kept for this
commit, and a later phase should re-run eval D's `plan-repo` case without it before deciding.
The rule for `probe-source`'s researcher (it commits only on `Commit: yes`) is unaffected.
