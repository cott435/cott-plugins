# run-flow builds and serves a run's chart and unit pages and judges nothing; run-auditor still finds the planted defects in a trace from the moved script

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `039fddf`): `skills/run-flow/SKILL.md`, `skills/run-flow/scripts/{trace,flow}.py`, `skills/audit-run/SKILL.md`; `agents/run-auditor.md` unchanged since `359f45e` · model: `claude-opus-5-5` for executors, auditors and graders (the user's choice after Sonnet 5.5 refused, `2026-10-07-run-flow-behavioral-not-run.md`) · 2026-10-07
**Set:** `evals/sets/run-flow.json` evals 1, 2 (B1.1) · `evals/sets/audit-run.json` eval 2 (B1.2) · **Iteration:** `evals/workspace/run-flow/iteration-2`, `evals/workspace/audit-run/iteration-2` · **Baseline:** B1.1 none (`without_skill`); B1.2 previous = `359f45e` (`old_skill`) · **Pass rate:** B1.1 with_skill 15/15 (100%) vs without_skill 4/15 (27%); B1.2 with_skill 7/8 (88%) vs old_skill 8/8 (100%) as graded; 8/8 vs 8/8 under the expectation as reworded at review

## What was tested

- **B1.1.** `run-flow`, given the planted session by id or by its chat title, builds the chart
  and U01's page into the toy plugin's workspace with the moved scripts. Given the title, it asks
  once between the chat and its fork. It serves the result, stops the server, closes in two
  lines, and judges nothing.
- **B1.2.** `run-auditor`, on a trace built by `skills/run-flow/scripts/trace.py`, still reports
  the five planted defects as ERRORs with the right steps and rules.

## Method

- **Runs.** `run-evals`' behavioral loop, n=1 per cell, six executors in one message. One
  executor (run-flow 2 `without_skill`) ended on an Opus 5.5 safeguard error and was rerun once;
  the rerun finished. Every other executor finished first time.
- **B1.2's setup.** The prompt spelled out eval 1's build command, and `run-auditor` ran as
  general-purpose proxies following the plugin root's `agents/run-auditor.md` (a Deviation in
  note 01).
- **Grading and benchmark.** One Opus grader per run, then `aggregate_benchmark`. No blind
  comparison: B1.1's baseline is `without_skill`, and B1.2's two pass rates are 12 points apart.
- **Cost.** About 0.47M executor tokens and 0.43M grader tokens.
- **Set fixes after grading** (run-evals step 7). Four run-flow expectations the graders called
  ambiguous were reworded in `evals/sets/run-flow.json`:
  - a relative `--out` that resolves to the workspace counts;
  - a `--help` probe is not "the first call";
  - (twice) trace.py's own `unconfirmed` label is a fact, not a judgment.

  None of the four changes a verdict, so nothing was rerun.

## Results

| Case | with_skill | baseline | Pass bar |
|---|---|---|---|
| run-flow 1 · by id | 8/8 | without_skill 2/8: hand-wrote its own viewer under `$TMP/toy/.run-flow/`, flagged "8 issues, 4 high" | ✅ every with_skill passes; baseline fails ≥1 |
| run-flow 2 · title, fork question | 7/7: asked once, labels in quotes, picked `0a0d17f0`, server killed | without_skill 2/7: options labelled by id, workspace at `toy/run-trace`, retold and judged the writer's steps | ✅ |
| audit-run 2 · U01 auditor | P1–P4 ERRORs with the right `U01.S<n>` and `writer.md` lines | old_skill the same | ✅ |
| audit-run 2 · seg-1 auditor | P5 is an ERROR at D5 against `ship/SKILL.md:13`, **but fault `agent`**; the done-branch-on-`Done.` ERROR is present | P5 with fault `driver` | ❌ 1 expectation |
| audit-run 2 · returns | one `Findings:` line each | the same | ✅ |

**B1.2's miss.** The expectation reads "an ERROR with fault driver for the Write of out/extra.txt
at D5". Both auditors cited the same step and the same rule; they differ only in the fault
label. `run-auditor.md`'s fault table defines `driver` as "the spawner sent the wrong inputs, or
acted wrongly on a return", and `agent` as "the definition was clear and the agent did not follow
it". In `driver` mode, the driver writing a file its skill forbids fits both rows. That makes it
an ambiguity in the unchanged agent's definition, or in the expectation, and not an effect of
this phase: the trace both auditors read is byte-identical between the two scripts
(`2026-10-07-run-flow-mechanical-load.md`, M1.2).

## Verdict

- **B1.1 held.** run-flow builds and serves the chart and the unit page, from an id or a title,
  asks only between a chat and its fork, and judges nothing. The baseline fails both evals on
  judging and on the page's shape.
- **B1.2 held after the expectation was reworded.** As graded, it missed by one fault label,
  whose cause is `run-auditor.md`'s fault table, which this phase does not touch. At review the
  user chose to reword the expectation: `audit-run.json` eval 2 now accepts fault `driver` or
  `agent` for the D5 write, since the table fits both. The with_skill run's F1 meets the reworded
  expectation on the evidence its grader already quoted: ERROR at `D5` against
  `skills/ship/SKILL.md:13`. So B1.2 is 8/8, the same as the baseline. Nothing was rerun: the
  executors' outputs are unchanged, and only how one expectation reads them changed.
