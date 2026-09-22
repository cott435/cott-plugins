# The flow

The interactive version of this page (click a skill, see what it reads and writes) is the
artifact titled **dev_team v4 Flow** in your Claude gallery — a name, not a version of this
plugin; see `CHANGELOG.md`. This page is the same content as
static diagrams so it lives with the bundle.

## Where truth comes from

An implementer builds from its own design but consumes other work from what actually shipped.
Inside a package a dependency is a section, so it reads that section's README. Across packages
a dependency is a package, so it reads that package's `interface.md` and imports only from the
package's top level. Plan-time documents about a provider lose to the shipped document every
time.

```mermaid
flowchart LR
  subgraph data["package data"]
    direction LR
    ingD["design/ingest.md<br/>(plan-time)"]
    ingR["ingest/README.md<br/>(shipped)"]
    clnD["design/clean.md"]
    cln["implementer<br/>data/clean"]
    surf["surface.md"]
    fin["/dev-team:finalize-package data"]
    init["src/data/__init__.py<br/>pipelines/ cli.py"]
    iface["interface.md<br/>(shipped)"]
    clnD --> cln
    ingR -- "reads what shipped" --> cln
    ingD -. "never" .-> cln
    surf --> fin
    ingR --> fin
    fin --> init --> iface
  end
  subgraph analysis["package analysis"]
    featD["design/features.md"]
    feat["implementer<br/>analysis/features"]
    featD --> feat
  end
  iface -- "reads what shipped<br/>from data import load_bars" --> feat
```

## The week-by-week loop

```mermaid
flowchart TD
  S["/dev-team:shape-brief (in your conversation)<br/>→ docs/brief.md"]
  S --> K["/dev-team:set-constraints (in your conversation, optional)<br/>→ docs/constraints.md"]
  K --> A
  A["/dev-team:plan-repo<br/>→ docs/architecture.md (repo contract)"]
  A -. "contract wrong: correct the brief, re-plan (revise)" .-> S
  A --> B1["/dev-team:plan-package data (run 1)<br/>→ contract.md, design of the spine only, integration.md with Spine"]
  B1 --> R1["/dev-team:run-package data (spine mode)"]
  subgraph spine["what run-package drives on a spine plan"]
    direction TB
    SP["test-section → implement-section → test-section<br/>→ review-section data/ingest → sync-design data"]
    SP --> B2["plan-package data (run 2)<br/>→ the other designs, against the spine's README; integration.md; surface.md"]
    B2 --> RP["review-plan data<br/>→ reviews/date-data-plan.md, followups data/plan"]
  end
  R1 --> SP
  RP -. "request changes, converging: /dev-team:plan-package data re-plans the named sections and every section a cross-cutting fact reaches" .-> B2
  RP -. "request changes, not converging (round 2 unfixed, or round 3): one more round, or review-plan --defer → findings move to their sections, plan approved with fixes" .-> DEC
  RP --> DEC["you: docs/decisions.md"]
  DEC --> R2["/dev-team:run-package data (full mode)"]
  subgraph full["what run-package drives on a reviewed plan"]
    direction TB
    T1["test-section data/clean<br/>→ tests/intent/clean/ (red)"]
    T1 --> C["implement-section data/clean<br/>→ code, tests, section README, commit"]
    C --> T2["test-section data/clean (reconcile)"]
    T2 --> D["review-section data/clean<br/>→ reviews/, followups"]
    D -. "request changes (up to 3 builds)" .-> C
    D -->|next section| T1
    D --> E["finalize-package data<br/>→ __init__.py, pipelines/, cli.py, interface.md"]
    E --> F["review-package data<br/>→ package gate"]
    F --> SD["sync-design data<br/>→ design/*.md gain As shipped"]
  end
  R2 --> T1
  SD --> G["/dev-team:plan-package analysis<br/>reads data/interface.md as upstream"]
  G -.->|same loop| R2
  F --> H["/dev-team:plan-change '…'<br/>→ plans/slug/ with Downstream impact"]
  H --> I["/dev-team:implement-section pkg/section slug"]
  I --> J["/dev-team:sync-plan slug<br/>→ canonical docs + interface.md updated"]
  J --> K2["/dev-team:finalize-project<br/>→ package READMEs, docs/api, root README"]
  classDef stop stroke:#8a2f4a,stroke-width:2px;
  class A,B1,B2,RP,R1,R2,G,H stop;
```

