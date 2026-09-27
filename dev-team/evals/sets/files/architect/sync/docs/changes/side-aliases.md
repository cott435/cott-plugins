# Change — side-aliases
Status: open

## Change goal

The analyst's newer exports write the `side` column as `B` and `S`. `data/ingest` accepts
`B` and `S` (case-insensitive) as aliases for `buy` and `sell` and normalizes them before
the `Trade` record is built, so the stored **Trades** shape and every consumer are unchanged.

## Affected sections

- `data/ingest` — `read_export` accepts the aliases; `SIDE_ALIASES` in `reader.py`; the
  error message for a bad `side` names the four accepted values.

## Contract changes

### Package contract: data

- Changed — §2 row `ingest`, responsibility: "read the CSV export into `Trade` records,
  accepting `B`/`S` as aliases for `buy`/`sell`; reject a row with a missing or unparseable
  field, naming the row and the field".
- Changed — §3 `ingest`: "`side` accepts `buy`, `sell` and the aliases `B` and `S`
  (case-insensitive), normalized to `buy`/`sell`; anything else is a bad row." replaces
  "`side` accepts exactly `buy` and `sell`; anything else is a bad row."

### Interface: data

- none: `Trade.side` stays `Literal["buy", "sell"]`; no public name changes.

## Downstream impact

| consumer | shipped or planned | names affected | what breaks |
|---|---|---|---|
| — | — | — | nothing: the aliases are normalized inside `ingest` |
