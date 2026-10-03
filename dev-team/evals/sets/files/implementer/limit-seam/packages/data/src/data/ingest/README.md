# `data/ingest`

Shipped 2026-09-23. Run: `run-package data`.

## Purpose

Reads a trades CSV into `Trade` rows, in file order, parsing timestamps to UTC. Nothing is
filtered, sorted or aggregated here.

## Files

| File | Responsibility | Used by |
|---|---|---|
| `loader.py` | `Trade`, `IngestError`, `load_trades`, the CSV parse | `bars`, the `daily` pipeline |
| `__init__.py` | re-exports the three names above | siblings |

## Entry points and interfaces

| Name | Signature | Use case | Public |
|---|---|---|---|
| `load_trades` | `(path: Path) -> list[Trade]` | read one CSV; raises `IngestError` on a missing column or a bad cell | no |
| `Trade` | `@dataclass(frozen=True, slots=True)` — `ts: datetime`, `symbol: str`, `price: float`, `size: int`, `side: str` | the row type every section passes | yes |
| `IngestError` | `class IngestError(ValueError)` | the one error this section raises | no |

## Pipeline / workflow

`load_trades(path)` → `list[Trade]` in file order. First step of the `daily` pipeline.

## Configuration

None. The path is an argument.

## Running and testing

`uv run pytest packages/data/tests/unit/ingest packages/data/tests/intent/ingest`

## Implementation notes

- Rows come back in file order, which is not always time order: the venue appends late
  prints at the end of the file.
- `ts` is always timezone-aware: a naive timestamp in the file is taken as UTC (D1). A
  `Trade` built by hand, in a test or by `analysis`, can still carry a naive `ts`; nothing
  in the dataclass forbids it.
- `side` is whatever the file's `side` cell holds. The venue writes `buy` or `sell`; the
  loader does not check it.
- Dependencies consumed: none. Decisions applied: D1 (`ts` stored as UTC).
