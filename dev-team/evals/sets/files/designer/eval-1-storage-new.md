# Harness — designer eval 1: storage, mode new

Seed: you maintain `marketlab`, a two-package uv workspace; `data/ingest` shipped last week
and `data/storage` is next. You are not at the keyboard during the design step, so any
question the designer would ask goes to `outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The store engine is DuckDB, one file; that is D1 in `docs/decisions.md`, already decided.
- The file path comes from `DATA_DB_PATH`, as `docs/architecture.md` **Shared conventions**
  says; there is no second location and no server.
- `storage` consumes `Bar` exactly as the shipped `ingest` README defines it; nothing about
  `Bar` is up for discussion in this step.
- The only reader outside the package is `analysis`, through `query_bars`; the pipelines
  inside `data` call `write_bars`.
- Timestamps: treat `Bar.ts` as the shipped README describes it today; the tz change is a
  separate open change file about `ingest`, not this section.
- No answer here names a mode, an exit value or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path (for example
`outputs/docs/packages/data/design/storage.md`), and put the commit message — scope, summary
and trailer exactly as it would be committed — in `outputs/commit.txt`.