Nodes with the dark-red border can **stop**. The architect stops with questions in
`docs/decisions.md`, `review-plan` with plan CRITICALs, and `run-package` on any gate or
`blocked` return. Re-running the same command continues. Every node inside the two boxes is
also a command you can type by hand, `/dev-team:` prefixed, and does exactly the same thing.
A package of one or two sections, or `--all`, skips the spine: one `plan-package` run designs
everything, then `/dev-team:review-plan`, decisions, and `run-package` in full mode.

## Hand-offs

```mermaid
sequenceDiagram
  participant You
  participant Drv as run-package (your conversation)
  participant Arch as architect
  participant Des as designer ×N
  participant Tst as tester
  participant Impl as implementer
  participant Rev as reviewer
  participant Doc as documenter
  Note over You: /dev-team:shape-brief, /dev-team:set-constraints — in your conversation
  You->>Arch: /dev-team:plan-repo
  Arch-->>You: architecture.md · stubs (or: Stopped for decisions)
  You->>Arch: /dev-team:plan-package data
  Arch->>Des: Section, Mode, Contracts, Upstream interfaces, Write to
  Des-->>Arch: ≤10 lines each (designs on disk)
  Arch-->>You: integration.md (Spine) · commit
  You->>Drv: /dev-team:run-package data
  Drv->>Tst: test-section data/ingest (intent)
  Tst-->>Drv: Result · Mode · tests/intent/ingest/ (red)
  Drv->>Impl: implement-section data/ingest
  Impl-->>Drv: Result · files · deviations · README path
  Drv->>Tst: test-section data/ingest (reconcile)
  Drv->>Rev: review-section data/ingest
  Rev-->>Drv: Result · verdict (report + followups on disk)
  Drv->>Arch: sync-design data (ingest's design gains As shipped)
  Drv->>Arch: plan-package data (completion run)
  Arch->>Des: … Sibling shipped: ingest/README.md
  Drv->>Rev: review-plan data
  Rev-->>Drv: Result · Verdict · Loop: converging | stopped
  Drv-->>You: summary · next — answer decisions, or the two-command choice when the loop stopped
  You->>Drv: /dev-team:run-package data
  Note over Drv,Rev: per section: tester → implementer → tester → reviewer
  Drv->>Impl: finalize-package data
  Impl-->>Drv: interface.md
  Drv->>Rev: review-package data
  Drv->>Arch: sync-design data
  Arch-->>Drv: As shipped rows · commit
  Drv-->>You: summary · next: /dev-team:plan-package analysis
  You->>Doc: /dev-team:finalize-project
  Doc-->>You: READMEs · api pages · Known gaps
```

Every arrow into an agent is one run, and every run ends in one commit with a
`Dev-Team-Run:` trailer.

## Order of authority

**For what a section builds** (tie-break, highest first): `docs/constraints.md` (for the checks
it names only) → `decisions.md` (decided, in scope) → the integration doc for this run →
`contract-delta.md` (change work) → the package contract → the repo contract → the section's
design, read together with its **As shipped** section when one exists. The implementer builds
by this list and the reviewer carries it verbatim. A design line that a higher document
overrides is not a spec gap. A deviation recorded in the section README is at most a WARNING
unless it breaks a contract, a decided `D<n>`, a shipped interface or an intent test.

**For what a section consumes**: the provider's shipped document — a sibling's README, an
upstream package's `interface.md` — wins over every plan-time document about that provider.

## The `docs/` map

