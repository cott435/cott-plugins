# Package contract — data (excerpt: what the `clean` section needs)

In the repo this is `docs/packages/data/contract.md`.

## Sections

| section | path | responsibility | depends on | source | builds with |
|---|---|---|---|---|---|
| `download` | `src/data/download/` | pull one session day of trade prints from the vendor and store them raw | — | `api:tradefeed` | — |
| `clean` | `src/data/clean/` | turn the raw trade prints `download` stored into trades the rest of the package can trust | `download` | `stage:rawtrades` | `dev-team:data-quality`, `trade-cleaning` |

## Shapes

`RawTrade`, one row per trade, as `download` stores it and as `clean` receives it (a `dict`):

| field | type | rule |
|---|---|---|
| `seq` | int | the line number in the vendor file; the row's key |
| `trade_id` | str | one row per trade |
| `symbol` | str | in the universe |
| `ts` | str | ISO 8601 with offset |
| `price` | float | above zero |
| `size` | int | above zero |
| `side` | str | `B` or `S` |
| `venue` | str | in the venue list |

`clean`'s entry point is `clean(rows: list[dict]) -> CleanResult`. A `Trade` is a `RawTrade`
that `clean` accepted.

## Package conventions

- `stage:rawtrades` — the raw trade prints `download` stored, one row per print; lands at `data/raw/trades/`; pull cap 5 session days, D5
- Universe: `AAPL`, `MSFT`, `NVDA`, `TSLA`.
- Venue list: `XNAS`, `XNYS`, `ARCX`, `BATS`, `XOFF`.
- Regular session: 09:30:00 up to, not including, 16:00:00, America/New_York.
- Rows `clean` does not accept, and rows it changes, are stored by its caller in the table
  `trades_rejects`; `clean` itself returns them and writes no store.
