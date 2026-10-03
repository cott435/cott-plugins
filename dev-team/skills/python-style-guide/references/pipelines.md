# Pipelines and orchestrators

A package is read from its command down. `cli.py` calls a pipeline, the pipeline calls
section entry points, and an entry point either does one thing or runs its section's phases
in order. This file is the shape of the two functions in the middle, the pipeline and the
orchestrating entry point, so that a reader who opens one can say what the package does
without opening anything else.

Read it before writing a function under `pipelines/`, before writing a section entry point
that runs more than one phase, and before judging either.

## The shape of a pipeline

A pipeline is the steps of one contract **Pipelines** entry, as calls, in order.

```python
def run_build(*, start: date, end: date, account: str) -> BuildSummary:
    """Download, clean and store the bars for one account; record the run in `runs`."""
    settings = load_settings()

    with recorded_run("build", account=account) as run:
        # Fetch the vendor's bars for the window.
        raw = download_bars(account, start=start, end=end, client=settings.vendor)

        # Drop bars outside the session and fill single-bar gaps.
        bars = clean_bars(raw, calendar=settings.calendar)

        # Write the cleaned bars and the run's row counts.
        stored = store_bars(bars, run_id=run.id)

    return BuildSummary(run_id=run.id, rows=stored.rows)
```

- One call statement per step, in the contract's order, each under a one-line comment that
  says what the step is for.
- Each callee is a section entry point, imported at the top of the module, by name or through
  its module (`ingest.download_bars(…)`).
- Inputs are keyword arguments; each result is bound to a name the next step reads.
- No logic of the pipeline's own beyond passing one step's result to the next. A loop over
  accounts or dates is one statement around the steps, not a helper that hides them.

## The shape of a section orchestrator

An entry point that runs its section's phases in order is the same shape one level down: the
phases are calls to functions of the section, in the order the design's **Workflow /
pipeline** lists them.

```python
def download_bars(account: str, *, start: date, end: date, client: VendorClient) -> RawBars:
    """Download one account's bars from the vendor, one request per trading day."""
    days = trading_days(start, end)

    # One request per day: the vendor caps a response at a day of bars.
    pages = [fetch_day(client, account, day) for day in days]

    return merge_pages(pages)
```

An entry point that does one thing has no phases to order and is not an orchestrator.

## Wrapping behaviour

A guard, a retry, a transaction or a run ledger wraps a step without becoming a frame the
reader has to pass through:

```python
# Yes: the step is still a direct call.
with recorded_run("build", account=account) as run:
    raw = download_bars(account, start=start, end=end, client=client)

# Yes: the wrapping is on the step's own definition.
@retry(times=3, on=VendorTimeout)
def fetch_day(client: VendorClient, account: str, day: date) -> Page: ...

# No: the step is handed to the wrapper, and the path now runs through a lambda.
raw = guarded(lambda: download_bars(account, start=start, end=end, client=client))
```

## Dispatch

Choosing a step by a value is written so each target can be read at the call site:

```python
# Yes
match stage:
    case "market":
        rows = load_market(account, day)
    case "reference":
        rows = load_reference(account, day)

# No: the reader has to find the mapping, then the key, to learn what runs.
rows = _RUNNERS[stage](account, day)
```

A mapping of callables is fine where the set is open (a plug-in registry) and off the main
path. On it, the branches are few and fixed, and they are named.

## The reader's test

Open the pipeline, or the orchestrating entry point, and nothing else. It passes when all
four hold:

1. **Steps in order** — every step of the contract's **Pipelines** entry (for a section
   orchestrator, of the design's **Workflow / pipeline**) is one call statement in the body,
   in that order, under a one-line comment saying what the step is for.
2. **Jump by name** — every step's callee is a function defined with `def`, reached by an
   imported name or as an attribute of an imported module. No lambda, no nested function
   passed as an argument, no `functools.partial`, no callable pulled from a mapping, no
   callable received as a parameter.
3. **Named inputs and results** — each step's arguments are named values (keyword arguments
   past the first), and each result is bound to a named variable. No `**options` bag and no
   tuple packed to carry several values.
4. **Wrapping in view** — behaviour that wraps a step is a `with` block around the call or a
   decorator on the step's definition, never a function that takes the step as an argument.

## Depth

`project-structure` §2 gives the main-path depth: the frames from a command function to its
first effect outside the package. A command, a pipeline, a section entry point and two or
three frames inside the section reach a client well inside it. A path that needs more is
usually a pipeline whose steps were pushed down into helpers, which items 1 and 2 above put
back.
