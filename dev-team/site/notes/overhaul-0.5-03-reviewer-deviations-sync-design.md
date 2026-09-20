# 03 — Reviewer order of authority, the deviation rule, and `sync-design`

Phase 3. Three edits that close the same gap: a section that correctly departed from its
design is currently indistinguishable, to the reviewer, from one that ignored it; and the
design it departed from is never corrected.

## A. The reviewer carries the order of authority

`agents/reviewer.md` gains a section, placed directly after §Inputs, with this content:

> ## Order of authority
>
> You review against the same order the implementer builds by. **For what the section
> builds**, highest first: `docs/constraints.md` (for the checks it names; phase 6) →
> `docs/decisions.md` entries that are `decided` and in scope → the integration doc for this
> run → `contract-delta.md` (when a plan slug is set) → the package contract → the repo
> contract → the section's design, read together with its **As shipped** section when one
> exists. A finding is measured against the highest document that speaks to it; a design
> line that a higher document overrides is not a spec gap.
>
> **For what the section consumes**: the provider's shipped document — a sibling's README
> **Entry points and interfaces**, an upstream package's `interface.md`, an external
> source's probe doc — outranks every plan-time document about that provider.

`contracts.yml` `headings` gains: owner `agents/implementer.md`,
`owner_span: ['## Order of authority', '## The decisions file']`, reader
`agents/reviewer.md`, `cites: ['Order of authority']`. That does not check the two lists
say the same thing; it checks the reviewer's heading names one the implementer has. The
lists saying the same thing is the eval in §Steps.

## B. The recorded-deviation rule

The section review checklist item 1 (**Spec conformance**) is amended. Before the existing
text, insert:

> Read the section README's **Implementation notes** (item 7) first. Every deviation it
> records — *what the document said, what I did, why* — is a **recorded deviation**. Then:
>
> - A recorded deviation is **WARNING at most**, and its finding text names the document
>   it departed from and asks whether `/dev-team:sync-design` has run. It becomes CRITICAL
>   only when it (a) contradicts a contract — repo, package, or delta; (b) contradicts a
>   `decided` `D<n>` in scope; (c) changes a name or signature an upstream `interface.md`
>   or a sibling README that this section *consumes* defines; or (d) leaves an intent test
>   failing with no follow-up filed for it (phase 4).
> - A departure from the design that item 7 does **not** record is CRITICAL, as today —
>   the failure is the silence, not the departure.
> - A departure the README records *without a reason* is CRITICAL with the finding text
>   *deviation recorded without a reason*.

