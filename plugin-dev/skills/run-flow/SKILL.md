---
name: run-flow
description: Draw what a plugin's workflow run actually did, from its session transcripts, as a page in the browser pane - the run's flow chart (waves of agents, one column per section, each review coloured by its verdict) with every agent clickable through to its full record, which is the prompt it was sent, every step with its full input and output, each Write's content and each Edit's old and new text, its commits with their files, and what it handed back. Use when someone asks what a run or an agent did in some chat ("what did the profiler do in that chat?", "show me the run", "open the flow for session 1493ed56", "which agents ran in the architecture migration chat?"), or to rebuild a run's chart after an audit. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), or from the marketplace repo that holds it with --plugin naming the plugin. Not for judging a run against the plugin's files (that is audit-run), and not for reading ordinary chat history or a project's own logs.
argument-hint: "[chat title words | session-id | latest] [--plugin NAME]"
---

# Seeing a run

A run is what a plugin's workflow actually did in some chat: which agents it spawned, with
what, and what each of them did step by step. This skill draws one from the session's
transcripts, as a chart where every agent opens to its full record. It judges nothing: whether
an agent followed its definition is `audit-run`'s question, and this skill never answers it.

`T` below is `python3 ${CLAUDE_SKILL_DIR}/scripts/trace.py`.

## 1. The plugin and the session

1. **The plugin.** If `.claude-plugin/plugin.json` is in the working directory, its `name` is
   **P** and the plugin directory is `.`. Otherwise, if `.claude-plugin/marketplace.json` is
   in the working directory and `--plugin NAME` was given, **P** is NAME and the plugin
   directory is that plugin's `source` in `marketplace.json`. Otherwise stop, and say that this
   skill runs inside a plugin's own subdirectory, or at the marketplace root with `--plugin`:
   the trace and its pages are written into the plugin's workspace, so there has to be one.
2. **The session** is everything in the arguments before the first flag, resolved exactly as
   `audit-run` resolves it:
   - a path to a `.jsonl`, or a session id or unique prefix: use it;
   - `latest`: the newest session that used **P**;
   - words from the chat's title, as the app's sidebar shows it: pass them to `T build`
     as the session. It resolves them when exactly one chat matches; otherwise it prints the
     matches and exits 1, and you ask as below;
   - nothing: run `T find --plugin P`, and use the one hit if there is one.

   When several chats match, ask once with `AskUserQuestion`: one option per session, at most
   four, newest first. The label is the chat's title in quotes; the description is its
   project, its span, its agents and commands, and `fork of <id8>` when it is one. A forked or
   resumed chat is a new session whose history up to the split is a copy of the original's, so
   two chats with the same title are usually a chat and its fork; `T build` on the fork still
   finds the agents spawned before the split. Never pick between them yourself: the person
   knows which one they mean.
3. **The workspace** is `<plugin dir>/evals/workspace/audit/<first 8 chars of the session id>/`,
   the same one `audit-run` uses, so a run already audited keeps its badges. The trace holds
   the project's file contents and must never be committed: when the plugin directory is
   inside a git checkout, check `git -C <plugin dir> check-ignore -q evals/workspace/audit`,
   and if nothing ignores it, add `evals/workspace/` to `<plugin dir>/.gitignore` (creating
   the file when there is none). Outside a git checkout there is nothing to ignore; say so and
   go on.

## 2. Build

`T build <session> --plugin P --out <workspace>`. It writes:

- `flow.html`, the run as a chart. Rows are waves (the agents one spawner started in one
  message, so a shaded row ran in parallel), columns are sections, and a review box is
  coloured by its verdict. Every box links to its unit's page, and a table of every unit sits
  under the chart.
- `units/U<nn>.html`, one page per spawned agent: its header (type, spawner, model, start,
  duration, tool calls, errors, hook blocks), the prompt it was sent, every step with its full
  input and output, each Write's content and each Edit's old and new text, its commits with
  their files, and what it handed back.
- `units/U<nn>.json`, the full step data those pages are drawn from, and the clipped
  `units/U<nn>.md`, `run.md`, `driver/` and `index.json` that `audit-run`'s auditors read.

Step ids (`D<n>` in the main thread, `U<nn>.S<n>` in a unit) are stable: a rebuild of a
session that has grown since appends units and steps without renumbering, so a step id in an
issue or a report still points at the same step. Rebuild on every call; it takes seconds.

Print the script's summary lines. If `index.json` shows no units and no segments, the session
never ran **P**'s workflow: say so and stop.

## 3. Serve and open

A local page opens in the browser pane only when it is served:

1. Find a free port:
   `python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1])"`.
2. Run `python3 -m http.server <port> --bind 127.0.0.1 --directory <workspace>` in the
   background, and note its pid. It serves only the workspace, and only to this machine.
3. Open `http://127.0.0.1:<port>/flow.html` in the browser pane. With no browser pane (a
   terminal or headless session), print that URL and the path to `flow.html` instead.

Then tell the user, in two lines:

1. The run: **P** and its version, the command or commands it ran, its units and waves (the
   first line of `run.md`'s **Flow** section) — and the URL, with the path to `flow.html`.
2. That each box opens that agent's page, and that `/plugin-dev:audit-run` is how a run is
   judged against the plugin's files.

When the question was about one agent ("what did the writer do?"), point at its unit page by
its `U<nn>`, and let the page answer it: retelling its steps here, or saying whether they were
right, is the judgment this skill does not make.

## What this skill never does

- Judge the run, or say whether an agent followed its definition. That is `audit-run`.
- Edit the plugin, the project or the transcripts.
- Commit anything.
- Write anywhere but the workspace, plus a `.gitignore` line when one is missing.
