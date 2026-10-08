# 0.16-audit-ledger phase 9: the bundle's checks (M9.1), audit-run's mechanical evals (M9.2), and what loads (L9.1)

**Tested against:** uncommitted, see the working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `fe86085`): `README.md`, `site/workflows/audit-a-run.md`, `site/flow.md`, `CHANGELOG.md`. Scripts unchanged since `fe86085`. Model: none for M9.1 and M9.2 (scripts, checked by hand against each expectation); L9.1 ran `claude -p` on the CLI's default model · 2026-10-07
**Set:** M9.1 and L9.1 have no set (rows of `site/notes/0.16-audit-ledger-09-release.md` **Evals**); M9.2 is `evals/sets/audit-run.json` evals 1, 3, 4 · **Iteration:** none. Run in the phase chat, with the fixture in a scratchpad `mktemp -d` · **Baseline:** none · **Pass rate:** M9.1 4/4 · M9.2 18/18 · L9.1 1/1

## What was tested

- **M9.1:** the bundle as phase 9 leaves it still holds its own claims and builds its sites. That means `check-contracts` passes in plugin-dev and dev-team, `build-site` warns about nothing in either, and every committed set validates.
- **M9.2:** the moved `trace.py` still reproduces the planted fixture, the flow chart and title and fork resolution.
- **L9.1:** the plugin loads from its working copy with both agents and the model-invocable `run-flow`.

## Method

- **M9.1:**
  - `python3 scripts/contract_sweep.py` in `plugin-dev/`, and `python3 ../plugin-dev/scripts/contract_sweep.py` in `dev-team/`.
  - `python3 scripts/build_site.py` in both.
  - `eval_workspace.py validate` on each of the 18 files under `evals/sets/`.
- **M9.2:** I ran `make_session.py $TMP`, then each eval's commands as written, then checked each expectation against the output files with grep or `json`. One correction to how I ran eval 4: the title words had to be passed as one shell argument (`build 'toy file'`), as the prompt quotes them.
- **L9.1:** `claude --plugin-dir ./plugin-dev -p "List the skills and agents you have from plugin-dev"`, run from the repo root.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M9.1a | check-contracts all PASS in plugin-dev | 11/11. The first run failed `README's skills table names every skill`, because the new audit-run row backticked `definition`. The backticks were removed and the rerun passed | ✓ |
| M9.1b | check-contracts all PASS in dev-team | 54/54 | ✓ |
| M9.1c | build-site warns about nothing in either | plugin-dev 57 pages and dev-team 118 pages, no warning. dev-team's site has no page from `audits/` | ✓ |
| M9.1d | every set validates | all 18 exit 0 | ✓ |
| M9.2 eval 1 (6) | index.json root, version, segment and U01 spawned at D3; scratch.md written; pytest ERROR `1 failed, 3 passed`; `COMMIT UNCONFIRMED` and commits `['?abc1234']`; return begins `Done.`; driver Write of out/extra.txt at D5 | all six, as expected | 6/6 |
| M9.2 eval 3 (6) | four waves W1 `∥ 2`, W2–W4 `→`; U03 `[request changes, 1 crit]` and U05 `[approve]`; ask between W2 and W3 `Fix a/x or defer? → Fix it`; lane table a/x 4 runs, 2 rounds, a/y 1 run; flow.html lane headers, `∥ 2`, `✗ changes`, `1C 2W`, `✓ approve`, `Fix it`; U03 alone under Reviews that found issues | all six, as expected | 6/6 |
| M9.2 eval 4 (6) | find --all shows both "Ship the toy file" sessions; fork marked `fork of 0a0d17f0`; `build 'toy file'` exits 1 with `2 toy chats match` and no index.json; fork build has U01 `a0fixture00000001` and two segments; segments at 0.1.0; find without --all hides both | all six (without --all: `no session … used toy`, exit 1) | 6/6 |
| L9.1 | the reply names `run-flow`, `run-narrator` and `run-auditor` | skills table lists `plugin-dev:run-flow` (with `--agent` and `--explain`); agents table lists `plugin-dev:run-auditor` and `plugin-dev:run-narrator`. Typed skills (audit-run, fix-issues and others) are not listed, as expected | ✓ |

## Verdict

Held. M9.1 4/4, M9.2 18/18 and L9.1 names all three. The README and the workflow page now describe the final bundle, and no file under `skills/`, `agents/`, `README.md` or `site/workflows/` names `skills/audit-run/scripts/` or a workspace `report.md`.
