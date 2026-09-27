# 06 — architect and its three skills

Phase 06. Rewrites the architect to write and edit contracts only: survey, the interview gate,
WRITE for a new contract or a change list classified per item against the package state table
(unplanned / planned / built / shipped) into EDIT, EDIT+STALE, CHANGE (a `docs/changes/<slug>.md`)
or DECIDE (stop), an archive copy to `docs/history/` before every edit, and `sync-plan` as the
package close that applies approved deviations and pending change files to the canonical
contracts after verifying each against the code. `plan-repo`, `plan-package` and `sync-plan`
are rewritten to spawn it; `plan-package` always ends the Sections table with the `surface` row
and runs under the driver at the PLAN step. The `integration.md`, `surface.md` and
`contract-delta.md` templates are deleted with their claims: nothing reads them after this
phase. The gap it closes: a canonical contract could carry a future-tense claim about shipped
code, and a change to a bound package was a separate skill with its own document tree.

`map-repo` is phase 7; this phase leaves the architect's `map-repo` scope as a one-line
pointer ("phase 7").

## Decisions

- **The package state table** the architect classifies against is derived, not stored:
  `contract.md` exists → planned; any section path has code → built; `interface.md` exists and
  the `surface` section is DONE (`status.py`) → shipped. The architect runs `status.py <pkg>`
  for the last one rather than re-deriving it.
- **Classification per change item, at section granularity:** a section is *built* when its
  path has code, *shipped* when its package's `surface` section is DONE. An item touching no
  built or shipped section → EDIT (edit the contract now); an EDIT that changes a row, a shape
  or a convention a *planned* package's contract or **Consumes** table depends on → EDIT+STALE
  (edit now, list each stale package in the return); an item touching a built or shipped
  section → CHANGE (write `docs/changes/<slug>.md`, `Status: open`, edit nothing canonical);
  an item that reverses a dependency edge, creates a cycle, or changes a convention two bound
  packages disagree on → DECIDE (stub a `D<n>`, stop). One change item is exactly one of
  these; a request with several items yields several rows.
