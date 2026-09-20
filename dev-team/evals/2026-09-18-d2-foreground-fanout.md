# Foreground fan-out (0.5 eval D, follow-up) — does a forked architect finish `plan-package` headless

**Tested against:** `9fc74a3` for `dev-team/agents/architect.md`, `dev-team/agents/curator.md`
and the 12 forked skills. The change under test is uncommitted: see the working-tree diff on
`dev-team-0.5-overhaul`, which sits on top of the rest of the uncommitted phase-2 work · model:
`claude-sonnet-5` (every agent is `model: inherit`) · Claude Code 2.1.270 · 2026-09-18

## What was tested

Eval D ([2026-09-18-d-commit-per-run.md](2026-09-18-d-commit-per-run.md)) found that headless
`/dev-team:plan-package data` never finishes. The forked architect started its designers in
the background and ended on `echo waiting`. The completion notifications went to the main
conversation, not the fork, and the main thread then did its own unification: no
`surface.md`, no commit. The claim tested here: once every `Agent` call from a fork passes
`run_in_background: false`, and the calls still go out in one message, the fork gets all its
designers back in the same turn and writes `integration.md`, `surface.md` and the commit
itself. The designers still run in parallel.

## Method

Real headless runs on the `two-package` fixture (`reset.sh --no-constraints`, in a scratch
directory), each started from the fixture directory:

```
claude -p "/dev-team:plan-repo" --plugin-dir <dev-team> --permission-mode bypassPermissions --output-format stream-json --verbose
claude -p "/dev-team:plan-package data" --plugin-dir <dev-team> ...
```

`plan-repo` ran once (commit `e85650d`). Each `plan-package` run was preceded by
`git reset --hard e85650d`. The `Agent` inputs, agent types and timestamps come from the
session transcripts under `~/.claude/projects/<fixture>/<session>/subagents/`: each
subagent's `.meta.json` gives its `agentType`. Tool inputs made inside a fork do not appear in
the `stream-json` output. Cost: about $4.60 across the four runs.

The fix has two parts:

1. **The flag.** The architect and the curator each get a Hard rule: every `Agent` call
   passes `run_in_background: false`, and one batch goes in one message. The spawn sites
   (Delegating, Probing, curator Extract step 2) point to that rule. The old "continuing
   after backgrounded designers" paragraph is replaced, because a fork never receives those
   notifications.
2. **The agent prefix.** Found during this eval, below. All 12 forked skills change from
   `agent: <name>` to `agent: dev-team:<name>`.

## Results

| Run | Tree | Fork `agentType` | Designer calls | Designers overlap | Fork wrote | Commit | Main-thread tool calls | Pass |
|---|---|---|---|---|---|---|---|---|
| `plan-repo` | flag only | `general-purpose` | — (1 researcher, `run_in_background: false`) | n/a | `architecture.md`, `sources/trades.md` | `e85650d` | 0 | ✅, but see note |
| `plan-package` 1 | flag only | `general-purpose` | 3, one per message, **no flag** → "Async agent launched" | yes (19:33:06–19:35:31) | `contract.md` only, then ended: "running in the background. I'll wait…" | none | unification done in the main thread (`integration.md`), no `surface.md` | ❌ (reproduces eval D) |
| `plan-package` 2 | flag + prefix on `plan-package` only (scratch copy) | `dev-team:architect` | 3 in **one message**, all `false` | yes (19:39:07–19:41:15) | contract, 3 designs, `integration.md`, `surface.md` | `7a6945f` | 0 | ✅ |
| `plan-package` 3 | flag + prefix on all 12 skills (the real tree) | `dev-team:architect` | 3 in **one message**, all `false` | yes (19:45:02–19:47:48) | contract, 3 designs, `decisions.md`, `integration.md`, `surface.md` | `f5c7393` with `Dev-Team-Run: plan-package data` | 0 | ✅ |

**The root cause was not the flag.** In runs 1 and `plan-repo`, the fork's `agentType` was
`general-purpose`. A bare `agent: architect` in skill frontmatter does not resolve to the
plugin's agent and gives no error: the fork runs as general-purpose, without the architect's
prompt. `plan-repo` passed only because the fork went and `Read` `agents/architect.md` itself,
after the skill body kept citing "your **Probing** section". Run 1 never read it. So the new
Hard rule was invisible, and the only guidance on the flag the fork saw was the harness's
default, which says to use `false` only when the next action depends on the result. This matches
eval A3 (`subagent_type`: only `dev-team:<agent>` resolves), except that the bare name falls back
silently here instead of erroring.

Run 2 changed only the one frontmatter line, and it gave the full fix. The fork ran as the
architect, which follows its Hard rules, so both parts are needed: the prefix loads the
prompt, and the prompt carries the flag.

## Verdict

Holds after the fix. The designers still run in parallel: three calls in one message, with
overlapping lifetimes of about 1–2.5 min each, and the architect's turn resumes once the slowest
returns. The fork writes everything and commits, and the main thread makes no tool calls at all.

Consequences recorded elsewhere:

- `contracts.yml` gains two claims: `every forked skill names its agent with the plugin
  prefix` and `no forked run waits on a background notification`. Each was planted with one
  violation and reported `FAIL` at the planted line before being restored. 13/13 pass.
- Every forked agent (implementer, reviewer, curator, documenter, researcher via
  `probe-source`) had been running as general-purpose. That likely explains eval D's
  first-run finding that the architect never committed. The per-skill "commit then return"
  steps added in response may now duplicate the agents' own **Commit** sections; worth a look
  in a later phase.
- With the prompt loaded, `memory: project` takes effect too: the fixture gains
  `.claude/agent-memory/dev-team-{architect,designer}/` after a run. Expected, but it is new
  untracked output in any repo the plugin runs in.
- Not re-run here: `plan-change` (two waves), `extract-legacy` (curator fan-out), `map-project`,
  `sync-plan`. They get the same two fixes but no behavioral run in this eval.
