# Seed
/plugin-dev:plan-phases 0.1

# Setup
The plugin under test is trading-agents, freshly scaffolded by design-plugin, whose only
committed plan file is its design. Treat `evals/fixtures/trading-agents/` as the plugin
directory: its design is `evals/fixtures/trading-agents/site/notes/0.1-design.md`. It has no
`.claude-plugin/plugin.json`, no `CLAUDE.md` and no `contracts.yml` in the fixture; treat the
first check in **Find the design** as passed, and the plugin as having no `CLAUDE.md` rules
and no `contracts.yml` yet. Skip the branch and clean-tree checks.

# User's answers
- If the skill asks about a gap: pick the option marked Recommended.
- At the split approval: approve as shown.

# Harness override for this eval only
Write everything the skill would write in the plugin directory into
outputs/trading-agents/ instead, keeping plugin-relative paths under it: the overview, every
phase note, the ledger, evals/sets/*.json and evals/sets/files/**. Run the eval writers as the
skill says, pointing them at outputs/trading-agents/ as the plugin directory for writing, and
at the fixture for reading the design. Do not commit. Write the skill's final chat message to
outputs/chat.md.
