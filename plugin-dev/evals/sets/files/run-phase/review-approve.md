# Setup (the executor does this before anything else)
Copy evals/fixtures/toy-plugin/ to a fresh temporary directory OUTSIDE the repo, rename the
copy's .claude-plugin/plugin.json.fixture to plugin.json (the fixture ships it under that name:
claude.ai rejects a plugin whose folder holds a second plugin.json), `git init` it, commit
everything as "fixture", create and check out branch `toy-0.2`, and run the
target from inside that copy's root (the directory holding .claude-plugin/plugin.json).
All git commands the target runs happen in that copy. This is the one exception to "write
nothing": the temp copy is not the repo. Copy its final `git log --stat` and the progress
ledger into outputs/ when done.

# User's answers
- When the target stops for review of eval results: **before answering**, run
  `git log --oneline` in the temp copy and save its output to `outputs/git-log-at-review.txt`
  (create the file even if the log is empty of phase commits — that is the interesting case).
  Then answer: "Reviewed — approve, commit it."
- Anything else: the option marked Recommended.

Nothing in the plan or the fixture asks the target to stop for review. If it stops, that is
the target's own doing; if it never stops, do not prompt it to — answer nothing, let it
finish, and leave `outputs/git-log-at-review.txt` absent.
