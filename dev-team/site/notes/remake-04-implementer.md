# 04 — implementer

Phase 04. Rewrites the implementer: it builds one section to its design, the `surface` section
included (the old surface mode becomes the last row of the Sections table, with `interface.md`
as its README), logs internal deviations as `proposed` entries in `docs/deviations.md`, raises
`spec-change` with evidence, writes the `.dev-team/stop` marker before returning `blocked` or
`spec-change`, and drops its constraints step and its branch and baseline check because the
stop gate and the run gate own them. It fixes a gate failure into its own commit with `git
commit --amend --no-edit`. In the same phase `git-workflow-and-versioning` shrinks to §Project
convention with a run-gate pointer, the new message table and the lock-retry rule, and
`workspace-scaffold` derives import contracts 2 and 3 from the Sections table and runs the
`docs/constraints.md` rows in CI. The gap it closes: a correct deviation from a wrong contract
was graded CRITICAL, the implementer approved its own spec changes in a README paragraph, and
every mechanical check it ran was run again by the reviewer.

## Decisions

- **The design's order of authority shrinks to five**: `docs/constraints.md` (for the checks it
  names only), `docs/decisions.md` (decided, in scope), an open `docs/changes/<slug>.md` naming
  the section, `docs/packages/<pkg>/contract.md`, `docs/architecture.md`, then the design. The
  integration doc and the contract-delta are gone. The reviewer (phase 5) carries the same
  list; the existing `contracts.yml` order-of-authority claim keeps enforcing that.
- **Deviation vs spec-change is decided by the clause**: a clause inside the section (a
  module, an internal signature, an error message) is a `deviation`; a boundary shape, a public
  name, a consumed shipped signature or a nullable column is a `spec-change` at level `contract`
  when the contract says it, `design` when only the design does, `test` when the code and the
  design agree and an intent test asserts otherwise. Reason: the design's deviations-entry
  never-claims.
- **Consumed-side mismatches:** when a shipped README or `interface.md` differs from the
  contract for a name this section consumes, the implementer looks in `docs/deviations.md`
  first. An entry covering the difference (an `approved` deviation or any `spec-change` entry
  naming the clause) means the ledger already knows: build against the shipped document and
  say so in the return. No entry means the contract and the shipped code disagree with nobody
  having recorded it: append a `spec-change:contract` entry (`Found:` the README table row and
  the contract row), write the marker, build nothing further, return `Result: spec-change`.
  The contradiction is met in step 5, before any code, so the run stops there.
- **Entry details:** the heading date is ISO (`2026-09-27`); a fresh entry's `Resolved by:` is
  `—`; `Raised by:` is `implementer — <Run:>`. The return's `Intent tests:` line is the end
  count; `Gate:` reads `not run` when no stop hook fired (a harness or an old session).
- **Gate failures are amended in.** After an exit-2 stop, the fix is staged and folded into the
  run's commit with `git commit --amend --no-edit`; the one time an agent rewrites a commit,
  because it is this run's own and unpushed. §Project convention rule 4 states the exception.
- **`.gitignore`** gains `.dev-team/` in the implementer's `.gitignore` step, first section of
  the repo.
- **The `surface` section's README is `docs/packages/<pkg>/interface.md`** with today's seven
  headings; the implementer also writes `docs/api/<pkg>.md` and its `mkdocs.yml` nav entry,
  the `forbidden` import contract, and `[project.scripts]`, as the old surface mode did. The
  ledger sweep stays. The old preconditions (every section reviewed, no open follow-ups) go:
  the surface is DESIGN-ready only when every other section is DONE, which is the same check
  made by `status.py`.
- **§Project convention** rules, renumbered: 1 **Run gate** (the check moved to `status.py
  --run-gate`; the driver runs it once per run, a typed skill runs it first; an agent spawned by
  the driver does not run it), 2 **Staging**, 3 **Message**, 4 **One commit per run** (with the
  amend exception), 5 **Lock** (retry), 6 **Hygiene**. Reason: the design's *Parallel commits*
  decision and the run gate.

