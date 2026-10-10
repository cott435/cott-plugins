# The `docs/` layout

Where every document lives in a repo dev-team builds. [The flow](../flow.md) has who writes and who reads each one, and when it goes stale.

```
docs/
├── brief.md                         your input to plan-repo                        (shape-brief / you)
├── history/                         brief-contracted.md; every contract before an edit (architect)
├── constraints.md                   the bar: Floor, Enforced, Measured, Guarded, Exceptions (set-constraints / you)
├── architecture.md                  THE REPO CONTRACT                              (plan-repo, map-repo, sync-plan)
├── decisions.md                     D<n> ledger                                    (sync_decisions.py from the inboxes · architect · you · the driver · pair)
├── followups.md                     the backlog, `- [ ] <pkg>/<section>: …`, never a gate (reviewer, architect)
├── legacy/inventory.md              what to salvage from an old repo              (curator / you mark keep)
├── sources/<source>.md              SOURCE PROBE, one `## <pkg>/<section>` entry per consumer (researcher)
├── sources/<source>.sample.json · .probe.py    recorded responses + re-runnable probe   (api)
├── sources/<source>.stats.json  · .profile.py  column statistics + re-runnable profile  (dataset)
├── sources/<token>.md · .profile.py · .pull.py · .sample.json   a DATA PROFILE of a stage: source, up to five rows per kind (profiler)
├── api/<pkg>/index.md               the docs-site API page                         (the surface section's implementer)
├── index.md                         the docs-site home page                        (documenter)
├── packages/
│   └── data/
│       ├── contract.md              THE PACKAGE CONTRACT; Sections table ends with `surface`, **Data stages** for a data package, **Call paths** (plan-package)
│       ├── design/<section>.md      one per section; first line `Mode:`            (designer)
│       ├── interface.md             THE PUBLIC SURFACE AS SHIPPED — the surface section's README (implementer)
│       ├── decisions/<section>.md   the section's decisions inbox: D? stubs, Applied: lines (designer, implementer)
│       ├── deviations/<section>.md  one ledger per section: deviations, spec-changes (implementer, designer, tester, reviewer, architect)
│       ├── changes/<slug>.md        a change to built or shipped code, one per affected package, until sync-plan (architect)
│       └── reviews/
│           └── ingest/
│               ├── 2026-09-04-r1-a.md   round 1, conformance
│               ├── 2026-09-04-r1-b.md   round 1, correctness
│               └── 2026-09-05-r2-s.md   round 2, diff-scoped
└── deviations/ · deviations.md · reviews/ · changes/   (2.0 layouts, still read; never written)
```

Outside `docs/`: each section's code and `README.md` (the implementer's), its
`tests/unit/<section>/` (the implementer's) and `tests/intent/<section>/` (the tester's alone),
and under the gitignored `.dev-team/`: `gate/<pkg>/<section>.txt`, the stop gate's record for
each section, which the reviewer reads as evidence and `status.py` reads to hold a blocked or
let-through section BLOCKED; `stop/<pkg>/<section>`, an implementer's blocked or spec-change
marker;
`locks/`, the mkdir locks of `locked.py` and the sync hook; `tmp/`, agents' shell scratch.

**Canonical contracts describe code that exists.** An edit to a contract that touches a built
or shipped package becomes a change file instead; `sync-plan` applies it to the contracts once
the sections it names are DONE, after checking the code. Every contract is copied to
`docs/history/` before it is edited. Package status is derived, never written down:
`contract.md` exists → planned; section code exists → built; `surface` DONE and its check
passing → shipped.
