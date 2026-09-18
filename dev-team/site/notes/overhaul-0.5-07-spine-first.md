# 07 — Spine-first package planning

Phase 7. `/dev-team:plan-package` designs one section first — the one the most sections
depend on — and the rest only after that section has shipped, so the designs that would
have been most wrong are written against a README instead of a projection. All-at-once
planning stays available as `--all`, and is automatic for packages of one or two sections.

## Selecting the spine

From the contract's Sections table, build the in-package dependency DAG from `Depends on`.
For each section count its **transitive dependents** — every section that reaches it. The
spine is the section with the highest count; ties break by table order (first row wins).
A section with the maximum count has no in-package dependencies (anything it depended on
would have a strictly higher count), so it is always buildable first. If every count is
zero (no in-package edges), the spine is the first row.

The architect records the count and the reason; it does not choose on any other basis.
A user who wants a different spine passes `--spine <section>`; the architect uses it
without argument and notes it.

## Run detection (package scope)

After the interview rule and the contract (steps 3–4 of `plan-package`), before probing,
the architect classifies the run from what is on disk. `D` = sections with a design;
`B` = sections with a README; `N` = rows in the Sections table.

| Condition | Run | What happens |
|---|---|---|
| `--all` given, or `N ≤ 2` | **full** | 0.4 behavior: probe; design every section not in `D`; unify; surface |
| `D = ∅` | **spine** | probe all sources; choose the spine; delegate **only** the spine; write `integration.md` with **Spine** `Status: spine only`, **Dependency order** for all `N` sections, and every other heading for the one design; write **no** `surface.md`; return |
| spine ∈ `D` and spine ∈ `B` and `D ≠ all` | **completion** | delegate every section not in `D`, with `Sibling shipped:` naming the README of every section in `B`; unify (rewrite `integration.md`, **Spine** `Status: complete`); write `surface.md`; return |
| spine ∈ `D` and spine ∉ `B` | **too early** | return, without writing: *spine `<s>` is designed and not built. Run `/dev-team:test-section <pkg>/<s>`, `/dev-team:implement-section <pkg>/<s>`, `/dev-team:test-section <pkg>/<s>`, `/dev-team:review-section <pkg>/<s>`, then this again — or pass `--all` to design the remaining sections now against the plan-time design.* |
| `D = all` | **re-run** | 0.4 behavior for a complete plan: no designers; unify from disk (this also covers a 0.4 plan and a plan being re-run for `<pkg>/plan` follow-ups, note 05) |

"spine" in rows 3–4 is read from the existing `integration.md` **Spine** heading, not
recomputed, so a `--spine` choice sticks across runs.

## The **Spine** heading

`skills/planning-templates/references/integration.md` gains item **0. Spine**, before
**Contract deviations**:

```
## Spine
Status: spine only | complete
Section: <name>
Chosen because: <k> of <N−1> other sections depend on it (transitively); tie broken by table order | chosen by --spine
Designed this run: <names>
Pending design: <names> | none
```

Present in every integration doc written by 0.5, including full runs (`Status: complete`,
`Section: —` when `--all` or `N ≤ 2` skipped selection). `review-plan` blocks on
`spine only`; `status.py` shows it; `run-package` branches on it.

## Designer: `Sibling shipped:`

The architect's delegation prompt gains one field after `Upstream interfaces:`:

```
Sibling shipped: <README path>, … | none
```

`agents/designer.md` §Inputs: *a README listed under `Sibling shipped:` is the shipped
document for that sibling; for every name you consume from it, its **Entry points and
interfaces** table outranks that sibling's design, exactly as an upstream `interface.md`
outranks a contract. Reference the shipped signature; where it differs from what the
contract's Sections table implied, note it under §10 **Contract deviations** so the
architect reconciles the contract, not you.* `contracts.yml`: reader `agents/designer.md`
added under the implementer's README-template heading contract with
`cites: ['Entry points and interfaces']`.

## Skill and architect edits

- `skills/plan-package/SKILL.md`: `argument-hint: "<pkg> [--all] [--spine <section>]"`;
  `arguments: [pkg, flags]`; step 4c **Classify the run** (the table above, by reference to
  the architect's **Spine-first** section); step 5 **Delegate** says *the sections the run
  classification names*; step 7 **Surface** says *completion and full runs only*; the return
  for a spine run ends with the four commands for the spine and then
  `/dev-team:plan-package $pkg`.
- `agents/architect.md`: new section **Spine-first** after **Delegating to designers**,
  holding the selection rule, the run table, and the **Spine** heading's meaning. §Scopes
  package row: *Produces … in two runs on packages of three or more sections (Spine-first).*
- `skills/status/scripts/status.py`: the `plan:` line (note 05) reads the **Spine**
  heading: `plan: spine only (<section>) — build it, then re-run plan-package` when
  `Status: spine only`.
- `README.md` §Which skill to run: the `new repo` row becomes three lines (plan-package;
  build the spine; plan-package again). §Workflows and `site/workflows/new-repo.md`: the
  loop diagram in note 00.
- `site/flow.md` **The week-by-week loop**: node B splits into B1 and B2 as in note 00.

## What does not change

`plan-change` and `map-project` are unaffected: change plans design deltas, and adoption
runs are `document` mode for everything (`D = all` after one run). `plan-repo` is
unaffected. The interview rule, probing, and decision stubs behave identically in a spine
run and a completion run.

## Steps

1. Integration template item 0; architect **Spine-first** section; delegation field.
2. Designer §Inputs paragraph; `plan-package` skill edits; `status.py` line.
3. README, `flow.md`, `workflows/new-repo.md`.
4. `contracts.yml` reader entry; `check-contracts`; `build-site`.
5. Evals (note 09 §I): behavioral, on the fixture's `data` package (three sections,
   `clean → ingest`, `storage → clean`): (i) the first `plan-package` designs exactly
   `ingest` and writes no `surface.md`; (ii) a second run before building returns the
   *too early* message and writes nothing; (iii) after the spine ships, the completion run
   delegates exactly two designers, both prompts carry `Sibling shipped:` with the ingest
   README, and `surface.md` exists; (iv) `--all` on a fresh copy designs all three in one run.
   Log all four.
6. Commit: `dev-team 0.5 (phase 7): spine-first package planning`.

## Done when

The four eval checks pass and are logged; `review-plan` on a spine-only plan returns the
blocker from note 05; `status.py` prints the spine line.
