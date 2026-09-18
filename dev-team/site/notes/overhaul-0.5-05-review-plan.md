# 05 — `/dev-team:review-plan`

Phase 5. The reviewer gets a third mode. Before any implementer forks, an independent run
checks the architect's contract, the designers' designs, and the architect's own
reconciliation against each other and against everything above them. It is the design
review a real team holds; today the first check of any plan-time document is a
`review-section` run after code exists.

## `skills/review-plan/SKILL.md`

```yaml
---
name: review-plan
description: Review a package's complete plan — contract, every section design, integration.md, surface.md — against the repo contract, the decisions ledger, the shipped interfaces it consumes, the probe docs, and docs/constraints.md, before any section is implemented. Writes docs/reviews/date-pkg-plan.md and files CRITICAL findings to followups addressed to pkg/plan, which the next plan-package run picks up.
argument-hint: "<pkg>"
arguments: [pkg]
context: fork
agent: reviewer
background: false
disable-model-invocation: true
---
```

Body: guard; `$pkg` fallback; **Preconditions** — `docs/packages/$pkg/contract.md`,
`integration.md` and `surface.md` all exist. If `integration.md` has a **Spine** heading
whose status line reads `spine only` (phase 7), return the blocker *plan is spine-only:
build the spine, re-run `/dev-team:plan-package $pkg`, then this* and stop. **Paths** table:
the three documents above; every `docs/packages/$pkg/design/*.md`; `docs/architecture.md`;
`docs/decisions.md`; `docs/followups.md` (entries addressed to `$pkg/plan`, to skip what
is already listed); `docs/constraints.md` if present; for each package in the repo
contract's `Depends on` for `$pkg`, `docs/packages/<dep>/interface.md` or, if absent,
`contract.md` marked provisional; `docs/sources/<source>.md` for every `source` entry in
the Sections table; `docs/packages/$pkg/assessment.md` if present; **Write your report to**
`docs/reviews/<today>-$pkg-plan.md`. **Steps**: read; work the plan checklist; write;
append CRITICALs to `docs/followups.md` addressed to `$pkg/plan`; commit; return.

## Reviewer plan mode (`agents/reviewer.md`, new section after the package checklist)

> ## Plan review checklist — `/dev-team:review-plan`
>
> The object is the plan, not code. Every finding cites a document and a heading or row,
> in place of `file:line`. In priority order:
>
> 1. **Decomposition.** Every row of the contract's Sections table has a `path` a person
>    could own (`project-structure` §1) and appears in the integration doc's **Dependency
>    order**; `Depends on` forms a DAG; no design's **Module plan** exceeds `project-structure`
>    §2 hard limits on its face (a plan that needs a split is a plan that should have had two
>    sections). CRITICAL: a cycle, a section with no path, a section in the order that is not
>    in the table or vice versa.
> 2. **Seams.** For every name a design consumes from a sibling, the sibling's design §5
>    **Interfaces** provides it with the same signature; for every upstream name, the
>    upstream `interface.md` **Public names** lists it (or the contract does, and the design
>    marks it provisional). CRITICAL: a consumed name nobody provides, or two designs that
>    disagree on a signature the integration doc's **Cross-section mismatches** does not
>    resolve.
> 3. **Surface.** Every **Public names** row in `surface.md` names a providing section whose
>    design has that row `Public: yes`, and the contract's **Public surface (intent)** names
>    its consumer; every `Public: yes` design row is in `surface.md` or the integration doc
>    says why not. Every pipeline in `surface.md` calls sections in an order the DAG permits.
>    CRITICAL: a public name with no consumer, or a pipeline that calls a section before its
>    dependency.
> 4. **Contracts.** Every design §10 **Contract deviations** entry is resolved in the
>    integration doc's **Contract deviations** (accepted into the contract, rejected with a
>    required change, or `needs user decision` with a `D<n>`); every **Repo contract
>    deviations** entry likewise; no design contradicts a `decided` `D<n>` in scope.
>    CRITICAL: an unresolved deviation, or a contradiction with a decided entry.
> 5. **Decisions.** Every design §11 **Open questions** `OQ-…` tag has a `D<n>` whose
>    `Raised by:` cites it; every `D<n>` scoped to this package that is `open` carries an
>    `Assumption if unanswered:` or the integration doc's **Decisions needed from user**
>    says why it cannot. WARNING: an open decision with no assumption (it will block an
>    implementer; say which section). CRITICAL: an `OQ` with no `D`.
> 6. **Sources.** Every section with a `source` has a probe doc whose **Access** reads
>    `valid` or `readable`; every field the design's parser or loader names is under the
>    probe's **Observed schema**; for a dataset that ran task fit, the design's target, split
>    and excluded columns match **Target**, **Splitting**, **Leakage**. CRITICAL: a field not
>    observed, a split the probe forbids.
> 7. **Tests.** Every design §7 **Tests** names its fixtures and includes one end-to-end
>    path; `surface.md` §4 names one test per pipeline. Where `docs/constraints.md` sets a
>    coverage floor, no design's §7 is empty. WARNING otherwise.
> 8. **Skills.** Every section's design §9 **Skills used** lists the skills the contract's
>    `Builds with` column assigns it; a project skill assigned to no section is a WARNING
>    naming the architect's two signals (a skill with no section / a section with no skill).
>
> Report shape is the section shape with `Commit:` and these headings; the object of every
> finding is `<document>#<heading or row>`. Append CRITICALs to `docs/followups.md` as
> `- [ ] <pkg>/plan: <finding> — review <date>, see docs/reviews/<date>-<pkg>-plan.md`.
> Verdict `approve` means an implementer may fork; `request changes` means
> `/dev-team:plan-package <pkg>` must run again first.

