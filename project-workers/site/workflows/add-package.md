# Adding a package to an existing repo

```
/project-workers:plan-repo "Add a `reporting` package that turns cleaned bars into PDF/HTML summaries"
```

Forks into the **architect** at repo scope. Because `docs/architecture.md` already exists, this
run is **extending**, not new — mode is decided purely by whether that file exists, regardless
of whether anything downstream has actually shipped. It reads the current repo contract, every
shipped `docs/packages/*/interface.md`, and every planned-but-unshipped
`docs/packages/*/contract.md`, and persists what it finds to `docs/assessment.md`. That file is
scratch for this run — it feeds the same invocation's edit to `docs/architecture.md` and is
otherwise only read by a re-run of `plan-repo` itself, never by `plan-package`.

It then runs the interview rule and, if nothing stops it, edits `docs/architecture.md`: adds
the new package's row to the Packages table, its dependency-graph edge, and the shapes crossing
its boundaries — **but only where no shipped package provides or consumes the part being
edited.** That restriction is the fork point below.

## Shipped vs. not-shipped dependencies

The new package's brief may ask for a name another package doesn't expose yet. Which package
that dependency is — shipped or not — decides what happens next, inside the same `plan-repo`
run:

**Dependency is shipped** (`docs/packages/<dep>/interface.md` exists — its shapes are frozen).
`plan-repo` will not add the missing name itself; editing a shipped surface is outside a repo
contract run. It still writes everything about the new package that doesn't touch that surface
— its row, its other edges — and stubs the missing name as a `D<n>` entry in
`docs/decisions.md`, `Scope: repo`, tagged `Raised by: /project-workers:plan-repo (interview)`,
recommending `/project-workers:plan-change`. You resolve it against the *existing* package:

```
/project-workers:plan-change "Expose a summary_frame accessor from analysis for reporting to consume"
```

This computes downstream impact, writes `docs/plans/<slug>/contract-delta.md`, designs the
change in `Mode: change`, and — once implemented —
`/project-workers:sync-plan <slug>` folds the new name into
`docs/packages/analysis/interface.md`. Only from that point is the name real; until then,
`reporting`'s own planning can only reference it as `provisional`.

**Dependency is not shipped** (no `interface.md` — never planned, or planned but not yet
implemented). Nothing is frozen, so `plan-repo` edits the boundary directly in
`docs/architecture.md` — no stub, no `plan-change`. If the dependency already has a
`docs/packages/<dep>/contract.md`, re-run `/project-workers:plan-package <dep>` to add the new
surface to it; if it has never been planned, planning it — in dependency order — is just the
normal next step, no different from planning any other unshipped package.

## Then plan the new package itself

```
/project-workers:plan-package reporting
```

Reads `docs/architecture.md` (now updated) and, for each package `reporting` depends on: its
shipped `interface.md` when one exists — signatures are final, designers build against them
exactly — or its `contract.md` when only planned, in which case every consumed name is marked
`provisional` until that package ships. From here `reporting` follows the same loop as any
other package: contract, probe, parallel section designs, integration, surface, decision
stubs, then `/project-workers:implement-section reporting/<first section>`.
