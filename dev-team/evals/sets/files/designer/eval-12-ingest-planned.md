# Harness — designer eval 12: ingest, mode new, an entry point one frame above its effect

Seed: you maintain `marketlab`, a two-package uv workspace. `data` was planned on 2026-10-01
and its contract carries **Call paths**; `ingest.load_bars` is the third frame of the
`data-ingest` and `data-verify` file-read paths, and the file is opened by `load_bars`
itself. No section of `data` has been built. `data/ingest` depends on nothing, so the driver
sent `Dependency READMEs: none`. The repo for this run is
`evals/sets/files/designer/repo-planned`. You are not at the keyboard during the design step,
so any question the designer would ask goes to `outputs/interview.md` and is answered from
here.

Answers, as facts you would state:

- The fixture tree holds documents only: the repo contract, the decisions ledger and the
  `data` contract. Under `packages/data/src/data` the scaffold left an empty `__init__.py` and
  `errors.py` with `DataError`; there is nothing at `packages/data/src/data/ingest`.
- A broker export is a directory of a few thousand rows across a handful of `*.csv` files,
  one row per bar: `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`. The
  `timestamp` column is in the exchange's zone, which is why `DATA_INGEST_TZ` exists.
- No file under `root` is read by anything but `load_bars`; nothing else in `data` opens a
  CSV.
- `analysis` imports `Bar` from `data`'s top level and reads its fields; it never constructs
  one.
- Nothing about `data` is undecided. D1 is decided, and no change file is open.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/ingest.md` for the design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## What the transcript records

Besides the harness rules' steps: every file read, by its path, in the order read — a
document of the repo by its repo-relative path, a file of the plugin by its path under the
plugin root; each step of the designer's procedure as it is carried out, in order, by the
name its instructions give the step, with what was read, checked or changed in it; and the
designer's final message, verbatim.
