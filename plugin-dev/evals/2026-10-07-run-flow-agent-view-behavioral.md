# run-flow --agent across two sessions builds the right view and judges nothing, but the closing line gives no served URL

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `86c7637`): `skills/run-flow/SKILL.md` (with the phase-2 `--agent`, `--sessions` and `--branch` text; for iteration 4, also the §3 fix below), `skills/run-flow/scripts/{trace,flow}.py` · model: `claude-sonnet-5-5` for executors and graders (`model: "sonnet"`, per `run-evals` **The model**; no safeguard refusal this time) · 2026-10-07
**Set:** `evals/sets/run-flow.json` eval 3 (B2.1) · **Iteration:** `evals/workspace/run-flow/iteration-3`, `evals/workspace/run-flow/iteration-4` · **Baseline:** none (`without_skill`) · **Pass rate:** iteration 3: with_skill 7/8 (88%) vs without_skill 1/8 (12%); iteration 4: with_skill 7/8 (88%) vs without_skill 7/8 (88%)

## What was tested

B2.1 of `site/notes/0.16-audit-ledger-02-agent-view.md`. Typed as
`/plugin-dev:run-flow --agent writer --sessions 0a0d17f0-…fixt,0f10d17f`, run-flow should
build both sessions with one `trace.py view` command. It should write one
`views/writer-<date>.html` listing the four writer runs in time order, each linked to its unit
page. It should close in two lines with a served URL, and judge nothing.

## Method

- **Runs.** `run-evals`' behavioral loop, n=1 per cell, both executors in one message, on the
  `agent-view.md` harness and its `fixture.md`. One grader per run (skill-creator's
  `grader.md`), then `aggregate_benchmark`. No blind comparison: the baseline is
  `without_skill`.
- **Iteration 3** missed the pass bar on one expectation, so one fix was made inside the note's
  Files (below) and eval 3 was rerun as iteration 4.
- **Cost.** About 0.29M executor tokens and 0.30M grader tokens over both iterations.
- **Set fix** (run-evals step 7). Iteration 3's with_skill grader noted that the closing
  message's "each row opens the agent's page" disagrees with the view, where each row opens a
  unit page. The SKILL says "that run's page". The expectation now reads "each row opens that
  run's own page (its unit page, the agent's record)". This changes no verdict: the URL clause
  failed that expectation either way.

## Results

| Expectation (eval 3) | it 3 with | it 3 without | it 4 with | it 4 without |
|---|---|---|---|---|
| 1 one `trace.py view` command, no chat question | ✅ | ❌ wrote its own generator | ✅ | ✅ found `view` via the README and `--help` |
| 2 one `views/writer-<today>.html` naming both sessions | ✅ | ❌ `writer-flow.html` + `.md` | ✅ | ✅ |
| 3 the 12 columns, 4 writer rows in time order | ✅ | ❌ a bullet list | ✅ | ✅ |
| 4 links resolve, Mode `—`, Returned cells | ✅ | ❌ | ✅ | ✅ |
| 5 both workspaces complete, agent pages, `mode` keys | ✅ | ❌ | ✅ | ✅ |
| 6 two-line close with `http://127.0.0.1:<port>/views/…` and the path | ❌ path only, "no server started" | ❌ | ❌ a `file://` path and a literal `<port>` placeholder | ❌ 7 lines, no URL |
| 7 nothing judged | ✅ | ❌ listed the planted defects as findings | ✅ | ✅ |
| 8 no commit, no repo write, no server left running | ✅ | ✅ | ✅ | ✅ |
| **Total** | **7/8** | 1/8 | **7/8** | 7/8 |

**The miss.** In both iterations, the with_skill executor skipped serving the page. The run had
no browser pane, so its closing line carries a file path and no URL with a real port. The
harness allows exactly this: `evals/sets/files/run-flow/fixture.md` says "Where the target would
open a page, print the URL and the file path … If you start `python3 -m http.server` … kill it
… or do not start it, and say so." Its rules override the target's.

**The one fix.** Iteration 3 was read as ambiguity in §3 of `SKILL.md`, which said "With no
browser pane …, print that URL and the page's path instead". The fix spells it out: "serve it
all the same and print that URL and the page's path in place of opening it". Iteration 4's
executor still started no server: "not served: no browser pane in this session, so no http
server was started". Its grader quotes the fixed §3 against it. The fix did not move the
result, because the harness, not the skill, permits skipping the server. Phase 1's eval 1 run
did start a server and kill it, under the same harness, so whether the executor serves is
variance the harness leaves open.

**The baseline.** The iteration-4 `without_skill` executor found `skills/run-flow/scripts/trace.py
view` through the repo's README and `--help`, and so passed 7/8. The iteration-3 baseline wrote
its own generator and judged the writer (1/8). A no-skill run in this repo can reach the
scripts, so the baseline measures little beyond the closing message.

## Verdict

**Not met as written.** The pass bar is that every expectation passes for `with_skill`. 7/8 in
both iterations: everything the phase built holds, and the closing line's URL does not. The
view, the agent pages, the one-command build and the no-judging rule all held, in both runs.
The remaining miss sits between the harness, which lets the executor skip the server, and the
expectation, which requires a URL with a real port. Neither is in the note's Files.

Recorded as a Deviation in note 02. At review, the user chose to commit as is, with B2.1
recorded as missed because of the harness. The harness fix comes later, outside phase 2:
`evals/sets/files/run-flow/fixture.md` will require starting and then killing the server.
Eval 3 is rerun after that change.
