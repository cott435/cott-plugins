---
name: plan-repo
description: Plan a repository at the package level — new, extending, or revising. Produces docs/architecture.md, the repo contract - packages, dependency graph, the shapes crossing each boundary, shared conventions, toolchain - plus decision stubs. Rewrites the contract when the brief was corrected. Does not plan sections; run /dev-team:plan-package for each package afterwards.
argument-hint: "[repo brief, path to one, or --revise \"<what was wrong>\"]"
context: fork
agent: architect
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
  form after `/dev-team:shape-brief`, and the continue command after an interview stop. If the
  file does not exist, return a blocker naming `/dev-team:shape-brief` (or an inline brief).
- **`--revise "<notes>"`** — the user is correcting the brief: the contract came out wrong
  because the brief was wrong, incomplete, or misread. The notes are the correction.
- **Anything else** — inline text, or a path to a file whose contents are the brief (or an
  addition to it).

If `docs/brief.md` has a line `Status: draft`, return a blocker: the brief is mid-discussion —
finish it with `/dev-team:shape-brief`, or change the line to `Status: ready`.

## Modes — decided by what exists and how the brief changed

`docs/history/brief-contracted.md` is a verbatim copy of the brief `docs/architecture.md` was
last written from. Compare it with `docs/brief.md` using `diff` (read-only).

| Mode | When |
|---|---|
| **New** | No `docs/architecture.md`. |
| **Extend** | The contract exists, and either the argument is inline text or a path other than `docs/brief.md`, or the argument is empty and the only difference from the snapshot is new sections at the end headed `## Addition — <date>`. |
| **Revise** | The contract exists, and either the argument is `--revise`, or the argument is empty and existing brief text was changed or removed, or a new section is headed `## Revision — <date>`. With no snapshot at all (a contract older than the snapshot, or one `/dev-team:map-project` wrote), an empty argument means Revise. |
| **Unchanged** | The contract exists, the argument is empty, and the brief equals the snapshot. Return one line — the contract already reflects the brief; change it with `/dev-team:shape-brief`, pass what to add, or use `--revise` — and stop. |

A package is **bound** when `docs/packages/<pkg>/interface.md` exists (shipped) or its code
directory already holds source (built, or mapped from existing code). In every mode but New,
a part of the contract a bound package provides or consumes is never edited here: the change
it needs becomes a stub scoped `repo` recommending `/dev-team:plan-change`, and that part stays
as it is. The Packages table's `covers` cell is bookkeeping, not a shape: fill or correct it on
any row.

## Steps

1. **Persist the brief** — before anything that could stop, because `docs/brief.md` is the only
   statement of intent and what a continue run reads.
   - **New** — write the argument's contents verbatim to `docs/brief.md` (skip when the argument
     is empty or is `docs/brief.md`).
   - **Extend** with an argument — append it verbatim under `## Addition — <today>`.
   - **Revise** with `--revise` — copy `docs/brief.md` to `docs/history/<today>-brief.md`
     (suffix `-2`, `-3` if taken), then append the notes verbatim under
     `## Revision — <today>`, whose first line is: *Where this section conflicts with anything
     above it, this section wins.* Never reword the user's earlier text — reshaping a brief is
     `/dev-team:shape-brief`'s job, done with the user.
   - Otherwise the brief is already in place.

2. **Survey.** Enumerate the project skills per your instructions. Read `CLAUDE.md` and any
   existing repo structure. Invoke `workspace-scaffold` so the Toolchain section copies real
   shapes rather than remembered ones.
   - **Extend and Revise** — read the current contract, every `docs/packages/*/interface.md` and
     `contract.md`, and check each code directory the Packages table names, to know which
     packages are bound. If any package document or package code exists, persist the survey to
     `docs/assessment.md`; if nothing exists beyond the contract, there is nothing to persist.
   - **Revise** — also read the diff against the snapshot. The old contract is a record of what
     was misread, not an authority: a part of it survives only because the revised brief still
     supports it. Then sort every `docs/decisions.md` entry that is not `superseded`:
     - *premise gone* — the revised brief removes what it asks about, or the package it is
       scoped to no longer exists. Only `open` or `deferred` entries can be sorted here.
     - *conflict* — the entry is `decided` and the revised brief says otherwise. You never
       override a decision; it becomes a question in step 3.
     - *still holds* — everything else, applied as before.

