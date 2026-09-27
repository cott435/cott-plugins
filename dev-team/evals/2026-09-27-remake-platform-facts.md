# Platform facts for the remake (phase 0, PF-1…PF-5) — `SubagentStop` gate, loop guard, main-thread fan-out, plugin skill listing, concurrent commits

**Tested against:** `8641af4` (`site/notes/remake-design.md`, Platform facts table, `assumed`
rows), with stub agents and a probe hook in a scratch copy of the plugin, not the plugin's own
agents · model: `claude-sonnet-5` (the CLI default headless; every stub `model: inherit`) ·
Claude Code `2.1.270` · git `2.48.1` · 2026-09-27
**Set:** none — `platform-fact` evals are not part of a target's run (`run-evals`
`references/eval-kinds.md`); the assumed answers were written in the design before the test.

## What was tested

The five `assumed` rows of the design's Platform facts table, which phases 2, 4 and 8 build on:

- **PF-1** `SubagentStop` exit 2 prevents the subagent from stopping and its stderr reaches it.
- **PF-2** The loop guard: a marker file lets the stop through; a counter under
  `${CLAUDE_PLUGIN_DATA}` keyed by `agent_id` persists across the same agent's stop attempts;
  `stop_hook_active` in the input says whether this stop is already a retry.
- **PF-3** Main-thread parallel Agent calls in one message run concurrently and all return as
  that message's results.
- **PF-4** `ls ${CLAUDE_PLUGIN_ROOT}/skills` from an agent body lists the plugin's skills, and a
  colliding project skill is reported.
- **PF-5** Two subagents committing concurrently collide on `.git/index.lock`, and a retry of up
  to ten two-second waits lands both commits.

## Method

Real headless runs. The plugin's `plugin.json` and `skills/` were copied to a scratchpad
(`…/scratchpad/pf/plug/dev-team`), with four stub agents in place of the real ones
(`implementer`, `designer`, `tester`, `architect`, each a few lines saying exactly what to do)
and a probe `hooks/hooks.json`: `SubagentStop`, matcher `^dev-team:implementer$`, exec form
`python3 ${CLAUDE_PLUGIN_ROOT}/hooks/gate_probe.py`. The script logs its input and environment
to a JSONL file; deletes `.dev-team/stop` in `cwd` and exits 0 if present; otherwise it
increments `${CLAUDE_PLUGIN_DATA}/attempts-<agent_id>` and exits 2 until the count reaches 3,
with stderr `GATE-PROBE attempt <n>: … create the file gate-seen-<n>.txt …`. That instruction
has an effect on disk, so a file that exists proves the stderr reached the agent. The script
was first piped four recorded inputs (three attempts, a marker, malformed JSON) and gave the
expected exit codes.

Each run: a fresh `git init` project, `claude -p "<prompt>" --plugin-dir <copy> --settings
'{"enabledPlugins":{"dev-team@cott-plugins":false}}' --permission-mode bypassPermissions
--output-format stream-json --verbose`. The installed `dev-team` was disabled so only the copy
answered to `dev-team:*`; the `init` event lists the copy as `dev-team@inline` and exactly the
four stub agents. Evidence came from the stream-json (main-thread `tool_use` and `tool_result`
order), the subagent transcripts under `~/.claude/projects/<proj>/<session>/subagents/`, the
hook log, and the files on disk. It did not come from the model's own summary.

