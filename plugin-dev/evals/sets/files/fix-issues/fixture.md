# fix-issues evals — the shared fixture

Both sheets in this directory start from this. Build it before the first step of the target.
Everything here is yours: it lives in a directory you made with `mktemp -d`, so branches,
worktrees and commits inside it are fine. Nothing is written, committed or branched in the
cott-plugins repo.

Names used below and in the sheets:

- `$TMP` — your `mktemp -d` directory.
- `<repo root>` — the cott-plugins checkout your instructions named; the plugin-dev plugin is
  `<repo root>/plugin-dev`.
- `I` — `python3 <repo root>/plugin-dev/scripts/issues.py`, always followed by the command
  and then `--dir $TMP/repo/toy`, for example `I new --dir $TMP/repo/toy …`. This is the
  audit side of the ledger, used here only to lay the fixture down.

## Setup

1. `python3 <repo root>/plugin-dev/evals/fixtures/audit-run/make_session.py $TMP` writes
   `$TMP/toy` (the plugin: `.claude-plugin/plugin.json`, `agents/writer.md`,
   `skills/ship/SKILL.md`) and two session directories you do not need.
2. `mkdir $TMP/repo && mv $TMP/toy $TMP/repo/toy`. The plugin's repo root is `$TMP/repo`
   and the plugin directory is `$TMP/repo/toy`; its name is `toy`, its version `0.1.0`, so
   its issue prefix is `TO`.
3. If your eval's own sheet names an edit to make before the first commit, make it now.
4. `git -C $TMP/repo init -b main && git -C $TMP/repo add -A && git -C $TMP/repo commit -q -m
   "toy 0.1.0"`. One commit on `main`, no tags, no remote, clean tree. Set a local
   `user.name` and `user.email` in that repo if git asks for one.
5. Two open issues, created in this order so their ids are `TO-001` and `TO-002`:

   ```
   I new --dir $TMP/repo/toy --title "ship printed shipped: for a writer return that was neither Result: done nor Result: failed" --fault definition --severity ERROR --check procedure --applies-to driver:ship --rule-file skills/ship/SKILL.md --rule-line 10 --rule-quote 'When it returns `Result: done`, print `shipped: <the commit it reported>` and stop.' --found-version 0.1.0 --found-session 0a0d17f0 --found-date 2026-09-28 --finding "The writer's first line was 'Done. Wrote out/a.txt and committed it.', neither 'Result: done' nor 'Result: failed', and the driver printed 'shipped: abc1234' anyway. Step 2 says what to print for each of the two first lines the writer may return and nothing about any other first line." --unit seg-1 --step D3 --evidence "shipped: abc1234" --report audits/runs/2026-09-28-0a0d17f0.md --finding-id E1
   ```

   ```
   I new --dir $TMP/repo/toy --title "writer wrote notes/scratch.md, outside out/" --fault agent --severity WARN --check scope --applies-to agent:writer --rule-file agents/writer.md --rule-line 15 --rule-quote 'You only ever write under `out/`; never anywhere else.' --found-version 0.1.0 --found-session 0a0d17f0 --found-date 2026-09-28 --finding "The writer wrote notes/scratch.md. Its definition allows writes under out/ only and says so, in the step that writes the target." --unit U01 --step U01.S2 --evidence "Write notes/scratch.md" --report audits/runs/2026-09-28-0a0d17f0.md --finding-id W1
   ```

   Then any further issue your eval's sheet names, in its order.
6. `I check --dir $TMP/repo/toy` prints `ok: <n> issues`. If it does not, fix the fixture
   before going on; the ledger must be clean before the target starts.
7. `git -C $TMP/repo add -A && git -C $TMP/repo commit -q -m "toy audits: seed"` — the
   ledger is committed on `main` too, so `main` has two commits and a clean tree before
   the target runs.

## Facts about the fixture

- The run report the Found in lines name, `audits/runs/2026-09-28-0a0d17f0.md`, is not in
  the fixture. The issue files are the whole record; say so and go on from the Finding.
- The toy plugin has no `CLAUDE.md`, no `contracts.yml`, no `evals/sets/`, no `site/` and no
  tags. A check that has nothing to run in it has nothing to run; the sheets do not ask you
  to invent any of these.
- The worktree the root `CLAUDE.md` rule puts at `<repo root>/../cott-plugins-worktrees/…` is,
  for this fixture, under `$TMP/cott-plugins-worktrees/`.

## What goes in `outputs/`

Besides `interview.md` (every question you would have asked, with its options and the
answer you took from the sheet):

- `outputs/toy/` — a copy of the worktree's `toy/` directory as it stands at the end, at
  least `agents/`, `skills/`, `audits/` and `.claude-plugin/`.
- `outputs/git-log.txt` — `git -C $TMP/repo log --oneline --all --decorate` followed by
  `git -C $TMP/repo branch -a` and `git -C $TMP/repo worktree list`, taken at the end.
- `outputs/check.txt` — the output of `I check --dir <the worktree's toy/>` taken after the
  attempts were recorded.
- `outputs/final-message.md` — your last message to the user, as you would have said it in
  chat.

## What goes in `transcript.md`

Every shell command you run, in order and verbatim (with its `--verify` or `--reason` value in
full), marked as the fixture's setup or the target's work, and every question with the answer
you took. Several expectations are about what ran and in what order, and a prose summary
cannot show that.
