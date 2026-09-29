Mode: delta
Change: docs/packages/data/deviations/clean.md, data/clean — 2026-09-27 — spec-change:design — 1

# Design — `data/clean`

## Purpose and scope

As the contract row `clean` says.

## Inputs and outputs

Per contract §3.

## Data model / internal contracts

### Module plan

| module | holds |
|---|---|
| `clean/` | per the section README |

## Workflow / pipeline

Per contract §4.

## Interfaces

Per contract §3, and:

- `sort_by_ts` — stable: two records with equal `ts` keep their input order, whatever their
  `symbol`. `clean_trades` therefore keeps the export's order among same-`ts` records.

## Error handling and logging

`DataError` base; stdlib logging.

## Tests

One intent test per interface row, and one for the tie order of `sort_by_ts`.

## Pitfalls and risks

none.

## Skills used

none.

## Contract deviations

none at design time.

## Open questions

none.
