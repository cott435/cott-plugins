# remake phase 11 — the bundle: removed skills deleted, contracts final, README and site rewritten; the end-to-end build

**Tested against:** uncommitted — see working-tree diff (on `31dbc61`) · model: `claude-opus-5-5` (the phase, 11.1–11.2); `claude-sonnet-5` for 11.3, every 11.4 headless session and both graders · Claude Code `2.1.270` · 2026-09-27 to 2026-09-28
**Set:** `evals/sets/run-package.json` eval 4 (11.4); 11.1–11.3 are the note's mechanical and load rows · **Iteration:** `evals/workspace/run-package/iteration-4` (stopped) · `evals/workspace/run-package/iteration-5` · **Baseline:** `previous` = `af08482` (0.6.0's `skills/run-package/`) · **Pass rate:** with_skill 55.6% (5/9) vs old_skill 22.2% (2/9)

## What was tested

- **11.1** — with the eight skills deleted and `contracts.yml` final, every claim passes and every `files:`, `owner:` and reader path exists.
- **11.2** — the two `names_listed` claims pass after the deletions, and a stray `test-section` line in `site/site.yml` fails.
- **11.3** — the bundle loads from the working tree: eight agents, the knowledge skills, no removed skill.
- **11.4** — the whole two-package build, run headless by the six typed commands: both packages shipped, 398 rows stored and a second run storing nothing, every section approved with a round-1 pair, one trailered commit per agent run, a backlog with no review lines, the fixed cost per role, and `/dev-team:finalize-project` as the last `next:`.

## Method

- **11.1** — `contract_sweep.py`; a `python3` pass over `contracts.yml` globbing every `files:`, `owner:`, `file:` and reader path.
- **11.2** — a `  - test-section` line inserted before `status` in `workflow_skills_order`, the sweep run, the line removed, the sweep run again.
- **11.3** — `claude -p "List every skill and every agent you have from the dev-team plugin …" --plugin-dir ./dev-team --model sonnet` from a scratch directory whose `.claude/settings.json` disables the installed `dev-team@cott-plugins`. `/agents` is interactive and was not run. $0.07.
- **11.4** — real headless sessions, as phase 8 ran them, because in this session `dev-team:<agent>` resolves to the installed 0.6. A scratch-pad runner (`step.sh`, `chain*.sh`, `tail*.sh`; streams derived by `post.py` and `commits.py`; none committed) ran each command from a fresh `reset.sh` copy of `evals/fixtures/two-package/`: `claude -p "<command>" --plugin-dir <copy> --model sonnet --output-format stream-json --verbose --permission-mode bypassPermissions --disallowedTools AskUserQuestion`. A git-excluded settings file disabled the installed plugin. with_skill used the working tree copied without `evals/`. old_skill used the same copy with `skills/run-package/` from `af08482`. Both graders ran on `claude-sonnet-5`, using skill-creator's `grader.md`.
  - **Iteration 4** stopped in `run-package data` at `data/clean DESIGN`, after 43 minutes and $9.86 (with_skill; the baseline ran all six commands, $4.14). Fix 1 followed (below), and the build was rerun from scratch as iteration 5. The baseline's outputs were carried over, because its driver is the 0.6 file and no fix touches it.
  - **Iteration 5**: steps 1–4 ran clean. `run-package analysis` stopped four times: 5 (the platform refusal), 5b (the hyphenated path), 5c (the tester no-op) and 5d (the path cycle). Between them came two typed change requests (4b, 4c), fixes 2 and 3, and one user hand edit of the contract's path cell (`b71ff5e`). 5e ran to done; 6 finalized. $38.76 in all, 2 h 30 min of session time.
- **Fixed cost** — per spawn, from each subagent's first `assistant` event (`input + cache_creation + cache_read`), 50 spawns. A same-version control spawned 0.6.0's and the working tree's agents once each, with one trivial prompt, on today's Claude Code (task-completion `total_tokens`). $1.00.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 11.1 | all PASS; every path exists | 36/36; every path matches | ✅ |
| 11.2 | PASS, then the plant FAILs | 36/36; `listed but no such directory: test-section`, 35/36; 36/36 after removal | ✅ |
| 11.3 | eight agents, knowledge skills, no removed skill | `dev-team:architect, curator, designer, documenter, implementer, researcher, reviewer, tester`; nine knowledge skills; no removed name. The workflow skills are typed-only, so the model does not list them | ✅ (headless only) |
| 11.4 | every expectation passes for with_skill | 5/9 vs 2/9 | ❌ |

11.4, per expectation (with_skill · old_skill):

