# Adding a package to an existing repo

```
/dev-team:plan-repo "Add a `reporting` package that turns cleaned bars into PDF/HTML summaries"
```

Forks into the **architect** at repo scope. Because `docs/architecture.md` already exists and
the argument adds to the brief rather than correcting it, the argument is appended to
`docs/brief.md` under `## Addition — <date>` (`/dev-team:shape-brief` can write that addition
with you — then run `/dev-team:plan-repo` with no argument). A correction is
`/dev-team:plan-repo --fix "<notes>"`; see [New repo](new-repo.md).

## The change list

The architect diffs the brief against `docs/history/brief-contracted.md` and turns the addition
into change items: the new package's row in the Packages table, its dependency-graph edge, the
shapes crossing its boundaries. Each item is classified by the state of the package it touches
— unplanned, planned (a `contract.md`), built (section code) or shipped (the `surface` section
DONE and its surface check passing):

- **EDIT** — the item touches only unplanned packages, or planned ones it can simply change.
  Applied to `docs/architecture.md`.
- **EDIT+STALE** — applied, and the planned packages whose contracts it makes stale are listed
  in the return: re-run `/dev-team:plan-package <pkg>` for each.
- **CHANGE** — the item touches a built or shipped package, such as a name the new package
  needs from `data` that `data`'s `interface.md` does not provide. A canonical contract
  describes code that exists, so the architect writes `docs/packages/<pkg>/changes/<slug>.md`
  instead, one per affected package with the same slug: the goal, the affected sections, the contract changes (Added / Changed / Removed per contract)
  and the downstream impact, `Status: open`.
- **DECIDE** — the item reverses a dependency edge, makes a cycle, or needs a convention bound
  packages disagree on. A `D<n>` stub, and the run stops.

Before any edit, the old contract is copied to `docs/history/<date>-architecture.md`.

## Then

```
/dev-team:plan-package reporting
/dev-team:run-package reporting
```

The new package is planned and built as in [New repo](new-repo.md). A dependency it needs from a
shipped package is consumed from that package's `interface.md`; if the name is not there yet,
the change file carries it.

When a change file names sections of a built package:

```
/dev-team:run-package data
```

`status.py` re-opens every section the change file names at DESIGN; the designer runs in
`delta` mode against the change file, then the tester, the implementer and the reviewers as
usual. When every section is DONE again, the driver's close — `sync-plan` — applies the change
file to `docs/architecture.md` and `data`'s contract after verifying it against the code, marks
it `Status: synced`, and recomputes the consumers of every changed public name.
