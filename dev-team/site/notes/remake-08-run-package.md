# 08 — run-package

Phase 08. Rewrites the driver. `/dev-team:run-package <pkg> [<section>] [--step PROBE|DESIGN|
TEST|IMPLEMENT|REVIEW] [--defer]` runs in the user's conversation, runs the run gate once,
recomputes every section's state with `status.py` before every iteration, takes the ready set,
spawns every agent itself as `dev-team:<agent>` with `run_in_background: false` — probes,
designs and tests of the ready set in one message, implementers one at a time, the two round-1
reviewers in one message — branches on each return's first line, relays a return only for
`design-gap` and `spec-change`, asks the user on BLOCKED and writes the answer to
`docs/decisions.md`, runs `sync-plan` when every section is DONE, and ends with the summary
block. The gap it closes: the 0.6 driver carried a plan that was stale the moment the spine
shipped and needed five typed skills and an integration doc to know the next step.

## Decisions

- **Spawn blocks live here**, one per role, copied field for field from each agent's
  `## Inputs` table, plus `Run: run-package <pkg>` on every block. Reason: the driver is the one
  place that resolves paths; the agent owns which fields exist.
- **`--step <STEP>`** runs that one step for the named section against whatever is on disk,
  whatever the derived state, and stops: the agent's own preconditions produce `blocked` when
  a document is missing. `--step REVIEW` on a section at FIX n or BLOCKED-on-cap runs one more
  round (round `n+1`, `full`). `--step` without `<section>` is an error printed as one line.
