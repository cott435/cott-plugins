---
name: plan-package
description: Write or edit one package's contract under the repo contract - the Sections table (ending with the surface row), section interfaces, pipelines, public surface intent, consumes. On an existing contract each change item is classified EDIT, EDIT+STALE, CHANGE (a change file) or DECIDE (stop). Run after plan-repo, when the repo contract changed, when a spec-change at contract level is open, or to request a change; run-package runs it at the PLAN step.
argument-hint: "<pkg> [change request]"
arguments: [pkg, request]
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---

Plan package **$pkg** at **package scope**.

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `architect` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not plan in the main thread.

The command was typed with these arguments: **`$ARGUMENTS`**. The first word is the package;
anything after it is a change request, one or more items. If the package name above reached
you unsubstituted, as a literal dollar-sign placeholder, take the first word of the arguments
line as the package name directly.

**Spawned by run-package.** A prompt that carries `Package: <pkg>` and `Run: run-package <pkg>`
lines instead of a substituted argument comes from `/dev-team:run-package` at the PLAN step: use
that package, skip step 1 (the driver ran the run gate), and use `Dev-Team-Run: run-package
<pkg>` as the trailer. The Guard block does not fire: you have neither earlier turns nor
`AskUserQuestion`.

## Preconditions

`docs/architecture.md` must exist and its Packages table must have a row for `$pkg`. If not,
return `Result: blocked` naming `/dev-team:plan-repo` — a package planned without the repo
contract invents its own shapes and conventions, and the next package invents them differently.

## Steps

1. **Run gate.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate $pkg`.
   FAIL → return `Result: blocked` with its lines, and write nothing.

2. **Survey.** Read, and nothing beyond it:
   - `docs/architecture.md` — the `$pkg` row, its `depends on`, the Boundaries subsections for
     every edge into and out of it, Shared conventions, Toolchain.
   - `docs/brief.md` — only the rows of its **Scope — now** and **Scope — later** tables (and
     of any `Addition` section) whose capability is in `$pkg`'s `covers` cell, plus any
     `Revision` section naming one of them. Skip when `covers` is `—` or there is no brief.
   - For each package in `depends on`: `docs/packages/<dep>/interface.md` when that package is
     shipped (`status.py <dep>` reads `shipped: yes`); else its `contract.md` if it exists,
     else the repo contract's Boundaries — and every name consumed from it is **provisional**.
   - `docs/packages/$pkg/contract.md` if it exists, and the package's code directory if any.
   - `docs/packages/$pkg/deviations/*.md` (and the older `docs/deviations/$pkg/*.md` and
     `docs/deviations.md`): open `spec-change:contract` entries.
   - `docs/packages/$pkg/changes/*.md` with `Status: open`, and any pre-2.2 `docs/changes/*.md`
     naming a `$pkg/<section>`.
   - The project skills, per your **Project skills**; the repo contract's `candidate skills`
     column for `$pkg` is the starting point.

3. **Interview rule.** Section boundaries the repo contract does not settle, a candidate skill
   with no section, a section with no skill, a pipeline whose ordering is ambiguous, a covered
   *now* capability no section builds, a provisional upstream name you need settled, a section
   that plainly needs an external `source` whose vendor or token you cannot pin down, and every
   DECIDE item. Check the ledger; stub anything unasked tagged
   `Raised by: /dev-team:plan-package $pkg (interview)` and **stop** with the stop message,
   whose continue command is `/dev-team:plan-package $pkg`. Otherwise proceed.

4. **The contract.**
   - **No contract — WRITE.** Invoke `planning-templates`, read `references/package-contract.md`,
     and write `docs/packages/$pkg/contract.md` to it. **Purpose** carries the covered brief
     rows, Notes verbatim — designers read the contract, never the brief. The Sections table's
     `source` column names each external source as `<kind>:<token>` (`api:polygon`,
     `dataset:trades-2024`, several comma-separated, or `—`): the driver's PROBE step iterates
     over it, so a source missing from it is never probed. **Public surface (intent)** names a
     consumer — a downstream package or a CLI command — for every entry, and nothing without
     one. The table's last row is `surface`: path the package top level, `depends on` every
     other section, `builds with` and `source` `—`.
   - **A contract exists — the change list.** The items are the change request in the
     arguments, each open `spec-change:contract` entry naming the package, and whatever the
     repo contract's diff since its last archive copy under `docs/history/` changes for `$pkg`'s
     row, boundaries or conventions. With none of the three, return `Result: done` saying the
     contract is current, and commit nothing. Otherwise classify and apply each item per your
     **Edits — the change list**: EDIT, EDIT+STALE, CHANGE, DECIDE; archive before the first
     edit. A `spec-change:contract` entry answered by an EDIT, EDIT+STALE or CHANGE outcome is
     closed per your **Edits**; one answered by DECIDE stays `open`.

5. **Decisions.** Append a `D<n>` stub for every open question that survived — a convention you
   picked without a basis, a boundary you are unsure of — `Scope:` the sections it binds, or
   `$pkg` when it is package-wide, and list each number under the contract's **Open
   decisions**.

6. **Commit** per your **Commit** section — scope `plan $pkg`, trailer `Dev-Team-Run:
   plan-package $ARGUMENTS` (or `run-package $pkg` from the driver) — then **return** your
   standard message: the paths written or one row per change item, stale packages, provisional
   dependencies, `D<n>` stubs, `Commit:`, and the next command, `/dev-team:run-package $pkg`.

## Constraints

- Contracts only. No design, no code, no config, no tests, no probe: the driver's PROBE step
  probes each section's sources, and its designers design from this contract.
- Never edit another package's documents. A change a planned sibling needs is a stale package in
  your return; a change a shipped one needs is a CHANGE item.
- An existing codebase is adopted by `/dev-team:map-repo`, not here.
