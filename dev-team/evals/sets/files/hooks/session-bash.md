Use the Agent tool exactly once, with `subagent_type` set to `dev-team:implementer` and
`run_in_background` false, and give it this prompt verbatim, everything between the two
`>>>` lines:

>>>
Section: data/ingest
Design: docs/packages/data/design/ingest.md
Run: run-package data

Shell command: `echo x > packages/data/src/data/ingest/shell.py`
Check command: `test -e packages/data/src/data/ingest/shell.py && echo present || echo absent`
File: `packages/data/src/data/ingest/shell.py`, relative to the working directory.
Content, byte for byte, ending with one newline:

```python
"""Written with the Write tool after the shell write was refused."""
```

Follow your instructions' steps in order, then report as they say.
>>>

When the agent returns, reply with the line `agent reply:` followed by its reply verbatim,
and nothing else. Do not read, write or run anything yourself.
