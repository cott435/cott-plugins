# dev-team remake — overview

Branch: `dev-team-remake`. Release at the end: a **minor** bump (breaking under `0.x`, so
`0.7.0` from `0.6.0`) — proposed to `bump-version` in the last phase. Nothing here bumps or
tags anything. Date: 2026-09-27.

This is the index of the phase notes. Each numbered note after this one is one phase, done in
the order listed under **Phases**, one chat and one commit each, by `plugin-dev`'s `run-phase`
skill with the slug `remake`. The why, the workflows and their charts, the decisions and the
non-goals are in `remake-design.md`, approved before this was written. This note does not
repeat them; it says what the design turns into, file by file and phase by phase.

**Consistency, not releasability, at each boundary.** The design replaces the one shared state
derivation (`status.py`) in phase 1, and the old loop skills stop being runnable from that point
until the new driver lands in phase 8. Every boundary is still *consistent*: the bundle loads,
`check-contracts` passes, `build-site` builds, and that phase's evals pass. The branch is not
released before phase 11. Approved at the split, 2026-09-27.

## What changes, at a glance

- Agents: 8 → 8 files, six roles rewritten (`architect`, `designer`, `researcher`, `tester`,
  `implementer`, `reviewer`, `documenter`); `curator` unchanged. Every agent commits its own
  run and is spawned by the driver or a typed skill with a fixed prompt block.
- Workflow skills: 19 → 11. Kept and rewritten: `run-package` (the driver; gains `<section>`,
  `--step`, `--defer`), `plan-repo`, `plan-package`, `sync-plan`, `status` (`--gate` and
  `--plan-gate` go; `--surface`, `--repo` added), `probe-source`, `finalize-project`,
  `set-constraints`, `extract-legacy`. New: `map-repo`. Unchanged: `shape-brief`. Removed:
  `plan-change`, `sync-design`, `review-plan`, `map-project`, `finalize-package`,
  `review-package`, `test-section`, `implement-section`, `review-section`.
- Knowledge skills: 10 → 9. `reserved-skill-names` removed. `planning-templates` gains
  `change.md`, `deviations-entry.md`, `review-report.md` and the package contract's `surface`
  row, loses `surface.md`, `integration.md`, `contract-delta.md`. `git-workflow-and-versioning`
  shrinks to §Project convention with a run-gate pointer, the new message table and a lock-retry
  rule. `workspace-scaffold` derives import contracts 2 and 3 from the Sections table and runs
  `docs/constraints.md` rows in CI. The rest are unchanged.
- Hooks: new `hooks/hooks.json` with three scripts — `format_on_edit.py` (`PostToolUse`),
  `gate_on_stop.py` (`SubagentStop`, implementer only), `guard_writes.py` (`PreToolUse`).
- Scripts: `skills/status/scripts/status.py` rewritten to the state spec; its parsers are
  imported by the hooks.
- `contracts.yml`: every claim re-pointed or deleted with the file it guarded; new claims for
  the review report headings, the deviations-entry fields, the state vocabulary, the hook
  matchers, and `frontmatter` for agents and skills. `README.md`, `CLAUDE.md` (two-file rule),
  `VERSIONING.md`, `site/` rewritten in the last phase.
- Every added or removed skill lands in the files the plugin's `CLAUDE.md` names — until phase
  10, `reserved-skill-names`, `README.md`'s Contents tree and `site/site.yml`; from phase 10,
  the last two — in the same commit, and its checks run before that commit.

## The contents tree

Additions `+`; changed `~`; removed `✕`; unmarked is unchanged.