The package checklist already applies this rule to `interface.md` (lines 103–104 in 0.4:
"deviations `interface.md` records are noted, not repeated as findings; deviations it does
not record are findings"); the wording there is aligned to the same three-way split.

## C. `sync-design`

A new workflow skill, `skills/sync-design/SKILL.md`, run by the architect in sync scope. It
folds the recorded deviations of every built section of a package back into that section's
design document, appending — never rewriting — so the design stays readable as history and
truthful as a spec.

### Frontmatter

```yaml
---
name: sync-design
description: Fold each built section's recorded deviations (README item 7) back into its design doc under an As shipped heading, so docs/packages/pkg/design/ stops describing code that never existed. Run after review-package passes and before planning the next package.
argument-hint: "<pkg>"
arguments: [pkg]
context: fork
agent: architect
background: false
disable-model-invocation: true
---
```

### Body (specification, not prose to paste)

- Guard block, as every forked skill.
- **Preconditions**: `docs/packages/$pkg/contract.md` exists; at least one section README
  exists. Not required: `interface.md` (a package may be synced mid-build; only built
  sections are touched).
- **Reads**: the contract's Sections table; for each section with a README, that README's
  item 7 and the design at `docs/packages/$pkg/design/<section>.md`; `docs/decisions.md`
  (for the `Applied:` lines that name `$pkg/<section>`); `docs/packages/$pkg/interface.md`
  if it exists (for surface deviations, which go to `surface.md`, below).
- **Writes**, per built section whose item 7 records at least one deviation: append to the
  design doc a final section:

  ```
  ## As shipped — <date>

  Source: <path of the README>, item 7; commit <sha of last_commit(section)>.

  | Design said | Shipped | Why | Recorded in |
  |---|---|---|---|
  | <design item, quoted or cited by heading and row> | <what the README says exists> | <the README's reason> | README item 7 |

  Decisions applied: D<n>, D<m> (from docs/decisions.md Applied: lines naming this section)
  Design items unchanged by shipping: all others.
  ```

  A section whose item 7 records no deviation gets the same heading with the single line
  *No deviations recorded; the design above describes the shipped code as of commit <sha>.*
  A design that already has an **As shipped** section gets a new one appended below it,
  dated; earlier ones are never edited. That is the whole write; nothing above the heading
  changes.
- Also: where `interface.md` exists and its **Deviations** section names a surface
  deviation, append the same table shape to `docs/packages/$pkg/surface.md` under
  `## As shipped — <date>`.
- **Never** touches `contract.md`, `architecture.md`, `integration.md`, any README, any
  code. A deviation that contradicts the package contract is not folded; it is returned as
  a finding with the words *contract conflict — needs `/dev-team:plan-change`* and a `D<n>`
  stub is appended to the ledger with `Scope: $pkg/<section>` and
  `Raised by: /dev-team:sync-design $pkg`.
- **Commit** per §Project convention, scope `plan $pkg`, summary
  `sync-design: <n> sections, <m> deviations folded`.
- **Return**: sections synced; deviations folded per section; contract conflicts (with
  their `D<n>`); next command — `/dev-team:plan-package <next package in the repo
  contract's dependency order>` when `interface.md` exists, otherwise
  `/dev-team:implement-section $pkg/<next unbuilt section>`.

### Architect changes

`agents/architect.md` §Scopes table: the **sync** row's Skill cell becomes
`/dev-team:sync-plan`, `/dev-team:sync-design`; its Produces cell adds *; design docs
gain **As shipped** sections (sync-design)*. The document map row for
`docs/packages/<pkg>/design/<section>.md` Written-by cell becomes *designers you spawn;
you in sync scope (append-only, **As shipped**)*.

`skills/planning-templates/references/`: no new file. The **As shipped** shape lives in
the `sync-design` skill body because it is the only writer and `contracts.yml` names the
skill as owner: `headings` owner `skills/sync-design/SKILL.md`,
`owner_span: ['## As shipped', null]`, readers `agents/reviewer.md`
(`cites: ['As shipped']`), `skills/plan-change/SKILL.md` (`cites: ['As shipped']`).

### Who reads **As shipped**

- The reviewer (order of authority above): the design *together with* its As shipped
  sections is the lowest document, and a re-review after sync must not re-raise a folded
  deviation.
- `plan-change` (architect, change scope): its **What you read** list gains *each affected
  section's design including its **As shipped** sections — the latest one is the spec the
  change departs from.* One sentence; no other change to `plan-change`.
- `run-package` (phase 8) runs `sync-design` as its last step.

## Three-file rule and site

`sync-design` is added to `reserved-skill-names` (workflow), the README Contents tree,
and `site.yml` after `review-package`.

## Steps

1. Reviewer §Order of authority and the item-1 amendment; align the package checklist
   wording.
2. Write `skills/sync-design/SKILL.md`; architect edits; `plan-change` sentence.
3. `contracts.yml` two `headings` entries.
4. Three-file rule; `check-contracts`; `build-site`.
5. Evals (note 09 §E): mechanical — the two order-of-authority lists, extracted by regex
   from both agents, are identical after normalizing whitespace; behavioral — on the
   fixture, a section with one recorded deviation (with reason) and one unrecorded one is
   reviewed and the report has exactly one WARNING naming sync-design and exactly one
   CRITICAL; then `sync-design` runs and the design's As shipped table has one row.
6. Commit: `dev-team 0.5 (phase 3): reviewer order of authority, recorded-deviation rule, sync-design`.

## Done when

`check-contracts` passes with the two new heading contracts; the behavioral eval's report
has the 1 WARNING / 1 CRITICAL split; the As shipped section exists on the fixture design.

## Deviations

- **No `docs/constraints.md` item in either list yet.** §A's reviewer list opens with
  `docs/constraints.md` marked *phase 6*, and note 06 §Order of authority inserts it at the top
  of both lists. Adding it to the reviewer alone now would make the lists differ, and that
  equality is the check eval E runs. Both lists are six items until phase 6, which adds the
  seventh to both.
- **The reviewer carries the implementer's numbered item names, not the note's one-line
  prose.** Eval E compares lists "extracted by regex", and a regex has nothing to match in a
  single sentence of arrows. So the reviewer's section numbers the same six bolded items as the
  implementer. Item 6 in both is now **The section's design doc**; the implementer's was "Your
  section's design doc". The implementer's item 6 also gains *read together with its **As
  shipped** sections*, which the note gave only the reviewer, because an implementer re-running
  a section after a sync builds against the same design.
- **The order-of-authority contract uses a reader `span`, not `cites: ['Order of
  authority']`.** `check_headings` counts as owned only the numbered, bolded items in the
  owner's span, and the owner's heading is not one of them. `cites: ['Order of authority']`
  would therefore always FAIL. The reader span (`'design line that a higher document
  overrides'` → `'read together with'`) holds the reviewer's numbered items. Their bolded names
  must be the implementer's names, and a missing span marker is a FAIL, so the reviewer's
  section has to exist. Items that open with a backticked path are invisible to the reader
  parser. Eval E's control 2 confirms that gap, and eval E's script covers it.
- **The As shipped contract's owner span is `['## What you write', '## Commit and return']`,
  not `['## As shipped', null]`.** The template is a fenced block with no numbered items, so the
  note's span has nothing to own. **As shipped** is item 1 of the skill's numbered **What you
  write** list, with the surface version as item 2 and contract conflicts as item 3. The
  implementer is a third reader (`cites: ['As shipped']`) because its item 6 now names the
  heading.
- **README template item 7 asks for *why*.** It said "what the document said and what you
  did". The reviewer now grades a deviation recorded without a reason as CRITICAL, so the
  template names the reason as well, matching the implementer's own §Deviations.
- **`sync-design` skips a section whose latest As shipped already cites the section's current
  last commit.** Without the skip, a second run with nothing new shipped would append a
  duplicate dated section.
- **A deviation recorded without a reason is still folded,** with *no reason recorded* in the
  Why cell. The note does not cover this case, and the reviewer already raises it as CRITICAL.
- **Contract conflicts cover the repo contract and `decided` decisions too,** not only the
  package contract. That matches reviewer rules (a) and (b).
- **Next command after `interface.md` exists**: `/dev-team:finalize-project` when no package
  is left to plan. The note's two options had no case for the last package.
- **`review-package` returns `/dev-team:sync-design $pkg` on a passing verdict**, in place of
  `/dev-team:plan-package <next>` or `/dev-team:finalize-project`. The note puts sync-design
  after review-package, but nothing in the manual flow pointed the user there until phase 8's
  driver. `site/workflows/new-repo.md`, `site/flow.md` (the loop diagram and the two document
  rows) and README (§Which skill to run, §Workflows, the `docs/` layout, the hand-off diagram)
  name it as well.
- **Eval E's behavioral fixture state was written by hand**, not produced by
  `plan-repo` → `plan-package` → `implement-section`. The eval tests how the reviewer grades
  seeded deviations, so the deviations have to be exactly the ones seeded.
