# Changelog

One entry per tagged release. The versioning policy — what triggers patch/minor/major, and
how model and eval versioning relate to it — is in the `plugin-dev` plugin's `bump-version`
skill. This repo's own decisions are in `VERSIONING.md`.


## [3.0.0] - 2026-10-10

A change reaches a plugin by one of two routes, and every plugin's site has one shape. Major
because a typed command was renamed: `/plugin-dev:review-plugin` is now
`/plugin-dev:revise-plugin`.

### Changed

- **`review-plugin` is `revise-plugin`** (`c48c9df`). It plans a change across a whole
  plugin from facts about it, agent by agent and skill by skill, and takes
  `<slug> issues <selection>` for audited issues. The files it leaves keep their names
  (`<slug>-review-plan.md`, `templates/review/`, `Mode: review`), so a plan in flight is
  untouched; only the command you type changes.
- `design-plugin` is for an idea: a new plugin, or a workflow added or redrawn, each designed
  from its driver down. Typed for a change with no workflow in it, it names `revise-plugin`
  or `fix-issues` before asking anything. Its design template names each workflow's driver,
  where the run stands, each agent's returns and what holds it (`c48c9df`).
- `fix-issues` stops and names `revise-plugin` when `issues.py route` says the selection is
  more than one chat should plan; `--here` overrides. `audit-run` prints the route for what
  it just filed (`c48c9df`).
- The site's workflow pages are four, by where a change starts: designing a plugin or a
  workflow, changing a plugin from facts, planning and running the phases, checking a run
  (`1069a0f`).
- The README states the protocol and why, and lists nothing the site lists: no skills table,
  no bundle table, no workflow summaries. `contracts.yml` no longer requires the skills
  table (`4559643`).
- `site/flow.md` is the routes plus four parts the builder draws; the hand-written loop
  chart and hand-offs table are gone (`4559643`).

### Added

- `scripts/issues.py route [ids | --status | --session]`: exit 0 for `fix-issues`, exit 3
  for `revise-plugin` (more than six issues, more than three across more than three roles,
  or an issue that recurred after two fixes) (`c48c9df`).
- `scripts/build_site.py` fills five markers in `site/flow.md` from each agent's `skills:`
  frontmatter and a `flow:` block in `site/site.yml`: a table of which role uses which skill
  (always, or on a condition), a chart of who writes each document and one of who reads it,
  the documents table behind them, and one loop per driver with its ledger. A plugin with
  agents and no `site/flow.md` gets a page of those parts (`4559643`).
- `scripts/build_site.py` renders `site/reference/*.md` as a **Reference** section after
  Workflows, ordered by `reference_order` (`77eed6e`).
- `scripts/contract_sweep.py`: a fifth claim kind, `flow`, holds the `flow:` block to the
  files. It fails when a role's file names a skill or a document the block does not place,
  when the block lists one the file never names, when an agent is no role, and when a hook
  is wired and no driver names it (`172e41d`).
- `evals/fixtures/flow/check.py`: the `flow` claim and the flow page on a toy plugin, one
  planted disagreement per rule, no model (`172e41d`).
- `templates/site/flow.md`, a `flow:` example in `templates/site/site.yml`, and a README
  template in the new shape; `new-plugin` copies the flow page (`4559643`).

### Upgrading

- Type `/plugin-dev:revise-plugin` where you typed `/plugin-dev:review-plugin`.
- A plugin's `site/flow.md` keeps building as it is. To get the drawn parts, add a `flow:`
  block to `site/site.yml` and the marker lines to `flow.md` (`build-site`, **The flow
  page**), then a `flow:` claim to `contracts.yml`.

## [2.3.0] - 2026-10-10

`plugin-anatomy` starts from the driver: a workflow is a thin driver in the main chat, the
agents it spawns, and the scripts, hooks and ledger that keep the run on track.

### Added

- `plugin-anatomy`'s `SKILL.md`: **What a plugin is for**, ahead of the routing questions —
  the six parts of a workflow and the three rules (the driver is thin, the run is
  deterministic wherever it can be, the run lives in files); a Driver row and a Ledger row
  in the components table (`8b791a1`).
- `plugin-anatomy`'s `references/composition.md`: the driver's loop, the ledger (written or
  derived, one writer and it is a script), the hooks that hold a run, and how much driver a
  small workflow needs (`8b791a1`).
- `references/edge-cases.md`: a run that costs more with every step, and a run that cannot
  be continued in a new chat (`8b791a1`).
- `evals/sets/plugin-anatomy.json` evals 11 and 12, and three trigger queries (`8b791a1`).

### Changed

- `references/composition.md` is organized around composing a workflow with a driver, not
  around choosing a skill or an agent; **A workflow that runs for a long time** and **Where
  hooks and MCP servers fit** are folded into the new sections (`8b791a1`).
- The routing questions send keeping a run going to the driver, "where does the run stand"
  to a script, and a run's state to the ledger (`8b791a1`).
- `design-plugin`: a design names each workflow's driver, the script that prints where the
  run stands, its ledger and its return forms, and the checklist before the charts asks for
  them (`8b791a1`).

## [2.2.0] - 2026-10-10

Everything a run of a plugin leaves behind has one place, `runs/` in the audited plugin, and
an audit stops carrying issues that have stopped coming back.

### Added

- `trace.py where`: the workspace for a session, `runs/<project>/<command> <title>/<id8>`,
  named once and kept when the chat is renamed (`dc65572`).
- `settled`: an issue whose latest fix held in three sessions and has not been found again
  since is no longer handed to auditors and is one line in `INDEX.md` (`6489cda`).
- `issues.py list --format brief`: one line per fixed issue, what `audit-run` needs of it
  (`6489cda`).
- `evals/fixtures/issues/check.py`: a no-model check of the ledger layout and settling
  (`6489cda`).

### Changed

