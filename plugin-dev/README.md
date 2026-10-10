# plugin-dev

The shared kit every other plugin is built with. It covers how a plugin is designed and
planned in phases, which component each piece of it should be, how it is tested and how a
test run is recorded, how its cross-file claims are checked, how its reading site is
generated, and how it is versioned. One copy, installed as a plugin, instead of the same
conventions drifting apart across repos.

## Why this is a plugin and not a folder

The things being shared are two different kinds of thing, and only one of them is code.

The site builder is code, so it lives in `scripts/` and is invoked with a path. But the
versioning policy and the eval convention are *instructions for Claude* — the reason the eval
protocol works at all is that something tells Claude to write the file every time. A shared
folder can't do that; a `CLAUDE.md` copied into every repo can, but then there are N copies
to keep in sync, which is the problem being solved.

A skill is exactly an instruction that travels. So the policy is a set of skills, the builder
rides along in the same bundle, and every plugin repo keeps a `CLAUDE.md` that is a pointer
rather than a copy. Installing this plugin is what makes the protocol apply.

## The skills

Fifteen skills, in three groups by how they start. The table is the one list of them: a
`contracts.yml` claim fails when a directory under `skills/` has no row here.

| Skill | Starts | What it does |
|---|---|---|
| `log-eval` | on its own, every test run | Records a test against a plugin's own skills or agents as a dated file under `evals/` with the commit and model it ran against, plus an index row. A clean pass exactly like a failure. |
| `build-site` | on its own, after any agent or skill edit | Rebuilds the Sphinx site (`site/docs/`, HTML in `site/_build/`) from the bundle. |
| `check-contracts` | on its own, beside `build-site` and before any bump | Runs the cross-file claims in a bundle's `contracts.yml`: a heading one file parses and another owns, a pattern no file may contain, a list of names that goes stale, and frontmatter keys the platform does not document or ignores in plugins (checked against `plugin-anatomy`). A `FAIL` names the `file:line`. |
| `run-evals` | on its own, whenever a phase or change calls for evals | Runs one skill's or agent's evals from its committed set in `evals/sets/`: mechanical checks, a load check, behavioral runs graded assertion by assertion with skill-creator's grader. A script starts the runs as headless sessions and hands back one report, so the chat that asked reads a table, not every run. The baseline runs once per ref and is reused after; a regression row runs the working tree only. Stops for your review in skill-creator's viewer, then records the result with `log-eval`. |
| `plugin-anatomy` | on its own, when a plugin's components are designed, written or reviewed | The source of truth for plugin components: which one a responsibility belongs in (skill, agent, hook, MCP server, script, config), how skills and agents combine, every documented frontmatter field, and the edge cases that fail silently. Each fact is marked documented, proven by an eval, or unconfirmed. `design-plugin`, `plan-phases` and `run-phase` read it, and the frontmatter check in `check-contracts` enforces its key lists. |
| `new-plugin` | on its own, when a plugin is started | Scaffolds a plugin subdirectory from `templates/` and adds its row to the marketplace. |
| `design-plugin` | when you type it | Turns an idea for a new plugin, or a change that adds or redraws a workflow, into an approved design through discussion. In a review sweep it designs only the edit list's **Needs a design** items, which are usually none. Interviews you in rounds and composes the jobs into loops: each loop's unit of work, what makes that unit's output trustworthy, where every input it needs comes from (you, a file, or another cheaper loop), and the files where loops meet. Shows one flow chart per workflow plus a system chart for your approval, then the full writeup for your approval, and commits it as `site/notes/<slug>/<slug>-design.md` on a new branch. |
| `review-plugin` | when you type it | Reviews a whole existing plugin for what is wrong with it, for a sweep too big for one chat to read. Agrees the goal and the units with you from the plugin's shape (frontmatter, line counts, the audit index), then runs waves of agents that each read one role or one set of scripts whole and write findings, and one reconcile agent that turns every finding into one deduplicated edit list, `site/notes/<slug>/<slug>-edits.md`: each item with its files and lines, mechanism, dependencies, the issues it closes and the evals that prove it. Asks the decisions the findings leave open, and commits the list on a worktree branch. The orchestrating chat reads only `scripts/edits.py`'s output, never the plugin's files or the findings. Items that need a new workflow go to `design-plugin`. |
| `plan-phases` | when you type it, in a fresh chat | Splits an approved spec into phases: a design, an edit list (read through `scripts/edits.py`, never whole), or both, without the discussion behind it. Asks about any decision the spec did not take, shows the split for your yes, then writes an overview (each phase's scope and items, what it must not touch, the headings one phase writes and another reads, every phase's eval rows) and a progress ledger under `site/notes/<slug>/`, and has one writer subagent per target write the eval sets in parallel. Writes no phase note. Commits all of it as phase 0. |
| `run-phase` | when you type it, once per chat | Does the next unfinished phase: reads the spec, the overview and the ledger; writes that phase's note from its row and the files as they are now (or reads the note, in a plan that already has one); reads each component's `plugin-anatomy` reference before writing it; makes exactly the note's edits; runs the plugin's rules, `check-contracts`, `build-site` and the phase's evals; logs them and writes any proven platform fact back to `plugin-anatomy`; commits once; updates the ledger; stops. |
| `run-phases` | when you type it, in place of one `run-phase` chat per phase | Drives the plan from your chat: one fresh agent per unfinished phase, in series, each doing `run-phase` — a subagent, or a headless `claude -p` session where subagents cannot spawn (cloud sessions cap the depth at 1). Relays every review stop, question and bump proposal to you and resumes the same agent with your answer. Checks each phase's commit, clean tree and ledger row before the next. Does no phase work itself, and pushes, merges and bumps nothing. `--through N` stops after phase N. Phase agents run on Sonnet 5.5; `--model inherit` keeps your chat's model. |
| `run-flow` | on its own, when you ask what a run or an agent did; or typed | Draws a real run of the plugin's workflow from its session transcripts as a page in the browser pane: the flow chart `audit-run` draws, with every agent clickable through to its full record — the prompt it was sent, every step with full input and output, each Write's content and each Edit's old and new text, its commits and what it handed back. After an audit, each box also shows the issues found there and the prior fixes that held or recurred there. `--agent <type>` lists every run of one agent type in time order, in one chat or, with `--sessions` or `--branch`, across several. `--explain` puts a short plain account at the top of each agent's page, written by the run-narrator agent, each line linked to its steps. `scripts/trace.py` here is the trace builder `audit-run` runs too. Judges nothing. |
| `audit-run` | when you type it, from the plugin under test | Audits a real run of the plugin's workflow from its session transcripts. `run-flow`'s `trace.py` rebuilds what ran: each agent spawned and the prompt it was sent, every tool call, hook block, commit and hand-back. One run-auditor agent per selected agent, one per driver segment, and one for cross-agent consistency then hold it against the agent and skill files at the version that ran. Every finding cites a trace step and a `file:line`, and is classed by fault: agent, driver, definition or platform. Each ERROR is spot-checked before it is reported. Files every ERROR and WARN (and each definition NOTE) as an issue under the plugin's committed `audits/issues/`, matched to an existing issue by its quoted rule so an id stays the same from one audit to the next, writes the run report to `audits/runs/<date>-<id8>.md`, and commits `audits/` in one commit of its own. On a rerun it also checks every fixed issue whose fix was in the code that ran: it widens the selection so each one is exercised, gives each auditor the issues that apply to its piece, spot-checks every verdict, and records each issue as held, recurred, not exercised or not testable. Also draws the run as a flow chart: waves of agents, so what ran in parallel versus in series; one column per section, showing how many runs and review rounds it took; each review coloured by its verdict; and the points where the driver stopped to ask. Logs the run with `log-eval`, briefly: the issue ids by outcome and a link to the report. `--units new` re-audits only newly finished agents, so it can watch a workflow still running in another chat. |
| `fix-issues` | when you type it, from the plugin whose issues they are | Fixes the issues an audit filed under the plugin's `audits/issues/`: selects them (by id, by `run:<id8>`, or as open or recurred), plans one edit per issue and asks once, edits on a worktree branch, runs `check-contracts`, `build-site` and `run-evals` against the last tag, records a Fix attempt with a `Verify:` line in each issue, and proposes the merge and the bump. Never marks an issue verified: the next audit of a rerun does that. |
| `bump-version` | only on your yes | Decides patch/minor/major from what changed, bumps `plugin.json` and the marketplace row, writes the CHANGELOG line, tags, pushes. Stamps `fixed_in` on the issues the release carries. Proposes itself in chat and waits. |

