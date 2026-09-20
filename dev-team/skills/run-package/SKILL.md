---
name: run-package
description: Drive one package from a reviewed plan to a shipped surface without typing each step - per section test-section, implement-section, test-section, review-section, in dependency order; then finalize-package, review-package, sync-design. Stops on every gate the manual commands stop on. Use after review-plan approves and decisions are answered; on a spine-only plan it builds the spine, completes the plan, reviews it, and stops for you.
argument-hint: "<pkg>"
arguments: [pkg]
disable-model-invocation: true
---

Run package **$pkg**.

If the package name above reached you unsubstituted, as a literal dollar-sign placeholder,
take the first word of `$ARGUMENTS` as the package name.

This skill runs in your conversation, not in a fork. You are the driver: you spawn every agent
yourself with the Agent tool, so each one is layer 1 and the architect's designers stay at
layer 2. You remove the human *between* steps and never a verification — every agent you spawn
does the run the manual command would fork, reading the same skill file.

## What you never do

- Edit a file, answer a decision, or write to `docs/`.
- Run a git command that writes. The only git you run is `git rev-parse --short HEAD`, at the
  start and at the end, and `git rev-list --count <start>..HEAD` for the summary.
- Read an agent's return past its first two lines. Every agent you spawn begins its return
  with `Result: done | blocked | stopped`; the reviewer's second line is `Verdict: <verdict>`.
  Those lines and `status.py` are all you branch on. Do not open the files the agents wrote
  to check their work — the reviewer does that.
- Spawn anything in the background. Every Agent call is `run_in_background: false`; the next
  step needs the last one's commit.

## Spawning an agent

Every spawn is one Agent call with `subagent_type: "dev-team:<agent>"` — `dev-team:tester`,
`dev-team:implementer`, `dev-team:reviewer` or `dev-team:architect`, never the bare name —
and a prompt that is exactly one of these two blocks, with `<skill>`, the section and the
package filled in:

```
Section: <pkg>/<section>
Plan:
Procedure: open `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/SKILL.md` with the Read tool and
carry it out exactly, as the /dev-team:<skill> run for <pkg>/<section>, taking the section
and the plan slug from the two lines above. Do not call the Skill tool for it: the user
typed /dev-team:run-package, and that command runs this step through you.
```

```
Package: <pkg>
Procedure: open `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/SKILL.md` with the Read tool and
carry it out exactly, as the /dev-team:<skill> run for <pkg>, taking the package from the
line above. Do not call the Skill tool for it: the user typed /dev-team:run-package, and
that command runs this step through you.
```

| Step | `<skill>` | Agent | Block |
|---|---|---|---|
| intent tests, reconcile | `test-section` | `dev-team:tester` | Section |
| build a section | `implement-section` | `dev-team:implementer` | Section |
| review a section | `review-section` | `dev-team:reviewer` | Section |
| complete a spine-only plan | `plan-package` | `dev-team:architect` | Package |
| review the plan | `review-plan` | `dev-team:reviewer` | Package |
| build the surface | `finalize-package` | `dev-team:implementer` | Package |
| review the package | `review-package` | `dev-team:reviewer` | Package |
| fold deviations into designs | `sync-design` | `dev-team:architect` | Package |

If the first Agent call fails because the agent type is unknown, stop: the dev-team agents are
not registered. Tell the user to run `/reload-plugins` (or restart Claude Code), verify with
`/agents`, and re-run `/dev-team:run-package $pkg`.

