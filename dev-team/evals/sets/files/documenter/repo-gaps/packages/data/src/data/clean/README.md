# `data/clean`

## Purpose

Applies the cleaning rules to landed bars and returns the repo's `bars` shape.

## Files

| File | What it holds |
|---|---|
| `rules.py` | `clean_bars` and `BAR_COLUMNS` |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `clean_bars` | `(df: DataFrame) -> DataFrame` | yes |

## Pipeline / workflow

Read the landed parquet for the run date, keep `BAR_COLUMNS`, drop rows with any null.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DATA_LANDING_DIR` | `./landing` | where landed parquet is read from |
| `DATA_RETRIES` | `5` | re-reads of a landed file that is still being written |

## Running and testing

`uv run pytest packages/data/tests/test_clean.py`

## Implementation notes

`dropna` is over every column; a halted session with a null volume is dropped, see
`docs/followups.md`.
