# Harness — architect eval 1: `/dev-team:plan-package data`, WRITE

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
