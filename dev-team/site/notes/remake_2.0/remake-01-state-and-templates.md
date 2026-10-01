# 01 — state and templates

Phase 01. Rewrites `skills/status/scripts/status.py` to the design's state spec — one derivation
of every section's state from disk, the ready set, rounds from report filenames, `shipped` as
the `surface` section being DONE, and the exact next command — and rewrites `skills/status/SKILL.md`
to match. In the same commit `planning-templates` gains the four file shapes the loop writes
and reads from now on: the package contract's `surface` row, `change.md`, `deviations-entry.md`
and `review-report.md`. Everything later parses what this phase defines: the hooks import the
parsers, the agents write the templates, the driver reads the states. The gap it closes: 0.6
had four readers (driver, `status`, the reviewer, the documenter) deriving state four ways, and
no template for a review report or a deviation, so nothing could be checked against one.

The old flags `--gate` and `--plan-gate` go, and the old readers of `integration.md`,
`surface.md` and `docs/plans/` go with them. Nothing in this phase edits an agent or a workflow
skill other than `status`; the old skills keep their text and stop being runnable, per the
overview's consistency rule.

## Decisions

- **Rounds and verdicts.** A round is the set of reports sharing `-r<n>-`; its verdict is the
  worst of the set, ordered `request changes` > `spec-change` > `approve`. A report with no
  `Verdict:` line counts as `request changes`. A 0.6-era report (`<date>-<pkg>-<section>[-<k>].md`
  with no `-r<n>-`) is read as round 1, suffix `s`. Reason: the design fixes the filename and
  the worst-of rule; the fallback keeps a migrated repo readable.
- **"Newer than" is commit order**, never mtime: the newest commit touching path A is an
  ancestor of the newest commit touching path B means B is newer. Two paths last touched by
  the same commit are not newer than each other. An uncommitted change to a path makes that
  path `uncommitted`, which is reported in the evidence column and treated as newer than
  everything. Reason: the design's re-open rules are stated as "newer than", and only commits
  survive a fresh thread.
- **Regeneration commits** are commits whose summary line matches
  `^<pkg>/<section>: regenerate \d+ intent tests` — they are skipped when deciding whether
  the intent tree is newer than the README or the review. Reason: the *A proposed deviation
  and the stop gate* decision in the design.
- **"No assumption"** is an `Assumption if unanswered:` line that is absent, empty, `none` or
  `—`. Reason: users write all four.
- **`--run-gate` takes an optional package.** Without one it checks the branch and the baseline
  only; with one it also requires `docs/packages/<pkg>/contract.md`. Reason: typed skills that
  have no package (`plan-repo`, `probe-source`, `set-constraints`) run the same gate.
- **`--surface <pkg>`** is the design's accepted suggestion and an optional addition to this
  phase: nothing in the core depends on it. The stop hook (phase 2) calls it only for the
  `surface` section and treats "flag missing" as PASS.
- **Parsers are module-level functions** with no side effects at import: `ROOT` is set by
  `set_root(path)`, defaulting to `Path.cwd()`. Reason: the hooks import the module from the
  plugin cache and run in the user's repo.
- **The state list is written in the module docstring as numbered bold items** (`1. **PROBE**
  — …`), the form `check-contracts`' `headings` owner parser reads, so phase 8 can declare the
  vocabulary claim with `run-package` as the reader. Reason: no second copy of the list.

## Files

| Path | Change |
|---|---|
| `skills/status/scripts/status.py` | rewritten in full to the specification below |
| `skills/status/SKILL.md` | rewritten: frontmatter `argument-hint`, body describing the output and the four flags |
| `skills/planning-templates/SKILL.md` | description and table updated: rows for `change.md`, `deviations-entry.md`, `review-report.md`; rows for `surface.md`, `integration.md`, `contract-delta.md` kept until phase 6 |
| `skills/planning-templates/references/package-contract.md` | item 2 gains the `surface` row rule; item 5 re-pointed at the `surface` section's design; every `/dev-team:implement-section`, `/dev-team:finalize-package`, `/dev-team:plan-change` mention replaced |
| `skills/planning-templates/references/change.md` | new — specification below |
| `skills/planning-templates/references/deviations-entry.md` | new — specification below |
| `skills/planning-templates/references/review-report.md` | new — specification below |
| `contracts.yml` | two `frontmatter` claims added (agents, skills) |
| `evals/fixtures/state-cases/` | new: `build.py` and one case directory per state and re-open rule (below) |

