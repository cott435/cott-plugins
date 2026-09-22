# New repo, package by package

```
/dev-team:shape-brief "a quant research platform: data, forecasting, trading agents, portfolio optimisation"
```

Runs **in your conversation**, not as a subagent, because it asks. It restates the idea, maps
the domain — including the areas you did not name — and narrows it with you: each capability
*now*, *later*, or *out*. Then it asks about the constraints that would change the design and
what makes the first version done, and writes `docs/brief.md`. The brief says `Status: draft`
until you approve it, so the discussion can span sessions, and `plan-repo` refuses a draft.
Skip this step if you already have a brief you trust.

Every forked run from here on ends in one commit of the files it wrote, and refuses to start on
`main`/`master` or with other uncommitted changes (your hand edits to `docs/decisions.md`,
`docs/brief.md` and `docs/constraints.md` excepted). So the repo is a git repository on a
feature branch before the first one — `git init`, `git switch -c build`, and commit the brief.

```
/dev-team:set-constraints
```

Optional, and any time before the first review; also in your conversation. Four questions —
coverage floor, type strictness, docstring coverage, anything to measure without enforcing —
each with a default, then `docs/constraints.md`: the commands the implementer runs after its
tests, the reviewer runs before anything else, and `/dev-team:status --gate` runs before a
package is finalized. Skip it and the Toolchain's commands are the only bar.

```
/dev-team:plan-repo
```

Forks into the **architect** at repo scope. It reads your brief and your project skills and
writes `docs/architecture.md` — the **repo contract**: the package list with responsibilities
and the brief capabilities each one **covers**,
the dependency graph as an import-linter block, the **shapes** that cross each boundary (a
DataFrame of bars with these columns, a `Lot` record — not function signatures), the shared
conventions (error format, log keys, config prefixes, timezone, ID types), and the toolchain
(workspace tool, test and lint commands, docs renderer). It never spawns designers: packages
are planned one at a time, below.

If it has questions it cannot settle, it **stops** — see **Questions** on the home page — and you
re-run.

## When the contract comes out wrong

Reading `docs/architecture.md` is often when a brief's gaps show: the architect filled a hole
with a reasonable guess, and the guess is not what you meant. Correct the brief, not the
contract:

```
/dev-team:shape-brief        # "the contract assumed live trading; this is research only"
/dev-team:plan-repo
```

or, for a short correction, `/dev-team:plan-repo --revise "research only — no live execution"`.

The architect keeps `docs/history/brief-contracted.md`, a copy of the brief the contract was
written from, so it can tell a corrected brief from one that only grew. A correction puts it in
**revise** mode: it archives the old contract to `docs/history/`, rewrites it from the
corrected brief, retires open decisions whose premise is gone, turns a decided one that now
conflicts into a question, and lists the package plans that went stale — any package whose
boundaries changed, or whose covered capabilities changed in the brief. Anything a shipped or
already-built package is bound by stays as it is and becomes a stub pointing at
`/dev-team:plan-change`. Growing the scope instead is **extend** — see
[Adding a package](add-package.md).

## Then each package

```
/dev-team:plan-package data
```

Forks into the architect at package scope. It reads the repo contract; the brief rows for the
capabilities `data` covers — your notes on them, and nothing else from the brief; and, for
every package `data` depends on, that package's `docs/packages/<dep>/interface.md` — the
surface as shipped.
Then:

1. Writes `docs/packages/data/contract.md` — the **package contract**: the capabilities it
   covers with your notes quoted verbatim (designers read this, not the brief), the section list, what
   each section returns to its siblings (signatures now, not shapes), the pipelines that run
   the sections in order (`download → clean → audit → store`), what the package will expose,
   and a `Consumes` table of every upstream name it uses. Its Sections table names the
   external `source` each section consumes, each written `<kind>:<token>` — `api:polygon`,
   `dataset:trades-2024`.
2. Spawns one **researcher** per source, in parallel, and writes each one to
   `docs/sources/<source>.md` — a repo-wide path, so a source two packages consume is probed
   once. An `api` researcher checks the credential (env or a root `.env`), reads the vendor's
   reference, calls the real read endpoints plus one bad request each, and records the
   **observed** schema, pagination, limits, auth flow and error shapes with a scrubbed sample
   and a re-runnable probe; it never sends a write, so a write endpoint is recorded as
   documented rather than observed. A `dataset` researcher opens the data and records its
   columns, dtypes, null rates, duplicates and — when the purpose names a modeling task — its
   target, leakage, split and supported tasks, as statistics and never as rows. A source that
   cannot be reached **stops** the run here, naming it, before any design exists.
