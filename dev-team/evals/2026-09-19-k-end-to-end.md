# K — the whole new-repo workflow on the two-package fixture, under 0.5

**Tested against:** `9d1c048`, the phase-8 commit, plus uncommitted phase-9 edits to
`README.md`, `site/`, `CHANGELOG.md` and the two descriptions. None of those files is an
agent or skill a run loads · model: `claude-sonnet-5` (`--model claude-sonnet-5` on every
headless run; every agent on `inherit`; each run's `modelUsage` shows only
`claude-sonnet-5`). `claude-opus-5` ran the checks · Claude Code `2.1.270` · 2026-09-19

## What was tested

Note 09 §K: from `reset.sh` (with `docs/constraints.md`), the command sequence the note lists
builds both packages. It ends with both `shipped`, every section reviewed `approve`/`approve
with fixes`, the plan reviewed, zero open review follow-ups, zero `TODO(decision` markers,
tests, `lint-imports`, `mkdocs build --strict` and every Enforced constraint passing, one
commit per run with a trailer, and an **As shipped** section in every design.

## Method

Real headless runs, one per command: `claude -p "<command>" --plugin-dir <abs>/dev-team
--model claude-sonnet-5 --output-format stream-json --verbose --permission-mode
bypassPermissions`. Each ran on the same `reset.sh` copy (branch `build`, `git config
user.name/email` set in the copy). The note says "typed by hand in one session"; each command
here is its own session, as in eval J. The streams are the source for spawns, agent types and
tokens. Commits come from git.

| Run | Command | Cost | Result |
|---|---|---|---|
| 1 | `/dev-team:plan-repo` | $0.82 | `f7ca741`; dataset probed, 0 decisions |
| 2 | `/dev-team:plan-package data` | $0.70 | spine run, `ingest` (2 of 2), `c221841` |
| 3 | `/dev-team:run-package data` | $8.38 | 11 spawns, 7 commits: `ingest` built with 1 review round-trip, plan completed, plan `approve`, stop |
| — | (answer decisions) | — | none open; nothing answered |
| 4 | `/dev-team:run-package data` | $10.30 | 12 spawns, 9 commits: `clean`, `storage`, finalize, package review, sync-design; `done`, `next: /dev-team:plan-package analysis` |
| 5 | `/dev-team:plan-package analysis` | $1.36 | full run (2 sections), `surface.md`, D1 raised, `11ed554` |
| 6 | `/dev-team:review-plan analysis` | $0.49 | `request changes`, 1 CRITICAL (an OQ with no `D<n>`), 1 `analysis/plan` follow-up |
| — | answer D1 | — | `Decision: 20`, `Status: decided`, left uncommitted as a hand edit |
| 7 | `/dev-team:plan-package analysis` | $0.35 | re-plan: `integration.md` only, follow-up ticked, `e17554d` |
| 8 | `/dev-team:review-plan analysis` | $0.43 | `approve`, `743652d` |
| 9 | `/dev-team:run-package analysis` | $12.02 | 11 spawns, 9 commits; `done`, `next: /dev-team:finalize-project` |
| 10 | `/dev-team:finalize-project` | $0.58 | 3 READMEs + `docs/index.md`, `16b0f30`; both open gaps under Known gaps |
| 11 | `/dev-team:status` | $0.07 | the table below |

Total $35.50. Runs 6–8 are outside the note's list. The list has one `review-plan analysis`,
and the workflow's answer to `request changes` is `plan-package` then `review-plan` again.
Afterwards, from the repo root: `status.py <pkg> --gate` for each package, `uv run pytest`,
`uv run lint-imports`, `uv run mkdocs build --strict`, a `TODO(decision` grep, an `As shipped`
count per design, and a trailer check on every commit since the fixture's. Then
`uv sync --all-packages` and `data-ingest` twice into a fresh SQLite file, followed by
`analysis-report`.

## Results

