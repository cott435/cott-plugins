#!/usr/bin/env python3
"""Check that the `clean` a run of run-package eval 19 built honours the decided treatments.

    python3 check_treatments.py <copy> [--out FILE]

`<copy>` is the run's repository, as the agents left it. The report goes to stdout and, with
`--out`, to FILE; the last line is `exit: <n>` — 0 every check passed, 1 a check failed, 2 the
check could not run. Nothing in `<copy>` is written: part A sends the rejects file to a
temporary directory, and part B runs the profile program in a temporary clone.

**A — treatments**, two verdicts: `output` (the rows kept) and `reject record` (the rows
removed or altered, each recorded with its kind id). The built `clean_trades` is run on the stage's whole input — the file the
contract's `stage:rawtrades` line says the data lands at, the export `planted-rows.csv` was
appended to — read by the seeded `data.ingest.reader.read_trades`. What is expected of each row
is the user's answers in the harness, which hold for any row of the kind, planted or not:

- a row equal in all five fields to an earlier row: one copy kept, the repeats removed;
- a symbol that is not upper case: kept with the symbol upper-cased;
- a price of zero or below, or a size of zero or below: not in the output;
- any other row, a timestamp out of order among them: kept, unchanged.

So the output must be exactly that multiset of rows. Every row removed or altered must be in
the rejects file with its kind id in `reason` (`data-quality`, **The reject record**: "the kind
id as the reason"). The kind id of a group of rows is found without assuming the profile's
numbering or names: it is a kind whose example rows in `docs/sources/rawtrades.sample.json`
include a row of that group, and whose treatment in the design's kinds table
(`| kind | rule | handler | treatment | decided by |`, `data-quality`) is the one the answer
calls for — `drop` for the repeats, `repair` for the case, `drop` or `quarantine` for a price or
size. A reason may carry more than the id (`K2 non-positive price` passes).

Interfaces read, and where each is fixed: `clean_trades(trades, rejects)` and the rejects file's
columns — the five `Trade` fields in order, then `reason` — are the contract's **Section
interfaces** (`clean`); the module that defines `clean_trades` is the section's choice, so it is
found by searching the section's files for `def clean_trades`; `read_trades` is the seeded
`ingest` README's. The output's order (the contract's stable sort by `ts`) and whether a
flagged row is also recorded are reported, not judged.

**B — round 0 reproduced.** A later round may rewrite `rawtrades.profile.py` (round 1 of an
earlier run rewrote 87 lines of it). Its round-0 predicates must still count what round 0
recorded. The newest program is run in a fresh clone of `<copy>` — no `.dev-team/` store, so it
cannot read an earlier round's files — the way `agents/profiler.md` runs it at round 0, with no
argument (`uv run --no-project --with duckdb python docs/sources/rawtrades.profile.py`;
`--no-project` keeps uv off the clone's workspace). Each check's count is taken from the
`rounds/0/counts.json` it writes (the path `profiler.md` fixes; its layout is the program's, so
a check's count is read as the number under a `fail…` key, or the only number under the
check's key) and from its printed `<n> of <m>` (`profiler.md`: it prints, per check, rows
failing and the denominator). The expected count is the one the profile's `### Round 0` block
records (`data-profile.md` item 10), for every check that block lists.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLANTED = HERE / "seed" / "eval-19" / "planted-rows.csv"
TOKEN = "rawtrades"

RUN_CLEAN = r'''
import importlib, json, sys
from pathlib import Path
from data.ingest.reader import read_trades
module = importlib.import_module(sys.argv[1])
trades = read_trades(Path(sys.argv[2]))
kept = module.clean_trades(trades, Path(sys.argv[3]))
row = lambda t: [t.ts.isoformat(), t.symbol, t.price, t.size, t.side]
print(json.dumps({"input": [row(t) for t in trades], "output": [row(t) for t in kept]}))
'''


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failures: Counter = Counter()

    def say(self, line: str) -> None:
        self.lines.append(line)

    def check(self, part: str, ok: bool, line: str) -> None:
        self.lines.append(("ok   " if ok else "FAIL ") + line)
        self.failures[part] += 0 if ok else 1

    def verdict(self, part: str) -> None:
        self.lines.append(f"{part}: " + ("FAIL" if self.failures[part] else "PASS"))


# ------------------------------------------------------------------------------- row keys

def ts_key(value: str) -> str:
    """A timestamp as `YYYY-MM-DDTHH:MM:SSZ` when it parses with a zone, else as given."""
    value = value.strip()
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    if moment.tzinfo is None:
        return moment.isoformat()
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def key(ts: str, symbol: str, price, size, side: str) -> tuple:
    try:
        price = round(float(price), 6)
    except (TypeError, ValueError):
        pass
    try:
        size = int(float(size))
    except (TypeError, ValueError):
        pass
    return (ts_key(str(ts)), str(symbol).strip(), price, size, str(side).strip())


def folded(k: tuple) -> tuple:
    """The key with the symbol upper-cased: a repaired row and its original match."""
    return (k[0], k[1].upper(), *k[2:])


def show(k: tuple) -> str:
    return " ".join(str(x) for x in k)


# ------------------------------------------------------------------------------- part A

def stage_input(copy: Path) -> Path:
    path = copy / "docs/packages/data/contract.md"
    contract = path.read_text() if path.exists() else ""
    m = re.search(rf"`stage:{TOKEN}`[^\n]*?lands at ([^\s;,]+)", contract)
    return copy / (m.group(1).rstrip(".") if m else "data/trades.csv")


def clean_module(copy: Path) -> str | None:
    root = copy / "packages/data/src"
    found = sorted(p for p in (root / "data/clean").rglob("*.py") if re.search(r"^def clean_trades\(", p.read_text(), re.M))
    if not found:
        return None
    rel = found[0].relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def python_for(copy: Path) -> str:
    venv = copy / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def kinds_table(copy: Path) -> dict[str, str]:
    """Kind id -> treatment, from the design's kinds table."""
    design = copy / "docs/packages/data/design/clean.md"
    if not design.exists():
        return {}
    out: dict[str, str] = {}
    in_table = False
    for line in design.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if cells and [c.lower() for c in cells[:5]] == ["kind", "rule", "handler", "treatment", "decided by"]:
            in_table = True
            continue
        if in_table and not cells:
            in_table = False
        if in_table and len(cells) >= 4:
            kid = re.search(r"\bK\d+\b", cells[0])
            treat = re.search(r"\b(repair|drop|quarantine|flag)\b", cells[3].lower())
            if kid and treat:
                out[kid.group(0)] = treat.group(1)
    return out


