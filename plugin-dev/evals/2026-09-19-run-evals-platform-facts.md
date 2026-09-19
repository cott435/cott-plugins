# `run-evals` platform facts — where skill-creator lives, whether its trigger eval sees a plugin skill, whether its grader and static viewer work on our layout, whether subagents nest

**Tested against:** uncommitted — see working-tree diff (`skills/run-evals/`, branch `plugin-dev-0.9-evals` at `c76777a`) · skill-creator from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · Claude Code 2.1.270 · model: `claude-opus-5` (main chat, subagents, and `claude -p`) · 2026-09-19

## What was tested

The five facts phase 0 of 0.9-evals could not settle from the docs, each with its assumed
answer written down in `site/notes/0.9-evals-01-run-evals.md` before it was run: E0.1 where
skill-creator is found, E0.2 whether its `run_eval.py` detects a trigger for a plugin skill,
E0.3 whether its grader works on executor-written transcripts, E0.4 whether
`generate_review.py --static` writes a file and exits, E0.5 whether a subagent can spawn a
subagent.

## Method

- **E0.1** — globbed the three assumed locations plus `~/.claude/skills/`; `diff -rq`
  between the copies found.
- **E0.2** — a two-query set (one should-trigger log-eval request, one "capital of
  Australia") run with `python3 -m scripts.run_eval --skill-path plugin-dev/skills/log-eval
  --runs-per-query 1` from a scratch directory with its own `.claude/`. Then diagnosed by
  running the same `claude -p --output-format stream-json` command by hand and reading the
  tool calls and the init event's skill list. ~10 `claude -p` calls in all.
- **E0.3** — settled by P1-B1 (six graders on executor-written `transcript.md`); see
  `2026-09-19-run-evals-first-loop.md`.
- **E0.4** — `generate_review.py <P1-B1 iteration> --static <iteration>/review.html`, then
  checked the exit code, the file, and that nothing listened on port 3117.
- **E0.5** — one general-purpose subagent told to spawn one more whose only job was to write
  `nested-ok` to a scratch file, and not to work around a failure; read the file back.

## Results

| ID | Assumed | Observed | Held |
|---|---|---|---|
| E0.1 | found without installing at the marketplace checkout or the desktop copy; also check the plugin cache | Marketplace checkout: yes. Desktop copy: yes, at `~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/<id>/<id>/skills/skill-creator`. Plugin cache: none (not installed). The two copies differ only in `SKILL.md` and `scripts/quick_validate.py` (+ `__pycache__/`). Search order chosen: `$SKILL_CREATOR_DIR`, cache (installed), marketplace checkout, `~/.claude/skills/`, desktop copy. | yes |
| E0.2 | pointing `--skill-path` at `plugin-dev/skills/log-eval` detects the trigger | **Not as assumed.** First run: should-trigger 0/1, then 0/3. Three causes found: (1) `run_eval.py` tests the *description*, by writing it as a temporary command `<name>-skill-<uuid>` into `<project>/.claude/commands/`; with plugin-dev installed, the model invoked the real `plugin-dev:log-eval` instead (seen in the stream), which counts as not triggered. (2) With the installed plugin disabled for the run (`.claude/settings.json` `{"enabledPlugins": {"plugin-dev@cott-plugins": false}}`), a hand run invoked the temp command — but `run_eval.py` still scored 0/3, because its parallel workers each write an identically described temp command at once and the model picks a sibling's. (3) `<project>` is the nearest ancestor with a `.claude/`; from this worktree (none) that is `~`, so it would write into the user's own commands. With all three handled — scratch project dir with its own `.claude/`, installed plugin disabled there, `--num-workers 1` — it scored should-trigger 2/2, should-not 0/2. | no — works with three conditions |
| E0.3 | the grader accepts executor-written transcripts | All six `grading.json` files cite `transcript.md` or `outputs/` in their evidence; none reports a missing transcript. Graders do copy `timing.json` into `grading.json` as `grader.md` says, which hides tokens from the benchmark — handled by `eval_workspace.py finalize`. | yes |
| E0.4 | `--static` writes a standalone HTML file and exits | Exit 0, `review.html` 273 KB beginning `<!DOCTYPE html>`, nothing on port 3117. It pulls Google Fonts, so "standalone" means no server, not no network. | yes |
| E0.5 | a general-purpose subagent can spawn one more | The subagent had an Agent tool; its child wrote `nested-ok`, read back from the main chat. | yes |

## Verdict

Four of five held. E0.2 did not hold as assumed, and phase 2 depends on it: trigger evals
must run from a scratch project directory that has its own `.claude/` (so the temporary
command never lands in `~/.claude/commands/`), with the plugin under test disabled there
(otherwise its real skill wins and scores as a miss), and with `--num-workers 1` (otherwise
the parallel copies of the temporary command compete). Written into the ledger's Notes for
phase 2 and into `skills/run-evals/references/skill-creator.md`. E0.5 held, so phase 4's
executor can run `run-phase` nested; recorded in the ledger for phase 4.