| Check | Expected | Observed | Pass |
|---|---|---|---|
| both packages `shipped` | ✓ | `data` and `analysis` both `shipped`, `interface.md` ✓ | ✅ |
| every section reviewed | `✓` with approve / approve with fixes | 5/5 `✓`: `ingest` approve with fixes, the other four approve | ✅ |
| plan line | `plan: reviewed … approve` | **`plan: stale (last review … approve @…)`** for both: `sync-design` edits `design/*.md` after the plan review | ❌ |
| zero open review follow-ups | 0 | **1**: `analysis/surface`, a CRITICAL in a package review whose verdict was `approve with fixes` | ❌ |
| zero `TODO(decision` markers | 0 | 0 in code (3 grep hits are README prose saying there are none) | ✅ |
| `uv run pytest` | passes | **16 collection errors at the root**: both packages ship a `tests` package, so `tests.integration.*` collides. `pytest packages/data` 109 passed, `pytest packages/analysis` 54 passed, and all 163 pass with `--import-mode=importlib` | ❌ at root, ✅ per package |
| `lint-imports` | passes | 5 kept, 0 broken | ✅ |
| `mkdocs build --strict` | passes | exit 0 | ✅ |
| Enforced constraints | pass | `--gate` PASS for both, `8 enforced, 0 failing` | ✅ |
| one commit per run, trailers | every commit has `Dev-Team-Run:` | 32 commits, all with the trailer | ✅ |
| As shipped | in every design | 5/5 designs | ✅ |
| 398 rows stored | 398 | `parsed 400`, `stored 398`; a second run `stored 0`; report renders 3 symbols | ✅ |
| driver stops | spine: stop for decisions; full: `done` with the right `next` | runs 3, 4, 9 exactly that | ✅ |
| every spawn is a plugin agent | `dev-team:<agent>` | **run 5's two designers ran as `general-purpose`**; runs 2 and 3 resolved `dev-team:designer` | ❌ |

Every stop and intervention: run 3 stopped for decisions (none open). Run 6 stopped on a plan
CRITICAL, answered by runs 7–8. D1 was answered by hand before run 7, and run 7's architect
committed that hand edit with its own files. `uv sync --all-packages` was run before the CLI
check: the venv predates the `[project.scripts]` entries, so `data-ingest` was not installed.
No file was edited to get a run through.

Behavior that is wrong but did not fail a listed check:

- **A CRITICAL under `approve with fixes`.** `agents/reviewer.md` lists the three verdicts,
  but no rule says a CRITICAL means `request changes`. The `analysis` package review filed
  one CRITICAL, a test importing `data.storage.store`, and still approved. `run-package` and
  the finalize gate both read the verdict, so nothing re-finalized.
- **Bare `designer` in `agents/architect.md`.** "Spawn one `designer` per section" never
  names `dev-team:designer`. The fork chose the plugin agent in 2 of 3 batches and
  `general-purpose` in run 5. The general-purpose designs then drew the plan CRITICAL in run 6.
- **The tester's tree trips Guarded rows** (seen in phase 8). 12 of `ingest`'s 15 first-review
  CRITICALs are suppressions in `tests/intent/`, which the implementer may not edit. It filed
  them as a non-review follow-up and the second review approved. That follow-up stays open
  and nothing picks it up.
- **The implementer ran `find /`** for `workspace-scaffold/SKILL.md` after reading it through
  `${CLAUDE_PLUGIN_ROOT}`. It listed copies across the home directory. Nothing outside the
  plugin was read.
- `.claude/agent-memory/` stays untracked after every run (seen in phase 7, exempt from
  the gates).

## Verdict

Partial. The workflow runs end to end on its own: 11 commands, a correct stop for decisions
and a correct stop for a plan CRITICAL, both packages shipped, 398 rows stored idempotently,
every commit with its trailer, every design synced. Four listed checks fail, each a plugin
defect, and none is fixed in this phase:

1. `status.py` reads the plan as stale once `sync-design` runs. Its plan-freshness rule
   should ignore `design/*.md` edits made by `sync-design` commits, or read only the files a
   plan review covers.
2. The reviewer needs "any CRITICAL → `request changes`" (or `approve with fixes` must mean
   no CRITICAL). Once that holds, the driver's second finalize would have run.
3. `workspace-scaffold` must keep two packages' `tests/` from colliding at the root:
   `--import-mode=importlib` in the root pytest config, or no `tests/__init__.py`.
4. `agents/architect.md` must name `dev-team:designer` and `dev-team:researcher` in its
   spawn instructions, and `contracts.yml` should forbid the bare names there, as it does for
   the driver.

Eval L's numbers come from these runs.