## Specification

### `status.py`

Usage line and module docstring, verbatim at the top of the file:

```
"""Derive where every package and section stands from docs/ and the code. Nothing is stored.

Usage:  python3 status.py [pkg] [--run-gate [pkg]] [--rounds <pkg>/<section>] [--surface <pkg>] [--repo]

A section is in exactly one state, decided in this order, first match wins:

1. **BLOCKED** — an open decision with no assumption binds the section (`docs/decisions.md`
   entry with `Status: open`, no `Assumption if unanswered:`, `Scope:` covering `repo`, the
   package or the section); or the newest review round says `request changes` and the cap is
   hit: round 3 or later, or round 2 whose `Convergence:` line has one or more prior unfixed.
2. **PLAN** — an open `spec-change:contract` entry names the section in `docs/deviations.md`.
3. **PROBE** — a source in the row's `source` column needs probing: an `api:` source whose
   `docs/sources/<token>.md` lacks a `## <pkg>/<section>` heading, or a `dataset:` source with
   no `docs/sources/<token>.md` at all.
4. **DESIGN** — no design at `docs/packages/<pkg>/design/<section>.md`; or an open
   `spec-change:design` entry; or an open `docs/changes/<slug>.md` whose **Affected sections**
   names the section and is newer than the design; or a probe doc the row names is newer than
   the design.
5. **TEST** — no `tests/intent/<section>/` under the package root; or the design is newer than
   the intent tree; or an open `spec-change:test` entry; or an `approved` deviation entry whose
   `Clause:` is cited by an intent test docstring that carries no `(deviation ` tag
   (regenerate).
6. **IMPLEMENT** — no README (`<section path>/README.md`; for `surface`,
   `docs/packages/<pkg>/interface.md`); or the intent tree, regeneration commits skipped, is
   newer than the README.
7. **REVIEW** — no review round, or the section's code (its path, `tests/unit/<section>`,
   `tests/intent/<section>` less regeneration commits, its README) is newer than the newest
   round's `Commit:`, or the newest round's verdict is `spec-change` with no open entry left.
8. **FIX n** — the newest round `n` says `request changes`, the cap is not hit, and the code is
   not newer than its `Commit:`.
9. **DONE** — the newest round approves and the code is not newer than its `Commit:`.

