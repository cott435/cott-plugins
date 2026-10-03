#!/usr/bin/env python3
"""Seed repositories for `evals/sets/profiler.json`, and the collector its harness sheets name.

    python3 build.py case-<n> <dest>          build the seed repository of eval <n> in <dest>
    python3 build.py collect <dest> <outputs> copy what a run changed in <dest> into <outputs>

A seed is a small git repository: a `data` package whose `clean` section is marked
`stage:rawtrades`, the raw trades on disk under `data/raw/trades/`, and, from case 2 on, a
profile at `docs/sources/rawtrades.md` in the state the eval starts from. Every commit has a
fixed author and date, so a case's commits have the same sha on every build. The data is
`seed/trades.csv` with a few literal edits per case (`VARIANTS`); every number a seeded profile
prints is computed here from that data, by the same rules its program runs as queries.

An executor runs this file and does not read it: it holds what each case plants.
"""
from __future__ import annotations

import csv
import io
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLUMNS = ["trade_id", "symbol", "ts", "price", "size", "venue", "seq"]
RAW = "data/raw/trades/2026-09-14.csv"
STORE = ".dev-team/data/rawtrades"
PURPOSE = "validate and reconcile raw trade prints: remove duplicates, repair or reject bad rows"

# trade_id -> {column: value}, applied to seed/trades.csv.
NO_ZZ = {"500156": {"venue": "N"}}
SLIP = {"500196": {"price": "-326.00"}}
LATE = {"500100": {"symbol": "TEST"}, "500200": {"symbol": "TEST"}, "500150": {"size": "0"}}
VARIANTS = {"A": {}, "B": NO_ZZ, "C": {**NO_ZZ, **SLIP}, "D": {**NO_ZZ, **SLIP, **LATE}}

# ---------------------------------------------------------------------------- repo documents

GITIGNORE = ".dev-team/\n.venv/\n__pycache__/\n"

ARCHITECTURE = """# Architecture — trade tape

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| data | packages/data | — | pull raw trade prints, clean them |

## Toolchain

Python 3.11 or later; the `data` package uses the standard library only. A section runs as a
module, from the repo root:

```
PYTHONPATH=packages/data/src python3 -m data.<section>
```

## Data on disk

- `data/raw/trades/` — what `data/ingest` lands, one CSV per trading day. Never edited by hand.
- `data/clean/` — the project's working store, written by `data/clean`.
- `.dev-team/` — tool scratch, ignored by git.
"""

CONTRACT = """# data — package contract

## Purpose

Pulls the vendor's raw trade prints and turns them into a clean trade tape: every row either
accepted, or set aside with the reason.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | pull one trading day of trade prints from the vendor and land it unchanged | packages/data/src/data/ingest/ | docs/packages/data/design/ingest.md | csv | — | trades |
| clean | {purpose} | packages/data/src/data/clean/ | docs/packages/data/design/clean.md | dev-team:data-quality | ingest | stage:rawtrades |

## Shapes

`RawTrade`, one row of a landed file, columns in this order:

| column | type | rule |
|---|---|---|
| trade_id | integer | the vendor's id of the print; one row per id |
| symbol | text | the ticker, upper case |
| ts | text | UTC, `YYYY-MM-DDTHH:MM:SSZ`, second resolution. Within a symbol, `ts` is never earlier than the `ts` of the row before it in `seq`; an equal `ts` is valid |
| price | decimal, 2 places | above zero |
| size | integer | above zero |
| venue | text | a venue code the vendor probe lists |
| seq | integer | the vendor's sequence number of the print within its symbol and day, from 1 |

`CleanTrade` has the same columns; every `CleanTrade` row satisfies every rule above.

## Package conventions

- `stage:rawtrades` — raw trade prints as ingest lands them, one CSV per trading day; lands at data/raw/trades/; pull cap 5000 requests, D4

## Public surface (intent)

- `clean_trades`, realized by clean
""".format(purpose=PURPOSE)

VENDOR_PROBE = """# Source probe — trades — api — 2026-09-21

Purpose: the `data` package's ingest section pulls trade prints from this endpoint.
Samples: trades.sample.json

## Access

- `GET https://api.tapevendor.example/v2/trades?day=<YYYY-MM-DD>&cursor=<c>`; key in env `TRADES_API_KEY`.

## Observed schema

| field | type | observed | notes |
|---|---|---|---|
| trade_id | integer | 6 digits, rising through the day | unique per print |
| symbol | string | `ACME`, `BOLT`, `CRUX` on the probed day | upper case |
| ts | string | `2026-09-11T13:30:02Z` | UTC, second resolution |
| price | string | `12.41` | decimal, 2 places |
| size | integer | 25 to 500 | shares |
| venue | string | `N`, `Q`, `A` | the three venues the feed carries; no other code was observed or is documented |
| seq | integer | 1 upward | per symbol and day |

## Duplicates and keys

- `trade_id` is unique within a day in every probed response.

## Pagination

- Cursor pages of 100 rows; one request per page.

## Rate limits and quotas

- 10 requests a second; 20000 requests a month on the project's plan.

## Quirks

- `ts` has second resolution, so two prints of one symbol can carry the same `ts`.

## Cost and time of a full pull

- One trading day is about 300 rows, 3 to 4 requests, under 2 s.

## Sections served

## data/ingest

- every field above, landed unchanged
"""

DECISIONS_HEAD = """# Decisions

## D4 — Pull cap for `stage:rawtrades`: 5000 requests?

Scope: data
Raised by: docs/packages/data/contract.md, Package conventions
Recommendation: 5000 requests, a quarter of the monthly quota
Assumption if unanswered: 5000 requests
Status: decided
Decision: 5000 requests
"""

