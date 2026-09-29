# Source probe — trades — dataset — 2026-09-20

Purpose: the `data` package reads this export as its only input (`source: dataset:trades`).
Profile: `docs/sources/trades.profile.py`; statistics: `docs/sources/trades.stats.json`.

## Access

readable — `data/trades.csv`, 400 rows, read with the standard library's `csv`.

## Provenance

none found — a synthetic export with no data card or column dictionary.

## Shape

400 rows, 5 columns, 3 symbols (`AAA`, `BBB`, `CCC`).

## Observed schema

| column | declared | loaded as | null % | distinct |
|---|---|---|---|---|
| `ts` | ISO 8601 UTC | str (parses with `datetime.fromisoformat` after `Z` → `+00:00`) | 0 | 398 |
| `symbol` | str | str | 0 | 3 |
| `price` | float | str → float | 0 | 361 |
| `size` | int | str → int | 0 | 44 |
| `side` | `buy` / `sell` | str | 0 | 2 |

## Duplicates and keys

2 exact duplicate rows (observed). No key column; a row is unique only on all five fields.

## Target

none — not a modeling dataset.

## Leakage

none.

## Features

none.

## Splitting

none — not a modeling task; the analysis is a rolling window over the whole tape.

## Supported tasks

none — cleaning and aggregation only.

## Quirks

- 2 exact duplicate rows (observed).
- 1 row out of `ts` order (observed): the export is not sorted.
- `ts` ends in `Z`; Python's `fromisoformat` needs it rewritten as `+00:00` on 3.10.

## Cost and time of a full pass

under a second.
