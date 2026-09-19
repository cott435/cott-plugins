# Trigger rates of plugin-dev's five automatic skills, and the guarded description optimizer

**Tested against:** uncommitted — see working-tree diff (`evals/sets/*.trigger.json`, `skills/run-evals/`; the five descriptions as of `5fdfdd9`) · skill-creator `run_eval.py` / `run_loop.py` from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · Claude Code 2.1.270 · model: `claude-opus-5` (`claude -p` for every query and every rewrite) · 2026-09-19

**Set:** `evals/sets/{log-eval,build-site,check-contracts,new-plugin,run-evals}.trigger.json` (20 queries each, 10/10)

**Trigger rate:** log-eval 0.95 · build-site 1.00 · check-contracts 0.70 → 1.00 · new-plugin 1.00 · run-evals 0.50 → 0.90 — see the table — before is `run_eval` on all 20 queries; after is the description in the skill when this phase committed.

## What was tested

P2-T1…T5 of `site/notes/0.9-evals-02-trigger-evals.md`: does each automatic skill's
description get picked for queries that should invoke it, and stay unpicked for near-misses
and for the same task outside a plugin repo — and, below 0.9, does `run_loop` find a better
description that also passes the guard (held-out score beats the current one; every
outside-a-plugin query still does not trigger; the scoping clause is kept). Pass bar: final
accuracy ≥ 0.85 for each.

## Method

Real runs. Each description is written by `run_eval.py` as a temporary command into a
scratch project in the session scratchpad (its own `.claude/`, `plugin-dev@cott-plugins`
disabled in its `settings.json`, no repo and no `CLAUDE.md` above it), and each query goes
through `claude -p` from there, 3 runs per query, `--num-workers 1`, threshold 0.5. A query
counts as triggered only if the model's *first* tool call is `Skill`/`Read` on that command;
any other first tool call scores as not triggered. `run_loop.py` (skills below 0.9 only):
40% holdout (8 of 20 queries, seed 42), up to 5 iterations, rewrites by `claude -p` with the
same model, `--report none`. Raw results: `evals/workspace/<skill>/trigger/`
(gitignored). Cost: 300 `run_eval` calls plus ~180 in each loop and one rewrite call per
iteration; ~2.5 min per 60 calls.

## Results

| Skill | Before (all 20) | Should / should-not | Optimized? | Best held-out (iteration) | Guard | After |
|---|---|---|---|---|---|---|
| `log-eval` | 19/20 = 0.95 | 9/10 · 10/10 | no — ≥ 0.9 | — | — | 0.95, unchanged |
| `build-site` | 20/20 = 1.00 | 10/10 · 10/10 | no | — | — | 1.00, unchanged |
| `check-contracts` | 14/20 = 0.70 | 4/10 · 10/10 | yes, 3 iterations (all train passed at 3) | 7/8 (2) vs 6/8 current | (a) ✅ (b) ✅ (c) ❌ — rejected; then a hand rewrite with the clause kept: held-out 8/8, (a)(b)(c) ✅ — **applied** | **20/20 = 1.00** |
| `new-plugin` | 20/20 = 1.00 | 10/10 · 10/10 | no | — | — | 1.00, unchanged |
| `run-evals` | 10/20 = 0.50 | 0/10 · 10/10 | yes, 3 iterations (all train passed at 3) | 7/8 (2) vs 4/8 current | (a) ✅ (b) ✅ (c) ✅ — **applied** | **18/20 = 0.90** (9/10 · 9/10) |

No outside-a-plugin query triggered in any run of any skill, before, during or after
optimization. One near-miss *inside* a plugin did: with `run-evals`' new description, "log
that the implementer eval passed in dev-team/evals — I already ran it, just record it"
(a `log-eval` job) triggered 2/3 in the loop's train split and 3/3 in the after run. It has
no `plugin` in its text, so `validate`'s heuristic counts it as an outside query; it is
not one — it names `dev-team/evals` — and guard (b) was judged on the queries that really
are outside a plugin repo (pytest, the OpenAI evals harness, hyperfine, jest, pandas,
promptfoo, a `~/.claude/skills` skill "not a plugin"), all 0/3.

Misses before optimizing:

- `log-eval` — "I'm in dev-team/. The tester agent's skills preload test from this morning
  — document it as an eval, commit is a1b2c3d" 0/3.
- `check-contracts` — "does plugin-dev still pass its own cross-file claims?…", "I added a
  skill to plugin-dev but I'm not sure README's skills table is updated…", "before bumping
  plugin-dev to 0.9.0, verify every heading…", "after editing the log-eval skill, check the
  plugin's contracts…" 0/3 each; "run the contract sweep for the plugin in
  ~/dev/cott-plugins/dev-team…", "my contracts.yml in trading-agents has a new headings
  claim…" 1/3 each.
- `run-evals` — all ten should-trigger queries 0/3. A hand run of two of them with the
  temporary command present showed why: the model's first call is `Bash` (listing the
  plugin directory to find the set) — it starts the job itself rather than loading the
  skill, which `run_eval.py` scores as a miss.

### `check-contracts`: the rejected description, then the applied one

Before:

> Check the cross-file claims a plugin's own agents and skills act on — a heading one file parses and another owns, a rule one file states and another contradicts, a list of names that goes stale when a directory changes. Use only in a plugin repo that has a contracts.yml, after editing any agent or skill, and before proposing a version bump.

