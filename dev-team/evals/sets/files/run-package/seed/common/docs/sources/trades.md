# Source probe — trades — dataset — 2026-09-26
Purpose: `data/ingest` (`load trades`) — the columns, dtypes and quirks of the analyst's CSV export, so the designer can specify parsing and rejection.
Profile: none kept for this seed; every number below was computed from the full file (400 rows) and is `observed`.

## Access

Local file `data/trades.csv`, relative to the repo root: one header line and 400 data rows,
comma-separated, unquoted, UTF-8. Read whole; no credential, no network.

## Provenance

none found — no data card, README or column dictionary ships with the export. The brief names
the five columns and says `ts` is ISO 8601 UTC.

## Shape

400 rows × 5 columns. One trading session, 2026-09-01, `13:30:20Z` to `15:46:34Z`.

## Observed schema

| column | declared (brief) | loaded as | null % | distinct | example | label |
|---|---|---|---|---|---|---|
| `ts` | ISO 8601 UTC | str; every value matches `YYYY-MM-DDTHH:MM:SSZ` | 0 | not unique (see Duplicates) | `2026-09-01T13:30:20Z` | observed |
| `symbol` | str | str | 0 | 3 — `AAA` 128, `BBB` 147, `CCC` 125 | `AAA` | observed |
| `price` | float | float, two decimals, 8.36–120.81 | 0 | — | `49.74` | observed |
| `size` | int | int, 10–500 | 0 | — | `280` | observed |
| `side` | str | str, two values — `buy` 192, `sell` 208 | 0 | 2 | `sell` | observed |

No other column exists. In particular there is no venue, id, currency or exchange column.

## Duplicates and keys

Two exact duplicate rows, all five fields equal, each appearing twice:
`2026-09-01T14:04:58Z,BBB,119.98,420,sell` and `2026-09-01T14:54:03Z,CCC,8.65,380,sell`.
398 distinct rows. No single column is a key; the five fields together are unique after
deduplication.

## Target

not a modeling task — the consumer parses, cleans and stores rows.

## Leakage

not a modeling task.

## Features

not a modeling task.

## Splitting

not a modeling task.

## Supported tasks

Load, deduplicate, order and store; per-symbol aggregation downstream.

## Quirks

- The two exact duplicate rows above.
- One out-of-order timestamp: data row 311 (`2026-09-01T15:10:12Z`) follows data row 310
  (`2026-09-01T15:14:08Z`); the file is otherwise ascending by `ts`.
- `ts` carries a literal `Z`; no `+00:00` form appears.
- Every row parses; the rejection path (a missing or unparseable field) has no example in this
  export and needs a fixture of its own.

## Cost and time of a full pass

Under a second; 400 rows.

## Sections served

## data/ingest

Probed for: the `ingest` row of `docs/packages/data/contract.md` (`load trades`). Columns
needed: all five, as in **Observed schema**, with the parse rule per column — `ts` → tz-aware
UTC datetime from the `Z` form; `symbol` → str; `price` → float; `size` → int; `side` → one of
`buy`, `sell`. Duplicates and ordering are not this section's concern (`clean`). All `observed`.
