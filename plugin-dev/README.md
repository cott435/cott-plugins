# plugin-dev

The kit every other plugin in this repo is built with. It holds one protocol for what a
plugin is, and the skills that design one, change one, test it, check a real run of it, and
release it. It is installed as a plugin so there is one copy of the protocol, and it applies
wherever a plugin is being worked on.

## The protocol: a workflow that runs itself

A plugin exists to run a workflow on its own, for minutes or for hours, and get the same
result each time. So every workflow in every plugin here has the same six parts:

| Part | What it is | What it does |
|---|---|---|
| **Driver** | a skill you type, running in your chat | Asks a script what is next, spawns the agent for that step, acts on what comes back. Does none of the work itself |
| **Agents** | fresh contexts the driver spawns | Each does one unit of work and returns a short fixed form: a status and the paths it wrote |
| **Scripts** | plain code | Print the next step and the slice of a file an agent needs, check a step, write its record. A model never decides what a script can decide |
| **Hooks** | checks the harness runs | Hold anything that must be true before an agent stops or a file is written |
| **Ledger** | a file on disk, or state derived from the work's own files | Says what is done and what is next. One writer, and it is a script |
| **Knowledge skills** | reference an agent loads | The conventions a step needs, loaded by the role that needs them |

Three rules follow, and they are the point of doing it this way:

- **The driver stays thin.** Its context grows with every turn of a long run, so it holds
  only what its script prints, what each agent returns and your answers. It never reads the
  plan, the ledger or an agent's output whole.
- **Deterministic wherever it can be.** What is next, whether a step passed and what gets
  recorded are answered by a script or a hook, not by a model reading prose. A rule that
  matters is a check that fails, not a sentence an agent may skip.
- **The run lives in files.** Every hand-off is a file, so a run can stop, crash or change
  chats and pick up from the ledger, and a finished run can be audited against the plugin's
  own files from its transcripts.

`plugin-anatomy` is the full statement: which component each responsibility belongs in, how
skills attach to agents, every documented frontmatter field, and the edge cases that fail
silently, each fact marked documented, proven by an eval, or unconfirmed.

## How a change reaches a plugin

By where it starts. An idea for a new plugin or a workflow is designed, one workflow at a
time, from its driver down. Facts about a plugin as it is (audited issues, eval results, a
rule every agent must now meet) are fixed in one chat when they are few, and turned into an
edit list when they are many. Both routes hand a spec to the same phases, each planned up
front beside the others of its level, built by one agent and committed with its evals. A run of the finished workflow is then audited against
the plugin's files, and what the audit files as issues is the next set of facts.

The site's **The flow** page has the table that says which command to type, which role uses
which skill, who writes and reads each document, and how each driver runs. Each route has a
page under **Workflows**.

## One file answers each question

When two files disagree, the one named here wins and the other is fixed.

| Question | The truth |
|---|---|
| How does a plugin component behave? | the Claude Code docs, then `plugin-anatomy`'s references. Every other skill cites them and restates nothing |
| What is being built, and why? | the approved spec in `site/notes/<slug>/`: a design (from an idea) or an edit list (from facts) |
| What crosses phases, and where does the plan stand? | the overview and the ledger beside the spec, read and written through `scripts/phases.py` |
| Do two files still agree? | the plugin's `contracts.yml`, run by `check-contracts`. A `FAIL` is fixed in the file, not by relaxing the claim |
| Does it work? | a committed eval set in `evals/sets/`, run by `run-evals`, and its dated log in `evals/`. A clean pass is logged exactly like a failure |
| What went wrong in a real run? | the issues under `runs/audits/`, written only through `scripts/issues.py`, each with an id that stays |
| What version is installed? | `plugin.json`, its marketplace row, the CHANGELOG line and the tag, moved together by `bump-version` |

## Where you are asked

Nothing that commits, publishes or decides for you happens without a stop.

1. `design-plugin` waits twice, for the charts and then the writeup. `revise-plugin` waits
   for the goal and the units before any agent runs, then asks the decisions left open.
2. `plan-phases` asks any decision the spec did not take, waits for your yes to the split,
   then asks what the phase planners could not decide, in one round.
3. `run-evals` stops on every behavioral run until you have looked at the outputs.
4. `fix-issues` shows one planned edit per issue and edits nothing before your yes.
5. `bump-version` names a level in chat and does nothing until you say yes. The same holds
   for every merge and push.

## Install

```
/plugin marketplace add cott435/cott-plugins
/plugin install plugin-dev@cott-plugins
```

Install this one on every machine: its skills apply to whatever else lives in this repo.
After a `git pull`, `/plugin marketplace update cott-plugins` picks up the change.

## The reading site

Every agent, skill, script and workflow of a plugin as a browsable site, built from the
bundle by one shared builder. From any plugin's directory:

```
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py --build
python3 -m http.server --directory site/_build 8000      # http://127.0.0.1:8000
```

Once per machine (Python 3.10+):

```
pip install sphinx myst-parser furo sphinxcontrib-mermaid pyyaml
```

Every plugin's site has the same shape. This README is the home page. **The flow** is the
map: the routes, a table of which role uses which skill, a chart of who writes each
document and one of who reads it, and each driver's loop with its ledger. The last four
are drawn by the builder from the agents' frontmatter and the `flow:` block of
`site/site.yml`, so they cannot drift from each other, and `check-contracts` fails when the
block and the agent and skill files disagree. After them come one page per
workflow, then a page for every agent, skill, reference and script, found without any
config.

`site/site.yml`, `site/flow.md`, `site/workflows/` and `site/notes/` are authored and
committed; `site/docs/` and `site/_build/` are generated and gitignored. The `build-site`
skill has the full contract.

## What's here

| Path | What it is |
|---|---|
| `skills/` | The skills, one directory each |
| `agents/` | `run-auditor` and `run-narrator`, which `audit-run` and `run-flow` spawn |
| `scripts/` | The site builder, the contracts checker, and the three ledger scripts: `phases.py`, `edits.py`, `issues.py` |
| `hooks/` | Two hooks that hold a phased run and an eval run, silent everywhere else |
| `templates/` | What a new plugin starts with, and the shape of every spec, plan and issue file |
| `evals/` | The committed eval sets, the fixtures they run against, and every run's log |
| `site/` | The authored parts of this plugin's own site |
| `contracts.yml` | The cross-file claims this bundle makes about itself |