## The rest of the bundle

| Path | What it is |
|---|---|
| `agents/run-auditor.md` | One of the two agents: audits one unit, one driver segment, or the whole run for cross-agent consistency, and writes a findings file. On a rerun it is also given the prior issues that apply to its piece and reports each held, recurred or not exercised, with the step. Spawned only by `audit-run`. |
| `agents/run-narrator.md` | The second agent: with `run-flow --explain`, writes a short account of one unit, each line citing its steps. Never judges. |
| `audits/` (in each audited plugin) | The committed ledger an audit writes: `issues/<ID>.md`, `INDEX.md`, `runs/<date>-<id8>.md`. Written only through `scripts/issues.py`. |
| `scripts/build_site.py` | The site builder (Sphinx, MyST, Furo). Fully generic — everything is discovered from the bundle. |
| `scripts/contract_sweep.py` | The contracts checker. Its `frontmatter` check reads the allowed keys from `plugin-anatomy`'s references rather than its own copy. Shared, so a change to it gets a positive and a negative run before it is committed (this plugin's `CLAUDE.md`). |
| `scripts/edits.py` | A review's findings files and edit list, read and checked without a model: the shape of every findings file, the edit list's items and decisions, an index of one line per item, one phase's items printed whole, and coverage (every item in exactly one phase, dependencies respected). `review-plugin`, `plan-phases` and `run-phase` read the list through it. |
| `scripts/phases.py` | A phased plan, read and advanced without a model: the next phase and whether anything stops it, the slice of the overview and ledger one phase needs, the phase's items with the lines they cite carried to where they are now, the phase's mechanical checks in one call (the site built once, at the last phase), the ledger row and the commit that close a phase, the check that a phase stands, a status line per phase with eval pass counts and tokens, each eval target's last-touch phase, and the plan's eval rows against the checkpoint rule. `run-phases`, `run-phase` and `plan-phases` call it and never read the overview or the ledger whole. |
| `hooks/` | Two hooks, both silent unless they apply. `guard_agent.py` refuses an eval executor or grader spawned through the Agent tool for an iteration the runner should run. `gate_stop.py` checks a phase that was committed without `phases.py finish` before its chat stops. |
| `scripts/issues.py` | The audit ledger: creates and updates issue files under a plugin's `audits/issues/`, derives each issue's status, renders `audits/INDEX.md`, and checks the ledger. `audit-run`, `fix-issues` and `bump-version` write through it; nothing writes an issue file by hand. |
| `templates/audits/` | `issue.md` and `run-report.md`: the one list of an issue file's and a run report's sections. |
| `scripts/defaults/` | `extra.css` used when a plugin doesn't override it. |
| `templates/` | The files a new plugin subdirectory starts with. |
| `templates/phases/` | The design shape `design-plugin` writes, the overview and ledger shapes `plan-phases` writes, and the phase-note shape `run-phase` writes. |
| `templates/review/` | The review plan, findings-file and edit-list shapes `review-plugin` and its agents write. |
| `site/workflows/` | The five workflows below, one page each, rendered on the reading site. |
| `evals/sets/` | Every skill's committed eval set, and trigger set for the model-invoked ones, that `run-evals` runs. |
| `evals/fixtures/` | What those sets run against: a toy plugin for `run-phase`, a written design for `plan-phases`. Also the two checks that need no model: `run-evals-runner/check.py` for `eval_workspace.py`, `phases/check.py` for `phases.py` and the hooks. |

