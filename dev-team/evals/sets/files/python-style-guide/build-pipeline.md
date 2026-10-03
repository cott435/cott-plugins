# `data` package: what the `build` pipeline calls

Everything named here already exists and is shipped. The only file to write is
`src/data/pipelines/build.py`.

## From the package contract, **Pipelines**

| Pipeline | Function | Steps, in order |
|---|---|---|
| `build` | `data.pipelines.build.run_build(*, account: str, start: date, end: date) -> BuildSummary` | 1. `ingest`: download the account's bars for the window from the vendor. 2. `clean`: drop bars outside the session and fill single-bar gaps. 3. `storage`: write the cleaned bars. |

Every run is one row in `runs`, and every step of it is one row in `run_steps`. A step's row
is opened when the step starts and closed `ok` or `failed` when it ends; a failed step's row
carries the exception's text. When a step fails the run is closed `failed`, no later step
runs, and the exception reaches the caller unchanged. When all three succeed the run is
closed `ok`.

`BuildSummary` is in `data.pipelines.models`:

```python
@dataclass(frozen=True, slots=True)
class BuildSummary:
    """What one build run did."""

    run_id: int
    rows: int
```

## The three section entry points

From each section's README, **Entry points and interfaces**.

```python
# data/ingest/download.py
def download_bars(account: str, *, start: date, end: date, client: VendorClient) -> RawBars:
    """Download one account's bars from the vendor, one request per trading day."""

# data/clean/sessions.py
def clean_bars(raw: RawBars, *, calendar: Calendar) -> Bars:
    """Return the bars inside the exchange session, with single-bar gaps filled."""

# data/storage/bars.py
def store_bars(bars: Bars, *, run_id: int) -> StoredBars:
    """Write the bars to the `bars` table under one run; `StoredBars.rows` is the count."""
```

The vendor client and the calendar come from the package's settings:

```python
# data/configs.py
def load_settings() -> Settings:
    """Read the package settings from the environment."""

# Settings.vendor: VendorClient
# Settings.calendar: Calendar
```

## The run ledger

`data/storage/ledger.py`. These four functions are all it has; it has no context manager and
no decorator of its own.

```python
def open_run(pipeline: str, *, account: str) -> int:
    """Insert a `started` row in `runs` and return its id."""

def close_run(run_id: int, *, status: str) -> None:
    """Set a run's status (`ok` or `failed`) and its end time in `runs`."""

def open_step(run_id: int, step: str) -> int:
    """Insert a `started` row in `run_steps` for one step of a run and return its id."""

def close_step(step_id: int, *, status: str, error: str | None = None) -> None:
    """Set a step's status (`ok` or `failed`), its end time and its error text in `run_steps`."""
```