3. Picks the **spine** — the section the most other sections depend on, through `Depends on`;
   in `ingest → clean → storage` that is `ingest` — and spawns one **designer** for it alone,
   given its probe doc. A package of one or two sections, or `--all`, skips this: every section
   gets a designer at once, in parallel. Each writes `docs/packages/data/design/<section>.md`
   and returns ten lines.
4. Reads the designs and writes `docs/packages/data/integration.md`: a **Spine** heading
   (`Status: spine only` on this first run), deviations, mismatches, the dependency order of
   every section, shared work, risks, decisions needed — and **Repo contract deviations**,
   which it may resolve by editing the repo contract only when no shipped package is bound by
   the shape.
5. On a spine run, stops here and names the spine's four commands, which
   `/dev-team:run-package data` types for you. Otherwise writes `docs/packages/data/surface.md` — the design of the public surface, now that the
   section interfaces are concrete: the `__all__` names (only those a downstream package or a
   CLI command consumes, each with its consumer named), the pipeline signatures, the CLI
   commands with every argument, the import-linter contracts for this package.
6. Appends `D<n>` stubs to `docs/decisions.md`.

### Build the spine, complete the plan

```
/dev-team:run-package data
```

Runs **in your conversation** and spawns each agent itself, one at a time, handing it the same
skill file the manual command would fork. It starts with `/dev-team:status data --run-gate`: a
feature branch, a clean tree (your three hand-edited files excepted), and a plan that is
spine-only or passes the plan gate. On this spine-only plan it:

1. builds `ingest` — `test-section` (intent tests, red), `implement-section`, `test-section`
   again (reconcile), `review-section`, rebuilding on `request changes` while the review
   says the loop is converging (it counts rounds from `docs/reviews/`, and stops on round 2
   with a prior finding unfixed, or on round 3);
2. runs `sync-design data`, so `ingest`'s design gains an **As shipped** table of what the
   build changed — the design went through every implementer pass untouched, and without
   this the plan review would check the next two designs' seams against a spine that no
   longer exists;
3. re-runs `plan-package data`, which designs `clean` and `storage` with `Sibling shipped:`
   naming `ingest`'s README — so the two designs that consume `ingest` are written against
   what it actually returns, not what its design projected — then rewrites `integration.md`
   with `Status: complete` and writes `surface.md`;
4. runs `review-plan data`, and **stops** so you can answer decisions before the rest is built.

`review-plan` forks the reviewer in plan mode. Someone who wrote none of it checks the
contract, every design, `integration.md` and `surface.md` against each other and against the
repo contract, the ledger, the upstream `interface.md` files and the probe docs: every consumed
name has a provider with the same signature, every open question became a `D<n>`, every
deviation is resolved, every public name has a consumer. It writes
`docs/reviews/<date>-data-plan.md` and files each CRITICAL to `docs/followups.md` as
`data/plan: …`. On `request changes`, run `/dev-team:plan-package data`: it re-delegates the
sections a finding names — and, for a finding whose cause is one fact several designs assume
(the review writes that one once, with a `touches:` list), every section the fact reaches,
recorded under `integration.md`'s **Propagation** heading — and ticks the findings. Then run
`/dev-team:review-plan data` again. While a `data/plan` finding is open,
`/dev-team:implement-section` refuses every section of `data`.

That pair would loop forever, so the review counts. Each plan report carries `Round: <n>`,
the consecutive `request changes` reviews since the last approving one, and from round 2
`Convergence: <k> prior unfixed, <m> new`, where a fact still assumed by a section the last
re-plan did not reach is one *unfixed* finding, not a new one. On round 2 with a prior finding
unfixed, and on round 3 regardless, the review stops the loop
and offers two commands: `/dev-team:plan-package data` once more, or
`/dev-team:review-plan data --defer`, which moves the standing findings to the sections they
concern, approves the plan with fixes, and lets the build start — each finding is then a review
follow-up the implementer of that section must clear before `finalize-package`, where a wrong
session date is a failing intent test rather than a disagreement between two documents.

### Build the rest

Answer the decisions in `docs/decisions.md`, then:

```
/dev-team:run-package data
```