Every `status.py` below is
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py`, run from the repo root. It
exits 1 on a failing gate; that is the answer, not an error.

## Steps

1. **Gate.** Record `git rev-parse --short HEAD` as the start commit. Run
   `status.py $pkg --run-gate`. On `FAIL`, print its lines and go to step 6. On `PASS`, read
   the mode: `spine` or `full`.

2. **Order.** Read the **Dependency order** item of `docs/packages/$pkg/integration.md` — the
   only part of that file you read. In `spine` mode, the order is the single section its
   **Spine** item names.

3. **Each section, in order.** Keep a count of implementer runs per section. Skip a section
   whose `status.py $pkg` row is reviewed (`✓`) with verdict `approve` or `approve with
   fixes`, shows `(0 review, 0 intent)` in its open follow-ups column — other follow-ups do
   not count — and has an intent column that is `—` or `<n>/<n>`. For every other section:
   1. If the section's intent column reads `—` — no `tests/intent/<section>/` yet — spawn
      the tester (`test-section`; it runs intent mode). Check this for every section, before
      its first implementer spawn; never go straight to the build.
   2. If the row shows a non-zero `intent` count — findings in `tests/intent/<section>/`,
      which only the tester may edit — spawn the tester (`test-section`; reconcile mode)
      before anything else. Still non-zero after that pass → **stop**: the tester has said
      why in its return, and it is a document question, not a build one.
   3. Spawn the implementer (`implement-section`). Implementer run 1.
   4. Spawn the tester (`test-section`; it runs reconcile mode now that the README exists).
   5. If the section's intent column now shows fewer passing than total, the tester filed
      follow-ups: spawn the implementer again, then the tester again.
   6. Spawn the reviewer (`review-section`).
   7. On `Verdict: request changes`, while the section has had fewer than three implementer
      runs: implementer, tester, reviewer again — the tester first when the row's `intent`
      count is non-zero, since those findings are the implementer's to leave alone. Still
      `request changes` with three runs spent → **stop**.
   8. Any `Result: blocked` or `Result: stopped`, at any spawn → **stop**.
   9. After every spawn, run `status.py $pkg` and print the section's row — nothing else of
      the output. That row, not the agent's return, is the progress report.

4. **Spine mode, after the spine.** Spawn the architect (`plan-package`) — a completion run.
   `Result: stopped` (decisions or access) → **stop** with its first lines. Then spawn the
   reviewer (`review-plan`). Then **stop**, always; the summary's `stopped because` is:

   ```
   plan complete and reviewed: <verdict>; answer any decisions in docs/decisions.md, then
   re-run /dev-team:run-package $pkg.
   ```

5. **Full mode, after the last section.** Skip 5.1–5.2 when the `surface:` line of
   `status.py $pkg` shows the package review `✓` with `approve` or `approve with fixes`.
   1. Spawn the implementer (`finalize-package`), then the reviewer (`review-package`).
   2. On `Verdict: request changes`, once more each. Still `request changes` → **stop**.
   3. Spawn the architect (`sync-design`).

6. **Summary** — always your last message, whether you finished or stopped, as this block
   and nothing after it. Every line is required; `stopped because` only when stopped. The
   first line reads `done` only after `sync-design` in full mode — a spine-mode run always
   ends `stopped at plan review (spine mode)`, with the step-4 message as `stopped because`.

   ```
   run-package <pkg>: <done | stopped at <step>>
   sections: <built>/<total> built, <reviewed>/<total> reviewed (approve or approve with fixes)
   implementer runs: <n>; tester runs: <n>; reviewer runs: <n>
   commits: <first sha>..<last sha> (<count>)
   stopped because: <the agent's first two lines, or the status.py FAIL lines>   (only when stopped)
   next: <exact command>
   ```

   The run counts are per agent role as listed; count an architect run under none of them.
   `built` and `reviewed` come from a final `status.py $pkg`; `commits` from the start commit,
   `git rev-parse --short HEAD` and `git rev-list --count`. `<step>` names the section and
   the spawn, e.g. `data/clean review-section (implementer run 3)`.

## `next` — what the manual loop would type from here

| Where it stopped | `next` |
|---|---|
| run gate: branch, dirty tree | the gate's own fix, then `/dev-team:run-package $pkg` |
| run gate: missing contract or integration, plan incomplete, not reviewed, `request changes`, open plan finding | `/dev-team:plan-package $pkg` — or `/dev-team:review-plan $pkg` when the only reason is *not reviewed since last change* |
| run gate: an open `D<n>` with no assumption | answer it in `docs/decisions.md`, then `/dev-team:run-package $pkg` |
| a section, blocked or out of implementer runs | `/dev-team:implement-section $pkg/<section>` |
| architect `stopped` (decisions or access) | its own continue action: `/dev-team:plan-package $pkg` |
| spine mode, plan completed and reviewed | `/dev-team:plan-package $pkg` on `request changes`, else `/dev-team:run-package $pkg` |
| spine mode, completion ran but the review did not | `/dev-team:review-plan $pkg` |
| `finalize-package` blocked, or the package review still `request changes` | `/dev-team:finalize-package $pkg` |
| done | `/dev-team:plan-package <p>` for the first package in `docs/architecture.md`'s Packages table with no `docs/packages/<p>/contract.md`, or `/dev-team:finalize-project` when every package has one |

`next` is always one command you resolved yourself, with every name filled in and no angle
brackets left — for `done`, read the Packages table and check each `contract.md` now. Never
copy an agent's own next command in its place.

When an agent stops for decisions, its stubs are already in the ledger. Show its first two
lines and the `D<n>` numbers it names, and stop; answering is the user's.
