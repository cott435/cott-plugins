# `data/ingest`

Built 2026-09-24. Run: `run-package data`.

## Purpose

Reads a trades CSV into `Trade` rows, in file order, parsing timestamps to UTC, and drops
the rows the export repeats. Symbols are left as read and nothing is sorted here.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `loader.py` | `Trade`, `IngestError`, `load_trades`; the CSV read (`_read_rows`), the dedupe (`_drop_repeats`) and the timestamp parse | the `daily` pipeline |
| `__init__.py` | re-exports `load_trades`, `Trade` and `IngestError` | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `load_trades` | `(path: Path, *, normalise: Callable[[str], str]) -> list[Trade]` | read one CSV and drop its repeats; raises `IngestError` for an unreadable file, a missing column or a bad cell | no |
| `Trade` | `@dataclass(slots=True)` — `ts: datetime`, `symbol: str`, `price: float`, `size: int`, `side: str`; mutable, `eq=True`, **unhashable** (`__hash__` is `None`) | the row type every section passes | yes |
| `IngestError` | `class IngestError(ValueError)` | the one error this section raises | no |

## Pipeline / workflow

`load_trades(path, normalise=…)` → `_read_rows(path)` opens the file, checks the header and
parses each record → `_drop_repeats(rows, normalise)` keeps the first row of each key
`(ts, normalise(symbol), price, size, side)` → `list[Trade]` in file order. First step of the
`daily` pipeline, which passes `clean.normalise_symbol` as `normalise`.

## Configuration

None. The path and the normalise rule are arguments.

## Running and testing

`uv run pytest packages/data/tests/unit/ingest packages/data/tests/intent/ingest`

## Implementation notes

- The dedupe key takes the canonical symbol, because the venue repeats a row with its symbol
  spelled another way. The rule is `clean`'s and reaches this section as the `normalise`
  argument: `ingest` may not import `clean`, and the contract's Package conventions keep the
  rule's one definition there.
- The kept row's `symbol` is left as read; `clean_trades` rewrites it.
- `Trade` is not frozen, so it is unhashable; the dedupe keys on a tuple of fields.
- D1 binds this section (scope `data/ingest`): applied in `_parse_ts`.
- Dependencies consumed: none. Decisions applied: D1 (`ts` stored as UTC).
