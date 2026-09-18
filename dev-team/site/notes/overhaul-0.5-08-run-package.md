# 08 — `/dev-team:run-package`

Phase 8. A driver that runs the per-section loop and the package close-out without the
user typing each command, and stops on exactly the gates the manual loop already has.
It removes the human *between* steps, never a verification: every agent run it spawns is
the same run the manual command would fork, reading the same skill file.

## Shape

`skills/run-package/SKILL.md`, **no** `context: fork`. It runs in your conversation and
spawns agents itself with the Agent tool, so the agents are layer 1 and the architect's
designers stay at layer 2 — inside the default depth of three. `disable-model-invocation:
true`, like every workflow skill.

```yaml
---
name: run-package
description: Drive one package from a reviewed plan to a shipped surface without typing each step - per section test-section, implement-section, test-section, review-section, in dependency order; then finalize-package, review-package, sync-design. Stops on every gate the manual commands stop on. Use after review-plan approves and decisions are answered; on a spine-only plan it builds the spine, completes the plan, reviews it, and stops for you.
argument-hint: "<pkg>"
disable-model-invocation: true
---
```

## Reusing the skills without copying them

`${CLAUDE_PLUGIN_ROOT}` is substituted in a SKILL.md body (documented; `finalize-package`
relies on it today). The driver therefore hands each agent a task prompt that names the
skill file to execute:

```
Section: <pkg>/<section>
Plan:
Procedure: read `<absolute plugin root>/skills/<skill>/SKILL.md` and carry it out exactly
as if you had been invoked as `/dev-team:<skill> <pkg>/<section>`, taking `$section` and
`$plan` from the two lines above. You were spawned by /dev-team:run-package.
```

The `<absolute plugin root>` is the substituted value of `${CLAUDE_PLUGIN_ROOT}` at the
time the driver's body is loaded. Each forked skill gains one paragraph, **Invoked by
run-package**: *if your task prompt carries `Section:`/`Plan:` (or `Package:`) lines
instead of substituted arguments, use those; the Guard block above does not fire, because
you have neither earlier turns nor `AskUserQuestion`.* Nothing else in any skill changes,
so there is exactly one copy of every procedure.

The `subagent_type` string for a plugin agent is undocumented. This session's own tool
list renders this plugin's agents as `<plugin>:<agent>` (`project-workers:implementer`),
so the driver uses `dev-team:<agent>` and phase 0's eval (note 09 §A) confirms it before
phase 8 starts. If the first Agent call fails with an unknown agent type, the driver stops
with the `/reload-plugins` message the Guard blocks use.

## Agent return sentinel

Every agent the driver spawns starts its return message with one line the driver branches
on. Added to the return-message section of `architect.md`, `implementer.md`, `tester.md`,
`reviewer.md` in this phase:

```
Result: done | blocked | stopped
```

`blocked` is a blocking rule; `stopped` is the architect's decisions or access stop. The
reviewer's second line is its existing `Verdict:`. The driver reads only those lines and
`status.py`; it never parses the rest of a return.

## The driver, step by step

Every `status.py` call is `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py`.

1. **Gate.** `status.py <pkg> --run-gate`. On FAIL print its lines and stop. On PASS read
   `mode: spine` or `mode: full`.
2. **Order.** Parse **Dependency order** from `docs/packages/<pkg>/integration.md`. In
   `spine` mode the order is the one section named under **Spine**.
3. **Per section**, in order, skipping any whose `status.py` row is reviewed (`✓`) with a
   verdict of `approve` or `approve with fixes`, zero open review follow-ups, and an intent
   column with no failures:
   1. If `tests/intent/<section>/` is absent → spawn `dev-team:tester` (test-section; it
      chooses intent mode).
   2. Spawn `dev-team:implementer` (implement-section). Count this as implementer run 1.
   3. Spawn `dev-team:tester` (test-section; it chooses reconcile mode).
   4. If the tester's return lists follow-ups filed → spawn the implementer again
      (run 2) → tester again.
   5. Spawn `dev-team:reviewer` (review-section).
   6. If `Verdict: request changes` and implementer runs < 3 → implementer → tester →
      reviewer, once more. If still `request changes` → **stop** (below).
   7. Any `Result: blocked` or `Result: stopped` at any step → **stop**.
   8. After each spawn, run `status.py <pkg>` and print the section's row — that, not the
      return message, is the progress report.
