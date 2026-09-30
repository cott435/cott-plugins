Use the Agent tool exactly once, with `subagent_type` set to `dev-team:designer` and
`run_in_background` false, and give it this prompt verbatim, everything between the two
`>>>` lines:

>>>
Section: data/ingest
Design: docs/packages/data/design/ingest.md
Run: run-package data

You are stopping for one decision. Write the file `docs/packages/data/decisions/ingest.md`, relative to the working directory, with the Write tool, with exactly this content, byte for byte; the file ends with one newline; keep the heading's `D?` as it is.

```markdown
# Decisions — data/ingest

## D? — Does ingest reject or skip a row whose side is neither buy nor sell?
Scope: data/ingest
Raised by: OQ-data-ingest-1
Recommendation: Reject it: raise ValueError naming side, as for a missing field.
Assumption if unanswered: Reject, raising ValueError naming side.
Status: open
```

Then Read the file once and report as your instructions say.
>>>

When the agent returns, reply with the line `agent reply:` followed by its reply verbatim,
and nothing else. Do not read, write or run anything yourself.
