---
name: plan-repo
description: Plan a repository at the package level — new, extending, or fixing. Produces docs/architecture.md, the repo contract - packages, dependency graph, the shapes crossing each boundary, shared conventions, toolchain - plus decision stubs. On an existing contract each change item is classified EDIT, EDIT+STALE, CHANGE (a change file) or DECIDE (stop), and the contract is archived before any edit. Does not plan sections; run /dev-team:plan-package for each package afterwards.
argument-hint: "[brief | addition | --fix \"<notes>\"]"
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---

Plan this repository at **repo scope** from the brief below:

$ARGUMENTS

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `architect` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not plan in the main thread.

## The argument

- **Empty, or `docs/brief.md`** — the brief is `docs/brief.md` as it stands. This is the normal
  form after `/dev-team:shape-brief`, and the continue command after a stop. If the file does
  not exist, return `Result: blocked` naming `/dev-team:shape-brief` (or an inline brief).
- **`--fix "<notes>"`** — the user is correcting the brief: the contract came out wrong because
  the brief was wrong, incomplete, or misread. The notes are the correction.
- **Anything else** — inline text, or a path to a file whose contents are the brief (or an
  addition to it).

If `docs/brief.md` has a line `Status: draft`, return `Result: blocked`: the brief is
mid-discussion — finish it with `/dev-team:shape-brief`, or change the line to `Status: ready`.

## Modes — decided by what exists and how the brief changed

`docs/history/brief-contracted.md` is a verbatim copy of the brief `docs/architecture.md` was
last written from. Compare it with `docs/brief.md` using `diff` (read-only).

| Mode | When |
|---|---|
| **New** | No `docs/architecture.md`. |
| **Extend** | The contract exists, and either the argument is inline text or a path other than `docs/brief.md`, or the argument is empty and the only difference from the snapshot is new sections at the end headed `## Addition — <date>`. |
| **Revise** | The contract exists, and either the argument is `--fix`, or the argument is empty and existing brief text was changed or removed, or a new section is headed `## Revision — <date>`. With no snapshot at all (a contract older than the snapshot, or one `/dev-team:map-repo` wrote), an empty argument means Revise. |
| **Unchanged** | The contract exists, the argument is empty, and the brief equals the snapshot. Return `Result: done` and one line — the contract already reflects the brief; change it with `/dev-team:shape-brief`, pass what to add, or use `--fix` — and stop. |

## Steps

1. **Persist the brief** — before anything that could stop, because `docs/brief.md` is the only
   statement of intent and what a continue run reads.
   - **New** — write the argument's contents verbatim to `docs/brief.md` (skip when the argument
     is empty or is `docs/brief.md`).
   - **Extend** with an argument — append it verbatim under `## Addition — <today>`.
   - **Revise** with `--fix` — copy `docs/brief.md` to `docs/history/<today>-brief.md`
     (suffix `-2`, `-3` if taken), then append the notes verbatim under
     `## Revision — <today>`, whose first line is: *Where this section conflicts with anything
     above it, this section wins.* Never reword the user's earlier text — reshaping a brief is
     `/dev-team:shape-brief`'s job, done with the user.
   - Otherwise the brief is already in place.

