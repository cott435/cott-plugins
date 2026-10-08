---
name: run-flow
description: Draw what a plugin's workflow run actually did, from its session transcripts, as a page in the browser pane - the run's flow chart (waves of agents, one column per section, each review coloured by its verdict) with every agent clickable through to its full record, which is the prompt it was sent, every step with its full input and output, each Write's content and each Edit's old and new text, its commits with their files, and what it handed back. With --agent, every run of one agent type in time order, in one chat or, with --sessions or --branch, across several. Use when someone asks what a run or an agent did in some chat ("what did the profiler do in that chat?", "show me the run", "open the flow for session 1493ed56", "which agents ran in the architecture migration chat?", "list every reviewer run on that branch", "how many times did the profiler run, and what did each do?"), or to rebuild a run's chart after an audit. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), or from the marketplace repo that holds it with --plugin naming the plugin. Not for judging a run against the plugin's files (that is audit-run), and not for reading ordinary chat history or a project's own logs.
argument-hint: "[chat title words | session-id | latest] [--plugin NAME] [--agent TYPE] [--sessions a,b | --branch GLOB]"
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

   With `--sessions a,b` or `--branch GLOB`, no positional session is read: the sessions are
   the ones listed (each an id, a unique prefix or a path), or every session of **P** whose
   git branch matches the glob (`T find --plugin P --all` shows each session's branch). Those
   two flags list one agent type across sessions, so they need `--agent`. Without it, print
   `--sessions and --branch list one agent type across sessions: add --agent <type>` and stop,
   building nothing.

   When several chats match, ask once with `AskUserQuestion`: one option per session, at most
   four, newest first. The label is the chat's title in quotes; the description is its
   project, its span, its agents and commands, and `fork of <id8>` when it is one. A forked or
   resumed chat is a new session whose history up to the split is a copy of the original's, so
   two chats with the same title are usually a chat and its fork; `T build` on the fork still
   finds the agents spawned before the split. Never pick between them yourself: the person
   knows which one they mean.
3. **The agent type**, with `--agent TYPE`: the short name (`profiler`) or the full type
   (`dev-team:profiler`), either case; both match the same runs. Its pages are named by the
   short name, written **R** below.
4. **The workspace** is `<plugin dir>/evals/workspace/audit/<first 8 chars of the session id>/`,
   the same one `audit-run` uses, so a run already audited keeps its badges. Across sessions,
   each session gets its own, side by side under `<plugin dir>/evals/workspace/audit/`. The
   trace holds the project's file contents and must never be committed: when the plugin
   directory is inside a git checkout, check
   `git -C <plugin dir> check-ignore -q evals/workspace/audit`, and if nothing ignores it, add
   `evals/workspace/` to `<plugin dir>/.gitignore` (creating the file when there is none).
   Outside a git checkout there is nothing to ignore; say so and go on.

## 2. Build

One session, with or without `--agent`: `T build <session> --plugin P --out <workspace>`.
Across sessions: `T view --plugin P --agent <type> --root <plugin dir>/evals/workspace/audit
(--sessions a,b | --branch GLOB)`, one command that builds every session into its own
workspace and then the cross-session page; never several `T build` calls stitched by hand. A
`--branch` glob that matches nothing makes it print `no session of P on a branch matching …`
and exit 1: say so and stop.

`T build` writes:

- `flow.html`, the run as a chart. Rows are waves (the agents one spawner started in one
  message, so a shaded row ran in parallel), columns are sections, and a review box is
  coloured by its verdict. Every box links to its unit's page, and a table of every unit sits
  under the chart.
- `units/U<nn>.html`, one page per spawned agent: its header (type, spawner, model, start,
  duration, tool calls, errors, hook blocks), the prompt it was sent, every step with its full
  input and output, each Write's content and each Edit's old and new text, its commits with
  their files, and what it handed back.
- `agents/<role>.html`, one page per agent type in the run: every run of that type in time
  order, one row each (session, unit, mode, section, round, start, duration, tool calls,
  errors, files written, commits, and the first line it returned), each row opening its unit
  page. `flow.html` links them under **By agent type**.
- `units/U<nn>.json`, the full step data those pages are drawn from, and the clipped
  `units/U<nn>.md`, `run.md`, `driver/` and `index.json` that `audit-run`'s auditors read.

Step ids (`D<n>` in the main thread, `U<nn>.S<n>` in a unit) are stable: a rebuild of a
session that has grown since appends units and steps without renumbering, so a step id in an
issue or a report still points at the same step. Rebuild on every call; it takes seconds.

`T view` also writes `views/<R>-<YYYY-MM-DD>.html` under the root (today's date; a later
build the same day overwrites it): the same table across every session, each unit linking
to `../<id8>/units/U<nn>.html`, and a header line per session. It prints the page's path, then
one line per session: `<id8> · <title> · <branch> · <n> units of <type>`.

Print the script's summary lines. If `index.json` shows no units and no segments, the session
never ran **P**'s workflow: say so and stop. With `--agent` on one session, if no unit of
that type ran there (`agents/<R>.html` was not written), say so, name the types that did
run, and serve `flow.html` instead.

## 3. Serve and open

A local page opens in the browser pane only when it is served:

1. Find a free port:
   `python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1])"`.
2. Run `python3 -m http.server <port> --bind 127.0.0.1 --directory <dir>` in the
   background, and note its pid. `<dir>` is the workspace for one session, and
   `<plugin dir>/evals/workspace/audit/` across sessions, so the view's links into each
   session's workspace resolve. It serves only that directory, and only to this machine.
3. Open the page in the browser pane: `http://127.0.0.1:<port>/flow.html`; with `--agent`,
   `…/agents/<R>.html`; across sessions, `…/views/<R>-<date>.html`. With no browser pane (a
   terminal or headless session), serve it all the same and print that URL and the page's
   path in place of opening it: the URL is the page as the browser pane would show it, and
   the closing lines below give it either way.

Then tell the user, in two lines:

1. The run: **P** and its version, the command or commands it ran, its units and waves (the
   first line of `run.md`'s **Flow** section) — and the URL, with the path to `flow.html`.
2. That each box opens that agent's page, and that `/plugin-dev:audit-run` is how a run is
   judged against the plugin's files.

With `--agent`, the two lines are instead:

1. The agent type, and how many runs of it across which sessions (their `<id8>`s) — and the
   URL, with the page's path.
2. That each row opens that run's page, and that `/plugin-dev:audit-run` is how a run is
   judged against the plugin's files.

When the question was about one agent ("what did the writer do?"), point at its unit page by
its `U<nn>`, and let the page answer it: retelling its steps here, or saying whether they were
right, is the judgment this skill does not make.

## What this skill never does

- Judge the run, or say whether an agent followed its definition. That is `audit-run`.
- Edit the plugin, the project or the transcripts.
- Commit anything.
- Write anywhere but the workspace (across sessions, the session workspaces and `views/` under
  `evals/workspace/audit/`), plus a `.gitignore` line when one is missing.
