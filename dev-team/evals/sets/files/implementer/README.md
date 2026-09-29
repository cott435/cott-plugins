# Fixtures for `evals/sets/implementer.json`

Small repos, one per eval that needs one, each the state a `run-package data` run would find on
disk when it spawns the implementer on one section. Read-only: an executor writes into its
`outputs/`.

| Directory | Eval | Section | What is planted |
|---|---|---|---|
| `clean-deviation/` | 9 | `data/clean` | the design's dedupe clause (`set(rows)`, "Trade is a frozen dataclass") is unimplementable: the shipped `ingest` README says `Trade` is mutable and unhashable. Internal to the section, so it is a `deviation`, `Status: proposed`. No ledger at any location |
| `storage-spec-change/` | 10 | `data/storage` | the contract's Section interfaces row says `clean_trades(rows: list[Trade]) -> list[Trade]`; the shipped `clean` README says it returns `CleanResult`. A consumed shipped signature the contract names, so it is `spec-change:contract`. No ledger at any location |
| `parallel-batch/` | 11 | `data/ingest` | a first IMPLEMENT while a sibling implementer builds `data/calendar` in the same batch: `calendar/sessions.py` is half-built with an unused import (ruff F401) and `tests/intent/calendar/` errors at collection. The design's §9 names the project skill `venue-csv` (`.claude/skills/venue-csv/SKILL.md`), whose rules the 7 intent tests hold the code to; §3 names one new dependency (`python-dateutil`, D2) and one `.gitignore` pattern (`data/raw/`). `docs/decisions.md`: D1 decided (scope `data`), D2 decided (scope `data/ingest`), D3 open with an assumption (scope `repo`) |
| `fix-round-sibling/` | 12 | `data/clean` | a FIX round (`Round: 2`) after a round-1 pair under `docs/packages/data/reviews/clean/` (2.2 layout), both `Verdict: request changes`: one CRITICAL, `_dedupe` walks `reversed(rows)` (rules.py:32), so rows tied on `(ts, symbol)` come out in reverse file order — the shipped 5 intent and 4 unit tests all pass on it; one WARNING, an f-string log line (rules.py:56). `docs/decisions.md`: D1 decided (scope `data`), D2 open (scope `repo`, no line of `clean` affected) |

`clean-deviation/` and `storage-spec-change/` keep the 2.0/2.1 layout they were written in:
neither holds a ledger, a review or an inbox, so nothing in them is read at a moved path, and a
2.2 run writes its ledger and inbox under `docs/packages/data/` from scratch. The two 2.2
fixtures are laid out at the 2.2 paths.

Every tree holds `docs/architecture.md`, `docs/packages/data/contract.md`, the section's design,
`docs/decisions.md`, a root and package `pyproject.toml`, `.gitignore` (with `.dev-team/`), and
`packages/data/tests/intent/<section>/`; 9, 10 and 12 also hold the shipped sibling sections
their section depends on, with READMEs. No `docs/constraints.md`, no probe docs, no change
file.
