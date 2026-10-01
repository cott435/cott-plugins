# Fixture — `state-cases`

One small git repository per rule of `status.py`'s state derivation, built on demand from
`two-package/`'s brief and dataset. Each case is a directory holding `case.json`: the commits
that set the state up (`steps`, applied in order, one commit each, so commit order is the
evidence), files left uncommitted (`dirty`), the arguments `status.py` runs with (`args`), and
what its output must show (`expect`). Written for phase 1 of the remake
(`site/notes/remake-01-state-and-templates.md`).

```
python3 evals/fixtures/state-cases/check.py            # every case; exit 1 names each failure
python3 evals/fixtures/state-cases/check.py rounds     # one case
python3 evals/fixtures/state-cases/build.py <case> <dest>   # build one repo to look at
```

`build.py` makes the root commit on `main`, then works on branch `build` (unless the case says
`"branch": "main"`). A step is either explicit, `{"files": {...}, "message": "..."}`, or a
macro, `{"do": "<macro>", ...}`: `base` (architecture, the `data` contract with its `surface`
row, the `trades` probe doc; `contract: false | "api"`, `sources: false`), `design`, `tests`,
`build`, `review` (one report per suffix, `Commit:` the code reviewed), `done` (all four,
round 1 `a` and `b` approving), `fix`, `edit`, `regenerate` (a
`<pkg>/<section>: regenerate 1 intent tests` commit), `deviation` (one entry in the
section's ledger, `docs/packages/<pkg>/deviations/<section>.md` with the heading's `— <k>`, or
with `"legacy": true` in the pre-split `docs/deviations.md`), `change` (`slug`, `sections`,
`status`, `pkg`: a change file at `docs/packages/<pkg>/changes/<slug>.md`) and `inbox`
(`section`, `entries`: the section's decisions inbox, entries verbatim). `review`,
`deviation` and `change` take `"layout": "old"` for the 2.0 paths (`docs/reviews/…`,
`docs/deviations/<pkg>/<section>.md` with no `— <k>`, `docs/changes/<slug>.md`); the
default is the 2.2 layout, so every case that sets no layout runs under it. `review` takes
`spec` (letter → the line under its **Spec-change** heading); `base` takes `shorthand`
(ingest's path cell as `…/ingest/`); `edit` takes `append`, `"replace": ["<old>", "<new>"]`
(the first occurrence, applied before `append`), or both. `{HEAD}` in any file content is the commit the step
starts from.

**The 2.2 layout here.** Every case that sets no `layout` builds its reports at
`docs/packages/<pkg>/reviews/<section>/<date>-r<n>-<letter>.md`, its ledger at
`docs/packages/<pkg>/deviations/<section>.md` with `— <k>` headings, its change files at
`docs/packages/<pkg>/changes/<slug>.md` (one per package, naming only that package's sections)
and its inbox at `docs/packages/<pkg>/decisions/<section>.md`; `"layout": "old"` and
`"legacy": true` pin the 2.0 and pre-2.0 spellings `status.py` still reads, and
`review-both-layouts` and `ledger-moved-new` mix the two in one repo.

**The gate record (2.4).** The eleven `gate-*` cases (`site/notes/2.4-02-gate-record.md`,
the eleven rows after `surface-section-name-no-readme-row`) carry a top-level `gate` key: section → the text of its stop-gate
record, written to `.dev-team/gate/data/<section>.txt` after `dirty`, `{SECTION}` the short
sha of the newest commit touching the section's code and unit tree (resolved after every
step, so a review commit, which touches only `docs/`, leaves it naming the build). The key
also puts `.dev-team/` in `.git/info/exclude`, as a scaffolded repo's `.gitignore` would.

The 2.2 cases (phase 1 of `site/notes/2.2-01-status-paths.md`) are fifteen rows before the phase-12 ones. The eight phase-12 cases (`site/notes/2.2-12-run-fixes.md`) follow them: `--fields` for new, document, delta by a change file, delta by a `spec-change:design`, round 2 and a bad target, and the run gate's stale-`Applied:` FAIL and its other-section PASS. Six
older cases whose expectations spell a 2.0 path or heading (`inputs-fix-round`,
`inputs-spec-change-review`, `report-spec-change-b`, `report-spec-change-recorded`,
`test-regenerate`, `test-spec-change-test`) set `"layout": "old"`, so they keep pinning the old
layout; the rest run under the new one.

**The ledger Status rule and the additive probe (2.4).** Eight cases
(`site/notes/2.4-03-ledger-and-probe.md`, the last eight rows). A 2.2-or-later entry, one whose
heading ends `— <k>`, is live while its `Status:` reads `open`, whatever was committed since;
PLAN, DESIGN and TEST evidence lists every open heading of the level. A probe doc re-opens a
design only when a design-time line is gone or reworded. `design-spec-change-answered` and
`test-spec-change-answered` pin the commit-order rule, which now holds only for a heading
without `— <k>`, so their `deviation` step is `"layout": "old"`; `design-probe-newer` rewords
a shared line instead of appending one, which no longer re-opens anything.

**Surface names and shipped (2.4).** Seven cases (`site/notes/2.4-05-gate-checks.md`, the last
seven rows). `build.py` writes each section README's name cell as one backticked identifier
and gives the contract a **Public surface (intent)** item naming `load_trades`, so a package
whose `surface` is DONE passes `--surface` and `shipped` and `shipped-sync` still print
`shipped: yes`. `--surface <pkg> --section <s>` checks one README: each name cell exactly one
backticked identifier, each `Public: yes` name in the contract's intent. `shipped: yes` now also
needs the package-wide check.

Every `status.py` rule and flag is exercised at least once; the rule a case pins is in its
note. Two cases go beyond the phase note's list: `design-probe-other-section` (a new consuming
section's entry does not make an existing design stale, per the design's *Stale when* for a
probe doc) and `shipped-sync`, `run-gate-dirty-exempt`, `run-gate-no-contract`, `surface-*`
(the note's `shipped` and `run-gate-dirty` rows each named two outcomes; `--surface` is the
optional flag).

| Case | Sets up | Args | Expected |
|---|---|---|---|
| `blocked-cap-round-2-unfixed` | round 2 requests changes with a prior finding unfixed: cap | `—` | `ingest · BLOCKED`, evidence `/^review r2 request changes, 1 prior unfixed \(cap\)$/` |
| `blocked-cap-round-3` | round 3 requests changes: cap | `—` | `ingest · BLOCKED`, round 3, evidence `/^review r3 request changes \(cap\)$/`; `next: /dev-team:run-package data ingest --step REVIEW (one more round) or /dev-team:run-package data --defer` |
| `blocked-decision` | open decisions: none, an em dash, and a real assumption | `—` | `ingest · BLOCKED`, evidence `/^D3 open, no assumption$/`; `clean · BLOCKED · D4 open, no assumption`; `storage · DESIGN`; `next: answer D3 in docs/decisions.md, then /dev-team:run-package data` |
| `design-change-file-open` | DONE, then an open change file names the section | `—` | `ingest · DESIGN`, evidence `/^change vwap-window [0-9a-f]{7} newer than design [0-9a-f]{7}$/` |
| `design-dependency-not-done` | no design; ingest (a dependency) not DONE | `—` | `clean · DESIGN`, ready no |
| `design-missing` | no design; no dependencies | `—` | `ingest · DESIGN`, ready yes, evidence `/no design/` |
| `design-probe-newer` | a shared line of the probe doc reworded after the design (2.4: `replace`, in place of an `append`) | `—` | `ingest · DESIGN`, evidence `/docs/sources/trades.md [0-9a-f]{7} newer than design/` |
| `design-probe-other-section` | another section's entry appended to the probe doc: not stale | `—` | `ingest · IMPLEMENT` |
| `design-spec-change-design` | open spec-change:design after the tests | `—` | `ingest · DESIGN`, evidence `/spec-change:design/` |
| `design-spec-change-answered` | an open spec-change:design the design was rewritten after (remake phase 11); since 2.4 its entry is `"layout": "old"`, no `— <k>` | `—` | `ingest · TEST`, evidence `/^design [0-9a-f]{7} newer than tests [0-9a-f]{7}$/`; no `spec-change:design` |
| `done-and-surface-ready` | ingest, clean, storage DONE; surface ready | `—` | `surface · DESIGN`, ready yes; `ingest · DONE`; `clean · DONE`; `storage · DONE`; `shipped: no (surface DESIGN)`; `next: /dev-team:run-package data` |
| `fix-round-1` | round 1: a approves, b requests changes; the worst wins | `—` | `ingest · FIX 1`, round 1 |
| `implement-missing-readme` | intent tests, no README | `—` | `ingest · IMPLEMENT`, evidence `/no .*README.md/` |
| `implement-regeneration-skipped` | DONE, then an approved deviation and a regeneration commit: still DONE | `—` | `ingest · DONE`, round 1 |
| `implement-tests-newer` | intent tests edited after the README (not a regeneration) | `—` | `ingest · IMPLEMENT`, evidence `/^tests [0-9a-f]{7} newer than README [0-9a-f]{7}$/` |
| `inputs-bad-target` | --inputs names a section the contract does not have | `--inputs data/nope` | `no section nope in docs/packages/data/contract.md`; exit 2 |
| `inputs-first-build` | --inputs for a first build: one dependency README, no review, no change file | `--inputs data/clean` | the whole twelve-line block, in order; not `## data`; exit 0 |
| `inputs-fix-round` | --inputs at FIX 1: the round's reports, round 2, the dataset probe doc | `--inputs data/ingest` | `Review: docs/reviews/2026-09-27-data-ingest-r1-a.md, docs/reviews/2026-09-27-data-ingest-r1-b.md`; `Round: 2`; `Source probes: docs/sources/trades.md` |
| `inputs-upstream-change` | --inputs for a downstream package's section: provisional upstream contract, an open change file, no intent tree | `--inputs analysis/vwap` | `Upstream interfaces: provisional: docs/packages/data/contract.md`; `Intent tests: none`; `Change file: docs/changes/vwap-window.md`; `Run: run-package analysis` |
| `no-contract` | no package contract: next is plan-package | `—` | `next: /dev-team:plan-package data` |
| `not-blocked-round-2-fixed` | round 2 requests changes, every prior fixed: no cap | `—` | `ingest · FIX 2`, round 2 |
| `old-report-name` | a 0.6-era report name reads as round 1 | `—` | `ingest · DONE`, round 1 |
| `plan-spec-change-contract` | open spec-change:contract | `—` | `ingest · PLAN`, evidence `/spec-change:contract/`; `· spec-change:contract ·` |
| `probe-api-missing-heading` | api source whose probe doc lacks the section heading | `—` | `ingest · PROBE`, evidence `/api:polygon lacks ## data/ingest/` |
| `probe-dataset-no-doc` | dataset source with no probe doc | `—` | `ingest · PROBE`, evidence `/dataset:trades/` |
| `repo` | --repo lists the open D, the open spec-change and the unbuilt sections | `--repo` | `packages:⏎  - data: planned⏎  - analysis: no contract`; `sections:⏎  - data/ingest: BLOCKED`; `  - data/clean: `; `decisions:⏎  - D3: Which timestamp parser?`; `spec-changes:⏎  - data/clean — 2026-09-27 — spec-change:contract`; `changes:⏎  - none`; `backlog:⏎  - data/ingest: 2`; exit 0 |
| `review-code-newer` | approved, then the code changed | `—` | `ingest · REVIEW`, round 1, evidence `/newer than review r1/` |
| `review-none` | built, never reviewed | `—` | `ingest · REVIEW`, round 0, evidence `/no review/` |
| `rounds` | --rounds after two rounds | `--rounds data/ingest` | `rounds: 2`; `next round: 3`; not `## data`; exit 0 |
| `run-gate-dirty` | --run-gate with an uncommitted code file | `--run-gate data` | `run gate: FAIL`; `uncommitted changes outside the user-edited files: packages/data/src/data/ingest/__init__.py; commit or stash them and re-run`; exit 1 |
| `run-gate-dirty-exempt` | --run-gate with only docs/decisions.md dirty | `--run-gate data` | `run gate: PASS`; exit 0 |
| `run-gate-main` | --run-gate on main | `--run-gate` | `run gate: FAIL`; `on `main`; create a feature branch and re-run`; exit 1 |
| `run-gate-no-contract` | --run-gate for a package with no contract | `--run-gate data` | `data: missing docs/packages/data/contract.md — run /dev-team:plan-package data`; exit 1 |
| `shipped` | surface DONE, nothing to sync: next package | `—` | `surface · DONE`; `shipped: yes`; `next: /dev-team:plan-package analysis` |
| `shipped-sync` | surface DONE with an approved deviation: sync-plan | `—` | `ingest · DONE`; `shipped: yes`; `next: /dev-team:sync-plan data` |
| `surface-fail` | --surface: an extra __all__ name and an eager section import | `--surface data` | `surface: FAIL`; `extra: in __all__, not in interface.md Public names`; `loads section module data.ingest`; exit 1 |
| `surface-na` | --surface before interface.md exists | `--surface data` | `surface: n/a (no interface.md)`; exit 0 |
| `surface-pass` | --surface: __all__, interface.md and README Public rows agree; lazy import | `--surface data` | `surface: PASS`; exit 0 |
| `test-design-newer` | design edited after the intent tests | `—` | `ingest · TEST`, evidence `/^design [0-9a-f]{7} newer than tests [0-9a-f]{7}$/` |
| `test-missing` | design, no intent tree | `—` | `ingest · TEST`, ready yes |
| `test-regenerate` | approved deviation whose clause an untagged intent test cites | `—` | `ingest · TEST`, evidence `/^regenerate: data/ingest — 2026-09-27 — deviation$/` |
| `test-spec-change-test` | an open spec-change:test after the build (remake phase 11) | `—` | `ingest · TEST`, evidence `/^open data/ingest — 2026-09-27 — spec-change:test$/` |
| `test-spec-change-answered` | the same, then a regeneration commit (remake phase 11); since 2.4 its entry is `"layout": "old"`, no `— <k>` | `—` | `ingest · REVIEW`, evidence `/^no review$/`; no `spec-change:test` |
| `test-design-newer-tests-current` | a delta design after the build, then a tester stamp commit `intent tests current with design` (remake phase 11) | `—` | `ingest · REVIEW`, evidence `/^no review$/` |
| `ledger-old-layout` | approved deviation at the 2.0 `docs/deviations/data/ingest.md`, untagged citing test | `—` | `ingest · TEST`, evidence `/^regenerate: data\/ingest — 2026-09-27 — deviation$/` |
| `ledger-heading-k` | a proposed entry, then an approved one: heading `… — deviation — 2` in the new file | `—` | `ingest · TEST`, evidence `/— deviation — 2$/` |
| `ledger-moved-new` | an open `spec-change:design` first committed at the 2.0 path, the design answering it, then the entry moved under `docs/packages/data/deviations/` | `—` | `ingest · TEST` (still answered); no `spec-change:design` |
| `review-old-layout` | round 1 reports at the 2.0 `docs/reviews/…` | `—` | `ingest · DONE`, round 1 |
| `review-both-layouts` | round 1 at the old path, round 2 at the new | `--rounds data/ingest` | `rounds: 2`; `next round: 3` |
| `rounds-commit` | built section, one review | `--rounds data/ingest` | `rounds: 1`; a line matching `/^commit: [0-9a-f]{7}$/`; not `commit: none` |
| `rounds-commit-none` | contract only | `--rounds data/ingest` | `rounds: 0`; `commit: none` |
| `change-per-package` | DONE, then an open `docs/packages/data/changes/vwap-window.md` naming `data/ingest` | `—` | `ingest · DESIGN`, evidence `/^change vwap-window/` |
| `change-per-package-other-pkg` | an open `docs/packages/analysis/changes/x.md` naming `data/ingest` | `—` | `ingest · IMPLEMENT` (a per-package file names only its own package's sections) |
| `inputs-new-layout` | FIX 1 with reports at the new path and a per-package change file | `--inputs data/ingest` | `Review: docs/packages/data/reviews/ingest/2026-09-27-r1-a.md, docs/packages/data/reviews/ingest/2026-09-27-r1-b.md`; `Change file: docs/packages/data/changes/vwap-window.md` |
| `run-gate-inbox-stub` | inbox with a `## D? — Which parser?` stub | `--run-gate data` | `run gate: FAIL`; `unsynced inbox — docs/packages/data/decisions/ingest.md: D? stub not yet numbered`; exit 1 |
| `run-gate-inbox-applied` | inbox `## D3` with an `Applied:` line the central D3 lacks | `--run-gate data` | `run gate: FAIL`; `D3 Applied: line not in docs/decisions.md`; exit 1 |
| `run-gate-inbox-synced` | inbox `## D3` whose `Applied:` line is in the central D3 | `--run-gate data` | `run gate: PASS`; exit 0 |
| `clause-full-name` | approved deviation `Clause: design §5 load trades from csv`; one test cites it, another cites `load trades count` | `—` | `ingest · TEST`, evidence `/^regenerate: data\/ingest — 2026-09-27 — deviation — 1$/` |
| `clause-full-name-no-match` | the same clause (at the 2.0 path), only the `load trades count` test | `—` | `ingest · REVIEW`, evidence `/^no review$/` (no match on the first word alone) |
| `fields-new` | a design, nothing else | `--fields data/ingest` | `mode: new`, `change file: none`, `design mode: new`, `diff base: none`, in that order |
| `fields-document` | code, no design | `--fields data/ingest` | `mode: document`; `design mode: none` |
| `fields-delta-change` | DONE, then an open change file naming the section | `--fields data/ingest` | `mode: delta`; `change file: docs/packages/data/changes/vwap-window.md`; `/^diff base: [0-9a-f]{7}$/` |
| `fields-delta-spec-change` | an open `spec-change:design` after the tests | `--fields data/ingest` | `mode: delta`; `change file: none` |
| `fields-round-2` | round 1 requests changes, a fix, round 2 `s` | `--fields data/ingest` | `/^diff base: [0-9a-f]{7}$/` |
| `fields-bad-target` | contract only | `--fields data/nope` | `no section nope in docs/packages/data/contract.md`; exit 2 |
| `run-gate-stale-applied` | central D3 holds two `data/ingest` `Applied:` lines, the inbox one | `--run-gate data` | `run gate: FAIL`; `stale Applied: line — D3: Applied: data/ingest, 2026-09-27, …loader.py`; exit 1 |
| `run-gate-stale-applied-other-section` | central D3 holds a `data/clean` line and the inbox's `data/ingest` line | `--run-gate data` | `run gate: PASS`; exit 0 |
| `surface-name-cell-and-pipeline` | surface DONE; a README name cell `` `load_trades` `` (2.4 phase 5: the file hint `` (`__init__.py`) `` is gone, since the one-name rule fails it); `run_load` provided by `data.pipelines.load` with no README row (phase 12, the 12.7 stop) | `--surface data` | `surface: PASS` |
| `surface-section-name-no-readme-row` | the same with ingest's row `Public: no` | `--surface data` | `surface: FAIL`; `load_trades: in interface.md Public names, not in README Public: yes rows`; no `run_load` line; exit 1 |
| `gate-blocked` | `base`, `design`, `tests`, `build`; a `blocked` record for ingest's current commit (2.4, phase 2) | `—` | `ingest · BLOCKED`, evidence `/^gate blocked: status\.py --surface data fails on a sibling README$/`; `next: /dev-team:run-package data ingest --step IMPLEMENT (run it again) or /dev-team:run-package data ingest --step REVIEW (review anyway)` |
| `gate-let-through` | the same build; an `attempt 3` record, two `FAIL` lines, `result: letting the run stop after 3 attempts with 2 failures` | `—` | `ingest · BLOCKED`, evidence `/^gate let through after 3 attempts, 2 failures$/` |
| `gate-not-done` | an `attempt 1` record, one `FAIL`, `result: not done (attempt 1 of 3)` | `—` | `ingest · IMPLEMENT`, evidence `/^gate not done \(attempt 1 of 3\)$/` |
| `gate-pass` | an `attempt 1` record, `PASS` lines, `result: pass` | `—` | `ingest · REVIEW`, evidence `/^no review$/` |
| `gate-stale-commit` | the `blocked` record with `commit: 0000000` | `—` | `ingest · REVIEW`, evidence `/^no review$/` |
| `gate-no-commit-line` | the let-through record without its `commit:` line (pre-2.4) | `—` | `ingest · REVIEW`, evidence `/^no review$/` |
| `gate-report-ignored` | a `report` record with a `FAIL` and `result: fail (1 failure, report since HEAD)` | `—` | `ingest · REVIEW`, evidence `/^no review$/` |
| `gate-spec-change-ignored` | a `spec-change` record, `result: spec-change` | `—` | `ingest · REVIEW`, evidence `/^no review$/` |
| `gate-review-covers` | the `blocked` record, then round 1 `a` and `b` approve the same code | `—` | `ingest · DONE` |
| `gate-blocked-half-pair` | the `blocked` record, then round 1 with only `a` | `—` | `ingest · REVIEW`, evidence `/^review r1 lacks its b report$/` |
| `gate-blocked-dirty` | the `blocked` record, and an uncommitted `packages/data/src/data/ingest/extra.py` | `—` | `ingest · REVIEW`, evidence `/^no review$/` (the record is stale; with no review round rule 7 says `no review`) |
| `design-spec-change-open-after-rewrite` | `base`, `design`, `tests`, an open `spec-change:design` (`— 1`), then the design edited | `—` | `ingest · DESIGN`, evidence `/^open data/ingest — 2026-09-27 — spec-change:design — 1$/` |
| `design-spec-change-resolved` | the same, the design edit's commit also setting the entry's `Status: resolved` | `—` | `ingest · TEST`; no `spec-change:design` |
| `design-spec-change-two-open` | two open `spec-change:design` entries (the second with `"clause": "design §5 other_item"`) | `—` | `ingest · DESIGN`, evidence `/^open data/ingest — 2026-09-27 — spec-change:design — 1; data/ingest — 2026-09-27 — spec-change:design — 2$/` |
| `fields-delta-two-open` | the same | `--fields data/ingest` | `mode: delta` |
| `plan-spec-change-two-open` | `base`, `design`, two open `spec-change:contract` entries | `—` | `ingest · PLAN`, evidence `/— spec-change:contract — 1; data/ingest — 2026-09-27 — spec-change:contract — 2$/` |
| `test-spec-change-one-resolved` | `base`, `design`, `tests`, `build`, two open `spec-change:test` entries in one commit, then a regeneration commit that sets only entry 1 `resolved` | `—` | `ingest · TEST`, evidence `/^open data/ingest — 2026-09-27 — spec-change:test — 2$/` |
| `design-probe-added-lines` | `base`, `design`, then `- one timestamp out of order` appended to `docs/sources/trades.md` | `—` | `ingest · TEST`; absent `newer than design` |
| `design-probe-title-date` | `base`, `design`, then the probe doc's title line given a date (the fixture's title has none) | `—` | `ingest · TEST`; absent `newer than design` |
| `surface-names-pass` | `base`, `design`, `tests`, `build` for ingest: README row `` `load_trades` ``, `Public: yes` | `--surface data --section ingest` | `surface names data/ingest: PASS`; exit 0 |
| `surface-names-grouped` | the same, the row's cell `` `load_trades`, `Trade` `` | the same | `surface names data/ingest: FAIL`; `` `load_trades`, `Trade`: name cell is not one backticked identifier ``; exit 1 |
| `surface-names-dotted` | the same build, a second row `` `Loader.load` ``, `Public: no` | the same | FAIL, the same reason for `` `Loader.load` ``; no reason for `` `load_trades` ``; exit 1 |
| `surface-names-not-in-contract` | the same build, a row `` `helper` ``, `Public: yes`, not in the contract | the same | `helper: Public: yes, not in the contract's Public surface (intent)`; exit 1 |
| `surface-names-no-readme` | `base`, `design` for ingest, not built | the same | `surface names data/ingest: n/a (no README)`; exit 0 |
| `surface-grouped-cell` | every row DONE; ingest's README has one row `` `load_trades`, `Trade` `` (written before ingest's review), both in `__all__` and **Public names** | `--surface data` | `surface: FAIL`; `data/ingest README:` with the cell reason; no line holding `Trade: in interface.md Public names, not in README`; exit 1 |
| `shipped-surface-check-fail` | the same repo | `—` | `surface · DONE`; `shipped: no (surface check FAIL)`; `next: correct the README rows status.py --surface data names, then /dev-team:run-package data` |
| `fields-upstream-line` | `base`, ingest DONE, the `analysis` contract and a `vwap` design whose §2 ends `Upstream packages: data` (2.4, phase 7) | `--fields analysis/vwap` | fifth line `upstream interfaces: provisional: docs/packages/data/contract.md` |
| `fields-upstream-none` | the same, the line `Upstream packages: none` | the same | `upstream interfaces: none` |
| `fields-upstream-no-line` | the same, the design without the line | the same | `upstream interfaces: provisional: docs/packages/data/contract.md` (every upstream package, as before 2.4) |
| `inputs-upstream-none` | the same as `fields-upstream-none` | `--inputs analysis/vwap` | `Upstream interfaces: none` |
