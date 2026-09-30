---
name: sync-plan
description: Close a package - fold every approved deviation and every pending change file into the canonical contracts after verifying each against the shipped code, mark them synced, and recompute the consumers of any changed public name. run-package runs it when every section is DONE; run it by hand after editing a section ledger (docs/packages/{pkg}/deviations/) or a change file.
argument-hint: "<pkg>"
arguments: [pkg]
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---

Close package **$pkg** — **close scope**.

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `architect` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not plan in the main thread.

If `$pkg` reached you unsubstituted, take the package from `$ARGUMENTS`.

**Spawned by run-package.** A prompt that carries `Package: <pkg>` and `Run: run-package <pkg>`
lines comes from `/dev-team:run-package` at the package close: use that package, skip step 1
(the driver ran the run gate), and use `Dev-Team-Run: run-package <pkg>` as the trailer.

Until this runs, a package's contract describes the code as it was planned, not as it was
built: an approved deviation lives only in its section's ledger,
`docs/packages/<pkg>/deviations/<section>.md`, and an open change file only under
`docs/packages/<pkg>/changes/`. Those contracts are what the next `/dev-team:plan-package` reads as its
upstream. This is the step that stops the drift.

## Steps

1. **Run gate.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate $pkg`.
   FAIL → return `Result: blocked` with its lines, and write nothing.

2. **The close**, per your **sync-plan — the package close**: collect the approved deviations
   and the open change files for `$pkg`; verify each against the code; archive each contract
   before its first edit; apply what verified; set `synced` on what was applied; recompute and
   classify the consumers of every changed public name; then the W2 sweep, your **sync-plan**
   step 7. Invoke `planning-templates` and read
   `references/deviations-entry.md` and `references/change.md` before the first status line.
   Nothing to collect → return `Result: done` saying so, and commit nothing.

3. **Decisions.** For each `D<n>` scoped to `$pkg` or one of its sections, compare `Status:`
   and `Applied:` with the code: `decided` with no `Applied:` line and no matching code means it
   was answered but never built. Do not edit those fields — they belong to the user and the
   implementer. List every mismatch in your return.

4. **Commit** per your **Commit** section — scope `plan $pkg`, trailer `Dev-Team-Run: sync-plan
   $ARGUMENTS` (or `run-package $pkg` from the driver) — then **return**: one row per entry,
   `synced` or `left open: <why>`; the consumer classification (CHANGE per shipped consumer,
   with the change file written; STALE per planned one); decisions decided but not applied;
   `Commit:`; and the next command.

## Constraints

- Edit only `docs/architecture.md`, `docs/packages/*/contract.md`, the `Status:` and
  `Resolved by:` lines of ledger entries (`docs/packages/$pkg/deviations/*.md`, or
  the older `docs/deviations/$pkg/*.md` and `docs/deviations.md`), the `Status:` line of a change file
  (`docs/packages/$pkg/changes/*.md`, or a pre-2.2 `docs/changes/*.md`), a new change file for
  a shipped consumer under that consumer's `docs/packages/<pkg>/changes/`, and the archive
  copies under `docs/history/`.
- Never edit `interface.md` — its **Consumers (computed)** is the implementer's, rewritten when
  the `surface` section is next built — nor a design, a review, or code.
- Never write a claim you did not verify against the code. An unverifiable item stays open and
  goes in the return with why.