- **Breaking, for a plugin with an `audits/` directory:** the ledger moved to
  `runs/audits/` (`issues/`, `INDEX.md`, and the run reports as `reports/`), and a session's
  trace from `evals/workspace/audit/<id8>/` to `runs/<project>/<command> <title>/<id8>/`.
  `issues.py`, `audit-run`, `run-flow`, `fix-issues`, `bump-version` and the report template
  read the new paths; `dev-team`'s ledger is migrated and its `.gitignore` holds `runs/*` and
  `!runs/audits/` (`dc65572`).
- `audit-run` writes a Checks line only for a prior issue that held or recurred; `not
  exercised` and `not testable` live in the run report's Prior issues table, and
  `check-result` refuses them (`6489cda`).

### Fixed

- `audit-run` and `fix-issues` named `audits` in their ledger commits (`32f7d7f`).

## [2.1.0] - 2026-10-10

A phase of a plan spends less time waiting and reading. Two mechanical-only phases of
dev-team's determinism plan took 21 and 23 minutes; 9.5 and 14 of those went to the plugin's
fixture suite outlasting the Bash tool's 120 s default, and about 8 to fifty separate reads
before the note. Plans without a `**Checks:**` line are finished as before.

### Added

- `phases.py checks`: a phase's whole mechanical gate in one call — `check-contracts` and
  every command on the overview's new optional `**Checks:**` line, started together — one
  line per command, a failure's FAIL lines under it, the full output in `checks.log`
  (`3b51457`).
- `edits.py show --located`: under each item, where every `path:line` it cites is in the tree
  now, carried from the reviewed commit through `git diff`, with the lines there (`90928cd`).

### Changed

- `phases.py finish` refuses a plan that has a `**Checks:**` line until `checks` has passed
  on the tree as it stands; the note, the ledger and the eval logs may change after it. It
  takes `--log` as a bare file name too (`3b51457`).
- `phases.py brief`, against an edit list, prints the list's Goal, Decisions taken and What
  must not break, and the phase's items with their cited lines as they stand; `--short`
  leaves that part out (`90928cd`).
- `build-site` runs once in a plan, at its last phase, where `checks` runs it: the built site
  is not committed. `run-phase`, `plan-phases` and the phase templates no longer ask for it
  every phase (`90928cd`).
- `run-phase` makes the one `checks` call in the foreground with a ten-minute timeout, never
  polls it, and batches the reads the brief does not cover (`3b51457`, `90928cd`).

## [2.0.0] - 2026-10-10

The reading site is built with Sphinx, MyST and Furo instead of MkDocs, so skills nest their
references, scripts get pages, and lists render the way GitHub reads them. Breaking: every
plugin repo that builds its site now needs `sphinx myst-parser furo sphinxcontrib-mermaid
pyyaml` instead of `mkdocs mkdocs-material pymdown-extensions`, and the generated output
moved.

### Changed

- `scripts/build_site.py` is the Sphinx builder: generated sources stay in `site/docs/`,
  HTML goes to `site/_build/` with `--build`. `site/mkdocs.yml` and `site/_site/` are no
  longer written, and a per-repo `site/mkdocs-base.yml` is no longer read.
- A skill's `references/` are its children in the nav (`skills/<name>/index.html`), not a
  flat list.
- `scripts/defaults/extra.css` is written for Furo.
- `build-site` skill, README and templates describe the new build and how to serve it.

### Added

- A **Scripts** section: each `scripts/*.py` and `skills/*/scripts/*.py` has a page with its
  docstring, `--help` for every subcommand, its public functions and its source. A backticked
  mention of a script in any page links to it, and the script lists what links back.
- Relative `.md` links are rewritten to the generated layout; one that resolves to a page the
  site does not render is a Sphinx warning.

### Removed

- The MkDocs builder, `scripts/defaults/mkdocs-base.yml`, and the list re-indent pass that
  existed only for Python-Markdown.

## [1.2.0] - 2026-10-10

What a phased plan costs to run. Nineteen phases of one plan spawned 1,174 agents and read
about 2.0B cached tokens: half of it the phase chats re-reading their own context once per
finished eval agent, and much of the rest evals rerun on files a later phase edited again.
Minor: a new script, two new hooks and new flags; a plan already under way runs as before,
and its behavioral rows run wherever its overview has them.

### Added
- **`eval_workspace.py run`** (892e3b6): executes and grades every run an iteration owes as headless `claude -p` sessions and prints one report (pass counts per eval and side, each failed expectation with its evidence and the baseline's verdict, the graders' remarks, the cost). An errored run, or one that named a file its expectations are in, is run once more; a second `run` retries what was not run. Its sessions bill the account the CLI is logged into.
- **Baselines are reused** (892e3b6): `init` copies in a baseline run an earlier iteration finished at the same ref, model and inputs, and regrades it without rerunning it when only the expectations changed. `init --working-tree-only` starts no baseline; `--quiet` prints the counts and warnings only; `--by-hand` marks an iteration whose runs are spawned through the Agent tool.
- **`scripts/phases.py`** (dcfa250, 253266a): `next`, `brief`, `finish`, `check`, `status`, `touch`, `plan-check`. The chats that run a plan read the overview and ledger through it and never whole; `brief` prints the exact `init` command for each behavioral row; `finish` checks a phase is whole (its note, its logs, each row's ids laid out in the row's mode, contracts), writes its ledger row and makes its commit.
- **Two hooks** (dcfa250): `guard_agent.py` refuses an eval executor or grader spawned through the Agent tool for an iteration not laid out `--by-hand`; `gate_stop.py` checks a phase committed without `phases.py finish` before its chat stops. Both exit 0 at once unless they apply, and fail open.
- `skills/run-evals/references/prompts.md`: the one copy of the executor and grader prompts (892e3b6).
- `plugin-anatomy`, `references/composition.md`: the rules for a workflow that runs for a long time — the state of the run in files a script reads, a driver that holds the script's lines, each agent's return and the user's answers (dcfa250).

