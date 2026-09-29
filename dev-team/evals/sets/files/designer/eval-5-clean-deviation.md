# Harness — designer eval 5: clean, mode new, one additive contract deviation

Seed: you maintain `marketlab`, a two-package uv workspace; `data/ingest` shipped last week.
The repo for this run is `evals/sets/files/designer/repo-clean`, the same workspace as
`repo/` with one more planned section, `data/clean`, between `ingest` and `storage`, and one
more pipeline, `check_csv`. `data/clean` is ready to design. Any question the designer would
ask goes to `outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- `check_csv` is wanted exactly as the contract states it: per-reason drop counts under
  `ohlc`, `volume` and `duplicate`, nothing written. It backs the CLI command
  `marketlab check`.
- `clean_bars` is consumed by the `ingest_csv` and `refresh_prices` pipelines as the contract
  gives it. The `surface` section, not built yet, wires all three pipelines.
- How `clean` supplies the counts `check_csv` reports is the designer's call; I have no
  preference.
- `Bar` is the shipped `ingest` shape; `clean` yields it unchanged.
- The store engine is DuckDB, D1 in `docs/decisions.md`, already decided; nothing about it
  concerns `clean`.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/clean.md` for the design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

For the grader: the fixture has no ledger for `data/clean` at any location, so an entry the
designer appends starts a new file, `# Deviations — data/clean`, and is numbered `— 1`. Under
2.2 that file is `docs/packages/data/deviations/clean.md`; a 2.1 designer writes
`docs/deviations/data/clean.md` with a heading that has no `— <k>`.
