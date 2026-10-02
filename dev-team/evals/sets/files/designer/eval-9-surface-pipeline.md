# Harness — designer eval 9: surface, mode new, one pipeline over three shipped sections

Seed: you maintain `marketlab`, a two-package uv workspace. The three working sections of
`data` have shipped: `ingest` on 2026-09-22, `clean` on 2026-09-25 and `storage` on
2026-09-26, each reviewed and approved. `data/surface`, the last row of the contract, is
ready to design. The repo for this run is `evals/sets/files/designer/repo-shipped`. You are
not at the keyboard during the design step, so any question the designer would ask goes to
`outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The fixture tree holds documents only. The three sections' code is not in it and is not
  needed: each README is that section's shipped document and describes its code as it is.
- Under `packages/data/src/data` the scaffold left an empty `__init__.py` and `errors.py`
  with `DataError`. There is no `cli.py` and no `pipelines` directory yet, and
  `packages/data/pyproject.toml` has no `[project.scripts]` table.
- `analysis` imports `Bar` and `query_bars` from `data`'s top level and nothing else.
  Nothing outside `data` calls `load_bars`, `clean_bars`, `write_bars` or `recorded_run`.
- `data-ingest` is the package's only command. I run it by hand, and a nightly job runs it.
- I read the `runs` table to see which nightly runs failed, so a run that raised must still
  have its row.
- The storage README describes two ways to use `recorded_run`. Both work as it says; which
  one the pipeline uses is the designer's to decide from its instructions.
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