- **`sync-plan` never edits `interface.md`** (the implementer's file) or a design; its commit
  scope is `plan <pkg>`. On a greenfield WRITE the ledger is created only when a stub is
  written.
- **Archive** is `docs/history/<date>-<name>.md`, a verbatim copy of the file about to be
  edited (`architecture.md`, `<pkg>-contract.md`), suffix `-2`, `-3` if taken. Never for a
  WRITE.
- **`sync-plan` verifies before it applies:** for an `approved` deviation, the `Did:` is
  present in the code at the clause's path; for a change file, every **Affected sections** row
  is DONE and every **Contract changes** item is realized in the code; an unverifiable item is
  listed in the return and left open. Applied entries get `Status: synced` / `Resolved by:
  <sha>`; a synced change file gets `Status: synced`. Consumers of a changed shipped name are
  recomputed with the shared grep and classified: CHANGE per shipped consumer (a new change
  file per package), STALE per planned one (listed).
- **Interview tags** are `Raised by: /dev-team:plan-repo (interview)`, `/dev-team:plan-package
  <pkg> (interview)`, `/dev-team:map-repo (interview)`; the re-run rule (every tagged entry
  counts as asked whatever its status but `superseded`) stays verbatim.
- **Dataset probes at repo scope** stay in `plan-repo` (one researcher per dataset the brief
  names, `Section: repo`); `plan-package` probes nothing — PROBE is the driver's step.
- **The architect spawns** researchers (datasets, `plan-repo`) and architects (`map-repo` phase
  2, next phase); never designers.

## Files

| Path | Change |
|---|---|
| `agents/architect.md` | rewritten in full — specification below |
| `skills/plan-repo/SKILL.md` | rewritten: modes New / Extend / Revise stay; step 4 becomes WRITE or the change list; `--fix "<notes>"` replaces `--revise` in the argument-hint (the design's argument); run gate first |
| `skills/plan-package/SKILL.md` | rewritten: preconditions, survey, interview, WRITE (Sections table ends with `surface`) or change list; no probing, no designers, no integration or surface doc; `Package:` line for the driver; run gate first unless spawned by the driver |
| `skills/sync-plan/SKILL.md` | rewritten: argument `<pkg>`; the close per **Decisions** |
| `skills/planning-templates/SKILL.md` | the three old rows removed |
| `skills/planning-templates/references/integration.md`, `surface.md`, `contract-delta.md` | deleted |
| `skills/planning-templates/references/repo-contract.md` | `/dev-team:map-project` → `/dev-team:map-repo`; "edited later … by sync-plan after a change ships" wording kept |
| `contracts.yml` | integration-headings and surface-headings claims deleted; `As shipped` claim deleted (its owner goes in phase 11; the architect and plan-package readers stop citing it now — delete the whole claim here and note phase 11 removes the owner file); change-file `headings` claim added; deviations-entry claim gains the architect; architect's spawn-name claim re-pointed at `researcher|architect`; §Project convention reader span updated; `plan-loop-exit` claim's `skills/review-plan/SKILL.md` entry left until phase 8 |

## Specification

### `agents/architect.md`

```yaml
---
name: architect
description: Writes and edits the contracts — the repo contract docs/architecture.md and each package contract — and nothing else. Surveys, asks through the decisions ledger, writes a new contract or classifies each change item as EDIT, EDIT+STALE, CHANGE (a change file) or DECIDE (stop), archives before every edit, and as sync-plan applies approved deviations and change files after verifying them against the code. Spawns researchers for datasets and architects for map-repo; never designs. Invoked by /dev-team:plan-repo, /dev-team:plan-package, /dev-team:sync-plan and /dev-team:map-repo, and by /dev-team:run-package at the PLAN step and the package close.
tools: Agent, Read, Write, Edit, Glob, Grep, Bash, Skill, WebSearch, WebFetch
model: inherit
memory: project
skills:
  - project-structure
  - git-workflow-and-versioning
color: purple
---
```

Headings, in order: `## Hard rules`, `## Scopes`, `## Questions — the interview rule`,
`## Project skills`, `## The document map`, `## Packages and sections`, `## Decisions`,
`## Edits — the change list`, `## Probing`, `## sync-plan — the package close`, `## map-repo`
(pointer, filled in phase 7), `## Final return message`, `## Commit`, `## Memory`.

**Hard rules** keep: write only under `docs/`; Bash read-only but for `git add`/`commit`;
shell inside the repo; every `Agent` call `subagent_type: "dev-team:<agent>"` and
`run_in_background: false`, fan-outs in one message; `WebSearch` for external facts; invoke
`planning-templates` before writing a contract, a change file or a deviations status. New:
never edit `docs/packages/*/design/**` or `docs/reviews/**`; never spawn `dev-team:designer`;
never write a signature at repo scope; a canonical contract never carries a future-tense
claim outside a greenfield package.

**Scopes** table: repo (`plan-repo`, `map-repo` phase 3) → `docs/architecture.md`; package
(`plan-package`, `map-repo` phase 2) → `docs/packages/<pkg>/contract.md`; close (`sync-plan`).

**Project skills**: enumerate `.claude/skills/*/`, subtract `ls ${CLAUDE_PLUGIN_ROOT}/skills`
(the plugin's own, derived at run time); a project skill whose name collides with a plugin
skill is reported in the return as `collides with a plugin skill: <name>` and left out. The
rest as today (candidate skills per package, `builds with` per section, the two signals).

**The document map**: the design's file table, canonical rows only (`brief.md`, `history/`,
`architecture.md`, `sources/`, `decisions.md`, `followups.md` (backlog), `changes/`,
`deviations.md`, `packages/<pkg>/contract.md`, `design/`, `interface.md`, `reviews/`), each
with its writer. `docs/plans/`, `assessment.md`, `integration.md`, `surface.md` gone.

**Packages and sections** as today, plus: the last row of every Sections table is `surface`
(the template's rule); `<pkg>/surface` is a section, not a reserved name.

**Decisions** as today (the ledger shape, `Scope:`, `Status:`, retiring, older ledgers).

**Edits — the change list**: the four outcomes per **Decisions**; the archive; the return row
per item `| <item> | EDIT / EDIT+STALE (<pkgs>) / CHANGE docs/changes/<slug>.md / DECIDE D<n> |`.
A change file is written from `planning-templates/references/change.md`.

**Probing**: datasets only, at repo scope, one `dev-team:researcher` per dataset the brief
names, prompt fields `Mode: probe`, `Kind: dataset`, `Source:`, `Purpose:`, `Access:`,
`Extracted skill:`, `Section: repo`, `Write to:`; the access stop as today; **Supported tasks**
and **Splitting** read back into the contract.

**sync-plan — the package close** per **Decisions**, step by step, with the shared consumer
grep written out once: `grep -rln "from <pkg>\b\|import <pkg>\b" packages/*/src` excluding
`<pkg>`, plus every `docs/packages/*/contract.md` whose **Consumes** names `<pkg>`.

**Final return message**: `Result: done | stopped | blocked`; then the rows per change item (or
the paths written on a WRITE), stale packages, provisional dependencies, `D<n>` stubs, `Commit:
<sha>`, the next command. The interview stop message verbatim as today, with the new tags.

**Commit**: §Project convention (preloaded); scope `plan <target>`; stage every file the run
and its researchers wrote (researchers now commit their own probe docs, so stage only what the
architect wrote); trailer `Dev-Team-Run: <skill> <argument>` from the skill, or `run-package
<pkg>` from the driver's `Run:` line.

### `skills/plan-package/SKILL.md`

```yaml
---
name: plan-package
description: Write or edit one package's contract under the repo contract - the Sections table (ending with the surface row), section interfaces, pipelines, public surface intent, consumes. On an existing contract each change item is classified EDIT, EDIT+STALE, CHANGE (a change file) or DECIDE (stop). Run after plan-repo, when the repo contract changed, when a spec-change at contract level is open, or to request a change; run-package runs it at the PLAN step.
argument-hint: "<pkg> [change request]"
arguments: [pkg, request]
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---
```

Body: the Guard block as today; `Package:` line rule for the driver (`Package: <pkg>` and
`Run: run-package <pkg>` mean: skip the run gate, use that trailer); step 1 run gate
(`python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate <pkg>` — FAIL →
`Result: blocked` with its lines) unless spawned by the driver; step 2 survey (the repo
contract's row, the brief's covered rows, dependencies' `interface.md` or provisional
contracts, the code directory if any, `docs/deviations.md` open `spec-change:contract`
entries naming the package, open change files, project skills); step 3 interview rule with
the tag; step 4 WRITE (no contract: `planning-templates` → `package-contract.md`; Sections
table ends with `surface`) or the change list (the argument, open `spec-change:contract`
entries, the repo contract's diff since the archive), classified and applied per the agent's
**Edits**; step 5 decisions; step 6 commit and return, next command `/dev-team:run-package
<pkg>`. No probing (the driver's PROBE step), no designers, no adoption section (`map-repo`).

### `skills/plan-repo/SKILL.md`

Frontmatter as today with `argument-hint: "[brief | addition | --fix \"<notes>\"]"` and the
description's `--revise` → `--fix`. Body: the argument forms (`--fix` replaces `--revise`,
same semantics); modes New / Extend / Revise / Unchanged as today; steps: persist the brief;
run gate; survey (bound packages; no `docs/assessment.md` — the survey travels in the run);
probe datasets; interview rule; the contract: New → WRITE from `repo-contract.md`; Extend and
Revise → the change list per the agent's **Edits** (archive first); decisions; commit and
return, next command `/dev-team:plan-package <pkg>` for the first stale or unplanned package.

### `skills/sync-plan/SKILL.md`

```yaml
---
name: sync-plan
description: Close a package - fold every approved deviation and every pending change file into the canonical contracts after verifying each against the shipped code, mark them synced, and recompute the consumers of any changed public name. run-package runs it when every section is DONE; run it by hand after editing deviations.md or a change file.
argument-hint: "<pkg>"
arguments: [pkg]
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---
```

Body: Guard; `Package:`/`Run:` rule; run gate unless spawned; the close per the agent's
**sync-plan — the package close**; commit and return with one row per entry (`synced` /
`left open: <why>`), the consumer classification, next command.

### `contracts.yml`

```yaml
  - name: change file headings its readers parse are ones planning-templates defines
    owner: skills/planning-templates/references/change.md
    owner_span: ['1. **Change goal**', null]
    readers:
      - file: agents/architect.md
        cites: ['Change goal', 'Affected sections', 'Contract changes', 'Downstream impact']
      - file: agents/designer.md
        cites: ['Contract changes']
```

Deviations-entry claim gains `- file: agents/architect.md` with `cites: ['Clause', 'Did',
'Status', 'Resolved by']`. The architect spawn claim's pattern becomes
`'\b(?<!dev-team:)(architect|researcher)`? per (package|source|dataset)'` with `unless:
['dev-team:architect', 'dev-team:researcher']`. Delete: the integration-headings claim, the
surface-headings claim, the `As shipped` claim. The `plan-loop-exit` claim's `files:` list
drops nothing yet (the old skill files still exist until phase 11; the pattern will not match
them after phase 8 rewrites the claim).

## Steps

1. Delete the three references; edit `planning-templates/SKILL.md` and `repo-contract.md`.
2. `agents/architect.md`.
3. `plan-package`, `plan-repo`, `sync-plan`.
4. `contracts.yml`; plant a bare `designer per section` in a scratch architect and watch the
   spawn claim fail.
5. The plugin's own rules (no skill added or removed).
6. `check-contracts`; `build-site`.
7. Evals, through `run-evals`, logged with `log-eval`.
8. Commit: `dev-team remake (phase 06): architect writes and edits contracts; plan-repo, plan-package, sync-plan; integration and surface templates removed`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 6.1 | mechanical | `contracts.yml` | — | `check-contracts` + the plant | all PASS; the plant FAILs |
| 6.2 | behavioral | `architect` | previous | `evals/sets/architect.json` 1, 2, 3 | every expectation passes for `with_skill`; `old_skill` fails the `surface` row, the CHANGE outcome and the `synced` status |
| 6.3 | load | `plan-repo`, `plan-package`, `sync-plan` | — | `claude --plugin-dir ./dev-team -p "/dev-team:sync-plan data"` in a `state-cases` `shipped` build | the run returns `Result: done` and a commit with the `Dev-Team-Run: sync-plan data` trailer |

## Done when

- `ls skills/planning-templates/references/` lists exactly `change.md`, `deviations-entry.md`, `package-contract.md`, `repo-contract.md`, `review-report.md`, `source-probe.md`.
- `grep -c 'integration.md\|surface.md\|Spine' agents/architect.md skills/plan-package/SKILL.md skills/plan-repo/SKILL.md skills/sync-plan/SKILL.md` is 0 on every file.
- `check-contracts` all PASS; `build-site` exits 0.
- Logs for 6.1–6.3 in `evals/README.md`.
- The ledger row for phase 6 reads `done`.

## Deviations

- **`package-contract.md` and `repo-contract.md` edited beyond the Files table.** Deleting
  `integration.md` and `surface.md` left `package-contract.md` telling the architect to raise a
  repo-shape change "under **Repo contract deviations** in the integration doc", and saying
  `/dev-team:plan-package` probes every `source` entry before its designers. `repo-contract.md`
  said a boundary's signature is fixed in the providing package's `surface.md`. Now: a repo-shape
  change is a `D<n>` scoped `repo` for `/dev-team:plan-repo`; the driver's PROBE step probes the
  column; the signature lives in the providing contract's **Section interfaces**. Phase 1's ledger
  row had assigned the first two to phase 6.
- **The spawn claim's pattern could not fail the note's own plant.** The note's pattern,
  `(architect|researcher)`? per (package|source|dataset)`, does not match `designer per section`,
  which step 4 plants. A second branch, `` \b(dev-team:)?designer`? per section ``, was added:
  the architect never spawns designers, so the prefixed form fails too. Both plants fail
  (`architect.md:333`, `:464`), and the prefixed designer line fails at `:333`.
- **The architect closes a `spec-change:contract` entry it answers.** The note is silent. The
  design lists the architect as a writer of `resolved`, and `status.py` holds a section at PLAN
  while such an entry is open, so without the close a `plan-package` run under the driver would
  loop. **Edits** now sets `Status: resolved` and `Resolved by:` (the run trailer, plus the
  change file after a CHANGE) after an EDIT, EDIT+STALE or CHANGE; a DECIDE leaves it open.
- **`--fix` keeps `--revise`'s semantics**, as the note says: the notes are appended to the brief
  under `## Revision — <date>`. The design's Components row says `--fix` "corrects without
  touching the brief". The note was followed; the design is not edited.
- **`sync-plan`'s `Resolved by: <sha>`** is the section's latest approving review `Commit:`,
  since the close's own commit does not exist when the line is written.
- **6.3's commit bar cannot hold on `shipped` as written.** Nothing is open there, so the close
  writes nothing, and §Project convention rule 4 says a run that writes nothing commits nothing:
  the run returned `Result: done` and `Commit: none`. A second build of `shipped` with one
  committed, verifiable `approved` deviation gave `Result: done` and a commit carrying
  `Dev-Team-Run: sync-plan data`.
- **6.2's set prompts were rewritten (iteration 2), on the user's call.** In iteration 1 every
  prompt quoted the new skills' tasks, so the 0.6 architect passed 24/24 as well and the
  baseline half of the bar could not be measured. Each prompt now names the forking skill and has
  the executor read that `SKILL.md` from its configuration's own plugin copy. Iteration 2: 100%
  vs 63%. The 0.6 architect now fails the `surface` row (eval 1, 6/8) and the CHANGE outcome
  (eval 2, 1/7). **The `synced` half of the bar is still missed**: eval 3's baseline, finding no
  `docs/plans/<slug>/` for the 0.6 `sync-plan`, improvised the close from the fixture and passed
  9/9. The bar, the result and what was tried are in
  `evals/2026-09-27-remake-phase6-architect.md`.
- **Commit prefix `(phase 6)`**, not the note's `(phase 06)`, to match the ledger's grep.
