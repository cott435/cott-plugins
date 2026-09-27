---
name: map-repo
description: Adopt an existing repository into the planning system in one run - list its packages (on a monolith, propose the split and stop for your answer), write one package contract per package from the code in parallel, then the repo contract from those contracts and the import graph. Every existing contract line is a claim checked against the code; defects go to the backlog. Run once on a repo with code and no docs/, and again when the contracts have drifted.
argument-hint: "[scope - a directory or a note on what to focus on; optional]"
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---

Map this existing repository into its contracts — **map-repo**, all three phases.

Scope hint (may be empty — map the whole repo if so):

$ARGUMENTS

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `architect` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not plan in the main thread.

Run this on a repo that has code and no `docs/`, and again when the contracts have drifted far
enough from the code to mislead. One run writes every package contract and the repo contract;
no per-package run follows. Each adopted section then walks `/dev-team:run-package`'s loop from
a `document`-mode design: a green intent suite, a README, a review.

Your **map-repo** section is the procedure; the steps below are its order. Everything you write
describes the code as it is. Nothing here proposes a change: where the code is wrong, the
contract still says what it does and the defect goes to `docs/followups.md`.

## Steps

1. **Run gate.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate`.
   FAIL → return `Result: blocked` with its lines, and write nothing.

2. **Phase 1 — the packages.** `Explore` over the repo, or over the scope above: packages,
   entry points, top-level exports, the imports between packages, the toolchain. Verify what it
   cites. Enumerate the project skills per your **Project skills**. Then the monolith test from
   your **map-repo** section:
   - **Packages found** — `packages/*/pyproject.toml`, an existing `docs/architecture.md`'s
     Packages table, or split entries tagged `/dev-team:map-repo (interview)` in
     `docs/decisions.md` (decided, or still open with an assumption). Proceed.
   - **A monolith with no split in the ledger** — stub one `D<n>` per proposed package, each
     naming the directories it would own, and **stop** with the interview message, continue
     command `/dev-team:map-repo` plus the scope as typed. Commit `docs/decisions.md` only, per
     step 6, before you return. No contract, no fan-out.

   Build the import graph: `uv run lint-imports` when `[tool.importlinter]` is configured, else
   the read-only grep of `from` and `import` lines, kept to the lines naming another package.

3. **Phase 2 — one package architect per package.** Every call in one message, each
   `subagent_type: "dev-team:architect"` and `run_in_background: false`, each prompt the
   spawn block of your **map-repo** section with this package's `Package:`, `Path:`,
   `Existing contract:` (the path when `docs/packages/<pkg>/contract.md` exists, else `none`),
   `Sibling packages:`, `Import graph:` lines, `Write to:`, and `Run: map-repo $ARGUMENTS`.
   Batches of 20 above 20 packages. Each commits its own contract and backlog lines and
   returns ten lines.

4. **Phase 3 — the repo contract.** From the contracts and the returns, write
   `docs/architecture.md` per your **map-repo** section: Packages dependency-ordered, `covers`
   `—` without a brief, the Dependency graph from the import graph (a cycle recorded as the
   order that should hold, one line saying it does not yet hold, and a backlog line), the
   shapes crossing each edge, the conventions and toolchain actually in use. On a re-map,
   archive it first and check every existing line as a claim.

5. **Decisions.** One `D<n>` stub per question a package architect returned and per
   cross-package gap you found, each with its recommendation and assumption, tagged
   `/dev-team:map-repo (interview)`, and its number under the right contract's **Open
   decisions**. None of these stops the run.

6. **Commit** per your **Commit** section — scope `plan repo`, trailer `Dev-Team-Run: map-repo
   $ARGUMENTS` — last, after every package commit. Then **return**: `Result: done`; `packages:
   <name> (<path>), …`; the contract paths written; the corrections, grouped as *stale doc
   corrected* and *code looks wrong, filed*; the defects filed; the `D<n>` stubs; collisions
   and project skills left out; `Commit:`; and the next command, `/dev-team:run-package <pkg>`
   for the lowest package in the Dependency graph.

## Constraints

- Contracts, the ledger and the backlog only. No design, no code, no config, no tests, no probe.
- Never classify an item per **Edits** here, and never write a change file: a mapped contract
  describes existing code, which is what a canonical contract is.
- Every existing contract line is a claim. A re-map that silently rewrites half a contract is
  indistinguishable from one that hallucinated it, so every correction is in the return.
- Be honest about what you could not determine. A gap marked as a gap is worth more than a
  guessed shape, because the next run plans against the guess.