### Changed
- **A phase runs its mechanical checks; a target's behavioral evals run once, after its last edit** (dcfa250): at the first checkpoint at or after the last phase that touches it, new evals compared, existing ones working tree only. `plan-phases` names the checkpoints in the overview (`**Checkpoints:**`) and shows the split with its cost; `phases.py plan-check` fails a behavioral row anywhere else.
- **`run-phase` and `run-phases` call `phases.py`** (dcfa250) for the next phase, the phase's slice of the plan, the commit and the check that it stands. `run-phases` starts phase agents on Sonnet 5.5; `--model inherit` keeps the chat's model (892e3b6).
- **Blind comparison runs only when a row says `blind`** (892e3b6), no longer whenever the two pass rates are close.
- `eval-kinds.md`: **When behavioral evals run**, and a cost table from measured sessions (892e3b6, dcfa250).
- Evals: `evals/2026-10-10-run-evals-runner-mechanical.md`, `evals/2026-10-10-phases-script-and-hooks-mechanical.md`.

## [1.1.2] - 2026-10-09

### Fixed
- One rule for when a review item needs a design (2e9efd9): a fix that adds a new workflow, a new agent with its own loop, or a new file two workflows meet at goes under **Needs a design** and through `design-plugin`; a hook, a script flag or a record file inside an existing loop stays an edit with its exact behavior and a fixture. The README, `review-plugin`, its reconcile prompt, the edit-list template, `design-plugin` and the review-sweep page now say the same, and an empty section means `plan-phases` is next. The README no longer offers `design-plugin` for any "change too big for one chat".

## [1.1.1] - 2026-10-09

### Fixed
- With a design and an edit list in one plan, `plan-phases` writes a gap answer into the edit list's **Decisions taken** (next `D-` id, its items in the Items cell), so `edits.py show` prints it beside those items; the design's table stays as approved. 1.1.0 said "the spec's" and left which one open (a4bb688).

## [1.1.0] - 2026-10-09

A second way into a phased change, for one that starts from evidence rather than an idea, and
phase notes written when their phase starts. Minor: a new skill and script; a plan that
already has its notes runs as before.

### Added
- **`review-plugin`** (b78f708): reviews a whole plugin for what is wrong with it. Agrees the goal and the units with you from the plugin's shape, runs waves of unit agents that each read one role whole and write findings, and one reconcile agent that writes the edit list `site/notes/<slug>/<slug>-edits.md`; asks the decisions the findings leave open and commits. The orchestrating chat reads only script output. Templates under `templates/review/`; a workflow page, `site/workflows/review-sweep.md`.
- **`scripts/edits.py`** (b78f708): checks findings files and an edit list (fields, dependency cycles, open decisions, every finding cited), prints an index of one line per item and one phase's items whole, and checks coverage: every item in exactly one phase, dependencies respected.

### Changed
- **`plan-phases` plans from a design, an edit list, or both, and writes no phase note** (b78f708). The overview carries each phase's items, what it must not touch, the files other files parse and a new **Evals by phase** table; the eval sets are still written up front. An edit list is read through `edits.py`, never whole.
- **`run-phase` writes its phase's note when the phase starts** (b78f708), from the overview's row and the files as they are, finding each edit-list item's cited line where earlier phases moved it. A plan whose notes already exist reads them as before.
- `design-plugin` sends evidence-driven sweeps to `review-plugin` and designs only an edit list's **Needs a design** items, on the review's branch (b78f708).
- The overview template's Phases table gains Items and Must not touch columns; four `contracts.yml` claims bind the new templates to their readers (b78f708).
- Eval fixtures moved into per-plan folders; a toy review plan, `site/notes/fix/`, added; `evals/2026-10-09-review-plugin-and-notes-at-phase-start.md` (b78f708).

## [1.0.0] - 2026-10-09

1.0.0 because a path every typed skill reads has moved: a plan whose notes are still flat is no
longer found by `run-phase` or `run-phases`.

### Changed
- **Breaking: a plan's notes live in a folder per plan, `site/notes/<slug>/`** (735da32).
  `design-plugin` writes `site/notes/<slug>/<slug>-design.md`; `plan-phases`, `run-phase` and
  `run-phases` read and write the overview, the phase notes and the ledger beside it. A plan
  already in flight moves its `site/notes/<slug>-*.md` files into `site/notes/<slug>/`. The
  README, `site/flow.md`, the workflow pages and `build-site` follow.
- `build_site.py` renders only a plan folder's `<slug>-00-overview.md` under Notes, labelled
  `<slug> overview`; the design, phase notes and ledger stay out of the site. Loose files in
  `site/notes/` render as before (735da32). Rebuilding `dev-team` adds one page, the overview of
  its `remake_2.0` folder; `evals/2026-10-09-notes-folder-layout-mechanical.md`.

## [0.16.0] - 2026-10-08

### Added
- **`run-flow`** (86c7637, 23b3b69, fe86085): draws any run from its transcripts as a page in the browser pane; every agent on the chart opens to its full record (prompt, every step with full input and output, each Write's content and each Edit's old and new text, commits, hand-back). `--agent <type>` lists every run of one agent type across one chat or several (`--sessions`, `--branch`). `--explain` adds a short narration per unit from the new `run-narrator` agent (Sonnet 5.5).
- **A committed issue ledger** (1465e84, d50bc1f): every audit files its ERROR and WARN findings (and `definition` NOTEs) as issues under the audited plugin's `audits/issues/` with ids that stay (`DT-031`), an index, and the run report under `audits/runs/`. `scripts/issues.py` is the only writer; status is derived, never stored.
- **`fix-issues`** (6974d1e): fixes ledger issues from any chat on a worktree branch, records a Fix attempt with a `Verify:` line in each, and proposes the merge and the bump.
- **Rerun audits check prior fixes** (dd6af0f): `run-auditor` takes the fixed issues that apply to its piece and reports each held, recurred or not exercised with a step; `audit-run` tests whether the fix was in the code that ran, widens the selection for coverage, spot-checks every verdict, and writes a Checks line per issue. The chart marks held and recurred on the boxes.
- `dev-team/audits/` seeded from the ca48b249 audit: 27 issues (1984aa1).