| Run | Fact | Main-thread prompt, in short | Cost |
|---|---|---|---|
| a | PF-1, PF-2 counter | one `dev-team:implementer`, `run_in_background: false`: write `impl.txt`, then stop | $0.26 |
| b | PF-2 marker | same, also write `.dev-team/stop` before stopping | $0.24 |
| c | PF-3 | two `dev-team:designer` in one message, both `false`; each stub sleeps 20 s between two timestamps it writes to `design-<a,b>.md`; then `ls; cat` | $0.28 |
| d | PF-4 | one `dev-team:architect` whose body says `ls ${CLAUDE_PLUGIN_ROOT}/skills`, `ls .claude/skills`, and report collisions; the project has `.claude/skills/status/` (collides) and `house-style/` | $0.25 |
| e1 | PF-5 | two `dev-team:tester` in one message; each writes a file, then `git add <f> && git commit -m …`, retrying on `index.lock`; the project's `pre-commit` hook sleeps 8 s to widen the window | $0.30 |
| git-only | PF-5 | no model: the same two commits from a shell, commit A in the background with a 4 s `pre-commit`, then `git add`/`git commit` B 1 s later, once plain and once with `-- <path>` | — |
| e2 | PF-5 fix | as e1, but the stub commits with `git commit -m … -- <file>`; `pre-commit` 15 s | $0.13 |
| e3 | PF-5 retry | as e2, plus a shell watcher that holds `.git/index.lock` for 7 s the moment `one.txt` appears | $0.13 |

Total ≈ $1.58.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| PF-1: exit 2 keeps the subagent running | a second turn after the hook's stderr | Subagent transcript: final text `Created …/impl.txt containing "built".`, then a user turn `Stop hook feedback: [python3 …/gate_probe.py]: GATE-PROBE attempt 1: …`, then a `Write` of `gate-seen-1.txt`. It repeats for attempt 2. `gate-seen-1.txt` and `gate-seen-2.txt` exist | ✅ |
| PF-1: what the parent receives | (not assumed) | The main thread's `tool_result` is the **last** turn's text only: `Created gate-seen-2.txt containing "seen-2".` The pre-gate reply is lost | finding |
| PF-2: counter keyed by `agent_id` persists | 1, 2, 3 for one agent | Hook log: the same `agent_id` `ada83ca2a510745ac` on all three stops, `attempt` 1 → 2 → 3, decisions `exit 2`, `exit 2`, `exit 0 (attempt 3)`. The file under `${CLAUDE_PLUGIN_DATA}` held `3` after the session | ✅ |
| PF-2: `${CLAUDE_PLUGIN_DATA}` in a hook | set, exported | `/Users/connorott/.claude/plugins/data/dev-team-inline` for a `--plugin-dir` plugin, created on first use. `CLAUDE_PLUGIN_ROOT` = the copy's path | ✅ |
| PF-2: `stop_hook_active` | present; true on a retry | present in the input: `false` on attempt 1, `true` on attempts 2 and 3 | ✅ |
| PF-2: marker lets the stop through | one hook call, marker deleted, no counter | run b: one hook call, `marker_present: true`, `exit 0 (marker, deleted)`; `.dev-team/` is empty afterwards; no `gate-seen-*` file; no counter written | ✅ |
| PF-2: other input fields | (not assumed) | `SubagentStop` input keys: `agent_id`, `agent_transcript_path`, `agent_type`, `background_tasks`, `cwd`, `effort`, `hook_event_name`, `last_assistant_message`, `permission_mode`, `prompt_id`, `scratchpad_dir`, `session_crons`, `session_id`, `stop_hook_active`, `transcript_path` | finding |
| PF-3: one message, concurrent, both returned | two `tool_use` in one assistant message; both results before the next call; overlapping lifetimes | Both `Agent` calls share one message id and both are `run_in_background: false`. Both `tool_result`s (`Result: done …design-a.md`, `…design-b.md`) come before the next `tool_use` (`ls; cat`). Timestamps: a 830.67–850.69, b 831.13–851.15, which is 19.6 s of overlap in 20 s | ✅ |
| PF-4: listing from an agent body | plugin skills listed, collision reported | The agent quoted `PLUGIN-SKILLS-DIR: /private/tmp/…/pf/plug/dev-team/skills`, already substituted. Its Bash call was `ls "/private/tmp/…/plug/dev-team/skills"` and returned the 29 directories. Reply: `Plugin skills: 29`, `Project skills: house-style`, `Colliding: status` | ✅ |
| PF-5 e1: concurrent plain commits | a lock collision, then a retry, then two commits | **No lock error.** Tester two ran `git add two.txt && git commit`. While its `pre-commit` ran (835.9–843.9), tester one's `git add one.txt` **succeeded** (15:27:23.3). Two's commit `96d49ee two: add two.txt` then contained **both** `one.txt` and `two.txt`. One's commit failed with `nothing to commit`. `git log`: one commit, wrong message for one file | ❌ |
| PF-5 git-only, plain | — | The hook saw `index.lock` absent and `GIT_INDEX_FILE=.git/index`. B's `git add` exited 0. A's commit contains both files, and B's commit exits 1 with `nothing to commit` | reproduces e1 |
| PF-5 git-only, `-- <path>` | — | The hook saw `.git/index.lock` held, with `GIT_INDEX_FILE=.git/next-index-<pid>.lock`. B's `git add` failed with `fatal: Unable to create '…/.git/index.lock': File exists.` A's commit contains `two.txt` only | the lock the rule assumes |
| PF-5 e2: `git commit … -- <file>` | two commits, one file each | `ee92e1f one: add one.txt` (one.txt), `e221bfd two: add two.txt` (two.txt), clean tree. The commits did not overlap (19.2 vs 22.4), so neither agent saw the lock | ✅ (no collision) |
| PF-5 e3: retry under a held lock | the agent retries and lands its commit | Tester one got `fatal: Unable to create '…/.git/index.lock': File exists.`, ran `sleep 2 &&` the same command twice, and the third attempt landed `7c42f5d one: add one.txt` (one.txt). It returned `retries=2` and quoted the error. Tester two landed `b54544f` (two.txt). The tree is clean | ✅ |

