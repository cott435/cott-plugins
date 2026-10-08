# Setup (after your first Read of the target, before anything else)

PD is the plugin directory this file lives under (the parent of its `evals/`). For a
`with_skill` run it is the plugin root your executor prompt names; use that copy.

1. `TMP=$(mktemp -d)` (under the session scratchpad when there is one). Everything below
   happens in that copy; it is your own, not the repo, and writing there is the one
   exception to "write nothing".
2. `python3 PD/evals/fixtures/audit-run/make_session.py $TMP`
3. `python3 PD/skills/run-flow/scripts/trace.py build $TMP/flow-session/*.jsonl --plugin toy --out $TMP/wsf`
   (`flow-session/` holds one main transcript; its id has changed between plan phases, so
   the glob names it rather than the id.)
4. Confirm `$TMP/wsf/units/U03.md` and `$TMP/wsf/units/U03.json` exist, and that
   `$TMP/wsf/index.json` lists U03 as `toy:reviewer`, description `Review a/x r1`. If U03 is
   not that unit, say which unit is in `transcript.md` and still narrate U03 as asked. If the
   build failed, stop and put its output in `transcript.md`; write no account.

# The spawn block

Treat these four lines, with `$TMP` replaced by the absolute path `mktemp -d` printed, as the
whole prompt you were spawned with. Every path is absolute.

```
Unit: U03
Trace: $TMP/wsf/units/U03.md
Full: $TMP/wsf/units/U03.json
Output: $TMP/wsf/explain/U03.md
```

Write the account at exactly that Output path (create `explain/` if it is missing), and
nowhere else under `$TMP`.

# When done

- Copy `$TMP/wsf/explain/U03.md` to `outputs/explain/U03.md`.
- Copy `$TMP/wsf/units/U03.md` and `$TMP/wsf/units/U03.json` to `outputs/units/` (the grader
  checks the account against them).
- In `transcript.md`: every file you read, in the order you read it; every file you wrote;
  then a final heading `## Return` followed by exactly what you would hand back to whoever
  spawned you, verbatim. Your two-line summary to the user comes after that heading's text.

# User's answers

The task asks nothing. If anything would prompt, take the option marked Recommended.
