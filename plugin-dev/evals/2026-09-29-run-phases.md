# `run-phases` — a plan's phases in series from one chat; skill-creator in a cloud session

**Tested against:** uncommitted — see working-tree diff (on `ba2ba38`): `skills/run-phases/SKILL.md` (new), `skills/run-evals/scripts/eval_workspace.py`, `skills/run-evals/references/skill-creator.md`, `skills/plugin-anatomy/references/agents.md`, `edge-cases.md` · executors and graders Claude Opus 5.5 (`model: "opus"`); the headless phase sessions ran Claude Code 2.1.285 on the session default (`claude-sonnet-5-5`) · 2026-09-29
**Set:** `evals/sets/run-phases.json` eval 1 · **Iteration:** `evals/workspace/run-phases/iteration-2` (iteration 1 stopped, below) · **Baseline:** none · **Pass rate:** 100% (8/8) vs 38% (3/8) · graded with skill-creator's `agents/grader.md`, benchmark and static viewer from the cloud session's synced copy, found by `locate-skill-creator` with no override

## What was tested

- That `run-phases`, typed as `/plugin-dev:run-phases 0.2` on a two-phase toy plan, keeps phase work out of the main chat. It runs one fresh agent per phase, in series. It brings phase 1's review stop back to the user and resumes the same agent with the reply. It checks each commit before starting the next phase, and stops once the plan is done.
- The platform facts that shape it.
- That `locate-skill-creator` finds skill-creator in a Claude Code cloud session.

## Method

**Platform facts:** real `claude -p` runs in the session scratchpad, Claude Code 2.1.285, as root.
- **Nested Agent:** a subagent asked to list its tools and spawn one more.
  - A cloud session sets `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` (from `env`).
  - This session's own general-purpose subagent had no `Agent` tool (iteration 1's executor), and nor did a subagent inside a `claude -p` child.
  - With `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=3` on the child, the nested spawn replied `HAS-AGENT NESTED-OK`.
- **Session ids:** `claude -p` children report the parent's session id `9463f5ee…` (`CLAUDE_CODE_SESSION_ID` is inherited). A fresh child still starts empty: asked for an earlier codeword, it answers `NONE`.
- **Resume:** with `--session-id A` and `--session-id B` given explicitly, `--resume A` answered `ALPHA-7`, A's codeword and not B's.

**Behavioral:** `run-evals` on eval 1.
- **Harness:** a temp copy of `evals/fixtures/toy-plugin/` with a second, mechanical-only phase (`wave`) added (`evals/sets/files/run-phases/two-phases.md`). Review answered "approve".
- **Iteration 1** used the first design (subagents only). Its with-skill executor stopped before phase 1, correctly by the skill's "if an agent cannot be started, stop" rule: it had no `Agent` tool. The baseline was stopped. That result produced the headless mode and the facts above.
- **Iteration 2**, with the headless mode and expectations 1 and 3 made mode-neutral: one executor per configuration and one grader per run, all on Opus.

**Locator:** `env -u SKILL_CREATOR_DIR python3 skills/run-evals/scripts/eval_workspace.py locate-skill-creator`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| locator | a path, no override | `/root/.claude/skills/synced/<org>_<id>/skill-creator`, exit 0. Before the change: `skill-creator not found`, exit 1 | ✓ |
| nesting | subagents nest in a cloud session? | no at the default depth 1; yes with the variable raised | fact |
| session ids | children separable | only with an explicit `--session-id`; `--resume` then continues the right one | fact |
| eval 1, with skill | every expectation | 8/8 | ✓ |
| eval 1, baseline | fails the orchestration lines | 3/8. It did both phases inline, with no phase agent, and composed the review itself | ✓ |

**Eval 1 with skill, in detail:**
- Headless mode chosen (depth `1`).
- Phase 1 ran in session `dd410d05` and returned `Status: review`. Its For the user block was relayed in full to `interview.md`, and `git-log-at-review-1.txt` shows only `fixture`.
- The session was resumed with `--resume` and the reply. It committed `e35c6a6 toy 0.2 (phase 1): farewell`, and `evals/workspace/farewell/` holds one iteration.
- The main chat checked summary, tree and ledger row, then started phase 2's own session: `82caa8e toy 0.2 (phase 2): wave`, with the phase-1 SHA resolved in the ledger.
- No push or tag command appears anywhere.
- The grader confirmed the order from timestamps: review file 22:19:15, resume 22:19:29, phase-1 commit 22:19:35, phase 2 start 22:20:11.

## Expectations corrected (run-evals step 7)

- **Before iteration 2:** expectations 1 and 3 now accept either mode, a subagent or a headless session.
- **After grading:**
  - **2** now requires the review to be relayed from a phase agent's `review` return: the inline baseline passed the old wording.
  - **7** checks for `git push` and `git tag` commands: the temp copy has no remote, so "nothing pushed" could not fail.
  - The with-skill verdicts are unchanged, checked against its `interview.md` and session streams. The baseline was regraded, from 4/8 to 3/8.
- **Left as is:** expectations 4 and 8 are outcome checks an inline run also passes. The orchestration is carried by 1, 2, 3, 5 and 6.

## Noticed, not fixed here

- The phase agent resolved `(phase 1)` in the ledger but not in the toy's `evals/README.md` row. `run-phase` resolves only the ledger's Commit cells.
- Inside a cloud session a headless child inherits the parent's commit-attribution instructions, so its commits carry this session's `Claude-Session` URL. That comes from the environment, not from the skill.
- The subagent mode is not exercised by this eval here, since the cloud depth forces headless mode. Its parts are the `run-phase` file read by path, as `run-phase`'s own evals do, and SendMessage, which this session used throughout.

## Verdict

Holds. `run-phases` drives a two-phase plan from one chat: fresh agents in series, the review relayed and resumed, each commit checked, nothing done inline. The first design did not survive a cloud session, and the eval caught it: the skill now picks headless sessions when subagents cannot spawn. `plugin-anatomy` records the depth variable and the session-id rule as `[proven]` against this log.
