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
with `"legacy": true` in the pre-split `docs/deviations.md`; `raised_by` sets its `Raised by:`), `change` (`slug`, `sections`,
`status`, `pkg`: a change file at `docs/packages/<pkg>/changes/<slug>.md`), `inbox`
(`section`, `entries`: the section's decisions inbox, entries verbatim), `commands` (a
package with one `[project.scripts]` command, **The call tree (2.5)** below) and
`paths_review` (a package's paths report, **The paths report (2.5)** below). `review`,
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

**The shape check (2.5).** Ten cases (`site/notes/2.5-readability-02-shape-slice.md`, the
ten `shape-*` rows at the end). Each builds `ingest`, then commits
`packages/data/src/data/ingest/helper.py` or a variant of it, and runs `--shape data --section
ingest`: a private helper of one statement whose one reference is a call fails at its `def`
line, while a second caller, a reference that is not a call (`key=_strip`), a fourth
statement, a test file, a dunder, a `@property` and a method name two classes define each
pass. A round-1 review whose `Commit:` covers the helper is the base, so the helper is not
added (`shape-helper-before-review`); a helper committed after the review is
(`shape-helper-after-review`).

**The shape check, complete (2.5).** Eight more cases
(`site/notes/2.5-readability-05-shape-complete.md`, the eight `shape-*` rows after the
`calltree-*` ones). `bag.py` is a function `load_with(path, **options: Unpack[LoadOptions])`
at line 12: added, it fails as `options-bag`; under a round-1 review, or as keyword-only
parameters, it passes. Every `--shape` run now prints `MEASURED shape indirect: <n>` (a lambda
passed as `key=` plus a `_RUNNERS[kind](…)` call make 2) and one `MEASURED shape depth <name>:
<n>` per README entry point (`none` for the built `load_trades`, which calls nothing; 0 for the
`commands` macro's `read_trades`, which makes its effect calls itself), so `shape-pass` and
`shape-trivial-helper` also expect `MEASURED shape indirect: 0`. A design whose first line is
`Mode: document`, committed after `helper.py`, makes the design's commit the base: the adopted
helper passes, and a bag committed after the design still fails.

**The call tree (2.5).** Nine cases (`site/notes/2.5-readability-04-paths-resolver.md`, the
nine `calltree-*` rows at the end). Each runs `base`, then the `commands` macro: one commit,
`data/surface: commands`, of a package `pyproject.toml` with one command (`data-load =
"data.cli:load"`), `cli.py`, `pipelines/__init__.py`, `pipelines/load.py` and
`ingest/reader.py`, whose tree reaches `shutil.copy` and `open` at depth 2; its `files` key
replaces or adds any file in the same commit. Each runs `--paths data`. A lambda handed to a
package function prints under that function, a dict dispatch prints every value, both
`[indirect]`; a method on a local is `[unresolved]`; `loguru` and `re` are not effects and
`requests` is; a method called through `self` is a frame; a self-call is `[recursive]`. The
macro goes before any `done` step, so a section's review covers its files. The `paths-*` names
are left for the package line phase 7 adds.

**The paths report (2.5).** Three cases (`site/notes/2.5-readability-06-paths-reviewer.md`,
the three `rounds-*` rows at the end). The `paths_review` macro (`round`, `verdict`,
`critical`, `focus`, defaulting to `paths`) commits
`docs/packages/data/reviews/paths/2026-09-27-r<n>-p.md` with the summary `review data/paths:
r<n>-p: <verdict> (<k> critical)`, its `Commit:` the newest commit touching the package's
code, tests or `interface.md` before it, and its headings written `## <name>`. `--rounds
data/paths` prints five lines; a paths report is never a section's round.

**The paths review (2.5).** Fourteen cases (`site/notes/2.5-readability-07-state-and-driver.md`,
the fourteen rows after the `rounds-*` ones). "All done" is `base`, `commands`, then `done` for
`ingest`, `clean`, `storage` and `surface`; the P2 line is `ingest: P2 —
packages/data/src/data/ingest/reader.py:7 — a lambda on the main path — call the step by name`.
Once every row is DONE, or a paths report exists, the block prints `paths:` after `scaffold:`:
`needed` with no current report, `approved (<report>)` or `approved (no commands)`, or `round
<n> (request changes: <sections>)`, ` (cap)` from round 3. Below the cap a named section that
is otherwise DONE is `FIX n` with the evidence `paths r<m> request changes (<report>)`; a fix
to its code makes the report stale, so the section reads REVIEW and the line `paths: needed`.
`shipped: yes` needs `paths: approved`. `--inputs` adds the paths report to `Review:`, and
`--fields` prints it as a sixth line, `paths report:`, until a review round of the section is
newer than it; every other `fields-*` case now also expects `paths report: none`
(`fields-bad-target` prints no fields). `shipped` and `shipped-sync` build no package
`pyproject.toml`, so they stay `shipped: yes` and also expect `paths: approved (no commands)`.

**The paths review end to end (2.5).** One case (`site/notes/2.5-readability-09-docs-and-release.md`,
the last row), `paths-e2e`: all done, with the `commands` step's `load.py` replaced by
`calltree-lambda`'s, so the one command reaches its effect through a lambda. Its check is
`--paths data`; its job is the seed `run-package` eval 14 builds, where `status.py data` prints
`paths: needed` and the driver spawns the paths review.

**Readiness and dependency READMEs (2.6).** Six cases (`site/notes/2.6-spine-03-status-readiness.md`,
the last six rows). `base` takes `call_paths: true`, which appends a `## Call paths` heading
whose one entry is the `commands` macro's tree (`data-load`, budget 8, `cli.load` →
`pipelines.run_load` → `ingest.read_trades` → `shutil.copy`), or a string, written as the
heading's body verbatim; without it every contract stays the 2.5 one. With the heading the
`surface` row is ready at DESIGN and TEST before any sibling is DONE, and waits for every
other section from IMPLEMENT on; without it the surface waits at every state, as before.
`--fields` prints a seventh line, `dependency readmes:`, the READMEs of the row's `depends on`
that exist on disk in the Sections table's order, `none` when none does.

**Against the contract (2.6).** Nine cases (`site/notes/2.6-spine-05-against-contract-review.md`,
the `calltree-contract-*` rows at the end; `-prose-line` from phase 7; the two `-change-file`
cases from the release's follow-up: an open change file's entry is compared in the contract's
place, a synced one is not). Each runs `base` with a `call_paths` heading
(or none), then `commands`, and `--paths data --against-contract`. After the block's footer the
contract's entry prints: `contract: data-load (budget 8)`, the kind, each contract frame `match`
with the built frame or `missing`, a built frame between two matched ones `extra`, the effect
`reached`, and `summary: <k> match, <e> extra, <m> missing; depth <d> of budget <n>`. The frame
column is padded to the entry's longest frame, so the expectations on a shorter frame are
regexes. Without an entry, or without the heading, one `contract:` line ends the block and no
`summary:` prints.

**Data stages (2.7).** Fourteen cases (`site/notes/2.7-data-loop-02-status-and-driver.md`,
the last fourteen rows). Each runs `base` with `"stage": true`: the `clean` row's `source` is
`stage:rawtrades`, its `builds with` `dev-team:data-quality`, and the contract ends with a
**Package conventions** line for the stage (pull cap 400 rows, `D1`). The `profile` macro
commits `docs/sources/rawtrades.md`, a round-0 profile with one kind under **Quirks** and a
`## data/clean` heading under **Sections served**, then one round line per entry of `lines`
(`Round <r> — 2026-09-27 — commit <c> — <verdict>`), or with `append` only the lines. A
`stage:` source is PROBE with no round line, or while the newest one is `pending verify` or
`revise: …`; any other verdict closes round 0 and the row moves on. `--profile` prints the
profiler's fifteen-line block. Four of the fourteen (`stage-round0-closed`,
`stage-round0-blocked`, `stage-design-kept-on-append`, `inputs-stage-source-probes`) already
passed on 2.6.0's `status.py`, which ignores a `stage:` source: they pin that round 0 closed
leaves the row where the older rules put it. Phase 5 adds seven
(`site/notes/2.7-data-loop-05-after-build-rounds.md`), each after a closed round 0: a row that
would be DONE is PROBE again while its newest round line's commit is `none` or older than the
section's code. Four of them (`-clean`, `-new-kinds`, `-verify`, `-not-done`) passed before the
change: they pin that the after-build round never preempts another state. Phase 6 adds six
(`site/notes/2.7-data-loop-06-cap-and-defer.md`), each after a closed round 0 on built code,
with the `deviation` macro's `raised_by` option for the profiler's `spec-change:design` entry:
a round 2 or later closing `new kinds: …` while that entry is open is BLOCKED at the profile
cap, and `--profile … --defer` prints the defer block. Three of them (`-round1-not-cap`,
`-entry-resolved`, `stage-deferred`) and `fields-delta-profile-cap` passed before the change:
they pin that the cap fires only at round 2 or later on an open entry, and that `--fields`
stays `delta` once the cap's evidence leads with `profile`.
Phase 7 adds two (`site/notes/2.7-data-loop-07-size-guard.md`): `--run-gate` fails a data
profile's `rawtrades.sample.json` over 200 KB, and passes a researcher's api sample of the same
size. A `files` content may be `{"repeat": ["<string>", <n>]}`, the string repeated `n` times.
`run-gate-sample-api-over-pass` passed before the change, by construction.

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
| `shape-pass` | `base`, `design`, `tests`, `build` for ingest | `--shape data --section ingest` | `PASS shape data/ingest`; `MEASURED shape indirect: 0` (2.5 phase 5); exit 0 |
| `shape-trivial-helper` | the same, then a commit adding `helper.py` (`load_rows` calls `_strip`, one statement) | the same | `FAIL shape: packages/data/src/data/ingest/helper.py:9 trivial-helper _strip`; `MEASURED shape indirect: 0` (2.5 phase 5); no `PASS shape`; exit 1 |
| `shape-helper-two-callers` | `helper.py` with a second function `load_text` that also calls `_strip` | the same | `PASS shape data/ingest`; exit 0 |
| `shape-helper-callback` | `helper.py` whose `load_rows` returns `sorted(path, key=_strip)` | the same | `PASS shape data/ingest` |
| `shape-helper-four-statements` | `helper.py` whose `_strip` has four statements | the same | `PASS shape data/ingest` |
| `shape-helper-before-review` | the `helper.py` commit, then round 1 `a` and `b` approving | the same | `PASS shape data/ingest` (the review's `Commit:` covers the helper) |
| `shape-helper-after-review` | round 1 `a` and `b` approving, then the `helper.py` commit | the same | the `shape-trivial-helper` FAIL line; exit 1 |
| `shape-exempt-kinds` | a commit adding `kinds.py`: `__repr__`, a `@property` `_size`, and `_fetch` (two statements) in two classes, called once through `self` | the same | `PASS shape data/ingest` |
| `shape-test-file-exempt` | `helper.py`'s two functions committed as `packages/data/tests/unit/ingest/test_helper.py` | the same | `PASS shape data/ingest` |
| `shape-bad-target` | `base`, `design`, `tests`, `build` for ingest | `--shape data --section nope` | `no section nope in docs/packages/data/contract.md`; exit 2 |
| `calltree-direct` | `base`, `commands` | `--paths data` | the macro's whole block, line for line: `command: data-load = data.cli:load`, frames `load`, `run_load`, `read_trades`, leaves `[effect: shutil.copy]` and `[effect: open]`, `depth to first effect: 2`, `deepest effect: 2`, `indirect frames: 0`; exit 0 |
| `calltree-lambda` | `commands` with `load.py` holding `guarded(step)` (`return step()`) and `rows = guarded(lambda: read_trades(path))` | the same | `guarded (…load.py:6)`; under it `step() (…load.py:8) [unresolved]` and `lambda (…load.py:13) [indirect]`; `read_trades` under the lambda; `depth to first effect: 4`; `indirect frames: 1` |
| `calltree-mapping` | `load.py` with `_RUNNERS = {"trades": read_trades}` and `rows = _RUNNERS["trades"](path)` | the same | `read_trades (…reader.py:7) [indirect]`; `indirect frames: 1`; `depth to first effect: 2` |
| `calltree-unresolved` | `load.py` with `reader = make_reader()` (a package function returning a `TradeReader`) and `rows = reader.read(path)` | the same | a line holding `reader.read(path)` ending `[unresolved]`; `depth to first effect: none` |
| `calltree-logging-not-effect` | `cli.py` calling `logger.info("x")` (`loguru`) and `re.compile("x")` before `run_load` | the same | no `[effect: logger.info]`, no `[effect: re.compile]`; `depth to first effect: 2` |
| `calltree-third-party` | `reader.py` calling `requests.get(path, timeout=10)` in place of the copy and the open | the same | `[effect: requests.get]`; `depth to first effect: 2` |
| `calltree-self-method` | `reader.py` with a class `Reader` whose `read` calls `self._copy(path)`, `_copy` calling `shutil.copy`, and `read_trades` returning `Reader.read(Reader(), path)` | the same | frames `Reader.read (…reader.py:9)` and `Reader._copy (…reader.py:14)`; `depth to first effect: 4` |
| `calltree-recursive` | `load.py` whose `run_load` calls itself under an `if` before `read_trades` | the same | `run_load (…load.py:6) [recursive]`; `depth to first effect: 2` |
| `calltree-no-commands` | the package `pyproject.toml` without `[project.scripts]` | the same | the one line `paths: no commands`; exit 0 |
| `shape-options-bag` | `base`, `design`, `tests`, `build` for ingest, then a commit adding `bag.py` | `--shape data --section ingest` | `FAIL shape: packages/data/src/data/ingest/bag.py:12 options-bag load_with`; `MEASURED shape indirect: 0`; no `PASS shape`; exit 1 |
| `shape-options-bag-before-review` | the `bag.py` commit, then round 1 `a` and `b` approving | the same | `PASS shape data/ingest`; no `FAIL shape`; exit 0 |
| `shape-keyword-only-pass` | a commit adding `keywords.py`: `load_with(path, *, strict, limit, retries, since, until)` | the same | `PASS shape data/ingest`; no `FAIL shape`; exit 0 |
| `shape-measured-indirect` | a commit adding `runners.py`: `sorted(rows, key=lambda r: r[0])` and `_RUNNERS[kind](path)` | the same | `MEASURED shape indirect: 2`; `PASS shape data/ingest` |
| `shape-measured-zero` | `base`, `design`, `tests`, `build` for ingest | the same | `MEASURED shape indirect: 0`; `MEASURED shape depth load_trades: none`; `PASS shape data/ingest` |
| `shape-depth` | `base`, `commands`, then `design`, `tests`, `build` for ingest, then an `edit` giving the README a second row, `` `read_trades` `` | the same | `MEASURED shape depth load_trades: none`; `MEASURED shape depth read_trades: 0` |
| `shape-adopted-document` | `base`; a commit adding `helper.py` under ingest; a design whose first line is `Mode: document`; `tests`, `build` | the same | `PASS shape data/ingest`; no `FAIL shape` (the helper predates the design) |
| `shape-adopted-added-after` | the same, then a commit adding `bag.py` | the same | the `shape-options-bag` FAIL line; no `trivial-helper`, no `PASS shape`; exit 1 |
| `rounds-paths-none` | `base`, `design`, `tests`, `build` for ingest | `--rounds data/paths` | `rounds: 0`; `next round: 1`; a line matching `/^commit: [0-9a-f]{7}$/`; `previous: none`; `diff base: none`; exit 0 |
| `rounds-paths-one` | the same, then `paths_review` round 1, `request changes`, one `ingest: P2 — …` critical | the same | `rounds: 1`; `next round: 2`; `previous: docs/packages/data/reviews/paths/2026-09-27-r1-p.md`; a line matching `/^diff base: [0-9a-f]{7}$/` |
| `rounds-section-unaffected` | the same as `rounds-paths-one` | `--rounds data/ingest` | `rounds: 0`; no `previous:`, no `diff base:` (a paths report is not a section's round) |
| `paths-needed` | all done | `—` | `paths: needed`; `shipped: no (paths needed)`; `next: /dev-team:run-package data` |
| `paths-no-commands` | all done, without `commands` | `—` | `paths: approved (no commands)`; `shipped: yes` |
| `paths-approved` | all done; `paths_review` round 1 `approve` | `—` | `paths: approved (docs/packages/data/reviews/paths/2026-09-27-r1-p.md)`; `shipped: yes` |
| `paths-request-changes` | all done; `paths_review` round 1 `request changes`, the P2 line | `—` | `ingest · FIX 1`, evidence `/^paths r1 request changes \(docs/packages/data/reviews/paths/2026-09-27-r1-p\.md\)$/`; `clean · DONE`; `paths: round 1 (request changes: ingest)`; `shipped: no (paths round 1)`; `next: /dev-team:run-package data` |
| `paths-stale-after-fix` | the same; then an `edit` of `ingest/reader.py` | `—` | `ingest · REVIEW`; `paths: needed` |
| `paths-reviewed-after-fix` | the same; then a round-2 `s` review of `ingest` that approves | `—` | `ingest · DONE`; `paths: needed`; `shipped: no (paths needed)` |
| `paths-round-2-approved` | the same; then `paths_review` round 2 `approve` | `—` | `paths: approved (docs/packages/data/reviews/paths/2026-09-27-r2-p.md)`; `shipped: yes` |
| `paths-cap` | all done; `paths_review` rounds 1, 2 and 3, each `request changes` with the P2 line | `—` | `ingest · DONE`; `paths: round 3 (request changes: ingest) (cap)`; `shipped: no (paths round 3)`; `next: /dev-team:run-package data or /dev-team:run-package data --defer` |
| `paths-defer-approved` | the same; then `paths_review` round 4, `approve`, `"focus": "defer"` | `—` | `paths: approved (docs/packages/data/reviews/paths/2026-09-27-r4-p.md)`; `shipped: yes` |
| `paths-no-section-named` | all done; `paths_review` round 1 `request changes`, critical `the build command is too deep` | `—` | `ingest · DONE`; `paths: round 1 (request changes: no section named)` |
| `paths-not-all-done` | `base`, `commands`, `done` for `ingest` only | `—` | no `paths:` |
| `inputs-paths-fix` | as `paths-request-changes` | `--inputs data/ingest` | a line `/^Review: docs/packages/data/reviews/paths/2026-09-27-r1-p\.md$/`; `Round: 2`; exit 0 |
| `fields-paths-report` | as `paths-stale-after-fix` | `--fields data/ingest` | sixth line `paths report: docs/packages/data/reviews/paths/2026-09-27-r1-p.md`, after `upstream interfaces: none`; exit 0 |
| `repo-paths-needed` | as `paths-needed` | `--repo` | `  - data: building (4/4 DONE, paths needed)`; exit 0 |
| `paths-e2e` | all done, with `calltree-lambda`'s `load.py` in the `commands` step | `--paths data` | `lambda (…load.py:13) [indirect]`; `indirect frames: 1`; exit 0 (the seed of `run-package` eval 14) |
| `surface-early-design-ready` | `base` with `call_paths: true` | `—` | `surface · DESIGN`, ready `yes`; the `clean` row ready `no` (its dependency `ingest` is not DONE) |
| `surface-early-test-ready` | `base` (`call_paths: true`), `design` surface | `—` | `surface · TEST`, ready `yes` |
| `surface-early-implement-waits` | `base` (`call_paths: true`), `design` and `tests` surface | `—` | `surface · IMPLEMENT`, ready `no` |
| `surface-no-call-paths-waits` | `base` | `—` | `surface · DESIGN`, ready `no` |
| `fields-dependency-readmes-none` | `base` (`call_paths: true`) | `--fields data/surface` | `paths report: none` then `dependency readmes: none`; exit 0 |
| `fields-dependency-readmes-some` | `base`, `done` ingest, `build` clean | `--fields data/surface` | `dependency readmes: packages/data/src/data/ingest/README.md, packages/data/src/data/clean/README.md` (storage has no README); exit 0 |
| `calltree-contract-match` | `base` (`call_paths: true`), `commands` | `--paths data --against-contract` | `contract: data-load (budget 8)`; a line `/^    1 cli\.load\s+match  load \(packages/data/src/data/cli\.py:6\)$/`; `3 ingest.read_trades  match  read_trades (packages/data/src/data/ingest/reader.py:7)`; `effect shutil.copy  reached`; `summary: 3 match, 0 extra, 0 missing; depth 2 of budget 8`; exit 0 |
| `calltree-contract-extra` | as `-match`, `load.py`'s `run_load` calling `_read(path)` and `_read` calling `read_trades` | the same | a line `/^    -\s+extra  _read \(packages/data/src/data/pipelines/load\.py:\d+\)$/`; `summary: 3 match, 1 extra, 0 missing`; exit 0 |
| `calltree-contract-missing` | the matching entry with a fourth frame `4 `ingest.parse_rows`` before the effect | the same | a line `/^    4 ingest\.parse_rows\s+missing$/`; `effect shutil.copy  reached`; `summary: 3 match, 0 extra, 1 missing`; exit 0 |
| `calltree-contract-no-entry` | an entry for `` `data-build` (budget 8) `` only | the same | `contract: no entry for data-load`; no `summary:`; exit 0 |
| `calltree-contract-no-heading` | `base` without `call_paths`, `commands` | the same | `contract: no Call paths heading`; no `summary:`; exit 0 |
| `calltree-contract-past-budget` | the matching entry with `(budget 1)` | the same | `summary: 3 match, 0 extra, 0 missing; depth 2 past budget 1`; exit 0 |
| `calltree-contract-prose-line` | as `-match`, with a wrapped prose line starting `**Call paths**` above `## Public surface (intent)` (`edit`) | the same | `contract: data-load (budget 8)`; `summary: 3 match, 0 extra, 0 missing; depth 2 of budget 8`; no `contract: no entry`; exit 0 (phase 7: only a numbered bold line is an item) |
| `calltree-contract-change-file` | as `-extra`, plus an open `docs/packages/data/changes/load-read.md` whose `## Contract changes` gives the `data-load` entry `from` (three frames) and `to` (with `3 pipelines._read`), a nested bullet after it | the same | `contract: data-load (budget 8) from docs/packages/data/changes/load-read.md`; a line `/^    3 pipelines\._read\s+match  _read \(…load\.py:\d+\)$/`; `summary: 4 match, 0 extra, 0 missing; depth 3 of budget 8`; no `extra  _read`; exit 0 |
| `calltree-contract-change-file-synced` | as `-change-file`, `Status: synced` | the same | `contract: data-load (budget 8)`; `summary: 3 match, 1 extra, 0 missing`; no ` from docs/packages/data/changes/`; exit 0 |
| `stage-probe-dependency-not-done` | `base` (`stage: true`) | `—` | `clean · PROBE`, ready `no`, evidence `stage:rawtrades lacks ## data/clean` |
| `stage-probe-no-profile` | the same, ingest done | `—` | `clean · PROBE`, ready `yes`, the same evidence |
| `stage-probe-pending-verify` | ingest done; `profile` `["pending verify"]` | `—` | `clean · PROBE`, evidence `stage:rawtrades r0 pending verify` |
| `stage-probe-revise` | ingest done; `profile` `["pending verify", "revise: K1"]` | `—` | `clean · PROBE`, evidence `stage:rawtrades r0 revise: K1` |
| `stage-round0-closed` | ingest done; `profile` `["pending verify", "kinds: 1 (0 to decide)"]` | `—` | `clean · DESIGN`, evidence `no design` |
| `stage-round0-blocked` | as closed, `kinds: 1 (1 to decide)`; `docs/decisions.md` with `D2` open, `Scope: data/clean`, no assumption | `—` | `clean · BLOCKED`, evidence `D2 open, no assumption` |
| `stage-design-kept-on-append` | as closed; `design` clean; `profile` `append` one more round-0 line | `—` | `clean · TEST`; no `newer than design` |
| `profile-block-round0` | ingest done | `--profile data/clean` | every field line in order, `Mode: profile` to `Run: run-package data`, `Skills to invoke: none`, the `Data:` line as the contract writes it; `Source probes: docs/sources/trades.md`; exit 0 |
| `profile-block-verify` | as `stage-probe-pending-verify` | `--profile data/clean` | `Mode: verify`, `Round: 0`, `Revise: none` |
| `profile-block-revise` | as `stage-probe-revise` | `--profile data/clean` | `Mode: profile`, `Revise: K1` |
| `profile-block-none-due` | as `stage-round0-closed` | `--profile data/clean` | `Mode: profile`, `Round: 0`, `Revise: none`, `Commit: none` |
| `profile-no-stage-source` | `base` (`stage: true`) | `--profile data/ingest` | `profile: no stage source in data/ingest`; exit 0 |
| `profile-bad-target` | the same | `--profile data/nope` | `no section nope in docs/packages/data/contract.md`; exit 2 |
| `inputs-stage-source-probes` | as `stage-round0-closed`; `design` clean | `--inputs data/clean` | `Source probes: docs/sources/rawtrades.md` |
| `run-gate-stage-no-deps` | `base` (`stage: "no-deps"`): the `clean` row's `depends on` is `—` (phase 4) | `--run-gate data` | `run gate: FAIL`; `data/clean: stage:rawtrades has no depends on; nothing produces its data`; exit 1 |
| `run-gate-stage-ok` | `base` (`stage: true`) (phase 4) | `--run-gate data` | `run gate: PASS`; exit 0 |
| `stage-after-build-due` | ingest done; round 0 closed; `done` clean (phase 5) | `—` | `clean · PROBE`, evidence `stage:rawtrades r0 not profiled on built code` |
| `stage-after-build-clean` | as `-due`; `profile` `append` round 1 on `{HEAD}`, `clean` | `—` | `clean · DONE` |
| `stage-after-build-code-newer` | as `-clean`; `fix` clean; `review` round 2 `s` approving the new code | `—` | `clean · PROBE`, evidence matches `stage:rawtrades r1 \w{7} older than code \w{7}` |
| `stage-after-build-new-kinds` | as `-due`; round 1 `new kinds: K2`; an open `spec-change:design` ledger entry, `Raised by: profiler — run-package data` (explicit step) | `—` | `clean · DESIGN`, evidence starts `open data/clean — ` |
| `stage-after-build-verify` | as `-due`; round 1 `pending verify` | `—` | `clean · PROBE`, evidence `stage:rawtrades r1 pending verify` |
| `stage-after-build-not-done` | ingest done; round 0 closed; `design` and `tests` clean, no build | `—` | `clean · IMPLEMENT` |
| `profile-block-round1` | as `stage-after-build-due` | `--profile data/clean` | `Mode: profile`, `Round: 1`; a line `^Commit: [0-9a-f]{7,40}$`; exit 0 |
| `stage-cap` | as `-due`; `profile` `append` round 1 `new kinds: K2` and round 2 `new kinds: K3` on `{HEAD}`; an open `spec-change:design` entry, `raised_by` `profiler — run-package data` (phase 6) | `—` | `clean · BLOCKED`, evidence matches `^profile r2 new kinds \(cap\), open data/clean — ` |
| `stage-cap-round1-not-cap` | as `-due`; round 1 `new kinds: K2`; the entry, open | `—` | `clean · DESIGN`, evidence starts `open data/clean — ` |
| `stage-cap-entry-resolved` | as `stage-cap`, the entry `resolved` | `—` | no `clean · BLOCKED`, no `(cap)` |
| `stage-deferred` | as `stage-cap`, the entry `resolved`; `profile` `append` round 2 `deferred` on `{HEAD}` | `—` | `clean · DONE` |
| `profile-block-defer` | as `stage-cap` | `--profile data/clean --defer` | `Mode: defer`, `Round: 2`; a line `^Commit: [0-9a-f]{7,40}$`; exit 0 |
| `fields-delta-profile-cap` | as `stage-cap` | `--fields data/clean` | `mode: delta` |
| `run-gate-sample-over` | `base` (`stage: true`); `profile` `[]`; `docs/sources/rawtrades.sample.json` as `{"repeat": ["x", 210000]}` (phase 7) | `--run-gate data` | `run gate: FAIL`; `docs/sources/rawtrades.sample.json: 205 KB, over 200 KB`; exit 1 |
| `run-gate-sample-api-over-pass` | `base`; `docs/sources/polygon.sample.json` the same size, no `— stage —` sibling (phase 7) | `--run-gate data` | `run gate: PASS`; exit 0 |
