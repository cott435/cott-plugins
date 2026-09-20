# 09 — Evals and the fixture repo

Phases 0 and 9, plus the per-phase evals every other note names. Every eval is logged
with `plugin-dev`'s `log-eval` before its phase commits — a clean pass exactly like a
failure — and every behavioral eval runs against the same fixture, so results are
comparable across phases.

## The fixture — `evals/fixtures/two-package/`

A complete input to the new-repo workflow that needs no network and no credentials:

```
evals/fixtures/two-package/
├── README.md              what this is; how to reset; what each eval expects
├── reset.sh               copies the fixture to a fresh directory, `git init`, creates
│                          branch `build`, commits the brief and the dataset; prints the path
├── docs/
│   ├── brief.md           the brief, already shaped (Scope now / later / out)
│   └── constraints.md     coverage 80, mypy strict, docstrings 95 (used from phase 6 on;
│                          earlier phases delete it in reset.sh --no-constraints)
└── data/
    └── trades.csv         400 synthetic rows: ts (ISO, UTC), symbol (3 values), price,
                           size, side; two duplicate rows and one out-of-order timestamp,
                           on purpose
```

The brief contracts two packages:

- `data` — sections `ingest` (reads `data/trades.csv`, `source: dataset:trades`),
  `clean` (dedupe, sort; `Depends on: ingest`), `storage` (SQLite via stdlib `sqlite3`;
  `Depends on: clean`). Three sections, so spine-first selects `ingest` (two transitive
  dependents).
- `analysis` — sections `features` (rolling VWAP per symbol; consumes `data.load_trades`),
  `report` (a markdown summary; `Depends on: features`). Two sections, so it plans in one
  run.

Sizes are chosen so a full `run-package data` finishes in one sitting and the whole
two-package build is feasible for the phase-9 end-to-end eval.

`reset.sh` is the only executable in `evals/`; it is bash, `set -e`, and prints the
created path as its last line.

## The evals

| ID | Phase | Kind | Claim | Pass when |
|---|---|---|---|---|
| A | 0 | mechanical | a main-conversation skill can spawn a plugin agent, and the `subagent_type` string is `dev-team:<agent>` | a throwaway skill in a scratch project spawns `dev-team:reviewer` with the prompt "return the word ok"; the call succeeds; the log records which of `dev-team:reviewer` / `reviewer` resolved |
| B | 0 | mechanical | `${CLAUDE_PLUGIN_ROOT}` is substituted in a main-conversation skill body; and in an agent body (implementer.md line ~176 relies on it) | the throwaway skill echoes the substituted path; a spawned implementer, asked to print the lint-config path it would read, prints an absolute path |
| C | 1 | mechanical | no vendored skill carries JS-stack text or the upstream file name | `grep -rlE 'npm|jest|describe\(|it\(|eslint|@ts-ignore|CONSTRAINTS\.md'` over the four vendored files hits only Provenance lines |
| D | 2 | mechanical + behavioral | `status.py` reviewed-since-build is commit-based; the implementer commits exactly its paths with the trailer | three-state check on the fixture; `git show --stat HEAD` after one implement run equals the staged-paths set; `git log -1 --format=%B` contains `Dev-Team-Run: implement-section data/ingest` |
| E | 3 | mechanical + behavioral | the two order-of-authority lists are identical; the reviewer splits recorded / unrecorded deviations; sync-design writes As shipped | regex extraction equal after whitespace normalization; report has 1 WARNING (naming sync-design) and 1 CRITICAL; the design gains one As shipped row |
| F | 4 | behavioral | the tester never reads source; intent tests are red; commits only its tree; reconcile touches only cited tests | four checks listed in note 04 §Steps 5 |
| G | 5 | behavioral | review-plan finds seeded defects; plan-package re-run re-delegates only the affected section and ticks the follow-ups; the gate passes after | the three-run sequence in note 05 §Steps 5 |
| H | 6 | mechanical + behavioral | the gate runs constraints rows; the reviewer flags a lowered bar | one `constraint … FAIL` line; one `bar lowered` CRITICAL |
| I | 7 | behavioral | spine selection, too-early return, completion run with `Sibling shipped:`, `--all` | four checks in note 07 §Steps 5 |
| J | 8 | behavioral | the driver runs the loop, stops on the right gates, and duplicates no skill text | three runs in note 08 §Steps 6; the grep in its Done-when |
| K | 9 | end-to-end | the whole new-repo workflow runs on the fixture under 0.5 | below |
| L | 9 | measurement | fixed context cost per section | below |

Log file names: `evals/<date>-<id-in-kebab>.md`, e.g. `2026-09-19-a-subagent-type-resolution.md`,
each with **Tested against** commit and model per `log-eval`, and a row in
`evals/README.md`.

## K — end-to-end

