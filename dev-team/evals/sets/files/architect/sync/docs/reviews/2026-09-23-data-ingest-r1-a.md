# Review — data/ingest — round 1 — conformance
Scope: docs/packages/data/contract.md, docs/packages/data/design/ingest.md, packages/data/src/data/ingest, packages/data/tests
Commit: 4c1d9e2
Verdict: approve
Round: 1
Focus: conformance

## CRITICAL
- none

## WARNING
- none

## SUGGESTION
- none

## Coverage
| clause or design item | pass / fail / can't-tell | file:line |
|---|---|---|
| contract §3 ingest read_export | pass | packages/data/src/data/ingest/reader.py:19 |
| contract §3 ingest side buy/sell only | pass | packages/data/src/data/ingest/reader.py:50 |
| design §6 TradeParseError row and field | pass | packages/data/src/data/errors.py:12 |
