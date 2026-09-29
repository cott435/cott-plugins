# The SCAFFOLD step, and a short amendment after a gate retry

**Tested against:** uncommitted, see the working-tree diff on branch `lint-at-plan` (on `61d1e58`, which holds the amendment change): `skills/status/scripts/status.py`, `agents/implementer.md`, `skills/run-package/SKILL.md`, `skills/workspace-scaffold/SKILL.md`, `skills/status/SKILL.md`, README, site pages · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/fixtures/state-cases` (58 cases, 5 new), `evals/fixtures/hook-events` (67 cases, 1 new, 2 changed) · **Baseline:** dev-team 2.0.0 (`1d0fc6d`) · **Pass rate:** 58/58 and 67/67

## What was tested

1. **The retry amendment** (`61d1e58`). After the stop gate sends an implementer back, it now hands back a short amendment (`Result:`, `Amends:`, `Gate:`, `Fixed:`, the amended `Commit:`), not its whole report again. run-package takes an agent's last hand-back as its return.
2. **The SCAFFOLD step.** When `status.py --scaffold <pkg>` says the workspace is missing, run-package's first spawn is an implementer in scaffold mode. It builds:
   - the root `pyproject.toml` with the plugin's lint block (when the repo has none);
   - the package skeleton;
   - `mkdocs.yml` and `.gitignore`;
   - `uv sync`, then the empty workspace's checks, then one commit including `uv.lock`.

   So every tester writes and runs its intent tests inside the workspace, under the repo's own lint rules. The first section's implementer no longer scaffolds.

## Why not write the lint config at plan-repo (option 2, abandoned)

Tried first. A root `pyproject.toml` holding only the lint block makes `uv run pytest` treat the repo as a project. The quant testers ran exactly that command before any workspace existed, and it wrote an untracked `uv.lock` and `.venv/` into the repo. Neither `[tool.uv] managed = false` nor `--no-sync` prevented both. With no root file at all, `uv run` writes nothing. So the config can come early only as part of a real workspace, whose `uv.lock` is committed and whose `.venv/` is ignored. That is the SCAFFOLD step.

## Method

- **State cases:**
  - `scaffold-no-root`: exit 1, `no root pyproject.toml`.
  - `scaffold-no-package`: a uv workspace root and no package pyproject → exit 1.
  - `scaffold-done`: exit 0.
  - `scaffold-adopted`: a root that is not a uv workspace needs nothing.
  - `scaffold-in-report`: the package block shows `scaffold: needed` before `shipped:`.
- **Hook cases:**
  - `gate-scaffold`: a scaffold-only commit carrying the trailer and touching `src/data/__init__.py` (inside `surface`'s path, before its design exists). The gate finds no section and exits 0, writing no record.
  - `gate-fail-attempt-1/2`: assert the amendment wording.
- **The recipe, built by hand in a scratch repo:** exactly as scaffold mode's steps 2–3 say (the §1 root with the lint block merged, contract 1 and contract 3 with every section wrapped, the §2 package, §4 mkdocs, `.gitignore`). Then step 4's checks offline: `uv sync --all-packages`, `ruff check`, `ruff format --check`, `lint-imports` (2 kept, 0 broken), `mkdocs build --strict`. All exit 0.
- **A tester's command inside the scaffold:** a red intent test run with `cd packages/data && uv run pytest tests/intent/<s>` and with `uv run --package data pytest …`. Both ran (1 failed, as intended), and `git status` showed only the new test file. That run found one gap: `mkdocs build` writes `site/`, so it is now in the scaffold's `.gitignore` list.
- **Contracts:** dev-team 36/36. The site rebuilt.
- **Not run:** a behavioral implementer run in scaffold mode, and a behavioral run of the amendment. The next real `run-package`, audited with `/plugin-dev:audit-run`, is their test.

## Results

| Case | 2.0.0 | Now |
|---|---|---|
| state-cases | 53/53 | 58/58 (5 new) |
| hook-events | 66/66 | 67/67 (1 new, 2 changed) |
| option 2, lint-only root + tester `uv run pytest` | — | untracked `uv.lock` + `.venv/` → abandoned |
| scaffold recipe: sync, ruff, format, lint-imports, mkdocs strict | — | all exit 0 |
| tester run inside the scaffold | improvised runners (quant: half fell back to `/opt/anaconda3/bin/python -m pytest`) | the Toolchain command works; tree clean but for the test file |

## Verdict

The mechanics hold: the scaffold check, the gate's pass-through, the recipe's checks, and a clean tree after a tester runs. The agent-side behavior (scaffold mode, and the amendment after a retry) is prose, not yet proven by a run.

This is a minor change: a new step and a new implementer mode, with no path any existing file reads changed. A repo already built under 2.0.0 already has its workspace, so `--scaffold` says `done` and nothing changes for it.