```
dev-team/
├── .claude-plugin/plugin.json            ~ description (phase 11); version by bump-version only
├── agents/
│   ├── architect.md          ~ contracts only: survey, interview gate, WRITE or EDIT/EDIT+STALE/CHANGE/DECIDE, archive, sync-plan close, map-repo phases
│   ├── designer.md           ~ modes new/document/delta; exits done/stopped/spec-change; commits; spawned by the driver
│   ├── researcher.md         ~ probe mode extends one doc under `## <pkg>/<section>`; always commits
│   ├── tester.md             ~ exits done/design-gap; red by construction; regenerate cited tests; no reconcile mode
│   ├── implementer.md        ~ `surface` is a section; deviations.md `proposed`; spec-change; stop marker; no constraints/branch/baseline step
│   ├── reviewer.md           ~ Focus conformance/correctness/full/defer; coverage table; round 2+ diff-scoped; closed CRITICAL list; runs no command
│   ├── documenter.md         ~ Known gaps = status.py --repo plus document-only checks
│   └── curator.md
├── hooks/
│   ├── hooks.json            + PostToolUse ruff · SubagentStop gate · PreToolUse write guard
│   ├── format_on_edit.py     + ruff format + check --fix on .py edits by implementer and tester
│   ├── gate_on_stop.py       + constraints rows, intent suite (ledger tolerance), Guarded grep, --surface; marker + attempt counter
│   └── guard_writes.py       + per-role path allowlist
├── skills/
│   ├── run-package/          ~ the driver: ready set from status.py; spawns every agent; asks on BLOCKED; <section>, --step, --defer
│   ├── plan-repo/            ~ WRITE or edit classification; dataset probes; archive
│   ├── plan-package/         ~ Sections table ends with `surface`; edit classification; PLAN step under the driver
│   ├── map-repo/             + forked → architect; three phases; monolith stops at the split
│   ├── sync-plan/            ~ package close: approved deviations and change files into the contracts
│   ├── status/               ~ SKILL.md to the new flags; scripts/status.py rewritten, parsers importable
│   ├── probe-source/         ~ re-probe after the world changed; appends the section heading
│   ├── finalize-project/     ~ trimmed procedure; Known gaps from --repo
│   ├── set-constraints/      ~ wording: the file is the hook's spec; "after shape-brief" dropped
│   ├── extract-legacy/       ~ no reserved-names check; a colliding name is reported
│   ├── shape-brief/
│   ├── planning-templates/   ~ references: package-contract (surface row), change.md +, deviations-entry.md +, review-report.md +, source-probe (per-section heading); surface.md ✕ integration.md ✕ contract-delta.md ✕
│   ├── git-workflow-and-versioning/  ~ §Project convention: run-gate pointer, staging, new message table, one commit per run, lock retry
│   ├── workspace-scaffold/   ~ contracts 2 and 3 from the Sections table; CI runs constraints rows
│   ├── security-review/  · project-structure/  · python-style-guide/  · python-implementation/
│   ├── test-driven-development/  · debugging-and-error-recovery/
│   ├── plan-change/ ✕  sync-design/ ✕  review-plan/ ✕  map-project/ ✕  finalize-package/ ✕
│   ├── review-package/ ✕  test-section/ ✕  implement-section/ ✕  review-section/ ✕
│   └── reserved-skill-names/ ✕
├── evals/
│   ├── sets/                 + designer, tester, reviewer, architect, map-repo, run-package, hooks; ~ implementer, researcher, documenter
│   └── fixtures/             + state-cases/ (phase 1), hook-events/ (phase 2); two-package/ (unchanged, the end-to-end input)
├── contracts.yml             ~ see Files other files parse
├── README.md  CLAUDE.md  VERSIONING.md  CHANGELOG.md   ~ phase 10 (CLAUDE.md), phase 11 (the rest)
└── site/                     ~ flow.md, five workflows/, site.yml (phase 11); notes/ (this plan)
```

## Files other files parse

Every row is a `contracts.yml` entry some phase writes or rewrites; the phase note names which.

| Path or heading | Written by | Read by | Status |
|---|---|---|---|
| `status.py` docstring: the state vocabulary `PROBE · DESIGN · TEST · IMPLEMENT · REVIEW · FIX n · PLAN · DONE · BLOCKED` | `status.py` (phase 1) | `run-package` (phase 8, `cites`) | new (claim lands in phase 8) |
| `planning-templates/references/review-report.md`: header lines and headings **CRITICAL**, **WARNING**, **SUGGESTION**, **Coverage**, **Carried**, **Spec-change**, **Deferred** | template (phase 1) | reviewer (phase 5), implementer (phase 4, **CRITICAL**, **WARNING**), `status.py` (`Verdict:`, `Commit:`, `Round:`, `Convergence:` — a mechanical eval, phase 1) | new (claim lands in phase 5) |
| `planning-templates/references/deviations-entry.md`: **Clause**, **Said**, **Did**, **Found**, **Why**, **Status**, **Raised by**, **Resolved by** | template (phase 1) | implementer (4), reviewer (5), designer and tester (3), architect (6), `status.py` and `gate_on_stop.py` (mechanical) | new (claim lands in phase 3, readers added per phase) |
| `planning-templates/references/change.md`: **Change goal**, **Affected sections**, **Contract changes**, **Downstream impact**; `Status:` | template (phase 1) | architect (6), designer (3), `status.py` (mechanical) | new (claim lands in phase 6) |
| package contract Sections table columns `section`, `responsibility`, `path`, `builds with`, `depends on`, `source`; last row `surface` | `planning-templates/references/package-contract.md` (phase 1) | `status.py`, every loop agent | changed (surface row); no new claim — the columns are parsed loosely by header name as today |
| section README's seven headings; `interface.md`'s seven | implementer (phase 4, owner) | documenter, reviewer, designer, architect | unchanged headings; readers re-pointed as each is rewritten |
| design template's eleven headings + **Module plan**; first line `Mode:` | designer (phase 3, owner) | tester (3), reviewer (5) | unchanged headings; `As shipped`/`Revision` gone; claim re-pointed in phase 3 and 5 |
| probe doc headings + `## <pkg>/<section>` per-section entries | `source-probe.md` (phase 3) | designer, architect, reviewer, implementer | new heading; existing claim kept |
| `docs/constraints.md` **Floor**, **Enforced**, **Measured**, **Guarded**, **Exceptions** | `set-constraints` template (unchanged) | `gate_on_stop.py` (2), `status.py` (1), reviewer (5), tester (3), `workspace-scaffold` (4) | unchanged; readers re-pointed (implementer and `status` SKILL.md leave; the hook is a mechanical eval) |
| `git-workflow-and-versioning` §Project convention rule names | the skill (phase 4, owner) | every committing agent (each phase updates its reader span) | changed (rule list) |
| `hooks/hooks.json` matchers `^dev-team:implementer$` and the scripts' `agent_type` tables | hooks (phase 2) | — (a `forbid`-style claim that each matcher names an agent under `agents/`) | new (claim lands in phase 2) |

