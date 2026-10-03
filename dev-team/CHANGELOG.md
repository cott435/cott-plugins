# Changelog

Format: one entry per tagged release. The versioning policy — what triggers patch/minor/major,
and how model and eval versioning relate to it — is in the `plugin-dev` plugin's
`bump-version` skill. This repo's own decisions are in `VERSIONING.md`.

**Versions are the `0.x` line below, and nothing else.** This plugin had generations before
`0.1.0` — it was `project-workers` until `259785a`, and prose once referred to a "v3" and a
"v4" — but none of that is recorded here and none of it is a version this repo can resolve. So
those labels are not used to date anything: where an older artifact still has to be read, it is
described by what it looks like, not by the generation that produced it. The one surviving use
of the name is the **dev_team v4 Flow** artifact in the gallery, which is a title.


## [Unreleased]

A package reads from its command down to its first external effect. From the `data` package
of `quant`, built under 2.3.0 with every review approved: 17 frames to the first download, 416
single-use helpers, 49 options bags. Design: `site/notes/2.5-readability-design.md`.
Evidence: the `2.5-*` logs in `evals/`.

### Changed

- The lint block caps positional parameters (`PLR0917`, `max-positional-args = 5`) instead of
  all of them, and requires ruff 0.16.0 or later (cab4131)
- The stop gate runs `status.py --shape`: a run that adds a trivial single-use helper or an
  options bag fails, indirect calls and entry-point depth are recorded as `MEASURED`, and
  adopted code is never failed (c61905d, 52cff96)
- `python-style-guide`: no options bag, main paths called by name, docstrings written from the
  caller's side, `log` for logging only, private class names unique among sections that call
  each other; new `references/pipelines.md` (08ae90b)
- `status.py --paths <pkg>` prints each command's call tree to its external effects
  (7d549dd)
- The reviewer gains `Focus: paths`, once per package when every section is DONE, with a
  closed blocking list P1 to P4; its findings re-open the sections they name, and a package is
  not shipped until it approves (652f0c1, 7646362)
- The implementer meets a size limit with a seam and fixes a paths finding in its own section;
  the designer writes pipelines to the reader's test (ac163c0)

### Fixed

- The implementer and reviewer invoke `dev-team:security-review` by its full name. The bare
  `security-review` resolved to Claude Code's built-in command of that name, which reviewed
  the branch diff and replaced the implementer's return (in 2.4.0 too)

### Upgrading

- **`shipped:` needs the paths review.** A package shipped before 2.5 that has commands reads
  `shipped: no (paths needed)` after the upgrade. Run `/dev-team:run-package <pkg>` once: the
  driver spawns the paths review, and its findings re-open the sections they name as FIX
  rounds. A package with no `[project.scripts]` commands reads `paths: approved (no commands)`
  and stays shipped.
- **The lint block caps positional parameters, not all of them.** An existing repo keeps its
  root `pyproject.toml`: replace `PLR0913` with `PLR0917` and `max-args` with
  `max-positional-args` by hand, add `required-version = ">=0.16.0"` under `[tool.ruff]`, and
  upgrade ruff to 0.16.0 or later. An older ruff now refuses to run instead of skipping the
  rule.
- **The stop gate fails a run that adds a trivial single-use helper or an options bag**
  (`FAIL shape: …`). Inline the helper or name the parameters. Code already reviewed, and
  adopted code, is measured and never failed.
- **`paths` is a reserved section name.** Rename a section called `paths` in its package
  contract before its next run: `reviews/paths/` holds the package's paths reports.
- **`status.py --fields` prints six lines, and `reviews/paths/` holds reports with letter
  `p`.** A script of your own that reads `--fields` expects the sixth line, `paths report:`,
  and one that walks the review directories skips `reviews/paths/` when it means a section's
  reports.


## [2.4.0] - 2026-10-01

A run stops where the files say it should. From three audited runs (`site/notes/open_items.md`,
items 1 to 20) and the defects the 2.2 ledger left open. Design:
`site/notes/2.4-design.md`. Evidence: the `2.4-*` logs in `evals/`.

### Changed

- The stop gate's record names the commit it speaks for (`commit:` on line 2) and records a
  marker stop as `result: blocked` or `result: spec-change` under the earlier attempt's lines.
  `status.py` reads the record for the section's current commit: an implementer that blocked
  or was let through after three attempts leaves the section BLOCKED, one that died between
  attempts leaves it at IMPLEMENT; `next:` offers running the implementer again or reviewing
  anyway. A stale, pre-2.4 or `--report` record changes nothing (9c917c7)
- A ledger entry written since 2.2 stays open until the agent that answers it sets
  `resolved`, whatever was committed since; PLAN and DESIGN evidence list every open heading,
  as TEST already did. A re-probe that only adds lines to a shared probe doc no longer sends
  built consumers back to DESIGN, and the researcher keeps the shared body byte for byte unless
  an observation changed (1f3cdce)
- `entry_point.py` adds one entry-point line to a package `pyproject.toml` under the `deps`
  lock and runs `uv sync`; the Bash guard lets it through only under `locked.py deps` and only
  for the caller's own package. The write guard stops a section, `surface` included, at its
  siblings' paths and refuses a suppression comment added under `tests/intent/`. Both guards
  act from `docs/brief.md` as well as `docs/architecture.md`, and a researcher may redirect to
  scratch outside the repo (ab4d453)
- `status.py --surface <pkg> --section <s>` checks one section README's name cells, and the
  stop gate runs it for every section but `surface`. `shipped: yes` needs the package's
  surface check to pass. Guarded counts removed asserts and `pytest.raises` net per test file,
  reads a wrapped `xfail(` call to its closing bracket, and keeps ruff 0.15's `--> path:line`
  locations (1fe4292)
- The implementer hands back once and its return carries no check results; after a gate retry
  it ends with the one line `Result: done`. It registers entry points through `entry_point.py`,
  writes one exported name per README row, marks every line that hard-codes an open decision's
  assumption, treats a false gate FAIL in its own file as a block, and commits what it built
  before blocking. The kind table gains a test that fails before the code and a contract-stated
  signature that is not public (d558190)
- The designer takes several `Spec-change:` headings and resolves each; the design names its
  `Upstream packages:`, the entry points it owns, and which open decisions bind the section;
  no test case needs a subprocess, a skip or an unreachable service without its substitute.
  The architect stages from `git status --short` and resolves each contract entry it is
  handed. `status.py --fields` gains `upstream interfaces:`, and the tester, implementer and
  reviewer get only the upstream interfaces their design consumes (3bb3ecb)
- The tester reads its documents only, preloads `test-driven-development`, stops with
  `spec-change:design` on a case the repo's lint or the no-skip rule forbids, writes a
  decision assigned elsewhere as a `Not written:` line, removes a test file with `git rm`, and
  returns the bare `Tests:` count. The reviewer grades a `blocked` gate record or a failing
  surface check CRITICAL, and a departure with no entry CRITICAL even when the design
  contradicts itself (7d5cf7a)
