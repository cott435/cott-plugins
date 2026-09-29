Mode: new

# Design — `analysis/features`

## Purpose and scope

Rolling VWAP per symbol over a window of the last `window` trades of that symbol.

## Inputs and outputs

In: `list[Trade]` as `data.load_trades()` returns it (the **Trades** shape), and `window: int`.
Out: `list[VwapPoint]`, one point per input trade, in input order.

## Data model / internal contracts

`VwapPoint` frozen dataclass: `symbol: str`, `ts: datetime`, `vwap: float`.

### Module plan

| module | holds |
|---|---|
| `features/vwap.py` | `VwapPoint`, `rolling_vwap` |

## Workflow / pipeline

Group by `symbol`, keeping input order; per symbol, a deque of the last `window` trades;
`vwap = sum(price * size) / sum(size)` over the deque.

## Interfaces

| name | signature | public |
|---|---|---|
| `VwapPoint` | dataclass `(symbol, ts, vwap)` | no |
| `rolling_vwap` | `(trades: list[Trade], window: int) -> list[VwapPoint]` | no |

## Error handling and logging

`window < 1` raises `AnalysisError`. An empty tape returns `[]`. No logging.

## Tests

Three trades of one symbol with `window=2` give the expected three VWAPs; two symbols never
share a window; `window=0` raises `AnalysisError`.

## Pitfalls and risks

Float sums: compare with `pytest.approx`.

## Skills used

none.

## Contract deviations

none.

## Open questions

none.
