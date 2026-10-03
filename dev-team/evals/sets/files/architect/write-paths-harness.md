# Harness — architect eval 7: `/dev-team:plan-package data`, WRITE, with **Call paths**

Seed: the repo is `evals/sets/files/architect/write/`, read in place and read-only, with
`docs/brief.md` read from `evals/fixtures/two-package/docs/brief.md`; every file the run
would write goes under `outputs/` at its repo-relative path, and the commit is recorded in
`outputs/commit.txt`, not made.

Answers as the user would state them. The brief's constraints settle the sections (`ingest`,
`clean`, `storage`, in that dependency order; SQLite through `sqlite3`; UTC), so a question
about them is answered from the brief. For any question below, answer with the fact given;
for any other question, accept the architect's own `Assumption if unanswered:`.

- Which section provides `load_trades` and the **Trades** shape to `analysis`? — `storage`:
  it reads the stored rows back from SQLite. `ingest`'s CSV reader is internal to `data`.
- Where does the `Trade` record live? — In `ingest`, the lowest section; `storage` returns it.
- Where does the SQLite file live, and how is it configured? — `DATA_DB_PATH`, default
  `./trades.sqlite` (repo contract, Shared conventions). No other configuration.
- Should a bad row be skipped, or the run stopped? — Stopped on the first bad row, naming
  the row and the field, with nothing written (brief: "Reject a row … and say which").
- Does `ingest` also dedupe or sort? — No. Three sections, in the brief's order.
- Is there a CLI, and with what library? — One console script, `data-ingest <csv> [--db
  <path>]`, `argparse` (repo contract).
- May `analysis` read the SQLite file directly? — No; only through `data`'s public
  `load_trades`.
- A project skill with no section, or a section with no skill? — There are no project
  skills in this repo; assign none.
- Is the `trades` dataset to be re-probed? — No. `docs/sources/trades.md` is the repo-scope
  probe and it is readable; probing is the driver's step, not this run's.
- What does `data-ingest` touch outside the package? — It reads the CSV at the path it is
  given and writes the SQLite file; it prints one line, `stored <n> new rows`. Nothing else:
  no network, no other file.
- Does the analyst want a retry layer, a staging step or any other machinery between the
  three steps, for robustness? — No. Read, clean, store, in that order, nothing between; the
  file is local and small.
- Does any other command exist, or run one section on its own (a schema init, a backfill)?
  — No. `data-ingest` is the package's only command; `analysis` calls `load_trades` in
  process and the analyst runs `data-ingest` by hand.
