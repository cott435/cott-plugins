# Seed
Spawn run-auditor twice on the trace from eval 1: Mode unit on units/U01.md against $TMP/toy/agents/writer.md, and Mode driver on driver/seg-1.md against $TMP/toy/skills/ship/SKILL.md; Project /tmp/toy-project (absent, as a real project's history may be)

# Setup (the executor does this before anything else)
"The trace from eval 1" is not built yet. Build it yourself:

1. `TMP=$(mktemp -d)` (under the session scratchpad when there is one).
2. `python3 <plugin-dev dir>/evals/fixtures/audit-run/make_session.py $TMP`, where
   `<plugin-dev dir>` is the working tree's plugin-dev directory (the one holding
   `evals/sets/`); the fixture lives there whichever plugin root you were given. It writes the
   toy plugin at `$TMP/toy` and the recorded session under `$TMP/session/`.
3. `python3 <trace.py> build $TMP/session/0a0d17f0-0000-4000-8000-00000000fixt.jsonl --plugin toy --out $TMP/ws`,
   where `<trace.py>` is the one under your plugin root, wherever the target file says it
   lives. `$TMP/ws` is the workspace the request means.
4. Spawn the auditors as the target says. If `plugin-dev:run-auditor` would load a copy other
   than your plugin root's, spawn general-purpose agents told to read and follow
   `<plugin root>/agents/run-auditor.md` with the input block instead.

# User's answers (use these whenever the target would ask; for anything not covered, pick the option you marked Recommended)
- Anything beyond the two auditors (select, cross, report, log): out of scope, stop after both return.

# Where what the target would write goes
- Copy `$TMP/ws/findings/` to `outputs/findings/`, `$TMP/ws/units/` and `$TMP/ws/driver/` to
  `outputs/trace/units/` and `outputs/trace/driver/`, and `$TMP/toy/agents/` and
  `$TMP/toy/skills/` to `outputs/toy/agents/` and `outputs/toy/skills/`, so the citations can
  be checked from `outputs/` alone.
- Write each auditor's return, verbatim and whole, to `outputs/returns.md`.
