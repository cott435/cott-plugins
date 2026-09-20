# Using skill-creator

`run-evals` owns what to test and where results live; skill-creator owns the grader, the
benchmark and the viewer. Nothing of it is copied into plugin-dev — it is used where it is
found, and when it is not found, `run-evals` grades inline (see `SKILL.md`, **When
skill-creator is missing**).

## Finding it

`python3 ${CLAUDE_SKILL_DIR}/scripts/eval_workspace.py locate-skill-creator` prints the
first directory holding both `agents/grader.md` and `scripts/aggregate_benchmark.py`, in
this order (the newest match wins within one pattern), and exits 1 when none does:

1. `$SKILL_CREATOR_DIR` — an explicit override.
2. `~/.claude/plugins/cache/*/skill-creator/*/skills/skill-creator` — the plugin installed
   and enabled from a marketplace; the copy the user actually runs.
3. `~/.claude/plugins/marketplaces/*/plugins/skill-creator/skills/skill-creator` — the
   marketplace checkout. It is there whenever the marketplace is added, installed or not;
   the files are usable either way, since `run-evals` reads them rather than invoking the
   skill.
4. `~/.claude/skills/skill-creator` — a user-level skill.
5. `~/Library/Application Support/Claude/**/skills/skill-creator` — the Claude desktop
   app's own copy, under `local-agent-mode-sessions/skills-plugin/<id>/<id>/`.

On 2026-09-19 (0.9-evals E0.1) this machine had 3 and 5, not 2.

## What is used

| File | Used for |
|---|---|
| `agents/grader.md` | the grader's instructions, given to a general-purpose subagent per run |
| `agents/comparator.md` | the blind comparator — which of two outputs is better, without being told which is the working tree's |
| `scripts/aggregate_benchmark.py` | `benchmark.json` and `benchmark.md` for an iteration — run as `python3 -m scripts.aggregate_benchmark` from the skill-creator directory |
| `eval-viewer/generate_review.py` | the review page, served or `--static`, always through `eval_workspace.py review` |
| `scripts/run_eval.py`, `scripts/run_loop.py` | trigger evals and the description optimizer — see below |

Its scripts import `scripts.utils`, so they run as modules from the skill-creator directory
(`cd <sc> && python3 -m scripts.<name>`) or with `PYTHONPATH=<sc>`.

### Trigger evals: the mechanism

0.9-evals E0.2 found `run_eval.py --skill-path <plugin>/skills/<name>` detects triggers
directly — no copy into a project's `.claude/skills/` — but only under three conditions,
and phase 2 chose that mechanism: the script tests the description as a temporary
command, so it runs from a scratch project with its own `.claude/` (run as a module with
`PYTHONPATH=<skill-creator>`, never from the skill-creator directory), with the plugin
under test disabled in that project's `.claude/settings.json`, and with `--num-workers 1`.
`run_loop.py` calls `run_eval` the same way and needs the same three. `SKILL.md` **Trigger
evals** has the commands.

## Layout its scripts expect

- `aggregate_benchmark.py <dir>` globs `<dir>/eval-*`, then every subdirectory that has a
  `run-*` child as a configuration, then `run-*/grading.json`. Configuration names become
  its labels — hence `with_skill`, `old_skill`, `without_skill`. When the layout is off it
  prints a warning at most and **reports 0%** rather than failing: a benchmark with a 0% row
  is checked against the directory tree before it is believed.
- It reads `eval_id` from `eval-*/eval_metadata.json` (the eval level), and tokens and time
  from `run-*/timing.json` only when `grading.json` has no `timing` block. Its grader copies
  one in (`agents/grader.md` says to), and then tokens fall back to
  `execution_metrics.output_chars`, or 0 — so `eval_workspace.py finalize` removes the copy
  before aggregating.
- Its delta is `configs[0] − configs[1]` in directory order: `with_skill` − `without_skill`
  is the right way round, but `old_skill` sorts first, so against a changed target the delta
  is baseline − target and its sign is inverted.
- `grading.json` needs `expectations[]` with `text`, `passed`, `evidence`, and `summary`
  with `passed`, `failed`, `total`, `pass_rate`; the viewer requires the same field names.
- `generate_review.py <dir>` treats every directory with an `outputs/` child as a run, and
  reads its prompt from `eval_metadata.json` in the run directory or its parent — the
  configuration level. That is why `eval_metadata.json` is written twice, at the eval level
  and the configuration level. Files named `transcript.md`, `user_notes.md` and
  `metrics.json` inside `outputs/` are hidden from the viewer.
- `generate_review.py` inlines every output file into a `<script>` block with
  `json.dumps`, which does not escape `</script>`. An output that is itself an HTML page
  with a script ends the viewer's script early: the page shows no prompt and no outputs,
  and the console says `SyntaxError: Invalid or unexpected token`. `eval_workspace.py
  review` runs the viewer unmodified with `</` escaped in that data.
- `generate_review.py --static <file>` writes one standalone HTML file and exits; without
  it, it serves on port 3117 (killing whatever holds it) and writes `feedback.json` into
  the workspace when the reviewer submits.
- `agents/comparator.md` names its inputs `output_a_path`, `output_b_path`, `eval_prompt`
  and `expectations` (the last optional), and writes `comparison.json` with `winner`
  (`"A"`, `"B"` or `"TIE"`), `reasoning`, `rubric` and `output_quality` per side, plus
  `expectation_results` when expectations were given. It generates its own rubric from the
  task, so it needs the prompt, not just the two directories. `SKILL.md` **Blind
  comparison** has the prompt; `eval_workspace.py blind` stages the two directories.
- `run_eval.py` writes a temporary command into `<project>/.claude/commands/`, where
  `<project>` is the nearest ancestor of the working directory that has a `.claude/`. From
  a repo with none, that is `~` — it writes into the user's own commands. See **Trigger
  evals: the mechanism**.

## Known differences between copies

The marketplace checkout and the desktop app's copy found on 2026-09-19 differed in
`SKILL.md` and `scripts/quick_validate.py` only (plus a `__pycache__/` in the desktop copy);
every file `run-evals` uses was identical. If a later copy differs in a used file, the eval
log names the path it ran from.
