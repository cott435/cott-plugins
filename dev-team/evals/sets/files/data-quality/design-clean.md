# Design — data/clean

In the repo this is `docs/packages/data/design/clean.md`. Written 2026-10-02 from the contract
row and the data profile `docs/sources/rawtrades.md` (round 0, closed `kinds: 6 (2 to decide)`).

## Purpose

Turn the raw trade prints `download` stored into trades the rest of the package can trust.

## Interface

```python
@dataclass(frozen=True)
class CleanResult:
    accepted: list[dict]   # the trades, in input order
    rejects: list[dict]    # the reject record, per data-quality


def clean(rows: list[dict]) -> CleanResult: ...
```

`rows` are `RawTrade` dicts (contract, **Shapes**). `clean` is pure: it reads no store and
writes none. Its caller stores `rejects` in `trades_rejects`. An input row is never mutated; a
changed row is a new dict.

## Workflow / pipeline

1. Run the handlers in the order of the table below. Each handler takes the rows still in
   play, isolates its kind by the rule, applies the treatment, and returns the rows that go on.
2. Check every row still in play against the profile's seven checks, C1 to C7
   (`docs/sources/rawtrades.md`, **Checks**; the universe, the venue list and the session are
   module constants taken from the contract's **Package conventions**). A row no handler
   claimed that fails one of them is handled as `data-quality` says.
3. Return `CleanResult`: the rows that passed, with the repaired and the flagged ones, in input
   order; and the reject record.

| kind | rule | handler | treatment | decided by |
|---|---|---|---|---|
| K1 negative-size | `size` is below zero | `_repair_negative_size` | repair: `size` becomes its absolute value and `side` becomes `S` | D7 |
| K2 duplicate-trade-id | the row's `trade_id` was already seen on a row with a lower `seq` | `_quarantine_duplicate_trade_id` | quarantine | — (D8 is open) |
| K3 zero-price | `price` is zero or below | `_quarantine_zero_price` | quarantine | — |
| K4 off-session | the time of `ts` is outside the regular session | `_flag_off_session` | flag: the row is accepted with `flags` set to `["K4"]` | — |
| K5 unknown-symbol | `symbol` is not in the universe | `_quarantine_unknown_symbol` | quarantine | — |

K6 odd-lot is `unverified` in the profile and has no row here. A row that is not flagged has no
`flags` key, so an accepted row equals its input row.

## Tests

Fixtures: `rawtrades.sample.json`, copied to `tests/fixtures/`.

- `test_k1_negative_size` — the `K1` rows.
- `test_k2_duplicate_trade_id` — the `K2` rows, run together with the `accepted` rows (rows
  `seq` 1041 and 7780 are their first prints).
- `test_k3_zero_price` — the `K3` rows.
- `test_k4_off_session` — the `K4` rows.
- `test_k5_unknown_symbol` — the `K5` rows.
- `test_accepted_rows` — the `accepted` rows.
- `test_row_of_no_kind` — the `K6` rows, which fail C6 and have no row in the table.

## Open questions

- OQ-data-clean-1 — K2 duplicate-trade-id is quarantined while D8 is open; a `drop` waits on
  that decision.

## Skills used

- `data-quality`
- `trade-cleaning`
