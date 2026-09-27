# 03 — designer, tester, researcher

Phase 03. Rewrites the three agents that run before any code exists: the designer (modes
`new`, `document`, `delta`; exits `done`, `stopped`, `spec-change`; commits its own design),
the tester (exits `done` or `design-gap`; red by construction on new code, green on adopted
code; regenerates only the tests an approved deviation or a `spec-change:test` cites; no
reconcile mode), and the researcher in probe mode (one document per source, extended under a
`## <pkg>/<section>` heading per consuming section; always commits). Each is now spawned by the
driver with a fixed prompt block rather than by the architect or a typed skill, so each agent's
**Inputs** section is the contract the driver copies in phase 8. The gap it closes: the 0.6
tester had a reconcile mode that edited tests to match code, the designer was briefed through an
integration doc nobody read, and a probe doc could not say which section it served.

## Decisions

- **Every agent commits and every agent has Bash** for that purpose; the designer gains
  `Bash` in `tools`. Each agent's shell rule stays: inside the repo, `${CLAUDE_PLUGIN_ROOT}`
  the one exception, `find /` and `find ~` off limits.
- **The spawn prompt fields are owned by the agent** in a `## Inputs` table (field · what it
  is · `none` allowed?). `run-package` (phase 8) copies the field names verbatim; the
  `contracts.yml` claim for that is a `headings` claim whose owner span is each agent's Inputs
  table, added in phase 8.
- **`design-gap` writes nothing.** The tester returns the gaps and leaves no tree, so the
  derived state stays TEST and a re-run re-finds the gap. A gap is: an **Interfaces** row with
  no signature or no module in **Module plan**; a consumed name in no document the tester was
  given; an **Error handling and logging** case with no exception type; a **Workflow /
  pipeline** step with no output. A mere silence (a case the documents do not support) is not
  a gap: the case is not written and the return says so.
- **The tester does not preload `test-driven-development`.** Its inventory step reads that
  skill's **The TDD Cycle** RED paragraph by path
  (`${CLAUDE_PLUGIN_ROOT}/skills/test-driven-development/SKILL.md`) with the Read tool. The
  skill file is unchanged; the design's Cost line (the TDD skill trimmed to RED for the
  tester) is met by not preloading it.
- **Regenerated tests carry the tag** ` (deviation <date>)` appended to the docstring's first
  line, where `<date>` is the entry heading's date. The regeneration commit summary is
  `<pkg>/<section>: regenerate <k> intent tests`. Both are what `status.py` reads.