## Files

| Path | Change |
|---|---|
| `agents/implementer.md` | rewritten in full — specification below |
| `skills/git-workflow-and-versioning/SKILL.md` | §Project convention rewritten; everything below **Core Principles** unchanged; description updated |
| `skills/workspace-scaffold/SKILL.md` | §3: contracts 2 and 3 derived from the Sections table's `Depends on`, written by the `surface` section's implementer (2) and the first section's (3); §5: CI runs the constraints rows; every `/dev-team:finalize-package` and `/dev-team:implement-section` mention replaced |
| `contracts.yml` | §Project convention claim: owner span end stays `## Core Principles`, implementer reader span updated; deviations-entry claim gains the implementer reader; section-README and interface.md heading claims keep the implementer as owner with the new `owner_span` markers; the `As shipped` claim loses its implementer reader |

## Specification

### `agents/implementer.md`

```yaml
---
name: implementer
description: Implements one section of one package from its design, the contracts, the shipped READMEs it consumes, the intent tests and the latest review round; the surface section is the package's public surface and its README is interface.md. Writes code, unit tests and the README, logs deviations as proposed entries, raises spec-change with evidence, and finishes only when the stop gate is green. Spawned by /dev-team:run-package at the IMPLEMENT and FIX steps.
tools: Read, Write, Edit, Glob, Grep, Bash, Skill, WebSearch, WebFetch
model: inherit
memory: project
skills:
  - project-structure
  - python-style-guide
  - git-workflow-and-versioning
  - test-driven-development
color: green
---
```

Headings, in order: `## Inputs`, `## Order of authority`, `## The decisions file`, `## Decisions
and markers`, `## Blocking rules`, `## Procedure`, `## Files outside your section`, `## Section
README template`, `## The surface section`, `## Deviations and spec-changes`, `## The stop
gate`, `## Return message`, `## Commit`, `## Memory`.

