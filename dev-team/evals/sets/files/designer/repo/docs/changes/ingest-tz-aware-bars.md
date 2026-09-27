# Change — ingest-tz-aware-bars

Written by `/dev-team:plan-package data` on 2026-09-26 (CHANGE outcome: `ingest` is shipped,
so the canonical contract stays as shipped until `sync-plan` applies this).

## Change goal

The broker's CSV exports carry exchange-local timestamps with no offset, while Alpaca bars
are UTC. Today `ingest` emits a naive `Bar.ts` that `storage` would write beside tz-aware
Alpaca bars and mis-order. `ingest` must emit tz-aware UTC timestamps, converting from a
caller-supplied zone.

## Affected sections

- `data/ingest` — the change.
- `data/storage` — planned consumer of `Bar.ts`; designs against the changed shape.
- `data/surface` — planned; `ingest_csv` passes the zone through.

## Contract changes

### Package contract: data

- Changed: `load_bars(paths: Iterable[Path]) -> Iterator[Bar]` becomes
  `load_bars(paths: Iterable[Path], *, tz: str = "America/New_York") -> Iterator[Bar]`; `tz`
  is the IANA zone the CSV's timestamps are in; every yielded `Bar.ts` is tz-aware UTC.
- Added: `IngestError` code `data.ingest.unknown_tz` when `tz` is not an IANA zone.
- Changed (Pipelines): `ingest_csv(root, db_path=None)` gains `tz: str = "America/New_York"`,
  passed to `load_bars`.
- Unchanged: `discover_files`, `Bar`'s fields.

### Repo contract

- Unchanged: `Bar.ts` was already specified tz-aware UTC in **Boundaries**; `ingest`'s naive
  timestamp was a shipped deviation this change removes.

## Downstream impact

| consumer | state | names affected | what breaks |
|---|---|---|---|
| data/storage | planned | `Bar.ts` | nothing built yet; design against tz-aware UTC |
| data/surface | planned | `ingest_csv` | gains the `tz` parameter |
| analysis | planned | `Bar.ts` | nothing built yet |

Status: open
