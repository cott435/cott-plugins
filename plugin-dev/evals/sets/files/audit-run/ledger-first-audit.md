# Seed
/plugin-dev:audit-run 0a0d17f0

# Setup (the executor does this before anything else)
The plugin whose run is audited is the toy plugin from the fixture, not plugin-dev. Make it
in a directory of your own and work there:

1. `TMP=$(mktemp -d)` (under the session scratchpad when there is one). Run
   `python3 <plugin-dev dir>/evals/fixtures/audit-run/make_session.py $TMP`, where
   `<plugin-dev dir>` is the working tree's plugin-dev directory (the one holding
   `evals/sets/`); the fixture lives there whichever plugin root you were given. It writes
   the toy plugin at `$TMP/toy` (`.claude-plugin/plugin.json`: name `toy`, version 0.1.0,
   agent `toy:writer`, skill `toy:ship`) and the recorded session
   `0a0d17f0-0000-4000-8000-00000000fixt` under `$TMP/session/`.
2. `export AUDIT_RUN_PROJECTS=$TMP` so the trace scripts find the session. The audited
   project `/tmp/toy-project` does not exist; that is normal for a finished run.
3. `$TMP/toy` is the plugin directory: `cd` there for everything the target does "from the
   plugin's own directory". It is your own copy, not the repo, so git is allowed in it and
   nowhere else: `git init` it, `git add -A && git commit -m "fixture"` once, before the
   target starts. Any commit the target makes lands there and only there.
4. `${CLAUDE_PLUGIN_ROOT}` stays the plugin root the executor prompt gave you: plugin-dev's
   scripts, templates and agents are read from there, never from `$TMP/toy`.

# User's answers (use these whenever the target would ask; for anything not covered, pick the option you marked Recommended)
- Which session: 0a0d17f0 is the one. No other.
- The unit selection: approve it as proposed, the default `--units risk` (one agent ran: the writer, plus the ship command's segment). Do not widen or narrow it.
- Open the flow chart / serve the page: no.
- Make the edits for definition faults still at HEAD: no, change nothing in the toy plugin.
- Anything about the project the run built: out of scope, skip it.

# Where what the target would commit or write goes
- The `audits/` commit happens for real in `$TMP/toy`; nothing else is committed. When done, save `git -C $TMP/toy log --stat` to `outputs/git-log.txt` and `git -C $TMP/toy status --short` to `outputs/git-status.txt`.
- Copy the whole `$TMP/toy/audits/` tree to `outputs/audits/` (so `outputs/audits/issues/`, `outputs/audits/runs/`, `outputs/audits/INDEX.md`), and the workspace's `findings/` directory to `outputs/findings/`.
- After the target's own checks, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/issues.py check` from `$TMP/toy` once more and save its stdout, stderr and exit code to `outputs/issues-check.txt`. If your plugin root has no `scripts/issues.py`, write that into the file instead.
- The eval log: `log-eval` would write an entry under the audited plugin's `evals/` and commit it. Write that entry's full content to `outputs/eval-log.md` instead, and skip its README row and its commit. If the target wrote the entry somewhere in `$TMP/toy` as well, copy it; the `outputs/` copy is the one that counts.
- Your final message to the user goes at the end of `transcript.md`, verbatim.
