# Decisions

## D1 — Are timestamps stored as UTC or as read?

Scope: data
Raised by: /dev-team:plan-repo (interview)
Recommendation: UTC; a value with an offset is converted, a naive value is taken as UTC.
Assumption if unanswered: UTC.
Decision: UTC.
Status: decided

## D2 — Which parser reads XVEN's `TradeTime` values?

Scope: data/ingest
Raised by: OQ-data-ingest-1
Recommendation: `python-dateutil` — exports from before 2025 mix `.` and `/` date separators and some omit seconds, which no single `strptime` format reads.
Assumption if unanswered: `python-dateutil`.
Decision: `python-dateutil`, `dateutil.parser.parse(value, dayfirst=True)`, added to `data`'s dependencies. No other section of `data` imports it.
Status: decided

## D3 — Does every log record carry a structured `event` key?

Scope: repo
Raised by: /dev-team:plan-repo (interview)
Recommendation: yes — `extra={"event": "<section>.<step>", …}` on every `INFO` line, so logs filter without parsing messages.
Assumption if unanswered: yes, as recommended.
Decision:
Status: open