- The driver branches on the first hand-back, asks about a gate-BLOCKED row (*run the
  implementer again*, *review anyway*, *stop here*) and about a failing surface check (*fixed,
  retry*, *stop here*; the close waits), sends every open heading of a level, ends the run on
  a free-text answer, prints `uncommitted: docs/decisions.md` from git, and writes `none` for
  an empty `builds with`. Its evals' runner is committed under `evals/runners/run-package/`
  (131e40e)

### What you will notice

| Change | What to do |
|---|---|
| A section whose implementer blocked or was let through now shows BLOCKED with `gate …` evidence, and `/dev-team:run-package` asks about it | Answer the question, or type the `next:` line |
| A package shipped under 2.3 whose surface check fails prints `shipped: no (surface check FAIL)` | Run `status.py --surface <pkg>` and correct the README rows it names: one exported name per row |
| A README with grouped or dotted name cells fails its section's next gate | The same correction, in that section |
| A 2.2-or-later ledger entry still `open` re-opens its step even though its document was committed since | Run `/dev-team:run-package <pkg>`; if it was in fact answered, set its `Status:` to `resolved` by hand |
| A re-probe that only adds to a shared probe doc no longer sends built consumers back to DESIGN | Nothing |
| A repo with `docs/brief.md` and no `docs/architecture.md` now has the write and Bash guards on | Nothing; a refusal names the rule |
| An implementer's return no longer lists test or lint results | Read `.dev-team/gate/<pkg>/<section>.txt` |
| A tester stops with `spec-change:design` on a test case the repo's lint forbids, where it used to rewrite the case | Nothing; the designer rewrites the case in the next batch |

### Fixed

- The stale retry string in the `gate-fail-attempt-1` hook-event case, the contract claim that
  refused `plugin-dev:` commands, `documenter.json`'s API page path, and a duplicate row in
  `evals/README.md`; every suite green from here (4799002)
- Definition fixes from the 9ecf4176 audit, merged after 2.3.0 with no changelog entry:
  several open `spec-change:test` entries reach the tester, one entry per implementer stop,
  no security line in the return, `delta` on a never-built section, test paths under
  `tests/unit/<section>/` (1e81553). First run against an agent in 2.4's phases 6 to 9.

## [2.3.0] - 2026-09-30

Definition fixes from the audit of a real `run-package content` run (session `befb4798`, 2.2.0:
13 errors, 17 warnings, 26 notes). Evidence: `evals/2026-09-30-audit-run-package-befb4798.md`,
`evals/2026-09-30-audit-fixes-definition-faults.md`, `evals/2026-09-30-audit-fixes-e5-e12.md`.
Contracts 43/43; no behavioral re-run of the changed agents.

### Changed

- `run-package`: a `blocked` or `stopped` return is asked about whatever row the next `status.py`
  shows, since an implementer can block after its commit; the driver prints changed rows as the
  table does, with no label or sentence (d000f3f)
- The reviewer appends each `ELSEWHERE` line to `docs/followups.md`, the one place a lint or type
  hit in the tester's lines survives the run (d000f3f)
- A conformance reviewer reads every file under `Intent tests:` before its first Coverage row,
  names them in `Scope:`, and gives each design **Tests** case its own row (772a499)
- The implementer's first return says `Gate: not yet run`, not `Gate: PASS`: the stop gate runs
  after the return (d000f3f)
- A gate-retry amendment is the implementer's final text, not a second `SubagentHandback` call,
  which delivers one report; the gate's retry message says the same (d000f3f)
- The scaffold return is a closed list too; the tester reports a lint hit it left in the tree on
  a `Not written:` line; the designer's `Deviations:` is the count alone; the architect's
  return has no opening paragraph or header row (d000f3f)
- The implementer's one route for a binary file Write cannot make: a generator under
  `.dev-team/tmp/` and a single `cp` of that file, named in the README (d000f3f)
- The surface section's one route when `mkdocs build --strict` fails on a sibling docstring's
  cross-reference: `members` and one `mkdocs.yml` setting, each a `proposed` deviation (772a499)
- The architect reads the reference for each document it edits, and `Resolved by:` is the
  section's `approve @<sha>` (d000f3f)
- The tester takes the RED paragraph from its preloaded skill; the designer checks each **Tests**
  case against the sections it tests (d000f3f)

### Added

- `attr_list` in the scaffold's `mkdocs.yml`, so a docstring anchor resolves under `--strict`
  (772a499)

## [2.2.0] - 2026-09-30

Implementers in parallel; the per-section documents under their package. Evidence:
`evals/2026-09-29-audit-run-package-f1c390a1.md` and the 2.2 phase logs.

### Breaking

| Change | What to do |
|---|---|
| Implementers run in parallel by default, and a batch holds every ready row's step, PLAN alone (d7a39a8) | nothing; `/dev-team:run-package <pkg> --serial` is the 2.1 loop, for sections that must edit one file the write guard cannot split |
| The stop gate no longer runs `repo`-scope pytest rows of `docs/constraints.md`; the record says `SKIPPED <row>: repo-scope pytest is CI's` (2efa480) | nothing; CI still runs them |
| New entries, reports, change files and decision stubs go to `docs/packages/<pkg>/…` — `decisions/`, `deviations/`, `reviews/<section>/`, `changes/` (43c5e36, e8a7cb5) | nothing; `docs/deviations/`, `docs/deviations.md`, `docs/reviews/` and `docs/changes/` are still read, and an entry is edited where it is. No migration |
| The tester's spawn field `Adopted code:` is `Design mode: new \| document \| delta`, and the tester may return `Result: spec-change` (fc6ab8a) | nothing under the driver; a hand-written tester spawn sends the design's first line as `Design mode:` |
| A designer or implementer never writes `docs/decisions.md`: stubs and `Applied:` lines go to the section's inbox, `docs/packages/<pkg>/decisions/<section>.md`, and a hook merges them (7fccd1d) | a session without the hook fails the run gate on an unsynced inbox; `python3 <plugin>/hooks/sync_decisions.py --all` repairs it |
| A gate retry amends only when `HEAD` is the run's own commit; otherwise it is a second commit with the same trailer, so a run may have two commits (e8a7cb5) | nothing |
| The `.dev-team/stop` marker is per section, `.dev-team/stop/<pkg>/<section>`; the deviation heading gains `— <k>` and the docstring tag `(deviation <date>-<k>)` (2efa480, e8a7cb5) | nothing; the old heading and tag spellings still match |

### Added
- `hooks/sync_decisions.py`, the decisions inbox and its template (7fccd1d); `hooks/guard_bash.py`
  (ff75747); `skills/status/scripts/locked.py` (7fccd1d); `run-package --serial` (d7a39a8);
  `status.py --rounds` `commit:` and the run gate's inbox check (43c5e36); the tester's
  `spec-change:design` route and `Design mode:` (fc6ab8a); `SKIPPED` gate lines (2efa480).

### Changed
- **The gate is section-aware** (2efa480): the section from the spawn prompt in the subagent
  transcript; the diff is the section's paths since its last review `Commit:`; intent and unit
  suites; any located failure outside the section is `ELSEWHERE`.
- **The write guard confines an implementer to its section** (ff75747), and a Bash guard refuses
  shell writes to repo files (E4).