## Workflows

Four ways work reaches a plugin, and one way to check what a plugin did once it ran. Each is
a page under `site/workflows/`; the summaries here say which skills run, in what order, and
which of them wait for you.

**[A new plugin](site/workflows/new-plugin.md).** Three kinds of chat. First, from the
repo root, `/plugin-dev:design-plugin --new <name>`: it reads the closest existing plugin for
conventions, interviews you in rounds, and composes the jobs into loops. Then it shows one flow
chart per workflow plus a system chart and waits for your yes, then shows the writeup and waits
again. Only then does it create the branch, invoke `new-plugin` for the scaffold and
marketplace row, and commit `site/notes/0.1/0.1-design.md`. Second, in a fresh chat,
`/plugin-dev:plan-phases 0.1` from `<name>/`: from the design alone, it splits the work into
phases (phase 1 is the smallest bundle that loads), shows the split for your yes, and commits
the notes, the ledger and every phase's eval sets as phase 0. Third, one chat per phase:
`/plugin-dev:run-phase 0.1`, each running that phase's evals through `run-evals`. The last
phase proposes tagging `0.1.0`; `bump-version` does it on your yes. A plugin that will only
ever be one or two skills skips all this: `new-plugin`, write them, `build-site`,
`check-contracts`, `run-evals` on whatever is behavioral, propose the tag.

