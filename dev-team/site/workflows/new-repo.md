# New repo, package by package

The whole path from an idea to shipped packages: shape the brief, set the bar, write the repo
contract, then for each package in dependency order write its contract and let the driver walk
every section to DONE.

## 0. The repo

Every run from here on starts with the run gate and ends in one commit of the files it wrote.
The gate refuses `main`/`master` and any uncommitted change outside `docs/decisions.md`,
`docs/brief.md`, `docs/constraints.md` and `.claude/agent-memory/`, the files you edit by hand
between runs. So the repo is a git repository on a feature branch before the first run —
`git init`, `git switch -c build`.

## 1. Shape the brief

```
/dev-team:shape-brief "a quant research platform: data, forecasting, trading agents, portfolio optimisation"
```

Runs **in your conversation**, not as a subagent, because it asks. It restates the idea, maps
the domain — including the areas you did not name — and narrows it with you: each capability
*now*, *later*, or *out*. Then it asks about the constraints that would change the design and
what makes the first version done, and writes `docs/brief.md`. The brief says `Status: draft`
until you approve it, and `plan-repo` refuses a draft. Commit it. Skip this step if you already
have a brief you trust.

## 2. Set the bar (optional)

```
/dev-team:set-constraints
```

Also in your conversation, any time before the first build. Four questions — coverage floor,
type strictness, docstring coverage, anything to measure without enforcing — each with a
default, then `docs/constraints.md`: **Floor**, **Enforced**, **Measured**, **Guarded** and
**Exceptions** rows, each a command. That file is the stop gate's spec: every implementer
stop runs its Floor and Enforced rows, and CI runs the same rows. Skip it and the Toolchain's
commands in `docs/architecture.md` are the bar.

## 3. The repo contract

```
/dev-team:plan-repo
```

Forks into the **architect** at repo scope. First it spawns a **researcher** per dataset the
brief names and profiles it, because data that cannot support the task changes which packages
exist. Then the interview rule: a question that would change a boundary is stubbed in
`docs/decisions.md` and the run **stops** (see **Questions** on the home page); re-run the same
command to continue. Otherwise it writes `docs/architecture.md` — Packages, Dependency graph,
Boundaries (shapes, never signatures), Shared conventions, Toolchain, Non-goals, Open
decisions — and snapshots the brief as `docs/history/brief-contracted.md`.

If the contract came out wrong, `/dev-team:plan-repo --fix "<what was wrong>"` corrects it
without touching the brief, or correct the brief with `/dev-team:shape-brief` and re-run. On an
existing contract every change item is classified by the state of the package it touches:
EDIT, EDIT+STALE, CHANGE (a change file, once a package is built) or DECIDE (a stop). The old
contract is archived to `docs/history/` first.

## 4. Each package: its contract

```
/dev-team:plan-package data
```

Forks into the **architect** at package scope. It reads the repo contract, the brief rows the
package covers, and each upstream package's `interface.md` (or its `contract.md`, marked
provisional, when the upstream has not shipped). It writes `docs/packages/data/contract.md`: the
Sections table — `section`, `responsibility`, `path`, `builds with`, `depends on`, `source` —
ending with the `surface` row, which depends on every other section; Section interfaces;
Pipelines; Public surface (intent); Consumes. It designs nothing: the designer does that, one
section at a time, when the section is ready.

## 5. Each package: the loop

```
/dev-team:run-package data
```

The driver runs in your conversation and spawns every agent itself. Each iteration it runs
`status.py data`, takes the ready set — the sections whose in-package dependencies are DONE —
and spawns one kind of step for all of them in one message:

- **PROBE** — a researcher per `api` source the section names, extending
  `docs/sources/<source>.md` with a `## data/<section>` entry.
- **DESIGN** — a designer per section: `docs/packages/data/design/<section>.md`, from the
  contract row, the READMEs of the sections it depends on (they shipped: DONE means built and
  reviewed), the probe docs and the decisions ledger.
- **TEST** — a tester per section: `tests/intent/<section>/`, written from the documents and
  never the code, all red. A design it cannot test returns `design-gap`, and the designer runs
  again with its reasons.
- **IMPLEMENT** — one implementer at a time: code, unit tests and the section README. The stop
  gate keeps it running until the constraints rows, the intent suite and the Guarded grep are
  green.
- **REVIEW** — round 1 is two reviewers in parallel: A for conformance (a coverage table over
  every contract clause and design item), B for correctness and security. `request changes`
  makes the section FIX 1: the implementer reads the reports, then one diff-scoped reviewer.

The `surface` section comes last, since it depends on every other: its design is built from
the shipped READMEs, its implementer writes the lazy top-level `__init__.py`, the pipelines,
`cli.py`, `docs/api/data.md` and `docs/packages/data/interface.md`, and its review approves
the package's public surface. When every section is DONE, the driver runs the architect as
`sync-plan`: approved deviations go into the contract, verified against the code. The summary
ends with `next: /dev-team:plan-package analysis`.

The driver asks you when a section is BLOCKED — an open decision with no assumption, a missing
credential, a review at its cap (*one more round* or *defer*), a third `design-gap` — records
the answer in `docs/decisions.md`, and continues. Re-running the same command at any point
picks up where the files say.

## 6. The next package, and the docs

```
/dev-team:plan-package analysis
/dev-team:run-package analysis
/dev-team:finalize-project
```

`analysis` is planned against `docs/packages/data/interface.md`, the shipped surface, and
imports only the names it lists. `finalize-project` forks into the **documenter**: a README per
package from its `interface.md` and section READMEs, `docs/index.md`, and the root README, whose
**Known gaps** are `status.py --repo` verbatim plus what only a document check finds. It is
safe to run early and often.
