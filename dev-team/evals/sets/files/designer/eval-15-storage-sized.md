# Harness — designer eval 15: storage, mode new, a section that is not small

Seed: you maintain `marketlab`, a two-package uv workspace. `data` was planned on 2026-10-01
and `data/storage` is ready to design. No section of `data` has been built, so the driver
sent `Dependency READMEs: none`. The repo for this run is
`evals/sets/files/designer/repo-planned`. You are not at the keyboard during the design step,
so any question the designer would ask goes to `outputs/interview.md` and is answered from
here.

Answers, as facts you would state:

- The fixture tree holds documents only: the repo contract, the decisions ledger and the
  `data` contract. Under `packages/data/src/data` the scaffold left an empty `__init__.py` and
  `errors.py` with `DataError`; there is nothing at `packages/data/src/data/storage`.
- The DuckDB file is one file at `DATA_DB_PATH` (D1); `analysis` reads it through `query_bars`
  only; nothing but `data` writes it.
- I expect `storage` to be the biggest section in `data`: opening and migrating the store, the
  upsert, the range query that returns a `BarFrame`, and the `runs` ledger with its
  context manager. Several hundred lines in all.
- Nothing about `data` is undecided. D1 is decided, and no change file is open.
- No answer here names a mode, an exit value, a file name, a size or a document heading;
  those are the designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path (for example
`outputs/docs/packages/data/design/storage.md`), and put the commit message — scope, summary
and trailer exactly as it would be committed — in `outputs/commit.txt`.