- **Templates at the 2.2 paths; the retry commit rule** (e8a7cb5): §Project convention rule 4
  amends only the run's own commit; an agent whose inbox changed stages it and
  `docs/decisions.md`.
- **The implementer runs in a batch** (768ef75): `Applied:` to the inbox, the per-section
  marker, shared edits through `locked.py`, no shell writes, scratch under `.dev-team/tmp/`,
  the `(name)` unwrap moved to the `surface` section (E3, E10, E11, E12).
- **Designer and tester** (fc6ab8a): stubs to the inbox as `## D?`; the E1 test at §10; the
  tester's W1 route, `Design mode:` (W4), full-name tag match (W3), closed return form (E2),
  Python only through the test command (E6); each sets `resolved` on what it answers (W2).
- **Reviewer and architect** (0f3c820): the E1 rule for designer-raised contract deviations;
  `Commit:` from `status.py --rounds`, never `HEAD` (F12); reports per section; one change file
  per affected package; the W2 sweep at the close.
- **`run-package`** (d7a39a8): every ready row's step in one message, the architect alone at
  PLAN; return first lines only (E7); changed rows printed without grep (E8). `pair` at the
  2.2 paths.
- **`plan-package`, `sync-plan`, `finalize-project`** at the 2.2 paths (5f87ce0).
- **The fixes the end-to-end build pointed at** (54efe7d; `evals/2026-09-30-2.2-docs-and-release.md`, `evals/2026-09-30-2.2-run-fixes.md`):
  a lint, type or Guarded failure located in an intent-test file is the gate's `ELSEWHERE`
  again, as in 2.1, and an `xfail` reason `D5_OPEN` cites D5; every turn an implementer ends
  is a `Result:` hand-back, a gate failure in a file it may not edit is `Result: blocked`, and
  the driver re-derives before asking on a return with no `Result:` line; a section's own
  `Applied:` lines in `docs/decisions.md` follow its inbox, and the run gate fails on a stale
  one; the driver reads its spawn fields from the new `status.py --fields <pkg>/<section>`
  (`mode`, `change file`, `design mode`, `diff base`) instead of listing and grepping files; the
  scaffold writes the root config the first consumer needs (`[tool.mypy] mypy_path`, contract
  2 with `allow_indirect_imports = true`); the Bash guard refuses a python here-document write
  and exempts only `uv` and the `.gitignore` printf under `locked.py`; `plan-package` runs the
  run gate with no package; §Project convention lists paths literally.
- **The package API page is `docs/api/<pkg>/index.md`** (54efe7d): Claude Code refuses a
  subagent's Write of a `.md` whose name starts `analysis` (or `report`, `summary`, `findings`),
  so `docs/api/analysis.md` could never be written; the old name is still read and writable.
  The `surface` implementer may edit its package `pyproject.toml` for `[project.scripts]`;
  `status.py --surface` reads a README name cell's first backticked span and needs no section
  README row for a name a surface-owned module (a pipeline, the CLI) provides.

## [2.1.0] - 2026-09-29

Testers now work inside the real workspace, and a gate retry no longer fills the driver's
context with repeated reports. Evidence: `evals/2026-09-29-scaffold-step-and-retry-amendment.md`.

### Added
- **The SCAFFOLD step** (21175fc). `run-package`'s first spawn, right after the run gate, when
  `status.py --scaffold <pkg>` says the workspace is missing. One implementer, in its new
  scaffold mode, builds the root `pyproject.toml` with the plugin's lint rules, the package
  skeleton, `mkdocs.yml` and `.gitignore`. It runs `uv sync` and the empty workspace's checks,
  and commits them with `uv.lock`. Every tester then writes and runs its intent tests inside
  the workspace, under the repo's own lint rules, with the Toolchain's own test command.
- **`status.py --scaffold <pkg>`** (21175fc), and a `scaffold: needed` line in the package
  block. A root that is not a uv workspace (an adopted repo) needs nothing.

### Changed
- **After a gate retry the implementer hands back an amendment** (61d1e58): `Result:`,
  `Amends:`, `Gate:`, `Fixed:` and the amended `Commit:`, not its whole report again.
  `run-package` takes an agent's last hand-back as its return.
- **The first section's implementer no longer scaffolds** (21175fc). The root and the package
  skeleton are the SCAFFOLD step's. The implementer adds only its section's `configs.py`,
  dependencies and contract-3 entry.

A repo built under 2.0.0 already has its workspace, so `--scaffold` prints `done` and nothing
changes for it.

## [2.0.0] - 2026-09-29

The audit fixes. `/plugin-dev:audit-run` held a real 105-agent `run-package` (the quant
`data` package) against 1.0.0's own files. It found nine faults in the plugin and a dozen
smaller gaps, and a whole-package health check found one more. Evidence for each is under
`evals/2026-09-28-audit-run-package-1493ed56.md` and the 2026-09-29 logs.

### Breaking

| Change | What to do |
|---|---|
| The ledger is one file per section, `docs/deviations/<pkg>/<section>.md`, not `docs/deviations.md` (ff5776a) | nothing to start: the old file is still read, and its entries are edited in place. Before a run with parallel reviewers, split it by section; a moved entry keeps its first commit (508d664), so the split re-opens nothing |
| The gate's record is `.dev-team/gate/<pkg>/<section>.txt`, not `.dev-team/gate.txt` (eda16c0) | nothing; a section implemented under 1.0.0 has no record, and its reviewer says so under WARNING. `gate_on_stop.py --report --base <rev>` writes one |