### Changed
- `trace.py` and `flow.py` live at `skills/run-flow/scripts/`; `audit-run` runs them from there (86c7637). Running them by hand from the old path no longer works.
- An audit makes one more commit (`audits/`) in the checkout it runs in, and its eval log is short: the issue ids by outcome and a link to the run report (d50bc1f).
- `bump-version` stamps `fixed_in` on the issues a release carries, when the plugin has `audits/` (6974d1e).

## [0.15.0] - 2026-10-01

### Added
- **`run-evals` names its plugin root** (2c0a04f): `init`'s manifest gives every run a `plugin_root` and the iteration a `baseline_plugin_root`, and the executor prompt tells the executor to read every `${CLAUDE_PLUGIN_ROOT}` path under it.
- **`run-evals` warnings** (2c0a04f): `init` warns, on stderr and in the manifest's `warnings`, when `previous` fell back to HEAD and when the baseline is identical to the working tree. It still exits 0.
- **`run-evals` rules for its agents** (2c0a04f): an executor ended by an API error is rerun once; grader material is not staged where an executor may read; every eval agent runs on Sonnet 5.5 unless you name another model (`VERSIONING.md`).
- **`plugin-anatomy` facts** (2c0a04f): inside a subagent a hook's `transcript_path` is the parent's, with the subagent transcript's own path and `agent_transcript_path` on `SubagentStop`; `claude -p --model sonnet` was Sonnet 5 in CLI 2.1.283 while the Agent tool's `sonnet` was Sonnet 5.5; a subagent's Write is refused for a `.md` whose name starts `analysis`, `report`, `summary` or `findings`. All `[proven]` by dev-team logs.

### Fixed
- **The baseline snapshot is the whole plugin** (2c0a04f): it used to hold only the target's directory, so a baseline that read another skill of its plugin got the working tree's copy and a change there showed on both sides. `evals/` is left out. Eval: mechanical 15/15 vs 6/15, probe 6/6 vs 2/6 (`evals/2026-10-01-run-evals-harness-fixes.md`).
- **Executors can no longer read what they are graded on, or share a scratch copy** (2c0a04f): the executor prompt forbids reading the iteration outside its own run directory and `evals/sets/`, requires a fixture copy to live in its own `mktemp -d` directory, and makes the first tool call a Read of the target.
- **`previous` in a clone with no local `main`** (2c0a04f): it also tries `origin/main` and `origin/master` before falling back to HEAD.
- **Blind comparators get only what they can check** (2c0a04f): `blind` withholds expectations that name the transcript, which a comparator does not see, and prints how many as `withheld_expectations`.
- **`plugin-anatomy`: what reaches an agent's caller** (2c0a04f): with `SubagentHandback` the caller receives the agent's first hand-back and nothing after it; a second call is refused. 0.12.1 said "the last hand-back" and that an agent "must hand back again", which was wrong (`evals/2026-10-01-handback-delivery.md`).

### Changed
- **`plugin-anatomy`: the 20-subagent limit is proven** (2c0a04f): the 21st spawn fails and is not queued.

## [0.14.0] - 2026-09-29

### Added
- **`run-phases`** (fa3e6a7): `/plugin-dev:run-phases <slug> [--through N]` drives a plan from one chat. It runs one fresh agent per unfinished phase, in series, each doing `run-phase`, relays every review stop, question and bump proposal to you, resumes the same agent with your answer, and checks each phase's commit, clean tree and `done` row before the next. The agent is a subagent reading `run-phase`'s file, or, where `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is below 2 (cloud sessions set 1), a headless `claude -p` session with its own `--session-id`, resumed with `--resume`. Eval: 8/8 vs 3/8 (`evals/2026-09-29-run-phases.md`).
- **`plugin-anatomy` facts** (fa3e6a7): the spawn-depth variable and that cloud sessions cap it at 1; a headless child needs its own `--session-id` to be resumed. Both `[proven]`.

### Fixed
- **skill-creator in a cloud session** (fa3e6a7): `run-evals`' `locate-skill-creator` also searches `~/.claude/skills/synced/*/skill-creator` and `/mnt/skills/*/skill-creator`, so a claude.ai/code session gets the grader, benchmark and viewer instead of inline grading.

## [0.13.0] - 2026-09-29

### Added
- **`audit-run` finds a chat by its title** (2bb54d9): `/plugin-dev:audit-run <words from the title>` resolves the chat the sidebar shows by that name, and lists the matches when there are several. `trace.py find` prints each session with its title, project, span and length, agent count, the commands actually typed, and `fork of <id8>` for a forked or resumed chat. Headless eval sessions are hidden unless `--all`.
- **Workflow page "Checking a run"** (10ed049): an 8-hour `run-package` chat audited end to end, and how the skill differs from the `run-auditor` agent.

### Fixed
- **A forked chat is audited whole** (2bb54d9): its trace finds the agent transcripts left under the original session, which it used to miss (105 of 110 on a real fork).
- **`find` counts** (2bb54d9): commands only where typed, not quoted in tool output, and agents no longer double-counted.

### Changed
- **Plugin version per segment and per unit** (2bb54d9): a chat resumed after a plugin update is checked against the version each part ran on.

## [0.12.1] - 2026-09-29

### Changed
- **`plugin-anatomy` records what reaches an agent's caller** (eda16c0): with a `SubagentHandback` tool, the caller receives the last hand-back, not the last turn, and a `SubagentStop` hook that exits 0 ends the agent with no further turn. It is marked proven by dev-team's audit of a real run.

## [0.12.0] - 2026-09-29

### Added
- **`audit-run`** (482d74a): a typed skill that audits a real run of a plugin's workflow from
  its session transcripts, holding it against the plugin's own agent and skill files at the
  version that ran. `scripts/trace.py` rebuilds each agent spawned, the prompt it was sent,
  every tool call, hook block, commit and hand-back. Commits it cannot tie to the agent's own
  files are marked unconfirmed. Findings cite a trace step and a `file:line` and are classed by
  fault, and every ERROR is spot-checked before it is reported. `--units new` re-audits only
  newly finished agents, to watch a run in progress.
- **`run-auditor`** (482d74a): plugin-dev's first agent. It audits one unit, one driver
  segment, or the whole run for cross-agent consistency, and writes one findings file.
- **The run as a flow chart** (7797882): `flow.html` and a Flow section in `run.md`. Waves of
  agents run in parallel or in series; each column is one section, with its runs and review
  rounds; each review is coloured by its verdict with its counts; bands mark where the driver
  asked the user; audit ERROR badges show after `trace.py flow`.
- **`contracts.yml` checks agent frontmatter** (482d74a) against `plugin-anatomy`'s key list.
- **`evals/sets/audit-run.json`** with a planted-defect fixture and a known-shape flow fixture
  (482d74a, 7797882).

### Changed
- `VERSIONING.md` and `CLAUDE.md`: the plugin now has one agent, `run-auditor`, on `inherit`.

## [0.11.0] - 2026-09-26

### Added
- **`site/flow.md`** (73013a4): the site's orientation page. It covers which file is the truth
  for each question and which wins when two disagree, how facts flow from the docs through
  `plugin-anatomy`, the chat-by-chat loop, the hand-offs, and every point where you are asked.
- **`owner_form: markdown` for `check-contracts`' `headings` claims** (85df293): a document
  template's own `##` headings can own a section list, with fenced code skipped.