In full mode it skips every section already reviewed `approve` or `approve with fixes` with no
open review follow-ups and no failing intent test, and runs the same four steps for each
remaining section in `integration.md`'s dependency order. Then it runs `finalize-package`,
`review-package` (finalizing once more on `request changes`) and `sync-design`. Between spawns
it prints the section's `status.py` row. It ends with a six-line summary whose `next:` is the
command you would type from where it stopped. Here that is `/dev-team:plan-package analysis`.

It stops, with the agent's first lines, on a failing run gate; on any agent returning `blocked`
(a blocking rule) or `stopped` (the architect's decisions or access stop); on a section still at
or package review that stopped its loop — then `next:` is the user's choice between one more
round and that review's `--defer`, which re-files the standing findings as ordinary follow-ups. It never edits a file, never answers a decision, and never commits. Each
agent commits its own run, exactly as by hand. After fixing what stopped it, run it again: it
resumes from the first section not yet done.

### What it types — every step works by hand

The driver holds no procedure of its own, so each step is a command you can run yourself, for a
hard section or to watch one step at a time:

```
/dev-team:test-section data/ingest        # intent tests from the design: red
/dev-team:implement-section data/ingest   # runs them first; done when they pass
/dev-team:test-section data/ingest        # reconcile: fold recorded deviations, file the rest
/dev-team:review-section data/ingest
/dev-team:sync-design data                # ingest's design learns what shipped
/dev-team:plan-package data               # completion run
/dev-team:review-plan data
   (answer decisions)
/dev-team:test-section data/clean
/dev-team:implement-section data/clean
…
/dev-team:finalize-package data
/dev-team:review-package data
/dev-team:sync-design data
```

Run `plan-package` again before the spine is built and it writes nothing and names the four
spine commands; `/dev-team:status` shows `plan: spine only (ingest)` in the meantime.

`/dev-team:test-section` forks the tester, which writes `tests/intent/<section>/` from the
design and the contracts without ever opening the section's code. Run before the build, it
writes tests that fail by construction. Run after, it folds each deviation the README records
into the tests that cite that design item, and files every test still failing as a follow-up
the next `/dev-team:implement-section` picks up. The implementer never edits those tests.

Sections go in that order and cannot be built out of it: `/dev-team:implement-section data/clean`
refuses while `data/ingest` has no README. Each implementer reads the **READMEs** of the
sections it depends on — what actually shipped — ranked above those sections' design docs.
`integration.md` is a plan-time document; it stops being true the moment the first
implementer deviates, and implementers deviate. The README is where a deviation is recorded,
so the README is what the next section codes against.

### Publish the package

`/dev-team:finalize-package` refuses until every section is built and reviewed since its last
build, no review-sourced follow-up is open, and every Floor and Enforced row of
`docs/constraints.md` passes. `/dev-team:status data --gate` shows the same check. Then it forks
into the implementer in **surface mode**: it writes the top-level `src/data/__init__.py`
(lazy re-exports — importing `data` loads nothing until a name is used — of only the names a
consumer needs), the `pipelines/` that compose the sections, `cli.py` with one function per
command (its docstring is the `--help` text), the package's `docs/api/data.md` page so the
docs site builds strict from here on, `Applied:` lines any section implementer missed, and
`docs/packages/data/interface.md` — the public surface **as shipped**. `/dev-team:review-package` is
the gate: `__all__`, `interface.md`, and the section READMEs agree; every public name has a
consumer; every shape the repo contract promised is realized; `lint-imports` and `mkdocs
build --strict` pass; the pipelines and commands run.

Last, `/dev-team:sync-design` folds what the sections recorded back into their designs. Every
section README's **Implementation notes** lists where the code departed from its design,
with a reason. `sync-design` appends each design an **As shipped** table of those
departures — never rewriting the design above it — so the reviewer stops measuring the code
against a line the section correctly left behind, and `/dev-team:plan-change` later starts
from what shipped. A deviation that contradicts a contract is not folded: it becomes a `D<n>`
stub and a pointer to `/dev-team:plan-change`.

A package of one or two sections, or `/dev-team:plan-package data --all`, has no spine: the
first run designs everything and writes `surface.md`. Then `/dev-team:review-plan data`,
decisions, and `/dev-team:run-package data` in full mode.

Next week:

```
/dev-team:plan-package analysis
```

reads `docs/packages/data/interface.md` as its upstream, and its designers reference those
names exactly. Planning against a package that has no `interface.md` yet is allowed — every
consumed name is marked `provisional` and the return says so.

```
/dev-team:finalize-project
```

writes a README per package and the root README from the shipped documents, plus the docs-site
API pages. Safe to run early and often.
