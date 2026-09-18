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
3. Spawns one **designer** per section, in parallel, each given its section's probe doc. Each
   writes `docs/packages/data/design/<section>.md` and returns ten lines.
4. Reads every design and writes `docs/packages/data/integration.md`: deviations, mismatches,
   dependency order, shared work, risks, decisions needed — and **Repo contract deviations**,
   which it may resolve by editing the repo contract only when no shipped package is bound by
   the shape.
5. Writes `docs/packages/data/surface.md` — the design of the public surface, now that the
   section interfaces are concrete: the `__all__` names (only those a downstream package or a
   CLI command consumes, each with its consumer named), the pipeline signatures, the CLI
   commands with every argument, the import-linter contracts for this package.
6. Appends `D<n>` stubs to `docs/decisions.md`.

Then answer the decisions, and implement in the order `integration.md` gives, reviewing as you
go:

```
/dev-team:implement-section data/ingest
/dev-team:review-section data/ingest
/dev-team:implement-section data/clean
/dev-team:review-section data/clean
…
```

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