2. **Run gate.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate`.
   FAIL → return `Result: blocked` with its lines, and write nothing further. The brief persisted
   in step 1 is exempt from the gate's clean-tree check, so a re-run after fixing the tree
   finds it in place.

3. **Survey.** Enumerate the project skills per your **Project skills**. Read `CLAUDE.md` and any
   existing repo structure. Invoke `workspace-scaffold` so the Toolchain section copies real
   shapes rather than remembered ones.
   - **Extend and Revise** — read the current contract, every `docs/packages/*/contract.md` and
     `interface.md`, and run `status.py` for each package, to know each one's state (your
     **The document map**). The survey travels in this run; nothing persists it.
   - **Revise** — also read the diff against the snapshot. The old contract is a record of what
     was misread, not an authority: a part of it survives only because the revised brief still
     supports it. Then sort every `docs/decisions.md` entry that is not `superseded`:
     - *premise gone* — the revised brief removes what it asks about, or the package it is
       scoped to no longer exists. Only `open` or `deferred` entries can be sorted here.
     - *conflict* — the entry is `decided` and the revised brief says otherwise. You never
       override a decision; it becomes a question in step 5.
     - *still holds* — everything else, applied as before.

4. **Probe datasets.** When the brief names a dataset the repo is being built around — a file,
   a table, a corpus, a hub id — probe it now, before the contract, per your **Probing**: one
   researcher per dataset, all in one message, `Purpose:` the brief capability that names it,
   verbatim, `Access:` the location the brief gives, else `discover`. A brief naming no dataset
   skips this step. An access failure is a **stop** with the access stop message. Otherwise
   anything in **Supported tasks**, **Target** or **Splitting** that contradicts what the brief
   asks for is a question for step 5, never an assumption.

5. **Interview rule.** Package boundaries the brief does not settle, dependency direction where
   two orders are defensible, a shared convention with no implied default (timezone, ID type,
   error envelope, config prefix scheme), a project skill with no package, an item under the
   brief's **Open questions** that changes the decomposition, anything step 4 found that the
   brief contradicts, every DECIDE item, and in Revise each *conflict* ("D3 decided X; the
   revised brief says Y — which holds?"). In Revise, first retire every *premise gone* entry
   (step 7's rule), so the ledger check does not count it as asked. Check the ledger; stub
   anything unasked tagged `Raised by: /dev-team:plan-repo (interview)` and **stop** with the
   stop message — its continue command is `/dev-team:plan-repo` with no argument. Otherwise
   proceed.

6. **The contract.** Invoke `planning-templates`.

   How to read a brief written by `/dev-team:shape-brief`: **Scope — now** is what gets
   packages. **Scope — later** is not planned; use it only to avoid a boundary that would block
   it. **Out of scope** feeds Non-goals. Stated **Constraints** are settled; one recorded as
   *no preference* is yours to decide, and a stub when a wrong guess is expensive. Give every
   package its `covers` cell, by the brief's capability names. A *now* capability no package
   covers is either a missing package or an interview question — never silently dropped.

   - **New — WRITE.** Read `references/repo-contract.md` and write `docs/architecture.md` to it.
     Decisions never go inside it: its Open decisions heading lists `D<n>` numbers only.
   - **Extend and Revise — the change list.** Each item is one thing the addition or the
     revised brief asks the contract to change: a package added, split, merged or dropped; a
     boundary shape; a convention; a dependency edge. Classify and apply each per your **Edits
     — the change list**, archiving `docs/architecture.md` before the first edit. The Packages
     table's `covers` cell is bookkeeping, not a shape: fill or correct it on any row as an
     EDIT whatever the package's state.

   Then copy `docs/brief.md` verbatim to `docs/history/brief-contracted.md` — the brief this
   contract now reflects. On a run whose only outcomes are DECIDE, skip the copy: the contract
   does not reflect the brief yet.

7. **Decisions.** Append a `D<n>` stub for every open question that survived — the conventions
   you had to pick without a basis, boundary shapes you are unsure of. Each gets a
   recommendation and an assumption, `Scope: repo` unless it belongs to one package.

   Retiring in Revise: give each *premise gone* entry `Status: superseded` and a
   `Superseded by:` line — the `D<n>` of the new stub when the question lives on in another
   form, otherwise `brief revision <today>`.

8. **Commit** per your **Commit** section — scope `plan repo`, trailer `Dev-Team-Run: plan-repo
   $ARGUMENTS` — then **return** your standard message. In Extend and Revise, add:
   - **Stale package plans** — every planned package whose row, boundaries or conventions an
     EDIT+STALE changed, or one of whose `covers` capabilities was added, removed, or had its
     brief row edited — one line each saying what changed. A package the new contract dropped
     is *orphaned*: its `docs/packages/<pkg>/` is no longer referenced, and removing it is the
     user's call.
   - **Superseded** — the `D<n>` numbers retired, on one line.

   End with the next command: `/dev-team:plan-package <pkg>`, naming the first package in
   dependency order that is stale or has no `docs/packages/<pkg>/contract.md`.

## Constraints

- The repo contract only. No package contract, no design, no code, no config, no tests.
- Researchers in probe mode for the datasets of step 4 are the one spawn. Do not probe an api
  here: without a section's purpose there is no call worth making.
- Shapes, not signatures, at every boundary. A signature belongs to the providing package's
  contract, under **Section interfaces**.
- Never delete a document. Retire it by reference: a history copy, the orphan list, a
  superseded entry.