- **`--step` skips the ask step**: a BLOCKED row does not stop a `--step` run, which is how
  *one more round* is typed by hand. Every spawn's trailer under the driver is
  `Dev-Team-Run: run-package <pkg>`, the architect's PLAN and close runs included. A driver
  `Decision:` line in `docs/decisions.md` rides in the next agent commit that stages that file
  (an implementer's `Applied:` edit) or stays for the user; either is correct.
- **`<section>` without `--step`** walks that section alone from its derived state to DONE or
  BLOCKED, skipping the ready-set rule for the rest of the package (its own dependencies must
  still be DONE, else the driver prints why and stops).
- **The design-gap cap** is two round-trips per run (the design's decision): the third
  `design-gap` for one section in one run is BLOCKED; the driver asks with the tester's `Gap:`
  lines as the question text, stubs a `D<n>` with `Raised by: /dev-team:run-package <pkg>
  (driver)` and the answer as `Decision:` / `Status: decided`, and the section re-enters DESIGN.
- **The review cap** is read from `status.py` (BLOCKED with evidence `cap`); the driver asks
  "one more round, or defer"; *one more round* spawns the `full` reviewer for round `n+1`
  after an implementer FIX; *defer*, or `--defer`, spawns the reviewer with `Focus: defer`.
- **Asking:** `AskUserQuestion`, one question, the agent's first lines as the text. When the
  tool is unavailable (a headless run) or the run has `--defer` and the block is not a review
  cap, the driver goes to the summary.
- **Round 2+ reviewer's `Diff:`** is the `Commit:` line of the previous round's `-s` report,
  or of the `-a` report for round 2.
- **The driver writes nothing but `docs/decisions.md`** and runs no git command that writes,
  so its ledger edit stays uncommitted: the file is baseline-exempt, the next agent's run
  leaves it alone, and the user commits it, as today. The summary lists it under
  `uncommitted:` when edited.
- **Summary block**, always the last message:

  ```
  run-package <pkg>: <done | stopped at <section> <STEP>>
  sections: <DONE>/<total> DONE; <list of section · state>
  agent runs: designer <n> · tester <n> · implementer <n> · reviewer <n> · researcher <n> · architect <n>
  commits: <first sha>..<last sha> (<count>)
  stopped because: <the agent's first two lines, or the run gate's FAIL lines>   (only when stopped)
  uncommitted: docs/decisions.md                                                   (only when edited)
  next: <status.py's next line>
  ```

## Files

| Path | Change |
|---|---|
| `skills/run-package/SKILL.md` | rewritten in full — specification below |
| `contracts.yml` | state-vocabulary `headings` claim (owner `status.py` docstring, reader `run-package`); spawn-field claims per agent (owner each agent's `## Inputs`, reader `run-package`); the `run-package spawns by prefixed name` claim kept; the `plan-loop-exit` claim rewritten (below) |

## Specification

### `skills/run-package/SKILL.md`

```yaml
---
name: run-package
description: Drive one package to shipped - derive every section's state from disk, run the ready set (probes, designs and tests in parallel, implementers one at a time, two reviewers in round 1), route design-gap and spec-change, ask you on a block and record the answer, close the package with sync-plan, and end with a summary and the exact next command. Optional section and --step run one section or one step by hand; --defer moves a stuck review's findings to the backlog instead of asking.
argument-hint: "<pkg> [<section>] [--step PROBE|DESIGN|TEST|IMPLEMENT|REVIEW] [--defer]"
arguments: [pkg, rest]
disable-model-invocation: true
---
```

Headings, in order: `## What you never do`, `## Arguments`, `## Spawning an agent`, `## Loop`,
`## Asking`, `## Summary`.

**What you never do**: edit a file other than `docs/decisions.md`; run a git command that
writes (`git rev-parse --short HEAD` and `git rev-list --count` only); read a return past its
first line except to relay `design-gap` and `spec-change` in full; open the files the agents
wrote; spawn in the background; spawn with a bare agent name.

**Spawning an agent**: one Agent call per spawn, `subagent_type: "dev-team:<agent>"`,
`run_in_background: false`; the prompt is exactly one of the blocks below with every field
resolved from `status.py`'s row and the contract's Sections table — one block per role
(researcher probe, designer, tester, implementer, reviewer, architect for PLAN, architect for
the close), each field list identical to that agent's `## Inputs`. The unknown-agent-type
error → tell the user `/reload-plugins`, then `/agents`, and stop.

**Loop**:

1. Run gate: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate <pkg>`;
   FAIL → summary with its lines.
2. `status.py <pkg>`; keep the rows. Every section DONE → step 7.
3. BLOCKED rows: for each, **Asking**; on an answer, re-run step 2.
4. Ready set R (or the one named section). For every ready row by state, all of one kind in
   one message: PROBE → researcher per source lacking the section heading; DESIGN → designer
   (mode from the row: `delta` when an open change file names it, `document` when the path
   has code and no design, else `new`; `Design-gap:` when this run's tester returned one for
   it); TEST → tester (`Regenerate:` from `approved` entries without regenerated tests;
   `Adopted code:`); IMPLEMENT and FIX n → implementer, one at a time, `Round:` n+1, `Review:`
   the newest round's reports; REVIEW → round 1: two reviewers in one message (`Focus:
   conformance`, `Letter: a`; `Focus: correctness`, `Letter: b`); round 2+: one (`Focus:
   full`, `Letter: s`, `Diff:`); PLAN → architect through `plan-package` (`Package:`, `Run:`).
5. Branch on each return's first line: `done` → nothing; `design-gap` → designer again for that
   section with `Design-gap:` (cap two per run); `spec-change` → the entry is on disk,
   `status.py` re-opens the step, nothing to relay except to the architect at PLAN
   (`Spec-change: <entry heading>` line in its block); `blocked` and `stopped` → **Asking**.
6. After every batch: `status.py <pkg>`, print the changed rows only, back to step 2.
7. Close: architect through `sync-plan` (`Package:`, `Run:`); then the summary with `status.py`'s
   `next:` line.

**Asking**: the question text is the agent's return (a `blocked` or `stopped` first line and
what follows, or the `cap` evidence with the two choices). One `AskUserQuestion`. The answer
goes to `docs/decisions.md`: for an architect or designer `stopped` (`D<n>` stubs already
written) fill `Decision:` and `Status: decided` on each named stub; for a cap, no ledger edit;
for a design-gap cap, a new stub as **Decisions** says. Then re-run step 2. No tool or `--defer`
without a cap → summary.

**Summary** as **Decisions**.

### `contracts.yml`

```yaml
  - name: the driver's state names are the ones status.py derives
    owner: skills/status/scripts/status.py
    owner_span: ['1. **BLOCKED**', 'Ready:']
    readers:
      - file: skills/run-package/SKILL.md
        cites: ['BLOCKED', 'PLAN', 'PROBE', 'DESIGN', 'TEST', 'IMPLEMENT', 'REVIEW', 'FIX n', 'DONE']

  - name: every field the driver sends an agent is one that agent's Inputs table defines
    # one claim per agent, owner_span the agent's `## Inputs` table, reader run-package citing
    # the field names it fills. Six claims: designer, tester, implementer, reviewer,
    # researcher (Kind, Source, Purpose, Access, Extracted skill, Section, Write to), architect
    # (Package, Run, Spec-change).
```

The Inputs tables must be written in the form the owner parser reads: each field as `N.
**Field** — …` lines under `## Inputs` — phases 3–6 wrote tables; this phase converts each
agent's Inputs table to that numbered-bold form (a formatting edit within the same Files rule,
recorded as this phase's edit to `agents/*.md`). The `plan-loop-exit` claim is rewritten to:

```yaml
  - name: the review loop's exit is never bypassed by a bare next command
    # The cap lives in status.py (BLOCKED at round 3, or round 2 with a prior unfixed); a
    # sentence in the driver or the reviewer that names the implementer as the next step on
    # `request changes` without the cap bypasses it.
    pattern: 'on `request changes`, (spawn|run) the implementer'
    near: 200
    unless: ['cap', 'BLOCKED', 'status.py']
    files: ['agents/reviewer.md', 'skills/run-package/SKILL.md']
```

## Steps

1. Convert the six agents' `## Inputs` tables to numbered-bold form.
2. `skills/run-package/SKILL.md`.
3. `contracts.yml`: the vocabulary claim, six field claims, the rewritten exit claim; plant a
   `Focus: correctnes` in a scratch driver and watch the reviewer field claim fail.
4. The plugin's own rules (no skill added or removed).
5. `check-contracts`; `build-site`.
6. Evals, through `run-evals`, logged with `log-eval`.
7. Commit: `dev-team remake (phase 08): run-package drives the ready set from derived state; --step, --defer, the ask step`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 8.1 | mechanical | `contracts.yml` | — | `check-contracts` + the plant | all PASS; the plant FAILs |
| 8.2 | behavioral | `run-package` | previous | `evals/sets/run-package.json` 1, 2, 3 | every expectation passes for `with_skill`: one section walked DESIGN → TEST → IMPLEMENT → REVIEW (two reviewers) to DONE on the two-package fixture with one commit per agent run; a designer `spec-change:contract` routes to the architect at PLAN; a `stopped` return produces one `AskUserQuestion` (written to `outputs/interview.md`) and a `Decision:` line; the summary block is the last message with a `next:` line |
| 8.3 | mechanical | `skills/run-package/SKILL.md` | — | `grep -c 'Procedure: open' skills/run-package/SKILL.md` | 0 — the driver holds no copy of a procedure and points at no skill file |

## Done when

- `grep -c 'subagent_type: "dev-team:' skills/run-package/SKILL.md` ≥ 6.
- `grep -c 'integration.md\|Spine\|Dependency order' skills/run-package/SKILL.md` is 0.
- `check-contracts` all PASS with seven new claims counted; `build-site` exits 0.
- Logs for 8.1–8.3 in `evals/README.md`; 8.2 names its iteration directory.
- The ledger row for phase 8 reads `done`.
