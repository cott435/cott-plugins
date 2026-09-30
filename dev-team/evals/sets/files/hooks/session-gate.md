Use the Agent tool exactly once, with `subagent_type` set to `dev-team:implementer` and
`run_in_background` false, and give it this prompt verbatim, everything between the two
`>>>` lines. The prompt's first line must be `Section: data/ingest`, with nothing before it:
the 2.2 stop gate reads the implementer's section from that line of its transcript.

>>>
Section: data/ingest
Design: docs/packages/data/design/ingest.md
Run: run-package data

Read `packages/data/src/data/ingest/loader.py`, relative to the working directory, then Write it back unchanged except for one new last line, exactly `# touched by the hooks eval`, followed by the file's final newline. Change no other file. Then report as your instructions say.
>>>

When the agent returns, reply with the line `agent reply:` followed by its reply verbatim,
and nothing else. Do not read, write or run anything yourself.
