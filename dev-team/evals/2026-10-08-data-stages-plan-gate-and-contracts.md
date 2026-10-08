# Data stages plan: the run gate, the profiler's `Data:` line and the contract claims

**Tested against:** uncommitted — see working-tree diff on branch `dev-team-data-stages` (base `29a66fa`, dev-team 2.10.0) (`skills/status/scripts/status.py`, `skills/planning-templates/references/package-contract.md`, `contracts.yml`) · model: none, mechanical · 2026-10-08
**Set:** `evals/fixtures/state-cases/` (every case) and `contracts.yml` (every claim) · **Iteration:** none (shell runs, no `run-evals`) · **Baseline:** 2.10.0 by construction: the four new FAIL cases cannot fail before the change · **Pass rate:** 226/226 state cases, 54/54 claims

## What was tested

`status.py --run-gate <pkg>` reads a marked section's **Data stages** row and fails on a
missing row (with no older **Package conventions** line), an empty cell, a `cleaned by` that
is another section, or a producer named in `data` that the section does not depend on, while
a 2.7-era contract with the conventions line alone still passes; `--profile` prints the row as
the `Data:` line, cells joined by ` · `; and the new **Data stages** and **Plan** headings are
claims `check-contracts` enforces.

## Method

Shell runs. `python3 evals/fixtures/state-cases/check.py` over every case after `build.py`'s
`stage: true` was switched to write the table; five new cases (`run-gate-stage-conventions-line`,
`-no-plan`, `-empty-cell`, `-producer-missing`, `-wrong-cleaner`) and `profile-block-round0`'s
`Data:` expectation rewritten. `python3 ../plugin-dev/scripts/contract_sweep.py` on the bundle;
then the **Data stages** item renamed to **Data plan** in the template, the sweep rerun, and
the rename reverted. No model ran; no API cost.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| all 221 prior state cases | PASS | 221 PASS (including the 2.7 stage cases, now on the table) | yes |
| `run-gate-stage-conventions-line` | `run gate: PASS`, exit 0 | as expected | yes |
| `run-gate-stage-no-plan` | FAIL `stage:rawtrades has no Data stages row; plan it with /dev-team:plan-package data`, exit 1 | as expected | yes |
| `run-gate-stage-empty-cell` | FAIL `leaves pull empty` | as expected | yes |
| `run-gate-stage-producer-missing` | FAIL `names producer storage not in its depends on` | as expected | yes |
| `run-gate-stage-wrong-cleaner` | FAIL `says cleaned by ingest, not clean` | as expected | yes |
| `profile-block-round0` | `Data:` is the row as one line, ` · `-joined | as expected | yes |
| contract sweep, bundle as edited | 54/54 PASS | 54/54 | yes |
| contract sweep, **Data stages** planted as **Data plan** | the package-contract claim FAILs naming architect, profiler, data-profile and status.py | `FAIL package contract headings …` naming all four | yes |
| contract sweep, restored | 54/54 | 54/54 | yes |
| `build_site.py` | the site builds with the new note | see the build output in the chat; the note and the heading render | yes |

## Verdict

The claims hold. Not run: the behavioral sets for the architect (`evals/sets/architect.json`)
and the profiler (`evals/sets/profiler.json`), whose expectations are written to the 2.7
conventions line and the twelve-heading profile; they need re-authoring for the **Data
stages** table and the **Plan** heading before a with/without comparison means anything. That
is the open item for 2.11.x.