DECISIONS_KINDS = """
## D5 — exact duplicate rows: drop 6 rows?

Scope: data/clean
Raised by: K1 of docs/sources/rawtrades.md
Recommendation: drop
Assumption if unanswered:
Status: decided
Decision: drop

## D6 — negative price: repair 4 rows?

Scope: data/clean
Raised by: K2 of docs/sources/rawtrades.md
Recommendation: repair
Assumption if unanswered:
Status: decided
Decision: repair — take the absolute value
"""

INGEST_README = """# ingest

Pulls one trading day of trade prints from the vendor and lands it unchanged.

## Entry points and interfaces

- `PYTHONPATH=packages/data/src python3 -m data.ingest --day <YYYY-MM-DD>` — pulls the day and
  writes `<DATA_RAW_DIR>/<day>.csv`, columns as the contract's `RawTrade`. One request per 100
  rows. Needs `TRADES_API_KEY`.
- Reading what is landed: every `*.csv` under `DATA_RAW_DIR`, a header row, then one row per
  print in the order the vendor returned them.

## Configuration

| setting | environment variable | default |
|---|---|---|
| where a day lands | `DATA_RAW_DIR` | `data/raw/trades` |
| the vendor key | `TRADES_API_KEY` | none |
"""

INGEST_MAIN = '''"""Pull one trading day of trade prints from the vendor and land it unchanged."""
import os
import sys


def main() -> int:
    if not os.environ.get("TRADES_API_KEY"):
        print("data.ingest: TRADES_API_KEY is not set", file=sys.stderr)
        return 2
    raise NotImplementedError("the vendor client is not part of this fixture")


if __name__ == "__main__":
    sys.exit(main())
'''

DESIGN = """# data/clean — design
Mode: new

## 4. Behavior

Every raw row ends in exactly one place: accepted, or the reject record with a reason. The
kinds table, from `docs/sources/rawtrades.md` **Quirks**:

| kind | rule | handler | treatment | decided by |
|---|---|---|---|---|
| K1 | a row equal in every column to an earlier row | `rules.clean`, the `seen` test | drop | D5 |
| K2 | a price below zero | `rules.clean`, the sign test | repair: the absolute value | D6 |
| K3 | a `ts` earlier than the last accepted row of its symbol | `rules.clean`, the order test | quarantine | no decision needed |
{extra}
A row that cannot be parsed is quarantined as `unclassified`.

## 5. Interfaces

- `python3 -m data.clean` reads every file under `DATA_RAW_DIR` and writes `accepted.csv` and
  `rejects.csv` under `DATA_CLEAN_STORE`.

## Tests

- one case per kind on its rows in `rawtrades.sample.json`; one case that the `accepted` rows stay accepted.

## Skills used

- dev-team:data-quality
"""
DESIGN_K4 = "| K4 | after the sign test, a price outside half to double its symbol's median | `rules.clean`, the band test | quarantine | no decision needed |\n"

CLEAN_README = """# clean

Validates and reconciles the raw trade prints `data/ingest` lands: every row is accepted, or
kept in the reject record with the kind that set it aside.

## Entry points and interfaces

- `PYTHONPATH=packages/data/src python3 -m data.clean` — reads every `*.csv` under
  `DATA_RAW_DIR`, in file-name order, and writes two files under `DATA_CLEAN_STORE`, replacing
  what is there:
  - `accepted.csv` — the `CleanTrade` rows, columns as the contract gives them.
  - `rejects.csv` — every row dropped, quarantined or altered, as it was read, plus `reason`
    (the kind id, or `unclassified`) and `action` (`dropped`, `quarantined`, `repaired`). A
    repaired row is in both files: as read here, as repaired in `accepted.csv`.
- `data.clean.rules.clean(rows)` — the same, on rows in memory; returns `(accepted, rejects)`.

## Configuration

| setting | environment variable | default |
|---|---|---|
| where the raw files are read from | `DATA_RAW_DIR` | `data/raw/trades` |
| the store the two files are written to | `DATA_CLEAN_STORE` | `data/clean` |

Both are read from the environment at each run; no file under the package holds a path.
"""

CLEAN_MAIN = '''"""`python3 -m data.clean`: clean every landed file into the store."""
import sys

from data.clean.rules import run

if __name__ == "__main__":
    accepted, rejects = run()
    print(f"data.clean: accepted {accepted}, rejects {rejects}")
    sys.exit(0)
'''

