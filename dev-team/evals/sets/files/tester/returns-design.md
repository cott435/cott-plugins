Mode: new

# Design — `features/returns`

Designed 2026-09-26 from `docs/packages/features/contract.md` (row `returns`),
`docs/architecture.md` and `docs/packages/data/interface.md`.

1. **Purpose and scope**

Owns computing per-symbol daily simple returns from a `BarTable`, and describing the result as
one manifest row in `data`'s `LandingManifest` shape. Does not read or write files and does not
call `data`'s pipeline — that is `surface` and the `features-daily` pipeline.

2. **Inputs and outputs**

Upstream packages: data

- In: `bars` — a `BarTable` (`docs/architecture.md` Boundaries; `docs/packages/data/interface.md`
  Shapes provided): a `pandas.DataFrame` with columns `symbol: str`, `ts: datetime` (tz-aware
  UTC), `open`, `high`, `low`, `close: float`, `volume: int`, sorted by `symbol, ts`.
- Out: a `ReturnTable` (§3).
- Out: a manifest row — a `dict[str, Any]` whose keys are `data`'s `LandingManifest` columns
  (`docs/packages/data/interface.md` Shapes provided), in the provider's order. Of those,
  `run_date` is `run_date.isoformat()` and `rows` is `len(returns)`.
- Configuration: none.

3. **Data model / internal contracts**

- `ReturnTable` — a `pandas.DataFrame` with exactly the columns `symbol: str`, `ts: datetime`
  (tz-aware UTC), `ret: float`, in that order; one row per symbol per session after that
  symbol's first; sorted by `symbol, ts`, with a fresh `RangeIndex`.
- `FeatureError(Exception)` — attributes `reason: str`, `detail: str`; `str()` is
  `f"{reason}: {detail}"` per the repo error convention.

**Module plan** (under `packages/features/src/features/returns/`):

| module | defines | §5 interfaces |
|---|---|---|
| `models.py` | `FeatureError`, `RETURN_COLUMNS` | `FeatureError` |
| `compute.py` | `daily_returns` | `daily_returns` |
| `manifest.py` | `manifest_row` | `manifest_row` |
| `__init__.py` | docstring only | — |

4. **Workflow / pipeline** (serves the package pipeline `features-daily`)

1. Check `bars`. Trigger: `daily_returns` called. Output: the frame, unchanged. Failure: a
   missing `BarTable` column raises `FeatureError("missing column", <the column>)`; any
   `close <= 0` raises `FeatureError("non-positive close", <the symbol>)`.
2. Per symbol, `ret = close / previous close - 1`; each symbol's first session is dropped.
   Output: a `ReturnTable`.
3. Log one INFO record `event=features.returns.compute symbols=<k> rows=<n>`. Output: the
   `ReturnTable`, returned to the caller.
4. `manifest_row(returns, run_date)`. Output: one manifest row. Failure: an empty `returns`
   raises `FeatureError("empty returns", run_date.isoformat())`.

5. **Interfaces**

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `FeatureError` | `FeatureError(reason: str, detail: str)` | `surface` | no | — |
| `daily_returns` | `(bars: pd.DataFrame) -> pd.DataFrame` | `surface`; the `features-daily` pipeline | no | `FeatureError` `"missing column"`, `"non-positive close"` |
| `manifest_row` | `(returns: pd.DataFrame, run_date: date) -> dict[str, Any]` | `surface`; the `features-daily` pipeline | no | `FeatureError` `"empty returns"` |

6. **Error handling and logging**

- A `bars` frame missing a `BarTable` column → `FeatureError(reason="missing column",
  detail=<the first missing column, in BarTable order>)`.
- Any row with `close <= 0` → `FeatureError(reason="non-positive close", detail=<that row's
  symbol>)`; no partial table is returned.
- An empty `returns` given to `manifest_row` → `FeatureError(reason="empty returns",
  detail=run_date.isoformat())`.
- Each successful `daily_returns` logs exactly one record at INFO on the logger
  `features.returns`, message `event=features.returns.compute symbols=<k> rows=<n>`.
  `manifest_row` logs nothing.

7. **Tests**

Fixtures, both built in `conftest.py`: a six-row `BarTable` to `docs/architecture.md`
Boundaries — `AAPL` and `MSFT`, sessions 2024-03-04, 2024-03-05 and 2024-03-06 at 05:00 UTC;
`AAPL` closes `175.10`, `170.12`, `169.12`; `MSFT` closes `414.92`, `402.65`, `402.09`; the
other columns any valid values — and a four-row `ReturnTable` built to §3 for `manifest_row`'s
cases.

- `daily_returns` on the six-row fixture → four rows; columns exactly `symbol, ts, ret`; the
  `AAPL` row for 2024-03-05 has `ret == pytest.approx(170.12 / 175.10 - 1)`.
- Neither symbol's 2024-03-04 session is in the output.
- The six-row fixture with its rows shuffled → the same table, sorted by `symbol, ts`.
- The fixture without its `close` column → `FeatureError` with `reason == "missing column"`
  and `detail == "close"`.
- One `MSFT` close set to `0.0` → `FeatureError` with `reason == "non-positive close"` and
  `detail == "MSFT"`.
- `FeatureError("missing column", "close")`: `str()` is `"missing column: close"`, `.reason`
  and `.detail` set.
- `daily_returns` on the six-row fixture: `caplog` holds one INFO record on `features.returns`
  whose message is `event=features.returns.compute symbols=2 rows=4`.
- `manifest_row(returns, date(2024, 3, 6))` on the four-row `ReturnTable` → `rows == 4` and
  `run_date == "2024-03-06"`.
- `manifest_row`'s keys are exactly `LandingManifest`'s columns, in the provider's order.
- `manifest_row` on an empty `ReturnTable` → `FeatureError` with `reason == "empty returns"`
  and `detail == "2024-03-06"`.
- End to end: `daily_returns` on the six-row fixture, then `manifest_row` on its result with
  `date(2024, 3, 6)` → a four-row `ReturnTable` and a manifest row with `rows == 4`.

8. **Pitfalls and risks**

1. A `pct_change` over the whole frame leaks one symbol's last close into the next symbol's
   first row; the shift is per symbol.
2. `LandingManifest` is `data`'s shape: a column added there is a column `manifest_row` must
   write.

9. **Skills used**

- `project-structure` — module sizes.

10. **Contract deviations**

None.

11. **Open questions**

None. No `D<n>` in scope is open.
