# audit-run — finding a chat by its title, and auditing a forked chat

**Tested against:** uncommitted, see the working-tree diff on branch `audit-run-titles` (off `10ed049`): `skills/audit-run/scripts/trace.py`, `skills/audit-run/SKILL.md`, `evals/fixtures/audit-run/make_session.py` · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/sets/audit-run.json` evals 1, 3, 4 · **Iteration:** none, run by hand · **Baseline:** `10ed049` for eval 4 (negative) · **Pass rate:** 13/13 vs baseline failing eval 4

## What was tested

- **Finding the chat.** A user who knows a chat only by its sidebar title can pick the right session.
- **Forks.** A forked or resumed chat is named as one, and its trace still finds the agents spawned before the fork.
- **Versions.** The version of the plugin is recorded per segment and per unit.

## Method

- **The problem, found by the user.** `find` printed only session ids, and the app shows none. On the real quant project it also:
  - counted quoted commands as typed (this chat appeared as a `run-package` session);
  - double-counted agents;
  - showed three chats titled "Project architecture migration" with nothing telling them apart.
- **What the real sessions showed.** One of those three, `5976c083`, is a fork of `1493ed56`: it holds 788 of the same record ids, identical timestamps up to 09-29 06:59, and only 5 of its 110 agent transcripts. The other 105 stay under `1493ed56/subagents/`. A trace of the fork on `10ed049` would have missed them.
- **Where the title comes from.** `customTitle` (a name set by hand or by the app) or `aiTitle` records in the session file.
- **The fixture** gains a title on the planted session, and a fork of it with no subagents directory.
- **The checks.** Eval 1 and eval 3 were re-run to confirm the planted-defect trace and the Flow section are unchanged. Eval 4 has six new checks. Against `10ed049`'s `trace.py` the eval-4 checks fail: `find` has no title, no `--all` and no projects override, so the checker stops at 4.2.
- **Real run.** `find --plugin dev-team` lists, by title:
  - the three quant chats: the fork is marked, the 14-minute false start is visible from its span, and the counts are 110, 105 and 0 agents;
  - "Summarization language model spec" twice, as a 13-hour run and a 31-minute `shape-brief`.

  `build 5976c083` traces 110 units across 2 segments, all on dev-team 1.0.0, 105 of them found under `1493ed56`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 1.1–1.6 | planted-defect trace unchanged | unchanged | ✅ ×6 |
| 3 | Flow section and flow.html for the flow fixture | present, same content | ✅ |
| 4.1 | both planted sessions listed as "Ship the toy file" | yes | ✅ |
| 4.2 | fork marked `fork of 0a0d17f0` | yes; the original unmarked | ✅ |
| 4.3 | ambiguous title builds nothing, lists matches | exit 1, "2 toy chats match", no index.json | ✅ |
| 4.4 | fork trace finds U01 under the original | 1 unit, `a0fixture00000001`, 2 segments | ✅ |
| 4.5 | per-segment version | 0.1.0 on both | ✅ |
| 4.6 | headless sessions hidden without `--all` | hidden | ✅ |
| Real | fork of 1493ed56 traced whole | 110 units (105 borrowed) | ✅ |

## Verdict

Holds. Not covered:
- a real run that spans two plugin versions. None exists on this machine, so the per-version split is tested only with one version.
- the AskUserQuestion labels, which are skill prose and have had no behavioral run.
