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
`<pkg>/<section>: regenerate 1 intent tests` commit) and `deviation` (one
`docs/deviations.md` entry). `{HEAD}` in any file content is the commit the step starts from.

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
| `design-probe-newer` | the probe doc's shared headings changed after the design | `—` | `ingest · DESIGN`, evidence `/docs/sources/trades.md [0-9a-f]{7} newer than design/` |
| `design-probe-other-section` | another section's entry appended to the probe doc: not stale | `—` | `ingest · IMPLEMENT` |
| `design-spec-change-design` | open spec-change:design after the tests | `—` | `ingest · DESIGN`, evidence `/spec-change:design/` |
| `done-and-surface-ready` | ingest, clean, storage DONE; surface ready | `—` | `surface · DESIGN`, ready yes; `ingest · DONE`; `clean · DONE`; `storage · DONE`; `shipped: no (surface DESIGN)`; `next: /dev-team:run-package data` |
| `fix-round-1` | round 1: a approves, b requests changes; the worst wins | `—` | `ingest · FIX 1`, round 1 |
| `implement-missing-readme` | intent tests, no README | `—` | `ingest · IMPLEMENT`, evidence `/no .*README.md/` |
| `implement-regeneration-skipped` | DONE, then an approved deviation and a regeneration commit: still DONE | `—` | `ingest · DONE`, round 1 |
| `implement-tests-newer` | intent tests edited after the README (not a regeneration) | `—` | `ingest · IMPLEMENT`, evidence `/^tests [0-9a-f]{7} newer than README [0-9a-f]{7}$/` |
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