From `reset.sh`: `shape-brief` is skipped (the brief is pre-shaped); `set-constraints` is
skipped (pre-written); then, typed by hand in one session with `/model` set and recorded
in the log:

```
/dev-team:plan-repo
/dev-team:plan-package data          → spine only (ingest)
/dev-team:run-package data           → builds ingest; completes and reviews the plan; stops
   (answer decisions)
/dev-team:run-package data           → clean, storage, surface, package review, sync-design
/dev-team:plan-package analysis      → one run (two sections)
/dev-team:review-plan analysis
   (answer decisions)
/dev-team:run-package analysis
/dev-team:finalize-project
/dev-team:status
```

Pass: `status.py` shows both packages `shipped`, every section `✓` reviewed with
`approve`/`approve with fixes`, `plan: reviewed … approve`, zero open review follow-ups,
zero `TODO(decision` markers; `uv run pytest`, `lint-imports`, `mkdocs build --strict`
and every Enforced constraint pass; `git log --oneline` shows one commit per run, all
with trailers; every design has an **As shipped** section. The log records every stop
that happened, every decision answered, and any manual intervention — an intervention is
not a failure, but an unlogged one is.

## L — fixed cost per section

For each Agent call the driver made in K, record from the transcript: input tokens at
first model turn (the cost of the prompt plus the documents read before any code is
written) and total tokens. Table in the log: section × role × (fixed, total). This is the
number the second critique asked for and the one that decides whether a *derived* task
packet is worth building in 0.6. No change to the plugin is made on its basis in 0.5.

## Phase 9 also

- `README.md`: Contents tree (all additions), §One-time setup (eight agents; git branch),
  §Which skill to run, §Workflows, §Questions (unchanged), §Follow-ups and reviews (add
  `<pkg>/plan` and `— tester` entries), §Code conventions table (tester column;
  three vendored rows), §`docs/` layout (`constraints.md`, `reviews/*-plan.md`,
  `tests/intent/`), §Hand-off diagram (tester, review-plan, run-package, sync-design),
  §Gotchas (branch, commit, driver context).
- `site/flow.md`: the three diagrams updated per note 00; **Order of authority** with
  `constraints.md` first and **As shipped**; the `docs/` map rows from note 00.
- `site/workflows/new-repo.md`: rewritten around spine-first and `run-package`;
  `change-shipped-code.md` gains one line on `sync-design` after `sync-plan`.
- `CHANGELOG.md`: an `## [Unreleased]` section with the five breaking items from note 00
  and one line per phase; `bump-version` turns it into `## [0.5.0]` when the user says yes.
- `marketplace.json` and `plugin.json` descriptions: "eight specialist subagents, a tester
  that writes tests from the design, and a driver that runs a package end to end".
- `check-contracts`, `build-site`, then commit
  `dev-team 0.5 (phase 9): docs, site, changelog; end-to-end eval logged`, then propose
  the bump in chat — 0.5.0, minor: additive with the five listed breaks, which is what
  the plugin's 0.x line has done at 0.3.0 and 0.4.0.

## Done when

K and L are logged; the README's Contents tree matches `ls` (the `names_listed` claim);
the site builds; the branch has ten phase commits and is ready for the bump proposal.

## Deviations

- **K ran as eleven headless sessions, not typed in one.** The note: "typed by hand in one
  session". Done: one `claude -p` run per command on one fixture copy, as in eval J. That
  way every run leaves its own stream for L and its own cost. The command sequence is the
  note's, and the only manual step was answering D1.
- **K has three extra runs.** `review-plan analysis` returned `request changes`, so
  `plan-package analysis` and `review-plan analysis` ran again before the note's
  `run-package analysis`. This is the documented answer to a plan CRITICAL.
- **K's pass line is not met by the first phase-9 commit, and a second one fixes it.**
  Four checks failed on plugin defects (eval K §Verdict): plan-freshness after
  `sync-design`, a CRITICAL under `approve with fixes`, the root `pytest` collision between
  two `tests` packages, and bare `designer` in `architect.md`. The note has phase 9 writing
  docs and logging K, so the fixes are a second commit on this phase, with their own eval
  (M) re-checking each on the repo K built. K itself is not re-run end to end.
- **L measures context size, not per-turn input.** The note: "input tokens at first model
  turn … and total tokens". The stream reports `usage.total_tokens` per task as a context
  size, first after one tool use. L records that value and its end-of-task value, and
  states the one-tool-result upper bound.
- **`README.md` needed less than the note lists.** Phases 4–8 had already updated the
  Contents tree, §One-time setup, §Which skill to run, the conventions table and most of
  §`docs/` layout. Phase 9 added the rest: the `— tester` follow-ups, the `Commit:` line,
  `tests/intent/`, the tester in the hand-off diagram, the branch/commit gotcha, and
  `run-package` in §Workflows.

