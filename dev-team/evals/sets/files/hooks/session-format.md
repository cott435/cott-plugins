Use the Agent tool exactly once, with `subagent_type` set to `dev-team:tester` and
`run_in_background` false, and give it this prompt verbatim, everything between the two
`>>>` lines:

>>>
Write the file `packages/data/tests/intent/ingest/test_parse.py`, relative to the working directory, with exactly this content, byte for byte: keep the unused import, the single quotes and the space inside the parentheses; the file ends with one newline; do not correct anything.

```python
import os


def test_parse_row( ):
    row = {'ts': '2026-09-01T13:30:20Z', 'symbol': 'AAA'}
    assert parse_row(row)['symbol'] == 'AAA'
```

Then Read the file once and report as your instructions say.
>>>

When the agent returns, reply with the line `agent reply:` followed by its reply verbatim,
and nothing else. Do not read, write or run anything yourself.