4. **Spine mode, after the spine section:** spawn `dev-team:architect` with
   `Package: <pkg>` and the plan-package procedure (a completion run); then
   `dev-team:reviewer` with the review-plan procedure; then **stop** with: *plan complete
   and reviewed: <verdict>; answer any decisions in `docs/decisions.md`, then re-run
   `/dev-team:run-package <pkg>`.* A `Result: stopped` from the architect (decisions or
   access) stops here with its message instead.
5. **Full mode, after the last section:** spawn `dev-team:implementer` with
   `Package: <pkg>` and the finalize-package procedure; then `dev-team:reviewer` with the
   review-package procedure; if `request changes`, once more each; then `dev-team:architect`
   with the sync-design procedure.
6. **Summary**, always, as the driver's last message:

   ```
   run-package <pkg>: <done | stopped at <step>>
   sections: <built>/<total> built, <reviewed>/<total> reviewed (approve or approve with fixes)
   implementer runs: <n>; tester runs: <n>; reviewer runs: <n>
   commits: <first sha>..<last sha> (<count>)
   stopped because: <the agent's first two lines, or the status.py FAIL lines>   (only when stopped)
   next: <exact command>
   ```

   `next` is the command the manual loop would type from this state: the failing
   section's `implement-section` after a review stop; `plan-package <pkg>` after a plan
   stop; `review-plan <pkg>` after a completion run; `plan-package <next pkg>` after
   sync-design.

The driver never edits a file, never runs git itself, and never answers a decision. When
an agent returns `stopped` for decisions, the stubs are already in the ledger; the driver
shows them and stops.

## `status.py --run-gate <pkg>`

Prints `run gate: PASS (mode: spine|full) | FAIL` and reasons; exit 1 on FAIL:

- `git branch --show-current` is not `main`/`master`; the directory is a repository.
- `git status --porcelain` is empty except `docs/decisions.md`, `docs/brief.md`,
  `docs/constraints.md`.
- `docs/packages/<pkg>/contract.md` and `integration.md` exist.
- If `integration.md` **Spine** reads `Status: spine only` → `mode: spine`, PASS.
- Else every `--plan-gate` condition (note 05) → `mode: full`, PASS.

## Three-file rule, contracts, site, README

- `reserved-skill-names`: `run-package` (workflow). README tree; §Which skill to run:
  *plan reviewed, decisions answered → /dev-team:run-package <pkg>*; a new README section
  **Running a package** with the step list above in prose and the stop conditions.
  `site.yml`: `run-package` after `review-plan`.
- `contracts.yml`:
  - `forbid`: `pattern: 'subagent_type: "(?!dev-team:)'` in `skills/run-package/SKILL.md`
    — every spawn is namespaced. (Adjust to the phase-0 eval's finding if the bare name is
    what resolves; the eval log is the record.)
  - `headings`: the driver cites `Dependency order` and `Spine` under the integration
    template's owner entry (added in note 05); add `skills/run-package/SKILL.md` as a
    reader with `cites: ['Dependency order', 'Spine']`.
- `README.md` §Gotchas: *`run-package` is a loop in your conversation; each agent return
  is ≤ 40 lines and the driver prints `status.py` between them, so a five-section package
  costs the driver roughly 30 short turns of context. Run it with `/clear` behind you.*

## Steps

1. Return sentinel in four agents.
2. **Invoked by run-package** paragraph in every forked skill (12 files).
3. `status.py --run-gate`.
4. Write `skills/run-package/SKILL.md` — the driver in prose that a model follows, with
   the exact Agent-tool prompt block and the summary block quoted verbatim.
5. Three-file rule; README section; `contracts.yml`; `check-contracts`; `build-site`.
6. Evals (note 09 §J): behavioral, on the fixture: (i) full mode on a reviewed two-section
   plan runs tester/implementer/tester/reviewer per section in order and finalize / review /
   sync-design after, ending with `done` and a sync-design commit at HEAD; (ii) spine mode
   builds one section, completes and reviews the plan, and stops with the decisions
   message; (iii) a seeded CRITICAL the implementer cannot fix (a review finding
   demanding a contract change) stops at implementer run 3 with the right `next`. Log all
   three.
7. Commit: `dev-team 0.5 (phase 8): run-package driver`.

## Done when

The three eval runs pass and are logged; no skill body is duplicated in the driver (grep
the driver for any sentence that also appears in `implement-section/SKILL.md`: zero);
`check-contracts` passes.
