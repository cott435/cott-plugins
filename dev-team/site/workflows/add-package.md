# Adding a package to an existing repo

```
/dev-team:plan-repo "Add a `reporting` package that turns cleaned bars into PDF/HTML summaries"
```

Forks into the **architect** at repo scope. Because `docs/architecture.md` already exists and the
argument adds to the brief rather than correcting it, this run is **extending**: the argument
is appended to `docs/brief.md` under `## Addition — <date>`. (`/dev-team:shape-brief` can write
that addition with you — then run `/dev-team:plan-repo` with no argument. A correction is
**revise**; see [New repo](new-repo.md).) Whether anything downstream has shipped does not
change the mode; it changes what may be edited, below. It reads the current repo contract, every
shipped `docs/packages/*/interface.md`, and every planned-but-unshipped
`docs/packages/*/contract.md`, and persists what it finds to `docs/assessment.md`. That file is
scratch for this run — it feeds the same invocation's edit to `docs/architecture.md` and is
otherwise only read by a re-run of `plan-repo` itself, never by `plan-package`.

It then runs the interview rule and, if nothing stops it, edits `docs/architecture.md`: adds
the new package's row to the Packages table (with the brief capabilities it covers), its dependency-graph edge, and the shapes crossing
its boundaries — **but only where no bound package — shipped, or with code already built — provides or
consumes the part being edited.** That restriction is the fork point below.

## Shipped vs. not-shipped dependencies

The new package's brief may ask for a name another package doesn't expose yet. Which package
that dependency is — shipped or not — decides what happens next, inside the same `plan-repo`
run:

**Dependency is shipped** (`docs/packages/<dep>/interface.md` exists — its shapes are frozen).
`plan-repo` will not add the missing name itself; editing a shipped surface is outside a repo
contract run. It still writes everything about the new package that doesn't touch that surface
— its row, its other edges — and stubs the missing name as a `D<n>` entry in
`docs/decisions.md`, `Scope: repo`, tagged `Raised by: /dev-team:plan-repo (interview)`,
recommending `/dev-team:plan-change`. You resolve it against the *existing* package:

```
/dev-team:plan-change "Expose a summary_frame accessor from analysis for reporting to consume"
```

This computes downstream impact, writes `docs/plans/<slug>/contract-delta.md`, designs the
change in `Mode: change`, and — once implemented —
`/dev-team:sync-plan <slug>` folds the new name into
`docs/packages/analysis/interface.md`. Only from that point is the name real; until then,
`reporting`'s own planning can only reference it as `provisional`.

**Dependency is not shipped** (no `interface.md` — never planned, or planned but not yet
implemented). A dependency with code already built but no `interface.md` yet is treated like a
shipped one: its code implements the shape, so the change goes through `/dev-team:plan-change`.
Otherwise nothing is frozen, so `plan-repo` edits the boundary directly in
`docs/architecture.md` — no stub, no `plan-change`. If the dependency already has a
`docs/packages/<dep>/contract.md`, re-run `/dev-team:plan-package <dep>` to add the new
surface to it; if it has never been planned, planning it — in dependency order — is just the
normal next step, no different from planning any other unshipped package.

## Then plan the new package itself

```
/dev-team:plan-package reporting
```

Reads `docs/architecture.md` (now updated), the brief rows for the capabilities `reporting`
covers, and, for each package `reporting` depends on: its
shipped `interface.md` when one exists — signatures are final, designers build against them
exactly — or its `contract.md` when only planned, in which case every consumed name is marked
`provisional` until that package ships. From here `reporting` follows the same loop as any
other package: contract, probe, parallel section designs, integration, surface, decision
stubs, then `/dev-team:implement-section reporting/<first section>`.