## Verdict

**PF-1 to PF-4 hold as assumed.** Phase 2 can build `gate_on_stop.py` as designed: exit 2
blocks the stop, and the stderr arrives as a `Stop hook feedback:` user turn. The per-`agent_id`
counter under `${CLAUDE_PLUGIN_DATA}` and the `.dev-team/stop` marker both work, and
`stop_hook_active` is present. Two findings the design did not assume, for phases 2, 4 and 8:

- **The parent gets only the last turn.** After a gate retry, the driver receives the text of
  the agent's final turn, not its first reply. The `Result:` line the driver branches on is
  lost unless the agent repeats it. The gate's exit-2 text, and the implementer's procedure,
  must say to end with the full return message again, starting `Result:`.
- **The counter outlives the session.** Nothing deletes it, so the hook should remove
  `attempts-<agent_id>` when it lets a stop through. The input also carries
  `last_assistant_message` and `agent_transcript_path`, which the gate could use instead of
  re-deriving what the agent said.

**PF-5 is false as stated.** Two concurrent `git add X && git commit` runs do not collide on the
index lock in git 2.48. A plain `git commit` holds no lock while its hooks run, and it re-reads
the shared index before writing the tree. So a parallel agent's `git add` lands in the other
agent's commit, with no error either agent can see. The result is one commit that carries both
files and one agent's message, and an `nothing to commit` failure for the other. The design's
retry rule never fires. The fix is to commit with an explicit pathspec: `git add <paths>`, then
`git commit -m … -- <paths>`. That commits only the named paths, whatever else is staged, and it
holds `.git/index.lock` for the whole commit. A parallel `git add` or `git commit` then fails
with the `index.lock` error, and the two-second retry up to ten times does land it (e3: two
retries, both commits correct). The same applies to the gate's `git commit --amend --no-edit`,
which phases 2 and 4 plan: without `-- <paths>` it would also sweep in anything another agent
has staged. Recorded as a Deviation in `remake-00-overview.md` and in the ledger's phase 2 and
4 rows. The design is not edited.

Limits: one run per case, on one model. These are platform and git facts, not behavioral ones.
The e3 collision was forced by a shell process holding the lock, not by a second agent. e1 shows
an agent-on-agent collision does happen, but its timing cannot be controlled. PF-3 used
10-line stubs. A real designer's longer run only widens the overlap.
