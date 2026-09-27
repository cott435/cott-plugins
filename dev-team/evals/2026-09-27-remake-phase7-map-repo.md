# remake phase 7 — map-repo

**Tested against:** uncommitted — see working-tree diff (on `4ee8f00`; `skills/map-repo/SKILL.md` new, `agents/architect.md`, `skills/map-project/` deleted, `skills/reserved-skill-names/SKILL.md`, `README.md`, `site/site.yml`) · model: `claude-opus-5-5` (the phase, 7.1), executors and graders `claude-sonnet-5`, the 7.3 headless session `claude-sonnet-5` (its forked architect and two package architects inherit it) · 2026-09-27
**Set:** `evals/sets/map-repo.json` evals 1, 2 · **Iteration:** `evals/workspace/map-repo/iteration-1` · **Baseline:** none (`without_skill`) · **Pass rate:** 100% vs 41% (eval 1: 11/11 vs 9/11; eval 2: 7/7 vs 0/7)

## What was tested

- **7.1** The three `names_listed` claims FAIL when `map-repo` exists and is unlisted (and `map-project` is listed with no directory), and all claims PASS after the three-file edits.
- **7.2** Following `/dev-team:map-repo` with `agents/architect.md` maps a two-package tree into two package contracts (each Sections table ending with `surface`) and a repo contract, files the planted cross-package internals import to the backlog, and states phase 2 as two `dev-team:architect` spawns in one message with the spawn block. On a monolith, it stops with open `D<n>` stubs tagged `/dev-team:map-repo (interview)` and writes no contract.
- **7.3** `/dev-team:map-repo` loads from `--plugin-dir` and runs end to end in a real repo with two `packages/*/pyproject.toml`: it returns `Result:`, and `docs/architecture.md` exists.

## Method

- **7.1** `contract_sweep.py` on the working tree after `map-repo` was created and `map-project` removed, then again after the edits to `reserved-skill-names`, the README tree and `site.yml`.
- **7.2** `run-evals`, one run per configuration. Proxy executors were general-purpose subagents. `with_skill` read the skill file and followed `architect.md`. `without_skill` got the command and the harness sheet only, and ran inside the plugin repo, so it could see the dev-team agents' descriptions. Graders followed skill-creator's `grader.md`. No blind comparison (baseline `none`).
- **7.3** The `two-packages` fixture was copied into the scratchpad, git-initialised on branch `adopt` with one commit, with a committed `.claude/settings.json` disabling the installed dev-team. Then: `claude --plugin-dir <worktree>/dev-team --model sonnet --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Agent Skill" -p "/dev-team:map-repo"`, stream-json captured. Cost $1.34, 253 s.

## Results

| Row | Case | Expected | Observed | Pass |
|---|---|---|---|---|
| 7.1 | sweep before the three-file edits | FAIL on all three `names_listed` claims, `map-repo` unlisted | 26/29: all three FAIL with `not listed …: map-repo; listed but no such directory: map-project` | yes |
| 7.1 | sweep after | all PASS | 29/29 | yes |
| 7.2 | eval 1 two packages, `with_skill` | every expectation | 11/11 (hand-checked: `Scope: package (map-repo phase 2)` ×2, both surface rows, the `analysis/report` backlog line, `Next: /dev-team:run-package data`) | yes |
| 7.2 | eval 1, `without_skill` | — | 9/11: no `Result:` line and no next command. Spawn block `Scope: package`, not the phase-2 field; the grader passed this, **regraded to FAIL by hand** | — |
| 7.2 | eval 2 monolith, `with_skill` | every expectation | 7/7: one open `D1` proposing package `app` owning `ingest`, `clean`, `report`, `cli.py`, `settings.py`; `Result: stopped`; only `decisions.md` and `interview.md` written | yes |
| 7.2 | eval 2, `without_skill` | — | 0/7: wrote a full `architecture.md` naming `app`, no stub, `Result: done` | — |
| 7.3 | real run, two packages | `Result:` and `docs/architecture.md` | `Result: done`. Two `dev-team:architect` spawns, `is_backgrounded: false`, in one turn. Commits `1e6c8a5 plan analysis`, `0e0b000 plan data`, then `08f5379 plan repo`, each with `Dev-Team-Run: map-repo`. Clean tree | yes |

## Verdict

All three rows hold.

**Expectation corrected** (run-evals step 7): the grader called eval 2's expectation 7 weak. It passed the baseline, which wrote an architecture map naming `app` as the package, because the map was not titled "Packages". Expectation 7 now requires that every file under `outputs/` is `docs/decisions.md` or `interview.md`. Both eval-2 runs were regraded by hand against the new wording: `with_skill` still passes, and the baseline's verdict on that expectation goes from pass to fail. No executor was rerun.

**Grader error:** eval 1's baseline expectation 8 was passed on a quoted `Scope: package`. It is corrected to FAIL.

**Watch:**

- In 7.3, five of the seven backlog lines were plugin-convention findings, not defects of the mapped code: no `configs.py`, an eager `__init__`, no `mkdocs.yml`, no import-linter, no `tests/`.
- The eval-1 `with_skill` proxy filed a `repo:` backlog line, which is not the `<pkg>/<section>` form.
- The eval-2 grader noted that one stub satisfies "taken together" trivially. The fixture's README says "One package", so a one-package proposal is legitimate.