### Changed
- **The design template is the one list of the design's sections** (85df293).
  `design-plugin` no longer repeats them; the contract `plan-phases` is checked against now
  reads `templates/phases/design.md`.
- **`run-evals` runs trigger evals before behavioral ones** (3f3acfb), because `run_loop` may
  rewrite the `description:` a behavioral run reads.
- **A new plugin's `CLAUDE.md` points to the repo root's** for the shared protocol instead of
  restating it (3f3acfb). `build-site` says a change needing a rebuild also updates the
  authored pages it affects.
- **The README and the three workflow pages follow `design-plugin` and `plugin-anatomy`**
  (cd56a94). The README's workflow-skill rule now includes `disable-model-invocation: true`,
  and the phased-change page's worked example points to plugin-dev's own `0.9-evals` notes.

### Fixed
- **Phase 0 can be completed when the design assumes no platform facts** (85df293).
  `plan-phases` now writes its row `done` in that case, and `in progress` with the evals listed
  otherwise; `run-phase` treats that in-progress row as its work, not an interrupted chat.
  Before, nothing marked a fact-free phase 0 done.

## [0.10.0] - 2026-09-26

### Added
- **`design-plugin`**, split out of `plan-phases` (bdd8340). It owns the whole design
  discussion: interview rounds, composing jobs into loops (each loop's unit of work, what
  strengthens it, where every input comes from, the files where loops meet), one flow chart
  per workflow plus a system chart for approval, then a writeup for approval. It commits the
  approved design as `site/notes/<slug>-design.md` on a new branch. The composing method and
  the chart and page rules live in its `references/`.
- **`plugin-anatomy`**, the source of truth for plugin components (c4c1404). It has a routing
  guide for which component a responsibility belongs in (skill, agent, hook, MCP server,
  script, config) and one reference each for skills, agents, composition, hooks, MCP, the
  manifest, the rarer components and edge cases. Every fact is marked `[docs]`,
  `[proven: …]` or `[unconfirmed]`, read against the docs for Claude Code 2.1.270.
- **A `frontmatter` check kind in `check-contracts`** (c4c1404). It reads its allowed and
  ignored-in-plugins key lists from `plugin-anatomy`, and fails on a misspelled key or a key
  plugin agents ignore (`hooks`, `mcpServers`, `permissionMode`, `initialPrompt`) at its
  `file:line`. plugin-dev declares it for its own skills.
- **`templates/phases/design.md`**, and `plan-phases`' eval-writer prompt: one subagent per
  target writes that target's eval set, all in parallel.
- **Eval sets**: `design-plugin.json` (three domain evals moved from `plan-phases`, a
  research-scientist two-loop eval, a through-writeup eval), `plan-phases.json` rewritten (from
  a fixture design; a planted gap it must ask about), and `plugin-anatomy.json` plus its
  trigger set. Only the mechanical and load checks have been run:
  `evals/2026-09-26-design-plugin-split-mechanical.md`,
  `evals/2026-09-26-plugin-anatomy-and-frontmatter-check.md`.

### Changed
- **`plan-phases` starts from the design file, in a fresh chat** (bdd8340). It no longer
  interviews or proposes. It reads the design alone, asks about any decision the design did
  not take, shows the phase split for approval, writes the notes and ledger, and fans out the
  eval writers. **`plan-phases --new` is gone:** start a new plugin with
  `/plugin-dev:design-plugin --new <name>`, then run `/plugin-dev:plan-phases 0.1` in a new
  chat.
- **`run-phase` reads the design first**, reads a component's `plugin-anatomy` reference
  before writing it, and writes proven platform facts back to it. Plans written before this
  release have no design file; their overview still carries the why.
- **The overview template is slimmed** to what the design turns into (contents tree, parsed
  files, phases, breaking changes). The why, decisions, flow and non-goals live in the design.
- `new-plugin`, `bump-version`, `run-evals`' eval kinds, the README and the workflow pages
  follow the new flow and point to `plugin-anatomy`.

## [0.9.3] - 2026-09-21

