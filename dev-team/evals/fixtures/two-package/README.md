# Fixture — `two-package`

A complete input to the new-repo workflow that needs no network and no credentials. Every
behavioral eval from 0.5 on runs against it, so results are comparable across phases. The
design is `site/notes/overhaul-0.5-09-evals-and-fixture.md`.

## What is here

| Path | What |
|---|---|
| `docs/brief.md` | the brief, already shaped (`Status: ready`) — `shape-brief` is skipped |
| `docs/constraints.md` | coverage 80, `mypy --strict`, docstrings 95 — used from phase 6 on |
| `data/trades.csv` | 400 synthetic trades: `ts` (ISO, UTC), `symbol` (3 values), `price`, `size`, `side`; two exact duplicate rows and one out-of-order timestamp, on purpose |
| `reset.sh` | the only executable in `evals/` |

The brief asks for two packages: `data` — `ingest` (reads `data/trades.csv`,
`source: dataset:trades`), `clean` (dedupe and sort; depends on `ingest`), `storage` (SQLite
through `sqlite3`; depends on `clean`) — and `analysis` — `features` (rolling VWAP per symbol,
consuming `data.load_trades`) and `report` (a markdown summary; depends on `features`).
Three sections in `data`, so spine-first picks `ingest`; two in `analysis`, so it plans in one
run.

## Reset

```
evals/fixtures/two-package/reset.sh [--no-constraints] [dest]
```

Copies the fixture to `dest` (default: a fresh `mktemp` directory), runs `git init`, commits
an empty root on `main`, creates branch `build`, and commits the brief and the dataset there —
agents refuse to commit on `main`. Prints the created path as its last line. Pass
`--no-constraints` for evals from phases before 6, which predate `docs/constraints.md`.

Never run the plugin inside this directory: the fixture is the pristine input, and a run
writes `docs/`, `packages/` and commits.

## What each eval expects of it

| Eval | Phase | Expects |
|---|---|---|
| D | 2 | after `plan-repo`, `plan-package data` and `implement-section data/ingest`: `status.py` reads the three review states from commits; `git show --stat HEAD` is exactly the implementer's paths, with a `Dev-Team-Run: implement-section data/ingest` trailer |
| E–J | 3–8 | per `site/notes/overhaul-0.5-09-evals-and-fixture.md` |
| K | 9 | the whole two-package build: both packages `shipped`, `398` rows stored, one commit per run |
