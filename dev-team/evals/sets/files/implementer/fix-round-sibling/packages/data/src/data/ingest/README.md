# `data/ingest`

Shipped 2026-09-23. Run: `run-package data`.

## Purpose

Reads a trades CSV into `Trade` rows, in file order, parsing timestamps to UTC. Nothing is
deduplicated or sorted here.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `loader.py` | `Trade`, `IngestError`, `load_trades`, the CSV parse | `clean`, `storage`, the `daily` pipeline |
| `__init__.py` | re-exports the three names above | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `load_trades` | `(path: Path) -> list[Trade]` | read one CSV; raises `IngestError` on a missing column or a bad cell | yes |
| `Trade` | `@dataclass(slots=True)` — `ts: datetime`, `symbol: str`, `price: float`, `size: int`, `side: str`; mutable, `eq=True`, **unhashable** (`__hash__` is `None`) | the row type every section passes | yes |
| `IngestError` | `class IngestError(ValueError)` | the one error this section raises | no |

## Pipeline / workflow

`load_trades(path)` → `list[Trade]` in file order. First step of the `daily` pipeline.

## Configuration

None. The path is an argument.

## Running and testing

`uv run pytest packages/data/tests/unit/ingest packages/data/tests/intent/ingest`

## Implementation notes

- `Trade` is deliberately **not frozen**: `clean` normalizes a naive `ts` in place rather
  than rebuilding every row. The cost is that `Trade` is unhashable — `set(rows)` and
  `dict` keys raise `TypeError: unhashable type: 'Trade'`. Dedupe by a field tuple instead.
- A naive timestamp is taken as UTC (repo contract, Shared conventions).
- Dependencies consumed: none. Decisions applied: D1 (`ts` stored as UTC).
