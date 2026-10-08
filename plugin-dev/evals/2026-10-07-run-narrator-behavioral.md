# run-narrator phase 8 — a step-ranged account of one unit that judges nothing (B8.1), Sonnet 5.5

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `dd6af0f`): `agents/run-narrator.md` (new; `model: claude-sonnet-5-5`, a full id, not a dated pin) · model: executors and graders `claude-sonnet-5-5` (Agent tool `model: sonnet`; the executors' transcripts record `claude-sonnet-5-5`) · 2026-10-07
**Set:** `evals/sets/run-narrator.json` evals 1, 2 · **Iteration:** `evals/workspace/run-narrator/iteration-1`, `evals/workspace/run-narrator/iteration-2` (after the one fix; viewer `iteration-2/review.html`) · **Baseline:** none (`without_skill`) · **Pass rate:** iteration 1 (regraded on the corrected set) with_skill 20/21 (eval 1 11/12, eval 2 9/9) vs without_skill 9/21 (7/12, 2/9); iteration 2 with_skill 22/22 (eval 1 12/12, eval 2 10/10) vs without_skill eval 2 2/10, eval 1 not run (two safeguard errors) · **Blind:** not run (`without_skill` baseline)

## What was tested

That run-narrator, spawned with the four `Field: value` lines, writes `explain/U<nn>.md` as a
header `U<nn> · <type> · steps 1–<n>` and step-ranged lines covering S1–S<n> with no gap or
overlap (one per step for a two-step unit), states only what the cited steps show (the failed
pytest, the failed `git add` and no commit, the hook block, the reviewer's verdict and counts
as handed back), judges nothing, reads the clipped `.md` before any `.json`, writes nothing
else, and returns one `Explained:` line (B8.1). The proxy: a general-purpose executor told to
follow `agents/run-narrator.md`, which does not reproduce its `tools: Read, Write`.

## Method

- `run-evals` behavioral loop, one run per configuration. Fixture:
  `evals/fixtures/audit-run/make_session.py` into a `mktemp -d` per run; eval 1 narrates the
  planted session's U01 (`toy:writer`, 8 steps), eval 2 the flow session's U03
  (`toy:reviewer`, 2 steps). Harnesses `evals/sets/files/run-narrator/planted-u01.md` and
  `flow-u03.md`.
- **Set corrections after iteration 1's graders** (`run-evals` step 7; iteration 1 regraded on
  the corrected set, first grades kept outside the iteration):
  - both evals' Return expectation now reads the *first* line under `## Return`: the harness
    tells the executor to put its summary after that line, and two graders split on it;
  - eval 1's outputs expectation allows the harness's own `interview.md`;
  - eval 1's no-judgment expectation now fails a file that judges anywhere ("what the report
    gets wrong", "rule breaks"), not only one using five listed words: the first baseline
    judged throughout and passed it;
  - eval 1 gained an expectation that S3 names `notes/scratch.md` and S6 the hook block, which
    nothing checked;
  - eval 2's "nothing the steps do not show" now says that "no other tool call, read or
    write" is something two steps do show;
  - eval 2 gained an expectation that the S1 line names section `a/x` (added after iteration
    1's regrade, so graded in iteration 2 only).
- **The one fix.** Iteration 1's with_skill eval 1 missed the S5 expectation: its line quoted
  the pathspec error and "the trace marks the commit as unconfirmed" but never said the commit
  was not made. `agents/run-narrator.md` **What to do** now says a failed command is described
  as failing in plain words, with what it left undone when the output shows it, and that
  quoting the error or the trace's `unconfirmed` label is not enough. Both evals were rerun in
  both configurations as iteration 2.
- **Not run:** iteration 2's eval 1 `without_skill` executor ended twice on the Sonnet 5.5
  safeguard (`reasoning_extraction`), the second time on the rerun the loop allows; it is left
  out of iteration 2's pass rate. The fix does not reach a `without_skill` run (it never reads
  the agent file), and iteration 1's eval 1 baseline was graded on the same 12 expectations
  (7/12), so the pass bar's "without_skill fails at least one per eval" rests on that run.
- Cost: executors 61.5k–64.9k tokens and 27–80 s each; graders about 65–71k each.

## Results

| Eval · config | Iteration 1 | Iteration 2 | Notes |
|---|---|---|---|
| 1 · with_skill | 11/12 | **12/12** | it. 1 miss: S5 never said the commit was not made; it. 2: "The add failed … so no commit of out/a.txt was made by this call", 7 lines (S7–S8 merged) |
| 1 · without_skill | 7/12 | not run | a 35-line report with "What the report gets wrong" and "Rule breaks" sections, numbered `**U01.S1**` items, no header, prose return |
| 2 · with_skill | 9/9 | **10/10** | two lines, `S1 · … "Section: a/x"` and `S2 · … request changes … 1 critical, 2 warnings` |
| 2 · without_skill | 2/9 | 2/10 | prose reports that tell what followed (D6, U04, U05) and question the reviewer ("Was a/x actually read?") |

Grader critiques left as they are: the read-order and files-written expectations rest on the
executor's own `transcript.md` (no tool log), which is how every harness here works; the
forbidden-word list could trip on a quoted message containing "must", which neither fixture
has; nothing checks that S7 quotes all three handed-back claims (both with_skill runs did).

## Verdict

Held after one fix. B8.1's bar, every expectation for `with_skill` and at least one miss for
`without_skill` per eval, is met: with_skill 22/22 in iteration 2, without_skill 7/12 (eval 1,
iteration 1, same expectations) and 2/10 (eval 2, iteration 2). Iteration 1 missed the bar by
one expectation; the fix to the agent's failed-command rule closed it.
