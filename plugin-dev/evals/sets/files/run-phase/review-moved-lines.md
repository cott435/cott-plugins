# Setup (the executor does this before anything else)
Copy evals/fixtures/toy-plugin/ to a fresh temporary directory OUTSIDE the repo, rename the
copy's .claude-plugin/plugin.json.fixture to plugin.json, `git init` it, commit everything as
"fixture", create and check out branch `toy-fix`, and run the target from inside that copy's
root (the directory holding .claude-plugin/plugin.json), with the slug `fix`. All git commands
the target runs happen in that copy. This is the one exception to "write nothing": the temp
copy is not the repo. Run every `edits.py` command the target names with plugin-dev's own
`scripts/edits.py`. Copy the copy's final `git log --stat`, `skills/greet/SKILL.md`, the
progress ledger and every `site/notes/fix/fix-0*.md` file into outputs/ when done.

The plan is `site/notes/fix/`: an edit list, an overview and a ledger with phases 0 and 1
done.

# User's answers
- If the target stops for review: "Reviewed — approve, commit it."
- Anything else: the option marked Recommended.
