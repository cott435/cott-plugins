# The run-package driver evals' runner

Runs `evals/sets/run-package.json` evals 1, 2, 3, 5 and 6 as real headless driver sessions
(`claude -p "/dev-team:run-package …"`), the way `run-evals` cannot from inside a chat: an
executor subagent acting as the driver would spawn the installed `dev-team` agents, not the
ones under test, and its hooks would key on the plugin directory instead of the fixture copy.
Evals 7 to 10 turn on a question and run no agent; they run in `run-evals`' ordinary executor
loop. Eval 4 has its own harness (`evals/sets/files/run-package/harness-4-end-to-end.md`).

Kept here, not under `evals/sets/files/`, which executors may read, and not under
`evals/workspace/`, which is never committed.

## The two commands

From the plugin directory, after `eval_workspace.py init . run-package --evals 1,2,3,5,6
--baseline <ref>` has made the iteration:

```
bash evals/runners/run-package/run.sh <eval id> <with_skill|old_skill> <plugin dir> <run dir>
python3 evals/runners/run-package/post.py <run dir> <repo copy>
```

- `<plugin dir>` is the plugin the session loads with `--plugin-dir`: the working tree (`.`)
  for `with_skill`, the iteration's `baseline-snapshot/<plugin>/` for `old_skill`. The
  manifest's `plugin_root` for the run is the value.
- `<run dir>` is the manifest's `run_dir`, `…/eval-<id>-<name>/<config>/run-1`.
- `run.sh` calls `post.py` itself when the session exits; run `post.py` by hand only to
  rebuild the outputs of a run whose copy still exists (`runner.json` names it).
- The sessions are long (15 to 25 minutes for a walk to DONE); run each in the background, and
  several at once: every run makes its own copy.

Environment: `RUN_PACKAGE_MODEL` (default `claude-sonnet-5-5`, the full ID: `--model sonnet`
in a headless session is a different model) and `RUN_PACKAGE_TMP` (where the copy is made;
default `$TMPDIR`; a session scratchpad is the right place).

## What `run.sh` does

1. A fresh `evals/fixtures/two-package/reset.sh` copy in a `mktemp -d` directory, seeded and
   committed as the eval's harness sheet says under **Before starting**. Seeds and sheets are
   always the working tree's, since a baseline snapshot has no `evals/`.
2. A copy of `<plugin dir>` without `evals/` beside the fixture copy, which is what the session
   loads: Claude Code refuses a Write inside a `--plugin-dir` directory as a sensitive file, and
   for `with_skill` the run's `outputs/` is inside the working tree. `runner.json` names both.
3. `.claude/settings.json` in the copy disabling an installed `dev-team@cott-plugins`, so only
   `<plugin dir>` is loaded; `.claude/` goes in the copy's `.git/info/exclude`, so the run gate
   sees a clean tree.
4. An appended system prompt (`<run dir>/system-prompt.md`): a headless session has no
   `AskUserQuestion`, so a question is appended to `outputs/interview.md` and answered from the
   harness sheet's **Answers**, which is copied in, with **Where the walk ends** when the sheet
   has one (evals 5 and 6). It holds no expectation.
5. From the copy: `claude -p "<command>" --plugin-dir <that copy> --model <model>
   --permission-mode acceptEdits --add-dir <run dir>/outputs --disallowedTools AskUserQuestion
   --output-format stream-json --verbose --allowedTools Agent Bash Read Write Edit Glob Grep
   Skill TodoWrite WebSearch WebFetch`, into `<run dir>/stream.jsonl`. The session's cwd is the
   copy, so the plugin's hooks — the stop gate, both guards, the inbox sync — fire for real.
6. Beside it, harness 4's watcher keeps every gate-record version in `outputs/gate-history/`.
7. `<run dir>/runner.json`: the eval, the configuration, the copy, the seed commit, the exit
   code and the wall time. Then `post.py`.

## What `post.py` writes

Derived mechanically from `stream.jsonl`, the session's subagent transcripts
(`~/.claude/projects/*/<session id>/subagents/`) and the copy, read-only. Nothing it writes
holds an expectation.

| File | What it is |
|---|---|
| `transcript.md` | the driver's every text and tool call in order, with inputs and results (an Agent call's result is its return's first line), the final message, then `--- harness copies ---` |
| `outputs/summary.md` | the session's final message, verbatim |
| `outputs/spawns.md` | every driver Agent call: batch (one assistant message id is one batch), `subagent_type`, `run_in_background`, the `Section:`/`Scaffold:`/`Round:`/`Focus:`/`Letter:` lines, the prompt verbatim, the return's first line (the whole return for `design-gap` and `spec-change`); each `status.py` run between batches |
| `outputs/status-log.txt` | every `status.py` call the driver made, with its output |
| `outputs/status-final.txt` | `status.py <pkg>` once more, with the session's own plugin |
| `outputs/driver-bash.md` | every Bash command the driver ran |
| `outputs/returns.md` | per agent run: the first line of the report its caller received, and of its last assistant text |
| `outputs/git-log.txt`, `git-oneline.txt`, `git-status.txt` | the copy's commits after the seed (`%H%n%B --stat`), its one-line log, its `status --porcelain` |
| `outputs/repo/` | the copy's `docs/`, `tests/`, `packages/` and `.dev-team/{gate,stop}/` |
| `outputs/gate-history/`, `outputs/gates.md` | every gate-record version with its modification time; per batch of two or more implementers, their gate windows and an `F4:` line |
| `outputs/cost.json` | the session's cost, duration, per-model usage and token sum |

## The model

The model a session ran on is read from the transcript's `model` field — the assistant records
`post.py` lists in `transcript.md`'s header and `cost.json`'s `models_seen` — not from the
flag. Claude Code 2.1.283 prints `unrecognized_model` for `claude-sonnet-5-5` on stderr and
runs it.