**Inputs** table: `Section:`, `Design:`, `Contract:`, `Repo contract:`, `Dependency READMEs:`,
`Upstream interfaces:`, `Source probes:` (as the designer's), plus `Intent tests: <package
root>/tests/intent/<section>/`, `Review: <the newest round's report paths, comma-separated> |
none`, `Round: <n>` (1 on the first build; `n+1` in FIX n), `Change file: docs/changes/<slug>.md
| none`, `Run: run-package <pkg>`.

**Order of authority**: the five documents in **Decisions**, numbered; then the consumed-side
rule as today (README over design, `interface.md` over contract, probe doc over the design's
assumed shape). The marker line `## Order of authority` … `## The decisions file` stays the
owner span of the existing claim.

**Blocking rules** keep: no contract (`/dev-team:plan-repo` or `/dev-team:map-repo` named as
the fix); an unanswerable question that defines the section; an unbuilt dependency (a `depends
on` section with no README, an upstream package with neither `interface.md` nor code). Gone:
branch, dirty tree, open plan finding, unresolved integration deviation, "a shipped surface
would change" (that is a `spec-change:contract` now). Every blocker: write `.dev-team/stop`
with the line `blocked`, commit nothing, return.

**Procedure**, numbered:

0. Run the intent suite; note the count.
1. Scaffold or match the layout (as today; `workspace-scaffold` §1–§2; contract 3 from the
   Sections table's `Depends on`; `.dev-team/` and the tool caches into `.gitignore`).
2. Invoke the design's **Skills used**.
3. Security (as today, verbatim).
4. Resolve stale decision markers (as today).
5. Read what you consume (as today; the missing-probe fallback stays, filing a `spec-change:
   design` entry instead of a followups line when the observed shape differs).
6. Pick up the review: read every report in `Review:`; every **CRITICAL** and **WARNING**
   line addressed to this section is part of the task; a bug gets the Prove-It pattern. Read
   `docs/followups.md` lines for this section and take any you can (tick `[x] <date>`).
7. Build (as today).
8. Test: the design's **Tests**, the unit suite, `lint-imports`, then the intent suite; a
   failing intent test is fixed in the code or becomes a `proposed` deviation entry (below); a
   test still failing after two attempts → `debugging-and-error-recovery`.
9. Size check (as today).
10. Record `Applied:` lines (as today).
11. Section README (below).
12. Commit.
13. Finish; the stop gate runs. On exit 2, fix what it names, stage, `git commit --amend
    --no-edit`, finish again.

**Deviations and spec-changes**: read
`${CLAUDE_PLUGIN_ROOT}/skills/planning-templates/references/deviations-entry.md` with the Read
tool before writing an entry. A deviation → one `deviation` entry, `Status: proposed`, `Raised
by: implementer — <Run:>`, and README item 7 cites it by heading rather than restating it. A
spec-change → one `spec-change:<level>` entry, `Status: open`, `Found:` with `file:line` or the
probe doc heading; then write `.dev-team/stop` with the line `spec-change`, commit the ledger
and whatever was built, and return `Result: spec-change`. Never edit `tests/intent/`, a
contract or a design.

**The surface section**: what differs — the design is `docs/packages/<pkg>/design/surface.md`;
build `src/<pkg>/__init__.py` (lazy re-exports, names = the design's `Public: yes` rows
reconciled against the READMEs; a name no README provides is a `spec-change:contract`),
`pipelines/`, `cli.py` and `[project.scripts]`, the `forbidden` import contract (contract 2),
`docs/api/<pkg>.md` and its nav entry, tests per pipeline and command; the ledger sweep; the
README is `docs/packages/<pkg>/interface.md` with the seven headings **Public names**,
**Pipelines**, **CLI commands**, **Configuration**, **Shapes provided**, **Deviations**,
**Consumers (computed)** — the text of the old surface mode's `interface.md` block, with
`surface.md` references replaced by the design and `/dev-team:plan-change` by `sync-plan`.

**The stop gate**: what it runs, what the exit-2 text looks like, and the three-attempt rule,
in the words of phase 02's specification; the marker file's two lines; `.dev-team/gate.txt` as
the reviewer's source.

**Return message**: first line `Result: done | blocked | spec-change`; under 25 lines: files;
test command and result; `lint-imports`; `Intent tests: <pass>/<total>`; `Gate: PASS | passed
after <n> attempts | let through after 3 attempts`; deviations (entry headings); spec-change
(entry heading); `D<n>` applied; markers left; review findings addressed; README path;
`Commit: <sha>`.

**Commit**: §Project convention (preloaded); stage the paths listed; scope `<pkg>/<section>`
(`<pkg>/surface` for the surface); trailer from `Run:`.

### `git-workflow-and-versioning/SKILL.md` §Project convention

```
## Project convention

Every dev-team run that writes files ends by committing exactly those files. These rules are
the one copy; agents cite this section and do not restate it.

1. **Run gate** — The branch and baseline checks are `status.py --run-gate` (in this plugin's
   `skills/status/scripts/status.py`): not on `main` or `master`, a git repository, and a tree
   clean but for `docs/decisions.md`, `docs/brief.md`, `docs/constraints.md` and
   `.claude/agent-memory/`. `/dev-team:run-package` runs it once before its first spawn; a typed
   skill that forks an agent runs it first and returns its FAIL lines as the blocker. An agent
   the driver spawned does not run it again.

2. **Staging** — Stage by explicit path — the paths the run wrote, which are the paths its
   return message lists. Never `git add -A`, `git add .`, or `git commit -a`. A file the run
   did not write is never staged, even if it is modified.

3. **Message** — First line `<scope>: <imperative summary>`, at most 72 characters:

   | Run | `<scope>` | Example |
   |---|---|---|
   | designer | `<pkg>/<section>` | `data/ingest: design` |
   | tester | `<pkg>/<section>` | `data/ingest: 14 intent tests from design` · `data/ingest: regenerate 2 intent tests` |
   | implementer | `<pkg>/<section>` · `<pkg>/surface` | `data/ingest: parse trades.csv into Trade rows` |
   | reviewer | `review <pkg>/<section>` | `review data/ingest r1-a: request changes (2 critical)` |
   | researcher | `probe <source>` | `probe polygon: aggregates for data/ingest` |
   | architect | `plan <target>` | `plan data: contract with surface row` |
   | curator | `legacy` | `legacy: inventory of ../old-repo` |
   | documenter | `docs` | `docs: package READMEs, root README` |
   | set-constraints | `docs` | `docs: set constraints (coverage 80, mypy strict, docstrings 95)` |

   Body: blank line, then one trailer and nothing else: `Dev-Team-Run: <skill> <argument as
   typed>` — under the driver, `run-package <pkg>` for every agent it spawns.

4. **One commit per run** — A run never makes two commits, and a run that wrote nothing
   commits nothing and returns `Commit: none`. The one exception to "never two": an
   implementer whose stop gate exits 2 stages its fix and runs `git commit --amend --no-edit`
   on its own, unpushed commit.

5. **Lock** — Agents run in parallel and commit concurrently. When `git commit` or `git add`
   fails with `.git/index.lock`, wait two seconds and retry, up to ten times; a failure after
   that is a blocker quoting the error.

6. **Hygiene** — The run's own verification has already passed before the commit step. If a
   pre-commit hook rejects the commit, fix what it names and retry once; a second rejection is
   a blocker quoting the hook output.
```

The `## Core Principles` heading and everything below stay. Description: `Structures git
workflow practices — atomic commits, descriptive messages, save points, pre-commit hygiene.
Preloaded into every dev-team agent that commits. §Project convention is the commit rule every
agent follows.`

### `contracts.yml`

- §Project convention claim: implementer reader span `['§Project convention', 'trailer from']`.
- deviations-entry claim gains `- file: agents/implementer.md` with `cites: ['Clause', 'Said',
  'Did', 'Found', 'Why', 'Status', 'Raised by']`.
- interface.md headings claim: `owner_span: ['**Public names**', null]` under the new `## The
  surface section` heading — set the start marker to the exact line the new file uses.
- section README claim: `owner_span: ['## Section README template', '## The surface section']`.
- `As shipped` claim: remove the `agents/implementer.md` reader.

## Steps

1. `git-workflow-and-versioning/SKILL.md`.
2. `workspace-scaffold/SKILL.md`.
3. `agents/implementer.md`.
4. `contracts.yml` edits; plant a bare `git add -A` in a scratch copy and watch the staging
   claim fail.
5. The plugin's own rules (no skill added or removed).
6. `check-contracts`; `build-site`.
7. Evals, through `run-evals`, logged with `log-eval`.
8. Commit: `dev-team remake (phase 04): implementer builds the surface as a section, deviations ledger, stop marker; commit rule with run gate and lock retry`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 4.1 | mechanical | `contracts.yml` | — | `check-contracts` + the planted `git add -A` | all PASS; the plant FAILs |
| 4.2 | behavioral | `implementer` | previous | `evals/sets/implementer.json` 1–8 (regression) | pass rate for `with_skill` ≥ the 2026-09-20 log's 87.5%, and ≥ `old_skill`'s in this run |
| 4.3 | behavioral | `implementer` | previous | `evals/sets/implementer.json` 9, 10 | every expectation passes for `with_skill`; `old_skill` fails the `proposed` entry and the marker file |
| 4.4 | load | `implementer` | — | the agents listing | the name appears |

## Done when

- `grep -c 'constraints.md' agents/implementer.md` counts only the order-of-authority row and the gate paragraph (no "run every Floor and Enforced row" step).
- `grep -n 'index.lock' skills/git-workflow-and-versioning/SKILL.md` finds rule 5.
- `check-contracts` all PASS; `build-site` exits 0.
- Logs for 4.1–4.4 in `evals/README.md`.
- The ledger row for phase 4 reads `done`.

## Deviations

- **Four other agents' commit sentences re-pointed.** The note renames §Project convention's
  rules and drops **Branch** and **Baseline**, but `reviewer.md`, `architect.md`, `curator.md`
  and `documenter.md` still told their agent to check those two rules, and the commit-rule
  claim reads the bold names in each reader's span. Left alone, `check-contracts` fails on four
  readers. Done instead: one sentence in each now reads *check its **Run gate** and
  **Staging** rules … return the run gate's FAIL lines if it fails*, each span's end marker
  kept. Phases 5, 6 and 9 rewrite those agents anyway; the curator is unchanged by the design
  except for this sentence. `skills/set-constraints/SKILL.md` still names **Branch** and
  **Baseline** in prose (no claim reads it); that is phase 10's wording change.
- **The reviewer's order-of-authority list re-pointed.** The note drops the integration doc
  and the contract-delta from the implementer's list and says the reviewer (phase 5) carries
  the same list, with the existing claim enforcing it. At this boundary the reviewer still
  named **The integration doc for this run**, which the owner no longer has, so the claim
  failed. Done: the reviewer's items 3 and 4 became the implementer's item 3 (**An open
  `docs/changes/<slug>.md` naming the section**) and the rest renumbered; its item 6 text
  (*read together with its **As shipped** sections*) is phase 5's to rewrite.
- **The pathspec commit is in the rules, not only the lock rule.** Per the ledger (phase 0,
  PF-5 false as stated): **Staging** requires `git add <paths>` then `git commit -m … --
  <paths>`, and **One commit per run**'s amend exception is `git commit --amend --no-edit --
  <paths>`, matching the gate's exit-2 text. **Lock** says *never delete the lock file*. The
  message table carries the designer's and tester's phase-3 summaries and a no-`Run:`
  trailer form (`designer data/ingest`).
- **No `docs/index.md` at scaffold.** The note keeps step 1 "as today", which writes a stub
  `docs/index.md` with a `Home` nav entry. The write guard (phase 2, as the design specifies)
  refuses the implementer anything under `docs/` but the ledgers, `interface.md` and
  `docs/api/*.md`. Done: `workspace-scaffold` §4's nav starts at `Architecture` and
  `Decisions`, and `/dev-team:finalize-project` writes `index.md` and adds `Home`; the
  implementer's step 1 no longer mentions the stub.
- **Backlog lines are taken, not ticked.** The note's step 6 says the implementer ticks the
  `docs/followups.md` lines it takes. The write guard refuses it that file. Done: the
  implementer lists the lines it took under *backlog lines taken* in its return, and the
  **Decisions and markers** row that filed a follow-up now reports *decided but blocked* in the
  return instead. Whoever ticks them is an open question for the guard or the design (a ledger
  *noticed* line).
- **The missing-probe fallback stops.** The note says a differing observed shape files a
  `spec-change:design` entry "instead of a followups line". A spec-change entry means the
  marker and `Result: spec-change`, per the note's own **Deviations and spec-changes**, so the
  fallback now stops the run there rather than building on and continuing.
- **`Gate:` on a first return.** The implementer cannot see a gate pass (exit 0 stderr reaches
  no one, phase 2), so the return line is defined by what the agent has seen: `PASS` on a
  first return (a failing gate would have stopped it), `passed after <n> attempts` after
  `n-1` exit-2s, `let through after 3 attempts` when finishing a third time, `not run` when a
  harness says no hook runs.
- **Blocking rule "no contract"** also names `/dev-team:plan-package <pkg>` when only the
  package contract is missing; the note named only `plan-repo` and `map-repo`.
- **The `Clause:` of a deviation** is written `design §<n> <item>`, since `status.clause_key()`
  needs the literal `design` to match the intent test's docstring (phase 3's *noticed*).
- **Commit prefix `(phase 4)`.** The note's step 8 writes `(phase 04)`; the ledger resolves SHAs
  with `--grep='(phase N)'`, and phases 1–3 used the unpadded form, so this commit does too.
- **Evals 5–8, expectation 2 reworded** in `evals/sets/implementer.json` on the graders' critique
  (it measured whether a proxy executor admitted an orientation read, not the target); no verdict
  changed. See the eval log.