- **Tester details settled here:** the regenerate summary is the literal string
  `<pkg>/<section>: regenerate <k> intent tests` (plural whatever `k` is — `status.py` matches
  it); on a regenerate run `Adopted code:` is whatever the row says and the delete-passing-tests
  step does not apply; the tester never edits `docs/deviations.md` statuses (`sync-plan` sets
  `synced`); a `design-gap` return is twenty lines or fewer with `Commit: none`; `Not written:
  none` when every case is supported; code at the path with `Mode: new` and `Adopted code: no`
  (an aborted run's scaffold) changes nothing — the intent procedure runs and deletes what
  passes; the driver's `Run: run-package <pkg>` line becomes the trailer `Dev-Team-Run:
  run-package <pkg>` verbatim.
- **Adopted code:** the driver passes `Adopted code: yes` when the section path has code and
  the design's first line is `Mode: document`. The tester then expects the suite green; a red
  test is a `spec-change:design` entry (`Found:` the failing assertion) and the return is still
  `done`, listing the entry.
- **The designer's `spec-change`** is raised only for a boundary shape, a public name, a
  consumed signature or a nullable column the contracts get wrong (level `contract`), or a
  probe doc contradicting the row (level `contract`); an internal question is an **Open
  questions** entry with an assumption. The designer never raises level `design` or `test`.
- **Researcher commit scope** `probe <source>`; `Commit: yes` is no longer a field — every
  probe commits.
- **Designer details settled here:** the `spec-change` exit's commit summary is `<pkg>/<section>:
  spec-change (contract)`; in `delta` mode the change file's **Contract changes** are the spec
  and are not listed under **Contract deviations** (that heading holds departures the change
  file does not sanction); `Deviations: <count>` counts **Contract deviations** entries; in
  `delta` and `document` modes the designer also reads the section's own README when one
  exists (the `Dependency READMEs:` field carries it first, prefixed `own:`); **Skills used**
  with no project skill lists the preloaded ones; `Raised by:` in a designer's entry is
  `designer — <Run:>`.

## Files

| Path | Change |
|---|---|
| `agents/designer.md` | rewritten in full — specification below |
| `agents/tester.md` | rewritten in full — specification below |
| `agents/researcher.md` | Hard rules (always commits; per-section heading), Probe mode step 7 and **The probe doc** (the section heading); extract mode unchanged |
| `skills/planning-templates/references/source-probe.md` | both kinds gain, after their last numbered item, item **Sections served** — specification below |
| `contracts.yml` | `headings` claim for `deviations-entry.md` (readers designer, tester); design-headings claim re-pointed (tester reads `Mode:`; `As shipped`/`Revision` no longer cited); §Project convention reader spans updated for the three agents |

## Specification

### `agents/designer.md`

```yaml
---
name: designer
description: Designs one section of one package from its contract row, the repo contract, the shipped READMEs of the sections it depends on, upstream interface.md files and probe docs. Modes new (no code at the path), document (code and no design) and delta (an open change file names the section). Returns done, stopped or spec-change. Spawned by /dev-team:run-package at the DESIGN step.
tools: Read, Write, Edit, Glob, Grep, Bash, Skill, WebSearch, WebFetch
model: inherit
memory: project
skills:
  - project-structure
  - git-workflow-and-versioning
color: blue
---
```

Headings, in order: `## Hard rules`, `## Inputs`, `## Modes`, `## Procedure`, `## Design
document template`, `## Spec-change`, `## Return`, `## Commit`, `## Memory`.

**Inputs** table (the spawn block):

| Field | Holds | `none`? |
|---|---|---|
| `Section:` | `<pkg>/<section>` | no |
| `Mode:` | `new`, `document` or `delta` | no |
| `Contract:` | `docs/packages/<pkg>/contract.md` | no |
| `Repo contract:` | `docs/architecture.md` | no |
| `Dependency READMEs:` | the README of every section in the row's `depends on`, comma-separated | yes |
| `Upstream interfaces:` | `docs/packages/<dep>/interface.md` per upstream package, or `provisional: <contract.md>` | yes |
| `Source probes:` | `docs/sources/<source>.md` per entry in the row's `source` | yes |
| `Change file:` | `docs/changes/<slug>.md` (`delta` only) | yes |
| `Design-gap:` | the tester's return, verbatim, when re-designing after a `design-gap` | yes |
| `Skills to invoke:` | the row's `builds with` | yes |
| `Write to:` | `docs/packages/<pkg>/design/<section>.md` | no |

**Modes** as the design: `new` — design from the contracts; `document` — code exists and no
design: write what the code does, past tense, defects under **Pitfalls and risks**; `delta` — an
open change file names the section: apply its **Contract changes** to the existing design and
rewrite the whole document (no changelog stapled on). For the `surface` section every mode
reads every sibling README's **Entry points and interfaces** and `Public: yes` rows, and every
public name in the design cites the README that provides it.

**Procedure**: read the contracts, the shipped documents, the probe docs (authority per heading
as today); invoke every skill in `Skills to invoke`; on `Design-gap:`, answer every `Gap:` line
in the rewritten document and list them under **Open questions** as answered; `WebSearch` for an
external fact; write the document; commit; return.

**Design document template**: first line `Mode: new | document | delta`, second line `Change:
docs/changes/<slug>.md` in `delta` mode; then the eleven headings exactly as today (`1.
**Purpose and scope**` … `11. **Open questions**`), with **Module plan** inside item 3 and the
`Public` column rule in item 5 re-pointed at the contract's **Public surface (intent)** (the
`surface` section's design is built from the `yes` rows). No **Revision**, no **As shipped**:
a revision rewrites the document.

**Spec-change**: when a contract clause is wrong per the rule in **Decisions**, append a
`spec-change:contract` entry to `docs/deviations.md` per
`${CLAUDE_PLUGIN_ROOT}/skills/planning-templates/references/deviations-entry.md` (read it with
the Read tool), write no design, commit the ledger, return `Result: spec-change`.

**Return**, first line one of `Result: done | stopped | spec-change`; then:

```
Result: done
Design: docs/packages/<pkg>/design/<section>.md
Open questions: OQ-<pkg>-<section>-1 (assumption: …), …  | none
Deviations: <count> under Contract deviations
Commit: <sha>
```

`stopped` is a decision the design cannot be written without: the second line is `Stopped for
decisions: D<n>, …` after stubbing them in `docs/decisions.md` with `Raised by:
OQ-<pkg>-<section>-<k>` and an `Assumption if unanswered:` where one honestly exists; commit the
ledger. `spec-change`: second line `Spec-change: contract — <one line>`, third the entry heading.
Ten lines or fewer.

**Commit**: per `git-workflow-and-versioning` §Project convention (preloaded): stage the design
(and `docs/decisions.md` or `docs/deviations.md` when written), scope `<pkg>/<section>`,
summary `design` / `design (delta)` / `design (document)`, trailer `Dev-Team-Run:` as given by
the spawn prompt's `Run:` line — the driver adds `Run: run-package <pkg>` to every spawn block
(phase 8); a direct spawn with no `Run:` line uses `Dev-Team-Run: designer <pkg>/<section>`.

### `agents/tester.md`

```yaml
---
name: tester
description: Writes a section's intent tests from its design, the contracts and the shipped documents it consumes, never from its source. Red by construction when the section path has no code, expected green on adopted code. Returns done or design-gap; regenerates only the tests an approved deviation or a spec-change cites. Spawned by /dev-team:run-package at the TEST step.
tools: Read, Write, Edit, Glob, Grep, Bash, Skill
model: inherit
memory: project
skills:
  - project-structure
  - python-style-guide
  - git-workflow-and-versioning
color: green
---
```

Headings: `## Hard rules`, `## Inputs`, `## Design gaps`, `## Procedure`, `## Regenerate`,
`## Return`, `## Commit`, `## Memory`.

**Hard rules** keep today's: never open the section's source (nothing under its path but
`README.md`); write only `tests/intent/<section>/`, `tests/fixtures/`, and `docs/deviations.md`
(a `spec-change` entry); Bash for the one-package test command on the intent tree, `git`, the
formatter and linter on the tree (the hook runs them too), read-only inspection; the tree
passes lint and format; no suppression; never weaken a test. Gone: reconcile mode,
`docs/followups.md`, the integration doc, the Branch/Baseline check (the run gate owns it).

**Inputs** table: `Section:`, `Design:`, `Contract:`, `Repo contract:`, `Dependency READMEs:`,
`Upstream interfaces:`, `Source probes:` (as the designer's), plus `Regenerate:` (entry
headings from `docs/deviations.md`, one per line, or `none`), `Adopted code: yes | no`,
`Write to: tests/intent/<section>/ under <package root>`.

**Design gaps**: the four gap kinds from **Decisions**, each with what the return says. When any
is found: write nothing, commit nothing, return `Result: design-gap` and one `Gap: §<n> <item>
— <why it cannot be tested>` line per gap.

**Procedure** (intent): inventory per design heading, reading the TDD RED paragraph by path;
write `conftest.py`, one `test_<interface>.py` per **Interfaces** row, `test_workflow.py`;
docstrings `Design §<n> <row or step>: <one line>`; imports inside each test from the module the
**Module plan** assigns — for the `surface` section, from the package top level (`from <pkg>
import <name>`); a decision with only an assumption is `xfail(strict=False, reason="D<n> open —
assumption: …")`; run; with `Adopted code: no` delete any passing test and say so; with `yes`
every failing test becomes one `spec-change:design` entry (`Found:` the assertion) and the test
stays; `docs/constraints.md` **Enforced** coverage row sizes the suite; commit; return.

**Regenerate**: for each entry in `Regenerate:`, the tests whose docstring cites the entry's
`Clause:` (the `§<n> <item>` match rule of the stop gate) are rewritten to assert `Did:` for a
deviation or the document as corrected for a `spec-change:test`, with ` (deviation <date>)`
appended to the docstring; every other file is untouched; the suite must be green afterwards
(the code shipped); summary `<pkg>/<section>: regenerate <k> intent tests`.

**Return**: `Result: done | design-gap`; then `Tests: <n> written (<by heading>)` or
`Regenerated: <k>`; `Not written: <cases the documents do not support>`; `Deleted for
passing: <n>`; `Spec-change: <entry headings>`; `Commit: <sha>`. Twenty lines or fewer.

**Commit** as the designer's, summary `<n> intent tests from design` or the regenerate
summary.

### `agents/researcher.md` changes

- Hard rules: "You do not commit" becomes: every run commits its `docs/sources/<source>.*`
  files per §Project convention, scope `probe <source>`, whoever spawned it; the `Commit: yes`
  field goes.
- Probe mode gains a seventh field `Section: <pkg>/<section>` (or `repo` for a dataset probed
  by `plan-repo`), and step 7 becomes: when the doc exists, re-run the probe or profile
  program (rewriting the `.probe.py`/`.profile.py` and `.sample.json`/`.stats.json`), keep the
  document, and append or replace the `## <pkg>/<section>` heading under **Sections served**
  with the endpoints or columns that section's purpose needs and nothing else; the ISO date in
  the title line becomes today's; **Changes since last probe** is written only when the
  observed schema changed and is otherwise absent; the task-fit headings written for an
  earlier section are kept. When the doc does not exist, write it whole.
- The commit trailer without a `Run:` line is `Dev-Team-Run: researcher <source>`; under the
  driver, `run-package <pkg>`.
- **The probe doc** paragraph names the new item.

### `source-probe.md`

After item 12 (`api`) and item 14 (`dataset`), one item each:

```
13. **Sections served** — one `## <pkg>/<section>` heading per consuming section (a `##`
    heading, literally, so `status.py` and the driver find it), appended by the probe that
    served it: the purpose it was probed for (the contract row), then only the endpoints (api)
    or columns (dataset) that section needs, each with its `observed` / `documented` label. A
    new consuming section makes the section need PROBE; it does not make the document stale.