| # | Expectation | with_skill | old_skill |
|---|---|---|---|
| 1 | both packages `shipped: yes`, every section DONE | ✅ `data` 4/4, `analysis` 3/3 (`md-report` for the brief's `report`) | ❌ every section DESIGN |
| 2 | 398 rows, second run stores 0 | ✅ `rows newly stored: 398`, then `0`; `count(*)` 398 both times | ❌ nothing built |
| 3 | every section an approving round, round 1 an `-a`/`-b` pair, no Deferred entry | ✅ seven pairs; `data/ingest` and `data/surface` approved at `-r2-s` | ❌ no reviews |
| 4 | one trailered commit per agent run | ❌ the tester's `dfab49a data/ingest: 13 intent tests from design` has no `Dev-Team-Run:` line, and the same run added a second, untrailered commit `0acd737 … remove __pycache__ accidentally staged` | ✅ |
| 5 | backlog holds no review lines | ✅ `docs/followups.md` absent | ✅ |
| 6 | fixed cost per role; tester below 39,652, reviewer below 38,467 | ❌ tester 41,201, reviewer 43,787 (table below) | ❌ |
| 7 | each `run-package` run ends in the summary block; `analysis`'s `next:` is `/dev-team:finalize-project` | ❌ 5e ends `next: /dev-team:finalize-project`, but stopped runs 5 and 5b–5d put prose after or before the block | ❌ |
| 8 | commands ran in order, each stream has a `result`, prefixed spawns, no `Procedure: open` | ✅ after the expectation's correction (regraded by hand) | ❌ `Procedure: open` in the tester's prompt |
| 9 | the driver writes only `docs/decisions.md` and runs only `status.py`, `git rev-parse`, `git rev-list` | ❌ no Write or Edit, and no git command that writes. But while diagnosing its stops, the driver ran `git log`, `git show`, `git status`, and `cat`/`sed`/`grep`/`find` on the contract | ❌ |

Fixed cost, iteration 5, first assistant turn per spawn:

| role | n | min | max | mean | eval L mean | same-version 0.6.0 | same-version working tree |
|---|---:|---:|---:|---:|---:|---:|---:|
| architect | 3 | 45,055 | 45,244 | 45,176 | 38,411 | 40,046 | 45,023 |
| designer | 9 | 34,898 | 35,198 | 35,006 | 26,055 | 26,157 | 34,772 |
| tester | 10 | 40,964 | 41,598 | 41,201 | 39,652 | 40,715 | 41,097 |
| implementer | 11 | 55,491 | 55,758 | 55,587 | 54,342 | 54,916 | 55,349 |
| reviewer | 16 | 43,588 | 44,047 | 43,787 | 38,467 | 43,094 | 43,416 |
| researcher | 1 | 28,164 | 28,164 | 28,164 | — | — | — |

Observations:

- **Three defects found by the build, fixed in this phase on the user's call** (the note's Deviations have the detail):
  1. An open `spec-change:design` or `:test` entry was never closed, so its section re-opened forever. `status.py` now treats the next design or intent-tree commit as its answer. Three state cases.
  2. Claude Code 2.1.270 refuses a subagent Write of any file matching `/^(REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$/i`. `project-structure` §4 and the package-contract template now forbid such section and source names.
  3. A tester run that found nothing to change left the section at TEST. It now commits a `conftest.py` stamp, `intent tests current with design`, which `status.py` skips like a regeneration. One state case.
  The fixture cases stand at 40/40 and the hook fixtures at 47/47.
- **Re-planning and change files worked end to end.** The rename was an EDIT on a planned section, with the contract archived to `docs/history/`. The path correction was a CHANGE on a built section: `docs/changes/md-report-path.md`, a `delta` design, the stamp, a review, and the close's `sync-plan` marking it synced (`08c03e4`). It exposed a real cycle: a CHANGE to a built section's *path* cannot close. `status.py` reads the README at the canonical path, and `sync-plan` applies the change only at DONE. The driver named it and asked for a human call.
- **The `data` package took 1 h 15 min and $19.79.** Seven reviewers for four sections, two sections needing a round 2, no cap and no defer. `run-package analysis` (5e) took 21 min and $6.57.
- **The driver's summary counts run low.** `run-package data` reported `designer 3 · tester 3 · implementer 5 · reviewer 7`. The stream holds 4, 4, 6 and 10 of those spawns. The counts are kept in the driver's memory, and they drift over a 75-minute walk.
- **Fixed cost.** On the platform eval L ran on, the bar compared across Claude Code versions: 0.6's own reviewer is 4.6k above L's mean today. Against a same-version 0.6.0, the tester (+0.4k), reviewer (+0.3k) and implementer (+0.4k) are flat; the designer (+8.6k) and architect (+5.0k) grew. The design expected the tester and reviewer to fall. They did not.
- **The tester trailer miss** is phase 8's *noticed* line (`agents/tester.md`), seen again. So is the `Co-Authored-By:` paragraph after every trailer, which hides `Dev-Team-Run:` from git's trailer parser.
- **Grader critique acted on.** Expectation 8's "ending in a `result` event" measured a platform bookkeeping line and was rewritten ("carrying a final `result` event"). The with_skill verdict flipped to PASS by hand; the old_skill verdict is unchanged. Expectation 1 was corrected for the naming rule. The graders also noted that expectation 6's bar belongs against a same-version control. That is left for the user, since it changes the bar, not its wording. Expectations 1–3 and 6–7 fail by construction for the 0.6 driver, which stops before any design.
- **Cost.** 11.4 with_skill $9.86 (iteration 4) + $38.76 (iteration 5); old_skill $4.14; control $1.00; graders not counted.

## Verdict

11.1, 11.2 and 11.3 hold (11.3 headless only). **11.4 missed its bar after three fixes**: 5/9 against 2/9. Both packages shipped end to end, idempotent at 398 rows, every section approved with a round-1 pair, and `next:` is `/dev-team:finalize-project`. It missed on:
- the tester's trailer and second commit;
- a fixed-cost bar set on another platform version, with the same-version tester and reviewer flat;
- summary discipline on stopped runs;
- the driver's read-only diagnostic Bash calls.

Commit on the user's yes.
