# Seed
/plugin-dev:design-plugin 0.2-returns make the writer's return rule and the ship skill's handling of it consistent everywhere, and close the open audit issues

# The plugin
Build the fixture in `evals/sets/files/fix-issues/fixture.md` (under the same repo root as
this sheet) exactly, and run the seed from `$TMP/repo/toy`, the toy plugin's directory. It has
one agent (`agents/writer.md`), one skill (`skills/ship/SKILL.md`) and two open issues in
`runs/audits/issues/`. Nothing is written, committed or branched in the cott-plugins repo.

# User's answers (use these whenever the skill would ask; for anything not covered, pick the option you marked Recommended)
- What I want: the same as I typed. No new command, no new agent. The ship workflow should
  do what it does today, with its rules agreeing with each other and the two issues fixed.
- Anything else: I have nothing to add.

# What goes in `outputs/`
- `outputs/chat.md`: everything you said to the user, in order.
- `outputs/interview.md`: every question you asked or would have asked, with its options and
  the answer taken. Write "no questions asked" when there were none.
- `outputs/git-log.txt`: `git -C $TMP/repo log --oneline --all --decorate`, then
  `git -C $TMP/repo branch -a` and `git -C $TMP/repo worktree list`, taken at the end.
