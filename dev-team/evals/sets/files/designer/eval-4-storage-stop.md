# Harness — designer eval 4: storage, mode new, stopped for a decision

Seed: you maintain `marketlab`, a two-package uv workspace; `data/ingest` shipped last week
and `data/storage` is next. The repo for this run is `evals/sets/files/designer/repo-stop`,
the same workspace as `repo/` except that nobody has chosen the bar store's engine: there is
no entry for it in `docs/decisions.md`, and no default anywhere. You are not at the keyboard
during the design step, so any question the designer would ask goes to
`outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The store engine is not chosen. I have no default and do not want one assumed: an embedded
  file and a server lead to different `open_store` arguments, a different upsert, and
  different rules for two pipelines writing at once, and which one fits depends on whether
  `analysis` will run on a second machine, which I have not settled.
- If asked what I would pick: I have no recommendation of my own; the designer may make one.
- `DATA_STORE_URL` is the config name whatever the engine.
- `storage` consumes `Bar` exactly as the shipped `ingest` README defines it.
- The only reader outside the package is `analysis`, through `query_bars`; the pipelines
  inside `data` call `write_bars`.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give, and
put the commit message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## The sync hook's stand-in

A real session runs the dev-team plugin's `PostToolUse` hook `hooks/sync_decisions.py` after
every Write or Edit to a file matching `docs/packages/*/decisions/*.md`, before the model
continues: it numbers each `## D?` stub, rewrites the inbox heading to the number, and merges
the entry into `docs/decisions.md`. The executor cannot run hooks, so it stands in for this
one. `<plugin>` below is the dev-team plugin directory the eval was initialized from (the
directory holding `evals/sets/designer.json`); `<outputs>` and `<run_dir>` are this run's.

After each Write or Edit the designer makes to an inbox under
`<outputs>/docs/packages/*/decisions/`, and before the designer's next step:

1. If `<plugin>/hooks/sync_decisions.py` does not exist, do nothing else: no hook ran in this
   session, and the inbox keeps what was written. Record
   `harness: no sync_decisions.py in this checkout; inbox left as written` and go on.
2. Otherwise run, with `cp` and no redirect, heredoc, `tee` or `sed -i`:
   - `rm -rf <run_dir>/hook-scratch`
   - `cp -r <plugin>/evals/sets/files/designer/repo-stop <run_dir>/hook-scratch`
   - `cp -r <outputs>/docs <run_dir>/hook-scratch/` — the run's files over the fixture
   - from `<run_dir>/hook-scratch`: `CLAUDE_PLUGIN_ROOT=<plugin> python3 <plugin>/hooks/sync_decisions.py --all`
   - copy each inbox under `<run_dir>/hook-scratch/docs/packages/*/decisions/` back to the
     same path under `<outputs>`, and, when `cmp -s` says
     `<run_dir>/hook-scratch/docs/decisions.md` differs from `repo-stop/docs/decisions.md`,
     copy it to `<outputs>/docs/decisions.md`.
3. Give the designer the script's stdout as the hook's `additionalContext` would have been
   given, and let it continue.

`hook-scratch/` is under `<run_dir>`, never under `<outputs>`.

## What the transcript records

Besides the harness rules' steps: every Bash command the designer runs, verbatim; every Write
or Edit with its path and, for an inbox, the `## ` heading line exactly as written; and every
stand-in command above prefixed `harness:`, with the script's stdout verbatim, so the grader
can tell the stand-in's writes from the designer's.
