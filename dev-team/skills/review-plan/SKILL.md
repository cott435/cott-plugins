---
name: review-plan
description: Review a package's complete plan — contract, every section design, integration.md, surface.md — against the repo contract, the decisions ledger, the shipped interfaces it consumes, the probe docs, and docs/constraints.md, before any section is implemented. Writes docs/reviews/date-pkg-plan.md and files CRITICAL findings to followups addressed to pkg/plan, which the next plan-package run picks up. Numbers the plan-and-review rounds and stops the loop when it is not converging; --defer re-addresses the standing findings to their sections so the build can start.
argument-hint: "<pkg> [--defer]"
arguments: [pkg, flags]
context: fork
agent: dev-team:reviewer
background: false
disable-model-invocation: true
---

Review plan: **$pkg** — the documents `/dev-team:plan-package $pkg` wrote, before any
implementer forks against them.

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `reviewer` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run.

The command was typed with these arguments: **`$ARGUMENTS`**. The first word is the package;
if `$pkg` reached you unsubstituted, take it from there. `--defer` after it makes this a
**deferral run** — your **Rounds and convergence** section's `--defer`: no review, the open
`$pkg/plan` findings re-addressed to their sections, an `approve with fixes` report. It is
what the user types after a plan review stopped the loop; on a package whose newest plan
review approves, or with no open `$pkg/plan` finding, return `Result: blocked` saying there
is nothing to defer.

**Invoked by run-package.** If your task prompt carries a `Package:` line instead of a
substituted argument — `/dev-team:run-package` spawns you that way — use it: the package from
that line, and the same name as the argument in your commit trailer. The Guard block above
does not fire: you have neither earlier turns nor `AskUserQuestion`.

## Why this exists

Every other review runs after code exists. By then a seam two designs disagree on, or an open
question nobody turned into a decision, has already been built into two sections. This is the
design review a team holds before anyone writes code: the architect's contract, the designers'
designs and the architect's reconciliation, checked against each other and against everything
above them by someone who wrote none of them.

## Preconditions

First, if `docs/packages/$pkg/integration.md` has a **Spine** heading whose status line reads
`spine only`, return the blocker *plan is spine-only: build the spine, re-run
`/dev-team:plan-package $pkg`, then this* and stop — a spine run writes no `surface.md`, so this
check comes before the next one or it would never be reached.

Then `docs/packages/$pkg/contract.md`, `docs/packages/$pkg/integration.md` and
`docs/packages/$pkg/surface.md` all exist. If any is missing, return the blocker naming
`/dev-team:plan-package $pkg` — the plan is not complete, and a partial plan has no seams to
check.

## Paths

| Document | Path |
|---|---|
| Package contract | `docs/packages/$pkg/contract.md` |
| Integration | `docs/packages/$pkg/integration.md` |
| Surface | `docs/packages/$pkg/surface.md` |
| Designs | every `docs/packages/$pkg/design/*.md` |
| Repo contract | `docs/architecture.md` |
| Decisions | `docs/decisions.md` |
| Follow-ups | `docs/followups.md` — entries addressed to `$pkg/plan`: skip what is already listed, and append your CRITICAL findings here |
| Constraints | `docs/constraints.md`, if present |
| Upstream interfaces | for each package in the repo contract's `Depends on` for `$pkg`: `docs/packages/<dep>/interface.md`, or, if absent, `docs/packages/<dep>/contract.md` read as provisional |
| Source probes | `docs/sources/<source>.md` for every entry in the `source` column of the contract's Sections table |
| Assessment | `docs/packages/$pkg/assessment.md`, if present |
| **Write your report to** | `docs/reviews/<today's date, YYYY-MM-DD>-$pkg-plan.md` |

## Steps

1. Read every document above that exists. There is no code to read. Run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py $pkg --plan-rounds` from
   the repo root: this review is round `n + 1`.
2. Work your **Plan review checklist** in priority order. From round 2 on, classify the
   previous report's CRITICALs first, per your **Rounds and convergence** section — a fact
   the last re-plan corrected in some sections and not others is one unfixed finding, not a
   new one per section.
3. Write your report to the path above, with its `Round:` line and, from round 2 on, its
   `Convergence:` line.
4. Append every CRITICAL finding to `docs/followups.md` addressed to `$pkg/plan`, so the next
   `/dev-team:plan-package $pkg` run picks them up without anything passing through chat.
5. Commit per your **Commit** section — scope `review $pkg/plan`, trailer
   `Dev-Team-Run: review-plan $ARGUMENTS` — then return your summary, ending with the next
   command: on `request changes`, `/dev-team:plan-package $pkg` while **Rounds and
   convergence** says the loop is converging, else that section's not-converging block, which
   offers `/dev-team:plan-package $pkg` and `/dev-team:review-plan $pkg --defer` and leaves the
   choice to the user; otherwise
   `/dev-team:test-section $pkg/<first section in the integration doc's Dependency order>`.

On a deferral run, steps 1–4 are replaced by the `--defer` procedure in **Rounds and
convergence**; step 5 commits the report and `docs/followups.md` with the trailer
`Dev-Team-Run: review-plan $ARGUMENTS` and ends with the `test-section` command.

Change nothing but your report and `docs/followups.md`.
