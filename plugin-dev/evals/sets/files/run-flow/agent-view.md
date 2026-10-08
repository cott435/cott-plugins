# Seed
/plugin-dev:run-flow --agent writer --sessions 0a0d17f0-0000-4000-8000-00000000fixt,0f10d17f

# Setup
Do everything in `fixture.md` (same directory) first. The two sessions in the seed are both
recorded chats of the toy plugin in project /tmp/toy-project: `0a0d17f0-0000-4000-8000-00000000fixt`
("Ship the toy file", one writer run) and `0f10d17f-0000-4000-8000-0000000flow0` (untitled,
on branch `flow`: three writer runs and two reviewer runs). `0f10d17f` is a unique prefix.

# User's answers
- If asked which plugin: `toy`, the one whose `.claude-plugin/plugin.json` is in the working
  directory.
- If asked which chat or which agent type: both sessions and the writer are already in the
  seed; repeat them.
- Anything else: the option marked Recommended.

# Copy out, when done
Copy the whole `evals/workspace/audit/` tree the target built under `$TMP/toy` to
`outputs/audit/`, so `outputs/audit/views/`, `outputs/audit/0a0d17f0/` and
`outputs/audit/0f10d17f/` hold what the target wrote.