Ready: a section whose state is neither DONE nor BLOCKED and whose every in-package `depends
on` is DONE. The `surface` row depends on every other row whatever its cell says.
Shipped: the `surface` section is DONE. Rounds: the highest `n` over
`docs/reviews/<date>-<pkg>-<section>-r<n>-<a|b|s>.md`; a round's verdict is the worst of its
reports (request changes > spec-change > approve); a report with no `-r<n>-` is round 1.
"""
```

Output, per package, exactly these lines (columns separated by ` · `):

```
## <pkg>
section · state · evidence · ready · round · open spec-change · last commit
<section> · <STATE> · <one phrase: the rule that fired, with its path or commit> · yes|no · <n or —> · <kind or —> · <sha7 or —>
…
shipped: yes | no (surface <STATE>)
next: <exact command>
```

`evidence` examples: `no design`, `design 3f2a1c9 newer than tests 8b1e0d2`, `review r2 request
changes, 1 prior unfixed (cap)`, `D4 open, no assumption`, `api:polygon lacks ## data/ingest`,
`regenerate: data/ingest — 2026-09-27 — deviation`, `uncommitted: packages/data/src/data/ingest`.

`next`, one command with every name filled in:

| Condition | `next` |
|---|---|
| any section BLOCKED on a decision | `answer D<n> in docs/decisions.md, then /dev-team:run-package <pkg>` |
| any section BLOCKED on the review cap | `/dev-team:run-package <pkg> <section> --step REVIEW` (one more round) `or /dev-team:run-package <pkg> --defer` |
| any section ready | `/dev-team:run-package <pkg>` |
| every section DONE and an `approved` deviation or an open change file names the package | `/dev-team:sync-plan <pkg>` |
| every section DONE, nothing to sync, a package in `docs/architecture.md`'s Packages table has a contract and a section not DONE | `/dev-team:run-package <that package>` (first in table order) |
| every section DONE, nothing to sync, a package in `docs/architecture.md`'s Packages table has no contract | `/dev-team:plan-package <that package>` (first in table order) |
| every section DONE, nothing to sync, every package has a contract | `/dev-team:finalize-project` |
| no contract for `<pkg>` | `/dev-team:plan-package <pkg>` |

Flags:

- `--run-gate [pkg]` prints `run gate: PASS` or `run gate: FAIL` followed by one `  - <reason>`
  per failure, exit 1 on FAIL. Reasons, verbatim: `not a git repository; git init, create a
  branch, and re-run`; ``on `<branch>`; create a feature branch and re-run``; `uncommitted
  changes outside the user-edited files: <paths>; commit or stash them and re-run`; `<pkg>:
  missing docs/packages/<pkg>/contract.md — run /dev-team:plan-package <pkg>`. The baseline
  exemptions are `docs/decisions.md`, `docs/brief.md`, `docs/constraints.md` and anything under
  `.claude/agent-memory/`; the constant `BASELINE_EXEMPT` keeps them and is the one copy.
- `--rounds <pkg>/<section>` prints two lines and nothing else: `rounds: <n>` (the newest round
  number, 0 with none) and `next round: <n+1>`. No package report, so no test runs.
- `--surface <pkg>` prints `surface: PASS` or `surface: FAIL` with reasons: the three-way set
  difference between `__all__` in `src/<pkg>/__init__.py`, the **Public names** table of
  `docs/packages/<pkg>/interface.md`, and the union of `Public: yes` rows over the section
  READMEs' **Entry points and interfaces** tables; and the lazy-import check (`python -X
  importtime -c "import <pkg>"` names no section module). Exit 1 on FAIL; prints `surface:
  n/a (no interface.md)` and exits 0 before the surface ships.
- `--repo` prints the repo-wide gap list the documenter copies under **Known gaps**: six
  groups in this order, each a label line (`packages:`, `sections:`, `decisions:`,
  `spec-changes:`, `changes:`, `backlog:`) followed by one `  - <item>` line per item, or
  `  - none`. Items: `packages:` every package in the Packages table as `<pkg>: planned |
  building (<n>/<total> DONE) | shipped | no contract` (the `surface` row counts in `<total>`);
  `sections:` every section not DONE as `<pkg>/<section>: <STATE>`; `decisions:` every `D<n>`
  `open` or `deferred` as `D<n>: <question>`; `spec-changes:` every open entry by heading;
  `changes:` every open change file by slug; `backlog:` the count of unchecked
  `docs/followups.md` lines per target as `<target>: <n>`. The documenter derives none of
  these itself.

Parsers the hooks import, exported names and signatures (all module-level, no I/O at import):

```
set_root(path: Path) -> None
table_rows(md: str, must_have: tuple[str, ...]) -> list[dict[str, str]]
col(row: dict[str, str], name: str) -> str
packages() -> list[tuple[str, Path]]                       # (name, path) from architecture.md
sections(pkg: str) -> list[dict[str, str]]                 # the Sections table rows, path resolved
section_for_path(path: Path) -> tuple[str, str] | None     # (pkg, section) by longest section path prefix; the package top level → (pkg, "surface")
package_root(pkg: str) -> Path                             # packages/<pkg> or the root for path `.`
constraints_rows(pkg: str) -> list[tuple[str, str, str, str]]   # (heading, dimension, command with <pkg> filled, scope) over Floor, Enforced, Measured
guarded_items() -> list[str]                               # the Guarded bullet texts
exceptions_rows() -> list[dict[str, str]]                  # Exceptions rows
toolchain_commands() -> list[str]                          # one command per line of every fenced block under architecture.md's Toolchain heading
deviation_entries(pkg: str, section: str | None = None) -> list[dict[str, str]]   # heading fields: section, date, kind; and Clause, Said, Did, Found, Why, Status, Raised by, Resolved by
intent_docstrings(tree: Path) -> dict[str, str]           # test node id → first docstring line, via ast
section_state(pkg: str, section: str) -> tuple[str, str]   # (STATE, evidence)
rounds(pkg: str, section: str) -> int
newest_round(pkg: str, section: str) -> tuple[int, str, str | None, dict[str, str]]   # (n, verdict, Commit sha, header fields)
```

### `skills/status/SKILL.md`

```yaml
---
name: status
description: Print where every package and section stands — one state per section (PROBE, DESIGN, TEST, IMPLEMENT, REVIEW, FIX n, PLAN, DONE, BLOCKED), the ready set, whether the package shipped, and the exact next command — derived from docs/ and the code every time, never from a status file. Use whenever you have lost track, before planning the next package, or to see why run-package stopped.
argument-hint: "[pkg] [--run-gate [pkg]] [--rounds <pkg>/<section>] [--surface <pkg>] [--repo]"
disable-model-invocation: true
---
```

Body: run `python3 ${CLAUDE_SKILL_DIR}/scripts/status.py $ARGUMENTS` from the repo root, show
the output verbatim, then two or three lines on what the `next:` line means. One paragraph per
flag, in the words of the specification above. No other action.

### `planning-templates/SKILL.md`

Table rows, replacing the current table (the three old rows stay until phase 6 deletes their
files):

| You are writing | Read |
|---|---|
| `docs/architecture.md` — the repo contract | `references/repo-contract.md` |
| `docs/packages/<pkg>/contract.md` — the package contract | `references/package-contract.md` |
| `docs/changes/<slug>.md` — a change file | `references/change.md` |
| an entry in `docs/deviations.md` — a deviation or a spec-change | `references/deviations-entry.md` |
| `docs/reviews/<date>-<pkg>-<section>-r<n>-<a, b or s>.md` — a review report | `references/review-report.md` |
| `docs/sources/<source>.md` — a source probe, either kind | `references/source-probe.md` |
| `docs/plans/<slug>/contract-delta.md` | `references/contract-delta.md` (removed in phase 6) |
| `docs/packages/<pkg>/integration.md` | `references/integration.md` (removed in phase 6) |
| `docs/packages/<pkg>/surface.md` | `references/surface.md` (removed in phase 6) |

Description: `The heading-by-heading templates for the documents the loop writes and parses —
repo contract, package contract, change file, deviations entry, review report, source probe.
Invoke when about to write one of them and read only the reference for that document. Kept
out of the always-loaded prompts so a run pays for the templates it uses.`

### `references/package-contract.md`

Item 2 gains, after the `source` paragraph:

> The last row is always `surface`: responsibility *the package's pipelines (§4) and public
> surface (§5)*, path the package top level (`packages/<pkg>/src/<pkg>/`, or `src/<pkg>/` in a
> single-package repo), owner doc `docs/packages/<pkg>/design/surface.md`, `builds with` `—`,
> `depends on` every other section by name, `source` `—`. It is designed last, from the shipped
> READMEs, and its README is `docs/packages/<pkg>/interface.md`.

Item 5's last sentence names the `surface` section's design as what the list is checked
against. Every `/dev-team:implement-section`, `/dev-team:finalize-package` and
`/dev-team:plan-change` mention becomes `/dev-team:run-package` or is dropped.

### `references/change.md`

```
# `docs/changes/<slug>.md` — a change file

Written by the architect when an edit touches a built or shipped package (CHANGE outcome);
read by `status.py` (re-opens the named sections at DESIGN while `Status: open`), the designer
(`delta` mode), the implementer, the reviewer, and `sync-plan`, which applies it to the
canonical contracts and sets `Status: synced`. Budget 120 lines. The slug is one lowercase
token; the file is history once synced and is never edited afterwards except for that line.

The line after the title is `Status: open | synced`.

1. **Change goal** — one paragraph.
2. **Affected sections** — qualified `<pkg>/<section>` names, one line each with what changes
   for it, including the consumer sections this change adapts.
3. **Contract changes** — grouped **Repo contract**, **Package contract: <pkg>** (one per
   package), **Interface: <pkg>** (one per shipped surface altered); Added / Changed / Removed
   within each. Every altered shipped name with its old and new signature.
4. **Downstream impact** — table: consumer | shipped or planned | names affected | what breaks.
   Consumers from the grep `sync-plan` and the architect share (`from <pkg>\b|import <pkg>\b`
   over `packages/*/src`, plus every contract whose **Consumes** names the package).

Never claims a change to a canonical contract: the contracts are edited by `sync-plan` once
the sections are DONE, never here.
```

### `references/deviations-entry.md`

```
# `docs/deviations.md` — one entry per deviation or spec-change

Append-only; status lines are the only edits. Written by the implementer (`deviation`,
`spec-change`), the designer and the tester (`spec-change`), and read by the reviewer (which
sets `approved` or `rejected`), the tester (regenerates the tests an `approved` entry's clause
is cited by), `status.py` (an open spec-change re-opens its step), the stop hook (tolerates a
failing intent test whose docstring cites a `proposed` or `approved` clause) and `sync-plan`
(applies `approved` entries to the contracts and sets `synced`).

Entry heading: `## <pkg>/<section> — <date> — <kind>`, `kind` one of `deviation`,
`spec-change:test`, `spec-change:design`, `spec-change:contract`. Then these lines, in order:

1. **Clause** — the contract row or design item, as the reader cites it: `contract §2 row
   ingest`, `design §5 load_trades`, `design §6 EmptyFile`.
2. **Said** — what the document says, quoted.
3. **Did** — what was built (a deviation).
4. **Found** — the evidence, `file:line` or a probe doc heading (a spec-change).
5. **Why** — the reason. A deviation with no reason is a CRITICAL review finding.
6. **Status** — `proposed | approved | rejected | synced` for a deviation; `open | resolved`
   for a spec-change.
7. **Raised by** — the role and the run: `implementer — run-package data`.
8. **Resolved by** — the commit or run that closed it; `—` while open.

Never claims a boundary shape, a public name or a nullable column as an internal deviation:
those are `spec-change` entries, routed by level.
```

### `references/review-report.md`

````
# `docs/reviews/<date>-<pkg>-<section>-r<n>-<a, b or s>.md` — a review report

Written by the reviewer, one file per reviewer per round: `a` (conformance) and `b`
(correctness) in round 1, `s` from round 2 (`full`) and for a `defer` run. Read by
`status.py` (round, verdict, `Commit:`, `Convergence:`), the fix-round implementer (the queue),
the next reviewer (fixed / unfixed), never the documenter. `n` comes from `status.py --rounds`.
Never overwrite a report; the filename is the round.

Header, the first lines of the file, each `Key: value`:

```
# Review — <pkg>/<section> — round <n> — <focus>
Scope: <what was read>
Commit: <sha reviewed>
Verdict: approve | request changes | spec-change
Round: <n>
Focus: conformance | correctness | full | defer
Convergence: <k> prior unfixed, <m> new        (round 2 and later)
Diff: <sha>..HEAD                              (round 2 and later)
```

Then these headings, in order; an empty one is written with `- none`:

1. **CRITICAL** — one line per finding: `<file:line> — <finding> — <what to change>`. Only the
   closed list: a break (contract, decided `D<n>`, consumed shipped signature), a wrong result
   on the main path, a security finding, a silent or unreasoned deviation.
2. **WARNING** — should fix; the fix round picks these up.
3. **SUGGESTION** — consider; **Measured** values from the gate's output go here.
4. **Coverage** — `conformance` and `full` only: table `clause or design item | pass / fail /
   can't-tell | file:line`, one row per contract clause and design item.
5. **Carried** — round 2 and later: each prior CRITICAL as `fixed` or `unfixed`, worded as it
   was, with `file:line` where it stands.
6. **Spec-change** — when that is the verdict: the level (`test | design | contract`) and the
   evidence; the same content as the `docs/deviations.md` entry the reviewer appends.
7. **Deferred** — `defer` runs only: each standing CRITICAL and the `docs/followups.md` line it
   became.

A round's verdict is the worst over its reports. Never a mechanical failure (the gate owns
those), never a fix, never a CRITICAL outside the closed list, and on round 2 or later never a
CRITICAL on code the fix did not touch that the previous round did not raise.
````

### `contracts.yml` additions

```yaml
frontmatter:
  - name: every agent uses only fields plugin agents honor
    kind: agent
    files: 'agents/*.md'
  - name: every skill uses only documented frontmatter fields
    kind: skill
    files: 'skills/*/SKILL.md'
```

### `evals/fixtures/state-cases/`

`build.py <case> <dest>` copies `two-package/`'s brief and dataset, runs `git init` on branch
`build`, then applies the case: it writes the files the case names and makes one commit per
step in the order the case lists, so commit order is the evidence. `README.md` in the directory
lists every case and its expected row. Cases, one directory each holding `case.json`
(`steps: [{files: {...}, message: "..."}]`, `expect: {section: "...", state: "...", ready:
true|false, rounds: n}`):

| Case | Expected |
|---|---|
| `no-contract` | `next: /dev-team:plan-package data` |
| `probe-api-missing-heading` | `ingest · PROBE`, evidence names `api:polygon` |
| `probe-dataset-no-doc` | `ingest · PROBE` |
| `design-missing` | `ingest · DESIGN`, ready yes |
| `design-dependency-not-done` | `clean · DESIGN`, ready no (ingest not DONE) |
| `test-missing` | `ingest · TEST` |
| `test-design-newer` | `ingest · TEST`, evidence names both commits |
| `test-regenerate` | `ingest · TEST`, evidence `regenerate:` |
| `implement-missing-readme` | `ingest · IMPLEMENT` |
| `implement-tests-newer` | `ingest · IMPLEMENT` |
| `implement-regeneration-skipped` | `ingest · DONE` (the newer intent commit is a regeneration) |
| `review-none` | `ingest · REVIEW`, round 0 |
| `review-code-newer` | `ingest · REVIEW`, round 1 |
| `fix-round-1` | `ingest · FIX 1` (round 1 pair, `a` approve and `b` request changes → worst) |
| `blocked-cap-round-3` | `ingest · BLOCKED` |
| `blocked-cap-round-2-unfixed` | `ingest · BLOCKED` (`Convergence: 1 prior unfixed, 0 new`) |
| `not-blocked-round-2-fixed` | `ingest · FIX 2` (`Convergence: 0 prior unfixed, 1 new`) |
| `blocked-decision` | `ingest · BLOCKED`, evidence `D3 open, no assumption` |
| `plan-spec-change-contract` | `ingest · PLAN` |
| `design-spec-change-design` | `ingest · DESIGN` |
| `design-change-file-open` | `ingest · DESIGN`, evidence names the slug |
| `design-probe-newer` | `ingest · DESIGN` |
| `done-and-surface-ready` | `ingest`, `clean`, `storage` DONE; `surface · DESIGN`, ready yes; `shipped: no (surface DESIGN)` |
| `shipped` | `shipped: yes`; `next: /dev-team:sync-plan data` when an approved deviation is open, else `/dev-team:plan-package analysis` |
| `old-report-name` | a `2026-09-01-data-ingest.md` report reads as round 1, `s` |
| `run-gate-main` | `--run-gate` FAIL, ``on `main` `` |
| `run-gate-dirty` | `--run-gate` FAIL naming the path; a dirty `docs/decisions.md` alone PASSes |
| `rounds` | `--rounds data/ingest` prints `rounds: 2` and `next round: 3` |
| `repo` | `--repo` lists the open D, the open spec-change and the unbuilt section |

`check.py` runs every case into a temporary directory, runs `status.py` there, and exits 1
naming each case whose expectation is not in the output.

## Steps

1. Write the three new references and edit `package-contract.md` and `planning-templates/SKILL.md`.
2. Rewrite `status.py` to the specification; keep `table_rows`, `col`, `git`, `last_commit`,
   `uncommitted`, `changed_since` (with the regeneration-commit skip) as the base.
3. Rewrite `skills/status/SKILL.md`.
4. Write `evals/fixtures/state-cases/` and run `check.py` until every case passes.
5. Add the two `frontmatter` claims to `contracts.yml`; plant a bogus key (`allowed_tools`) in
   a scratch copy of one agent and watch the claim fail, then remove it.
6. The plugin's own rules (`CLAUDE.md` three-file rule: no skill added or removed).
7. `check-contracts`; `build-site`.
8. Evals — the table below, through `run-evals`, logged with `log-eval`.
9. Commit: `dev-team remake (phase 01): status.py to the state spec; change, deviations and review templates`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 1.1 | mechanical | `skills/status/scripts/status.py` | — | `evals/fixtures/state-cases/check.py` | exit 0; every case listed in the fixture README passes |
| 1.2 | mechanical | `contracts.yml` | — | `check-contracts`, plus the planted `allowed_tools` key | all claims PASS; the planted key FAILs the agent `frontmatter` claim |
| 1.3 | mechanical | the three new references | — | `check-contracts`' owner parser: a scratch `headings` claim with `owner_span: ['1. **Clause**', null]` and a reader citing `Resolved by` | the claim parses eight items from `deviations-entry.md` and seven from `review-report.md` (run and discard; the real claims land in phases 3 and 5) |
| 1.4 | load | `status` | — | `claude --plugin-dir ./dev-team -p "/dev-team:status --repo"` in a `state-cases` build | the output has `packages:` and `next:` lines |

## Done when

- `python3 evals/fixtures/state-cases/check.py` exits 0.
- `python3 skills/status/scripts/status.py --run-gate` on `main` exits 1 with the branch reason.
- `grep -c '^\d*\. \*\*' skills/status/scripts/status.py` counts nine state items in the docstring.
- `check-contracts` prints all PASS with the two `frontmatter` claims counted.
- `build-site` exits 0.
- `evals/README.md` has a row for this phase's log.
- The ledger row for phase 1 reads `done`.

## Deviations

- **Eval 1.4's pass bar asked for a `next:` line from `--repo`**, which the Specification above
  defines as six groups and no `next:`. Done instead: `packages:` was checked on
  `/dev-team:status --repo` and `next:` on `/dev-team:status data`, both through `claude
  --plugin-dir`. The bar was wrong, not the script. Log:
  `evals/2026-09-27-remake-phase1-state-and-templates.md`.
- **Rule 4's probe-doc clause ignores other sections' entries.** Read literally ("a probe doc
  the row names is newer than the design"), the PROBE step for `data/clean` appending
  `## data/clean` to `docs/sources/trades.md` would re-open `data/ingest` at DESIGN. The
  design's *Stale when* for a probe doc says a new consuming section does not make it stale.
  So the rule compares the doc as of the design's commit with the doc now, each less every
  other section's `## <pkg>/<section>` block; it fires only when commit order says newer
  *and* that comparison differs. Case `design-probe-other-section` pins it.
- **The fixture goes beyond the listed shape.** `case.json` steps may be macros
  (`{"do": "done", "section": "ingest"}`) as well as `{files, message}`, and `expect` adds
  `evidence` (a regex), `contains`, `absent` and `exit`. There are 36 cases, not 29: the
  `shipped` and `run-gate-dirty` rows each named two outcomes and became two cases, plus
  `design-probe-other-section`, `run-gate-no-contract`, and three `--surface` cases.
- **`skills/status/SKILL.md` still cites `docs/constraints.md`'s Floor and Enforced**, in
  one closing sentence (the stop hook runs those rows through this script's parser). The
  overview lists the `status` SKILL.md as a reader that leaves. Removing it would fail the
  existing constraints-headings claim, and this phase's Files do not touch that claim. The
  claim's reader list is re-pointed with the hook in phase 2.