CLEAN_RULES = '''"""Clean raw trade prints: one handler per kind of docs/sources/rawtrades.md."""
import csv
import os
import pathlib
import statistics

COLUMNS = ["trade_id", "symbol", "ts", "price", "size", "venue", "seq"]


def raw_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("DATA_RAW_DIR", "data/raw/trades"))


def store_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("DATA_CLEAN_STORE", "data/clean"))


def read_raw() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(raw_dir().glob("*.csv")):
        with path.open(newline="") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def _reject(row: dict[str, str], reason: str, action: str) -> dict[str, str]:
    return {**row, "reason": reason, "action": action}


def clean(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    accepted: list[dict[str, str]] = []
    rejects: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    last_ts: dict[str, str] = {}
__MEDIAN__    for row in rows:
        try:
            price = float(row["price"])
            int(row["size"]), int(row["seq"]), int(row["trade_id"])
        except (KeyError, ValueError):
            rejects.append(_reject(row, "unclassified", "quarantined"))
            continue
        key = tuple(row[column] for column in COLUMNS)
        if key in seen:  # K1, D5: drop
            rejects.append(_reject(row, "K1", "dropped"))
            continue
        seen.add(key)
        if row["ts"] < last_ts.get(row["symbol"], ""):  # K3: quarantine
            rejects.append(_reject(row, "K3", "quarantined"))
            continue
__BAND__        if price < 0:  # K2, D6: repair, the absolute value
            rejects.append(_reject(row, "K2", "repaired"))
            row = {**row, "price": row["price"].lstrip("-")}
        last_ts[row["symbol"]] = row["ts"]
        accepted.append(row)
    return accepted, rejects


def _write(path: pathlib.Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\\n")
        writer.writeheader()
        writer.writerows(rows)


def run() -> tuple[int, int]:
    accepted, rejects = clean(read_raw())
    store = store_dir()
    store.mkdir(parents=True, exist_ok=True)
    _write(store / "accepted.csv", COLUMNS, accepted)
    _write(store / "rejects.csv", [*COLUMNS, "reason", "action"], rejects)
    return len(accepted), len(rejects)
'''
RULES_MEDIAN = '''    by_symbol: dict[str, list[float]] = {}
    for row in rows:
        try:
            by_symbol.setdefault(row["symbol"], []).append(abs(float(row["price"])))
        except (KeyError, ValueError):
            pass
    median = {symbol: statistics.median(prices) for symbol, prices in by_symbol.items()}
'''
RULES_BAND = '''        if not 0.5 * median[row["symbol"]] <= abs(price) <= 2 * median[row["symbol"]]:  # K4: quarantine
            rejects.append(_reject(row, "K4", "quarantined"))
            continue
'''

FOLLOWUPS = """# Follow-ups

- data/ingest — the vendor's monthly quota is not checked before a pull — deferred at review round 2 (docs/packages/data/reviews/ingest/2026-09-24-r2-a.md)
"""

# ------------------------------------------------------------------------ the profile program

PROGRAM = r'''"""Profile program — stage `rawtrades`. Re-runnable; every check is one query predicate.

    uv run --with duckdb python docs/sources/rawtrades.profile.py             round 0: the raw stage
    uv run --with duckdb python docs/sources/rawtrades.profile.py --round 1   a built section's output

Round 0 reads data/raw/trades/*.csv. Round n >= 1 reads accepted.csv and rejects.csv under
.dev-team/data/rawtrades/work/, where the section was pointed. Either way it prints, per check,
the rows failing and the denominator, beside the previous round's counts; it writes only the
failing rows, each tagged with the ids of the checks it fails, to
.dev-team/data/rawtrades/rounds/<n>/failing.parquet, and the counts to counts.json beside it.
Run from the repo root.
"""
import argparse
import json
import pathlib

import duckdb

STORE = pathlib.Path(".dev-team/data/rawtrades")
RAW = "data/raw/trades/*.csv"
TYPES = ("{'trade_id': 'BIGINT', 'symbol': 'VARCHAR', 'ts': 'VARCHAR', 'price': 'DOUBLE', "
         "'size': 'BIGINT', 'venue': 'VARCHAR', 'seq': 'BIGINT'}")
ROW = "trade_id, symbol, ts, price, size, venue, seq"

# id: (rule, judged against, predicate that is true for a failing row)
CHECKS = {
__CHECKS__}


def load(con, name, path, side, ordinal):
    con.execute(
        f"create table {name} as select *, '{side}' as side, {ordinal} as ordinal, "
        f"row_number() over () as rowno from read_csv('{path}', header = true, types = {TYPES})")


def judged(con, name, source):
    """`source` with what the checks compare a row against: an earlier copy of itself, the
    previous row of its symbol, its symbol's median price in the raw stage."""
    con.execute(f"""
        create view {name} as
        select s.*,
               row_number() over (partition by {ROW} order by ordinal, rowno) as copy_n,
               lag(ts) over (partition by symbol order by seq, ordinal, rowno) as prev_ts,
               (select median(price) from stage r where r.symbol = s.symbol and r.price > 0) as med_price
        from {source} s""")


def failing(con, view, side):
    tags = ", ".join(f"case when {pred} then '{cid}' end" for cid, (_, _, pred) in CHECKS.items())
    any_ = " or ".join(f"coalesce({pred}, false)" for _, _, pred in CHECKS.values())
    return (f"select * exclude (copy_n, prev_ts, med_price, ordinal), "
            f"list_filter([{tags}], x -> x is not null) as checks "
            f"from {view} where side = '{side}' and ({any_})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, default=0)
    n = parser.parse_args().round
    con = duckdb.connect()
    load(con, "stage", RAW, "stage", 0)
    if n == 0:
        judged(con, "j_stage", "stage")
        sides = {"stage": "j_stage"}
    else:
        work = STORE / "work"
        load(con, "accepted", work / "accepted.csv", "accepted", 0)
        load(con, "rejected", work / "rejects.csv", "rejected", 1)
        # A rejected row is judged with the accepted rows around it: a dropped copy is a copy
        # of an accepted row, a quarantined row is out of order among the accepted ones.
        con.execute("create view both_sides as select * from accepted union all by name select * from rejected")
        judged(con, "j_accepted", "accepted")
        judged(con, "j_rejected", "both_sides")
        sides = {"accepted": "j_accepted", "rejected": "j_rejected"}
    con.execute("create table failing as " + " union all by name ".join(failing(con, v, s) for s, v in sides.items()))
    rows = {s: con.execute(f"select count(*) from {v} where side = '{s}'").fetchone()[0] for s, v in sides.items()}
    counts = {cid: {s: con.execute("select count(*) from failing where side = ? and list_contains(checks, ?)",
                                   [s, cid]).fetchone()[0] for s in sides} for cid in CHECKS}
    failed = {s: con.execute("select count(*) from failing where side = ?", [s]).fetchone()[0] for s in sides}
    out = STORE / "rounds" / str(n)
    out.mkdir(parents=True, exist_ok=True)
    con.execute(f"copy failing to '{out / 'failing.parquet'}' (format parquet)")
    result = {"round": n, "rows": rows, "failing_rows": failed,
              "passing_rows": {s: rows[s] - failed[s] for s in sides}, "checks": counts}
    if n > 0:
        result["rejected_by_reason"] = dict(con.execute(
            "select reason, count(*) from rejected group by reason order by reason").fetchall())
    (out / "counts.json").write_text(json.dumps(result, indent=2) + "\n")

    before = STORE / "rounds" / str(n - 1) / "counts.json"
    previous = json.loads(before.read_text())["checks"] if n > 0 and before.exists() else {}
    print(f"round {n} — " + ", ".join(f"{s} {rows[s]} rows, {failed[s]} failing" for s in sides))
    print("check | " + " | ".join(f"{s} failing" for s in sides) + " | of | previous round")
    for cid in CHECKS:
        prev = "/".join(f"{v} {s}" for s, v in previous.get(cid, {}).items()) or "—"
        print(f"{cid} | " + " | ".join(str(counts[cid][s]) for s in sides) + " | "
              + "/".join(str(rows[s]) for s in sides) + f" | {prev}")
    if n > 0:
        print("rejected by reason: " + ", ".join(f"{k} {v}" for k, v in result["rejected_by_reason"].items()))


if __name__ == "__main__":
    main()
'''

