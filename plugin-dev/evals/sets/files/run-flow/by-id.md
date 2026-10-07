# Seed
/plugin-dev:run-flow 0a0d17f0-0000-4000-8000-00000000fixt

# Setup
Do everything in `fixture.md` (same directory) first. The session id in the seed is the
planted chat "Ship the toy file" in project /tmp/toy-project; it resolves on its own, so the
target has no reason to ask which chat.

# User's answers
- If asked which chat: the one whose id begins `0a0d17f0`, titled "Ship the toy file" — not
  its fork.
- If asked which plugin: `toy`, the one whose `.claude-plugin/plugin.json` is in the working
  directory.
- Anything else: the option marked Recommended.

# Copy out, when done
Copy these from the workspace the target built into `outputs/`, keeping the names:
`flow.html` → `outputs/flow.html`; `index.json` → `outputs/index.json`;
`units/U01.html` → `outputs/units/U01.html`; `units/U01.json` → `outputs/units/U01.json`.
Also copy `$TMP/toy/.gitignore` to `outputs/toy.gitignore` if that file exists.
