# Harness — designer eval 6: ingest, mode delta, two open spec-change:design entries

Seed: you maintain `marketlab`; `data/ingest` shipped on 2026-09-22. `run-package data` has
re-opened it at DESIGN for two reasons at once: the open change file
`docs/changes/ingest-tz-aware-bars.md` names it, and its ledger holds two open
`spec-change:design` entries, one a tester raised on 2026-09-28 and one an implementer raised
on 2026-09-29. The driver's spawn block names the change file and both entry headings. Any
question goes to `outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The broker's CSV exports are in `America/New_York`; that is why the change file makes it
  the default `tz`.
- The canonical contract still describes the shipped code on purpose; the change file is
  the delta until `sync-plan` runs. Design to the change file where they differ.
- `discover_files` and `Bar`'s fields are not changing.
- Both ledger entries are about the design on disk, `docs/packages/data/design/ingest.md`.
  Nobody has edited that design since they were raised, and nobody has answered either one.
- `DATA_INGEST_DELIMITER` is a real setting and it stays: one broker's exports are
  semicolon-delimited.
- Nothing outside `loaders.py` uses a name `_parse_row`.
- No answer here names a mode, an exit value, a status or a document heading; those are the
  designer's to decide from its instructions.

## The ledger for this run

The fixture tree has no `docs/packages/data/deviations/ingest.md`. For this run that file's
content is `evals/sets/files/designer/eval-6-ingest-ledger.md`, under the dev-team plugin
directory the eval was initialized from (the directory holding `evals/sets/designer.json`).
Read that file wherever the designer would read the section's ledger, and treat it as being at
`docs/packages/data/deviations/ingest.md` in the repo. The fixture file itself is never
edited.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write,
edit or commit under `outputs/` at its repo-relative path, the path its own instructions give
(for example `outputs/docs/packages/data/design/ingest.md` for the design). A file it would
edit is written there whole: the text it read, with the designer's edits applied and every
other line as it was. Put the commit message — scope, summary and trailer exactly as it would
be committed — in `outputs/commit.txt`, then a line `---`, then each path the commit would
stage, one per line, exactly as its `git commit … -- <paths>` pathspec would name them.

## What the transcript records

Besides the harness rules' steps: every Write or Edit the designer makes, with its path and,
for an Edit, the line before and the line after; and the designer's final message, verbatim.