The reviewer's `tools:` is unchanged. Its Bash usage paragraph gains: *in plan mode there
is no code to run; Bash is `git` and read-only inspection only.*

## Closing the loop: the architect reads `<pkg>/plan` follow-ups

`agents/architect.md`, package scope, a new step between the interview rule and the
contract (in `skills/plan-package/SKILL.md` it is step 3b **Plan findings**):

> Read `docs/followups.md` for open entries addressed to `$pkg/plan`. If there are none,
> continue. Otherwise this is a re-plan: for each finding, decide which document it
> corrects — the contract (edit it), the integration doc or `surface.md` (rewritten at
> unify anyway), or a design (re-delegate that section only, with
> `Existing design: <path>` and a new field `Review findings: docs/reviews/<date>-$pkg-plan.md`
> in the delegation prompt; the designer reads the findings that name its section and
> revises in place). Sections with no finding are not re-delegated. When every finding has
> been addressed, tick each `- [ ] $pkg/plan:` entry `[x] <date>`. Your return names the
> plan review you answered and says `/dev-team:review-plan $pkg` is the next command.

`agents/designer.md`: the delegation-prompt field list gains `Review findings: <path> |
none`; §Inputs says *when a path is given, read the findings that cite your section and
address each one in the revised design; list what you changed under a final heading
**Revision** so the reviewer can check the finding against it.* `contracts.yml`: the
architect's delegation template is the owner of that field name (already in the
`architect.md` body); no new contract — the field is a prompt line, not a parsed heading.

## Implementer blocking rule

`agents/implementer.md` §Blocking rules, new entry:

> **An open plan finding.** `docs/followups.md` has an unchecked entry addressed to
> `<pkg>/plan` whose text contains `review `. The plan you would build from has a CRITICAL
> finding against it. Return the blocker naming `/dev-team:plan-package <pkg>` and the
> review file.

A plan that was never reviewed does **not** block a manual `implement-section`; only
`run-package` requires a review (phase 8). That keeps the manual loop as flexible as 0.4.

## `status.py --plan-gate <pkg>`

Prints `plan gate: PASS|FAIL` with reasons, exit 1 on FAIL:

- `docs/packages/<pkg>/{contract,integration,surface}.md` exist.
- `integration.md` has no **Spine** heading reading `spine only`.
- The newest `docs/reviews/*-<pkg>-plan.md` exists and its `Commit:` equals
  `last_commit("docs/packages/<pkg>")`; otherwise *plan not reviewed since last change*.
- Its `Verdict:` is `approve` or `approve with fixes`.
- No open `- [ ] <pkg>/plan:` entry containing `review `.
- No `D<n>` with `Status: open`, no `Assumption if unanswered:` value, and a `Scope:` that
  is `repo`, `<pkg>`, or contains `<pkg>/`.

The package report also gains a line `plan: reviewed <date> <verdict> @<sha> | unreviewed`.

## Three-file rule, contracts, site

- `reserved-skill-names`: `review-plan` (workflow). README tree and §Which skill to run
  (`plan reviewed? → /dev-team:review-plan <pkg>` after `plan-package`). `site.yml`: after
  `plan-package`.
- `contracts.yml` `headings`: the plan checklist cites design headings (`Interfaces`,
  `Module plan`, `Tests`, `Skills used`, `Contract deviations`, `Open questions`), integration
  headings (`Dependency order`, `Cross-section mismatches`, `Contract deviations`, `Repo
  contract deviations`, `Decisions needed from user`), surface headings (`Public names`,
  `Pipelines`, `Tests`), probe headings (already covered), and `interface.md` `Public
  names` (already covered). Add `agents/reviewer.md` as a reader with those `cites` under
  the existing owners: `agents/designer.md` (template span), and new owners
  `skills/planning-templates/references/integration.md` and
  `skills/planning-templates/references/surface.md` (`owner_span` from their first numbered
  item to `null`).

## Steps

1. Reviewer plan mode section; skill file.
2. Architect step 3b and delegation field; designer input and **Revision** heading.
3. Implementer blocking rule; `status.py --plan-gate` and the `plan:` line.
4. Three-file rule; `contracts.yml`; `check-contracts`; `build-site`.
5. Evals (note 09 §G): behavioral — on the fixture, a plan seeded with two defects (a
   consumed name no design provides; an `OQ` with no `D`) yields a report with exactly those
   two CRITICALs and two `data/plan` follow-ups; then `plan-package` re-run re-delegates
   exactly one designer and ticks both; then `review-plan` approves and `--plan-gate`
   passes. Log it.
6. Commit: `dev-team 0.5 (phase 5): review-plan, reviewer plan mode, plan gate`.

## Done when

The three-run eval sequence passes and is logged; `--plan-gate` exists; the implementer
blocks on an open plan finding (checked mechanically by seeding one).
