---
name: run-phases
description: Drive a plan written by plan-phases from the main chat - run one fresh agent (a subagent, or a headless session where subagents cannot delegate) per unfinished phase, in series, each doing run-phase, relay its review stops and questions to the user, check its commit, and go on to the next phase until the plan is done or something needs the user. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), typed by the user.
argument-hint: "[slug] [--through N]"
disable-model-invocation: true
---

# Running a plan's phases in series

`run-phase` does one phase per chat, so every phase starts from the ledger in a clean
context and not from a long conversation. This skill keeps that and removes the typing. Each
phase runs in a fresh agent, and this chat drives them. It reads the ledger, starts the
agent, relays to the user whatever the agent stops for, checks the agent's commit, and
starts the next. It does no phase work itself, so its own context holds only the ledger rows
and what each agent returned.

Platform facts it rests on (`plugin-anatomy`):

- A subagent has no `AskUserQuestion` (`references/agents.md`), so every stop `run-phase`
  makes for the user comes back to this chat, which asks.
- A phase's evals spawn `run-evals` executors, graders and comparators. So the agent running
  a phase must itself be able to spawn. Subagents nest to `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
  (`references/agents.md`), and a Claude Code cloud session sets it to `1`: there a
  subagent cannot spawn anything, and the phase runs as a headless session instead.
- `run-phase` is typed only (`disable-model-invocation: true`), so a subagent cannot invoke
  it through the Skill tool and reads its file instead. A headless session is started with
  the typed command as its prompt, which does invoke it (`references/skills.md`).

## Before the first phase

1. Confirm this is a plugin subdirectory (`.claude-plugin/plugin.json` exists).
2. Find the ledger the way `run-phase` does: `site/notes/<slug>-progress.md`. With no slug
   and exactly one ledger, use it. With several, ask which. With none, stop: `plan-phases`
   has not run.
3. Check the branch and the tree the way `run-phase` does. `git branch --show-current` must
   equal the branch the ledger names. `git status --porcelain` must be empty, or list only
   the paths an `in progress` row names under Notes. Stop and say so otherwise; a failure is
   cheaper to report here than from inside an agent. Never switch branches.
4. Pick the mode: `echo "${CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH:-unset}"`. Use **subagent**
   when it is unset or 2 or more. Use **headless** when it is 0 or 1.
5. Read the ledger and nothing else of the plan. Say in chat which phases will run, in
   order: every row not `done`, or up to phase N with `--through N`. Also say the mode.

## The phase agent's instructions

Both modes give the agent this text, verbatim with `<…>` filled. Call it **the return
rules**:

> You have no live user. Where `run-phase` stops for the user, stop there and return instead
> of waiting: the review of a behavioral row, a Deviation that asks whether to commit, a
> question the plan does not answer, and a release the note says to propose. Commit nothing
> before the reply, which comes back to you in this conversation. For a review, write the
> viewer with `--static` and give its path. Also read any `CLAUDE.md` in `site/notes/` before
> the plan's files: a chat started there would have loaded it. End every turn with exactly
> this form, and nothing after it:
>
> ```
> Status: committed | review | question | proposal | blocked | in progress
> Phase: <N>
> Commit: <short sha> <summary> | none
> Ledger row: <the phase's row as it stands>
> For the user: <for review: the results table, the review.html path, and what to look at;
>   for question or proposal: the question, its options, your recommendation; for blocked
>   or in progress: what stops you and what is uncommitted; for committed: one line of
>   eval pass rates>
> Next: <the next phase's number and note> | none
> ```

## Each phase

1. **Re-read the ledger.** The first row not `done` is this phase. If it is not the one the
   previous agent named as next, say so before starting it. An `in progress` row is fine:
   `run-phase` finishes it rather than restarting.
2. **Start one agent**, and never two phases at once, not even phases the overview says may
   pair. They share one working tree, and each note assumes the commit before it.
   - **Subagent mode.** The Agent tool, `subagent_type: general-purpose`,
     `run_in_background: false`. The prompt:

     > You are running one phase of a plan, as a fresh chat typed `/plugin-dev:run-phase
     > <slug>` would. Read `${CLAUDE_PLUGIN_ROOT}/skills/run-phase/SKILL.md` and follow it
     > exactly, slug `<slug>`, in the plugin directory `<absolute path>`. That file's paths
     > that start with the plugin-root variable are under `${CLAUDE_PLUGIN_ROOT}`.
     >
     > `<the return rules>`

   - **Headless mode.** A new id per phase: `python3 -c "import uuid; print(uuid.uuid4())"`.
     Inside a cloud session every child otherwise reports the parent's session id, and a
     resume would be ambiguous (`references/edge-cases.md`). Write the return rules once to
     `evals/workspace/run-phases/<slug>/return-rules.md` (they hold backticks and quotes, so
     they go through a file). Then, from the plugin directory, run with the Bash tool, in
     the background (a phase can outlast a foreground call), and wait for it to exit:

     ```
     claude -p "/plugin-dev:run-phase <slug>" --session-id <id> \
       --append-system-prompt "$(cat evals/workspace/run-phases/<slug>/return-rules.md)" \
       --plugin-dir ${CLAUDE_PLUGIN_ROOT} \
       --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Agent Skill" \
       --output-format stream-json --verbose \
       > evals/workspace/run-phases/<slug>/phase-<N>-<k>.jsonl
     ```

     `<k>` counts this phase's turns from 1. The session runs unattended with the listed
     tools, because it has nobody to ask; the user chose that by typing this skill. Drop
     `--plugin-dir` when `ls -d ~/.claude/plugins/cache/*/plugin-dev` finds an installed
     copy, so the plugin is not loaded twice. `evals/workspace/` is gitignored. The agent's
     return is the `result` field of the file's last `"type": "result"` line. When there is
     none, the session died: treat it as `blocked`, and give the file's last lines.
3. **Act on its `Status:`.**
   - `committed`: check it before going on. `git log -1 --format=%s` must start `<plugin>
     <slug> (phase <N>):`, `git status --porcelain` must be empty, and the ledger row must
     read `done`. Any mismatch stops the series, and you say which check failed. Otherwise
     print one line, `phase <N> committed: <sha> — <pass rates>`, and go on.
   - `review`, `question` or `proposal`: give the user **For the user** in full (tables,
     paths, the recommendation), and wait. Never answer for them. Then continue the same
     agent with the user's reply verbatim, and act on the status it returns next. It holds
     the edits, the eval iteration and the review page in its context.
     - Subagent mode: SendMessage to the agent. Without SendMessage, start a fresh subagent
       with the prompt above plus: "A previous agent stopped at `<status>` for this phase
       and left the working tree as it is. The user replied: `<reply>`. Pick up from that
       stop. Redo no edit and no eval run the reply does not ask for."
     - Headless mode: the same command with `--resume <id>` in place of `--session-id <id>`,
       the reply as the prompt, and the next `<k>`.
   - `blocked` or `in progress`: stop the series and relay **For the user**. The ledger
     already says where the phase stands, and the next `run-phases` or `run-phase` resumes
     from it.

## Stop

Stop the series when:
- every phase is `done`, or `--through N` is reached;
- an agent returns `blocked` or `in progress`;
- a `committed` check fails;
- the user says stop.

A `proposal` for a release (the last phase's bump) is relayed, and `bump-version` runs only
on the user's yes, like everywhere else. Then print the ledger rows this run changed and
the next phase, or "the plan is done".

## Rules

- **No phase work in this chat.** It makes no edits, runs no evals and makes no commits. If
  an agent cannot be started, stop and say so; doing the phase inline defeats the point.
- **Relay, never decide.** Reviews, questions and proposals go to the user word for word
  enough that they can answer without asking the agent.
- **Nothing is pushed, merged, bumped or tagged here.** Those stay the user's, as in
  `run-phase`.
