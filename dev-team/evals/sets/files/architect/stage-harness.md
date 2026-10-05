# Harness — architect eval 10: `/dev-team:plan-package data`, WRITE, a vendor download and a cleaning step

Answers as the user would state them. The brief's constraints settle the sections (`download`,
`clean`, `storage`, in that dependency order; `httpx` for the vendor; SQLite through
`sqlite3`; UTC), so a question about them is answered from the brief. For any question below,
answer with the fact given. For any other question — how much may be spent on the vendor
included — the user gives no answer: record the question in `outputs/interview.md`, accept the
architect's own `Assumption if unanswered:`, leave its entry open, and continue. The run does
not stop to wait for an answer.

- What does `download` do with a row? — Nothing. It calls the vendor, checks the HTTP status,
  and appends each response's rows as sent to `var/raw/bars/<symbol>.jsonl` (under
  `DATA_RAW_DIR`). It never reads, changes or drops a row.
- What does `clean` read? — The raw bar files `download` wrote, nothing else. It never calls
  the vendor.
- What happens to a row that fails a check? — It is set aside with the reason, in a rejects
  file beside the clean bars; the run goes on. Nothing is dropped without a record.
- Does `storage` check or change anything? — No. It writes the clean bars `clean` hands it to
  SQLite exactly as received, and reads them back.
- Which section provides `load_bars` and the **Bars** shape to `analysis`? — `storage`: it
  reads the stored rows back from SQLite.
- Where does the `Bar` record live? — In `clean`, the first section that holds a checked bar;
  `download` deals in the vendor's raw rows only, and `storage` returns `Bar`.
- Where do the raw files and the SQLite file live? — `DATA_RAW_DIR`, default `./var/raw`, with
  daily bars under `bars/`; `DATA_DB_PATH`, default `./bars.sqlite` (repo contract, Shared
  conventions).
- Which plan is the vendor key on? — The "Research" plan. The analyst has not bought "Desk"
  and does not intend to.
- Is there a CLI, and with what library? — One console script, `data-refresh [--year <YYYY>]`,
  `argparse` (repo contract).
- May `analysis` read the SQLite file or the raw files directly? — No; only through `data`'s
  public `load_bars`.
- Does `download` also dedupe, or `clean` also adjust for splits? — No. Three sections, in the
  brief's order; split adjustment is out of scope.
- A project skill with no section, or a section with no skill? — There are no project skills
  in this repo.
- Is the vendor to be re-probed? — No. `docs/sources/barfeed.md` is the repo-scope probe and
  the API is reachable; probing is the driver's step, not this run's.
