Use the Agent tool exactly once, with `subagent_type` set to `dev-team:implementer` and
`run_in_background` false, and give it this prompt verbatim, everything between the two
`>>>` lines:

>>>
Read `packages/data/src/data/ingest/loader.py`, relative to the working directory, then Write it back unchanged except for one new last line, exactly `# touched by the hooks eval`, followed by the file's final newline. Change no other file. Then report as your instructions say.
>>>

When the agent returns, reply with the line `agent reply:` followed by its reply verbatim,
and nothing else. Do not read, write or run anything yourself.
