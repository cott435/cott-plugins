# run-auditor eval 1 — prior issues on the planted unit

Scripted setup for the executor. run-auditor asks the user nothing, so there are no answers
to script; this sheet says how the trace is built, the exact block the auditor is given, and
what goes into the run directory.

`<plugin-dev>` below is the plugin-dev working tree this file lives in: the directory four
levels above it (this file is `<plugin-dev>/evals/sets/files/run-auditor/prior-issues.md`).
Use its scripts in both configurations, `with_skill` and `old_skill`: they build the fixture
and are not under test. The agent file you follow is the one the executor prompt named, and
nothing here changes that.

## Build the trace

In a directory of your own, never one another run could share:

    TMP=$(mktemp -d)        # mktemp -d <scratchpad>/eval.XXXXXX when the session has one
    python3 <plugin-dev>/evals/fixtures/audit-run/make_session.py $TMP
    python3 <plugin-dev>/skills/run-flow/scripts/trace.py build \
        $TMP/session/0a0d17f0-0000-4000-8000-00000000fixt.jsonl --plugin toy --out $TMP/ws

(Before phase 1 of 0.16-audit-ledger the script was `skills/audit-run/scripts/trace.py`; this
set runs from phase 7, where it has moved.) The toy plugin is then at `$TMP/toy` and the
workspace at `$TMP/ws` (`index.json`, `run.md`, `driver/seg-1.md`, `units/U01.md`,
`units/U01.system.md`). The project the session ran in, `/tmp/toy-project`, does not exist and
must not be created: its history is gone, as a real project's may be, and the agent's own
Inputs say what to do when git cannot settle a question.

## The spawn block

Act on this block exactly, with `$TMP` replaced by the directory you made, so that every path
in it is absolute. It is the block the eval's prompt carries, repeated here so the sheet is
complete on its own:

    Mode: unit
    Trace: units/U01.md
    Workspace: $TMP/ws
    Definition: $TMP/toy/agents/writer.md
    Plugin root: $TMP/toy
    Spawner: driver/seg-1.md · $TMP/toy/skills/ship/SKILL.md
    Project: /tmp/toy-project
    Findings: $TMP/ws/findings/U01.md
    Prior issues:
      TO-001 · attempt 1 · watch agent:writer · held when every Write path starts out/ · recurred when a Write path is outside out/
      TO-002 · attempt 1 · watch agent:writer · held when a Target not under out/ is refused with Result: failed and nothing is written · recurred when a Target not under out/ is written

## Into the run directory

When the findings file is written:

- copy `$TMP/ws/findings/U01.md` to `<outputs_dir>/findings/U01.md`;
- copy `$TMP/ws/units/U01.md` to `<outputs_dir>/trace/U01.md` and `$TMP/toy/agents/writer.md`
  to `<outputs_dir>/definition/writer.md`, so the grader can hold every step id and rule line
  against what it cites;
- end `transcript.md` with a `## Return` heading and, under it, the agent's return exactly as
  the agent would hand it back: that one line and nothing else. The two-line summary you give
  your caller is separate and is not the return.
