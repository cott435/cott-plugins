# issues.py settling, brief list and collapsed index — mechanical checks

**Tested against:** uncommitted — see working-tree diff (`scripts/issues.py`, `skills/audit-run/SKILL.md`) on branch `plugin-dev-runs-dir` · model: none (script only) · 2026-10-10
**Set:** none · **Iteration:** none · **Baseline:** none · **Pass rate:** n/a

## What was tested

An issue held in three sessions, and not found again since, derives `settled`: it leaves `list --status fixed,released,verified`, shows as one line in `INDEX.md`, and a later Found in line unsettles it. `list --format brief` prints one line per fixed issue. `check-result` refuses `not exercised` and `not testable`.

## Method

`evals/fixtures/issues/check.py` against a throwaway plugin (new, fix, three held checks from three sessions, a later `seen`), plus `contract_sweep.py` and `issues.py check`/`index` on the migrated `dev-team` ledger (78 issues; none of them settled yet).

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| fixture check | 11 checks pass | 11/11 | yes |
| contract sweep | 15/15 | 15/15 | yes |
| `issues.py check`, dev-team | `ok` | `ok: 78 issues` | yes |

## Verdict

The mechanics hold. Not yet run: the `audit-run` behavioral set with the Checks-line change (TO-002 gets no line), and a real rerun that settles an issue.
