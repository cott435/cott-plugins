# M — the four defects eval K found, fixed

**Tested against:** `8d1c722`, the phase-9 commit, with the fixes uncommitted — see the
working-tree diff: `skills/status/scripts/status.py`, `agents/reviewer.md`,
`agents/architect.md`, `skills/workspace-scaffold/SKILL.md`, `skills/status/SKILL.md`,
`contracts.yml` · model: `claude-sonnet-5` (headless runs; `claude-opus-5` ran the checks) ·
Claude Code `2.1.270` · 2026-09-20

## What was tested

The four defects [eval K](2026-09-19-k-end-to-end.md) found, each fixed and re-checked on the
repo K built:

1. `status.py` reads a plan as stale once the package ships. Fix: a plan review's freshness is
   measured over the documents it covers — the contract, `design/`, `integration.md`,
   `surface.md` — and a commit whose `Dev-Team-Run:` trailer is `sync-design` does not age it.
2. The reviewer can write `approve with fixes` with a CRITICAL standing. Fix: a **Verdict**
   section in `agents/reviewer.md` deciding the verdict from severity alone.
3. Root `uv run pytest` collides on two packages' `tests` trees. Fix: the root `pyproject.toml`
   template in `workspace-scaffold` carries `addopts = "--import-mode=importlib"`.
4. `agents/architect.md` says bare `designer`, and a fork spawned `general-purpose` designers.
   Fix: the three places that name an agent name it `dev-team:<agent>`, plus a `contracts.yml`
   claim forbidding the bare form there.

## Method

The repo eval K built is the fixture: `…/scratchpad/k/repo` at `16b0f30`, both packages
shipped. Copies of it per case, so no case sees another's edits.

**Mechanical.** For 1, seven states of a copy, reading `status.py`'s `plan:` line and
`--plan-gate`. For 3, root and per-package `pytest` before and after adding the template's
`addopts` line to that repo's root `pyproject.toml`. For 4, `contract_sweep.py` on the real
files and with the old bare wording planted back.

**Behavioral.** Real headless runs, `claude -p "<command>" --plugin-dir <abs>/dev-team --model
claude-sonnet-5 --output-format stream-json --verbose --permission-mode bypassPermissions`,
each on its own copy, `uv sync --all-packages` first (a copied `.venv` points at the original).

- 2: `/dev-team:review-package analysis` on a copy at `16b0f30`. The CRITICAL K's review
  filed — two integration tests importing `data.storage.store` — is still in the code and
  still open in `docs/followups.md`. The 0.5 reviewer said `approve with fixes` on it.
- 4: `/dev-team:plan-package analysis` on a copy reset to `4555b51`, the commit before K's
  run 5, which is the run that spawned `general-purpose` designers. It stopped for D1 first
  (that copy predates the ledger entry), so it ran again to accept the assumption, as the stop
  message says. Spawns are read from the stream's `subagent_type`.

Cost: $2.07 over three runs ($0.48 + $0.32 + $1.27).

## Results

| # | Case | Expected | Observed | Pass |
|---|---|---|---|---|
| 1 | baseline: `sync-design` and `finalize-package` are the newest commits | `plan: reviewed` | `reviewed … @ceef58b` for `data`, `@e17554d` for `analysis` | ✅ |
| 1 | a design edited by a plain commit | stale | `plan: stale` | ✅ |
| 1 | the same edit under a `Dev-Team-Run: sync-design data` trailer | reviewed | `plan: reviewed` | ✅ |
| 1 | the package contract edited | stale, gate FAIL | `plan: stale`; `plan gate: FAIL — data: plan not reviewed since last change` | ✅ |
| 1 | `interface.md` rewritten under a `finalize-package` trailer | reviewed | `plan: reviewed` | ✅ |
| 1 | a design edited, uncommitted | uncommitted | `plan: uncommitted` | ✅ |
| 1 | the plan review's `Commit:` line removed | stale | `plan: stale … @—`, and reviewed again once restored | ✅ |
| 1 | both plan gates on the shipped repo | PASS | `plan gate: PASS` for both packages | ✅ |
| 2 | re-review of the package whose CRITICAL is unfixed | `request changes` | `Verdict: request changes`, the CRITICAL carried and named, 0 new follow-ups (already filed) | ✅ |
| 3 | root `pytest`, before | 16 collection errors | 16 errors | — (control) |
| 3 | root `pytest`, after `addopts` | passes | 163 passed | ✅ |
| 3 | per-package `pytest`, after | still passes | 109 passed | ✅ |
| 4 | `plan-package` fan-out | two `dev-team:designer` spawns | 2 tasks, both `dev-team:designer`, both foreground; designs and `surface.md` written, `99f06b6` | ✅ |
| 4 | contracts, real files | 23/23 | 23/23 | ✅ |
| 4 | contracts, bare `designer` planted back | the new claim fails | `FAIL … agents/architect.md:319` | ✅ |

The run-4 stop for D1 is correct behavior, not a failure: that copy predates the ledger entry
K's run 5 created, and the architect asks once per tag.

## Verdict

All four hold. 1 and 3 are mechanical and exhaustive on the states that matter; 2 and 4 are
real runs of the exact commands that failed in K, on the repo K built. K's four failing checks
would now read: plan `reviewed`, the package review `request changes` (so `run-package` would
finalize and review again instead of stopping with an open CRITICAL), root `pytest` passing in
a repo scaffolded from here on, and every designer a plugin agent.

Two things K logged are still open by design, and are not this pass's subject: the tester's
own intent tests trip Guarded constraint rows with nobody able to fix them, and the
implementer ran `find /` for a skill file it had already read. K is not re-run end to end —
fix 3 only helps a repo scaffolded after it, and re-running K would cost what K cost.
