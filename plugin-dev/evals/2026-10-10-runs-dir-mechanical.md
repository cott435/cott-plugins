# runs/ directory move — mechanical checks

**Tested against:** `dc65572` (`scripts/issues.py`, `skills/run-flow/scripts/trace.py`, `skills/run-flow/scripts/flow.py`) · model: none (scripts only, no agent run) · 2026-10-10
**Set:** none · **Iteration:** none · **Baseline:** none · **Pass rate:** n/a

## What was tested

The ledger and the session workspaces moved under the audited plugin's `runs/`: `runs/audits/` for the committed ledger, `runs/<project>/<command> <title>/<id8>/` for a session's trace. The scripts and the migrated `dev-team` ledger read and write the new paths, and a session keeps its folder once built.

## Method

Run by hand against the working tree, no model. `contract_sweep.py` on plugin-dev; `evals/fixtures/phases/check.py`; `issues.py index` then `check` on the migrated `dev-team/runs/audits/`; and, on the `audit-run` fixture (`make_session.py`, `AUDIT_RUN_PROJECTS` set), `trace.py where`, `build`, a second `where`, `view --root runs` and `flow`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| contract sweep | every claim holds | 15/15 pass | yes |
| phases fixture | unchanged | 56/56 pass | yes |
| `issues.py check` on migrated ledger | `ok`, INDEX.md fresh | `ok: 78 issues` | yes |
| `where` on the fixture session | `runs/toy-project/ship the-toy-file/0a0d17f0` | as expected | yes |
| `where` again after `build` | the same folder | the same folder | yes |
| `view --root runs` | page at `runs/views/`, links URL-encoded across run folders | `../toy-project/ship%20the-toy-file/0a0d17f0/units/U01.html` | yes |
| `where` on an untitled session | no `untitled` in the folder name | `runs/toy-project/ship/0f10d17f` (after a fix) | yes |

## Verdict

The mechanical side holds. Not yet run: the behavioral sets that were edited to the new paths (`audit-run`, `run-flow`, `fix-issues`, `bump-version`), and the rename-after-build case of the frozen slug, which `where` implements by globbing `runs/*/*/<id8>` but which no check has exercised. The `build-site` rebuild is pending the merge.
