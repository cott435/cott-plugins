# fix-issues eval 1 — `open`, a definition ERROR and an agent WARN

Seed: build the fixture in `fixture.md` (same directory as this sheet) exactly; this eval
adds no edit before the first commit and no further issue. The ledger holds TO-001 and
TO-002, both `open`.

## Answers

Answer each question you would have asked with the first line below that covers it. If none
does, take the option marked Recommended.

- Which plugin: the one in the working directory, `$TMP/repo/toy`.
- Approve the plan, as proposed: **Approve the plan.** (If asked again after a change: approve.)
- Merge the branch into `main`: **No. Leave the branch and the worktree where they are;
  I will merge later.**
- Bump the version, or run `bump-version`: **No, not now.**
- Anything about the writer's `notes/scratch.md` write beyond what the issue says: I have
  nothing to add; the issue file is what I know.
- Anything about what the ship skill should do on an unexpected first line: I have no
  preference; whatever you propose in the plan is what I will approve.
- The fixture's main checkout (`$TMP/repo`) is on `main` with a clean tree; nobody else is
  working in it.

## Where to write what you would commit

Commits and branches in `$TMP/repo` and its worktrees are fine — that is the fixture's job.
Nothing is written in the cott-plugins repo. At the end, fill `outputs/` as `fixture.md`
says.
