# Composition: a workflow is a driver, its agents, and the files between them

The component files say what each piece can do. This one says how a workflow is put together
from them. A plugin exists to run a workflow on its own: the user types one command in the
main chat, and the work goes on, step after step, until it is done or something needs them.
One shape does that, and every workflow in a plugin takes it.

The shape, the loop and the driver's rules are design rules, not platform facts; the runs
they were measured on are cited where they are stated. Platform facts here cite `skills.md`,
`agents.md`, `hooks.md` and `manifest.md` rather than restating their evidence.

## The shape of a workflow

```
 the user types /<plugin>:<workflow>
        │
 ┌──────▼──────────────────────────────────────┐
 │ DRIVER   typed workflow skill, main thread  │◄──► the user: questions, approvals
 │ ask the script → spawn → record → again     │
 └──────┬─────────────────────▲────────────────┘
        │ a slice, printed    │ a return, in a fixed form
 ┌──────▼─────────────────────┴────────────────┐
 │ AGENTS   one fresh context per step         │───► KNOWLEDGE SKILLS, preloaded or invoked
 └──────┬──────────────────────────────────────┘
        │ write                                      HOOKS refuse what must never happen, and
 ┌──────▼──────────────────────────────────────┐     hold a step open until its check passes
 │ FILES    the work, and the LEDGER           │◄─── SCRIPTS print the next step and each
 └─────────────────────────────────────────────┘     slice, check a step, write its record
```

| Part | Is | Holds | Does not hold |
|---|---|---|---|
| **Driver** | the workflow's typed skill, run inline in the main thread | The loop: which agent runs the step the script names, how wide a fan-out is, where the user is asked, when the run stops | The state of the run, which is the ledger's; the work of any step, which is an agent's; anything a script can print |
| **Agent** | an `agents/*.md`, spawned by the driver | One way of working: its role, what it reads, the contract for its output, when it stops, the judgment that belongs only to its job, its tools and model | Orchestration (it cannot ask the user, and it does not decide what else runs), or knowledge another agent also needs |
| **Knowledge skill** | a skill agents preload or invoke | Templates, checklists, style guides, domain methods: anything two agents would otherwise each carry | Instructions about when to run or whom to spawn |
| **Script** | code in the plugin, run by the driver, an agent or a hook | Every answer that is a lookup or a check: where the run stands, one agent's slice of the plan, whether a step is whole, the record of it | Judgment |
| **Hook** | an entry in `hooks/hooks.json` | What must hold whatever a model decides: where an agent may write, what a step must pass before its agent stops, how something is spawned | A rule that "almost always" is good enough for |
| **Ledger** | files in the user's project | What is done, by what evidence, and so what is next | Anything only a conversation knows |

The driver is in the main thread for two reasons. It is the only place that can ask the
user: a subagent, and so a forked skill, never gets `AskUserQuestion` (`agents.md`), so a
design that puts a user decision inside an agent has no way to make it. And every agent it
spawns is then one layer down, with the nesting the platform allows still below it
(`agents.md`, the spawn depth).

## The driver's loop

Every driver is the same loop. What differs between workflows is the script it asks and the
agents it spawns.

1. **Ask the script where the run stands.** One command prints the next step in a line or a
   block, with an exit code for each outcome: a step to run, something that stops the run,
   the run is done. The driver acts on the code. It does not open the ledger or the plan and
   work it out.
2. **Spawn the step's agent**, or every ready step's agent in one message when the steps do
   not depend on each other, at most 20 at once (`agents.md`). The prompt is the agent's
   slice as a script printed it: named fields, the ones the agent's own **Inputs** defines,
   and nothing the agent can read for itself.
3. **Take each return in a fixed form.** The agent's contract ends with the form: a status
   word from a closed list first, then the fields the driver needs for that status. The
   driver branches on the status and reads past it only to relay a question.
4. **A script checks the step and records it.** Whether the step landed is the script's
   answer from the files, not the agent's claim: a return can be wrong, and audited runs
   held false ones (`dev-team/skills/run-package/SKILL.md`, **What you never do**). The same
   script writes the ledger row, and the commit that closes the step where there is one,
   and refuses when the step is not whole.
5. **Route what is not done.** A question goes to the user in full, and the answer goes
   back to the agent that asked. A rejection goes back to the agent that produced the work,
   for a stated number of rounds, after which the step is marked unresolved and not retried.
   A block stops the run with the line that says why.
6. **Ask the script again.** The loop ends when the script says the run is done, when a
   step blocks, or when the user says stop.

Because step 1 reads only files, the command typed again a week later, after a crash or a
hand edit, picks up where the files say. A run that can only be continued from its own
conversation is not finished being designed.

## What the driver holds: almost nothing

