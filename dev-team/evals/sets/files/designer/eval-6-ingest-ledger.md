# Deviations — data/ingest

Append-only. One entry per item; a status line is the only edit an entry ever gets.

## data/ingest — 2026-09-28 — spec-change:design — 1

Clause: `docs/packages/data/design/ingest.md` §3 **Data model / internal contracts**, the Module plan's `loaders.py` line, and §4 step 3.
Said: "`loaders.py` — `discover_files`, `load_bars`, `_parse_row` (§5)." and, in §4 step 3, the action "`_parse_row` → `Bar`".
Found: §5 **Interfaces** has three rows, `Bar`, `load_bars` and `discover_files`, and none for `_parse_row`. `packages/data/src/data/ingest/README.md` **Entry points and interfaces** lists no such name either. The Module plan marks `_parse_row` as a §5 interface, and §5 does not define it.
Why: the intent tests import every §5 name from the module the plan gives it, and `_parse_row` has no row, no signature and no error case to write a test from.
Status: open
Raised by: tester — run-package data
Resolved by: —

## data/ingest — 2026-09-29 — spec-change:design — 2

Clause: `docs/packages/data/design/ingest.md` §7 **Tests**, the case "delimiter from settings".
Said: "Unit: a well-formed file; a missing column; a bad float; a bad timestamp; delimiter from settings. Fixture: `tests/fixtures/ingest/aapl-3d.csv`."
Found: §4 step 2's action is "`csv.DictReader`, check columns" and names no delimiter, and no other step of §4 reads `DATA_INGEST_DELIMITER`, which §3 puts in `configs.py`. The one fixture §7 names, `aapl-3d.csv`, is comma-delimited, and a comma is the setting's default.
Why: the case names a setting no step of §4 uses, and no data that tells a configured delimiter from the default, so the unit test it asks for cannot be written from the design.
Status: open
Raised by: implementer — run-package data
Resolved by: —
