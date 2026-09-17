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
  S --> A
  A["/dev-team:plan-repo<br/>→ docs/architecture.md (repo contract)"]
  A -. "contract wrong: correct the brief, re-plan (revise)" .-> S
  A --> B["/dev-team:plan-package data<br/>→ contract.md, design/*.md, integration.md, surface.md"]
  B --> C["/dev-team:implement-section data/ingest<br/>→ code, tests, section README"]
  C --> D["/dev-team:review-section data/ingest<br/>→ reviews/, followups"]
  D -->|next section| C
  D --> E["/dev-team:finalize-package data<br/>→ __init__.py, pipelines/, cli.py, interface.md"]
  E --> F["/dev-team:review-package data<br/>→ package gate"]
  F --> G["/dev-team:plan-package analysis<br/>reads data/interface.md as upstream"]
  G -.->|same loop| F
  F --> H["/dev-team:plan-change '…'<br/>→ plans/slug/ with Downstream impact"]
  H --> I["/dev-team:implement-section pkg/section slug"]
  I --> J["/dev-team:sync-plan slug<br/>→ canonical docs + interface.md updated"]
  J --> K["/dev-team:finalize-project<br/>→ package READMEs, docs/api, root README"]
  classDef stop stroke:#8a2f4a,stroke-width:2px;
  class A,B,G,H stop;
```

Nodes with the dark-red border can **stop** with questions in `docs/decisions.md`; re-running
the same command continues.

## Hand-offs

```mermaid
sequenceDiagram
  participant You
  participant Arch as architect
  participant Des as designer ×N
  participant Impl as implementer
  participant Rev as reviewer
  participant Doc as documenter
  Note over You: /dev-team:shape-brief — a discussion in your conversation → docs/brief.md
  You->>Arch: /dev-team:plan-repo
  Arch-->>You: architecture.md · stubs (or: Stopped for decisions)
  You->>Arch: /dev-team:plan-package data
  Arch->>Des: Section, Mode, Contracts, Upstream interfaces, Write to
  Des-->>Arch: ≤10 lines each (designs on disk)
  Arch-->>You: integration.md · surface.md · order
  You->>Impl: /dev-team:implement-section data/ingest
  Impl-->>You: files · tests · deviations · README path
  You->>Rev: /dev-team:review-section data/ingest
  Rev-->>You: verdict (report + followups on disk)
  You->>Impl: /dev-team:finalize-package data
  Impl-->>You: interface.md
  You->>Rev: /dev-team:review-package data
  You->>Doc: /dev-team:finalize-project
  Doc-->>You: READMEs · api pages · Known gaps
```

## Order of authority

**For what a section builds** (tie-break, highest first): `decisions.md` (decided, in scope) →
the integration doc for this run → `contract-delta.md` (change work) → the package contract →
the repo contract → the section's design.

**For what a section consumes**: the provider's shipped document — a sibling's README, an
upstream package's `interface.md` — wins over every plan-time document about that provider.

## The `docs/` map

| Path | Kind | Written by | Read by |
|---|---|---|---|
| `docs/brief.md` | canonical | shape-brief, you; plan-repo appends | plan-repo, map-project, curator; plan-package (only its `covers` rows) |
| `docs/history/` | archive | plan-repo, shape-brief | plan-repo (`brief-contracted.md`) |
| `docs/legacy/inventory.md` | survey | curator (extract-legacy); you mark `keep` | curator, researchers in extract mode; probe-source (the `Extracted skill:` row) |
| `docs/architecture.md` | **repo contract** | plan-repo; map-project, sync-plan | everyone |
| `docs/decisions.md` | ledger | architect stubs · you · implementer `Applied:` | every agent |
| `docs/followups.md` | queue | implementer, reviewer, sync-plan | implementer, documenter |
| `docs/assessment.md` | survey | map-project, plan-repo (extend, revise) | re-runs |
| `docs/api/<pkg>.md` | site | finalize-package; finalize-project fills gaps | mkdocs |
| `docs/packages/<pkg>/assessment.md` | survey | plan-package | designers |
| `docs/packages/<pkg>/contract.md` | **package contract** | plan-package; sync-plan | designers, implementer, reviewer, plan-change (Consumes) |
| `docs/packages/<pkg>/design/<section>.md` | plan-time | designer; sync-plan | implementer, reviewer |
| `docs/packages/<pkg>/sources/<source>.md` + `.sample.json`, `.probe.py` | **probed** — the external system as it answered, on the date probed | researcher in probe mode, spawned by plan-package or run as probe-source | designers, implementer, reviewer |
| `docs/packages/<pkg>/integration.md` | plan-time | architect; sync-plan | implementer, reviewer, finalize-package |
| `docs/packages/<pkg>/surface.md` | plan-time | architect at unify; sync-plan | finalize-package, review-package, implementer |
| `docs/packages/<pkg>/interface.md` | **shipped** | finalize-package; sync-plan | plan-package and every consumer |
| `packages/<pkg>/src/<pkg>/<section>/README.md` | **shipped** | implementer | dependents, finalize-package, reviewer, documenter |
| `docs/reviews/<date>-<pkg>-<section>.md` | report | review-section | implementer; finalize-package (it gates on the date) |
| `docs/reviews/<date>-<pkg>-package.md` | report | review-package | finalize-package on a re-run |
| `docs/plans/<slug>/…` | proposal | plan-change, designers | implementer, sync-plan |
| `docs/plans/synced.md` | ledger | sync-plan | sync-plan, finalize-project |