**[A small change](site/workflows/small-change.md).** One agent or skill, one chat. Read
the component's `plugin-anatomy` reference; edit; the plugin's own rules (`CLAUDE.md`); `check-contracts`; `build-site`; if the edit changes
what an agent *does*, `run-evals` on the target's set in `evals/sets/` — the new case added
to the set first — logged with `log-eval` before results are reported; one commit. If it
looks bump-worthy, `bump-version` says so and waits.

**[A large change, in phases](site/workflows/phased-change.md).** For a change that adds or redraws a workflow. Inside the plugin,
`/plugin-dev:design-plugin <slug>`: it reads what the change touches, interviews you in rounds,
shows the changed workflows as charts (new, changed and suggested components marked) and then
the writeup, each waiting for your yes, and commits the design on a new branch. Then, in a fresh
chat, `/plugin-dev:plan-phases <slug>` splits the design into phases, with every behavioral
eval's prompts and expectations written into `evals/sets/`, and commits phase 0. Then one fresh
chat per phase, each opened with nothing but `/plugin-dev:run-phase <slug>`, which writes
that phase's note against the files as they are, runs its evals through `run-evals` and stops
for your review of the viewer before it commits, until the ledger's last row is `done` and the
last phase has proposed the bump. Or one chat, `/plugin-dev:run-phases <slug>`, which runs a
fresh agent per phase in series and brings each review back to you.

**[A review sweep](site/workflows/review-sweep.md).** For fixing what is wrong across a plugin
too big for one chat to read, rather than adding something. Inside the plugin,
`/plugin-dev:review-plugin <slug>`: it agrees the goal and the review units with you, runs
waves of agents that each read one role whole and write findings, has one agent reconcile them
into an edit list, asks you the decisions it leaves open, and commits the list on a new
branch. From there the path is the large change's: `plan-phases`, then `run-phase` per phase.
`design-plugin` comes in only for the items under the edit list's **Needs a design**: a fix that adds a new workflow, a new agent with its own loop, or a new file two workflows meet at. A hook, a script flag or a record file inside a loop that already exists is not one of these: it is an edit, whose item gives its exact behavior and a fixture. That section is usually empty, and then the next chat is `plan-phases`.

**[Checking a run, fixing it, and checking the fix](site/workflows/audit-a-run.md).** A workflow ran in some project's chat,
maybe for hours, and you want to know whether it did what the plugin says. Open a fresh chat
on the plugin's folder (`dev-team/`, not the project) and type `/plugin-dev:audit-run` with
words from the chat's title, as the sidebar shows it. With several matches, or none given, it
lists the candidates by title, span, agent count and fork, and asks. It rebuilds the run from the
transcripts on disk and draws it as `flow.html`. It proposes up to 12 agents to audit and asks
before more. The skill runs in your chat: it asks, selects, merges and spot-checks. The
`run-auditor` agents it spawns each judge one agent's trace in a fresh context, then one
more checks consistency across them. The run report is committed under the plugin's
`audits/runs/`, and the run is logged by `log-eval`. It never edits the plugin itself.
`--units new` watches a run that is still going. What it finds is filed as issues under the
plugin's `audits/`, with ids that stay. `/plugin-dev:fix-issues` fixes them from any chat and
records how a rerun will show each fix; the next `/plugin-dev:audit-run` of a rerun reports
each one held, recurred, not exercised or not testable, and `/plugin-dev:run-flow` draws any
run with every agent one click from its full record.

