# Harness — designer eval 13: storage, mode new, a Call paths frame Section interfaces does not define

Seed: you maintain `marketlab`, a two-package uv workspace. `data` was planned on 2026-10-01
and its contract carries **Call paths**. No section of `data` has been built; `data/storage`
is ready to design, and since `ingest` has no README yet the driver sent `Dependency READMEs:
none`. The repo for this run is `evals/sets/files/designer/repo-planned`, with one of its
documents replaced (below). You are not at the keyboard during the design step, so any
question the designer would ask goes to `outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The fixture tree holds documents only: the repo contract, the decisions ledger and the
  `data` contract. Under `packages/data/src/data` the scaffold left an empty `__init__.py` and
  `errors.py` with `DataError`; there is nothing at `packages/data/src/data/storage`.
- The contract is the architect's document, written at PLAN. I have not edited it since, and
  nobody else has. I do not know, offhand, which names it lists where; the document says what
  it says.
- The DuckDB file is one file at `DATA_DB_PATH` (D1). `analysis` reads it through
  `query_bars` only; nothing but `data` writes it.
- I read the `runs` table to see which nightly runs failed, so a run that raised must still
  have its row.
- Nothing about `data` is undecided. D1 is decided, and no change file is open.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## The document substituted for this run

The repo for this run is `evals/sets/files/designer/repo-planned`, with one of its documents
replaced. The replacement is under the dev-team plugin directory the eval was initialized
from (the directory holding `evals/sets/designer.json`):

- `docs/packages/data/contract.md` is `evals/sets/files/designer/eval-13-contract.md`.

Read the replacement wherever the designer would read the document, and treat it as being at
the document's path in the repo. The tree's own copy is not part of this run and is not read.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/deviations/storage.md` for a ledger), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## What the transcript records

Besides the harness rules' steps: every file read, by its path, in the order read — a
document of the repo by its repo-relative path, a file of the plugin by its path under the
plugin root; each step of the designer's procedure as it is carried out, in order, by the
name its instructions give the step, with what was read, checked or changed in it; and the
designer's final message, verbatim.
