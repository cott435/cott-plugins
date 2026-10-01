Mode: new

# Design — `data/ingest`

Written 2026-10-01 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Reads one XVEN export file into **Trade** rows, in file order, with timestamps in UTC. Owns
the venue's file dialect and nothing else: no dedupe, no sorting, no calendar logic, no
fetching (the files are dropped by hand into `data/raw/`).

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `path` | `Path` — one export file | the `daily` pipeline (`data/raw/<date>.csv`) |
| out | the rows | `list[Trade]` in file order | `surface`, `analysis` |

Upstream packages: none

## 3. Data model / internal contracts

`Trade` — `@dataclass(frozen=True, slots=True)` with `ts: datetime`, `symbol: str`,
`price: float`, `size: int`, `side: str`, the **Trade** shape of the repo contract. No state,
no configuration (`configs.py` is not needed).

**Module plan** — under `packages/data/src/data/ingest/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports `load_export`, `Trade`, `IngestError` | — |
| `loader.py` | `Trade`, `IngestError`, `load_export`, the dialect's per-line parse | `load_export`, `Trade`, `IngestError` |

entry point: venuedata.readers xven = data.ingest.loader:load_export

The `daily` pipeline looks a venue's reader up by the venue's name in the entry-point group
`venuedata.readers` (`importlib.metadata.entry_points(group="venuedata.readers")`), so a
second venue is a new section and no edit to the pipeline. This section owns the one entry
`xven`. It is registered in `packages/data/pyproject.toml` through `locked.py`, never by
hand.

**Dependencies** — `python-dateutil>=2.9` (D2) is added to `packages/data/pyproject.toml`;
it is the section's only third-party import.

**Repo files** — the root `.gitignore` gains `data/raw/`: the exports this section reads live
there, are large, and are never committed (repo contract, Shared conventions).

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), once per trading day's file.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 | `load_export(path)` is called | open the file, UTF-8 | lines | `IngestError` naming the file when it cannot be read |
| 2 | — | read the lines in the venue's dialect, as the project skill `venue-csv` (§9) prescribes — its rules are the skill's and are not restated here | header row and data rows | `IngestError` naming `<file name>:<line>` for a missing column |
| 3 | — | each data row → `Trade`: `ts` parsed with `python-dateutil` (D2) and converted to UTC (D1); `side`, `size`, `price` per `venue-csv` | `Trade` | `IngestError` naming `<file name>:<line>` for a cell that does not parse or an unknown side code |
| 4 | — | log `rows_out`; return the rows in file order | `list[Trade]` | — |

Line numbers in errors are the ones `venue-csv` defines.

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `load_export` | `(path: Path) -> list[Trade]` | `surface`, the `daily` pipeline (through the `xven` entry point) | no | `IngestError` on a missing column, a bad cell or an unknown side code, naming `<file name>:<line>`; a file with no data rows returns `[]` |
| `Trade` | `@dataclass(frozen=True, slots=True)` — the **Trade** shape | everyone | yes | — |
| `IngestError` | `class IngestError(ValueError)` | `surface` | no | — |

## 6. Error handling and logging

Logger `data.ingest`. One `INFO` line per file at step 4 with `path` and `rows_out` in
`extra=`, plus the `event` key D3's assumption asks for. Messages name the file and the line,
never a row's contents (repo contract, Shared conventions). `IngestError` is the one
exception type this section raises. No retries.

## 7. Tests

Unit (`packages/data/tests/unit/ingest/`): the per-line parse on a separator-bearing `Qty`;
an unknown side code; a comment line between data rows; a file with only comments and the
header row returns `[]`.

Intent (`packages/data/tests/intent/ingest/`, the tester's): one file per §5 row.

Fixtures: small export files written to `tmp_path` in each suite's `conftest.py`.

## 8. Pitfalls and risks

1. `TradeTime` with an offset — convert with `astimezone(timezone.utc)`, never
   `replace(tzinfo=…)`, which relabels without converting.
2. Line numbers drift when comment lines are dropped before counting; count first.
3. `python-dateutil` guesses month-first on ambiguous dates unless told otherwise (D2 says how).
4. An entry point whose target module does not exist yet breaks every run that loads the
   `venuedata.readers` group; `loader.py` comes first.

## 9. Skills used

- `venue-csv` — the project skill at `.claude/skills/venue-csv/`: the export's dialect, which
  step 2 and step 3 follow rule by rule.
- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.
- `project-structure` — one module under the section path; no `configs.py` when there is no
  configuration.

## 10. Contract deviations

None.

## 11. Open questions

- OQ-data-ingest-1 — which parser reads `TradeTime` — is D2, decided.
- D3 binds this section: §6's `event` key on the step-4 log line.