## Phases

One commit per phase. Commit messages begin `dev-team remake (phase N): <what>`. After every
phase that touches an agent or skill: the plugin's own rules (its `CLAUDE.md` as it stands in
that phase), `check-contracts`, `build-site`, then the phase's evals logged with `log-eval`,
then the commit.

| Phase | Note | Commit contents | Depends on |
|---|---|---|---|
| 0 | 00 | the phase notes, the eval sets and the ledger; four gap answers and one assumed fact in the design; then platform-fact evals PF-1…PF-5 from the design's assumed facts | design |
| 1 | 01 | `status.py` to the state spec, `status` SKILL.md, `planning-templates` (surface row, `change.md`, `deviations-entry.md`, `review-report.md`), `frontmatter` claims, `evals/fixtures/state-cases/` | 0 |
| 2 | 02 | `hooks/hooks.json`, the three scripts, `evals/fixtures/hook-events/`, the hook-matcher claim | 0 (PF-1, PF-2), 1 |
| 3 | 03 | `designer.md`, `tester.md`, `researcher.md`, `source-probe.md` per-section heading; deviations-entry claim | 1 |
| 4 | 04 | `implementer.md`, `git-workflow-and-versioning`, `workspace-scaffold` | 1, 2 |
| 5 | 05 | `reviewer.md`; review-report claim | 1, 4 |
| 6 | 06 | `architect.md`, `plan-repo`, `plan-package`, `sync-plan`; `integration.md`, `surface.md`, `contract-delta.md` deleted with their claims; change-file claim | 1, 3 |
| 7 | 07 | `skills/map-repo/`, architect map scope; `map-project` deleted under the three-file rule | 6 |
| 8 | 08 | `run-package` rewritten; state-vocabulary claim; plan-loop-exit claim rewritten | 2, 3, 4, 5, 6 |
| 9 | 09 | `documenter.md`, `finalize-project` | 1 |
| 10 | 10 | `probe-source`, `set-constraints`, `extract-legacy`, `reserved-skill-names` deleted, plugin `CLAUDE.md` two-file rule, `names_listed` trimmed | 1, 3 |
| 11 | 11 | eight removed skills deleted; `contracts.yml` final; `README.md`, `VERSIONING.md`, `plugin.json` description, `site/flow.md`, `site/workflows/`, `site/site.yml`, `CHANGELOG.md` unreleased; end-to-end eval; fixed-cost measurement; release proposed in chat | all |