A driver's cost is its turns times its context, and both grow with the run: it is the one
context that lasts from the first step to the last, and every turn re-reads all of it. On
one 19-phase plan, 48% of the cache-read tokens were the phase drivers' own turns
(`plugin-dev/evals/2026-10-10-run-evals-runner-mechanical.md`). So what a driver holds
decides what the whole run costs, and a driver is written to hold as little as the loop
needs.

- **A driver carries three things**: what the script printed, what each agent returned in
  its fixed form, and the user's answers. It keeps the work going, reports counts, and
  routes a question to the user and the answer back to the agent that asked. It reads no
  file an agent could read for itself and does none of the work.
- **The state of the run lives in files, and a script reads them.** Where a run stands —
  the next step, whether the last one landed, what is left — is printed by a script from the
  repo and the ledger. (`dev-team`'s `status.py`; `plugin-dev`'s `scripts/phases.py`.)
- **Each agent gets its slice, printed.** A script prints the part of the plan one agent
  needs. An agent that reads the whole plan to find its row pays for every other row on
  every turn, and a driver that reads it to build the prompt pays for it until the run ends.
- **Fan-out is waited on by a script.** Many runs started one tool call each wake the
  driver once each, and every wake re-reads its context: on one plan that cost as much as
  all the runs together. One background command starts them, waits, and prints one report.
- **The skill itself is short.** Its text is in the driver's context for the whole run, so
  it holds the loop, the spawn form for each agent and what to do with each status. A method
  is the agent's, a template is a knowledge skill's, and a lookup is a script's.
- **What must hold is a hook; what must be known is a script's output; what is left is
  judgment**, and only that is the model's. When a rule is being written into a driver's
  prose for the third time, it belongs in one of the first two.

## The ledger

The ledger is the workflow's memory. The driver keeps none of its own, and an agent's ends
with its run.

- **It is in the user's project**, beside the work it describes, or under
  `${CLAUDE_PLUGIN_DATA}` when it is not the project's to keep. Never under
  `${CLAUDE_PLUGIN_ROOT}`, which is replaced on every update (`manifest.md`).