### Fixed
- **The desktop app lists plugin-dev again** (91dcf5c). claude.ai, which the desktop app
  syncs marketplaces through, rejected the plugin twice where the CLI accepted it: "Zip must
  contain exactly one plugin.json. Found 2." for the `run-phase` eval fixture's manifest, then
  "SKILL.md description cannot contain XML tags" for `run-evals`. The fixture's manifest now
  ships as `evals/fixtures/toy-plugin/.claude-plugin/plugin.json.fixture`, renamed back in the
  eval's temp copy by `evals/sets/files/run-phase/review-approve.md`; `run-evals`'
  description drops `<skill>`, `<agent>` and `<target>`.

### Added
- **A contract forbidding a tag in any skill or agent description** (91dcf5c), so
  `check-contracts` catches the second rejection before claude.ai does:
  `evals/2026-09-21-description-xml-tag-contract.md`.

## [0.9.2] - 2026-09-21

### Fixed
- **Ordered lists on the site count the way their author wrote them** (e5f186f).
  `mdx_truly_sane_lists` discards a list's starting number. A list resumed after an aside
  markdown cannot express as a marker — `plan-repo`'s `2b.` — restarted at 1, so its Steps
  read 1, 2, 1, 2, 3, 4, and `plan-package` repeated a 1; a list written from `0.` — the
  `implementer`'s Procedure, whose own prose says "step 0 below" — renumbered to 1, putting
  all fourteen steps one off from every reference to them. Both predate 0.9.1, which fixed
  list *structure* and not counting. 64 of 64 pages across both bundles now render every
  list exactly as GitHub does, up from 58:
  `evals/2026-09-21-build-site-list-numbering.md`.

### Changed
- **The site renders with stock `sane_lists`; `mdx_truly_sane_lists` is dropped** (e5f186f).
  That extension was only there to read the 2-space nesting these files use, which
  `build_site.py` now normalizes away — it re-indents each generated page to
  Python-Markdown's own 4 spaces instead of 2. One fewer third-party dependency to install.
  A plugin that pins its own `site/mkdocs-base.yml` to `nested_indent: 2` would need the
  same swap; none does today.


## [0.9.1] - 2026-09-21

### Fixed
- **`build_site.py`: list indentation is normalized on the way into `site/docs/`** (e900d88).
  Python-Markdown reads list nesting at one fixed width; the sources here nest at whatever
  the marker is wide, which is what GitHub does. An ordered item's 3-space continuation kept
  a stray space and swallowed every item below it — `plan-phases` §Compose the workflows lost
  items 3–7 into a paragraph. Each page is now re-indented to one width, a marker pressed
  straight against a paragraph gets a blank line above it, and lists inside blockquotes are
  normalized too. Sources are untouched. Checked against a CommonMark render of every page in
  both bundles: `evals/2026-09-21-build-site-list-normalization.md`.


## [0.9.0] - 2026-09-20

Evals become a thing the kit does, rather than a thing each chat improvises. `run-evals` is
the loop; every skill and agent gets a committed set that outlives the plan that created it;
`plan-phases` specifies each phase's evals against it and `run-phase` runs them and stops for
your review. Planned and built with `plan-phases`/`run-phase` themselves — the design set is
`site/notes/0.9-evals-*.md`, one commit per phase, each with its evals beside it.

### Added
- **`run-evals`, an automatic skill: the eval loop** (5fdfdd9). One target, one committed set,
  one iteration. Mechanical checks, then a load check, then behavioral runs — the working tree
  and a baseline in parallel, each writing `outputs/` and a `transcript.md`, one grader per run
  quoting evidence per assertion, a benchmark and the viewer. The grader, benchmark, viewer and
  trigger scripts are skill-creator's, found where they are installed, with an inline fallback
  that says so in the log when they are not. `references/eval-kinds.md` is the one list of the
  five kinds (`mechanical`, `load`, `behavioral`, `trigger`, `platform-fact`);
  `scripts/eval_workspace.py` lays out the workspace skill-creator's scripts expect. Evals:
  `evals/2026-09-19-run-evals-platform-facts.md`,
  `evals/2026-09-19-run-evals-first-loop.md`.
- **Committed eval sets, one per target** (5fdfdd9, c76777a). `evals/sets/<target>.json` holds
  each eval's prompt, expectations, baseline and scripted-answer sheet, with `added_in` naming
  the change that added it, so the next change to that target reruns it as regression.
  `eval_workspace.py validate` enforces the shape.
- **Trigger evals and a guarded description optimizer** (29b317b). For a skill the model
  invokes itself, `evals/sets/<target>.trigger.json` measures how often its description is
  picked for queries that should invoke it and left alone for near-misses. `run_loop` may
  rewrite a description below 0.9, and its best is applied only under a guard: the held-out
  score must beat the current one, every outside-a-plugin query must still not trigger, and the
  description's scoping clause must survive. Evals:
  `evals/2026-09-19-trigger-sets-validate.md`,
  `evals/2026-09-19-trigger-rates-automatic-skills.md`.
- **Blind comparison for a changed target** (2f256ed). When both configurations pass everything
  the pass rates stop separating them, so `eval_workspace.py blind` stages each eval's two
  output directories as `A` and `B` in a random order, keeps the key out of every prompt, and
  asks skill-creator's comparator which is better. A loss is reported as a loss. Eval:
  `evals/2026-09-20-blind-comparison.md`.
- **`dev-team` gets eval sets** (71cd13e). `dev-team/evals/sets/{implementer,researcher,documenter}.json`,
  seeded from its own eval logs, so its next change has regression tests to rerun. Eval:
  `dev-team/evals/2026-09-20-implementer-security-review-sets.md`.

### Changed
- **`plan-phases` specifies each phase's evals** (f688731). Every phase note gains an `## Evals`
  table — ID, kind, target, baseline, which evals of the target's set, and the pass bar — and
  the phase-0 commit writes those evals into `evals/sets/`, so a phase arrives with its tests
  rather than inventing them. `references/example-phase.md` is the worked note; the phase
  template follows. Eval: `evals/2026-09-19-plan-phases-evals-table.md`.