3. **Interview rule.** Decide what you would ask — package boundaries the brief does not
   settle, dependency direction where two orders are defensible, a shared convention with no
   implied default (timezone, ID type, error envelope, config prefix scheme), a project skill
   with no package, an item under the brief's **Open questions** that changes the
   decomposition, and in Revise each *conflict* ("D3 decided X; the revised brief says Y —
   which holds?"). In Revise, first retire every *premise gone* entry (step 5's rule), so the
   ledger check below does not count it as asked. Check the ledger; if anything is unasked,
   stub it tagged `Raised by: /dev-team:plan-repo (interview)` and **stop** with the stop
   message — its continue command is `/dev-team:plan-repo` with no argument. Otherwise proceed.

4. **Repo contract.** Invoke `planning-templates` and read `references/repo-contract.md`.
   Only now — a contract written before the interview rule proceeds is a contract written on
   guesses, and decisions never go inside it (its Open decisions heading lists `D<n>` numbers;
   the entries live in `docs/decisions.md`).

   How to read a brief written by `/dev-team:shape-brief`: **Scope — now** is what gets
   packages. **Scope — later** is not planned; use it only to avoid a boundary that would block
   it. **Out of scope** feeds Non-goals. Stated **Constraints** are settled; one recorded as
   *no preference* is yours to decide, and a stub when a wrong guess is expensive. A brief in
   any other shape is read for the same things.

   Give every package its `covers` cell, by the brief's capability names. A *now* capability
   no package covers is either a missing package or an interview question — never silently
   dropped.

   - **New** — write `docs/architecture.md`.
   - **Extend** — edit only what the addition needs, and nothing bound.
   - **Revise** — copy the current contract to `docs/history/<today>-architecture.md`, then
     rewrite `docs/architecture.md` from the revised brief, keeping every bound part verbatim.
     A package whose responsibility still fits keeps its name.

   Then copy `docs/brief.md` verbatim to `docs/history/brief-contracted.md` — the brief this
   contract now reflects.

5. **Record decisions.** Append a `D<n>` stub for every open question that survived — the
   conventions you had to pick without a basis, boundary shapes you are unsure of. Each gets a
   recommendation and an assumption, `Scope: repo` unless it belongs to one package.

   Retiring in Revise: give each *premise gone* entry `Status: superseded` and a
   `Superseded by:` line — the `D<n>` of the new stub when the question lives on in another
   form, otherwise `brief revision <today>`.

6. **Return** your standard summary. In Revise, add:
   - **Stale package plans** — every package with a `contract.md` whose row, boundaries or
     conventions changed, or one of whose `covers` capabilities was added, removed, or had
     its brief row edited — one line each saying what changed; each needs
     `/dev-team:plan-package <pkg>` again. A package the new contract dropped is *orphaned*:
     its `docs/packages/<pkg>/` is no longer referenced, and removing it is the user's call.
   - **Held by bound packages** — what the revised brief wanted but this run could not change,
     with the `D<n>` for each.
   - **Superseded** — the `D<n>` numbers retired, on one line.

   End with the next command: `/dev-team:plan-package <pkg>`, naming the first package in
   dependency order that is stale or has no `docs/packages/<pkg>/contract.md`.

## Constraints

- Planning documents only. No code, no config, no tests.
- Do not spawn designers and do not plan sections. Packages are planned one at a time by
  `/dev-team:plan-package`, each against the shipped surface of the packages below it.
- Shapes, not signatures, at every boundary. A signature belongs to the providing package's
  `surface.md`, which does not exist yet.
- Never delete a document. Retire it by reference: a history copy, the orphan list, a
  superseded entry.
