Mode: new

# Design — `data/surface`

Designed 2026-10-02, right after PLAN, from `docs/packages/data/contract.md` (row `surface`;
**Section interfaces**, **Pipelines**, **Call paths**, **Public surface (intent)**) and
`docs/architecture.md`. No sibling has been designed or built and no sibling README exists:
every sibling name below — `ingest.PolygonClient`, `ingest.fetch_bars`, `ingest.IngestError`,
`clean.clean_bars` — is the contract's **Section interfaces** entry, and the implementer
reconciles each against the shipped README when this section is built, last.

1. **Purpose and scope**

Owns the package's public surface: the `daily` pipeline that chains the sections, the
`data-daily` command that runs it, the settings the run reads from the environment, and the
public names `from data import <name>`. Does not fetch, parse, validate or de-duplicate a bar —
that is `ingest` and `clean` — and never reads a `Bar`'s fields: rows pass through it.

2. **Inputs and outputs**

Upstream packages: none

- In: `run_date: date` (the command's `--run-date`, ISO); the environment — `DATA_VENDOR_KEY`,
  `DATA_SYMBOLS`, `DATA_LANDING_DIR`, `DATA_BASE_URL` (contract **Package conventions**).
- Siblings consumed, by the contract's **Section interfaces**: `ingest.PolygonClient` (built
  once), `ingest.fetch_bars` (once per symbol), `ingest.IngestError` (the abort),
  `clean.clean_bars` (once, over every symbol's rows).
- Out: the landing file `<DATA_LANDING_DIR>/<run_date>.csv`, a `BarTable` written with a header
  row in `docs/architecture.md` Boundaries column order and no index column; its `Path`
  returned, and printed by the command.

3. **Data model / internal contracts**

- `DataError(Exception)` — attributes `reason: str`, `detail: str`; `str()` is
  `f"{reason}: {detail}"` per the repo error convention.
- `DataSettings` — frozen dataclass; fields in this order: `vendor_key: str`,
  `symbols: tuple[str, ...]`, `landing_dir: Path`, `base_url: str = "https://api.polygon.io"`.
  `DataSettings.from_env() -> DataSettings` reads the four variables; `DATA_SYMBOLS` is split on
  `,` with blanks dropped.

**Module plan** (under `packages/data/src/data/`; `ingest/` and `clean/` beneath it are the
siblings' paths, not this section's):

| module | defines | §5 interfaces |
|---|---|---|
| `models.py` | `DataError` | `DataError` |
| `configs.py` | `DataSettings`, `from_env` | `DataSettings` |
| `pipelines.py` | `daily_pipeline`; binds `PolygonClient`, `fetch_bars` and `clean_bars` as module attributes (imported by name from `data.ingest` and `data.clean`) so a test replaces any of them with `monkeypatch.setattr("data.pipelines.<name>", fake)` | `daily_pipeline` |
| `cli.py` | `main`, the argument parser | `main` |
| `__init__.py` | re-exports `DataError`, `DataSettings`, `daily_pipeline`, `main` — the public surface (`interface.md`): every §5 name is imported `from data import <name>`, never from the defining module | — |

4. **Workflow / pipeline** (the package pipeline `daily`)

Call paths entry: `data-daily` (budget 8) — vendor call `1 cli.main → 2 pipelines.daily_pipeline
→ 3 ingest.fetch_bars → 4 ingest.PolygonClient.get → urllib.request.urlopen`; file write
`1 cli.main → 2 pipelines.daily_pipeline → DataFrame.to_csv`.

Frame 2, the pipeline, in `pipelines.md`'s shape:

```python
def daily_pipeline(run_date: date) -> Path:
    # settings from the environment — a private phase, off the path (§3)
    settings = DataSettings.from_env()
    # the vendor client, built once: the contract's ingest.PolygonClient
    client = PolygonClient(settings.vendor_key, settings.base_url)
    # frame 3, once per symbol, a one-day range: the contract's ingest.fetch_bars;
    # an IngestError propagates and aborts the run before anything is written
    fetched = [fetch_bars(symbol, run_date, run_date, client=client) for symbol in settings.symbols]
    # the contract's clean.clean_bars, every symbol's rows together, in symbol order
    table = clean_bars(chain.from_iterable(fetched))
    # the file write: the effect, once, after every fetch succeeded
    path = settings.landing_dir / f"{run_date.isoformat()}.csv"
    table.to_csv(path, index=False)
    # one INFO record (§6), then return the landing path
    return path
frames to effect: 3 (vendor call, through ingest.fetch_bars → ingest.PolygonClient.get); 1 (file write)
```

Frame 1, the command:

```python
def main(argv: Sequence[str] | None = None) -> int:
    # parse --run-date (required, ISO date); argparse exits 2 on a bad or missing value
    args = _parse(argv)
    # frame 2
    path = daily_pipeline(args.run_date)
    # the landing path on stdout, one line
    print(path)
    return 0
frames to effect: 4 (vendor call); 2 (file write)
```

Steps, as the pipeline runs them:

1. `DataSettings.from_env()`. Trigger: `daily_pipeline` called. Output: a `DataSettings`.
   Failure: §6 — a missing variable or no symbols raises `DataError` before any sibling is
   called.
2. `PolygonClient(settings.vendor_key, settings.base_url)`, once. Output: the client every
   fetch shares.
3. `fetch_bars(symbol, run_date, run_date, client=client)` for each symbol of
   `settings.symbols`, in order, `retries` left at its default. Output: one `tuple[Bar, ...]`
   per symbol. Failure: an `IngestError` from any symbol propagates unchanged; no later symbol
   is fetched, `clean_bars` is not called, nothing is written.
4. `clean_bars(<every symbol's rows, in fetch order>)`, once. Output: a `BarTable`.
5. `table.to_csv(settings.landing_dir / f"{run_date.isoformat()}.csv", index=False)`. Output:
   the file, header row in `BarTable` column order.
6. Log one INFO record `event=data.surface.daily run_date=<run_date> symbols=<k> rows=<n>`
   (`k` the symbol count, `n` the table's row count) and return the path.

`main` wraps the pipeline: on `IngestError` or `DataError` it writes `error: <str(exc)>` and a
newline to stderr, writes nothing to stdout, and returns 1.

5. **Interfaces**

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `DataError` | `DataError(reason: str, detail: str)` | `main`; `features` | yes | — |
| `DataSettings` | frozen dataclass, fields in §3 order; `DataSettings.from_env() -> DataSettings` | `daily_pipeline` | yes | `DataError` `"missing setting"`, `"no symbols"` |
| `daily_pipeline` | `(run_date: date) -> Path` | `main`; `features` | yes | `IngestError` (from `ingest.fetch_bars`, unchanged); `DataError` (§6) |
| `main` | `(argv: Sequence[str] \| None = None) -> int` | the `data-daily` console script | yes | exit code 1 on `IngestError` or `DataError`; `SystemExit(2)` from argparse on a missing or malformed `--run-date` |

6. **Error handling and logging**

- `DATA_VENDOR_KEY`, `DATA_SYMBOLS` or `DATA_LANDING_DIR` unset → `DataError(reason="missing
  setting", detail=<the variable name, the first missing in that order>)`.
- `DATA_SYMBOLS` set but holding no ticker after splitting (`""`, `","`) →
  `DataError(reason="no symbols", detail="DATA_SYMBOLS")`.
- An `IngestError` raised by `ingest.fetch_bars` for any symbol propagates out of
  `daily_pipeline` unchanged; `clean_bars` is not called and the landing directory is left as it
  was.
- `main` catches `IngestError` and `DataError` only: `error: <str(exc)>` on stderr, nothing on
  stdout, return 1. Anything else propagates.
- Each successful `daily_pipeline` logs exactly one record at INFO on the logger
  `data.surface`, message `event=data.surface.daily run_date=<run_date> symbols=<k> rows=<n>`.
  Nothing else is logged at INFO or above on the happy path; a failed run logs nothing.

7. **Tests**

Fakes, all in `conftest.py`, built to the contract's **Section interfaces** — no sibling README
exists yet — and installed on `data.pipelines` with `monkeypatch.setattr("data.pipelines.<name>",
fake)` (§3 Module plan): a fake `PolygonClient`, a callable taking what the contract's
constructor takes and returning one sentinel object, recording its arguments; a fake
`fetch_bars` with the contract's signature, recording every call's `symbol`, `start`, `end`,
`client` and `retries`, returning a queued `tuple` of two stand-in rows per call (this section
never reads a `Bar`'s fields) or raising a queued `IngestError`; a fake `clean_bars` with the
contract's signature, recording `list(bars)` and returning a four-row `BarTable` built to
`docs/architecture.md` Boundaries (`AAPL` and `MSFT`, two sessions each). `IngestError` for the
abort case is the contract's `ingest.IngestError`, imported from `data.ingest` inside the test.
The environment: `monkeypatch.setenv` for `DATA_VENDOR_KEY=secret-key`, `DATA_SYMBOLS=AAPL,MSFT`,
`DATA_LANDING_DIR=<tmp_path>`.

- `DataError("missing setting", "DATA_VENDOR_KEY")`: `str()` is
  `"missing setting: DATA_VENDOR_KEY"`, `.reason` and `.detail` set.
- `DataSettings.from_env()` with the three variables set → `vendor_key == "secret-key"`,
  `symbols == ("AAPL", "MSFT")`, `landing_dir == tmp_path`, `base_url == "https://api.polygon.io"`.
- `dataclasses.fields(DataSettings)` names are exactly `vendor_key, symbols, landing_dir,
  base_url`; the instance is frozen.
- `DATA_BASE_URL=https://example.test` → `base_url == "https://example.test"`.
- `DATA_VENDOR_KEY` unset → `DataError` with `reason == "missing setting"` and
  `detail == "DATA_VENDOR_KEY"`.
- `DATA_SYMBOLS=","` → `DataError` with `reason == "no symbols"`.
- `daily_pipeline(date(2024, 3, 6))` → the fake `PolygonClient` was called once with
  `("secret-key", "https://api.polygon.io")`.
- `daily_pipeline(date(2024, 3, 6))` → the fake `fetch_bars` saw exactly two calls, in order
  `AAPL` then `MSFT`, each with `start == end == date(2024, 3, 6)`, `client` the sentinel the
  fake `PolygonClient` returned, and `retries` at the contract's default.
- `daily_pipeline(date(2024, 3, 6))` → the fake `clean_bars` saw one call whose rows are the
  four stand-ins in fetch order.
- `daily_pipeline(date(2024, 3, 6))` returns `tmp_path / "2024-03-06.csv"`; the file exists and
  its first line is `symbol,ts,open,high,low,close,volume`.
- The fake `fetch_bars` raises `IngestError("vendor 500", "MSFT")` on its second call →
  `daily_pipeline` raises that `IngestError` (`reason == "vendor 500"`), `clean_bars` was never
  called, and `tmp_path` holds no file.
- `daily_pipeline(date(2024, 3, 6))`: `caplog` holds one INFO record on `data.surface` whose
  message is `event=data.surface.daily run_date=2024-03-06 symbols=2 rows=4`.
- `main(["--run-date", "2024-03-06"])` → returns 0; `capsys` stdout is the landing path and a
  newline; stderr empty.
- `main(["--run-date", "2024-03-06"])` with the fake `fetch_bars` raising
  `IngestError("vendor 500", "MSFT")` → returns 1; stderr is `error: vendor 500: MSFT\n`;
  stdout empty.
- `main([])` → `SystemExit` with `code == 2`.
- End to end: `main(["--run-date", "2024-03-06"])` with every fake installed → 0; the fake
  `fetch_bars` saw `AAPL` and `MSFT` with `start == end == date(2024, 3, 6)`; the file
  `2024-03-06.csv` under `tmp_path` has four data rows after its header; one INFO record on
  `data.surface`.

8. **Pitfalls and risks**

1. Calling `fetch_bars` with a range wider than one day makes the pipeline re-land sessions
   `clean` has already seen; the range is `run_date` to `run_date` and nothing else.
2. Writing the landing file before every symbol has fetched leaves a partial file behind on an
   `IngestError`; the write is the last step.
3. A `print` of the path inside the pipeline would put the command's stdout contract in the
   wrong frame; only `main` prints.

9. **Skills used**

- `project-structure` — the surface's place in the package, module sizes.
- `python-style-guide/references/pipelines.md` — the skeleton shape in §4.

10. **Contract deviations**

None.

11. **Open questions**

None. D2 is scoped to `data/ingest`, not this section; no `D<n>` in scope is open.