- **`run-phase` runs the evals and stops for review** (a0a381f). At the note's Evals step it
  invokes `run-evals` once per target, fixes and reruns once if a bar is missed, records a
  Deviation if it is still missed, and does not commit until you have looked at the outputs.
  `log-eval` entries gain `**Set:**`, `**Iteration:**`, `**Baseline:**`, `**Pass rate:**` and
  `**Trigger rate:**`. Eval: `evals/2026-09-19-run-phase-evals-and-review-gate.md`.

### Verified
- **Both sets rerun end to end against `plugin-dev-v0.8.0`** on the finished branch:
  `plan-phases` 98.5% vs the baseline's 73.5%, `run-phase` 100% vs 85.5%. The difference is
  carried by the two evals this change added — `plan-phases` eval 4 (7/7 vs 0/7) and
  `run-phase` eval 1 (7/7 vs 5/7); the rest is regression cover 0.8.0 also passes. Trigger
  rates on the five automatic skills: 1.00 · 1.00 · 0.90 · 1.00 · 0.95, no description
  changed. Evals: `evals/2026-09-20-end-to-end-0.9.0.md`,
  `evals/2026-09-20-release-checks-0.9.0.md`, `evals/2026-09-20-trigger-rates-rerun.md`.
- **`run-phase` gained one clause the end-to-end run forced.** `run-evals` step 7 requires a
  weak expectation to be corrected in its set "in this change"; `run-phase`'s "only this
  phase's edits" forbade it. The eval sets a phase's own `run-evals` run reads are now
  explicitly in scope for expectation corrections — the target's behavior still is not.

### Breaking
1. `run-phase` now stops before committing when the phase ran a behavioral eval, until the
   user has reviewed the viewer. Mechanical-only phases commit as before.
2. `run-evals`' trigger optimizer may rewrite the `description:` of a skill the model invokes
   itself; each rewrite is logged with the trigger rate before and after.
3. Plugins get a gitignored `evals/workspace/`; new plugins get it from the template.
4. `templates/phases/phase.md` gains a `## Evals` section; notes written before 0.9 still run.

## [0.8.0] - 2026-09-19

### Changed
- **`plan-phases` composes jobs into shared layers before it proposes** (72712ec). A new
  *Compose the workflows* step designs from the unit of work a practitioner reads one at a
  time: per-unit agents fanned out in parallel (extract), one status file per entity that
  every job reads (synthesize), a comparison against peers or baseline that is core by
  default (compare), and thin typed commands on top (act). Agents are methods shared across
  jobs; the proposal states each job's first-run and warm-run cost and each shared file's
  rules (what it cites, never claims, when it goes stale). Suggestions attach and never
  carry the core; components are labelled *asked*, *composed* or *suggested*.
- **The proposal is a page, not code in chat.** Published as an Artifact with the flow
  chart rendered; the page declares UTF-8 and loads mermaid from cdnjs with a
  theme-aware, full-size init, so it also renders as a downloaded file. The chart is
  budgeted to about 20 nodes and 30 edges, grouped by layer. README and both phased
  workflow pages follow. Eval: `evals/2026-09-19-plan-phases-compose-layers.md`.

## [0.7.0] - 2026-09-19

### Changed
- **`plan-phases` expands the idea before it plans** (1e0b2a0). It reads first, then
  interviews in themed rounds of 2–4 questions (recommendation first, each round built on the
  last answers) until every component can be named. It then shows a proposal in chat — the
  idea restated, a mermaid flow chart of every command, skill, agent and file, a components
  table, decisions, a phase outline, non-goals — with its own suggested additions dashed and
  accepted or rejected by name. No branch, scaffold or file exists before the user approves;
  the approved proposal becomes the overview. `templates/phases/overview.md` gains an Origin
  column under Decisions taken and a line for declined suggestions under Non-goals; the
  README and both phased workflow pages follow. Eval:
  `evals/2026-09-19-plan-phases-interview-and-approval.md`.

## [0.6.0] - 2026-09-18

### Added
- **`plan-phases`** — a typed skill that splits a change too big for one chat into phases: a
  branch, `site/notes/<slug>-00-overview.md`, one note per phase with its own evals, and a
  progress ledger, committed as phase 0. `--new <name>` from the repo root starts a whole
  plugin the same way, with `new-plugin`'s scaffold as its phase 0. Templates in
  `templates/phases/`.
- **`run-phase`** — a typed skill that does the next unfinished phase in a fresh chat: exactly
  that note's edits, the checks, the phase's evals logged, one commit, the ledger updated, then
  stop.
- **`plugin-dev`'s own `contracts.yml`** — no bare `/<name>` command in the bundle, the README's
  skills table names every skill, and every typed skill is in `site/site.yml`'s run order. Each
  claim watched fail on a planted defect: `evals/2026-09-18-phases-skills-contracts.md`.
- **`site/`** — the bundle's reading site, with three workflow pages (small change, phased
  change, new plugin) that the README summarizes.

### Changed
- `new-plugin` hands a plugin with agents, or more than a couple of skills, to
  `plan-phases --new` after the scaffold instead of writing it in the same chat.
- The root `CLAUDE.md` and the plugin `CLAUDE.md` template describe the two typed skills, and
  the root `CLAUDE.md` gains *Working in one plugin*: stage by plugin path, never `git add -A`,
  and commit-bearing steps run in Claude Code, not Cowork.

## [0.5.0] - 2026-09-17

