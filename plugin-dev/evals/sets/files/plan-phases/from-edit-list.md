# Seed
/plugin-dev:plan-phases fix

# Setup
Copy `evals/fixtures/toy-plugin/` to `outputs/toy-plugin/` before starting, then in the copy:
1. Rename `.claude-plugin/plugin.json.fixture` to `.claude-plugin/plugin.json`.
2. Delete `site/notes/fix/fix-00-overview.md` and `site/notes/fix/fix-progress.md`: this eval
   plans the `fix` edit list from scratch. Leave `site/notes/fix/fix-edits.md` as it is.
3. Delete the whole `site/notes/0.2/` folder: it is another plan, not this eval's.
4. Overwrite `skills/greet/SKILL.md` with the eight lines the edit list was reviewed against
   (no phase of `fix` has run yet):

   ```
   ---
   name: greet
   description: Greet someone by name. Use when the user asks to say hello to a person.
   ---

   # Greet

   Write `outputs/greeting.txt` containing one line: `Hello, <name>.`
   ```

Treat `outputs/toy-plugin/` as the plugin directory. It has no `contracts.yml`. Skip the branch
and clean-tree checks. Run every `edits.py` command the skill names against the copy, with
plugin-dev's own `scripts/edits.py`.

# User's answers
- If the skill asks about a gap: pick the option marked Recommended.
- At the split approval: approve as shown.

# Harness override for this eval only
Write everything the skill would write into outputs/toy-plugin/, keeping plugin-relative paths
under it. The plan has no behavioral rows unless the skill adds one; if it spawns eval
writers, let them write into outputs/toy-plugin/evals/sets/. Do not commit. Write the skill's
final chat message to outputs/chat.md.