`run_loop`'s best (iteration 2, held-out 7/8, train 11/12), not applied:

> Use when someone asks to check, verify, or sweep a Claude Code plugin's own contracts — the cross-file claims its agents and skills make about each other (a heading one file parses and another owns, a rule one file states and another contradicts, a list of skill or agent names that goes stale when a directory changes). Typical asks: "check the contracts for this plugin", "run the contract sweep", "I edited an agent/skill — does the bundle still hold?", "which file:line fails?", or before bumping a plugin version. Runs a script over a `contracts.yml` at the bundle root and reports PASS/FAIL with exact file:line. Not for API/service contract testing (Pact, OpenAPI, contract tests in a service repo), type checking, or generic markdown/link linting — this is only about a plugin's internal prompt files agreeing with each other.

Why not: guard (c) — it drops "Use only in a plugin repo that has a contracts.yml", the
clause `plugin-dev/CLAUDE.md` requires so the skill stays quiet in unrelated sessions.
Iteration 3 (train 12/12, held-out 7/8) dropped it too ("Use when working inside a Claude
Code plugin/bundle repo…" — no `contracts.yml` condition, and "Treat any 'check contracts'
phrasing in a plugin context as this skill" widens it).

**Follow-up, same day, at the user's request:** a hand rewrite that keeps iteration 2's
content (the "check, verify, or sweep" asks, the not-for list) and restores the clause
verbatim, re-measured with `run_eval --description` on all 20 queries, same conditions:

> Check a Claude Code plugin's own contracts — the cross-file claims its agents and skills make about each other (a heading one file parses and another owns, a rule one file states and another contradicts, a list of skill or agent names that goes stale when a directory changes) — and report PASS/FAIL with exact file:line. Use when someone asks to check, verify, or sweep a plugin's contracts ("check the contracts", "run the contract sweep", "does the bundle still hold after my edit?", "which file:line fails?"), after editing any agent or skill, and before proposing a version bump. Use only in a plugin repo that has a contracts.yml. Not for API/service contract testing (Pact, OpenAPI, tests/contract/), type checking, or markdown/link linting.

20/20 (10/10 · 10/10, every query 0/3 or 3/3); on `run_loop`'s held-out 8 it is 8/8 against
6/8 for the old description, and no should-not query triggered — guard (a), (b), (c) hold.
Applied. Caveat: the held-out queries are held out from the optimizer, not from this
rewrite — its author had read every miss, including the held-out ones — so 8/8 is weaker
evidence than `run_loop`'s 7/8. Raw: `run_eval-candidate.json`.

### `run-evals`: the applied description

Before:

> Run the evals for one skill or agent of a Claude Code plugin - mechanical checks, a load check, behavioral runs against a baseline graded assertion by assertion with skill-creator's grader, benchmark and viewer, and trigger tests for skills the model invokes - then record the result with log-eval. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), whenever a phase note or a change calls for evals, or before claiming that a skill or agent behaves a certain way.

After (iteration 2; train 11/12, held-out 7/8; all 20: 18/20):

> Use when the user wants to test, prove, benchmark, or verify the behavior of a specific skill or agent that lives in a Claude Code plugin repo — e.g. "run the evals for <skill>", "run eval N against the baseline", "does <agent> still do X after my edit?", "benchmark this skill against main/the previous version", "prove it before I claim that", "check whether the description triggers". Covers running a target's committed eval set (evals/sets/<target>.json), comparing the working-tree version against a baseline ref, grading each assertion, opening the benchmark/viewer for review, trigger-rate tests, and logging the result. Use it whether the user names the set file, the target, the plugin directory, or just asks to test behavior after a change. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json); not for application test suites, generic eval harnesses for models, or creating a new skill from scratch.

Iteration 3 (train 12/12, held-out 7/8) tied on held-out score — `run_loop` keeps the first
best — and dropped the scoping clause ("Use when… in a Claude Code plugin repo" with no `only inside` sentence).

Still missed after: "the phase note says to run P3-B1 on plan-phases; run it and stop for my
review" 0/3 — with no path or plugin named, the model starts on it directly.

## Verdict

**All five meet the pass bar** — `check-contracts` only after the follow-up hand rewrite.

- `log-eval` 0.95, `build-site` 1.00, `new-plugin` 1.00 — at or above 0.9, not optimized.
- `run-evals` 0.50 → 0.90 with an applied description that passes the guard.
- `check-contracts` 0.70 → 1.00. The optimizer's best (held-out 6/8 → 7/8) failed guard
  (c) and was not applied; its misses were should-trigger queries phrased as a
  verification ("does plugin-dev still pass its own cross-file claims?", "verify every
  heading…") rather than naming contracts. A hand rewrite of that description with the
  clause restored scored 20/20 and passed the guard, and was applied (see the caveat
  above).
- Every outside-a-plugin query stayed quiet for all five.
- *Noticed:* `run-evals`' new description now claims the `log-eval` near-miss above. In a
  real session both skills are present and `run-evals` ends by invoking `log-eval`, so
  the cost is a longer path to the same log, but the overlap is worth a `log-eval`
  trigger rerun alongside `run-evals` next time either description changes.
