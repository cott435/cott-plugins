# dev-team

A Claude Code **plugin** that plans, builds, reviews and documents a Python monorepo, one
section of one package at a time. Six specialist agents each answer one question: the
architect writes the contracts, the designer designs a section, the researcher probes an
external source, the tester turns a design into failing intent tests, the implementer builds
the section, the reviewer judges it. One driver, `/dev-team:run-package`, runs in your
conversation and spawns every one of them over a ready set it derives from disk each
iteration. Hooks run every mechanical check, so no lint error, failing test or lowered bar
reaches a reviewer.

You drive it. Every workflow skill is `disable-model-invocation: true`, so Claude never starts
one on its own — you type them. It plans a **repo of packages** — `data` → `analysis` → `ml`,
say — where each package's `surface` section, built last, publishes an `interface.md` that the next
package is planned and built against. A single-package repo is the same thing with one row in
the Packages table.

## Contents

```
dev-team/
├── .claude-plugin/
│   └── plugin.json           the plugin manifest
├── agents/
│   ├── architect.md      writes and edits contracts: repo, package, change files, the package close
│   ├── designer.md       designs one section from its contract row — new, document or delta mode
│   ├── researcher.md     probe: one api or dataset → docs/sources/<source>.md · extract: one legacy row → a project skill
│   ├── tester.md         intent tests for one section, from its design — never from its code
│   ├── implementer.md    builds one section; the `surface` section is the package's public surface
│   ├── reviewer.md       judges one section: conformance, correctness, a diff-scoped full round, or defer
│   ├── documenter.md     package READMEs, docs/index.md, root README; Known gaps from status.py --repo
│   └── curator.md        surveys an old repo into docs/legacy/inventory.md; coordinates researchers
├── hooks/
│   ├── hooks.json            registers the five hooks below
│   ├── format_on_edit.py     PostToolUse: ruff on every .py edit by the implementer or tester
│   ├── sync_decisions.py     PostToolUse: a section's decisions inbox folded into docs/decisions.md under a lock
│   ├── gate_on_stop.py       SubagentStop: the implementer may not finish while its section's checks are red; --report by hand
│   ├── guard_writes.py       PreToolUse: each role writes only where its job is; an implementer only in its section
│   └── guard_bash.py         PreToolUse Bash: no repo file written from the shell; locked.py and entry_point.py exempt
├── pyproject-lint-config.toml  merge into the root pyproject.toml; enforces the hard limits
└── skills/
    ├── shape-brief/        (inline)        idea → docs/brief.md, discussed with you: now / later / out
    ├── set-constraints/    (inline)        the quality bar → docs/constraints.md, the stop gate's spec
    │   └── references/                     the constraints template + vendored constraint-driven-development (MIT)
    ├── extract-legacy/     → curator       old repo → inventory (stop) → project skills, one per kept row
    ├── plan-repo/          → architect     the repo contract: write, extend, or --fix
    ├── plan-package/       → architect     one package contract, ending with the surface row, with Call paths; edits classified
    ├── run-package/        (inline)        the driver: <pkg> [<section>] [--step] [--defer] [--serial]
    ├── pair/               (inline)        one built section, edited with you turn by turn; wrap-up hands it back
    ├── probe-source/       → researcher    re-probe one source for one section after the world changed
    ├── sync-plan/          → architect     the package close: approved deviations and change files into the contracts
    ├── map-repo/           → architect     adopt an existing repo: package contracts in parallel, then the repo contract
    ├── finalize-project/   → documenter    package READMEs, docs/index.md, root README
    ├── status/             (inline)        every section's state, the ready set, the next command
    │   └── scripts/status.py               the one state derivation; the driver, the hooks and the documenter run it too
    │       + locked.py                     a mkdir lock around the three shared edits (uv add, an entry-point line, the .gitignore block)
    │       + entry_point.py                one entry-point line in the package pyproject.toml, under the deps lock
    ├── planning-templates/   headings for every document the loop writes and parses, the decisions inbox included
    ├── project-structure/    layout, size limits, config placement        (preloaded: 5 agents)
    ├── python-style-guide/   inside a file: docstrings, function shape, … (preloaded: impl, test, review)
    ├── python-implementation/ splitting mechanics, config code            (invoked on demand)
    ├── workspace-scaffold/   pyproject / import-linter / mkdocs / CI skeletons (invoked on demand)
    ├── security-review/      checklist                                    (implementer on triggers, reviewer)
    ├── test-driven-development/      red-green-refactor, pytest (vendored, MIT)
    ├── debugging-and-error-recovery/ root-cause triage (vendored, MIT)
    └── git-workflow-and-versioning/  §Project convention, the commit rule (vendored, MIT)

site/                         the authored parts of the reading site — see site/README.md
CLAUDE.md                     how to work on this repo's own source
CHANGELOG.md                  one entry per tagged release
VERSIONING.md                 this plugin's versioning decisions (policy lives in plugin-dev)
evals/                        test runs against this plugin's own agents and skills
```

Versioning, eval logging and the site builder are shared with every other plugin and live in
the **`plugin-dev`** plugin, not here.

