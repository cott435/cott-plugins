---
name: test-section
description: Write a section's intent tests from its design before it is built (intent mode, red by construction), or fold the built section's recorded deviations into them and file what still fails (reconcile mode). Use before /dev-team:implement-section, and again after it, before /dev-team:review-section.
argument-hint: "<pkg>/<section> [plan-slug]"
arguments: [section, plan]
context: fork
agent: dev-team:tester
background: false
disable-model-invocation: true
---

Test section: **$section**
Plan slug (empty for canonical work): **$plan**

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `tester` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not write tests in the main thread.

If `$section` reached you unsubstituted — literally the text `$section` — parse the section
and optional plan slug from `$ARGUMENTS` instead, first token and second token. If your task
prompt carries `Section:` and `Plan:` lines instead (`/dev-team:run-package` passes them that
way), use those.

## Resolve the identity

`$section` is `<pkg>/<name>`. Split on the `/`: `$pkg` is the part before it, `$name` the part
after. If there is no `/`, read the Packages table in `docs/architecture.md`: with exactly one
row, that is `$pkg`; with more, return a blocker asking for the qualified name. If `$name` is
`surface`, stop: a package's surface is tested by `/dev-team:finalize-package $pkg`.

## Paths

| Document | Path | If absent |
|---|---|---|
| Repo contract | `docs/architecture.md` | Blocker naming `/dev-team:plan-repo`. |
| Package contract | `docs/packages/$pkg/contract.md` | Blocker naming `/dev-team:plan-package $pkg`. |
| Contract delta | `docs/plans/$plan/contract-delta.md` *(only when a slug is set)* | The canonical contracts stand. |
| Design | `docs/plans/$plan/$pkg/$name.md` if a slug is set, else `docs/packages/$pkg/design/$name.md` | Blocker. There is no spec to test against. |
| Integration | `docs/plans/$plan/integration.md` if a slug is set, else `docs/packages/$pkg/integration.md` | Proceed on the design alone; say so. |
| Decisions | `docs/decisions.md` | No decisions to assert. |
| Constraints | `docs/constraints.md` — its **Enforced** coverage row | No coverage floor to size the suite against. |
| Follow-ups | `docs/followups.md` | Created on your first append (reconcile mode). |
| Dependency READMEs | the README of each section in the package contract's `Depends on` for `$name` | Proceed with fakes built from the package contract; say which consumed signatures are plan-time. |
| Upstream interfaces | `docs/packages/<dep>/interface.md` for each package `$pkg` depends on | As above, from that package's `contract.md`. |
| Source probe | `docs/sources/<source>.md` for every entry in the section's `source` column, plus `<source>.sample.json` or `<source>.stats.json` | Fixtures come from the design's **Tests** section; say so. |
| Section README | `README.md` at the section's path in the package contract's Sections table | Intent mode. |
| **Your tree** | `tests/intent/$name/` under the package root | Created in intent mode. |

With a plan slug the tests still go to `tests/intent/$name/`: they describe the section, not
the plan. The design they are written from is the plan's.

## Mode

**Reconcile** if the section README exists, else **intent**. Say which as the first line of
your return.

## Steps

1. Read every document above that exists — and nothing under the section's source path but
   its `README.md`.
2. Run the mode from your agent body.
3. Commit per your **Commit rule** — trailer `Dev-Team-Run: test-section $ARGUMENTS` — then
   return your summary in your standard format.
