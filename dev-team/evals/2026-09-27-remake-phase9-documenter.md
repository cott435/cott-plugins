# remake phase 9 — documenter and finalize-project: Known gaps from status.py --repo

**Tested against:** uncommitted — see working-tree diff (on `2937046`; `agents/documenter.md` and `skills/finalize-project/SKILL.md` rewritten, `contracts.yml`, `evals/sets/files/documenter/status-repo.txt` regenerated) · model: `claude-opus-5-5` (the phase, 9.1), executors, graders and blind comparators `claude-sonnet-5`, the 9.3 headless session `claude-sonnet-5` · 2026-09-27
**Set:** `evals/sets/documenter.json` evals 1, 2, 3 · **Iteration:** `evals/workspace/documenter/iteration-1` (evals 1–3), `evals/workspace/documenter/iteration-2` (eval 3, after one fix) · **Baseline:** `af08482` (`git merge-base HEAD main`: the 0.6 documenter) · **Pass rate:** iteration 1 93.3% (14/15) vs 86.7% (13/15), per eval 5/5 vs 5/5, 4/4 vs 4/4, 5/6 vs 4/6; iteration 2 (eval 3) 100% (6/6) vs 33% (2/6) · **Blind:** new preferred 3/3 (two of three comparators read the new spec; see Method)

## What was tested

- **9.1** — the rewritten API-page claim (`all_of: ['finalize-project']`, `unless: ['surface section', 'the implementer', 'Known gaps']`) passes on the bundle and fails on a planted sentence crediting `docs/api/<pkg>.md` to `finalize-project`.
- **9.2** — the rewritten documenter still carries `interface.md`'s CLI commands into the package README and turns a missing `interface.md` heading into a Known gaps line (evals 1–2, regression). Eval 3: it copies `status.py --repo` verbatim at the head of Known gaps, writes no `docs/api/` file, reports the conflicting `DATA_RETRIES` default, and takes the Packages statuses from the script.
- **9.3** — `/dev-team:finalize-project` loads from the working tree and writes and commits a root README with Known gaps in a `state-cases` `shipped` build.

## Method

- **9.1** — `contract_sweep.py` on the working tree; then on a scratch copy with the line ``7. `/dev-team:finalize-project` writes `docs/api/<pkg>.md` for every shipped package.`` appended to `skills/finalize-project/SKILL.md`. A second appended line, one the claim exempts (``The surface section writes `docs/api/<pkg>.md`; finalize-project lists a missing one.``), checks the exemption.
- **9.2** — `run-evals`, proxy runs: one general-purpose `sonnet` executor per eval and configuration, given the agent file (working tree, or the `af08482` snapshot) and the set's prompt. One run each. Eval 3 reads `status-repo.txt` in place of the script. That file was regenerated in this phase by the new `evals/sets/files/documenter/build_status_repo.py`, which runs the real `status.py --repo` over the fixture union plus the loop state it needs (designs, intent tests, approving reviews, in commit order, in a scratch git repo). The eval set's 2026-09-20 origin log records no documenter pass rate, since the set was written there and never run. So the evals 1–2 bar is taken against this iteration's baseline. Blind comparison ran automatically: the pass rates were within 10 points.
- **9.3** — `evals/fixtures/state-cases/build.py shipped` into the scratchpad. Added a `.claude/settings.json` disabling the installed `dev-team@cott-plugins` (git-excluded, so the run gate stays clean). Then `claude --plugin-dir ./dev-team -p "/dev-team:finalize-project" --model claude-sonnet-5`, $0.28.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 9.1 bundle | all PASS | 37/37 | ✅ |
| 9.1 plant | the claim FAILs at the plant | `FAIL … skills/finalize-project/SKILL.md:99`; the exempted line (101) silent | ✅ |
| 9.2 eval 1 | ≥ baseline | 5/5 vs 5/5 | ✅ |
| 9.2 eval 2 | ≥ baseline | 4/4 vs 4/4 | ✅ |
| 9.2 eval 3 | every expectation for `with_skill` | 5/6: the script block is verbatim and first; no `docs/api/` file; the conflict is reported; no `docs/plans/`. **Miss:** expectation 4, `report`'s status written `planned (no contract yet)`, not `planned`. Baseline 4/6: no verbatim block, no Status column | ❌ |
| 9.2 eval 3, iteration 2 | every expectation for `with_skill` | 6/6: the Packages table reads exactly `shipped` / `building (1/2 DONE)` / `planned`; everything else as in iteration 1. Baseline 2/6: no verbatim block, statuses in prose, no missing-API-page line, and its Known gaps names `docs/plans/synced.md` | ✅ |
| 9.3 | root README with Known gaps, committed | `Result: done`; `README.md`, `docs/index.md`, `packages/{data,analysis}/README.md` in one commit `docs: package READMEs, root README` with `Dev-Team-Run: finalize-project`; Known gaps opens with the script's block, then document checks (no `docs/api/data.md` for shipped `data`) | ✅ |

Blind: eval 1 A (with_skill) 9.7 vs 5.0; eval 2 A (with_skill) 9.7 vs 6.0; eval 3 A (with_skill) 9.6 vs 6.3. The eval-1 and eval-2 comparators opened the working tree's `agents/documenter.md` (eval 1 also `skills/finalize-project/SKILL.md`) and judged the outputs against it. Only eval 3's comparison is clean.

Set correction (run-evals step 7): the eval-1 old_skill grader noted that expectation 4 passed a run that left D1 out entirely. It now also requires D1 under Key decisions with its decision. Both runs list it there, so no verdict changes and there was no rerun. The eval-2 grader's critique of the `BAR_COLUMNS` expectation (passable without opening `rules.py`) was not taken: not inferring the shape is the outcome it measures.

Iteration 2 graders: the with_skill grader called expectation 5 (`docs/plans/`, `synced.md`) unable to fail. The iteration-2 baseline failed exactly it, so it was kept. The old_skill grader questioned expectations 2 and 4 as wording artifacts. They encode the behavior this phase adds, so they were kept.

Observations:

- The evals 1–2 prompts predate `status.py`. Both `with_skill` runs ran the real script from inside the fixture directory, which has no `.git` of its own, so git answered from the plugin worktree around it. The result was lines like `data/data/ingest: DESIGN`, which the runs copied verbatim, one of them flagging the artifact. Neither prompt gives a `status-repo.txt` as eval 3's does.
- Evals 1–2 ask for `docs/api/data.md`; both `with_skill` runs refused, citing the hard rule. No expectation measures that.
- The eval-1 baseline executor opened the working tree's `skills/finalize-project/SKILL.md` and declined to follow it.
- The eval-2 baseline wrote `::: data.ingest.loader` for a module it had itself reported missing. The new documenter writes no API page, so that case cannot recur.
- `repo-gaps/README.md`, the overlay's own description, lands at the union's root. The iteration-2 `with_skill` run preserved it to `docs/readme-previous.md` as a hand-written root README. That was correct behavior on a misleading fixture.
- 9.3's commit body carries a `Co-Authored-By:` line after the trailer. That is the session's default attribution, and §Project convention's **Message** allows one trailer and nothing else.

## Verdict

9.1 and 9.3 hold. 9.2 holds after one fix. Evals 1–2 equal the baseline, 5/5 and 4/4, since the 2026-09-20 log has no rate to hold them to. Iteration 1's eval 3 missed its every-expectation bar on one cell: `report`'s status was written `planned (no contract yet)`. The fix, in `agents/documenter.md`'s **Assembling**, says the cell holds the script's word and nothing after it. Iteration 2 reran eval 3, both configurations: 6/6 against 2/6.