- **Two forms.** A *written* ledger is a file with one row per step that a script fills
  (`plugin-dev`'s `<slug>-progress.md`, filled by `phases.py finish`). A *derived* ledger
  is no file at all: a script works out each step's state from the documents, the code and
  git on every call (`dev-team`'s `status.py`). Derive where the work's own files can
  answer, because a derived state cannot disagree with the repo and survives a hand edit.
  Write a row for what the files cannot show: that a check passed, on which commit, in
  which round.
- **One writer, and it is a script.** A row an agent or a driver writes by hand is a claim.
  A row the checking script writes is a result, and the script refuses to write it for a
  step that is not whole. A check a model performs by reading is a check that is sometimes
  skipped.
- **A row carries its evidence**: the commit, the check that passed, the file the step
  produced. The next step, and a later audit, read the row and not a transcript.
- **An outcome that can change after an agent hands back is carried in a file.** The
  driver receives an agent's first report only (`agents.md`, **What reaches its caller**),
  so the answer the driver acts on is the script's reading of the file, not the report.

A workflow of one step needs no ledger: its deliverable is the record. The ledger starts
where a run can stop partway.

## The hooks that hold a run

An instruction in a driver or an agent is a request. These are the places a workflow needs
more than that, and each is a plugin hook in `hooks/hooks.json`. A plugin agent's own
`hooks:` field is ignored (`agents.md`).

| What must hold | Hook | In this repo |
|---|---|---|
| An agent's step is whole before the agent stops | `SubagentStop`, matched to the agent's type, running the check the ledger's script runs; exit 2 sends the agent back with the reason | `dev-team`'s `gate_on_stop.py`, on the implementer |
| An agent writes only where its role may | `PreToolUse` on `Write\|Edit`, and on `Bash` for shell writes, branching on `agent_type` in the hook's input | `dev-team`'s `guard_writes.py` and `guard_bash.py` |
| Something is started the workflow's way | `PreToolUse` on `Agent` | `plugin-dev`'s `guard_agent.py`: an eval's executors are started by the runner script, not one Agent call each |
| A chat does not stop on a step that was not recorded | `Stop` | `plugin-dev`'s `gate_stop.py`: a phase committed without `phases.py finish` |

Three rules for every one of them (`hooks.md`):

- **Scope it to a run.** A plugin hook fires in every session the plugin is enabled in. It
  exits 0 at once unless the event's `cwd` holds a run of this workflow.
- **Block with exit 2, on every path that should block.** A crash, a timeout or any other
  exit code lets the action through.
- **A guard that should exist only once the workflow has started** can go in the driver
  skill's own `hooks:` field, which registers on invocation and stays for the session.

## What goes in the agent file

- **Identity and scope**: one sentence of what it is and one of what it never does.
- **Inputs**: exactly the fields the driver sends (paths, a mode, a question) and what the
  agent reads from them. The driver's spawn block and this list are one contract; a
  `contracts.yml` claim holds them together.
- **Method**: the steps specific to this job. A step that is really a shared method is a
  skill, and the agent points to it.
- **Output contract**: the file it writes, with its sections and rules, and the return
  form: the closed list of statuses and the fields that follow each.
- **Stop conditions**: when it is done, when it gives up, and what it returns then. An
  agent that meets a decision it cannot make returns it as a question; it cannot ask.

Keep it stable. An agent file that changes with every new use is holding knowledge that
belongs in a skill.

## Attaching skills to an agent

Two ways, with different costs:

| | Preload: `skills:` in the agent's frontmatter | On demand: the agent invokes the `Skill` tool |
|---|---|---|
| Loaded | at every spawn, full content | only when the agent decides it needs it |
| Cost | the skill's full size × every instance; a fan-out of 20 pays 20 times | nothing until used |
| Reliability | always present | the agent must recognize the need; test it |
| Use for | what shapes *every* run: the template it fills, the style it writes in, the checklist it applies | situational knowledge: a debugging method used only when a test keeps failing |
| Requires | nothing | `Skill` in the agent's `tools` |

Several skills on one agent is normal: preload the one or two that define its work, and name
the situational ones in its body with when to invoke each. If an agent preloads more than a
few, check the size against its fan-out width, and whether some are only sometimes needed.

**One skill shared by many agents** is the point of a knowledge skill. When the agent
depends on the skill's headings or names, write a `contracts.yml` claim (`headings` or
`names_listed`) so a rename in the skill fails the sweep instead of an agent.

**Skills that only agents use** get `user-invocable: false`, so they stay out of the `/`
menu. A driver gets `disable-model-invocation: true`: a person starts a run, and no agent
starts one through the `Skill` tool.

**The driver invokes no knowledge skill.** One invoked in the main thread stays in the
driver's context for the rest of the run. Knowledge reaches the work through the agents.

## How much driver a workflow needs

The shape is the default for anything the user types. It scales down, and not away:

| The workflow is | It gets |
|---|---|
| Several steps, a fan-out, or anything that can stop partway and be resumed | The whole shape: driver, script, ledger, and a hook for each "must" |
| One step by one agent, with a question or an approval | A driver of a few lines: spawn, relay, report. No ledger |
| One self-contained job that asks nothing and spawns nothing | A **forked skill** (`context: fork`): the work stays out of the main context and a result comes back. It cannot ask the user (`skills.md`) |

When the same isolated job is typed by a person *and* spawned by a driver, make it an agent
and give the person a thin driver that spawns it. A forked skill is one entry point; an
agent is a method several drivers can share, often many at once, with a fixed tool list and
model.

## Tools and models

- **Least privilege.** List `tools` explicitly for every plugin agent. A reviewer that only
  reads gets no `Write`, or writes only its findings file. An agent that must never spawn
  others does not get `Agent`.
- **Model per role.** A cheap, wide loop (a survey, a classifier, a per-unit pass over
  hundreds of items) takes a cheaper model; the loop where judgment is made takes the
  strongest. Pinned models are recorded in the plugin's `VERSIONING.md`, so a model change is
  not mistaken for a prompt regression.
- An external system an agent needs is a **plugin MCP server** (`.mcp.json`), and the agent
  lists its tools by full name, `mcp__plugin_<plugin>_<server>__<tool>`, in `tools` (`mcp.md`).

## Anti-patterns

- **A workflow with no driver.** The user types each step and carries the order in their
  head. The steps exist; the workflow does not.
- **A driver that reads the plan.** A skill that keeps a run going and opens the ledger,
  the plan or its agents' outputs to decide what is next. Print it from a script.
- **A driver that does the work.** A step done inline because it is small stays in the
  driver's context until the run ends. If an agent cannot be started, the run stops and
  says so.
- **A driver that is an agent.** It cannot ask the user, and everything it spawns is a
  layer deeper, where a session may give it no `Agent` tool at all (`agents.md`).
- **A run that lives in the conversation.** What is done is known only to the chat that did
  it, so a second chat cannot continue it and nothing can check it. Put it in the ledger.
- **A ledger written by hand.** A row a model fills in is a claim about the step. The
  script that checks the step writes the row.
- **One agent per command.** Commands and agents are counted separately; a 1:1 match means
  the work was not composed (see `design-plugin`'s composing reference).
- **Rules in the plugin's `CLAUDE.md`** meant for agents or skills at runtime. It is never
  loaded as plugin context (`agents.md`).
- **The same checklist pasted into three agents.** Make it a skill; preload or invoke it.
- **An agent that asks the user.** It cannot. Return the question.
- **A hook where an instruction would do**, or an instruction where only a hook would do.
  A hook runs in every session the plugin is enabled in, so it earns its place only when
  "almost always" is not good enough.
