# `analysis/features`

## Purpose

Computes the feature columns for one run date from `data`'s clean bars.

## Files

| File | What it holds |
|---|---|
| `build.py` | `build_features` and the per-feature functions |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `build_features` | `(bars: DataFrame) -> DataFrame` | yes |

## Pipeline / workflow

`clean_bars` output → one column per feature → the `features` shape.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `ANALYSIS_WINDOW` | `20` | rolling window, in sessions |

## Running and testing

`uv run pytest packages/analysis/tests/test_features.py`

## Implementation notes

Rolling features are left-aligned; the first `ANALYSIS_WINDOW - 1` rows are null by design.
