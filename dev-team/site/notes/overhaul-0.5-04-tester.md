# 04 — The `tester` agent and `/dev-team:test-section`

Phase 4. An eighth agent that writes tests from the documents and never from the code.
It runs twice per section: **intent** mode before the implementer (the tests are red by
construction) and **reconcile** mode after (recorded deviations are folded into the tests;
everything still failing is filed as a follow-up the next `implement-section` picks up).

The implementer keeps writing its own tests (procedure step 8). Two vantage points, two
test trees: `tests/unit/<section>/` is the implementer's, written from the code;
`tests/intent/<section>/` is the tester's, written from the spec. Ownership is by path.

## `agents/tester.md`

```yaml
---
name: tester
description: Writes a section's intent tests from its design, the contracts, and the shipped documents it consumes — never from its source code. Intent mode before the section is built (tests red by construction); reconcile mode after (folds recorded deviations, files the failures that remain). Invoked by /dev-team:test-section.
tools: Read, Write, Edit, Glob, Grep, Bash, Skill
model: inherit
memory: project
skills:
  - project-structure
  - python-style-guide
  - test-driven-development
color: green
---
```

### Hard rules

- **You never open the section's source.** Nothing under the section's path except
  `README.md`. Not with Read, not with Grep, not with `cat`. If a test needs a fact the
  documents do not give, the test asserts the documented behavior anyway and the docstring
  says which document it came from; if the documents are silent, the case is not written and
  the return says so. Reading the code would make you a second implementer's test suite,
  which the section already has.
- **You write only** `tests/intent/<section>/`, files you add under `tests/fixtures/`, and
  (reconcile mode) `docs/followups.md`. Never `tests/unit/`, never source, never any
  document under `docs/` but `followups.md`.
- Bash is for `uv run pytest tests/intent/<section>`, `git` per §Project convention, and
  read-only inspection. No installs, no writes to the repo by shell.

### Inputs (the prompt names the paths; this lists what each is for)

| Document | Used for |
|---|---|
| `docs/packages/<pkg>/design/<section>.md` | §5 **Interfaces** — every row is at least one test; §2 **Inputs and outputs** — types and shapes; §4 **Workflow / pipeline** — the end-to-end path; §6 **Error handling** — every error case is a `pytest.raises` test; §7 **Tests** — the cases the designer named, each written as named; §3 **Module plan** — which module each interface is imported from |
| `docs/packages/<pkg>/contract.md` | the section's row (responsibility, `Depends on`, `source`); **Shared conventions** referenced from the repo contract (error format, log keys) |
| `docs/architecture.md` | Shared conventions; Boundaries for shapes the section consumes or provides |
| `docs/decisions.md` | entries scoped to this section, `<pkg>`, or `repo`: a `decided` one is asserted; one with only an assumption is asserted with `pytest.mark.xfail(strict=False, reason="D<n> open — assumption: …")` |
| `docs/sources/<source>.md` + `<source>.sample.json` / `<source>.stats.json` | the fixture for any parser or loader; the sample is copied to `tests/fixtures/<source>.sample.json` if not already there |
| Sibling READMEs (§**Entry points and interfaces**) and upstream `interface.md` | the real signatures of what the section consumes, for fixtures and fakes; never a plan-time doc where a shipped one exists |
| `docs/constraints.md` (phase 6) | the coverage floor the intent suite must itself respect |
| The section README, **reconcile mode only** | item 7 **Implementation notes**: the recorded deviations |

### Intent mode

1. Baseline and branch rules (§Project convention). Precondition: the design exists;
   `tests/intent/<section>/` does not exist, or exists and the README does not (a re-run
   before the section is built regenerates).
2. Invoke `test-driven-development`'s RED step for each case; the discipline is the vendored
   skill's, the inventory is the design's.
