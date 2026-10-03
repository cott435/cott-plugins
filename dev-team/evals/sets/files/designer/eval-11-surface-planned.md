# Harness — designer eval 11: surface, mode new, right after PLAN, no sibling built

Seed: you maintain `marketlab`, a two-package uv workspace. `data` was planned on 2026-10-01
and its contract carries **Call paths**. No section of `data` has been built: there is no code
and no README under `packages/data/src/data/` for `ingest`, `clean` or `storage`. `status.py`
marks the `surface` row ready at DESIGN right after PLAN, and the driver, copying the
`dependency readmes:` line of `status.py --fields`, sent the designer `Dependency READMEs:
none`. The repo for this run is `evals/sets/files/designer/repo-planned`. You are not at the
keyboard during the design step, so any question the designer would ask goes to
`outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The fixture tree holds documents only: the repo contract, the decisions ledger and the
  `data` contract. Under `packages/data/src/data` the scaffold left an empty `__init__.py` and
  `errors.py` with `DataError`; nothing else exists there — no section directory, no
  `cli.py`, no `pipelines` directory — and `packages/data/pyproject.toml` has no
  `[project.scripts]` table.
- No section of `data` has a README. That is the state of the repo on the day the surface is
  designed: the sections are designed beside it and built after it.
- `analysis` imports `Bar` and `query_bars` from `data`'s top level and nothing else.
  Nothing outside `data` calls `load_bars`, `clean_bars`, `write_bars` or `recorded_run`.
- `data-ingest` and `data-verify` are the package's two commands. I run `data-verify` over a
  fresh broker export by hand, then `data-ingest`; a nightly job runs `data-ingest`.
- I read the `runs` table to see which nightly runs failed, so a run that raised must still
  have its row. `data-verify` writes nothing and has no row.
- Nothing about `data` is undecided. D1 is decided, and no change file is open.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/surface.md` for the design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## What the transcript records

Besides the harness rules' steps: every file read, by its path, in the order read — a
document of the repo by its repo-relative path, a file of the plugin by its path under the
plugin root; each step of the designer's procedure as it is carried out, in order, by the
name its instructions give the step, with what was read, checked or changed in it; and the
designer's final message, verbatim.