def sample_kinds(copy: Path) -> dict[str, list[tuple]]:
    """Kind id -> the keys of its example rows in rawtrades.sample.json."""
    path = copy / f"docs/sources/{TOKEN}.sample.json"
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    out: dict[str, list[tuple]] = {}
    for kid, rows in data.items():
        if not re.fullmatch(r"K\d+", kid) or not isinstance(rows, list):
            continue
        keys = []
        for r in rows:
            if isinstance(r, dict) and all(f in r for f in ("ts", "symbol", "price", "size", "side")):
                keys.append(key(r["ts"], r["symbol"], r["price"], r["size"], r["side"]))
        out[kid] = keys
    return out


def part_a(copy: Path, rep: Report) -> None:
    rep.say("## A — treatments: the built clean on the stage's input")
    src = stage_input(copy)
    module = clean_module(copy)
    if module is None:
        rep.check("output", False, "no `def clean_trades` under packages/data/src/data/clean/")
        rep.check("reject record", False, "nothing to run")
        rep.verdict("output")
        rep.verdict("reject record")
        return
    rep.say(f"input: {src.relative_to(copy)} · clean_trades from `{module}` · python {python_for(copy)}")
    with tempfile.TemporaryDirectory() as tmp:
        rejects = Path(tmp) / "rejects.csv"
        env = {**os.environ, "PYTHONPATH": str(copy / "packages/data/src"), "DATA_REJECTS": str(rejects)}
        done = subprocess.run([python_for(copy), "-c", RUN_CLEAN, module, str(src), str(rejects)],
                              cwd=copy, env=env, capture_output=True, text=True, timeout=600)
        if done.returncode:
            rep.check("output", False, "the built clean_trades did not run: " + (done.stderr.strip().splitlines() or ["?"])[-1])
            rep.check("reject record", False, "nothing ran")
            rep.verdict("output")
            rep.verdict("reject record")
            return
        result = json.loads(done.stdout.strip().splitlines()[-1])
        recorded = []
        if rejects.exists():
            with rejects.open(newline="") as fh:
                rows = list(csv.reader(fh))
            for r in rows[1:]:
                if len(r) >= 6:
                    recorded.append((key(*r[:5]), ",".join(r[5:])))
    inputs = [key(*r) for r in result["input"]]
    output = Counter(key(*r) for r in result["output"])
    rep.say(f"rows: {len(inputs)} in, {sum(output.values())} out, {len(recorded)} in the rejects file")

    seen: set[tuple] = set()
    expected: Counter = Counter()
    group: dict[int, str] = {}
    latest = ""
    for i, k in enumerate(inputs):
        ts, symbol, price, size, _ = k
        if k in seen:
            group[i] = "repeat"
        elif (isinstance(price, float) and price <= 0) or (isinstance(size, int) and size <= 0):
            group[i] = "price" if isinstance(price, float) and price <= 0 else "size"
        elif symbol != symbol.upper():
            group[i] = "case"
            expected[(ts, symbol.upper(), *k[2:])] += 1
        else:
            group[i] = "out of order" if ts < latest else "good"
            expected[k] += 1
        seen.add(k)
        latest = max(latest, ts)

    missing, extra = expected - output, output - expected
    rep.check("output", not missing and not extra,
              f"output is exactly the expected rows ({sum(expected.values())}): "
              + ("yes" if not missing and not extra else
                 f"missing {sum(missing.values())} [{'; '.join(show(k) for k in list(missing)[:6])}], "
                 f"extra {sum(extra.values())} [{'; '.join(show(k) for k in list(extra)[:6])}]"))
    order = [key(*r)[0] for r in result["output"]]
    rep.say(f"note: output in `ts` order (the contract's stable sort): {'yes' if order == sorted(order) else 'no'}")

    table, samples = kinds_table(copy), sample_kinds(copy)
    rep.say("design kinds table: " + (", ".join(f"{k} {t}" for k, t in table.items()) or "not found"))
    wanted = {"repeat": {"drop"}, "case": {"repair"}, "price": {"drop", "quarantine"},
              "size": {"drop", "quarantine"}, "out of order": {"flag"}}
    members = {g: [inputs[i] for i, gg in group.items() if gg == g] for g in wanted}
    kind_of: dict[str, set[str]] = {}
    for g, treatments in wanted.items():
        rows_g = {folded(k) for k in members[g]}
        kind_of[g] = {kid for kid, ks in samples.items()
                      if table.get(kid) in treatments and any(folded(k) in rows_g for k in ks)}
        rep.say(f"group {g}: {len(members[g])} rows · kind by example rows and treatment: "
                + (", ".join(sorted(kind_of[g])) or "none"))

    planted = set()
    if PLANTED.exists():
        with PLANTED.open(newline="") as fh:
            planted = {key(*r[:5]) for r in csv.reader(fh) if len(r) >= 5}
    pool = list(recorded)
    for g in ("repeat", "price", "size", "case"):
        if not members[g]:
            continue
        if not kind_of[g]:
            rep.check("reject record", False, f"{g}: no kind in the design's table with treatment {'/'.join(sorted(wanted[g]))} "
                             f"whose example rows hold one of these rows")
        for k in members[g]:
            tag = " (planted)" if k in planted else ""
            same = [p for p in pool if folded(p[0]) == folded(k)]
            hit = next((p for p in same if set(re.findall(r"\bK\d+\b", p[1])) & kind_of[g]), None)
            any_rec = same[0] if same else None
            if hit:
                pool.remove(hit)
            rep.check("reject record", hit is not None,
                      f"{g}{tag} {show(k)}: in the rejects file with its kind id "
                      + (f"(reason `{hit[1]}`)" if hit else
                         f"— recorded with reason `{any_rec[1]}`" if any_rec else "— not recorded"))
    for k in members["out of order"]:
        rec = next((p for p in pool if p[0] == k), None)
        rep.say(f"note: out of order {show(k)}: kept (judged above); recorded: "
                + (f"yes, reason `{rec[1]}`" if rec else "no"))
    if planted:
        found = sum(1 for k in inputs if k in planted)
        rep.check("output", found == len(planted), f"the {len(planted)} planted rows are in the input: {found} found")
    rep.verdict("output")
    rep.verdict("reject record")


