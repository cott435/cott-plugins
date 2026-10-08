# Seed
What did the writer agent do in the "Ship the toy file" chat? Show me the run.

# Setup
Do everything in `fixture.md` (same directory) first. "Ship the toy file" is a chat title,
as the app's sidebar shows it, in project /tmp/toy-project. Two recorded chats carry that
title: the original, whose id begins `0a0d17f0`, and a fork of it, whose id begins `f0a0d17f`.
The user knows the title, not the id.

# User's answers
- When asked which "Ship the toy file" chat: the original one, not the fork — the id
  beginning `0a0d17f0`.
- If asked which plugin: `toy`, the one whose `.claude-plugin/plugin.json` is in the working
  directory.
- Anything else: the option marked Recommended.

# Copy out, when done
Copy these from the workspace the target built into `outputs/`, keeping the names:
`flow.html` → `outputs/flow.html`; `index.json` → `outputs/index.json`;
`units/U01.html` → `outputs/units/U01.html`; `units/U01.json` → `outputs/units/U01.json`.