# id -> (rule, judged against, predicate, the same rule in Python is in `failures`)
CHECK_ROWS = {
    "C1": ("no row repeats an earlier row in every column",
           "docs/sources/trades.md, Duplicates and keys: `trade_id` is unique", "copy_n > 1"),
    "C2": ("price is above zero", "docs/packages/data/contract.md, Shapes: RawTrade.price", "price <= 0"),
    "C3": ("ts never goes back as seq rises within a symbol",
           "docs/packages/data/contract.md, Shapes: RawTrade.ts; compared with the previous row of the same symbol",
           "ts < prev_ts"),
    "C4": ("venue is one of N, Q, A", "docs/sources/trades.md, Observed schema: venue", "venue not in ('N', 'Q', 'A')"),
    "C5": ("price is within half to double the symbol's median price",
           "comparison: the other rows of the same symbol in the stage",
           "not (price between 0.5 * med_price and 2 * med_price)"),
    "C6": ("symbol is one of the day's tickers", "docs/sources/trades.md, Observed schema: symbol",
           "symbol not in ('ACME', 'BOLT', 'CRUX')"),
    "C7": ("size is above zero", "docs/packages/data/contract.md, Shapes: RawTrade.size", "size <= 0"),
}
C3_BROAD = ("ts moves forward as seq rises within a symbol", CHECK_ROWS["C3"][1], "ts <= prev_ts")


def program(checks: dict[str, tuple[str, str, str]]) -> str:
    lines = "".join(f'    "{cid}": ("{rule}",\n           "{against}",\n           "{pred}"),\n'
                    for cid, (rule, against, pred) in checks.items())
    return PROGRAM.replace("__CHECKS__", lines)


# ------------------------------------------------------------------- the same rules, in Python

