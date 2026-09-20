# Changing shipped code

```
/dev-team:plan-change "Add volume-weighted bars"
```

1. Forks into the architect at change scope, which spawns **Explore** to assess what the change
   touches and writes `docs/plans/<slug>/assessment.md`.
2. **Downstream impact.** For every affected package with an `interface.md`, it computes the
   consumers — `grep` over `packages/*/src` for shipped ones, the `Consumes` tables in other
   packages' contracts for planned ones — and lists which public names each uses that the
   change alters. Nothing maintains a consumers list; it is derived every time.
3. Seeds anything canonical that is missing (see `/dev-team:map-project` for the full version).
4. Writes `docs/plans/<slug>/contract-delta.md`: only the contracts added, changed, or removed,
   grouped by **Repo contract**, **Package contract: <pkg>**, and **Interface: <pkg>**.
5. Spawns designers in `Mode: change` (or `new`) — including downstream consumer sections it is
   adapting — writing to `docs/plans/<slug>/<pkg>/<section>.md`.
6. Writes `docs/plans/<slug>/integration.md`, including **Canonical doc updates**.

Then implement with the slug, and fold the plan back when it ships:

```
/dev-team:implement-section data/clean add-vwap
/dev-team:implement-section analysis/features add-vwap
/dev-team:review-section data/clean add-vwap
/dev-team:sync-plan add-vwap
/dev-team:sync-design data
```

**A change to a shipped package's public surface must go through `/dev-team:plan-change`.** If you run
`/dev-team:implement-section data/clean` without a slug and the work would alter a name in
`docs/packages/data/interface.md`, the implementer refuses: consumers were built against that
file. Internal changes proceed.

**`/dev-team:sync-plan` is not optional.** Until it runs, the design docs, contracts, and `interface.md`
describe pre-change behavior — and those stale files are what the next `/dev-team:plan-change` hands its
designers and what `/dev-team:plan-package` hands the next package as its upstream. It folds in only the
sections it can verify shipped, records them in `docs/plans/synced.md`, recomputes consumers
for any `interface.md` it changed, and files follow-ups for consumers the plan did not adapt.

Then `/dev-team:sync-design <pkg>` for each package the change touched: it appends each design
an **As shipped** row for any deviation the change's section READMEs record, so the next
review and the next `/dev-team:plan-change` measure against what shipped.

**Scope lives in the brief.** `/dev-team:plan-change` works from the contracts and never edits
`docs/brief.md`. If the change adds or drops a capability, record that with
`/dev-team:shape-brief` once it has shipped, then run `/dev-team:plan-repo`: the shipped parts are
bound, so it finds the contract already matches and only updates `covers` and its brief
snapshot. Skip this and the next revise reads the brief as older than the code.
