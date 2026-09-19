# Setup (the executor does this before anything else)
Copy evals/fixtures/toy-plugin/ to a fresh temporary directory OUTSIDE the repo, `git init`
it, commit everything as "fixture", create and check out branch `toy-0.2`, and run the
target from inside that copy's root (the directory holding .claude-plugin/plugin.json).
All git commands the target runs happen in that copy. This is the one exception to "write
nothing": the temp copy is not the repo. Copy its final `git log --stat` and the progress
ledger into outputs/ when done.

# User's answers
- When the target stops for review of eval results: "Reviewed — approve, commit it."
- Anything else: the option marked Recommended.
