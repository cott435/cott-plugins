Use the Agent tool exactly once, with `subagent_type` set to `dev-team:implementer` and
`run_in_background` false, and give it this prompt verbatim, everything between the two
`>>>` lines. The prompt's first line must be `Section: data/ingest`, with nothing before it.

>>>
Section: data/ingest
Design: docs/packages/data/design/ingest.md
Run: run-package data

Write these two files, relative to the working directory, in this order, each with exactly the content given, byte for byte, ending with one newline. Then report as your instructions say.

1. `packages/data/src/data/ingest/schema.py`:

```python
"""Column order of the trade export."""

COLUMNS = ("ts", "symbol", "price", "size", "side")
```

2. `packages/data/src/data/clean/rules.py`:

```python
"""Which trade sides the clean section keeps."""

SIDES = ("buy", "sell")
```
>>>

When the agent returns, reply with the line `agent reply:` followed by its reply verbatim,
and nothing else. Do not read, write or run anything yourself.