```

(numbered 15 for `dataset`.)

### `contracts.yml`

Add under `headings`:

```yaml
  - name: deviations.md entry fields its readers parse are ones planning-templates defines
    owner: skills/planning-templates/references/deviations-entry.md
    owner_span: ['1. **Clause**', null]
    readers:
      - file: agents/designer.md
        cites: ['Clause', 'Found', 'Why', 'Status', 'Raised by']
      - file: agents/tester.md
        cites: ['Clause', 'Did', 'Found', 'Status']
```

(Phases 4, 5 and 6 append the implementer, reviewer and architect readers.) In the design
headings claim, the tester reader keeps its six cites; delete the `As shipped` claim's
`agents/designer.md`-adjacent readers only when they stop citing it (the designer never did;
no change there). The §Project convention readers for `agents/designer.md` (new), `tester.md`
and `researcher.md` get spans ending at the phrase each new file uses (`'rules; stage'`).

## Steps

1. `source-probe.md`, then `researcher.md`.
2. `designer.md`.
3. `tester.md`.
4. `contracts.yml`: the entry-fields claim, reader spans; plant a `cites: ['Clausee']` and watch
   it fail.
5. The plugin's own rules (no skill added or removed).
6. `check-contracts`; `build-site`.
7. Evals — the table below, through `run-evals`, logged with `log-eval`.
8. Commit: `dev-team remake (phase 03): designer modes and spec-change, tester design-gap and regenerate, per-section probe entries`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 3.1 | mechanical | `contracts.yml` | — | `check-contracts` + the planted cite | all PASS; the plant FAILs |
| 3.2 | behavioral | `designer` | previous | `evals/sets/designer.json` 1, 2, 3 | every expectation passes for `with_skill`; `old_skill` fails at least the `Mode:` first line and the `spec-change` return |
| 3.3 | behavioral | `tester` | previous | `evals/sets/tester.json` 1, 2, 3 | every expectation passes for `with_skill`; `old_skill` fails the `design-gap` return and the regenerate tag |
| 3.4 | behavioral | `researcher` | previous | `evals/sets/researcher.json` 1 (regression), 2 | eval 1's pass rate ≥ the 2026-09-20 log's; eval 2's every expectation passes for `with_skill` |
| 3.5 | load | `designer`, `tester`, `researcher` | — | `claude --plugin-dir ./dev-team -p "List the agents you have from dev-team"` | the three names appear |

## Done when

- `head -12 agents/designer.md` shows `Bash` in `tools` and `git-workflow-and-versioning` in `skills`; `agents/tester.md` has no `test-driven-development` line.
- `grep -c 'reconcile' agents/tester.md` is 0; `grep -c 'Sections served' skills/planning-templates/references/source-probe.md` is 2.
- `check-contracts` all PASS; `build-site` exits 0.
- Logs for 3.1–3.5 in `evals/README.md`, each behavioral one naming its iteration directory.
- The ledger row for phase 3 reads `done`.