| Path | Kind | Written by | Read by |
|---|---|---|---|
| `docs/brief.md` | canonical | shape-brief, you; plan-repo appends | plan-repo, map-project, curator; plan-package (only its `covers` rows) |
| `docs/history/` | archive | plan-repo, shape-brief | plan-repo (`brief-contracted.md`) |
| `docs/legacy/inventory.md` | survey | curator (extract-legacy); you mark `keep` | curator, researchers in extract mode; probe-source (the `Extracted skill:` row) |
| `docs/sources/<source>.md` + `.sample.json`/`.probe.py` (api) or `.stats.json`/`.profile.py` (dataset) | **probed** — the external system as it answered, or the dataset as it reads, on the date probed. Repo-wide: one document per source, however many packages consume it | researcher in probe mode, spawned by plan-package, by plan-repo for a dataset, or run as probe-source | designers, implementer, reviewer |
| `docs/constraints.md` | canonical — the quality bar: Floor, Enforced, Guarded rows, each a command | set-constraints, you | reviewer (all modes, axis 0), implementer, tester, `status.py --gate` |
| `docs/architecture.md` | **repo contract** | plan-repo; map-project, sync-plan | everyone |
| `docs/decisions.md` | ledger | architect stubs · you · implementer `Applied:` | every agent |
| `docs/followups.md` | queue; reserved targets `<pkg>/surface`, `<pkg>/plan` and `<pkg>/<section>/intent`; entries ending `— tester <date>` are failing intent tests | implementer, reviewer, review-plan, tester (reconcile), sync-plan | implementer (step 6; blocks on an open `<pkg>/plan`, skips `/intent`), tester (reconcile, clears `/intent`), architect on a re-plan, documenter, `status.py` |
| `docs/assessment.md` | survey | map-project, plan-repo (extend, revise) | re-runs |
| `docs/api/<pkg>.md` | site | finalize-package; finalize-project fills gaps | mkdocs |
| `docs/packages/<pkg>/assessment.md` | survey | plan-package | designers |
| `docs/packages/<pkg>/contract.md` | **package contract** | plan-package; sync-plan | designers, implementer, reviewer, plan-change (Consumes) |
| `docs/packages/<pkg>/design/<section>.md` | plan-time; **As shipped** sections appended once built | designer; sync-plan; sync-design (append-only) | implementer, reviewer, plan-change (the latest As shipped) |
| `docs/packages/<pkg>/integration.md` | plan-time; item 0 **Spine** (`Status: spine only` or `complete`) | architect; sync-plan | plan-package run 2, run-package, implementer, reviewer, finalize-package, `status.py` |
| `docs/packages/<pkg>/surface.md` | plan-time | architect at unify; sync-plan; sync-design (As shipped) | finalize-package, review-package, implementer |
| `docs/packages/<pkg>/interface.md` | **shipped** | finalize-package; sync-plan | plan-package and every consumer |
| `packages/<pkg>/tests/intent/<section>/` | shipped tests — written from the design, never from the code; a finding here is addressed to `<pkg>/<section>/intent` | tester only | implementer (runs, never edits), reviewer, `status.py` intent column |
| `packages/<pkg>/src/<pkg>/<section>/README.md` | **shipped** | implementer | dependents, finalize-package, reviewer, documenter |
| `docs/reviews/<date>-<pkg>-<section>.md` | report; second line `Commit: <sha>` | review-section | implementer; the next review (diffs from `Commit:`); `status.py` and finalize-package (reviewed = `Commit:` is the newest commit touching the section) |
| `docs/reviews/<date>-<pkg>-package.md` | report | review-package | finalize-package on a re-run |
| `docs/reviews/<date>-<pkg>-plan.md` | report | review-plan | plan-package on a re-plan; `status.py --plan-gate` |
| `docs/plans/<slug>/…` | proposal | plan-change, designers | implementer, sync-plan |
| `docs/plans/synced.md` | ledger | sync-plan | sync-plan, finalize-project |
