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
5. On a spine run, stops here and names the next commands. Otherwise writes
   `docs/packages/data/surface.md` — the design of the public surface, now that the
   section interfaces are concrete: the `__all__` names (only those a downstream package or a
   CLI command consumes, each with its consumer named), the pipeline signatures, the CLI
   commands with every argument, the import-linter contracts for this package.
6. Appends `D<n>` stubs to `docs/decisions.md`.

Build and review the spine exactly as every section is built below, then plan the rest:

```
/dev-team:test-section data/ingest
/dev-team:implement-section data/ingest
/dev-team:test-section data/ingest
/dev-team:review-section data/ingest
/dev-team:plan-package data
```

The second run designs `clean` and `storage` with `Sibling shipped:` naming
`ingest`'s README — so the two designs that consume `ingest` are written against what it
actually returns, not what its design projected — then rewrites `integration.md` with
`Status: complete` and writes `surface.md`. Run `plan-package` again before the spine is built
and it writes nothing and names these four commands; `/dev-team:status` shows
`plan: spine only (ingest)` in the meantime.

Then have someone who wrote none of it check the plan before any code exists:

```
/dev-team:review-plan data
```

Forks the reviewer in plan mode. It checks the contract, every design, `integration.md` and
`surface.md` against each other and against the repo contract, the ledger, the upstream
`interface.md` files and the probe docs: every consumed name has a provider with the same
signature, every open question became a `D<n>`, every deviation is resolved, every public name
has a consumer. It writes `docs/reviews/<date>-data-plan.md` and files each CRITICAL to
`docs/followups.md` as `data/plan: …`. On `request changes`, re-run `/dev-team:plan-package data`:
it re-delegates only the sections a finding names, ticks the findings, and says to review the
plan again. While a `data/plan` finding is open, `/dev-team:implement-section` refuses every
section of `data`.

Then answer the decisions, and implement the remaining sections in the order
`integration.md` gives, testing and reviewing as you go:

```
/dev-team:test-section data/clean         # intent tests from the design — red
/dev-team:implement-section data/clean    # runs them first; done when they pass
/dev-team:test-section data/clean         # reconcile: fold recorded deviations, file the rest
/dev-team:review-section data/clean
/dev-team:test-section data/storage
…
```

Or let the driver type that loop:

```
/dev-team:run-package data
```

Runs in your conversation and spawns the same agents the commands above fork, one at a time,
in `integration.md`'s order — test, build, reconcile, review per section, rebuilding on
`request changes` up to three times — then `finalize-package`, `review-package` and
`sync-design` below. It stops on every gate the manual commands stop on and ends with the
command you would type next. Run it on the spine-only plan instead and it builds the spine,
re-runs `plan-package`, runs `review-plan`, and stops for your decisions. See **Running a
package** on the home page.

`/dev-team:test-section` forks the tester, which writes `tests/intent/<section>/` from the
design and the contracts without ever opening the section's code. Run before the build, it
writes tests that fail by construction; run after, it folds each deviation the README records
into the tests that cite that design item and files every test still failing as a follow-up
the next `/dev-team:implement-section` picks up. The implementer never edits those tests.

Sections go in that order and cannot be built out of it: `/dev-team:implement-section data/clean`
refuses while `data/ingest` has no README. Each implementer reads the **READMEs** of the
sections it depends on — what actually shipped — ranked above those sections' design docs. `integration.md` is a plan-time document; it stops
being true the moment the first implementer deviates, and implementers deviate. The README is
where a deviation is recorded, so the README is what the next section codes against.

When every section has a README *and a review newer than it*, publish the package:

```
/dev-team:status data --gate
/dev-team:finalize-package data
/dev-team:review-package data
```

`/dev-team:finalize-package` refuses until every section is built and reviewed since its last build and
no review-sourced follow-up is open — `/dev-team:status data --gate` shows the same check. Then it forks
into the implementer in **surface mode**: it writes the top-level `src/data/__init__.py`
(lazy re-exports — importing `data` loads nothing until a name is used — of only the names a
consumer needs), the `pipelines/` that compose the sections, `cli.py` with one function per
command (its docstring is the `--help` text), the package's `docs/api/data.md` page so the
docs site builds strict from here on, `Applied:` lines any section implementer missed, and
`docs/packages/data/interface.md` — the public surface **as shipped**. `/dev-team:review-package` is
the gate: `__all__`, `interface.md`, and the section READMEs agree; every public name has a
consumer; every shape the repo contract promised is realized; `lint-imports` and `mkdocs
build --strict` pass; the pipelines and commands run.

Once it passes, fold what the sections recorded back into their designs:

```
/dev-team:sync-design data
```

Every section README's **Implementation notes** lists where the code departed from its design,
with a reason. `/dev-team:sync-design` appends each design an **As shipped** table of those
departures — never rewriting the design above it — so the reviewer stops measuring the code
against a line the section correctly left behind, and `/dev-team:plan-change` later starts
from what shipped. A deviation that contradicts a contract is not folded: it becomes a `D<n>`
stub and a pointer to `/dev-team:plan-change`.

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
