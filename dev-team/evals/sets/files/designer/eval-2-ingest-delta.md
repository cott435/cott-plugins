# Harness — designer eval 2: ingest, mode delta

Seed: you maintain `marketlab`; `data/ingest` is shipped and an open change file,
`docs/changes/ingest-tz-aware-bars.md`, names it. `run-package data` has re-opened `ingest`
at DESIGN. Any question goes to `outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The broker's CSV exports are in `America/New_York`; that is why the change file makes it
  the default `tz`.
- Alpaca bars are UTC; `docs/sources/alpaca.md` shows the `t` field.
- The canonical contract still describes the shipped code on purpose; the change file is
  the delta until `sync-plan` runs. Design to the change file where they differ.
- `discover_files` and `Bar`'s fields are not changing.
- The existing design at `docs/packages/data/design/ingest.md` is the one on disk; nothing
  else describes the section but its README.
- No answer here names a mode, an exit value or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path (for example
`outputs/docs/packages/data/design/ingest.md`), and put the commit message — scope, summary
and trailer exactly as it would be committed — in `outputs/commit.txt`.