### Added
- **`near: <n>` on a `forbid` claim** — scopes `all_of` and `unless` to the matched text plus n
  characters either side instead of the whole line. Almost every exemption means "this occurrence
  is fine", not "this line is exempt", and an exemption lives exactly where the thing it pardons
  is discussed — which is where a violation would be written. `dev-team`'s `scripts/` claim, the
  oldest in the repo, had eight line-scoped exemptions pardoning ten lines outright: a genuine
  `scripts/` promise planted on any of them passed. Eleven of eleven planted violations leaked
  before, all eleven caught after, with the legitimate lines still silent —
  `evals/2026-09-17-forbid-exemption-scope.md`. One residual is documented rather than hidden: a
  violation inside the window, in the same clause as its exemption, is still pardoned.
- `check-contracts` states the scoping rule first among the three things to know about writing a
  claim, with both tighter options (a smaller window, or a negative lookahead in the pattern,
  which exempts a token and has no window), and says plainly that a claim nobody has watched fail
  is not enforcement — adding or changing one means planting the defect and running `log-eval`.

### Fixed
- **A skill's `references/*.md` was always filed under *Knowledge skills*,** whatever kind of
  skill owned it, so `dev-team`'s `shape-brief / brief` sat six entries away from
  `/dev-team:shape-brief` — while the page itself was written to `skills/workflow/`. A reference
  file is now listed with its owner, directly after it. Filing a workflow skill's reference under
  Knowledge separates the page from the only thing that explains it, and implies an agent reads
  it on its own.
- **`site_title` defaulted to the plugin's name with hyphens replaced by underscores,** so
  `dev-team` rendered as `dev_team`. It defaults to the name as written. This was the source of a
  wrong spelling that looked bundle-local; `dev-team` has dropped the explicit `site_title` it
  needed as a workaround, which is what proves the default.

Nav diffed across both bundles before and after — three changed lines in `dev-team`, one in
`plugin-dev`, each accounted for:
`evals/2026-09-17-build-site-reference-placement.md`.

## [0.4.0] - 2026-09-17

### Added
- `names_listed` gains **`form`** — how the target list cites a name, so a list is checked where
  it lives rather than reformatted to suit the checker. `code` (backticks, the default) for
  prose and tables, `tree` for an indented `── name/` branch in a fenced directory tree where
  backticks would render literally, `list` for a YAML sequence or Markdown bullet.
- `names_listed` gains **`where`** — which directories the list answers for, read from their
  `SKILL.md` frontmatter. A list covering one class of skill is checked against that class, so a
  knowledge skill is not reported missing from a list of workflow steps and a second list of
  which skills count never has to exist. A `where` that matches nothing is a `FAIL`, not
  `0 names, all listed`: a typo would otherwise switch the claim off while still printing PASS.
- `skills/**/*.py` joins the default authored set. A script a plugin ships is authored too, and
  it is the one file that prints to a person rather than to a model — which is how `dev-team`'s
  `status.py` was found printing unnamespaced commands.

### Changed
- `check-contracts` documents both keys, with a table for `form`, and states the line-level
  `unless` hazard as a design rule rather than a formatting caveat: one exempt phrase pardons
  everything else on its line, and an exemption tends to live exactly where the thing it pardons
  is discussed. Prefer a negative lookahead in the pattern, which exempts a token.

### Fixed
- `form: list` anchored a bullet to end-of-line, so a YAML entry with a trailing comment read as
  missing. The checker was fixed rather than the comment removed: a claim that dictates how the
  file it checks may be annotated will be worked around.

Tested, 15 cases over two rounds —
`evals/2026-09-17-contract-sweep-names-listed-where-form.md`. Round 1 found `dev-team`'s D2, D3
and D5; round 2 exists because round 1 tested the command claim with a bare command alone on its
own line, which is not how one gets written, and so missed the `unless` leak above.

## [0.3.0] - 2026-09-17

### Added
- `check-contracts` + `scripts/contract_sweep.py` — checks the cross-file claims a bundle's own
  prompts act on, which nothing else in a plugin verifies: a heading one file parses against
  the template another owns, a rule one file states and another contradicts, a list of names
  that goes stale when a directory changes. Config-driven like the site builder: each bundle
  declares its claims in its own `contracts.yml`, absent means nothing is checked. Owner
  templates are parsed out of the owner file rather than restated, so renaming a heading moves
  the check with it. Exit 0 all pass, 1 any fail, 2 nothing declared.
- Verified against planted defects, one per check kind —
  `evals/2026-09-17-contract-sweep-negative.md`. Two lessons about writing claims (a broad
  `unless` becomes an escape hatch; the checks are line-based, so an exemption phrase must fit
  on one line) are written into the skill.

### Changed
- `CLAUDE.md` carries the shared-script rule for `contract_sweep.py` alongside the one for
  `build_site.py`: a change to it gets both runs — the real bundle, which must still pass, and
  a defective copy, which must still fail.

## [0.2.0] - 2026-09-17

### Changed
- `scripts/build_site.py` — a skill only a person can start
  (`disable-model-invocation: true`) is now a **Workflow skill**, not a Knowledge skill.
  A step that runs inline in the conversation rather than forking into an agent was being
  filed as material an agent reads, and its `workflow_skills_order` entry had no effect.
  `dev-team` rebuild: `status` and `shape-brief` moved into Workflow skills, 48 pages.
- `build-site` — the run command now has a fallback for sessions where the plugin is not
  installed (`CLAUDE_PLUGIN_ROOT` unset): `python3 ../plugin-dev/scripts/build_site.py`.

## [0.1.0] - 2026-09-16

### Added
- `build-site` skill and `scripts/build_site.py` — the generic site builder, extracted from
  `dev-team/site/build_site.py` and de-hardcoded. Verified byte-identical against
  `dev-team`'s existing site; see `evals/2026-09-16-build-site-extraction.md`.
- `bump-version` skill — the semver, CHANGELOG, tag and marketplace procedure, plus the
  `model:` field policy, extracted from `dev-team/VERSIONING.md`.
- `log-eval` skill — the eval record convention, extracted from `dev-team/evals/README.md`.
- `new-plugin` skill and `templates/` — scaffolds a plugin as a subdirectory of this repo.
