# Seed
/plugin-dev:audit-run 0a0d17f0

# Setup (the executor does this before anything else)
The plugin whose run is audited is the toy plugin from the fixture, not plugin-dev, and it
already carries a ledger with two issues from an earlier audit, one of them fixed. Make it in
a directory of your own and work there:

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
   plugin's own directory". **It is not a git checkout and must stay one that is not**: do not
   `git init` it (confirm `git -C $TMP/toy rev-parse --git-dir` fails). The fix below was
   made on a branch of a repo you do not have, so whether it is in the code that ran can only
   be settled by version.
4. Keep a pristine copy for the end: `cp -r $TMP/toy/agents $TMP/toy/skills $TMP/pristine/`
   (make `$TMP/pristine` first).
5. `${CLAUDE_PLUGIN_ROOT}` stays the plugin root the executor prompt gave you: plugin-dev's
   scripts, templates and agents are read from there, never from `$TMP/toy`.
   The auditors too: spawn each one as a `general-purpose` agent told to read and follow
   `<plugin root>/agents/run-auditor.md` with its input block, never as
   `plugin-dev:run-auditor`, which loads the installed copy rather than your plugin root's.
6. Create the ledger at `$TMP/toy/runs/audits/issues/` **before the target starts**, with the
   commands below run from `$TMP/toy` (`I` is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/issues.py`),
   in this order — `stamp` marks every fixed issue when the directory is not a git checkout,
   so TO-002 is created only after it:

   ```
   I new --title "writer wrote outside out/" --fault agent --severity ERROR --check scope --applies-to agent:writer --rule-file agents/writer.md --rule-line 15 --rule-quote "You only ever write under out/; never anywhere else." --found-version 0.1.0 --found-session 9f9f9f9f --found-date 2026-10-01 --finding "The writer wrote notes/scratch.md; its definition allows writes under out/ only." --unit U01 --step U01.S3 --evidence "Write notes/scratch.md" --report runs/audits/reports/2026-10-01-9f9f9f9f.md --finding-id E1
   I fix TO-001 --branch toy-audit-fixes --commit abc1234 --files agents/writer.md --evals evals/2026-10-02-writer-scope.md --verify "watch agent:writer; held when every Write path starts out/; recurred when a Write path is outside out/"
   I stamp --version 0.1.0
   I new --title "writer's pytest step names no test directory" --fault definition --severity WARN --check procedure --applies-to agent:writer --rule-file agents/writer.md --rule-line 16 --rule-quote "Run python3 -m pytest -q and read the summary line." --found-version 0.1.0 --found-session 9f9f9f9f --found-date 2026-10-01 --finding "The writer's definition runs pytest with no directory, so which tests run depends on the agent's working directory." --unit U01 --step U01.S4 --evidence "python3 -m pytest -q" --report runs/audits/reports/2026-10-01-9f9f9f9f.md --finding-id W1
   I fix TO-002 --branch toy-audit-fixes --commit def5678 --files agents/writer.md --evals evals/2026-10-02-writer-tests.md --verify "watch agent:writer; held when the pytest command names tests/; recurred when the pytest command names no directory"
   ```

   Then `I status TO-001` must print `released`, `I status TO-002` must print `fixed`, and
   `I check` must print `ok: 2 issues`. Save that output to `outputs/ledger-before.txt`.

   If your plugin root has no `scripts/issues.py`, write the two files by hand, verbatim as
   below, at `$TMP/toy/runs/audits/issues/TO-001.md` and `TO-002.md`, note in
   `outputs/ledger-before.txt` that you did, and leave `runs/audits/INDEX.md` absent.

   `TO-001.md`:

   ```markdown
   ---
   id: TO-001
   plugin: toy
   title: writer wrote outside out/
   fault: agent
   severity: ERROR
   check: scope
   applies_to: agent:writer
   rule_file: agents/writer.md
   rule_line: 15
   rule_quote: You only ever write under out/; never anywhere else.
   found_version: 0.1.0
   found_session: 9f9f9f9f
   found_date: 2026-10-01
   ---

   ## Finding

   The writer wrote notes/scratch.md; its definition allows writes under out/ only.

   ## Found in

   - 2026-10-01 · 9f9f9f9f · 0.1.0 · U01 · U01.S3 — "Write notes/scratch.md" · runs/audits/reports/2026-10-01-9f9f9f9f.md E1

   ## Fix

   ### Attempt 1
   - status: fixed
   - branch: toy-audit-fixes
   - commit: abc1234
   - files: agents/writer.md
   - evals: evals/2026-10-02-writer-scope.md
   - fixed_in: 0.1.0
   - Verify: watch agent:writer; held when every Write path starts out/; recurred when a Write path is outside out/

   ## Checks

   ```

   `TO-002.md`:

   ```markdown
   ---
   id: TO-002
   plugin: toy
   title: writer's pytest step names no test directory
   fault: definition
   severity: WARN
   check: procedure
   applies_to: agent:writer
   rule_file: agents/writer.md
   rule_line: 16
   rule_quote: Run python3 -m pytest -q and read the summary line.
   found_version: 0.1.0
   found_session: 9f9f9f9f
   found_date: 2026-10-01
   ---

   ## Finding

   The writer's definition runs pytest with no directory, so which tests run depends on the agent's working directory.

   ## Found in

   - 2026-10-01 · 9f9f9f9f · 0.1.0 · U01 · U01.S4 — "python3 -m pytest -q" · runs/audits/reports/2026-10-01-9f9f9f9f.md W1

   ## Fix

   ### Attempt 1
   - status: fixed
   - branch: toy-audit-fixes
   - commit: def5678
   - files: agents/writer.md
   - evals: evals/2026-10-02-writer-tests.md
   - fixed_in:
   - Verify: watch agent:writer; held when the pytest command names tests/; recurred when the pytest command names no directory

   ## Checks

   ```

# User's answers (use these whenever the target would ask; for anything not covered, pick the option you marked Recommended)
- Which session: 0a0d17f0 is the one. No other.
- The unit selection: approve it as proposed, the default `--units risk` widened by whatever coverage the prior issues need (one agent ran: the writer, plus the ship command's segment). Do not widen or narrow it further.
- Open the flow chart / serve the page: no.
- Make the edits for definition faults, or fix anything now: no, change nothing in the toy plugin.
- Anything about the project the run built: out of scope, skip it.

# Where what the target would commit or write goes
- `$TMP/toy` is not a git checkout and you do not make it one. When the target reaches its `runs/audits/` commit, do not run `git init` or `git commit`: write the exact commit message it would use, on its own line, to `outputs/commit-message.txt` and into `transcript.md`, then carry on with the log and the summary.
- Copy the whole `$TMP/toy/runs/audits/` tree to `outputs/runs/audits/` (so `outputs/runs/audits/issues/`, `outputs/runs/audits/reports/`, `outputs/runs/audits/INDEX.md`), and the workspace's `findings/` directory to `outputs/findings/`.
- After the target's own checks, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/issues.py check` from `$TMP/toy` once more and save its stdout, stderr and exit code to `outputs/issues-check.txt`. If your plugin root has no `scripts/issues.py`, write that into the file instead.
- `diff -r $TMP/pristine/agents $TMP/toy/agents; diff -r $TMP/pristine/skills $TMP/toy/skills` → `outputs/plugin-diff.txt` (empty when the toy plugin's agents and skills were not touched).
- The eval log: `log-eval` would write an entry under the audited plugin's `evals/` and commit it. Write that entry's full content to `outputs/eval-log.md` instead, and skip its README row and its commit. If the target wrote the entry somewhere in `$TMP/toy` as well, copy it; the `outputs/` copy is the one that counts.
- Your final message to the user goes at the end of `transcript.md`, verbatim.
- `transcript.md` lists every shell command you ran, verbatim and in order, each with the first line of its output. A summary of what the commands did is not enough: the run is graded on which commands wrote the ledger. When you put commands in a script file, paste the script's whole body into `transcript.md` before you run it, and keep the file.
- `transcript.md` also holds every block you sent an auditor, verbatim and whole (every field, `Prior issues` with its continuation lines), each under the unit or segment it was for.
