---
name: sync-design
description: Fold each built section's recorded deviations (README item 7) back into its design doc under an As shipped heading, so docs/packages/pkg/design/ stops describing code that never existed. Run after review-package passes and before planning the next package.
argument-hint: "<pkg>"
arguments: [pkg]
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---

Fold the recorded deviations of package **$pkg** back into its design docs — **sync scope**.

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `architect` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not plan in the main thread.

If `$pkg` reached you unsubstituted, take the package name from `$ARGUMENTS`.

A section that correctly departed from its design records the departure in its README's
**Implementation notes** (item 7). The design it departed from is never corrected by anyone
else, so it goes on describing code that does not exist — and that stale design is what the
reviewer ranks lowest, what `/dev-team:plan-change` hands its designers as the baseline, and
what the next reader believes. This run appends the truth under each design; it never rewrites
the design above it, so the doc stays readable as history and truthful as a spec.

`/dev-team:sync-plan` is the other sync-scope skill: it folds a *change plan* into canonical
docs and rewrites them coherently. This one folds a *section's own* deviations, and only
appends.

## Preconditions

- `docs/packages/$pkg/contract.md` exists. Missing → return *`$pkg` is not planned; run
  `/dev-team:plan-package $pkg`* and stop.
- At least one section README exists at a path from the contract's Sections table. None →
  return *nothing built in `$pkg` yet* and stop.

Not required: `interface.md`. A package may be synced mid-build; only built sections — those
with a README — are touched.

## What you read

| Document | Path |
|---|---|
| Sections table | `docs/packages/$pkg/contract.md` |
| Each built section's README, item 7 | at the section's path from the Sections table |
| Each built section's design | `docs/packages/$pkg/design/<section>.md` |
| Decisions | `docs/decisions.md` — the `Applied:` lines that name `$pkg/<section>` |
| Last commit per section | `git log -1 --format=%h -- <section source path> <tests/unit/<section>> <tests/intent/<section>>` |
| Interface, if shipped | `docs/packages/$pkg/interface.md` — its **Deviations** section |
| Surface, if `interface.md` exists | `docs/packages/$pkg/surface.md` |

## What you write

1. **As shipped** — for every built section, append one final section to its
   `docs/packages/$pkg/design/<section>.md`:

   ```
   ## As shipped — <date>

   Source: <path of the README>, item 7; commit <sha of the section's last commit>.

   | Design said | Shipped | Why | Recorded in |
   |---|---|---|---|
   | <design item, quoted or cited by heading and row> | <what the README says exists> | <the README's reason> | README item 7 |

   Decisions applied: D<n>, D<m> (from docs/decisions.md Applied: lines naming this section)
   Design items unchanged by shipping: all others.
   ```

   One row per deviation item 7 records against the design, the contracts, the integration
   doc, or `surface.md`. Notes in item 7 that are not deviations — consumed READMEs, open
   markers — are not rows. A section whose item 7 records no deviation gets the heading and
   the single line *No deviations recorded; the design above describes the shipped code as of
   commit <sha>.*

   A design that already has an **As shipped** section gets a new one appended below it,
   dated; earlier ones are never edited. Skip a section whose latest **As shipped** already
   cites its current last commit — nothing shipped since. That is the whole write: nothing
   above the heading changes.

2. **As shipped** on the surface — when `interface.md` exists and its **Deviations** section
   names a surface deviation, append the same table shape to `docs/packages/$pkg/surface.md`
   under `## As shipped — <date>`, with `interface.md` **Deviations** as the source.

3. **Contract conflicts** — a recorded deviation that contradicts the package contract, the
   repo contract, or a `decided` `D<n>` is **not** folded. Leave it out of the table, append
   a `D<n>` stub to `docs/decisions.md` with `Scope: $pkg/<section>` and
   `Raised by: /dev-team:sync-design $pkg`, and return it as a finding worded
   *contract conflict — needs `/dev-team:plan-change`*.

Never touch `contract.md`, `architecture.md`, `integration.md`, any README, or any code. A
deviation recorded without a reason is folded with *no reason recorded* in the Why cell and
listed in your return — the reviewer already raises it as CRITICAL.

## Commit and return

**Commit** per your **Commit** section — scope `plan $pkg`, summary
`sync-design: <n> sections, <m> deviations folded`, trailer
`Dev-Team-Run: sync-design $ARGUMENTS` — then **return**: the paths of every document written or modified, sections synced, deviations folded
per section, sections skipped as already current, contract conflicts with their `D<n>`,
`Commit: <sha>`, and the next command — `/dev-team:plan-package <next package in the repo
contract's dependency order>` when `interface.md` exists (or `/dev-team:finalize-project`
when none is left), otherwise `/dev-team:implement-section $pkg/<next unbuilt section>`.