**Agents hold procedures; skills are entry points.** Every step's procedure lives in the agent
that does it: the driver spawns an agent with a block of `Field: value` lines that are that
agent's own **Inputs**, and nothing else. A typed skill says which agent runs and on what. Domain
knowledge — how *you* want a Postgres schema designed, how your vendor clients are built —
belongs in your own project skills under `.claude/skills/`. The architect finds them (every
directory there that is not one of this plugin's skills, listed with `ls
${CLAUDE_PLUGIN_ROOT}/skills`), assigns each to a section as its `builds with`, and the designer
and implementer invoke them, so the same conventions apply at design time and at build time.

## One-time setup

1. Add the marketplace and install the plugin:
   `/plugin marketplace add cott435/cott-plugins` then
   `/plugin install dev-team@cott-plugins`. In Cowork: Customize -> Plugins ->
   Add marketplace, then Install.
2. **Verify with `/agents`** before the first run: the eight agents must be listed. If they are
   not, run `/reload-plugins` (or restart Claude Code). The driver stops on its first spawn if
   they are missing. User-level definitions in `~/.claude/agents/` override same-named plugin
   agents, so those must not exist for the plugin's versions to take effect.
3. Run in **auto** or **acceptEdits** mode. Not plan mode: subagents inherit your mode, plan
   mode is read-only, and nothing would reach `docs/`.
4. Every agent inherits your session model, so set `/model` before you start a run.
5. `/dev-team:status` at any time prints where everything stands and the exact next command.
6. The repo you build in is a git repository on a feature branch. Every run starts with the
   run gate (`status.py --run-gate`): not `main` or `master`, and a clean tree except
   `docs/decisions.md`, `docs/brief.md`, `docs/constraints.md` and `.claude/agent-memory/`,
   which you edit by hand between runs. Every agent run ends in one commit of exactly the files
   it wrote.
7. The five hooks run in every session the plugin is enabled in, and exit 0 outside a dev-team
   repo — one with a `docs/architecture.md`. They never touch your own editing: only the
   plugin's agents are checked.

## Which skill to run

```
rough idea, scope not settled               → /dev-team:shape-brief, then /dev-team:plan-repo
quality bar not written down                → /dev-team:set-constraints (any time before the first build)
new repo, nothing exists yet                → /dev-team:plan-repo, then per package, lowest first:
                                              /dev-team:plan-package <pkg>, then /dev-team:run-package <pkg>
existing repo, no docs/ yet                 → /dev-team:map-repo, then /dev-team:run-package <pkg>, lowest package first
docs/ exist but have drifted from the code  → /dev-team:map-repo again: every contract line is checked against the code
adding a package to a planned repo          → /dev-team:plan-repo "<what to add>", then /dev-team:plan-package <pkg>
a change to shipped code                    → /dev-team:plan-package <pkg> "<change>" (or /dev-team:plan-repo "<change>"),
                                              which writes docs/packages/<pkg>/changes/<slug>.md (one per
                                              affected package), then /dev-team:run-package <pkg>
the repo contract came out wrong            → /dev-team:plan-repo --fix "<what was wrong>" (or correct the brief with
                                              /dev-team:shape-brief, then /dev-team:plan-repo)
one step of one section by hand             → /dev-team:run-package <pkg> <section> --step PROBE|DESIGN|TEST|IMPLEMENT|REVIEW
sections that must edit one shared file     → /dev-team:run-package <pkg> --serial (the 2.1 loop: one kind per batch,
                                              one implementer)
iterate by hand on built code (a UI, say)   → /dev-team:pair <pkg>/<section>, then the next: line it prints
an API changed, a dataset was refreshed     → /dev-team:probe-source <pkg>/<section> <source>
rebuilding from an old, messy repo          → /dev-team:extract-legacy <old repo> (twice), then /dev-team:plan-repo
human-facing docs                           → /dev-team:finalize-project (safe any time; lists what is still open)
lost track                                  → /dev-team:status
check what a run's agents actually did      → plugin-dev's audit-run skill, typed in a fresh chat opened on this
                                              folder (plugin-dev's site: Workflows → Checking a run)
```

Each pipeline has its own page in `site/workflows/`, rendered under **Workflows** on the
reading site: a new repo, adding a package, rebuilding from legacy, changing shipped code, and
adopting an existing repo.

## Running a package

`/dev-team:run-package <pkg>` walks every section of one package to DONE — the `surface`
section designed and tested right after PLAN, from the contract, and built last, from the
shipped READMEs — then closes the package. It runs in your conversation and spawns every agent
itself as `dev-team:<agent>`, one layer deep; no state is kept anywhere but on disk.

**Call paths** (item 5 of the contract) fixes, per command, the frames from `cli.py` to each
external effect and a depth budget (8 unless a decided `D<n>` says more), before any section
is designed. The surface's design and intent tests are written right after PLAN from the
contract; every section's design carries a skeleton for each entry point a path names, with
`frames to effect`; the paths review runs `status.py --paths <pkg> --against-contract` and
fails a frame the contract does not list, or lists and the code lacks, as a break. A contract
written before 2.6 has no heading: the `surface` row keeps waiting for every section, the
review runs as in 2.5, and the next close writes the heading as built, with a change file for
each command deeper than 8.

1. **Run gate.** `status.py --run-gate <pkg>`: the branch, the clean tree, the contract exists.
   Then **scaffold**: when `status.py --scaffold <pkg>` says the workspace is missing (no root
   `pyproject.toml`, or no package `pyproject.toml` in a uv workspace), one implementer builds
   it first — the root with the plugin's lint rules, the package skeleton, `uv sync`, one
   commit with `uv.lock`. Every tester then writes and runs its intent tests inside the
   workspace, under the repo's own lint rules.
2. **State.** `status.py <pkg>` derives one state per section from the documents, the code and
   git (**The states**, below). A re-run a week later, after hand edits or a crash, picks up
   exactly where the files say.
3. **The ready set.** A section is ready when it is neither DONE nor BLOCKED and every
   section it depends on in the package is DONE — except `surface` at PLAN, DESIGN and TEST
   once the contract has **Call paths**: only its IMPLEMENT waits for every section. Each
   role's **Dependency READMEs** line is copied from `status.py --fields`, which lists only the
   READMEs that exist, so the early surface designer and tester are sent only those (often
   `none`) and build to the contract's **Section interfaces** for the rest. The driver spawns every ready row's step in
   one message — probes, designs, tests, implementers, reviewer pairs together, whatever step
   each row is at — with one exception: a PLAN row runs the architect alone, since it edits
   what designers read. Implementers run in parallel: the write guard confines each to its
   section, the stop gate judges each on its own paths, the marker and the decisions inbox are
   per section, and `locked.py` serializes the three shared edits (`uv add`, an entry-point
   line through `entry_point.py`, the `.gitignore` block).
   `--serial` restores the 2.1 loop, one implementer at a time: the first kind of step
   in the order PLAN, PROBE, DESIGN, TEST, IMPLEMENT/FIX, REVIEW.
4. **Branch** on each return's first line, `Result: done | blocked | stopped | spec-change |
   design-gap`. A tester's `design-gap` goes back to the designer with the tester's reasons
   (three for one section in one run is a question for you); a tester that finds two design
   items contradicting each other returns `spec-change` instead. A `spec-change` needs no
   relay: its entry is in `docs/packages/<pkg>/deviations/<section>.md`, and the next
   `status.py` re-opens the step it names.
   `blocked` and `stopped` are asked, whatever row the next `status.py` shows. A return is the
   agent's first hand-back, and the only one the driver receives: what an implementer does
   after it — a gate retry, a block, a third red attempt — reaches the driver as a row, since
   the stop gate writes every stop to the section's record and `status.py` reads it.
5. **Re-derive** and loop.
6. **The close.** When every section is DONE, the architect runs as `sync-plan`: approved
   deviations and pending change files go into the contracts, each verified against the code.
7. **Summary** — always the last message: sections, agent runs per role, the commit range, why
   it stopped, and `next:`, the exact command to type.

**The caps.** A review loop gets three rounds, two when a prior finding is unfixed. At the cap
the section is BLOCKED and the driver asks: *one more round*, or *defer*. `--defer` answers
*defer* without asking: the reviewer writes a `defer` report that moves the standing findings
to `docs/followups.md`, and the section is DONE.

**The ask step.** A decision with no assumption, a missing credential, a review cap or a third
`design-gap` stops the ready set for that section. The driver asks you once per block, writes
your answer into `docs/decisions.md` (`Decision:` and `Status: decided`) and runs the step
again. That ledger edit is the only file it ever writes, and it runs no git command that
writes. With nobody to ask — a headless run — it ends in the summary instead. Two more
questions come from the stop gate's record:

- **A section whose implementer blocked, or was let through after three red attempts,**
  after its hand-back: the row is BLOCKED with `gate …` evidence, and the driver quotes the
  record's `result:`, `FAIL` and `blocked:` lines and offers *run the implementer again*,
  *review anyway* or *stop here*. Neither answer touches `docs/decisions.md`; once a review
  round covers the code, the record is no longer read, so *review anyway* holds.
- **A package whose surface check fails** (`shipped: no (surface check FAIL)`, every section
  DONE): the driver quotes the `FAIL` lines of `status.py --surface <pkg>` and offers *fixed,
  retry* or *stop here*. The close waits until the check passes; the faulty rows are usually
  in sibling READMEs, which you correct.
- **A paths review that still requests changes at round 3** (`paths: round 3 (request changes:
  …) (cap)`): the driver quotes the line and offers *one more round*, which runs an
  implementer and a review for each section it names and then the paths review again, or
  *defer*, which moves the findings to `docs/followups.md`.

An answer that is none of the options — free text typed in place of a choice — ends the run
where it stands with the Summary. The driver does not act on the text; you read the Summary
and type what you want next.

`<section>` walks one section; `--step` runs one step of it once, whatever its state, which is
how *one more round* is typed by hand.

## The states

Every section is in exactly one state, the first rule that matches, derived by `status.py` on
every call and never stored:

| State | When |
|---|---|
| **BLOCKED** | an open decision with no assumption binds the section; or the review cap is hit (round 3, or round 2 with a prior unfixed); or the stop gate's record for the section's current commit says the implementer blocked, or was let through after three attempts, and no review round covers that code |
| **PLAN** | an open `spec-change:contract` entry names the section — the architect edits the contract and sets the entry `resolved` |
| **PROBE** | an `api:` source has no `## <pkg>/<section>` entry in its probe doc, or a `dataset:` source has no probe doc |
| **DESIGN** | no design; or an open `spec-change:design` entry (one written since 2.2 stays open until its `Status:` is `resolved`); or an open change file naming the section is newer than the design; or a probe doc it names lost or reworded a line the design was written against |
| **TEST** | no intent tests; or the design is newer than them; or an open `spec-change:test` entry; or an `approved` deviation's clause is cited by a test not yet regenerated |
| **IMPLEMENT** | no README (for `surface`, no `interface.md`); or the intent tests are newer than it (a regeneration commit, or one marked `intent tests current with design`, does not count); or the gate's record for the current commit says `not done`, a run that died between attempts |
| **REVIEW** | no review round; or round 1 lacks its `a` or `b` report; or the code is newer than the newest round's `Commit:`; or a `spec-change` verdict has no open entry left |
| **FIX n** | round `n` says `request changes`, under the cap, and nothing changed since; or the section is DONE and the package's paths review names it |
| **DONE** | the newest round approves and the code is not newer than its `Commit:` |

A package is **shipped** when its `surface` section is DONE, `status.py --surface <pkg>`
passes, and its paths review, against the contract's **Call paths**, approves (`paths:
approved`). A package whose check fails prints
`shipped: no (surface check FAIL)`; one whose commands have not been reviewed prints `shipped:
no (paths needed)` until `/dev-team:run-package <pkg>` has run the review. A round is the
set of reports sharing `-r<n>`; its verdict is the worst of them.

## Pairing on a section

Some changes can only be judged by looking at them — a UI, a report layout, a CLI's output —
and a loop of design, tests, build and review per nudge is the wrong tool for them.
`/dev-team:pair <pkg>/<section>` runs in your conversation: it reads what the section's
implementer would read (`status.py --inputs`, the same block the driver sends), briefs you on
the section's boundary, and edits the code turn by turn while you try it. Nothing gates the
edits in between. It starts only from REVIEW, FIX n, DONE or a review cap, never ahead of an
unfinished step.

When you say you are done, it wraps up: sorts every change by the clause it touches — none,
`deviation` or `spec-change:<level>`, by the implementer's own table — shows you the list,
writes the entries to `docs/packages/<pkg>/deviations/<section>.md`, updates the section README, runs the stop gate's
checks by hand (`gate_on_stop.py --report --base <start>`, so the next reviewer reads a gate
record of *this* code), commits once, and prints the `next:` command. From there it is the
ordinary loop: one review round for changes inside the design, a verdict on each deviation, or
the spec-change's level re-opened first.

## Hooks

`hooks/hooks.json` registers five, and each exits 0 outside a repo with `docs/architecture.md`.
The two guards also act in a repo with only `docs/brief.md`, so `plan-repo`'s agents are
guarded before the repo contract exists:

- **`format_on_edit.py`** (`PostToolUse` on `Write|Edit`) — for the implementer and the tester,
  on a `.py` file: `ruff format`, `ruff check --fix`, `ruff format`, then `ruff check`. What
  remains is shown to the agent; the edit stands. Until the repo has a ruff config of its own,
  it lints with `pyproject-lint-config.toml`, so intent tests written before the first
  implementer merges that block already meet it.
- **`sync_decisions.py`** (`PostToolUse` on `Write|Edit`) — on a write to a decisions inbox,
  `docs/packages/<pkg>/decisions/<section>.md`, by anyone: under the lock
  `.dev-team/locks/decisions/`, a `## D?` stub gets the next free number, is appended to
  `docs/decisions.md` and renumbered in the inbox; the central entry's `Applied:` lines that
  name the inbox's own section are made equal to the inbox's, so a line the section edits or
  removes is edited or removed centrally, while other sections' lines are untouched. Nothing
  else flows, and `Decision:` and `Status:` never flow at all.
  The numbering comes back to the agent as context (`D? → D14`). `--all` by hand merges every
  inbox (**Decisions**, below).
- **`gate_on_stop.py`** (`SubagentStop`, `^dev-team:implementer$`) — the implementer may not
  finish while its section is red. It reads the section from the spawn prompt's `Section:`
  line in the agent's transcript, and its diff is that section's paths since the section's
  last review `Commit:` (else the empty tree), so a sibling's work under parallel implementers
  is never its own. It runs the section's intent and unit suites — an intent failure tolerated
  only when the test cites the clause of a `proposed` or `approved` deviation — a **Guarded**
  grep of that diff, `status.py --surface` for the `surface` section and, for every other
  section, the per-section name check `status.py --surface <pkg> --section <section>` (each
  row of the README's **Entry points and interfaces** names one exported identifier, in
  backticks, and every `Public: yes` name is one the contract's **Public surface (intent)**
  names), so a README's author meets a bad row in its own run; then the **Floor** and
  **Enforced** rows of `docs/constraints.md` for the package (else the Toolchain commands of
  `docs/architecture.md`). A `repo`-scope pytest row is CI's: the record says `SKIPPED <row>:
  repo-scope pytest is CI's` and never runs it. A check whose every located failure lies
  outside the section's paths, or in an intent-test file (a lint, type or Guarded hit in the
  tester's lines), is `ELSEWHERE`, not `FAIL`: the implementer may not edit there, and the
  reviewer carries each such line to `docs/followups.md`. A failing
  intent test is still `FAIL`, since what fails is the code. Guarded's removed items are a
  test file that lost more `assert` lines than it gained, or more `pytest.raises`, counted per
  file, so a rewritten or moved assert is not a removal. An `xfail` cites a decision when its
  `xfail(` call, read to its closing bracket, holds a `D<n>` not followed by a digit (`D5:`,
  `D5_OPEN`), so a formatter's wrap is harmless.
  The package-wide rows share a time budget under the hook's timeout: a row that runs out of
  time is `TIMEOUT`, not `FAIL`. Every line goes to the section's own record,
  `.dev-team/gate/<pkg>/<section>.txt`: the header `dev-team gate — attempt n — <stamp> —
  section <pkg>/<section>`, then `commit: <short sha>` (the newest commit touching the
  section's code, unit tests and README), the check lines, and a last `result:` line. The
  reviewer reads it as its evidence, and `status.py` derives the row from it (**The states**);
  a record whose `commit:` is not the section's current commit is ignored. It lets the agent
  stop on a green run; on its section's marker `.dev-team/stop/<pkg>/<section>` (the
  implementer writes it when it stops `blocked` or `spec-change`; a sibling's marker is never
  read), which is recorded, not silent: `blocked` or `spec-change` in the header's attempt
  slot, the earlier attempt's check lines, a `blocked: <reason>` or `spec-change: <heading>`
  line, and `result: blocked` or `result: spec-change`; or on the third red attempt, counted
  per agent under `${CLAUDE_PLUGIN_DATA}/gate/`, which leaves the section BLOCKED until you
  answer. A FAIL the implementer cannot clear — in a file it may not edit, or false in its own
  file — is a block, with the gate line quoted in the marker. The implementer hands back once:
  after a retry it fixes, commits and ends its turn with the one line `Result: done`, and the
  record is what the driver reads. A retry amends only when
  `git log -1 --format=%s` starts with the section's own scope, else it is a second commit with
  the same trailer; from the second attempt the message names `debugging-and-error-recovery`.
  By hand, `gate_on_stop.py --report [--base <rev>]` runs the same checks over
  `<rev>`..working tree with no counter and no marker, writes the same records, and exits 1 on
  a FAIL; `/dev-team:pair` runs it at wrap-up.
- **`guard_writes.py`** (`PreToolUse` on `Write|Edit`) — each role writes only where its job
  is: the architect under `docs/` but not designs or reviews; the designer to designs, the
  ledgers and its section's decisions inbox; the researcher to `docs/sources/` and
  `.claude/skills/`; the tester to `tests/intent/` and fixtures; the reviewer to review reports
  and the ledgers it edits; the documenter to the READMEs and `docs/index.md`; the implementer
  everywhere but `docs/`, except the ledgers, the inboxes, its `interface.md` and its API page.
  An implementer with a `Section:` line is confined to its section's files — its code,
  `tests/unit/<section>/`, fixtures, its ledger and inbox, `.dev-team/tmp/`, and for `surface`
  also `interface.md`, the API page `docs/api/<pkg>/index.md`, the package `pyproject.toml` (its
  `[project.scripts]`), the root `pyproject.toml` and `mkdocs.yml`. A path under another
  section's `path` is that section's and is refused first, which stops `surface` at its
  siblings and a parent section at its nested ones. An entry-point line in the package
  `pyproject.toml` goes through `locked.py` and `entry_point.py`, so no section but `surface`
  has that file in scope. A scaffold run or an unreadable transcript falls back to the
  role-wide rule. Every role's globs cover the 2.2 paths, and the old locations stay writable
  for status edits. Nobody but the tester writes under `tests/intent/`, and a Write or Edit
  there that adds `# noqa`, `# type: ignore` or `# pragma: no cover` is refused.
- **`guard_bash.py`** (`PreToolUse` on `Bash`) — no dev-team agent writes a repo file from the
  shell: a redirect (`>`, `>>`) to anything but `/dev/null` or a path under `.dev-team/tmp/`
  (refused as `may not redirect to <target>: it is outside .dev-team/tmp/`; a researcher may
  also redirect to a path outside the repo, its scratch), `sed -i`, `tee`, and python code
  that opens a file for writing — as `python -c`, or as a
  here-document script (`python3 - <<'EOF'`) — are refused, with the rule on stderr; an
  `sh -c` script is checked like a command of its own. `locked.py` is the one way an
  implementer runs `uv add`, `uv remove`, `uv lock` or `uv sync`, or appends the `.gitignore`
  block (`sh -c "printf … >> .gitignore"`), holding `.dev-team/locks/<name>/` while the command
  runs; those are let through, and any other command wrapped in `locked.py` is checked as if it
  were not. The third shared edit is an entry point: `locked.py deps -- python3
  …/entry_point.py <pkg> <group> <name> <target>` is let through for the caller's own package
  (the `<pkg>` of its spawn prompt's `Section:` line) and refused unwrapped, under another
  lock, or for another package. A command it cannot parse is let through with the rule on
  stderr.

## Questions

Subagents cannot ask you anything — Claude Code removes `AskUserQuestion` from every subagent.
So an agent with a question that changes a boundary writes a stub to `docs/decisions.md` (a
designer under the driver writes it to its section's inbox, **Decisions** below), tagged
`Raised by: /dev-team:plan-package data (interview)`, writes nothing else, and **stops**:

```
Stopped for decisions: D12, D13
- D12 — Bars: store timestamps as UTC or exchange-local? (assumption: UTC)
- D13 — Is audit its own section or part of clean? (assumption: its own)
Answer in docs/decisions.md, or re-run `/dev-team:plan-package data` as-is to accept the assumptions.
```

Fill in `Decision:` and set `Status: decided`, or do nothing — either way, re-run the same
command. The tag is how it knows not to ask twice. Under `/dev-team:run-package` the driver does
this for you: it shows the question with the stub's `Recommendation:`, records your answer and
continues.

## Decisions

Subagents start with a fresh context and never see your conversation, so anything you decide
has to be in a file. `docs/decisions.md` is that file, and it outranks every document a section
is built from. One ledger for the whole repo, one `D<n>` sequence.

```markdown
## D7 — Session store: Redis or Postgres?
Scope: data/storage, analysis/cache
Raised by: OQ-data-storage-2
Recommendation: Postgres. One dependency instead of two.
Assumption if unanswered: Postgres.
Decision: Postgres.
Status: decided
Applied: data/storage, 2026-09-09, packages/data/src/data/storage/session.py
```

`Scope:` is `repo`, a package name, or a list of `<pkg>/<section>`: one prefix rule binds an
implementer to it. The architect and the designer write stubs; you (or the driver, relaying
you) fill `Decision:` and `Status:`; the implementer adds `Applied:`.

Under the driver, a designer's stub and an implementer's `Applied:` line go to
`docs/packages/<pkg>/decisions/<section>.md`, one file per section; `hooks/sync_decisions.py`
folds it into `docs/decisions.md` under a lock and numbers `D?` stubs, so no two agents write
the ledger. You, the driver, `pair` and the architect still write it directly. A session
without the hook leaves an inbox unsynced, which fails the run gate;
`python3 <plugin>/hooks/sync_decisions.py --all` repairs it.

- `decided` — built, with an `Applied:` line per section.
- `deferred`, or `open` with an assumption — the assumption is built and marked
  `# TODO(decision D7)` at the affected line.
- `open` with **no** `Assumption if unanswered:` — the section is BLOCKED.
- `superseded` — the question is moot; only the architect sets this.

## Deviations and spec-changes

`docs/packages/<pkg>/deviations/<section>.md` is a section's ledger for "the document and the
code disagree", one file per section so agents running in parallel on different sections never
write the same file, one entry per item, `## <pkg>/<section> — <date> — <kind> — <k>` (`<k>` the
entry's sequence in the file, so two entries of one day never share a heading), with
**Clause**, **Said**, **Did** or **Found**, **Why**, **Status**, **Raised by** and **Resolved
by**. Append-only; the status line is the only edit. The older locations — the 2.0
`docs/deviations/<pkg>/<section>.md` and the pre-2.0 `docs/deviations.md` — are still read, and
an entry is edited where it is; a heading without `— <k>` still parses. An intent test tags a
tolerated clause `(deviation <date>-<k>)`.

- **`deviation`** — the implementer built something other than the design said, inside its
  section, for a reason. It writes the entry `proposed`; the reviewer sets `approved` or
  `rejected`; the tester regenerates the intent tests that cite an approved clause; `sync-plan`
  applies it to the contracts and sets `synced`. A departure with no entry, or with an empty
  **Why**, is a CRITICAL finding.
- **`spec-change:<level>`** — a document is wrong: a boundary shape, a public name, a test
  that asserts what no document says. The designer, tester, implementer or reviewer writes it
  `open` with its evidence, and `status.py` re-opens the step for its level: `test` → TEST,
  `design` → DESIGN, `contract` → PLAN, where the architect edits the contract and sets it
  `resolved`. A tester that finds two design items contradicting each other appends a
  `spec-change:design` citing both under **Found** and returns `Result: spec-change`. An entry
  written since 2.2 (its heading ends `— <k>`) is open until the agent that answers it sets
  its `Status:` to `resolved` — the tester for `test`, the designer for `design`, the
  architect for `contract` — whatever was committed since, and every open entry of a level
  reaches that agent in one spawn: `status.py`'s evidence lists them all (`open <h1>; <h2>`),
  and the driver sends each on its own line. An agent handed several sets `resolved` only on
  those its commit answers. An older entry without `— <k>`, and a review report's
  `spec-change` verdict, keep the earlier rule: answered by the next commit of the level's
  document, and `sync-plan` sweeps any such entry still `open` at the close. A spec-change is
  a normal exit, not a failure.
- **Two cases agents used to guess at.** An intent test that fails before it reaches the
  section's code — its own helper, fixture or import is broken — is a `spec-change:test`,
  with the test's docstring citation as **Clause** and the traceback line as **Found**. A
  signature the contract's **Section interfaces** states for a name that is not public is a
  seam: changing how a caller calls it is a `spec-change:contract`, while an additive,
  compatible change, such as a new optional parameter, is a `deviation`.

## Reviews

Round 1 is two reviewers in parallel, each writing its own report: **A** (`Focus:
conformance`) owns a coverage table with one row per contract clause and design item — pass,
fail or can't-tell, with `file:line` — plus the seams and the deviations ledger; **B**
(`Focus: correctness`) owns correctness and security. From round 2 one reviewer (`Focus:
full`) reads only the diff since the last round and the previous reports, classifies each
prior finding fixed or unfixed, and may raise a new CRITICAL only on lines the fix touched, so
the finding count can only fall.

Reports are `docs/packages/<pkg>/reviews/<section>/<date>-r<n>-<a|b|s>.md`, one directory per
section (a 2.0 `docs/reviews/<date>-<pkg>-<section>-r<n>-<letter>.md` is still read as that
round), and the report is the queue: the fix-round implementer reads its **CRITICAL** and
**WARNING** lines. A report's `Commit:` is the section's last commit as `status.py --rounds`
prints it, never `HEAD`, which in a batch may be a sibling's. The verdict is `approve`,
`request changes` or `spec-change`.

Once every section is DONE, one more reviewer (`Focus: paths`) follows each command of the
package from `cli.py` to its external effects, on the call tree `status.py --paths <pkg>
--against-contract` prints: each command's built frames beside its **Call paths** entry, each
frame `match`, `extra` (in the code, not in the contract) or `missing`. It writes
`docs/packages/<pkg>/reviews/paths/<date>-r<n>-p.md`, with one row per command under **Paths**
and a `contract` column. An `extra` or `missing` frame is a break, CRITICAL under the section
that holds it; beyond that it may block on four things only: a command deeper than its
**Call paths** budget, or than 8 frames from its first external effect when the contract has
no entry for it (P1), a lambda, closure or mapping dispatch on a main path (P2), a
pipeline or orchestrator that fails the reader's test in `python-style-guide`'s
`references/pipelines.md` (P3), and a trivial single-use helper or options bag on a main path
(P4). Each finding names a section, and `status.py` re-opens that section as FIX n with the
paths report as its previous round. A package is not shipped until this review approves; at
round 3 the driver asks *one more round* or *defer*. A package with no `[project.scripts]`
commands needs no paths review.

A designer's `proposed` entry against a contract row — its §10 items — is judged by one test,
the one the designer applied: additive and compatible (a new optional parameter, a helper the
row does not name) is `approved` and folded in at the close; anything a consumer must change
for (a signature, a public name, a shape) is `rejected`, a `spec-change:contract` is appended,
and the verdict is `spec-change`.

CRITICAL is a closed list: a **break** (a contract, a decided `D<n>`, or a name a consumer takes
from a shipped document), a **wrong result** on the main path, a **security** finding, a
**silent or unreasoned deviation**. Everything else is a WARNING or a SUGGESTION. A mechanical
failure is never the reviewer's: the stop gate already ran it, and the reviewer runs no command.
An out-of-diff finding on round 2+, and each `ELSEWHERE` line, is appended to `docs/followups.md`, the backlog —
work no loop step will pick up, never counted and never a gate. At the cap, **Running a
package** says what happens.

## Code conventions

Knowledge is scoped **by role**, through each agent's `skills:` frontmatter — the only
mechanism in Claude Code that scopes by agent.

| Skill | arch | design | impl | test | review | doc | research |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `project-structure` — layout, size limits, config placement, naming | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| `python-style-guide` — inside a file: docstrings, function shape, pipelines, `__init__.py`, naming | — | — | ✓ | ✓ | ✓ | — | — |
| `python-implementation` — splitting mechanics, config code | — | — | invoked | — | — | — | — |
| `workspace-scaffold` — pyproject, import-linter, mkdocs, CI skeletons | invoked | — | invoked | — | — | — | — |
| `planning-templates` — headings for every document the loop parses | invoked | read | read | read | read | — | invoked |
| `security-review` — checklist | — | — | invoked | — | invoked | — | — |
| `test-driven-development` — red-green-refactor, test design, pytest | — | — | ✓ | ✓ | — | — | — |
| `debugging-and-error-recovery` — root-cause triage for tests and builds | — | — | invoked | — | — | — | — |
| `git-workflow-and-versioning` — §Project convention, the commit rule | ✓ | ✓ | ✓ | ✓ | ✓ | invoked | invoked |

✓ is preloaded; *invoked* is loaded when the agent's procedure reaches it; *read* is one
reference file or paragraph opened with the Read tool. `git-workflow-and-versioning` §Project convention is the
one copy of the commit rule every agent follows: the run gate, staging by explicit path
(`git add <paths>` then `git commit -m … -- <paths>`), `<scope>: <summary>` with one
`Dev-Team-Run:` trailer, one commit per run, and a retry on `.git/index.lock`.
`test-driven-development` is preloaded for the tester and the implementer: the tester writes
to its RED step, and the implementer uses its Prove-It pattern on review findings that are
bugs. `security-review` goes to the implementer on its triggers, to
reviewer B in round 1, and to a round-2+ reviewer when the diff hits a trigger. The last three
skills are vendored from `addyosmani/agent-skills` (MIT) and adapted to this stack.

Three conventions in `python-style-guide` are marked *Project convention*:

- **`__init__.py`.** The top-level `__init__.py` of a package exposes *only the names a
  consumer outside the package needs*, resolved lazily (PEP 562) so `import data` costs
  nothing until a name is touched. The `surface` section writes it, and nothing else. Every
  nested one is empty. Inside a package, import from the defining module; from another
  package, import from its top level only. import-linter enforces the second.
- **Docstrings on everything.** Google style, `Args:` without types, `Examples:` in doctest
  form on public entry points. The docs build runs strict in CI — that is the docstring-rot
  catch. A summary line says what the function changes outside itself.
- **Function shape.** Phases inside a function are fine, each with a one-line purpose comment;
  a helper is extracted only when the jump buys something. A limit is met with a seam: no
  `**options` bag, no packed tuple, no three-statement helper with one caller. Every call on a
  main path names its target, and a pipeline reads as its steps (`references/pipelines.md`).

**CLI commands live in `src/<pkg>/cli.py`**, one function per command, registered under
`[project.scripts]`, with no `scripts/` directory — an entry point must be importable from the
installed package (`project-structure` §1).

**Enforced, not intended.** Dependency direction between packages, "consumers import the top
level only", and section layering inside a package are import-linter contracts in the root
`pyproject.toml`, derived from the Sections table's `depends on`. CI runs the same
`docs/constraints.md` rows the stop gate runs. Merge `pyproject-lint-config.toml` into the root
`pyproject.toml`; it ships beside this README so there is one copy. The lint block caps
positional parameters (`PLR0917`; keyword-only ones are free) and requires ruff 0.16.0 or
later. The stop gate also runs `status.py --shape`: a run that adds a trivial single-use helper
or an options bag does not pass.

This plugin ships no rule: Claude Code loads path-scoped rules only from `.claude/rules/`. For
your own interactive work, write a `.claude/rules/python-standards.md` in the repo you are
building that points at `project-structure` and `python-style-guide`.

## `docs/` layout

```
docs/
├── brief.md                         your input to plan-repo                        (shape-brief / you)
├── history/                         brief-contracted.md; every contract before an edit (architect)
├── constraints.md                   the bar: Floor, Enforced, Measured, Guarded, Exceptions (set-constraints / you)
├── architecture.md                  THE REPO CONTRACT                              (plan-repo, map-repo, sync-plan)
├── decisions.md                     D<n> ledger                                    (sync_decisions.py from the inboxes · architect · you · the driver · pair)
├── followups.md                     the backlog, `- [ ] <pkg>/<section>: …`, never a gate (reviewer, architect)
├── legacy/inventory.md              what to salvage from an old repo              (curator / you mark keep)
├── sources/<source>.md              SOURCE PROBE, one `## <pkg>/<section>` entry per consumer (researcher)
├── sources/<source>.sample.json · .probe.py    recorded responses + re-runnable probe   (api)
├── sources/<source>.stats.json  · .profile.py  column statistics + re-runnable profile  (dataset)
├── api/<pkg>/index.md               the docs-site API page                         (the surface section's implementer)
├── index.md                         the docs-site home page                        (documenter)
├── packages/
│   └── data/
│       ├── contract.md              THE PACKAGE CONTRACT; Sections table ends with `surface`, with **Call paths** (plan-package)
│       ├── design/<section>.md      one per section; first line `Mode:`            (designer)
│       ├── interface.md             THE PUBLIC SURFACE AS SHIPPED — the surface section's README (implementer)
│       ├── decisions/<section>.md   the section's decisions inbox: D? stubs, Applied: lines (designer, implementer)
│       ├── deviations/<section>.md  one ledger per section: deviations, spec-changes (implementer, designer, tester, reviewer, architect)
│       ├── changes/<slug>.md        a change to built or shipped code, one per affected package, until sync-plan (architect)
│       └── reviews/
│           └── ingest/
│               ├── 2026-09-04-r1-a.md   round 1, conformance
│               ├── 2026-09-04-r1-b.md   round 1, correctness
│               └── 2026-09-05-r2-s.md   round 2, diff-scoped
└── deviations/ · deviations.md · reviews/ · changes/   (2.0 layouts, still read; never written)
```

Outside `docs/`: each section's code and `README.md` (the implementer's), its
`tests/unit/<section>/` (the implementer's) and `tests/intent/<section>/` (the tester's alone),
and under the gitignored `.dev-team/`: `gate/<pkg>/<section>.txt`, the stop gate's record for
each section, which the reviewer reads as evidence and `status.py` reads to hold a blocked or
let-through section BLOCKED; `stop/<pkg>/<section>`, an implementer's blocked or spec-change
marker;
`locks/`, the mkdir locks of `locked.py` and the sync hook; `tmp/`, agents' shell scratch.

**Canonical contracts describe code that exists.** An edit to a contract that touches a built
or shipped package becomes a change file instead; `sync-plan` applies it to the contracts once
the sections it names are DONE, after checking the code. Every contract is copied to
`docs/history/` before it is edited. Package status is derived, never written down:
`contract.md` exists → planned; section code exists → built; `surface` DONE and its check
passing → shipped.

## Gotchas

- **Probes make real API calls, and read real data.** An `api` gets one request per read
  endpoint the section needs plus one deliberately bad one; it never sends a write. A `dataset`
  is profiled into statistics, never rows. Keys come from env or a root `.env`; the researcher
  never writes a value anywhere. `/dev-team:plan-repo` probes the brief's datasets before the
  repo contract, because data that cannot support the task changes which packages exist.
- **Work on a branch, commit your hand edits.** The run gate refuses `main`/`master` and a
  dirty tree outside the four exempt paths. Hand edits that depart from the design are
  CRITICAL findings until the ledger records them; `/dev-team:pair` writes those entries. `git log` is the run history: every commit carries
  a `Dev-Team-Run:` trailer.
- **Re-running the same command is the continue action** after a stop. Doing nothing in the
  ledger means "accept the assumptions".
- **`run-package` is a loop in your conversation.** It reads each return's first line only and
  prints only the rows whose state changed, but a package of five sections is still dozens of
  turns. Run it with `/clear` behind you.
- **Return size is context cost.** Agents return short summaries; the content is on disk.
- **Descriptions are always loaded.** Keep agent `description` fields short — the combined
  budget warns at 15,000 tokens.
- **Nesting depth.** The driver's spawns are layer 1. `map-repo` forks an architect that
  spawns one architect per package, layer 2; `plan-repo` spawns researchers for datasets. Both
  are within the three-layer limit.
- **Expect blocks on an adopted repo.** Open questions with no assumption stop a section by
  design. Answer them when the driver asks, or in `docs/decisions.md`, and re-run.
- **import-linter needs the packages importable.** Run `uv run lint-imports` inside the
  workspace, and expect it to fail on a package in `root_packages` with no code yet — which is
  why the block grows as packages are built.
- **The docs site builds strict from the first section.** The scaffold's nav names only files
  that exist; each `surface` section adds its package's API page, and
  `/dev-team:finalize-project` writes `docs/index.md`. MkDocs' `docs_dir` is `docs/`, your
  planning docs; change it in the repo contract's Toolchain before the first scaffold if you
  would rather not publish them.
- **No section named `report`.** Claude Code refuses a subagent's Write of a `.md` file whose
  name starts with `report`, `summary`, `findings` or `analysis`, so a section or source named
  that way could never get its design or probe doc. The architect names it after what it
  produces, one word such as `digest` (`project-structure` §4).
- **Implementers are parallel.** Two sections that must edit one file the write guard cannot
  split are the `--serial` case; the three edits every section shares — `uv add`, an
  entry-point line, the `.gitignore` block — go through `locked.py`.
- **A blocked or let-through implementer is a BLOCKED row.** A section whose implementer
  blocked, or was let through after three red attempts, shows BLOCKED with `gate …` evidence,
  and `/dev-team:run-package` asks about it. Answer the question, or type the `next:` line.
  An implementer's return no longer lists test or lint results: read
  `.dev-team/gate/<pkg>/<section>.txt`.
- **A package shipped under 2.3 may now print `shipped: no (surface check FAIL)`.** Run
  `status.py --surface <pkg>` and correct the README rows it names: one exported name per row,
  in backticks, no grouped or dotted names.
- **A package shipped under 2.4 may now print `shipped: no (paths needed)`.** `shipped:` needs
  the paths review. Run `/dev-team:run-package <pkg>` once: the driver spawns the paths review,
  and its findings re-open the sections they name as FIX rounds. A package with no
  `[project.scripts]` commands reads `paths: approved (no commands)` and stays shipped.
- **An existing repo keeps its old argument cap.** The lint block now caps positional
  parameters only, but the scaffold merges it only into a new repo. In your root
  `pyproject.toml`, replace `PLR0913` with `PLR0917` and `max-args` with `max-positional-args`,
  add `required-version = ">=0.16.0"` under `[tool.ruff]`, and upgrade ruff to 0.16.0 or later.
  An older ruff then refuses to run instead of skipping the rule.
- **The stop gate fails a run that adds a trivial single-use helper or an options bag**
  (`FAIL shape: …` in the gate record). Inline the helper or name its parameters; code already
  reviewed, and adopted code, is measured and never failed.
- **`paths` is a reserved section name.** Rename a section called `paths` in the package
  contract before its next run: its reviews would share `reviews/paths/` with the paths review.
- **`status.py --fields` prints seven lines, and `reviews/paths/` holds reports with letter
  `p`.** A script of your own that reads `--fields` or the review directories reads the sixth
  line, `paths report:`, and the seventh, `dependency readmes:` — the `depends on` READMEs that
  exist, `none` when none does, which the driver now sends as **Dependency READMEs** — and
  skips `reviews/paths/` when it means a section's reports. A hand-run that copied the six
  lines still works.
- **Upgrading from 2.5: `surface` is ready earlier.** With a `## Call paths` heading in the
  contract, the `surface` row is ready at PLAN, DESIGN and TEST before any sibling is DONE;
  IMPLEMENT still waits for every section. A package mid-build whose contract gains the
  heading at its next PLAN sees its surface designer spawn in the next batch; nothing already
  designed is re-opened. A contract without the heading keeps the 2.5 timing.
- **Upgrading from 2.5: the package contract has a fifth item.** **Call paths** sits after
  **Pipelines**; **Public surface (intent)**, **Consumes**, **Package conventions** and
  **Open decisions** are items 6 to 9. A contract written before 2.6 still parses: every
  reader finds its headings by name.
- **Upgrading from 2.5: the paths review compares the code to the contract.** Once a contract
  has **Call paths**, a frame on a command's path that the contract does not list, or one it
  lists that the code does not pass through, is a break (CRITICAL) under the section that
  holds it, and P1 uses the command's own budget. Without the heading the review runs as in
  2.5.
- **Upgrading from 2.5: a legacy close writes the heading.** `/dev-team:sync-plan <pkg>` (or
  `run-package`'s close) on a contract with no **Call paths** writes it as built from
  `status.py --paths`, and writes `docs/packages/<pkg>/changes/paths-<command>.md` for each
  command deeper than 8. Those change files re-open the sections they name at DESIGN when
  approved; nothing is rebuilt until then.
- **A README with grouped or dotted name cells fails its section's next gate.** The same
  correction, in that section.
- **A 2.2-or-later ledger entry still `open` re-opens its step** even when its document was
  committed since. Run `/dev-team:run-package <pkg>`: the answering agent is handed it. If it
  was in fact answered, set its `Status:` to `resolved` by hand.
- **A hookless session leaves inboxes unsynced.** A session or harness that runs the agents
  without this plugin's hooks writes an inbox no hook merges; the run gate says so and names
  `sync_decisions.py --all`.
- **Interactive session for a hard section:** `claude --agent dev-team:implementer` gives the
  main thread the implementer's prompt, tools and model, so you get its rules and return format
  while steering turn by turn. The stop gate is a `SubagentStop` hook and does not fire there.

Reference: https://code.claude.com/docs/en/sub-agents and https://code.claude.com/docs/en/skills
