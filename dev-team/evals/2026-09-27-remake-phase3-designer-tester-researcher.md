# remake phase 3 — designer modes and spec-change, tester design-gap and regenerate, per-section probe entries

**Tested against:** uncommitted — see working-tree diff (on `23a6d3f`; `agents/designer.md`, `agents/tester.md`, `agents/researcher.md`, `skills/planning-templates/references/source-probe.md`, `contracts.yml`) · model: `claude-opus-5-5` for designer iteration 1, researcher iteration 1 and tester iteration 1 (executors and graders, inherited); `claude-sonnet-5` for tester iteration 2 and the researcher eval 1 regrades (the user's instruction mid-phase: every eval agent on Sonnet) · 2026-09-27
**Set:** `evals/sets/designer.json` evals 1–3 · `evals/sets/tester.json` evals 1–3 · `evals/sets/researcher.json` evals 1–2 · **Iteration:** `evals/workspace/designer/iteration-1`, `evals/workspace/tester/iteration-1`, `evals/workspace/tester/iteration-2` (after one fix to `agents/tester.md`), `evals/workspace/researcher/iteration-1` · **Baseline:** `af08482` (`git merge-base HEAD main`, the 0.6 agents) · **Pass rate:** designer 100% vs 38%; tester iteration 1 69% vs 30%, iteration 2 93% vs 39%; researcher 100% vs 83% · **Blind:** not run (no target within 10 points of its baseline)

## What was tested

Five rows from `site/notes/remake-03-designer-tester-researcher.md` § Evals:

- **3.1** Does `check-contracts` pass with the new deviations-entry claim and the re-pointed
  reader spans, and does a planted `cites: ['Clausee']` fail?
- **3.2** Does the designer write `Mode:` as its first line, apply a change file in `delta`
  mode as a whole rewrite, and raise a contract contradiction as a `spec-change:contract`
  ledger entry with no design?
- **3.3** Does the tester return `design-gap` without writing anything, write red tests from
  documents only, and regenerate only the tests an approved deviation's clause cites, tagged
  ` (deviation <date>)`?
- **3.4** Does the researcher still write a statistics-only dataset probe on the template's
  headings (regression), and does a re-probe for a second section keep the doc and append its
  `## <pkg>/<section>` entry under **Sections served**, with a commit?
- **3.5** Do the three agents register when the plugin loads from its working copy?

## Method

- **3.1** `python3 ../plugin-dev/scripts/contract_sweep.py`, then the tester reader's `Clause`
  cite changed to `Clausee`, the sweep run again, and the plant reverted.
- **3.5** `claude --plugin-dir ./dev-team -p "List the agents you have from dev-team, one name
  per line, nothing else"` from the repo root.
- **3.2–3.4** `run-evals`: one executor per eval and configuration, spawned in one message, a
  general-purpose subagent given the agent file (proxy: the agent's `tools:` and `skills:` are
  not reproduced). `with_skill` read the working tree; `old_skill` read the snapshot at
  `af08482`. Plugin skills were read from the working tree in both. One grader per run
  (skill-creator's `grader.md`). 16 executors, 16 graders, plus reruns and regrades.
- **Contamination.** Designer eval 1's first `with_skill` run read `eval_metadata.json` (the
  assertions) before writing. It was discarded and rerun under an added harness rule forbidding
  reads of `evals/workspace/` and `evals/sets/*.json`. No other run read either (grep of every
  transcript).
- **Expectation corrections** (run-evals step 7), each from a grader's critique:
  - designer evals 1–3: the output allow-list admits the designer's own
    `.claude/agent-memory/designer/` file, which its Memory section tells it to write
    (designer eval 2 `with_skill` regraded 10/11 → 11/11);
  - tester evals 1–3: `find`, `tree` and any listing whose output names a file under the
    section path are forbidden alongside `ls`/Glob; eval 1's allow-list admits
    `interview.md` and tool caches; eval 2's §4/§6/§7 clause names the `Gap:` line's heading,
    not its why-clause; eval 3 allows import lines the rewritten test needs and counts the
    tag in `*.py` files only;
  - tester eval 2's fixture `ingest-gap.md` had dropped `VendorError`'s definition along with
    the `fetch.py` row, planting a second gap; the definition is restored, so the design lacks
    only the Module plan row;
  - tester harness sheets run pytest with `PYTHONDONTWRITEBYTECODE=1` and ruff with
    `--no-cache` (iteration 1 left `__pycache__/` in the read-only fixture trees; removed);
  - researcher eval 1: pandas reads `n/a` as missing by default, so `systolic` loads as
    float64; the expectation now asks for both missing spellings and a truthful dtype, and
    the heading order admits **Sections served** and requires the re-run-only headings
    absent. Both configurations regraded (Sonnet).
- **The one fix** (tester, after iteration 1): the Hard rule forbids `find`, `tree` and any
  recursive listing or search whose scope takes in the section path; **Regenerate** step 3
  says the tag ends the first line, after any closing period, and allows the imports the
  rewritten test needs; **Return** gets separate blocks for a first run, a regenerate run and
  a design gap. Iteration 2 reran all three tester evals, both configurations, on Sonnet.

## Results

| Row | Case | `with_skill` | `old_skill` | Pass bar | Holds |
|---|---|---|---|---|---|
| 3.1 | contract sweep | 30/30 PASS | — | all PASS | yes |
| 3.1 | planted `Clausee` | FAIL, `agents/tester.md names 'Clausee'` | — | the plant fails | yes |
| 3.5 | load | 8 agents listed, `designer`, `researcher`, `tester` among them | — | the three appear | yes |
| 3.2 | designer eval 1, storage `new` | 12/12 | 7/12 | every expectation passes; old fails `Mode:` line and `spec-change` return | yes |
| 3.2 | designer eval 2, ingest `delta` | 11/11 (after the allow-list correction) | 6/11 (no `Mode: delta`, kept As shipped/Revision, stapled a delta section) | as above | yes |
| 3.2 | designer eval 3, prices `spec-change` | 11/11 | 0/11 (wrote a design, deviation under Contract deviations) | as above | yes |
| 3.3 | tester eval 1, intent (iter 1 / iter 2) | 9/10 / 8/10 | 6/10 / 6/10 | every expectation passes; old fails `design-gap` and the regenerate tag | **no** |
| 3.3 | tester eval 2, design-gap (iter 1 / iter 2) | 3/5 / 5/5 | 0/5 / 0/5 | as above | yes (iter 2) |
| 3.3 | tester eval 3, regenerate (iter 1 / iter 2) | 4/7 / 7/7 | 2/7 / 4/7 | as above | yes (iter 2) |
| 3.4 | researcher eval 1, first probe (regression) | 9/9 | 7/9 | pass rate ≥ the baseline's | yes |
| 3.4 | researcher eval 2, second-section re-probe | 9/9 | 8/9 (did not commit: no `Commit: yes`) | every expectation passes | yes |

The tester's two misses in iteration 2, eval 1:

- **Source listing.** Before reading the design, the tester ran one exploratory `find` over
  the fixture repo that recursed into `packages/data/src/data/ingest/` and printed
  `__init__.py` and `models.py`. It opened neither and its imports come from the Module plan,
  but the rule forbids the listing outright. Iteration 1 did the same in all three evals
  (`find` was not yet named in the rule); the fix removed it from evals 2 and 3 and not from
  eval 1. The 0.6 baseline did it too in both iterations, so the habit is the proxy
  executor's orientation step, not new behavior.
- **Heading.** `test_fetch_bars_retries_once_on_429` cites `Design §7 vendor <status>`, where
  `vendor <status>` is an error case the design states in §6; the file's other three
  `vendor <status>` tests cite §6.

## Verdict

- **3.1, 3.2, 3.4, 3.5 hold.** The designer writes `Mode:` first, rewrites a delta whole with
  no stapled changelog, and raises a contract contradiction as a ledger entry and nothing
  else; the 0.6 designer does none of the three. The researcher keeps a first probe's quality
  and extends an existing doc for a second section, with a `probe <source>` commit.
- **3.3 is missed after one fix.** `design-gap` and regenerate now pass every expectation, and
  the baseline fails both as the bar requires, but intent-mode eval 1 is 8/10: one listing
  that reached the section path, one docstring on the wrong heading. Recorded as a Deviation
  in the phase note; no second fix was made.
- **Eval-set quality.** Graders repeatedly note that the transcripts are the executor's own
  narrative, not tool logs, so every "never read X" and "read Y first" expectation rests on
  self-report. Several also ask for split conjunctive expectations. Neither is changed here.
