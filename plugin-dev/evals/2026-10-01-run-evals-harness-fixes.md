# `run-evals` harness fixes — whole-plugin baseline snapshot, `previous` resolution, the executor prompt's fences, blind expectations

**Tested against:** uncommitted — see working-tree diff (on `b965418`; `skills/run-evals/scripts/eval_workspace.py`, `skills/run-evals/SKILL.md`, `skills/run-evals/references/eval-kinds.md`) · the negative control is the same files at `b965418` · model: mechanical rows none; probe executors `claude-sonnet-5-5` (the Agent tool's `sonnet`, recorded in every subagent transcript); the session itself `claude-fable-5-1` · Claude Code desktop app · 2026-10-01
**Set:** none — mechanical cases on scratch repos, and a behavioral probe of the executor prompt on a toy plugin. `run-evals` has no behavioral set; a set would have to run the whole loop as its target. · **Baseline:** the script and the executor prompt at `b965418` · **Pass rate:** mechanical 15/15 vs 6/15; probe 6/6 vs 2/6 (below)

## What was tested

Four defects and two smaller gaps the dev-team 2.2 ledger recorded against `run-evals`
(`dev-team/site/notes/2.2-progress.md`, the `*noticed:*` items of phases 6, 7, 8 and 10):

1. The baseline snapshot held only the target's directory, so a baseline that reads another
   file of its plugin through `${CLAUDE_PLUGIN_ROOT}` got the working tree's copy.
2. Executors could read the expectations (`eval_metadata.json`, one level above the run
   directory), and nothing told them not to.
3. Parallel executors worked in one shared scratch copy, and one deleted it.
4. `previous` resolved to HEAD, silently, in a clone with no local `main` and no
   `origin/HEAD`.
5. `blind` handed comparators the expectations that need a transcript they do not have.

The claim: each is fixed in the working tree, and each still fails at `b965418`, so the
cases can tell the two apart.

## Method

**Mechanical (M1–M9), no model.** A script in the session scratchpad builds scratch git
repos holding a toy plugin (`plug/`: skills `a` and `b`, a set whose three expectations
include two that name the transcript) and runs `eval_workspace.py` against them twice: the
working tree's copy and `git show b965418:` of it. Fifteen checks per script. The repos
are: a clone on a feature branch with skill `b` edited (M1, and M7 `blind` on its
iteration); the same with the edit committed, local `main` deleted and `origin/HEAD` unset
(M2); a repo with one branch called `work` and no remote (M3, M9); a clone on `main` in four
states (M4); a new untracked target with `baseline: previous` (M5); a repo whose root is the
plugin (M6). Then, on the real tree: `validate` over every committed set in `plugin-dev` and
`dev-team`, and `init . design-plugin --evals 1 --baseline previous` in `plugin-dev`, its
iteration deleted afterwards.

**Behavioral probe (B1), real runs, n=1 per cell.** A toy plugin in the scratchpad:
`skills/pack` (the target) says to read `${CLAUDE_PLUGIN_ROOT}/skills/style/SKILL.md` for a
heading word and an item format, to copy `fixtures/site` "to the system temp directory as
`site-work`", deleting any earlier one, to build it, and to write `RELEASE.md`. On `main`,
`style` says `CHANGES` and `* <item>`; on the branch under test it says `RELEASE` and
`- <item> (shipped)`. The target file is identical on both, which is the dev-team phase-10
case: the change is in a file the target reads. Two clones, one iteration each:

- **new**: `init` from the working tree's script, both executors given the working tree's
  executor prompt verbatim with the manifest's `target_file` and `plugin_root`.
- **old**: `init` from the script at `b965418`, both executors given that commit's prompt.

Four general-purpose subagents in one message, `model: sonnet`. What each did was read from
its subagent transcript (`…/subagents/agent-<id>.jsonl`, every `tool_use`), not from the
`transcript.md` it wrote. No grader: every check is a file's content or a recorded tool call.
About 54k tokens per executor, 20–25 s each.

One executor (old, `old_skill`) ended on an API safeguard error (`reasoning_extraction`)
after three tool calls and before writing any output. Under the rule this change adds, its
run directory was cleared and the same prompt was spawned once more; the rerun finished.
The aborted run's three calls are in its transcript and count below only where said.

## Results

Mechanical, new script against old:

| Case | Expected | Working tree | `b965418` |
|---|---|---|---|
| M1 snapshot holds the plugin's other skill at the ref | `baseline-snapshot/plug/skills/b/SKILL.md` with the old word | present, old word ✅ | absent ❌ |
| M1 snapshot leaves out `evals/` | no `evals/` | absent ✅ | absent ✅ |
| M1 snapshot keeps its manifest | `.claude-plugin/plugin.json` | present ✅ | absent ❌ |
| M1 manifest names each run's plugin root | `old_skill` → snapshot, `with_skill` → working tree, `baseline_plugin_root` | all three ✅ | no such keys ❌ |
| M1 baseline is the merge-base, no warning | the base commit, `warnings: []`, empty stderr | ✅ | ✅ |
| M7 `blind` withholds expectations naming the transcript | 1 expectation, `withheld_expectations: 2` | 1, 2 ✅ | 3 handed over ❌ |
| M7 `blind` leaks no key | no key path or field printed | ✅ | ✅ |
| M7 A and B match `key.json` | contents match | ✅ | ✅ |
| M2 only `origin/main` exists | the merge-base, not HEAD; no warning | merge-base ✅ | HEAD, silently ❌ |
| M3 no default branch at all | HEAD, exit 0, `fell back to HEAD` and `identical` in `warnings` and on stderr | both, 2 stderr lines ✅ | HEAD, no warning ❌ |
| M3 stdout is still one JSON manifest | parses | ✅ | ✅ |
| M4 identical-baseline warning | clean tree 1; an untracked file 0; an edited skill 0; only `evals/` edited 1 | 1, 0, 0, 1 ✅ | 0, 0, 0, 0 ❌ |
| M5 new target with `baseline: previous` | exit 1 naming `'none'`, no iteration left behind | exit 1, none left ✅ | exit 1, empty iteration left ❌ |
| M6 plugin at the repo root | snapshot root is `baseline-snapshot/`, other skill present, no `evals/` | ✅ | other skill absent ❌ |
| M9 `--baseline <ref>` | used as given, no warning | ✅ | ✅ |
| **Total** | | **15/15** | **6/15** |

On the real tree: `validate` exits 0 on all 12 `plugin-dev` set files (trigger sets included) and all 10 of `dev-team`'s.
`init . design-plugin --evals 1 --baseline previous` gave `baseline_ref: 07dcb19`, a
snapshot of the whole of `plugin-dev` minus `evals/`, and no warning. `07dcb19` is
`origin/main`; the local `main` this branch was cut from is `b965418`. `origin/HEAD` is
tried before a local `main`, as before this change, and `plugin-dev/` is identical at the
two commits, so nothing turned on it here.

Probe, per configuration (`with` and `old` are the two executors of each iteration):

| Check | New prompt and script | Old prompt and script |
|---|---|---|
| B1.1 the baseline's note uses the baseline's style | `old_skill`: `CHANGES` / `* alpha`. It read `baseline-snapshot/plug/skills/style/SKILL.md` ✅ | `old_skill`: `RELEASE` / `- alpha (shipped)`, the working tree's style. Its hand-back: "the baseline snapshot has no style skill, so I read it from the repo's" ❌ |
| B1.2 the working tree's note uses the working tree's style | `RELEASE` / `- alpha (shipped)` ✅ | same ✅ |
| B1.3 nothing read under the iteration outside the run directory and the snapshot | `with`: none. `old`: one `ls` of its own run directory ✅ ✅ | `with`: `cat …/with_skill/eval_metadata.json` ❌. `old`: none ✅ |
| B1.4 the fixture copy is in a directory the run made with `mktemp -d` | `…/eval.5q8UYU/site-work` and `…/eval.yQhecq/site-work` ✅ ✅ | `with`: `rm -rf <scratchpad>/site-work`, then the copy there ❌. `old` (rerun): `rm -rf $TMPDIR/site-work` ❌. The aborted run had used `<scratchpad>/site-work` too |
| B1.5 first tool call is a Read of the target file | both ✅ ✅ (not counted: the old runs did the same) | both ✅ ✅ |
| **Counted (B1.1–B1.4: one run, one run, two runs, two runs)** | **6/6** | **2/6** |

B1.5 is left out of the count: it passes on both sides, so it shows the new line does no
harm and nothing more.

## Verdict

Held for defects 1 to 5, each with a failing control at `b965418`.

- **Defect 1** is shown twice: mechanically (M1, M6) and in a real run, where the same
  target produced the old style for the baseline only when the snapshot held the whole
  plugin and the prompt named it as the plugin root.
- **Defect 2** reproduced without being provoked: the old-prompt executor opened
  `eval_metadata.json` while listing files, and said so. Neither new-prompt executor read
  outside its fence. One run each; the rule is a prompt line, not a guard, so this shows it
  is followed, not that it cannot be broken.
- **Defect 3**: all three old-prompt runs used a shared `site-work` path and ran `rm -rf` on
  it; both new-prompt runs made their own directory. They did not collide in this probe
  only because the builds took a second.
- **Defect 4**: M2 and M3. The warning is printed and in the manifest, and `init` still
  exits 0, so reading it out is on `SKILL.md` step 2, which no case here exercises.
- **Defect 5**: M7. The filter is the word `transcript`. An expectation that needs the
  transcript and does not name it is still handed over; the comparator prompt now tells it
  to leave such an expectation out rather than fail both sides, which this log does not test.

Not tested: the "first tool call is a Read" line could not fail here (the old runs read
the target first as well; the dev-team runs that did not were testers on a larger fixture);
the retry rule was followed once, by hand, on the aborted executor; the grader-staging rule
and the model section are instructions with no case. No comparator and no grader ran.

Noticed and left alone: `previous` prefers `origin/HEAD` over a local `main` that is ahead
of it, which is the state of this repo today.
