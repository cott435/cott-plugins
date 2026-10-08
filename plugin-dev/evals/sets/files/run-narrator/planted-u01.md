# Setup (after your first Read of the target, before anything else)

PD is the plugin directory this file lives under (the parent of its `evals/`). For a
`with_skill` run it is the plugin root your executor prompt names; use that copy.

1. `TMP=$(mktemp -d)` (under the session scratchpad when there is one). Everything below
   happens in that copy; it is your own, not the repo, and writing there is the one
   exception to "write nothing".
2. `python3 PD/evals/fixtures/audit-run/make_session.py $TMP`
3. `python3 PD/skills/run-flow/scripts/trace.py build $TMP/session/0a0d17f0-0000-4000-8000-00000000fixt.jsonl --plugin toy --out $TMP/ws`
4. Confirm `$TMP/ws/units/U01.md` and `$TMP/ws/units/U01.json` exist. If the build failed,
   stop and put its output in `transcript.md`; write no account.

# The spawn block

Treat these four lines, with `$TMP` replaced by the absolute path `mktemp -d` printed, as the
whole prompt you were spawned with. Every path is absolute.

```
Unit: U01
Trace: $TMP/ws/units/U01.md
Full: $TMP/ws/units/U01.json
Output: $TMP/ws/explain/U01.md
```

Write the account at exactly that Output path (create `explain/` if it is missing), and
nowhere else under `$TMP`.

# When done

- Copy `$TMP/ws/explain/U01.md` to `outputs/explain/U01.md`.
- Copy `$TMP/ws/units/U01.md` and `$TMP/ws/units/U01.json` to `outputs/units/` (the grader
  checks the account against them).
- In `transcript.md`: every file you read, in the order you read it; every file you wrote;
  then a final heading `## Return` followed by exactly what you would hand back to whoever
  spawned you, verbatim. Your two-line summary to the user comes after that heading's text.

# User's answers

The task asks nothing. If anything would prompt, take the option marked Recommended.