# ------------------------------------------------------------------------------- part B

def recorded_round0(copy: Path) -> dict[str, int]:
    path = copy / f"docs/sources/{TOKEN}.md"
    if not path.exists():
        return {}
    text = path.read_text()
    m = re.search(r"^### Round 0\s*$(.*?)(?=^### |^## |\Z)", text, re.M | re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(r"C\d+", cells[0]):
            n = re.match(r"\d+", cells[1])
            if n:
                out[cells[0]] = int(n.group(0))
    return out


def count_in(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        for k, v in value.items():
            if "fail" in str(k).lower() and isinstance(v, int) and not isinstance(v, bool):
                return v
        nested = [v for v in value.values() if isinstance(v, dict)]
        if len(nested) == 1:
            return count_in(nested[0])
        ints = [v for v in value.values() if isinstance(v, int) and not isinstance(v, bool)]
        if len(ints) == 1:
            return ints[0]
    return None


def find_check(data, cid: str):
    if isinstance(data, dict):
        if cid in data:
            return data[cid]
        for v in data.values():
            hit = find_check(v, cid)
            if hit is not None:
                return hit
    elif isinstance(data, list):
        for v in data:
            if isinstance(v, dict) and v.get("id") == cid:
                return v
            hit = find_check(v, cid)
            if hit is not None:
                return hit
    return None


def part_b(copy: Path, rep: Report) -> None:
    rep.say("")
    rep.say("## B — round 0 reproduced: the newest profile program, run as at round 0")
    expected = recorded_round0(copy)
    if not expected:
        rep.check("round 0 reproduced", False, f"docs/sources/{TOKEN}.md has no `### Round 0` table of check counts")
        rep.verdict("round 0 reproduced")
        return
    log = subprocess.run(["git", "log", "--format=%h %s", "--", f"docs/sources/{TOKEN}.profile.py"],
                         cwd=copy, capture_output=True, text=True).stdout.strip().splitlines()
    rep.say(f"program commits, newest first: {' | '.join(log) or 'none'}")
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "clone"
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(copy), str(clone)], check=True)
        done = subprocess.run(["uv", "run", "--no-project", "--with", "duckdb", "python",
                               f"docs/sources/{TOKEN}.profile.py"],
                              cwd=clone, capture_output=True, text=True, timeout=900,
                              env={k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"})
        counts_path = clone / f".dev-team/data/{TOKEN}/rounds/0/counts.json"
        if done.returncode or not counts_path.exists():
            rep.check("round 0 reproduced", False, "the program did not run as at round 0: "
                      + (done.stderr.strip().splitlines() or ["no counts.json written"])[-1])
            rep.verdict("round 0 reproduced")
            return
        counts = json.loads(counts_path.read_text())
        printed: dict[str, int] = {}
        for line in done.stdout.splitlines():
            m = re.search(r"\b(C\d+)\b.*?(\d+)\s+of\s+\d+", line)
            if m and m.group(1) not in printed:
                printed[m.group(1)] = int(m.group(2))
    for cid, want in expected.items():
        from_json = count_in(find_check(counts, cid))
        got = from_json if from_json is not None else printed.get(cid)
        agree = "" if from_json is None or cid not in printed or printed[cid] == from_json else \
            f" (printed {printed[cid]})"
        rep.check("round 0 reproduced", got == want, f"{cid}: round 0 recorded {want}, rerun counts "
                  + (str(got) if got is not None else "nothing readable") + agree)
    rep.verdict("round 0 reproduced")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("copy", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    copy = args.copy.resolve()
    rep = Report()
    rep.say(f"# treatment check — {copy}")
    code = 0
    try:
        part_a(copy, rep)
        part_b(copy, rep)
        code = 1 if sum(rep.failures.values()) else 0
    except Exception as error:  # the check could not run: say so, never pass
        rep.say(f"could not run: {type(error).__name__}: {error}")
        code = 2
    rep.say(f"exit: {code}")
    text = "\n".join(rep.lines) + "\n"
    print(text, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
