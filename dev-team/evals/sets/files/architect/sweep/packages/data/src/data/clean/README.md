# `data/clean`

## Purpose

Drops exact duplicate records and sorts by `ts`.

## Files

| File | What it holds |
|---|---|
| `rules.py` | `dedupe`, `sort_by_ts`, `clean_trades` |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `dedupe` | `(trades: list[Trade]) -> tuple[list[Trade], int]` | no |
| `sort_by_ts` | `(trades: list[Trade]) -> list[Trade]` | no |
| `clean_trades` | `(trades: list[Trade]) -> list[Trade]` | no |

## Pipeline / workflow

`dedupe` → `sort_by_ts`; `clean_trades` composes the two.

## Configuration

none.

## Running and testing

`uv run pytest packages/data/tests/intent/clean`

## Implementation notes

`dedupe` returns the dropped count beside the kept records — `docs/deviations.md`,
`data/clean — 2026-09-24` (approved). The dedupe key is the whole record (contract §7).
