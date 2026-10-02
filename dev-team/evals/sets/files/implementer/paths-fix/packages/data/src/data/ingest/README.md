# `data/ingest`

Built 2026-09-24. Run: `run-package data`.

## Purpose

Reads a trades CSV into `Trade` rows, in file order, parsing timestamps to UTC. Nothing is
deduplicated or sorted here.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `loader.py` | `Trade`, `IngestError`, `load_trades`; the CSV read (`_read_rows`), the wrapper it runs in (`_guarded`) and the timestamp parse | `clean`, the `daily` pipeline |
| `__init__.py` | re-exports `load_trades`, `Trade` and `IngestError` | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `load_trades` | `(path: Path) -> list[Trade]` | read one CSV; raises `IngestError` for an unreadable file, a missing column or a bad cell | no |
| `Trade` | `@dataclass(slots=True)` — `ts: datetime`, `symbol: str`, `price: float`, `size: int`, `side: str`; mutable, `eq=True`, **unhashable** (`__hash__` is `None`) | the row type every section passes | yes |
| `IngestError` | `class IngestError(ValueError)` | the one error this section raises | no |

## Pipeline / workflow

`load_trades(path)` → `_guarded(step, source=path)` runs the read step it is handed, a
lambda around `_read_rows(path)` → `_read_rows` opens the file, checks the header and parses
each record → `list[Trade]` in file order. First step of the `daily` pipeline.

## Configuration

None. The path is an argument.

## Running and testing

`uv run pytest packages/data/tests/unit/ingest packages/data/tests/intent/ingest`

## Implementation notes

- The read runs inside `_guarded`, which turns an `OSError` into
  `IngestError("<file name>: cannot be read")` after logging one `WARNING` line `unreadable`.
- `Trade` is not frozen, so it is unhashable — `set(rows)` and `dict` keys raise
  `TypeError: unhashable type: 'Trade'`. Dedupe by a field tuple instead.
- A naive timestamp is taken as UTC (repo contract, Shared conventions).
- D1 binds this section (scope `data/ingest`): applied in `_parse_ts`.
- Dependencies consumed: none. Decisions applied: D1 (`ts` stored as UTC).