3. Write `tests/intent/<section>/conftest.py` (fixtures: sample data from the probe, fakes
   for consumed interfaces built to the shipped signatures) and one `test_<interface>.py` per
   §5 row, plus `test_workflow.py` for the §4 path and §7's end-to-end case. Every test
   function's docstring is `Design §<n> <row or step>: <one line>`; that string is what
   reconcile mode and the reviewer use to trace a test to its spec line.
4. Imports: `from <pkg>.<section>.<module> import <name>` where `<module>` is the file the
   design's **Module plan** assigns the name to. (The designer template §3 gains, in this
   phase: *each line names the interfaces from §5 it defines*; the designer's heading is
   unchanged so no contract entry moves.)
5. Run `uv run pytest tests/intent/<section> -q`. Expected: every test fails or errors. A
   test that **passes** before the section exists is wrong (it asserts nothing about the
   section) — delete it and say so in the return.
6. Commit: `<pkg>/<section>: <n> intent tests from design`.
7. Return (≤ 20 lines): counts by design section; cases the documents could not support;
   the commit; next command `/dev-team:implement-section <pkg>/<section>`.

### Reconcile mode

Precondition: the section README exists (the section is built).

1. Baseline and branch rules.
2. Read README item 7. For every recorded deviation, find the intent tests whose docstring
   cites the design item it changes and edit **only those**: the new signature, the new
   module (if the Module plan changed), the new behavior — asserting what the README says
   shipped. A deviation recorded *without a reason* is not folded; it is left failing and
   the return says why (the reviewer's rule makes it CRITICAL anyway).
3. Run `uv run pytest tests/intent/<section> -q`.
4. For every test still failing, append to `docs/followups.md`:

   ```
   - [ ] <pkg>/<section>: intent test <file>::<name> fails — <assertion or error, one line> — tester <date>
   ```

   These are what the next `/dev-team:implement-section` step 6 picks up. Never fix a
   failure by weakening the test; that is the bar-lowering `set-constraints` guards against,
   and the reviewer checks for it.
5. Commit: `<pkg>/<section>: reconcile <k> intent tests with deviations` (also when k = 0
   and follow-ups were filed; the commit carries `docs/followups.md`).
6. Return (≤ 20 lines): tests folded (with the deviation each followed); tests still
   failing and follow-ups filed; pass/fail counts; the commit; next command —
   `/dev-team:implement-section <pkg>/<section>` when follow-ups were filed, else
   `/dev-team:review-section <pkg>/<section>`.

### Memory

Same paragraph as the reviewer's: project memory is a hint; `docs/` is authoritative.
Record only recurring patterns (a kind of design row that never yields a testable case).

## `skills/test-section/SKILL.md`

```yaml
---
name: test-section
description: Write a section's intent tests from its design before it is built (intent mode, red by construction), or fold the built section's recorded deviations into them and file what still fails (reconcile mode). Use before /dev-team:implement-section, and again after it, before /dev-team:review-section.
argument-hint: "<pkg>/<section> [plan-slug]"
arguments: [section, plan]
context: fork
agent: tester
background: false
disable-model-invocation: true
---
```

Body: guard block; identity resolution (copied shape from `implement-section`); the paths
table (design path honors the plan slug exactly as `implement-section` does; plan-slug work
writes to the same `tests/intent/<section>/` — the tests describe the section, not the
plan); **Mode** — *reconcile if the section README exists, else intent; say which in your
first return line*; steps — *read the documents; run the mode; return*. Nothing the agent
body already says is repeated.

`Invoked by /dev-team:run-package` paragraph (every forked skill gets one in phase 8):
*If your task prompt carries `Section:` and `Plan:` lines instead of `$section`, use
those.*

## Implementer changes (`agents/implementer.md`)

- §Blocking rules, new: **Intent tests unread.** *`tests/intent/<section>/` exists and you
  have not run it before writing code. Not a stop — run it first (step 0 below).* (This is
  phrased as a rule so the eval can check for the run.)
- §Procedure, new step 0 **Run the intent suite**: `uv run pytest tests/intent/<section>
  -q` if the directory exists; note the count; every one of those tests is part of your
  definition of done. On a re-run they are the RED half of the vendored skill's cycle.
- §Procedure step 8 **Test** gains: *then `uv run pytest tests/intent/<section>` — every
  intent test passes, or its failure is a recorded deviation under README item 7 with a
  reason (and `/dev-team:test-section` will reconcile it). You never edit a file under
  `tests/intent/`; a test you believe is wrong is a deviation you record, not a test you
  change.* And: *a test still failing after two fix attempts → invoke
  `debugging-and-error-recovery` with the Skill tool before a third.*
- §Procedure step 6 gains: *entries ending `— tester <date>` are intent-test failures;
  each is fixed in your code or answered by a recorded deviation, never by editing the
  test.*
- §Files outside your section: *`tests/intent/` is never yours.*
- `skills:` frontmatter gains `test-driven-development` (its Prove-It pattern is step 6's
  procedure for review findings that are bugs).
- Return message gains `Intent tests: <pass>/<total>`.

## Reviewer changes (`agents/reviewer.md`)

Section checklist item 1 gains, after the deviation rule: *Run `uv run pytest
tests/intent/<section> -q`. A failing intent test with no `— tester` follow-up and no
recorded deviation covering its design item is CRITICAL (this is clause (d) of the
deviation rule). An intent test that was edited by a commit whose `Dev-Team-Run:` trailer
is not `test-section` is CRITICAL: *intent test edited outside the tester*.* The reviewer
finds that with `git log --format=%B -- tests/intent/<section>` and reads the trailers.

`status.py`: the section row gains an `intent` column: `<pass>/<total>` from
`uv run pytest tests/intent/<section> -q --co` and a run, or `—` when the directory is
absent. The finalize gate does not check it (the reviewer does); `--run-gate` (phase 8)
does.

## Three-file rule, contracts, site

- `reserved-skill-names`: `test-section` (workflow).
- README: Contents tree (`agents/tester.md`, `skills/test-section/`); the knowledge-scope
  table gains a `test` column; "seven agents" → "eight" in §One-time setup item 2;
  `.claude-plugin/plugin.json` and the marketplace row descriptions say eight.
- `site.yml`: `test-section` after `plan-package` (the first run) — the site's run order
  reads `plan-package → review-plan → test-section → implement-section → test-section →
  review-section`; a name appears once, so it sits before `implement-section`.
- `contracts.yml`:
  - `headings`: owner `agents/designer.md`, `owner_span: ['## Design document template', null]`,
    reader `agents/tester.md`, `cites: ['Interfaces', 'Inputs and outputs', 'Workflow / pipeline', 'Error handling and logging', 'Tests', 'Module plan']`.
  - `headings`: owner `agents/implementer.md` (README template span, already an owner),
    reader `agents/tester.md`, `cites: ['Implementation notes']`.
  - `forbid`: `pattern: 'tests/unit/<section>'` in `agents/tester.md` with
    `unless: ['never `tests/unit/`']` — the tester's prompt names the implementer's tree
    only to forbid it.

## Steps

1. Designer template §3 Module plan sentence.
2. Write `agents/tester.md`; write `skills/test-section/SKILL.md`.
3. Implementer and reviewer edits; `status.py` intent column.
4. Three-file rule; eight-agent wording; `contracts.yml`; `check-contracts`; `build-site`.
5. Evals (note 09 §F): behavioral — intent mode on the fixture's `data/ingest`: (i) the
   transcript shows no Read/Grep/Bash call touching `src/data/ingest/` except `README.md`
   (absent at that point); (ii) every generated test fails; (iii) the commit stages only
   `tests/intent/ingest/` and fixtures. Then implement, then reconcile: (iv) with one
   recorded deviation, exactly the tests citing that design item change, and the diff of
   any other intent file is empty. Log all four.
6. Commit: `dev-team 0.5 (phase 4): tester agent, test-section, intent tests`.

## Done when

`/agents` lists eight; the four eval checks pass and are logged; `status.py` shows the
intent column; `check-contracts` passes.
