# Seed
/plugin-dev:revise-plugin rev every skill should agree with CLAUDE.md

# Setup (the executor does this before anything else)
Copy evals/fixtures/toy-plugin/ to a fresh temporary directory OUTSIDE the repo and rename the
copy's .claude-plugin/plugin.json.fixture to plugin.json. Delete the copy's `site/notes/`
folder (its plans are other evals'). Then plant one defect:

- Append to the copy's `CLAUDE.md` the line: `Every skill writes exactly one file, under
  outputs/, and nothing else.`
- Write the copy's `skills/wave/SKILL.md` as:

  ```
  ---
  name: wave
  description: Wave at someone by name. Use when the user asks to wave at a person.
  ---

  # Wave

  Write `outputs/wave.txt` containing one line: `*waves at <name>*`. Then append the
  name to `outputs/waved.log`, one name per line.
  ```

`git init` the copy, commit everything as "fixture", and run the target from the copy's root
(the directory holding .claude-plugin/plugin.json). The copy is its own repository with no
default branch to worktree from: skip the worktree, create and check out the branch
`toy-rev` in the copy itself, and work there. Every git command the target and its agents run
happens in that copy. This is the one exception to "write nothing": the temp copy is not the
repo. Run every `edits.py` command the target names with plugin-dev's own `scripts/edits.py`.
When done, copy the copy's `git log --stat` and its whole `site/notes/rev/` folder into
outputs/.

# User's answers
- The goal question: what is wrong is that skills may disagree with CLAUDE.md; contradictions
  come first; nothing is out of scope.
- At the units approval: approve as shown.
- For each open decision: the option marked Recommended.
- Anything else: the option marked Recommended.
