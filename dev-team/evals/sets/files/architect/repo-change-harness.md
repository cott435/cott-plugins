# Harness — architect eval 4: `/dev-team:plan-repo "<addition>"`, a repo-level change

Answers as the user would state them. For any question below, answer with the fact given;
for any other question, accept the architect's own `Assumption if unanswered:`.

The repo has no git history, so `status.py` cannot run. Wherever the run would read
`status.py <pkg>`, this is its output, verbatim:

```
## data
section · state · evidence · ready · round · open spec-change · last commit
ingest · DONE · review r1 approve @4c1d9e2 · no · 1 · — · 4c1d9e2
clean · DESIGN · no docs/packages/data/design/clean.md · yes · — · — · —
storage · DESIGN · no docs/packages/data/design/storage.md · no · — · — · —
surface · DESIGN · no docs/packages/data/design/surface.md · no · — · — · —
shipped: no (surface DESIGN)
next: /dev-team:run-package data

## analysis
section · state · evidence · ready · round · open spec-change · last commit
features · DONE · review r1 approve @5a8e1f3 · no · 1 · — · 5a8e1f3
report · DESIGN · no docs/packages/analysis/design/report.md · yes · — · — · —
surface · DESIGN · no docs/packages/analysis/design/surface.md · no · — · — · —
shipped: no (surface DESIGN)
next: /dev-team:run-package analysis
```

- Is this an extension or a revision of the brief? — An extension: an addition, as typed.
- Is the request one item or several? — One: the **Trades** shape gains `venue`. `data`
  provides it and `analysis` consumes it, so the one item touches both packages.
- What is `venue`'s type and nullability? — `venue: str`, non-null, an upper-case exchange
  code (`XNAS`, `XNYS`). A row with a missing or empty `venue` is a bad row, like any other
  missing field.
- Does the export already carry the column? Should `data/trades.csv` be re-probed first? —
  The analyst's newer exports carry `venue` as a sixth column, and `data/trades.csv` will be
  replaced by one before the rebuild. Do not stop for a probe; the column is as stated here.
- Is `venue` part of the dedupe key? — Yes, with no separate change: the key is the whole
  record (repo contract, Shared conventions: IDs).
- Does `VwapPoint` change? — Yes: it gains `venue: str`, and `rolling_vwap` keeps one window
  per `(symbol, venue)` instead of per `symbol`.
- Does the summary report gain a venue column? — No. `report` is planned, not built; it keeps
  one row per symbol, and nothing in this addition asks more of it.
- Do `data/clean`, `data/storage` or `data/surface` re-open? — None is built, so nothing
  re-opens them; the stored table's new column belongs in `data`'s **Contract changes**, and
  their designers read it from there.
- Does the change reverse a dependency or touch a convention the packages disagree on? — No.
- Should `data` or `analysis` be re-planned in this run? — No.
