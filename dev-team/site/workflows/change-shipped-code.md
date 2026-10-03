# Changing shipped code

```
/dev-team:plan-package data "Add volume-weighted bars"
```

Forks into the **architect** at package scope with the change as its argument (a change that
crosses packages is `/dev-team:plan-repo "<change>"`, which classifies the same way). It turns
the request into change items and classifies each by the state of what it touches. `data` is
built, so the contract is not edited in place — a canonical contract describes code that
exists. The outcome is **CHANGE**: `docs/packages/data/changes/add-vwap.md`, with

- **Change goal** — one paragraph;
- **Affected sections** — qualified names, `data/clean` — this package's only; a change that
  crosses packages is one file per affected package, same slug;
- **Contract changes** — per contract (**Repo contract**, **Package contract: data**,
  **Interface: data**), what is Added, Changed and Removed, every altered shipped name with its
  old and new signature;
- **Downstream impact** — per consumer, shipped or planned, the names it uses that change and
  what breaks. Consumers are recomputed every time — a grep of the code for shipped ones, the
  **Consumes** tables of other contracts for planned ones; nothing maintains a list;
- `Status: open`.

A question that changes a boundary is a `D<n>` stub and a stop, as always.

A change you can only judge by looking at it — a UI, a layout — is easier the other way round:
build it first with `/dev-team:pair <pkg>/<section>`, and let its wrap-up write the ledger
entries that re-open the documents (**Pairing on a section**).

## Build it

```
/dev-team:run-package data
```

An open change file newer than a section's design re-opens that section at DESIGN. The designer
runs in `delta` mode (its design's first lines are `Mode: delta` and `Change:
docs/packages/data/changes/add-vwap.md`), and the implementer and reviewers read the change file above the
package contract: for anything it names, it wins. Consumer sections named under **Downstream
impact** re-open the same way when their package is run.

## The close

A paths report goes stale when any section's code changes after its `Commit:`, so once the
changed sections are DONE the paths review runs again before the package is shipped. It
compares the code's call tree (`status.py --paths data --against-contract`) to the contract's
**Call paths**: a frame the change added that the contract does not list, or one the contract
lists that the code no longer passes through, is a break (CRITICAL) under the section that
holds it, and P1 uses the command's own budget. A contract written before 2.6 has no **Call
paths**; its review runs as in 2.5 until the close writes the heading.

When every section of the package is DONE and the paths review approves, the driver runs the
architect as `sync-plan` (`/dev-team:sync-plan data` by hand does the same). It verifies each
contract change against the code, applies it to the canonical contracts — after archiving
each to `docs/history/` — sets the change file to `Status: synced`, and closes every approved
deviation the same way. From then the change file is history.

## When the contract itself is wrong

A section can find that a document is wrong while it is being built. That is a `spec-change`
entry in `docs/packages/<pkg>/deviations/<section>.md`, not a change request: a `spec-change:contract` re-opens the
section at PLAN, where the driver runs the architect to edit the contract (EDIT, EDIT+STALE,
CHANGE or DECIDE, exactly as above) and set the entry `resolved`.
