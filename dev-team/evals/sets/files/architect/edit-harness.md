# Harness — architect eval 2: `/dev-team:plan-package data <change request>`, edit

Answers as the user would state them. For any question below, answer with the fact given;
for any other question, accept the architect's own `Assumption if unanswered:`.

- Are `B` and `S` normalized to `buy` and `sell` before the record is built, leaving the
  **Trades** shape unchanged? — Yes. `Trade.side` stays `buy | sell`; only `read_export`
  accepts the aliases, case-insensitively. Neither the repo contract's shape nor any consumer
  changes.
- Does `symbols=None` mean every symbol? — Yes: `symbols: list[str] | None = None`. An
  unknown symbol yields no rows, not an error.
- Is the request one item or two? — Two, as typed: the alias (touches `ingest`) and the
  filter (touches `storage`).
- Should the alias item wait, or be folded into the filter item? — Neither. It is one change
  to a built section; file it on its own.
- Should `analysis` be re-planned in this run? — No. Name it stale in the return; re-planning
  it is `/dev-team:plan-package analysis`, later.
- Should the change re-open `data/clean` or `data/storage`? — No. The aliases are normalized
  inside `ingest`; nothing downstream sees them.