### Added
- **`/dev-team:pair <pkg>/<section>`** (4def96d): edit one built section with the user turn by turn, then sort the diff into deviations and spec-changes, run the gate by hand and commit once. With it come `status.py --inputs` (the implementer's spawn block) and `gate_on_stop.py --report`.
- **`ELSEWHERE` gate lines** (eda16c0): a check whose every located failure is in an intent-test file the run did not touch no longer blocks the implementer, who may never edit `tests/intent/`. In the audited run, 9 of 9 implementers had burned all three attempts on another section's intent-test lint.
- **`TIMEOUT` gate lines and a time budget** (5ef4b86): the section's own checks run first; package-wide rows share a budget under the hook's 600 s; a row out of time no longer blocks.
- **A spec-change can come from a review report** (ff5776a): a `spec-change` report re-opens the level its **Spec-change** heading names until the ledger records it, so a round-1 `b` reviewer's finding is no longer lost.
- **Designer `delta` mode for a spec-change** (ff5776a), with a `Spec-change:` field.

### Changed
- **The format hook lints with the plugin's lint block** until the repo has a ruff config (eda16c0), so intent tests meet the rules before the first implementer merges them.
- **Round 1 needs both reports** (ff5776a): one approval no longer ships a section.
- **Design §10 contract deviations are ledger entries** (ff5776a), approved by A and folded in by `sync-plan`.
- **Researcher returns start `Result: done | blocked`** (ff5776a).
- **The implementer re-sends its return through the hand-back** after a gate retry (eda16c0): the caller receives the last hand-back, not the last turn.
- **`…/<name>/` path cells resolve** to the package default (ff5776a); `--inputs` gives a post-spec-change implementer its round's reports.
- **Lint block:** D104 off for nested `__init__.py` (eda16c0); `.claude/` excluded (ff5776a); PLR0913 off under `tests/` (508d664).
- **Smaller rules** (ff5776a):
  - the driver's reads, and a route for a row that did not move after `done`;
  - one-line ledger edits, and a refused ledger edit still gets a report;
  - the implementer reads the backlog before coding, and runs step 0 after the first scaffold;
  - testers tag approved clauses on every run;
  - a per-run scratch directory for researchers;
  - parallel-safe memory;
  - `Co-Authored-By` is allowed after the trailer.

## [1.0.0] - 2026-09-28

The remake. One driver over derived state, six roles that each answer one question, and hooks
for every mechanical check. The loop in 0.6 did not converge: a wrong contract left the
implementer no correct move, each fresh reviewer re-sampled the whole section, `run-package`
carried a plan that was stale once the spine shipped, and half of every review was lint and
tests a machine could have run. Built in eleven phases on `dev-team-remake`
(`site/notes/remake-design.md`, `site/notes/remake-00-overview.md`).

### Breaking

| Change | What to do |
|---|---|
| `/dev-team:map-project` is `/dev-team:map-repo` | type the new name; it also adopts packages, so no per-package document-mode runs follow |
| `plan-change`, `sync-design`, `review-plan`, `finalize-package`, `review-package`, `test-section`, `implement-section`, `review-section` are gone | a change to shipped code is `/dev-team:plan-package <pkg>` (or `/dev-team:plan-repo`), which writes a change file, then `/dev-team:run-package <pkg>`; one step by hand is `/dev-team:run-package <pkg> <section> --step <STEP>`; the plan review is the tester's `design-gap`; the surface is the `surface` section |
| `surface.md`, `integration.md`, `assessment.md`, `docs/plans/`, **As shipped** sections are not read | a repo mid-flight under 0.6 is migrated by `/dev-team:map-repo`, which treats the existing contracts as claims; the old files stay on disk and are not deleted by the plugin |
| review CRITICALs are not in `docs/followups.md`, and the file is never counted | the report is the queue; old entries can be ticked or left |
| `docs/reviews/` filenames carry `-r<n>-<a, b or s>` | old reports are read as round 1 single reports |
| every implementer stop runs the `docs/constraints.md` rows | a repo whose rows fail today blocks on its first build; lowering the bar is `/dev-team:set-constraints`, your call |
| `/dev-team:status` loses `--gate` and `--plan-gate`; gains `--surface <pkg>` and `--repo` | `--run-gate` and the state table are the checks |
| agents commit under the retry rule; every driver spawn's trailer is `Dev-Team-Run: run-package <pkg>`; a regeneration commit's summary is `<pkg>/<section>: regenerate <k> intent tests` | nothing, unless you parse the trailers |

### Added
- **`hooks/`** (23a6d3f). `format_on_edit.py` (`PostToolUse`: ruff on every `.py` edit by the
  implementer or tester), `gate_on_stop.py` (`SubagentStop` on the implementer: the
  constraints rows, the intent suite with ledger tolerance, a Guarded grep of the diff and
  `status.py --surface`; a `.dev-team/stop` marker or a third attempt lets it stop), and
  `guard_writes.py` (`PreToolUse`: a per-role write allowlist). Each exits 0 outside a repo
  with `docs/architecture.md`.
- **`/dev-team:map-repo`** (b4dd3aa). Lists the packages, stops at a monolith's proposed split,
  writes one package contract per package in parallel, then the repo contract from those and
  the import graph.
- **`docs/deviations.md`** (6d005fb, 6d928e5, a4be52e). One ledger for deviations
  (`proposed`, `approved`, `rejected`, `synced`) and spec-changes (`test`, `design`,
  `contract`; `open`, `resolved`), with its template in `planning-templates`.
- **Change files** (4ee8f00). `docs/changes/<slug>.md` carries a change to built or shipped
  code until `sync-plan` applies it; the architect classifies every edit EDIT, EDIT+STALE,
  CHANGE or DECIDE and archives the contract to `docs/history/` first.
- **`run-package <pkg> [<section>] [--step] [--defer]`** (2937046) and the driver's ask step:
  a block is asked once, and the answer is written to `docs/decisions.md`.
- **The review report template** and a closed CRITICAL list (6d005fb, 48a1da6).
- `status.py --surface <pkg>` and `--repo` (6d005fb); the documenter's Known gaps copy the
  latter (1eff8a1).

### Changed
- **`status.py`** (6d005fb) derives one state per section — PROBE, DESIGN, TEST, IMPLEMENT,
  REVIEW, FIX n, PLAN, DONE, BLOCKED — with its re-open rules, the ready set, rounds from
  report filenames and the next command. The driver, the hooks and the documenter run it.
- **`run-package`** (2937046) spawns every agent itself over the ready set: probes, designs,
  tests and the two round-1 reviewers in parallel, implementers one at a time; it writes only
  `docs/decisions.md` and reads each return's first line.
- **The surface is a section** (6d005fb, a4be52e): the last row of every Sections table,
  depending on every other; its README is `interface.md`; shipped = surface DONE.
- **The designer** (6d928e5) runs in `new`, `document` or `delta` mode and returns `done`,
  `stopped` or `spec-change`; **the tester** returns `done` or `design-gap` and regenerates only
  cited tests; **the researcher** extends one probe doc per source under `## <pkg>/<section>`.
- **The implementer** (a4be52e) logs deviations as `proposed`, raises `spec-change` with
  evidence, and finishes only through the stop gate.
- **The reviewer** (48a1da6): `Focus: conformance | correctness | full | defer`; A owns a
  coverage table; round 2+ is diff-scoped; `spec-change` is a verdict; it runs no command.
- **The architect** (4ee8f00) writes and edits contracts only; `plan-repo --fix` replaces
  `--revise`; `sync-plan` is the package close.
- **The documenter** (1eff8a1) writes package READMEs, `docs/index.md` and the root README,
  never `docs/api/`.
- **`git-workflow-and-versioning`** (a4be52e) shrinks to §Project convention: the run gate,
  staging by explicit path with `git commit -- <paths>`, the message table, one commit per run,
  the lock retry. It is preloaded into every committing agent.
- `workspace-scaffold` derives import contracts from the Sections table, and CI runs the
  constraints rows. `probe-source` takes `<pkg>/<section>`. `extract-legacy` reports a
  colliding skill name instead of refusing it (31dbc61). `CLAUDE.md`'s three-file rule is two
  files.
- `README.md`, `VERSIONING.md`, `site/flow.md` and the five workflow pages rewritten; the
  manifest description updated (1a28944).
- Found by the end-to-end eval, fixed before release (1a28944): an open `spec-change:design` or
  `spec-change:test` entry is answered by the next commit of the design or the intent tests,
  derived by `status.py` (nothing ever set its `Status:`, so the section re-opened forever); a
  tester run that finds no test to change still commits, stamping `conftest.py` with the design
  it checked (`intent tests current with design`, skipped like a regeneration); and a section or
  source name never starts with `report`, `summary`, `findings` or `analysis`
  (`project-structure` §4), because Claude Code refuses a subagent's Write of such a `.md`
  file.

### Removed
- The skills (b4dd3aa, 31dbc61, 1a28944) `plan-change`, `sync-design`, `review-plan`, `map-project`, `finalize-package`,
  `review-package`, `test-section`, `implement-section`, `review-section` and
  `reserved-skill-names`.
- The `surface.md`, `integration.md` and `contract-delta.md` templates; `assessment.md`;
  `docs/plans/`; **As shipped** sections; the spine; the reviewer's axis 0 and the followups
  queue; the tester's reconcile mode.

## [0.6.0] - 2026-09-22

Every review-and-fix loop gets an exit, and the two things that kept one package looping —
a cross-cutting fact patched two sections at a time, and a spine design nobody synced — are
fixed at their source.

### Added
- **Round counting for every loop** (7d7fcce, 47414b9). `status.py --rounds <pkg> |
  <pkg>/<section> | <pkg>/surface` derives consecutive `request changes` reviews since the
  last approving one from `docs/reviews/`; section rows and the `surface:` line carry
  ` r<n>`; a `request changes` plan-gate line carries the round. The reviewer runs it first
  in every mode and writes `Round:` and, from round 2, `Convergence: <k> prior unfixed,
  <m> new` — a fact still assumed by a section, module or function the last fix did not reach
  is one *unfixed* finding, not a new one.
- **A stop rule and `--defer`** (7d7fcce, 47414b9). On `request changes`, the fixing
  command is next only while the loop converges: round 1, or round 2 with every prior
  CRITICAL fixed. Otherwise the review ends with a two-command choice — one more round, or
  `/dev-team:review-plan|review-section|review-package <scope> --defer`, which re-addresses a
  plan's standing findings to their sections as review follow-ups, or re-files a section's or
  surface's as `— noted` follow-ups the finalize gate does not count. A break or a failing
  check cannot be deferred. The reviewer's return opens with a fixed three-line template,
  `Result:` / `Verdict:` / `Loop: converging | stopped`, and `/dev-team:run-package` branches
  on the third line instead of a counter of its own, which reset on every re-run.
- **Propagation on a re-plan** (7d7fcce). The reviewer files a cross-cutting finding once
  with a `touches:` list; the architect greps every design for the fact, records the union
  under `integration.md`'s new **Propagation** heading, and re-delegates every section on it
  with a `Propagate: <fact> — <sections>` line the designer reads.
- **A closed CRITICAL list** (47414b9). A break, a failing check, a wrong result on the main
  path, a security finding, the silence rules and bar-lowered. A docstring, a function's
  shape, a name, a soft-limit overrun are WARNING however sure the reviewer is. On a
  re-review, a wrong-result or security finding outside the diff is WARNING plus a `— noted`
  follow-up, so the set of blockers shrinks every round.
- A `contracts.yml` claim forbidding a bare "on `request changes`, `<fixing command>`"
  sentence in the reviewer and the three review skills (7d7fcce, 47414b9).

### Changed
- **The spine is synced before the completion plan** (7d7fcce). `run-package` spawns
  `sync-design` between the spine's review and the completion `plan-package`; the spine run's
  command list gains `/dev-team:sync-design <pkg>`; the architect's completion run checks each
  built section's design for an **As shipped** citing its last commit and performs
  `sync-design`'s step 1 itself otherwise. The plan review's seam check reads a built
  sibling's README and As shipped rows, not its stale design §5.

### Fixed
- **A same-day re-review compared against nothing** (7d7fcce). The previous report was
  "newest by date, excluding today's"; it is now the immediately preceding one, today's
  included, highest suffix on the newest date.
- **A plan finding answered in the ledger read as carried** (7d7fcce). A plan review's diff
  range now includes `docs/decisions.md` and `docs/followups.md`, and a finding whose
  follow-up is ticked is re-verified, never carried.

Evals: `evals/2026-09-22-o-plan-loop-exit.md`, `evals/2026-09-22-p-section-loop-exit.md`.


## [0.5.2] - 2026-09-21

### Fixed
- **No tags in descriptions claude.ai would reject** (91dcf5c). claude.ai, which the desktop
  app syncs marketplaces through, rejects a plugin with any `<word>` in a skill or agent
  description; `probe-source` and `researcher` each named `docs/sources/<source>.md` there,
  now `{source}`.

### Added
- **A contract forbidding a tag in any skill or agent description** (91dcf5c). The
  `researcher`'s project-skill template, a `description:` line inside its body, is exempted.

## [0.5.1] - 2026-09-20

### Fixed
- **A Guarded-constraint hit in `tests/intent/` now has an owner.** The reviewer addresses a
  finding under `packages/<pkg>/tests/intent/<section>/` to the reserved target
  `<pkg>/<section>/intent`; `/dev-team:test-section` clears that target first thing in
  reconcile mode; `/dev-team:implement-section` skips it, since it never edits that tree;
  `status.py` counts it in the section row as `<n> (<r> review, <i> intent)` and fails the
  finalize gate on it; and `/dev-team:run-package` spawns the tester, not the implementer,
  while one is open. Under 0.5.0 such a finding was addressed to the section, where only the
  implementer would read it, and nobody could clear it.
- **The tester no longer writes suppressions.** It reads `docs/constraints.md` §Guarded as
  binding its own tree and writes the assertion the design supports instead — a `typing.cast`
  rather than a `# type: ignore`. `pyproject-lint-config.toml` exempts `tests/intent/**` from
  `B017` and `PT011`, so a design that leaves an exception type unstated needs no inline
  comment; the rules still bind `src`. A repo scaffolded before this carries the old
  `per-file-ignores` and needs the two codes added by hand.
- **No agent sweeps the machine for a file.** Every agent with read-only Bash now states that
  its shell stays inside the repo, with `${CLAUDE_PLUGIN_ROOT}` the one path outside it, read
  there or through the Skill tool and never searched for; a `contracts.yml` claim fails on a
  `find /` or `find ~` in any agent or skill body. In eval K an implementer that had already
  read a skill at `${CLAUDE_PLUGIN_ROOT}` ran `find /` for it anyway.

Eval: `evals/2026-09-20-n-intent-target-and-shell-scope.md`.


## [0.5.0] - 2026-09-20

Verification becomes a column beside every layer, not a floor under the last one: a tester
writes tests from the design, the plan is reviewed before any code exists, the reviewer carries
the order of authority, designs learn what shipped, every run commits, and a driver runs a
package end to end. Design set: `site/notes/overhaul-0.5-*.md`.

### Breaking
1. **`/dev-team:plan-package` is spine-first by default** on packages with three or more
   sections: the first run designs only the section the most others depend on. `--all`
   restores 0.4 behavior. A 0.4 plan (every design present, `surface.md` present) is detected
   as complete and is not re-planned.
2. **`/dev-team:implement-section` refuses to run on `main`/`master` and refuses a dirty tree.**
   Your hand edits to `docs/decisions.md`, `docs/brief.md` and `docs/constraints.md` are
   exempt. A repo that was never committed needs `git init` and a branch.
3. **`status.py` "reviewed since build" is commit-based**: the newest review's `Commit:` must be
   the newest commit touching the section. A 0.4 review has no `Commit:` line and reads as
   stale, so every section reviewed under 0.4 shows `·` until it is reviewed once under 0.5.
4. **The reviewer grades a deviation recorded under README item 7 as WARNING at most**, unless
   it breaks a contract, a decided `D<n>`, a shipped interface, or an intent test. A 0.4
   CRITICAL for the same thing is now a WARNING.
5. **An open review-sourced follow-up addressed to `<pkg>/plan` blocks
   `/dev-team:implement-section`** for every section of `<pkg>`.

### Added, by phase
- Phase 1: three knowledge skills vendored from `addyosmani/agent-skills` (MIT) and adapted to
  Python: `test-driven-development`, `debugging-and-error-recovery`,
  `git-workflow-and-versioning`.
- Phase 2: every forked run ends in one commit of exactly the files it wrote, with a
  `Dev-Team-Run:` trailer. Reviews record `Commit:` and diff from the previous one. Skills
  fork `agent: dev-team:<name>`: under the bare name every fork had run as general-purpose.
- Phase 3: the reviewer carries the implementer's order of authority verbatim and splits
  recorded from unrecorded deviations. New `/dev-team:sync-design` appends **As shipped** to
  each design.
- Phase 4: new `tester` agent (eight agents) and `/dev-team:test-section`. Intent tests are
  written from the design before the build and reconciled after. The implementer runs them
  and never edits them.
- Phase 5: new `/dev-team:review-plan` (reviewer plan mode), the `<pkg>/plan` follow-up target,
  the architect's re-plan of only the named sections, and `status.py --plan-gate`.
- Phase 6: new `/dev-team:set-constraints` and `docs/constraints.md`. It comes first in both
  authority lists and is the reviewer's axis 0. `status.py --gate` runs the constraint rows.
- Phase 7: spine-first package planning. Integration item 0 is **Spine**, and designers accept
  `Sibling shipped:`.
- Phase 8: new `/dev-team:run-package`, a driver in your conversation over the manual
  commands. It adds `status.py --run-gate` and a `Result:` first line on every agent return.
- Phase 9: README, `site/flow.md` and the workflow pages rewritten for the above. The
  end-to-end eval on `evals/fixtures/two-package/` is logged, and the four defects it found
  are fixed: `status.py` measures plan freshness over the documents a plan review covers and
  ignores `sync-design` commits; the reviewer's new **Verdict** rule makes any standing
  CRITICAL `request changes`; the `workspace-scaffold` root template sets pytest's
  `--import-mode=importlib`, without which a two-package repo fails collection at the root;
  and the architect spawns `dev-team:designer` / `dev-team:researcher` by name, a bare name
  having silently forked a general-purpose agent.

### Fixed
- The four defects the end-to-end eval found, each re-checked on the repo it built
  (`39f29d3`): plan freshness after `sync-design`, a standing CRITICAL passing as `approve
  with fixes`, root `pytest` colliding on two packages' `tests` trees, and the architect
  spawning a bare `designer`. Evals `2026-09-19-k-end-to-end.md`,
  `2026-09-19-l-fixed-cost-per-section.md`, `2026-09-20-m-k-defect-fixes.md`.


## [0.4.0] - 2026-09-18

Probing generalizes from "one external data API" to "one external source, of a kind".

### Breaking
- **Probe docs moved to `docs/sources/<source>.md`** from
  `docs/packages/<pkg>/sources/<source>.md`, and that document's **Credentials** heading is now
  **Access**. A repo planned under 0.3.2 has its probe docs at the old path under the old
  heading, so after upgrading `/dev-team:plan-package` finds none and re-probes every source —
  real requests against real quota — and the architect's stop check looks for a heading that is
  not there. No fallback read was added: a second path every reader has to know about is the
  duplication this change exists to remove. The fix in an existing repo is two commands' worth
  of work, once:

  ```
  git mv docs/packages/*/sources/* docs/sources/     # then remove the empty sources/ dirs
  sed -i '' 's/^## Credentials$/## Access/' docs/sources/*.md
  ```

  A `source` column written before this release still reads correctly: a bare token means
  `api`, which is what every such column held.

### Added
- **`dataset` is a probe kind.** `researcher`'s **Probe mode** now branches on a `Kind:` field:
  `api` keeps the existing procedure, widened; `dataset` is new — resolve and open the data,
  record its provenance claims, profile it with a re-runnable `<source>.profile.py`, and write
  columns, dtypes as loaded against dtypes declared, null rates, cardinalities, duplicates and
  candidate keys. When the purpose names a modeling task it also runs **task fit**: the target
  and the baseline any model must beat, the leaking columns, the usable features, and whether
  the rows admit a random split at all — then what the data can and cannot actually support.
  Ordered so each finding can invalidate the next, with leakage before features, because a
  leaking column is not a weak feature but a fake result.
- **Repo-scope dataset probing.** `/dev-team:plan-repo` gains step 2b: probe the datasets the
  brief names *before* the contract, because a target that cannot carry the task, or data that
  forbids a random split, decides which packages exist. Contradictions with the brief become
  interview questions in step 3 rather than assumptions. Only datasets — an api has no call
  worth making until a section's purpose exists.
- **Write-side API facts.** The `api` template gains **Write semantics** and **Webhooks**, and
  **Access** now records the auth *mechanism* — a static key or an OAuth2 grant with its token
  endpoint, lifetime and scopes — because a client that refreshes a token is a different client
  from one that sets a header.
- **A `contracts.yml` headings claim for the probe doc**, owned by `researcher.md` and cited by
  all four of its readers. The probe doc was the one document parsed by heading with no such
  claim behind it.

### Changed
- **Probe docs are repo-wide: `docs/sources/<source>.md`, not
  `docs/packages/<pkg>/sources/<source>.md`.** An external source belongs to no package, so two
  packages consuming one were probing it twice and could disagree about what it returned; and a
  dataset probed before any package exists had nowhere to live. Every reader moved with it —
  architect, designer, reviewer, implementer, `plan-package`, `plan-change`,
  `implement-section`, `review-section`, the package-contract template, `workspace-scaffold`'s
  mkdocs excludes, `README.md` and `flow.md`.
- **The Sections table's `source` column is `<kind>:<token>`**, comma-separated for a section
  consuming more than one. A bare token still means `api`, so contracts written before this
  read unchanged. A section could previously name only one source.
- **The credential stop is now the access stop**, and the heading it reads is **Access** in both
  templates rather than **Credentials**. One stop covers a key that is unset or rejected *and* a
  dataset that is missing or unreadable — the second of which previously had no stop at all.
- **A probe doc's authority is per heading.** A probe never sends a write, so write endpoints
  and webhooks are marked `documented` while read endpoints called are `observed` and a vendor
  sandbox is `sandbox`; the **Endpoints** table carries the marker. The designer treats a
  `documented` guarantee as an assumption to state, not a fact to build on. Without the
  distinction, widening to write-side APIs would have quietly diluted the one property that
  makes a probe doc worth reading.
- **`/dev-team:probe-source` takes `<pkg | repo> <source>`** and resolves `Kind:` from the
  argument's prefix, the contract, or `api`. Its artifacts differ by kind:
  `.sample.json`/`.probe.py` for an api, `.stats.json`/`.profile.py` for a dataset.
- **The probe doc templates moved out of `researcher.md`** into
  `skills/planning-templates/references/source-probe.md`, where the architect's five already
  live, and in the numbered-bolded form its siblings use. That form is not cosmetic:
  `check_headings` reads an owner template through `template_items()`, which matches only
  `N. **Name**`, so a template written as fenced `##` headings defines nothing a claim can be
  declared against — the claim failed on its own owner before the move, not on any reader
  (`evals/2026-09-18-probe-doc-headings-claim.md`). `researcher.md` drops from 377 to 284 lines
  and invokes `planning-templates` for the template, as the architect does; `planning-templates`
  is no longer an architect-only skill.
- **The repo contract records external sources.** `references/repo-contract.md` §5 now says to
  list each api's env var and each dataset's location — the field a probe's `Access:` is
  resolved from, which every caller already assumed was there and no template ever asked for.

### Security
- **A dataset probe writes statistics, never records.** There is no sample of real rows: example
  values are allowed only where the value is the statistic (numerics, categoricals under ~50
  distinct), free text and high-cardinality strings get shape and no contents, and any column
  that looks like a person is reduced to its null rate and cardinality and named under
  **Quirks**. The existing secret-scrubbing rule covered credentials in a response; it did not
  cover personal data in a file, and a record copied into `docs/` is in the repo's history for
  good.
- **Probes never mutate.** No POST, PUT, PATCH or DELETE against a live account, whatever the
  documentation calls reversible — the probe is holding the user's real credential. The
  implementer's own fallback probe inherits the rule.

## [0.3.2] - 2026-09-17

Passes 3 and 4 of the 2026-09-17 audit: the documents people read, and the site. No prompt an
agent loads changes. `flow.md` changes, and no agent reads it.

### Fixed
- **`README.md` annotated the architect `(opus)`.** It sets `model: inherit`; `VERSIONING.md`
  records `opus` as a candidate that is not applied.
- **"The `AskUserQuestion` widget is gone" was true of subagents only.** It is removed from every
  subagent whatever its `tools:` field says — which is why the architect writes decision stubs
  instead of asking — but it is there in the main conversation, where
  `/dev-team:shape-brief` uses it at four questions per call. The README says which is which.
- **"Three conventions … marked *Project convention*" listed four.** The style guide marks three:
  docstrings, function shape, `__init__.py`. CLI commands in `src/<pkg>/cli.py` with no
  `scripts/` is `project-structure` §1's rule and now stands in its own paragraph saying so.
- **`plugin.json`'s description was "Project planning skills and agents"** — the string `/plugin`
  shows — while the `marketplace.json` row said what the plugin does. They match now.
  `README.md`'s heading is `# dev-team`, and the site's H1 follows the plugin name.
- **`CLAUDE.md` pointed at an "untagged `1.1.0` loose end"** that `VERSIONING.md` never held. It
  now says what that file holds: the `model:` decisions, and nothing else.
- **The 2026-09-16 eval credited the eval convention to `VERSIONING.md`** in two places; it is
  `plugin-dev`'s `log-eval`.
- **The Workflows section promised one page per pipeline and listed four of five.**
  `add-package.md` was missing, though it was already in `site.yml` and the nav.
- **The Contents tree omitted `CHANGELOG.md` and `skills/status/scripts/status.py`**, the only
  executable here.
- **`flow.md` credited `docs/packages/<pkg>/assessment.md` to "plan-package, map-project".**
  `map-project` writes the four repo-level documents and is explicitly told not to write package
  documents; `docs/assessment.md` is its row, one line up.
- **`flow.md`'s `docs/` map omitted three things** — `docs/legacy/inventory.md`, the probe docs
  (`docs/packages/<pkg>/sources/<source>.md` with their sample and probe script), and the
  package-level review file. The probe docs are the omission that mattered: a designer reading
  the map would not have known the one document describing an external system as it actually
  answered. The two review rows now also name `finalize-package`, which gates on their dates.
- **`skills/python-style-guide/LICENSE` was not on the reading site.** That skill's frontmatter
  says "Complete terms in LICENSE" for CC BY 3.0 attribution to Google's guide, and a pointer to
  a file the reader cannot open is not attribution. Added to `config_files`.

### Changed
- Both `forbid` claims in `contracts.yml` set `near: 40`, scoping their exemptions to the match
  rather than the line, and the `scripts/` claim drops three of its eight exemptions: two
  redundant with the prohibition sentence they sat beside, and one (`.probe.py`) that pardoned
  nothing at all. Line-scoped, those eight had left ten lines unprotected — every line in the
  bundle where `scripts/` is discussed. Needs `plugin-dev` 0.5.0.
- The `v3` / `v4` labels are no longer used to date anything, because this repo cannot resolve
  them: `0.1.0` is the initial release under `cott-plugins`, the plugin was `project-workers`
  until `259785a`, and nothing earlier is recorded. `CHANGELOG.md` says exactly that, once. The
  two places that needed the labels describe the artifact instead — an older `decisions.md`
  "predating `0.1.0`", and **dev_team v4 Flow** as the title of a gallery artifact.
- `site/README.md` says what `--evals` actually renders (a JSON of eval *definitions*) and that
  the `evals/` directory is deliberately not on the site: dated records, read in the repo beside
  the commit they name, turning over faster than the prompts the site mirrors.

## [0.3.1] - 2026-09-17

Passes 1 and 2 of the 2026-09-17 audit. Every prompt change here removes a second statement of
something already stated elsewhere, or corrects a rule that contradicted another file. No
document path, format, frontmatter shape or invoked command changed.

### Fixed
- **Two probe-skip rules for the same agent.** `architect.md`'s **Probing** said skip a probe
  doc dated today *and* valid; `plan-change` told the same architect a valid doc is never
  re-probed however old. Probing now states the change-scope relaxation as its own paragraph,
  with the reason it is deliberate, and `plan-change` step 6b states neither rule — it points at
  Probing and at its own wave B, which handles a valid doc older than the code.
- **The curator's read boundary forbade three checks `extract-legacy` requires.** "Read only
  `docs/brief.md`" ruled out testing whether `docs/architecture.md` exists, and "never read
  `.claude/skills/`" read as ruling out testing whether a skill directory does. The hard rule
  now says existence checks are fine and content is not, naming both paths.
- **The finalize-package preconditions, four copies down to two.** `implementer.md` Surface mode
  defines them and `status.py --gate` computes them; `finalize-package` runs the gate and
  restates nothing, and the README gotcha states the no-partial-mode rule rather than the list.
- **The probe prompt claimed to be defined in a file that defines none of it.** `researcher.md`'s
  **Probe mode** is now named as the definition of the five fields; `architect.md` and
  `probe-source` each keep only their own resolution rules, which differ and are not duplicates.
- **`review-section`'s Paths table omitted `docs/followups.md`**, which the run reads — the
  reviewer skips findings already listed — and appends to in step 4. `review-package` listed it.
- **Commands nobody could type.** `site/flow.md`'s three diagrams and prose (21 occurrences) and
  `status.py`'s two user-facing messages printed bare `/plan-package`-style names; plugin skills
  are always namespaced. All prefixed, and now held by a `contracts.yml` claim.
- **`site.yml`'s `workflow_skills_order` omitted `status`**, leaving it to the alphabetical tail
  of a list whose only purpose is run order.

### Changed
- `contracts.yml` declares 8 claims, up from 5, and `CLAUDE.md`'s three-file rule now *is* three
  of them rather than a reminder to remember it. Corrects 0.3.0's note that `check-contracts`
  "cannot see the other two": with `plugin-dev` 0.4.0 it sees all three, in both directions —
  a skill missing from a list, and a name in a list with no such skill.
- The new command claim carries no exemptions. `/reload-plugins` is a negative lookahead in the
  pattern rather than an `unless`, because `unless` matches a whole line and that command
  appears in all 14 guard blocks; and the one sentence in `reserved-skill-names` that needed the
  other exemption now names "the project's own unprefixed `plan-repo` command" rather than
  writing it as a command.

## [0.3.0] - 2026-09-17

### Added
- `reserved-skill-names` — a knowledge skill holding the one copy of the names this plugin's
  own skills occupy, with what each reader does with them. The architect invokes it to know
  which `.claude/skills/` entries to skip; `/dev-team:extract-legacy` reads it (the curator has
  no `Skill` tool, so the skill passes it the path) to refuse a row that would overwrite a
  plugin skill. Both previously carried their own copy of a 20-name list.
- `contracts.yml` — the cross-file claims this bundle's prompts act on, checked by
  `plugin-dev`'s `check-contracts`: the `scripts/` prohibition, the `docs/api/<pkg>.md` writer,
  the `interface.md` and section-README heading contracts, and that every shipped skill is
  named in `reserved-skill-names`.

### Changed
- `CLAUDE.md` states what a new skill must be added to, in the same change:
  `reserved-skill-names`, `README.md`'s Contents tree and knowledge-scope table, and
  `site/site.yml`'s `workflow_skills_order` for a workflow skill. `check-contracts` enforces
  the first mechanically and cannot see the other two.

## [0.2.2] - 2026-09-17

### Changed
- A CLI command may run a **single section entry point**, not only a pipeline. `surface.md`
  §3's column is now "what it runs" and names the one-off command — schema init, a backfill, a
  cache rebuild — as the case: it has no row under **Pipelines**, and that is not a gap. The
  implementer's surface-mode step 3 and `project-structure` §1 say the same, and the package
  contract's **Public surface (intent)** takes such a command as a consumer. `interface.md`
  already had the looser column, so a command can now ship in the shape it was planned.
- `project-structure` §1 says what to do before the surface exists: there is no `cli.py` until
  `/dev-team:finalize-package` runs, so call the section's function directly and let the
  command arrive with the surface.

### Fixed
- Four v3 mentions of "scripts" where the plugin means `cli.py`: `/dev-team:finalize-package`'s
  description and its "Why this is a separate step" paragraph, and two `site/flow.md` diagram
  nodes. `project-structure` §1 forbids a `scripts/` directory outright, so these contradicted
  it.
- `docs/api/<pkg>.md` was credited to `/dev-team:finalize-project` in `README.md`'s `docs/`
  layout and in `site/flow.md`'s map. The implementer writes it in surface mode as each package
  ships; `finalize-project` regenerates `index.md` and fills gaps.
- Both fixes verified by a mechanical before/after sweep over the bundle —
  `evals/2026-09-17-cross-file-contract-sweep.md`, which also confirms the 0.2.1 documenter
  heading fix holds under a check that does not share its assumptions.

## [0.2.1] - 2026-09-17

### Fixed
- `documenter` read `interface.md` by two headings the implementer never writes: `Scripts`
  (heading 3 is **CLI commands**) and `Consumers` (it is **Consumers (computed)**). The
  paragraph no longer restates that template — it names the six headings the documenter
  consumes, spelled as the owner writes them, and makes a heading it cannot find a
  **Known gaps** entry rather than something to substitute a similar heading for. Checked
  mechanically in `evals/2026-09-17-documenter-interface-heading-contract.md`; the behavioral
  impact on a real run is recorded there as unverified.
- `/dev-team:finalize-package` ran `status.py <pkg>` without `--gate`, so it got the section
  table rather than its own preconditions as `PASS`/`FAIL`. It now runs the gate, and the
  skill says the non-zero exit is the gate reporting — the `FAIL` lines are the blocker to
  return.

### Removed
- `rules/python-standards.md`. A plugin has no `rules/` component — Claude Code loads
  path-scoped rules only from `.claude/rules/` or `~/.claude/rules/` — so this one never
  loaded on an installed plugin. The conventions it pointed at already reach the agents
  through their `skills:` frontmatter; `README.md` now says how to write one in the repo you
  are building if you want it for interactive work.

## [0.2.0] - 2026-09-17

### Added
- `/dev-team:shape-brief` — new skill, runs in the main conversation so it can ask: turns a
  rough idea into `docs/brief.md` by mapping the domain, narrowing it with the user to
  now / later / out, and recording constraints, success criteria and open questions. Also
  corrects an existing brief, or appends scope to one.
- `/dev-team:plan-repo` **Revise** mode — a corrected brief, or `--revise "<notes>"`: archives
  and rewrites the repo contract, retires open decisions whose premise is gone, turns a decided
  one that now conflicts into a question, and lists stale package plans. Mode is decided by how
  the brief changed against the new `docs/history/brief-contracted.md` snapshot, not only by
  whether the contract exists.
- Repo contract Packages table gains a `covers` column mapping brief capabilities to packages.
  `/dev-team:plan-package` reads only its covered brief rows and quotes their Notes into the
  package contract's **Purpose**, so the user's own wording reaches designers.

### Changed
- Built-but-unshipped packages are treated as bound (frozen) at repo scope, like shipped ones.
- `docs/assessment.md` is written by `plan-repo` only when there is something to survey.
- A `superseded` decision no longer counts as already asked, so a retired question can be
  raised again.
- Site workflow pages cover the new flow: new-repo (shape the brief, and correcting a wrong
  contract), add-package, rebuild-from-legacy (shape the brief before mining),
  adopt-existing-repo (new scope on a mapped repo), change-shipped-code (recording scope
  changes in the brief). `docs/packages/<pkg>/brief.md` is gone from the flow page — there is
  no per-package brief.
- `dev-team/CLAUDE.md` records that the shared protocol lives in the parent repo, that git runs
  from there, and how to rebuild the site without `plugin-dev` installed.

## [0.1.0] - 2026-09-16

Initial release under `cott-plugins`.

- Seven agents (architect, designer, implementer, reviewer, documenter, curator, researcher)
  and their skills, planning a repo of packages section by section through file-based
  contracts.
- `implementer`'s Security step invokes `security-review` on matching sections rather than
  writing a security paragraph from memory — see
  `evals/2026-09-16-implementer-security-review-trigger.md`.
- Skill extraction and external source probing (`researcher` extract/probe modes,
  `/dev-team:probe-source`).
