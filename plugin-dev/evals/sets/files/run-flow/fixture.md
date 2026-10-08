# Setup (the executor does this before anything else, after reading the target)
The run to draw is a planted fixture, not a real chat. Build it first:

1. `mktemp -d` a directory of your own (`mktemp -d <scratchpad>/eval.XXXXXX` when the session
   has a scratchpad). Write down the absolute path it printed; below it is `$TMP`. Shell state
   does not survive between your commands, so write the real path into every command rather
   than relying on a variable.
2. `python3 <repo>/plugin-dev/evals/fixtures/audit-run/make_session.py $TMP` — the script is
   `evals/fixtures/audit-run/make_session.py` under the plugin-dev directory of the repo named
   in your instructions. It writes `$TMP/toy` (a toy plugin with `.claude-plugin/plugin.json`),
   `$TMP/session/` and `$TMP/flow-session/` (the recorded chats).
3. The recorded chats are found only through the environment: prefix every `trace.py` command
   with `AUDIT_RUN_PROJECTS=$TMP` (the absolute path). Without it the scripts look in
   `~/.claude/projects` and find nothing of the toy plugin.
4. Work from `$TMP/toy` as the plugin directory: run every command the target gives with
   `cd $TMP/toy && …`, so `.claude-plugin/plugin.json` is in the working directory and the
   plugin is `toy`. The target's own scripts stay where they are, under the plugin root your
   instructions name; only the working directory is `$TMP/toy`.
5. The workspace the target writes goes where the target says, under `$TMP/toy` — that is the
   fixture copy, not the repo, so it is the one place outside `outputs/` you may write. Nothing
   under the repo is written, including its `evals/workspace/`.

# Browser and server
There is no browser pane in this session. Serve the page exactly as the target says all the
same: find a free port, start `python3 -m http.server <port> --bind 127.0.0.1 --directory
<dir>` in the background, note its pid, and confirm the page answers (`curl -s -o /dev/null
-w '%{http_code}' http://127.0.0.1:<port>/<page>` prints 200). Where the target would open the
page, print that `http://127.0.0.1:<port>/…` URL and the file path in your final message
instead. Then kill the server by its pid before your final message, and say in
`transcript.md` that you did. The URL in the final message is the one you served, even though
the server is gone by the time anyone reads it. Leave no server running.

# Harness override for every run-flow eval
Write the target's final chat message, exactly as you would say it to the user, to
`outputs/chat.md` (also in `transcript.md`). Do not commit, branch, edit any plugin, project or
transcript file, or write anywhere in the repo.
