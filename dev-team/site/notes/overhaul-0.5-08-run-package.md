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

## Deviations

1. **Invoked by run-package in eight skills, not twelve.** The note says every forked skill
   (12 files). There are fifteen forked skills now, and the driver spawns eight of them:
   `test-section`, `implement-section`, `review-section`, `plan-package`, `review-plan`,
   `finalize-package`, `review-package`, `sync-design`. The overview's non-goals rule out
   changes to `extract-legacy`, `probe-source`, `map-project` and `finalize-project`, and
   nothing spawns the rest this way, so the paragraph went only where it can fire. It also
   names the commit-trailer argument, because in a spawned run the trailer's `$ARGUMENTS` is
   never substituted. `test-section`'s existing one-line version was replaced by the same
   paragraph. No paragraph uses a `$` placeholder, per phase 7's substitution finding.
2. **Tester follow-ups come from `status.py`, not the return.** Step 3.4 says "if the
   tester's return lists follow-ups filed", which contradicts "the driver reads only those
   lines and `status.py`". The driver checks the section's intent column instead: fewer
   passing than total means reconcile left failures, and it files every one of them.
3. **Three implementer runs per section, as a cap.** Step 3.6 says "once more". Written as
   "while fewer than three implementer runs", so a section whose reconcile needed no second
   build still gets two review retries, and eval (iii)'s "stops at implementer run 3" holds
   either way.
4. **The driver runs read-only git.** "Never runs git itself" left the summary's `commits:`
   line with no source. It runs `git rev-parse --short HEAD` at the start and end and
   `git rev-list --count`, and nothing that writes.
5. **The run gate exempts `.claude/agent-memory/` too.** It checks the same exemptions as
   `git-workflow-and-versioning` §Project convention **Baseline**, which has exempted agent
   memory since phase 2. With only the three files, every second `run-package` would fail on
   the first run's memory. `status.py` reads `git status --porcelain -z` without the helper
   that strips output: the first version lost the leading space of the first entry and
   printed `ocs/decisions.md` (mechanical case 2 of eval J).
6. **Resume skip for the close-out.** Step 5 skips `finalize-package` and `review-package`
   when `status.py`'s `surface:` line already shows a fresh `approve` package review, so
   re-running the driver after a stop at `sync-design` does not rebuild the surface.
   `sync-design` always runs; it skips sections already current on its own.
7. **`arguments: [pkg]`** in the frontmatter, and the unsubstituted-name fallback every
   other skill has.
8. **Workflow pages now, not in phase 9.** The root `CLAUDE.md` asks for affected workflow
   pages to be updated with the skill. `site/workflows/new-repo.md` gained a paragraph on
   the driver, and `site/flow.md`'s loop a dotted `run-package` edge. Phase 9 still rewrites
   both for the end-to-end flow.
9. **The tester's `Mode:` line moved to second.** The sentinel is the first line of every
   return, so `test-section`'s "say which as the first line" now reads "on the line after
   your `Result:` line".
10. **Three fixes outside the note, found by eval J's spine run.** Each would have stalled
    the driver on a correct run. (a) `status.py`'s `open_followups` read only an entry's first
    line. The reviewer wraps its entries, so `review …` sat on a continuation line and two
    review-sourced follow-ups counted as `(0 review)`. It now reads each entry with its
    indented continuation lines. (b) The tester's intent tests failed the repo's lint and
    format Floor rows, and no role may edit them but the tester. The tester now runs the
    Toolchain's formatter and `ruff check --fix` on its own tree before every commit
    (**Hard rules**), and reconcile's "byte-for-byte" allows those fixes. (c) ruff 0.16 formats
    Python blocks inside Markdown, so `ruff format --check` failed on `docs/packages/*/design/*.md`,
    which no run may edit. `pyproject-lint-config.toml` now sets `extend-exclude = ["docs"]`.
11. **The summary is the last message, and a spine run is a stop.** The spine eval ended
    `run-package data: done` with no `next:` line and the step-4 message printed after the
    block. Step 6 now requires every line and nothing after the block, and reserves `done`
    for a full-mode run that reached `sync-design`. Step 4's message becomes the summary's
    `stopped because`.
12. **Eval (iii) ran on stub agents.** The real seed, an Enforced row that only a contract
    change can satisfy, made the implementer return `blocked` at run 1. The driver handled
    that correctly: it stopped with `next: /dev-team:implement-section data/clean`, which is
    logged as a pass for the blocked path. But it never reached the cap. A disciplined
    implementer blocks on what it cannot fix, so no real seed reliably reaches three reviews.
    The cap was tested with a plugin copy whose tester, implementer and reviewer are
    `haiku` stubs, the reviewer always returning `request changes`. The driver, the skills
    and `status.py` were the real ones.
13. **The spawn block says Read, not Skill.** "Carry it out as if you had been invoked as
    `/dev-team:<skill>`" led the `sync-design` architect to call the Skill tool. The
    platform refuses that for a `disable-model-invocation` skill and says not to replicate
    it, so the architect returned `blocked`. The block now says to open the file with the
    Read tool, not to call the Skill tool, and that the user's own `/dev-team:run-package` is
    what runs the step. Eleven earlier spawns had read the file without trouble. The resume
    run's architect read it and folded two deviations.
14. **`status.py`: xfail holds, and a shipped package skips the plan check.** The intent
    column counted an `xfail` as failing. The tester writes `xfail` for a decision still open
    on its assumption, so an approved section read `18/19` and the driver's skip rule would
    rebuild it. The column is now total less failed and errors. The run gate failed after
    `finalize-package`, because `interface.md` (and later `sync-design`'s appends) sit under
    `docs/packages/<pkg>/` and make the plan review stale by construction. With
    `interface.md` present the gate now returns `mode: full` without the plan check: only the
    close-out is left to resume, and the package review gates it.
15. **`next` is resolved, never copied.** The first resume printed the architect's own
    placeholder (`/dev-team:plan-package <next package in …>`). The `next` table now requires
    one command with every name filled in; the re-run printed `/dev-team:plan-package analysis`.