Phases 9 and 10 may pair in one chat. No other pair: every other phase either rewrites an
agent over 200 lines or runs a behavioral set above 0.5M tokens.

## Breaking changes to list in `CHANGELOG.md`

From the design's **What must not break**; listed here so phase 11 finds them.

1. `/dev-team:map-project` is `/dev-team:map-repo`; it also adopts packages, so no per-package
   document-mode runs follow.
2. `plan-change`, `sync-design`, `review-plan`, `finalize-package`, `review-package`,
   `test-section`, `implement-section`, `review-section` are gone. A change to shipped code is
   `/dev-team:plan-package <pkg>` (or `/dev-team:plan-repo`), which writes a change file, then
   `/dev-team:run-package <pkg>`; one step by hand is
   `/dev-team:run-package <pkg> <section> --step <STEP>`; the plan review is the tester's
   `design-gap`; the surface is the `surface` section.
3. `surface.md`, `integration.md`, `assessment.md`, `docs/plans/`, **As shipped** sections are
   not read. A repo mid-flight under 0.6 is migrated by `/dev-team:map-repo`, which treats the
   existing contracts as claims; the old files stay on disk and are not deleted by the plugin.
4. Review CRITICALs are not in `docs/followups.md`, and the file is never counted; the report
   is the queue. Old entries can be ticked or left.
5. `docs/reviews/` filenames carry `-r<n>-<a, b or s>`; old reports are read as round 1 single
   reports.
6. Every implementer stop runs the `docs/constraints.md` rows; a repo whose rows fail today
   blocks on its first build. Lowering the bar is `/dev-team:set-constraints`, the user's call.
7. `/dev-team:status` loses `--gate` and `--plan-gate`; gains `--surface <pkg>` and `--repo`.
8. Agents commit under the retry rule and every driver spawn's trailer is
   `Dev-Team-Run: run-package <pkg>`; a regeneration commit's summary is
   `<pkg>/<section>: regenerate <k> intent tests`.

## Deviations

- **PF-5 came out differently.** The design's Platform facts row said two agents committing at
  once collide on `.git/index.lock`, and that a retry of up to ten two-second waits lands both
  commits. Run as written (`git add <f> && git commit -m …`), there was no lock error. In git
  2.48, a plain `git commit` holds no lock while its hooks run and re-reads the shared index
  before writing the tree. So the other agent's staged file went into this agent's commit, and
  the other agent's own commit failed with `nothing to commit`. Nothing was lost on disk, but
  the result was one commit with one agent's message, and no error either agent could see.
  What was done instead: one fix, rerun twice. Commit with an explicit pathspec, `git add
  <paths>` then `git commit -m … -- <paths>`. That commits only those paths and holds the lock
  for the whole commit, so a parallel `git add` or `git commit` gets the `index.lock` error the
  retry rule is written for. Under a forced lock, the agent retried twice and landed its commit.
  Both runs gave two commits with one file each. The design is not edited; phases 2 and 4 carry
  the corrected rule (ledger notes). Log: `evals/2026-09-27-remake-platform-facts.md`.
- **PF-1 found something the design did not assume.** After a `SubagentStop` exit 2 and a
  retry, the parent's Agent result is the text of the subagent's **last** turn, not its first
  reply. The driver branches on a `Result:` first line, which a gated implementer loses unless
  it repeats its return message after every retry. This is a note for phases 2, 4 and 8, not a
  change here.
