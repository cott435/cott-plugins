Mode: new

# Design — `data/surface`

## 1. Purpose and scope

The package's public surface and its one pipeline. It exposes the two public names the
contract's **Public surface (intent)** lists, documents the BarFrame shape the package
provides, and runs `daily`: fetch each symbol's bars, clean them, land them as parquet. It
adds no cleaning or fetching logic of its own.

## 2. Inputs and outputs

- In: `data.ingest.fetch_bars` and `data.clean.clean_bars`, as their READMEs' **Entry points
  and interfaces** give them; the errors `VendorUnavailable` (`ingest/errors.py`) and
  `EmptyBars` (`clean/errors.py`), which the two READMEs' **Files** tables name as used by
  the `daily` pipeline; the environment variable `DATA_LANDING_DIR`.
- Out: `import data` exposing `fetch_bars` and `clean_bars`; one parquet file per symbol
  under `DATA_LANDING_DIR/<run_date>/`; the `data-daily` command's exit code;
  `docs/packages/data/interface.md`.

Upstream packages: none

## 3. Data model / internal contracts

No state. `<run_date>` is the run's `end` date in ISO form. BarFrame is a shape, not a
type: the seven columns the repo contract's **Boundaries** names, in that order. Nothing is
exported for it.

**Module plan**

| module | holds | lines (est.) |
|---|---|---|
| `__init__.py` | `__all__`, the lazy `__getattr__` that imports each public name from its section on first access | 30 |
| `pipelines.py` | `daily`, `main` | 90 |

entry point: `[project.scripts]` `data-daily = data.pipelines:main`, written by this
section in `packages/data/pyproject.toml`.

## 4. Workflow / pipeline

`daily`, for each symbol in the order given:

1. **Fetch** — `fetch(symbol, start, end)`, where `fetch` is `fetch_bars` unless the caller
   passes a replacement. `VendorUnavailable` is not caught: it ends the run.
2. **Clean** — `clean_bars` on the fetched frame. `EmptyBars` skips the symbol: one
   `data.daily.skipped` event (§6), nothing written, on to the next symbol.
3. **Land** — write the cleaned frame to `<landing_dir>/<run_date>/<symbol>.parquet`
   without its index (D3, open: one file per symbol is the assumption). The run's folder is
   created when missing.
4. **Return** — the paths written, in symbol order.

`main` parses `SYMBOL [SYMBOL ...] --start YYYY-MM-DD --end YYYY-MM-DD`, reads
`DATA_LANDING_DIR`, calls `daily`, and maps the outcome to an exit code (§6).

## 5. Interfaces

| name | signature | use | Public |
|---|---|---|---|
| `fetch_bars` | as `data/ingest`'s README gives it | re-exported from `data` | yes |
| `clean_bars` | as `data/clean`'s README gives it | re-exported from `data` | yes |
| `daily` | `(symbols: Sequence[str], start: date, end: date, landing_dir: Path, fetch: Callable[[str, date, date], DataFrame] = fetch_bars) -> list[Path]` | `main`; tests pass `fetch` in place of the vendor | no |
| `main` | `(argv: Sequence[str] \| None = None, fetch: Callable[[str, date, date], DataFrame] = fetch_bars) -> int` | the `data-daily` command | no |

`__all__` is exactly the `Public: yes` names. `import data` imports neither section and no
third-party package.

## 6. Error handling and logging

| case | behavior |
|---|---|
| `VendorUnavailable` from `fetch` | `daily` lets it propagate; `main` logs `log.error("data.daily.aborted", extra={symbol})` and returns 2 |
| `EmptyBars` from `clean_bars` | `log.info("data.daily.skipped", extra={symbol})`; the symbol is skipped |
| a name `data` does not export | `AttributeError` from `__getattr__` |
| the run finished | `main` returns 0 |

Nothing else is caught.

## 7. Tests

Intent tests (the vendor is replaced by a `fetch` callable built in `conftest.py`: two days
of bars for any symbol, and an empty BarFrame for the symbol `NONE`; files land under
`tmp_path`):

- `data.__all__` is `clean_bars` and `fetch_bars`; both resolve to callables; an unknown
  name raises `AttributeError`.
- `daily` lands `<run_date>/<symbol>.parquet` per symbol (D3, open).
- A landed file reads back with the seven BarFrame columns in order.
- A symbol with no bars is skipped, logged as `data.daily.skipped` with its `symbol`, and the
  other symbols still land.
- `VendorUnavailable` from `fetch` leaves `daily`; `main` returns 2 for it and 0 otherwise.

Unit tests cover the run folder's creation, the order of the returned paths, and that
`__getattr__` caches what it imports.

## 8. Pitfalls and risks

1. Importing a section at the top of `__init__.py` makes `import data` load pandas for a
   caller that only wants the command's `--help`.
2. Catching `VendorUnavailable` inside the loop would land a partial run that looks whole.

## 9. Skills used

- `project-structure` — module placement and sizes.
- `python-style-guide` — docstrings, exceptions.
- `workspace-scaffold` — the `[project.scripts]` entry.

## 10. Contract deviations

None.

## 11. Open questions

- OQ-data-surface-1 → D3 (open; designed against the assumption: one file per symbol).
- D3 binds this section: §4 step 3, the landed file's name.
- D1 binds data/clean, not this one.
- D2 binds data/clean, not this one.