def read_rows(variant: str) -> list[dict[str, str]]:
    with (HERE / "seed" / "trades.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row.update(VARIANTS[variant].get(row["trade_id"], {}))
    return rows


def to_csv(rows: list[dict[str, str]], columns: list[str] = COLUMNS) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def failures(rows: list[dict[str, str]], checks: dict, stage: list[dict[str, str]]) -> list[set[str]]:
    """Per row, the ids of the checks it fails — the program's predicates, row for row."""
    median = {}
    for symbol in {r["symbol"] for r in stage}:
        prices = [float(r["price"]) for r in stage if r["symbol"] == symbol and float(r["price"]) > 0]
        median[symbol] = statistics.median(prices) if prices else None
    failed: list[set[str]] = [set() for _ in rows]
    seen: set[tuple[str, ...]] = set()
    for i, row in enumerate(rows):
        key = tuple(row[c] for c in COLUMNS)
        if key in seen:
            failed[i].add("C1")
        seen.add(key)
        price, med = float(row["price"]), median.get(row["symbol"])
        if price <= 0:
            failed[i].add("C2")
        if row["venue"] not in ("N", "Q", "A"):
            failed[i].add("C4")
        if med is not None and not 0.5 * med <= price <= 2 * med:
            failed[i].add("C5")
        if row["symbol"] not in ("ACME", "BOLT", "CRUX"):
            failed[i].add("C6")
        if int(row["size"]) <= 0:
            failed[i].add("C7")
    broad = checks["C3"][2] == "ts <= prev_ts"
    order = sorted(range(len(rows)), key=lambda i: (rows[i]["symbol"], int(rows[i]["seq"]), i))
    for a, b in zip(order, order[1:]):
        if rows[a]["symbol"] == rows[b]["symbol"]:
            if rows[b]["ts"] < rows[a]["ts"] or (broad and rows[b]["ts"] == rows[a]["ts"]):
                failed[b].add("C3")
    return [f & set(checks) for f in failed]


def section_clean(rows: list[dict[str, str]], band: bool):
    """What the seeded `data.clean` does (v1, or v2 with the K4 band test)."""
    median = {s: statistics.median([abs(float(r["price"])) for r in rows if r["symbol"] == s])
              for s in {r["symbol"] for r in rows}}
    accepted, rejects, seen, last = [], [], set(), {}
    for row in rows:
        key = tuple(row[c] for c in COLUMNS)
        if key in seen:
            rejects.append({**row, "reason": "K1"})
            continue
        seen.add(key)
        if row["ts"] < last.get(row["symbol"], ""):
            rejects.append({**row, "reason": "K3"})
            continue
        price = float(row["price"])
        if band and not 0.5 * median[row["symbol"]] <= abs(price) <= 2 * median[row["symbol"]]:
            rejects.append({**row, "reason": "K4"})
            continue
        if price < 0:
            rejects.append({**row, "reason": "K2"})
            row = {**row, "price": row["price"].lstrip("-")}
        last[row["symbol"]] = row["ts"]
        accepted.append(row)
    return accepted, rejects


def round_counts(stage: list[dict[str, str]], checks: dict, band: bool) -> tuple[dict[str, tuple[int, int]], int, int]:
    """Per check, (accepted failing, rejected failing) as the program's round n >= 1 counts them."""
    accepted, rejects = section_clean(stage, band)
    acc = failures(accepted, checks, stage)
    both = failures(accepted + rejects, checks, stage)[len(accepted):]
    return ({c: (sum(c in f for f in acc), sum(c in f for f in both)) for c in checks}, len(accepted), len(rejects))


# ------------------------------------------------------------------------------- the profile

def schema_table(rows: list[dict[str, str]]) -> str:
    def span(column: str, cast) -> str:
        values = [cast(r[column]) for r in rows]
        return f"{min(values)} to {max(values)}"

    def top(column: str) -> str:
        counts: dict[str, int] = {}
        for r in rows:
            counts[r[column]] = counts.get(r[column], 0) + 1
        return ", ".join(f"`{k}` {v}" for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    spec = [("trade_id", "BIGINT", "integer", span("trade_id", int), "the vendor's print id"),
            ("symbol", "VARCHAR", "text", top("symbol"), ""),
            ("ts", "VARCHAR", "text", span("ts", str), "UTC, second resolution"),
            ("price", "DOUBLE", "decimal, 2 places", span("price", float), ""),
            ("size", "BIGINT", "integer", span("size", int), "shares"),
            ("venue", "VARCHAR", "text", top("venue"), ""),
            ("seq", "BIGINT", "integer", span("seq", int), "per symbol and day")]
    lines = ["| column | dtype as loaded | declared dtype | null % | distinct | range or top-k | notes |",
             "|---|---|---|---|---|---|---|"]
    for column, loaded, declared, rng, notes in spec:
        lines.append(f"| {column} | {loaded} | {declared} | 0.0 | {len({r[column] for r in rows})} | {rng} | {notes} |")
    return "\n".join(lines)


def build_profile(variant: str, *, broad: bool, verified: bool, root_sha: str) -> tuple[str, str, str, dict]:
    """The round-0 profile, its program and its example rows, computed from the data.

    Returns (profile text, program text, sample json, facts) — `facts` holds the counts the
    later-round blocks are written from.
    """
    rows = read_rows(variant)
    checks = {c: CHECK_ROWS[c] for c in ("C1", "C2", "C3", "C4", "C5")}
    if broad:
        checks["C3"] = C3_BROAD
    failed = failures(rows, checks, rows)
    n = len(rows)
    count = {c: sum(c in f for f in failed) for c in checks}
    total_failing = sum(bool(f) for f in failed)
    groups = {"K1": {"C1"}, "K2": {"C2", "C5"}, "K3": {"C3"}, "K4": {"C4"}}
    members = {k: [r for r, f in zip(rows, failed) if f & g] for k, g in groups.items()}
    if not members["K4"]:
        del members["K4"]
    state = "verified" if verified else "unverified"
    d1, d2 = ("D5", "D6") if verified else ("D?", "D?")
    k3_what = ("`ts` is not after the `ts` of the row before it in `seq`" if broad else
               "`ts` is one hour behind the rows on either side of it in `seq`")
    quirks = [
        f"- K1 exact duplicate rows — checks C1; {len(members['K1'])} of {n}; a row repeated in every column directly after its original; proposed: drop; {d1}; {state}",
        f"- K2 negative price — checks C2, C5; {len(members['K2'])} of {n}; the price carries a minus sign and its absolute value sits among the neighbouring prices of its symbol; proposed: repair; {d2}; {state}",
        f"- K3 timestamp out of order — checks C3; {len(members['K3'])} of {n}; {k3_what}; proposed: quarantine; no decision needed; {state}",
    ]
    if "K4" in members:
        quirks.append(f"- K4 unknown venue — checks C4; {len(members['K4'])} of {n}; venue `ZZ`, every other column ordinary; proposed: flag; no decision needed; {state}")
    in_kind = sum(bool(f & set().union(*(groups[k] for k in members))) for f in failed)
    check_table = "\n".join(f"| {c} | {rule} | {against} | {count[c]} | {n} |" for c, (rule, against, _) in checks.items())
    round0 = "\n".join(f"| {c} | {count[c]} |" for c in checks)
    size_kb = len(to_csv(rows).encode()) / 1024
    lines_served = ["Round 0 — 2026-09-28 — commit none — pending verify"]
    if verified:
        lines_served.append(f"Round 0 — 2026-09-28 — commit none — kinds: {len(members)} (2 to decide)")
    text = f"""# Source probe — rawtrades — stage — 2026-09-28

Purpose: {PURPOSE}
Profile: rawtrades.profile.py · Examples: rawtrades.sample.json

## Access

Location: data/raw/trades/ — on disk
CSV with a header row, one file per trading day. 1 file, `2026-09-14.csv`, {size_kb:.1f} KB.

## Provenance

- `python3 -m data.ingest --day <YYYY-MM-DD>` (`packages/data/src/data/ingest/README.md`, **Entry points and interfaces**), section `data/ingest` at commit {root_sha}.
- Vendor probe: `docs/sources/trades.md`.

## Shape

{n} rows × 7 columns, one file kind. The whole data was scanned as queries; nothing below is from a sample.

## Observed schema

{schema_table(rows)}

No column looks personal.

## Duplicates and keys

- Exact-duplicate rows: {count['C1']}, each a second copy of one earlier row.
- `trade_id`: not unique, {len({r['trade_id'] for r in rows})} distinct of {n}; unique once the exact duplicates are set aside.
- (`symbol`, `seq`): not unique, for the same rows.

## Checks

| check | rule | judged against | rows failing | of |
|---|---|---|---|---|
{check_table}

## Quirks

{chr(10).join(quirks)}

## Unexplained

{total_failing - in_kind} of {total_failing} failing rows are in no kind.

## Expected and not found

- none: the section's row names no project skill.

## Rounds

### Round 0

| check | rows failing |
|---|---|
{round0}

## Cost and time of a full pass

Under 1 s wall time, about 60 MB peak memory, {n} rows scanned. No pull: the data was on disk.

## Sections served

## data/clean

Purpose: {PURPOSE}

{chr(10).join(lines_served)}
"""
    clean_rows = [r for r, f in zip(rows, failed) if not f]
    sample = {k: v[:5] for k, v in members.items()}
    if broad:  # the first five rows the check flags, in file order
        sample["K3"] = members["K3"][:5]
    sample["accepted"] = clean_rows[10:15]
    facts = {"rows": rows, "checks": checks, "count": count, "n": n}
    return text, program(checks), json.dumps(sample, indent=2) + "\n", facts


def insert_after(text: str, anchor: str, addition: str) -> str:
    """Put `addition` (whole lines) directly after the line `anchor`; no other line changes."""
    assert text.count(anchor + "\n") == 1, anchor
    return text.replace(anchor + "\n", anchor + "\n" + addition, 1)


def insert_before(text: str, anchor: str, addition: str) -> str:
    assert text.count("\n" + anchor + "\n") == 1, anchor
    return text.replace("\n" + anchor + "\n", "\n" + addition + anchor + "\n", 1)


def round_block(n: int, counts: dict[str, tuple[int, int]], previous: dict[str, str]) -> str:
    rows = "\n".join(f"| {c} | {a} | {r} | {previous.get(c, '—')} |" for c, (a, r) in counts.items())
    return f"### Round {n}\n\n| check | accepted | rejected | previous round |\n|---|---|---|---|\n{rows}\n\n"


# ---------------------------------------------------------------------------------- git, build

class Repo:
    def __init__(self, dest: Path):
        self.dest, self.n = dest, 0
        dest.mkdir(parents=True, exist_ok=True)
        if any(dest.iterdir()):
            sys.exit(f"build.py: {dest} is not empty")
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        self.env = {**os.environ, "GIT_AUTHOR_NAME": "seed", "GIT_AUTHOR_EMAIL": "seed@example.invalid",
                    "GIT_COMMITTER_NAME": "seed", "GIT_COMMITTER_EMAIL": "seed@example.invalid",
                    "GIT_AUTHOR_DATE": f"2026-09-28T12:{self.n:02d}:00+0000",
                    "GIT_COMMITTER_DATE": f"2026-09-28T12:{self.n:02d}:00+0000",
                    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
        done = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
                              cwd=self.dest, env=self.env, capture_output=True, text=True)
        if done.returncode:
            sys.exit(f"build.py: git {' '.join(args)}: {done.stderr.strip()}")
        return done.stdout.strip()

    def read(self, rel: str) -> str:
        return (self.dest / rel).read_text()

    def commit(self, files: dict[str, str], message: str) -> str:
        for rel, text in files.items():
            path = self.dest / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.n += 1
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "--short=7", "HEAD")


def rules(band: bool) -> str:
    return CLEAN_RULES.replace("__MEDIAN__", RULES_MEDIAN if band else "").replace("__BAND__", RULES_BAND if band else "")


def ledger_entry(k: int, date: str, said: str, found: str, status: str, resolved: str) -> str:
    return (f"\n## data/clean — {date} — spec-change:design — {k}\n\nClause: design §4 kinds table\n"
            f"Said: {said}\nFound: {found} — docs/sources/rawtrades.md **Quirks**\n"
            f"Why: the built section's output holds rows no kind accounts for\nStatus: {status}\n"
            f"Raised by: profiler — run-package data\nResolved by: {resolved}\n")


def build(case: str, dest: Path) -> None:
    n = int(case.removeprefix("case-"))
    variant = {1: "A", 2: "A", 3: "A", 4: "C", 5: "B", 6: "C", 7: "D"}[n]
    repo = Repo(dest)
    rows = read_rows(variant)
    root = repo.commit({
        ".gitignore": GITIGNORE,
        "docs/architecture.md": ARCHITECTURE,
        "docs/decisions.md": DECISIONS_HEAD,
        "docs/packages/data/contract.md": CONTRACT,
        "docs/sources/trades.md": VENDOR_PROBE,
        "packages/data/src/data/__init__.py": "",
        "packages/data/src/data/ingest/__init__.py": "",
        "packages/data/src/data/ingest/__main__.py": INGEST_MAIN,
        "packages/data/src/data/ingest/README.md": INGEST_README,
        RAW: to_csv(rows),
    }, "data/ingest: build, and one landed day")
    section = None
    if n >= 2:
        text, prog, sample, facts = build_profile(variant, broad=(n == 2), verified=False, root_sha=root)
        repo.commit({"docs/sources/rawtrades.md": text, "docs/sources/rawtrades.profile.py": prog,
                     "docs/sources/rawtrades.sample.json": sample}, "profile rawtrades: round 0")
    if n >= 4:
        text, prog, sample, facts = build_profile(variant, broad=False, verified=True, root_sha=root)
        repo.commit({"docs/sources/rawtrades.md": text, "docs/decisions.md": DECISIONS_HEAD + DECISIONS_KINDS},
                    "profile rawtrades: round 0 verified, D5 and D6 decided")
        repo.commit({"docs/packages/data/design/clean.md": DESIGN.format(extra="")}, "data/clean: design")
        section = repo.commit({
            "packages/data/src/data/clean/__init__.py": "",
            "packages/data/src/data/clean/__main__.py": CLEAN_MAIN,
            "packages/data/src/data/clean/rules.py": rules(band=False),
            "packages/data/src/data/clean/README.md": CLEAN_README,
            "docs/packages/data/reviews/clean/2026-09-30-r1-a.md": "# Review — data/clean — round 1 — conformance\nVerdict: approve\n",
            "docs/packages/data/reviews/clean/2026-09-30-r1-b.md": "# Review — data/clean — round 1 — correctness\nVerdict: approve\n",
        }, "data/clean: build")
    if n >= 6:
        counts, n_acc, n_rej = round_counts(rows, facts["checks"], band=False)
        assert counts["C5"][0] == 1 and sum(a for a, _ in counts.values()) == 1, counts
        prev = {c: str(v) for c, v in facts["count"].items()}
        slip = next(r for r in rows if r["trade_id"] == "500196")
        k4 = (f"- K4 price a hundred times its symbol's level — checks C5; 1 of {n_acc} accepted; a K2 row whose "
              f"repaired price is about 100× the median of its symbol; proposed: quarantine; no decision needed; unverified\n")
        last_kind = next(line for line in reversed(text.splitlines()) if line.startswith("- K3 "))
        text = insert_after(text, last_kind, k4)
        text = insert_before(text, "## Cost and time of a full pass", round_block(1, counts, prev))
        text += f"Round 1 — 2026-10-01 — commit {section} — pending verify\n"
        sample_obj = json.loads(sample)
        sample_obj = {**{k: v for k, v in sample_obj.items() if k != "accepted"}, "K4": [slip], "accepted": sample_obj["accepted"]}
        repo.commit({"docs/sources/rawtrades.md": text, "docs/sources/rawtrades.sample.json": json.dumps(sample_obj, indent=2) + "\n"},
                    "profile rawtrades: round 1")
    if n == 7:
        text = text.replace("no decision needed; unverified\n", "no decision needed; verified\n")
        text += f"Round 1 — 2026-10-01 — commit {section} — new kinds: K4\n"
        ledger = "# Deviations — data/clean\n" + ledger_entry(
            1, "2026-10-01", "K1, K2, K3", f"K4 price a hundred times its symbol's level, 1 of {n_acc} accepted", "open", "—")
        repo.commit({"docs/sources/rawtrades.md": text, "docs/packages/data/deviations/clean.md": ledger},
                    "profile rawtrades: round 1 verified, new kinds K4")
        ledger = ledger.replace("Status: open", "Status: resolved").replace("Resolved by: —", "Resolved by: designer — run-package data")
        repo.commit({"docs/packages/data/design/clean.md": DESIGN.format(extra=DESIGN_K4).replace("Mode: new", "Mode: delta"),
                     "docs/packages/data/deviations/clean.md": ledger}, "data/clean: design, K4")
        section = repo.commit({
            "packages/data/src/data/clean/rules.py": rules(band=True),
            "docs/packages/data/reviews/clean/2026-10-02-r2-a.md": "# Review — data/clean — round 2 — full\nVerdict: approve\n",
        }, "data/clean: fix, K4 band test")
        checks = {**facts["checks"], "C6": CHECK_ROWS["C6"], "C7": CHECK_ROWS["C7"]}
        counts2, n_acc2, n_rej2 = round_counts(rows, checks, band=True)
        assert (counts2["C6"][0], counts2["C7"][0]) == (2, 1), counts2
        assert sum(a for c, (a, _) in counts2.items() if c not in ("C6", "C7")) == 0, counts2
        prev = {c: f"{a} accepted, {r} rejected" for c, (a, r) in counts.items()}
        text = insert_after(text, next(l for l in text.splitlines() if l.startswith("| C5 | ") and "median" in l),
                            "".join(f"| {c} | {CHECK_ROWS[c][0]} | {CHECK_ROWS[c][1]} | {counts2[c][0]} | {n_acc2} accepted (added at round 2) |\n" for c in ("C6", "C7")))
        k56 = (f"- K5 unknown symbol — checks C6; {counts2['C6'][0]} of {n_acc2} accepted; symbol `TEST`, which the vendor probe does not list; proposed: quarantine; no decision needed; unverified\n"
               f"- K6 zero size — checks C7; {counts2['C7'][0]} of {n_acc2} accepted; `size` is 0, every other column ordinary; proposed: quarantine; no decision needed; unverified\n")
        text = insert_after(text, next(l for l in text.splitlines() if l.startswith("- K4 ")), k56)
        text = insert_before(text, "## Cost and time of a full pass", round_block(2, counts2, prev))
        text += f"Round 2 — 2026-10-02 — commit {section} — pending verify\n"
        sample_obj = {**{k: v for k, v in sample_obj.items() if k != "accepted"},
                      "K5": [r for r in rows if r["symbol"] == "TEST"], "K6": [r for r in rows if r["size"] == "0"],
                      "accepted": sample_obj["accepted"]}
        repo.commit({"docs/sources/rawtrades.md": text, "docs/sources/rawtrades.profile.py": program(checks),
                     "docs/sources/rawtrades.sample.json": json.dumps(sample_obj, indent=2) + "\n"}, "profile rawtrades: round 2")
        text = text.replace("no decision needed; unverified\n", "no decision needed; verified\n")
        text += f"Round 2 — 2026-10-02 — commit {section} — new kinds: K5, K6\n"
        ledger += ledger_entry(2, "2026-10-02", "K1, K2, K3, K4",
                               f"K5 unknown symbol, {counts2['C6'][0]} of {n_acc2} accepted; K6 zero size, {counts2['C7'][0]} of {n_acc2} accepted",
                               "open", "—")
        repo.commit({"docs/sources/rawtrades.md": text, "docs/packages/data/deviations/clean.md": ledger,
                     "docs/followups.md": FOLLOWUPS}, "profile rawtrades: round 2 verified, new kinds K5, K6")
    repo.git("tag", "seed")
    print(f"seed: ok — {case} at {dest}, HEAD {repo.git('rev-parse', '--short=7', 'HEAD')}")
    print(f"section commit: {section or 'none'}")
    print(store(n, dest))


def store(n: int, dest: Path) -> str:
    """Build the ignored local folder the case starts with, by running the seeded program."""
    if n in (1, 7):
        return f"store: absent — {STORE}/ does not exist in this copy"
    uv = ["uv", "run", "--no-project", "--with", "duckdb", "python", "docs/sources/rawtrades.profile.py"]
    steps = [[*uv, "--round", "0"]]
    if n == 6:
        steps += [[sys.executable, "-m", "data.clean"], [*uv, "--round", "1"]]
    env = {**os.environ, "PYTHONPATH": "packages/data/src", "DATA_CLEAN_STORE": f"{STORE}/work"}
    for step in steps:
        try:
            done = subprocess.run(step, cwd=dest, env=env, capture_output=True, text=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as error:
            return f"store: not built — `{' '.join(step)}` could not run: {error}"
        if done.returncode:
            return f"store: not built — `{' '.join(step)}` failed: {done.stderr.strip().splitlines()[-1:]}"
    built = sorted(str(p.relative_to(dest)) for p in (dest / STORE).rglob("*") if p.is_file())
    return "store: built — " + ", ".join(built)


# ------------------------------------------------------------------------------------ collect

def collect(dest: Path, outputs: Path) -> None:
    def git(*args: str) -> str:
        done = subprocess.run(["git", *args], cwd=dest, capture_output=True, text=True)
        if done.returncode:
            sys.exit(f"build.py: git {' '.join(args)}: {done.stderr.strip()}")
        return done.stdout

    outputs.mkdir(parents=True, exist_ok=True)
    changed = [line.split("\t") for line in git("diff", "--name-status", "--no-renames", "seed").splitlines()]
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    lines = [f"{status}\t{path}" for status, path in changed] + [f"A\t{path}" for path in untracked]
    (outputs / "changes.txt").write_text(
        "# every path that differs from the seed commit (A added, M modified, D deleted); ignored paths are in store-files.txt\n"
        + ("\n".join(sorted(lines, key=lambda l: l.split("\t")[1])) or "(no path differs)") + "\n")
    (outputs / "changes.diff").write_text(git("diff", "--no-renames", "seed") or "(no tracked file differs)\n")
    (outputs / "commits-after-seed.txt").write_text(git("log", "--oneline", "seed..HEAD") or "(none)\n")
    for path in [p for s, p in changed if s != "D"] + untracked:
        target = outputs / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(dest / path, target)
    local = dest / ".dev-team"
    found = sorted(p for p in local.rglob("*") if p.is_file()) if local.exists() else []
    (outputs / "store-files.txt").write_text(
        "# every file under .dev-team/ (ignored by git), with its size in bytes\n"
        + ("\n".join(f"{p.relative_to(dest)}\t{p.stat().st_size}" for p in found) or "(no file)") + "\n")
    for p in found:
        if p.suffix in (".json", ".csv", ".txt", ".md") and p.stat().st_size <= 200_000:
            target = outputs / p.relative_to(dest)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
    print(f"collect: ok — {len(lines)} changed paths, {len(found)} files under .dev-team/, copied to {outputs}")


def main(argv: list[str]) -> None:
    if len(argv) == 3 and argv[0] == "collect":
        collect(Path(argv[1]).resolve(), Path(argv[2]).resolve())
    elif len(argv) == 2 and argv[0] in {f"case-{i}" for i in range(1, 8)}:
        build(argv[0], Path(argv[1]).resolve())
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