What is the same in the four that change a plugin: which component a responsibility belongs in, and every
platform fact a design relies on, come from `plugin-anatomy`, and a fact proven by an eval is
written back to it; every eval is a file before it is a sentence in chat; evals
run through `run-evals` from committed sets in `evals/sets/`; the site is rebuilt after
every agent or skill edit; contracts are checked before every commit that touches one; and
nothing is bumped, tagged or pushed without a yes.

## Install

```
/plugin marketplace add cott435/cott-plugins
/plugin install plugin-dev@cott-plugins
```

Install this one on every machine — the point is that its skills apply to whatever else
lives in this repo.

## The repo layout, and why

This plugin lives inside `cott-plugins`, one directory among several:

```
cott-plugins/
├── .claude-plugin/marketplace.json   the catalog — every plugin below, by relative path
├── plugin-dev/                       this kit
├── dev-team/                  a plugin
└── <next plugin>/                    a plugin
```

One repo, one clone, one push/pull. `marketplace.json` still lets you `/plugin install` each
plugin independently on whatever machine wants it — bundling only means the *source* of every
plugin is on disk everywhere the repo is cloned, not that every plugin is *installed*
everywhere. For a repo of markdown and small scripts, carrying the source of a plugin you
haven't installed costs nothing.

The trade-off, honestly: a single repo can't version or tag one plugin without touching the
tag namespace of the others, and a change to `dev-team` shows up in `plugin-dev`'s git
log even though nothing in `plugin-dev` changed. `bump-version` still works — see below — it
just tags the whole repo rather than one plugin's own history. If a plugin ever needs to be
shared outside this account, or versioned on a schedule independent of everything else here,
that's the point to split it back out into its own repo and point `marketplace.json` at
`{"source": "github", "repo": "...", "ref": "..."}` instead of a relative path — both are
valid `source` shapes, and moving between them later doesn't require rewriting anything else.

## A new machine

```
git clone git@github.com:cott435/cott-plugins.git ~/dev/cott-plugins
```

One clone gets the catalog and every plugin's source. Then add the marketplace and install
what that machine actually needs — the marketplace file is already on disk, so `marketplace
add` just points Claude Code at the local clone:

```
/plugin marketplace add ~/dev/cott-plugins
/plugin install plugin-dev@cott-plugins
```

(Or `/plugin marketplace add cott435/cott-plugins` to have Claude Code manage its own clone
instead of using yours — either works; using your own clone means one copy on disk instead of
two.)

## Working on a plugin with two machines

Ordinary git: push from one, pull on the other, same as any repo. A release still needs a
version bump and a tag — `bump-version` below — the only difference from a multi-repo layout
is that the tag names the whole repo's state, not one plugin in isolation, so tag messages
should say which plugin the release is actually about.

## The reading site

```
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py --build   # from any plugin subdirectory
python3 -m http.server --directory site/_build 8000                # http://127.0.0.1:8000
```

Without `--build` the script writes only the Sphinx source tree (`site/docs/`). The built
site is plain static HTML, so any static server works; `open site/_build/index.html` also
works for everything but search.

Requires, once per machine (Python 3.10+):

```
pip install sphinx myst-parser furo sphinxcontrib-mermaid pyyaml
```

`--build` names what is missing if one of them isn't installed. The nav is generated from what the script finds, so a new agent, skill, command,
rule, script or `references/` file appears without editing any config:

    Start (README, the flow) -> Workflows -> Agents -> Commands -> Workflow skills ->
    Knowledge skills -> Scripts -> Rules and config -> Notes -> Evals

A section with nothing in it is omitted. A skill is a **workflow skill** when its frontmatter
says `context: fork` or `disable-model-invocation: true`, and a **knowledge skill** otherwise.
A skill's `references/` pages are its children in the nav. Each script under `scripts/` and
`skills/*/scripts/` gets a page (docstring, `--help` for every subcommand, functions, source),
and a backticked mention of one anywhere links to it. `site/docs/` and `site/_build/`
are generated and gitignored in every plugin repo; `site/site.yml`, `site/flow.md`,
`site/workflows/` and `site/notes/` are authored and committed. Every key in `site.yml` is
optional — a plugin with no site config at all still builds.

See `skills/build-site/SKILL.md` for the full contract.
