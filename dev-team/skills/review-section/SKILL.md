---
name: review-section
description: Review an implemented section of a package against its design doc, the contracts, and the shipped documents it consumes. Writes findings to docs/reviews/date-pkg-section.md and files critical ones into docs/followups.md so the next implement-section run picks them up. Numbers the build-and-review rounds and stops the loop when it is not converging; --defer re-files the standing findings as ordinary follow-ups so the package can finalize.
argument-hint: "<pkg>/<section> [plan-slug] [--defer]"
arguments: [section, plan]
context: fork
agent: dev-team:reviewer
background: false
disable-model-invocation: true
---

Review section: **$section**
Plan slug (empty for canonical work): **$plan**

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `reviewer` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run.

If `$section` reached you unsubstituted, parse the section and optional plan slug from
`$ARGUMENTS` — first token and second token. A `--defer` token anywhere after the section
makes this a **deferral run** — your **Rounds and convergence** section's `--defer`, section
form: no review, the open review-sourced `$pkg/$name` findings re-filed as `— noted` entries,
an `approve with fixes` report. It is what the user types after a section review stopped the
loop; on a section whose newest review approves, or with no open review-sourced finding,
return `Result: blocked` saying there is nothing to defer.

**Invoked by run-package.** If your task prompt carries `Section:` and `Plan:` lines instead of
substituted arguments — `/dev-team:run-package` spawns you that way — use those: the section
from the first, the plan slug (usually empty) from the second, and the two, space-separated,
as the argument in your commit trailer. The Guard block above does not fire: you have neither
earlier turns nor `AskUserQuestion`.

## Resolve the identity

`$section` is `<pkg>/<name>`; split on the `/` into `$pkg` and `$name`. With no `/`, use the
sole row of the Packages table in `docs/architecture.md` as `$pkg`, or return a blocker asking
for the qualified name if there is more than one. If `$name` is `surface`, stop and name
`/dev-team:review-package $pkg`.

## Paths

| Document | Path |
|---|---|
| Repo contract | `docs/architecture.md` |
| Package contract | `docs/packages/$pkg/contract.md` |
| Contract delta | `docs/plans/$plan/contract-delta.md` *(when a slug is set)* |
| Design | `docs/plans/$plan/$pkg/$name.md` if a slug is set, else `docs/packages/$pkg/design/$name.md` |
| Integration | `docs/plans/$plan/integration.md` if a slug is set, else `docs/packages/$pkg/integration.md` |
| Surface | `docs/packages/$pkg/surface.md` — which entry points should be `Public: yes` |
| Decisions | `docs/decisions.md` |
| Constraints | `docs/constraints.md` — axis 0: **Floor** and **Enforced** rows to run, **Guarded** items to grep the diff for, **Exceptions** |
| Follow-ups | `docs/followups.md` — entries addressed to `$pkg/$name`: skip what is already listed, and append your CRITICAL findings here in step 4 |
| Section README | the README at the section's path in the package contract's Sections table |
| Dependency READMEs | the README of each section in `Depends on` for `$name` |
| Upstream interfaces | `docs/packages/<dep>/interface.md` for each package `$pkg` depends on |
| Source probe | `docs/sources/<source>.md` for every entry in the section's `source` column of the Sections table, plus `<source>.sample.json` for an `api` or `<source>.stats.json` for a `dataset` |
| **Write your report to** | `docs/reviews/<today's date, YYYY-MM-DD>-<pkg>-<section>.md`, with `$pkg` and `$name` in place of the placeholders |

If the design doc is missing there is no spec to conform to — review for correctness,
security, tests, and documentation only, and say in the report that spec conformance was not
checked and why.

## Steps

1. Read the documents above, then the section's code and tests. Run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --rounds $pkg/$name` from
   the repo root: this review is round `n + 1`.
2. Work your **section review checklist** in priority order, grading by your **Severity**
   list. Spec conformance first, including the seams: the point of this system is that the
   code matches the documents, and a section that works but diverges is the failure mode that
   only surfaces when another section — or another package — trusts the contract. From round
   2 on, classify the previous report's CRITICALs first, per your **Rounds and convergence**
   section.
3. Write your report to the path above, with its `Round:` line and, from round 2 on, its
   `Convergence:` line.
4. Append every CRITICAL finding to `docs/followups.md` addressed to `$pkg/$name`, so the next
   `/dev-team:implement-section $pkg/$name` picks them up without anything passing through chat.
5. Commit per your **Commit** section — trailer `Dev-Team-Run: review-section $ARGUMENTS` —
   then return your summary, ending with the next command: on `request changes`,
   `/dev-team:implement-section $section` while **Rounds and convergence** says the loop is
   converging, else that section's not-converging block, which offers that command and
   `/dev-team:review-section $section --defer` and leaves the choice to the user; otherwise the
   next section in the integration doc's Dependency order, or `/dev-team:finalize-package $pkg`
   after the last.

On a deferral run, steps 1–4 are replaced by the `--defer` procedure in **Rounds and
convergence**; step 5 commits the report and `docs/followups.md` with the trailer
`Dev-Team-Run: review-section $ARGUMENTS` and ends with the approving next command.

Change nothing but your report and `docs/followups.md`.
