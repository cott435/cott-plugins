#!/usr/bin/env python3
"""A review's findings files and its edit list, read and checked without a model.

`revise-plugin` has unit agents write findings under `site/notes/<slug>/findings/` and one
reconcile agent write the edit list `site/notes/<slug>/<slug>-edits.md`. `plan-phases`
assigns every item of that list to exactly one phase in the overview's **Phases** table, and
`run-phase` reads only the items its phase owns. Each of those steps reads this script's
output instead of the whole file, so a 150-item list costs a chat only what it needs.

Shapes, all owned by `templates/review/` in this bundle:

  findings file   `### F-<UNIT>-<nn> <title>` blocks of `- <field>: <value>` lines, under
                  `## Findings`; `## Checked, no finding` present.
  edit list       `### E-<nnn>[a-z] <title>` blocks under `## Edits` (any `###` without an
                  id, such as a group heading, is skipped); a `## Decisions taken` table whose
                  first column is a `D-<nn>` id. A section heading may carry a number prefix
                  (`## 1. Edits`).
  overview        a `## Phases` table with `Phase`, `Items` and `Depends on` columns. Items
                  holds ids and ranges: `E-001, E-004–E-009, E-012a` (`..` works for `–`).
                  Depends on holds phase numbers, `design`, `edits` or `all`.

Commands:

  findings <dir>                 check every findings file in <dir>
  check <edits> [--decided] [--findings DIR]
                                 check the edit list; --decided also requires every
                                 decision an item cites to have a Chosen value; --findings
                                 requires every finding id in DIR to appear in the list
  index <edits>                  one line per item: id, mechanism, decide, depends, files, title
  show <edits> <ID>...           print those items' blocks whole, then the decision rows they cite
  show <edits> --phase N --overview <overview>
                                 the same, for the items the overview gives phase N
  show ... --located [--at REF]  under each item, where every `path:line` its `files:` cites
                                 is in the tree now, with the lines there: the item's numbers
                                 are the reviewed commit's, and `git diff REF` carries each
                                 one across what has changed since. REF is the last commit
                                 the list's opening paragraph names in backticks; with none,
                                 the lines at the item's own numbers. Paths are the plugin's,
                                 so run it from the plugin's directory.
  coverage <edits> <overview>    every item in exactly one phase; no unknown id; an item's
                                 dependencies in its own phase or one its phase depends on

Exit 0 on success; 1 with one line per problem on stdout otherwise; 2 on bad usage.
Standard library only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

FINDING_FIELDS = ("kind", "severity", "files", "mechanism", "claim", "fix", "evals", "proof")
FINDING_KINDS = ("contradiction", "underspecified", "prose-to-script", "script-defect",
                 "missing-check", "duplication", "bloat", "missing-test")
SEVERITIES = ("ERROR", "WARN", "NOTE")
ITEM_FIELDS = ("findings", "files", "mechanism", "edit", "closes", "evals")
OPEN_CHOICES = ("", "open", "decide", "-", "—")

FINDING_HEAD = re.compile(r"^### (F-[A-Z][A-Z0-9-]*-\d+)\b\s*(.*)$")
ITEM_HEAD = re.compile(r"^### (E-\d{3}[a-z]?)\b\s*(.*)$")
ITEM_ID = re.compile(r"E-(\d{3})([a-z]?)")
DECISION_ID = re.compile(r"\bD-\d{2,}\b")
FIELD = re.compile(r"^- ([a-z][a-z ]*?):\s?(.*)$")
SECTION = re.compile(r"^## (?:\d+\.\s*)?(.+?)\s*$")


def sections(text: str) -> dict[str, list[str]]:
    """The `##` sections of a markdown file by name, number prefixes dropped."""
    out: dict[str, list[str]] = {}
    name = None
    for line in text.splitlines():
        m = SECTION.match(line)
        if m and not line.startswith("###"):
            name = m.group(1)
            out[name] = []
        elif name is not None:
            out[name].append(line)
    return out


def blocks(lines: list[str], head: re.Pattern) -> list[dict]:
    """`###` blocks whose heading matches `head`, with their fields and raw lines."""
    out: list[dict] = []
    cur = None
    for i, line in enumerate(lines):
        if line.startswith("### ") or line.startswith("## "):
            m = head.match(line)
            cur = None
            if m:
                cur = {"id": m.group(1), "title": m.group(2).strip(), "fields": {},
                       "raw": [line], "line": i}
                out.append(cur)
            continue
        if cur is None:
            continue
        cur["raw"].append(line)
        f = FIELD.match(line)
        if f:
            cur["fields"][f.group(1).strip()] = f.group(2).strip()
            cur["last"] = f.group(1).strip()
        elif line.startswith("  ") and cur.get("last"):
            key = cur["last"]
            cur["fields"][key] = (cur["fields"][key] + " " + line.strip()).strip()
    for b in out:
        while b["raw"] and not b["raw"][-1].strip():
            b["raw"].pop()
    return out


def table(lines: list[str]) -> list[dict[str, str]]:
    """The first markdown table in `lines`, as dicts keyed by header cell."""
    rows = [l for l in lines if l.strip().startswith("|")]
    if len(rows) < 2:
        return []
    cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
    head = cells(rows[0])
    return [dict(zip(head, cells(r))) for r in rows[2:]]


# --- findings ----------------------------------------------------------------------------

def cmd_findings(args) -> int:
    d = Path(args.dir)
    files = sorted(p for p in d.glob("*.md") if not p.name[0].isdigit())
    if not files:
        print(f"{d}: no findings files")
        return 1
    problems, seen = [], {}
    for p in files:
        secs = sections(p.read_text())
        mine = []
        if "Findings" not in secs:
            problems.append(f"{p.name}: no '## Findings' section")
        if "Checked, no finding" not in secs:
            problems.append(f"{p.name}: no '## Checked, no finding' section")
        for b in blocks(secs.get("Findings", []), FINDING_HEAD):
            mine.append(b)
            where = f"{p.name}:{b['id']}"
            if b["id"] in seen:
                problems.append(f"{where}: id also in {seen[b['id']]}")
            seen[b["id"]] = p.name
            for key in FINDING_FIELDS:
                if not b["fields"].get(key):
                    problems.append(f"{where}: no '{key}'")
            kind = b["fields"].get("kind", "")
            if kind and kind not in FINDING_KINDS:
                problems.append(f"{where}: kind '{kind}' is not one of {', '.join(FINDING_KINDS)}")
            sev = b["fields"].get("severity", "")
            if sev and sev not in SEVERITIES:
                problems.append(f"{where}: severity '{sev}' is not one of {', '.join(SEVERITIES)}")
        counts: dict[str, int] = {}
        for b in mine:
            k = b["fields"].get("kind", "?")
            counts[k] = counts.get(k, 0) + 1
        summary = ", ".join(f"{k} {n}" for k, n in sorted(counts.items())) or "none"
        print(f"{p.name}: {len(mine)} findings ({summary})")
    for line in problems:
        print(f"FAIL {line}")
    return 1 if problems else 0


# --- the edit list -----------------------------------------------------------------------

def load_edits(path: str):
    secs = sections(Path(path).read_text())
    items = blocks(secs.get("Edits", []), ITEM_HEAD)
    decisions = {}
    for row in table(secs.get("Decisions taken", [])):
        first = next(iter(row.values()), "")
        m = DECISION_ID.search(first)
        if m:
            decisions[m.group(0)] = row
    return secs, items, decisions


def ids_in(text: str) -> list[str]:
    return [m.group(0) for m in ITEM_ID.finditer(text)]


def chosen(row: dict[str, str]) -> str:
    return row.get("Chosen", "").strip()


def cmd_check(args) -> int:
    secs, items, decisions = load_edits(args.edits)
    problems = []
    for name in ("Edits", "Decisions taken", "Build order"):
        if name not in secs:
            problems.append(f"no '## {name}' section")
    known, dup = set(), set()
    for it in items:
        (dup if it["id"] in known else known).add(it["id"])
    problems += [f"{i}: id used twice" for i in sorted(dup)]
    graph = {}
    for it in items:
        f = it["fields"]
        for key in ITEM_FIELDS:
            if not f.get(key):
                problems.append(f"{it['id']}: no '{key}'")
        deps = ids_in(f.get("depends", ""))
        graph[it["id"]] = deps
        for d in deps:
            if d not in known:
                problems.append(f"{it['id']}: depends on {d}, which is not an item")
            if d == it["id"]:
                problems.append(f"{it['id']}: depends on itself")
        for d in DECISION_ID.findall(f.get("decide", "")):
            if d not in decisions:
                problems.append(f"{it['id']}: decide {d}, which has no row in Decisions taken")
            elif args.decided and chosen(decisions[d]).lower() in OPEN_CHOICES:
                problems.append(f"{it['id']}: decide {d} has no Chosen value yet")
        if "DECIDE" in f.get("edit", "") and not DECISION_ID.search(f.get("decide", "")):
            problems.append(f"{it['id']}: edit says DECIDE but no 'decide: D-nn' field")
    problems += cycles(graph)
    if args.findings:
        text = Path(args.edits).read_text()
        for p in sorted(Path(args.findings).glob("*.md")):
            if p.name[0].isdigit():
                continue
            for b in blocks(sections(p.read_text()).get("Findings", []), FINDING_HEAD):
                if not re.search(rf"{re.escape(b['id'])}\b", text):
                    problems.append(f"{b['id']} ({p.name}): cited by no item, conflict or non-goal")
    for line in problems:
        print(f"FAIL {line}")
    if not problems:
        open_d = [d for d, r in decisions.items() if chosen(r).lower() in OPEN_CHOICES]
        print(f"ok: {len(items)} items, {len(decisions)} decisions"
              + (f" ({len(open_d)} open: {', '.join(open_d)})" if open_d else ""))
    return 1 if problems else 0


def cycles(graph: dict[str, list[str]]) -> list[str]:
    state, out = {}, []

    def visit(n, path):
        state[n] = 1
        for d in graph.get(n, []):
            if state.get(d) == 1:
                out.append("dependency cycle: " + " → ".join(path[path.index(d):] + [d]))
            elif d in graph and not state.get(d):
                visit(d, path + [d])
        state[n] = 2

    for n in graph:
        if not state.get(n):
            visit(n, [n])
    return out


def paths_of(files: str) -> str:
    seen = []
    for part in files.split(","):
        p = part.strip().split(":")[0].strip("` ")
        if p and p not in seen:
            seen.append(p)
    return ", ".join(seen)


def cmd_index(args) -> int:
    _, items, decisions = load_edits(args.edits)
    for it in items:
        f = it["fields"]
        dec = " ".join(
            f"{d}={chosen(decisions[d]) or 'open'}" if d in decisions else f"{d}=?"
            for d in DECISION_ID.findall(f.get("decide", ""))
        )
        deps = ",".join(ids_in(f.get("depends", ""))) or "-"
        print(f"{it['id']}\t{f.get('mechanism', '?')}\t{dec or '-'}\tdeps:{deps}\t"
              f"{paths_of(f.get('files', ''))}\t{it['title']}")
    return 0


def phase_items(overview: str) -> tuple[dict[str, list[str]], dict[str, str], list[str]]:
    """Phase → item ids, phase → Depends on cell, and problems, from the overview."""
    secs = sections(Path(overview).read_text())
    rows = table(secs.get("Phases", []))
    out, deps, problems = {}, {}, []
    if not rows:
        return out, deps, ["overview: no '## Phases' table"]
    if "Items" not in rows[0]:
        return out, deps, ["overview: the Phases table has no 'Items' column"]
    for r in rows:
        ph = r.get("Phase", "").strip()
        out[ph] = r.get("Items", "")
        deps[ph] = r.get("Depends on", "")
    return out, deps, problems


def expand(cell: str, known: list[str]) -> list[str]:
    """Ids and ranges in a cell, expanded over the ids that exist, in list order."""
    out = []
    cell = cell.replace("..", "–").replace(" to ", "–")
    for part in re.split(r"[,;]", cell):
        ends = ids_in(part)
        if len(ends) == 2 and re.search(r"E-\d{3}[a-z]?\s*[–—-]\s*E-\d{3}", part):
            lo, hi = (int(ITEM_ID.match(e).group(1)) for e in ends)
            out += [k for k in known if lo <= int(ITEM_ID.match(k).group(1)) <= hi]
        else:
            out += ends
    return out


CITED = re.compile(r"^([^:\s]+?)(?::(\d+)(?:\s*[-–]\s*(\d+))?)?$")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
CONTEXT, MOST = 3, 40       # lines shown around a cited range; the most lines for one range


def reviewed_at(edits: str) -> str | None:
    """The commit the items' line numbers belong to: the last one the list's opening
    paragraph names, as `against `<sha>`` or after it."""
    head = Path(edits).read_text().split("\n## ")[0]
    found = re.findall(r"`([0-9a-f]{7,40})`", head)
    return found[-1] if found else None


def hunks(ref: str, path: str) -> list[tuple[int, int, int, int]] | None:
    """(old start, old count, new start, new count) per change to path since ref; None when
    git cannot say (no such ref, not a repository)."""
    r = subprocess.run(["git", "diff", "-U0", "--no-color", ref, "--", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    out = []
    for line in r.stdout.splitlines():
        m = HUNK.match(line)
        if m:
            out.append((int(m.group(1)), int(m.group(2) or 1), int(m.group(3)), int(m.group(4) or 1)))
    return out


def carry(line: int, changes: list[tuple[int, int, int, int]]) -> tuple[int, bool]:
    """Where a reviewed line is now, and whether it sits inside a change (then the place is
    the start of what replaced it)."""
    shift = 0
    for a, b, c, d in changes:
        if b == 0:                  # lines added after old line a
            if line <= a:
                break
        elif line < a:
            break
        elif line < a + b:
            return max(c, 1), True
        shift += d - b
    return line + shift, False


def located(item: dict, ref: str | None) -> list[str]:
    """The lines to print under an item: each cited place as it stands. With no commit to
    carry the numbers from, the lines at the review's own numbers."""
    out = [f"#### Where {item['id']}'s cited lines are now (numbers as reviewed at `{ref}` → the tree as it stands)"
           if ref else f"#### The lines {item['id']} cites, at the review's own numbers (the list names no commit to "
           "carry them from: check each against the item's text)", ""]
    for part in item["fields"].get("files", "").split(","):
        m = CITED.match(part.strip("` "))
        if not m or not m.group(2):
            continue                # a bare path cites no line
        path, lo = m.group(1), int(m.group(2))
        hi = int(m.group(3) or lo)
        cite = f"{path}:{lo}" + (f"-{hi}" if hi != lo else "")
        f = Path(path)
        if not f.is_file():
            out += [f"{cite} → the file is gone", ""]
            continue
        changes = hunks(ref, path) if ref else []
        if changes is None:
            out += [f"{cite} → git has no `{ref}` to carry it from; the numbers are the review's", ""]
            changes = []
        (new_lo, hit_lo), (new_hi, hit_hi) = carry(lo, changes), carry(hi, changes)
        inside = hit_lo or hit_hi or any(b and lo <= a <= hi for a, b, _, _ in changes)
        new_hi = max(new_hi, new_lo)
        now = f":{new_lo}" + (f"-{new_hi}" if new_hi != new_lo else "")
        out.append(f"{cite} → {now}" + ("" if not ref else ", changed since the review: an earlier phase may have "
                                         "made this edit" if inside else ", as reviewed" if (new_lo, new_hi) == (lo, hi)
                                         else ", moved"))
        text = f.read_text(errors="replace").split("\n")
        first, last = max(1, new_lo - CONTEXT), min(len(text), new_hi + CONTEXT, new_lo - CONTEXT + MOST)
        out += [f"{n:>6}  {text[n - 1]}" for n in range(first, last + 1)] + [""]
    return out if len(out) > 2 else []


def cmd_show(args) -> int:
    _, items, decisions = load_edits(args.edits)
    ref = args.at or reviewed_at(args.edits)
    known = [it["id"] for it in items]
    if args.phase is not None:
        if not args.overview:
            print("--phase needs --overview")
            return 2
        cells, _, problems = phase_items(args.overview)
        if problems:
            print("\n".join(f"FAIL {p}" for p in problems))
            return 1
        if args.phase not in cells:
            print(f"FAIL overview: no phase {args.phase}")
            return 1
        wanted = expand(cells[args.phase], known)
    else:
        wanted = []
        for a in args.ids:
            wanted += expand(a, known)
    by_id = {it["id"]: it for it in items}
    missing = [w for w in wanted if w not in by_id]
    cited = []
    for w in wanted:
        if w in by_id:
            print("\n".join(by_id[w]["raw"]) + "\n")
            if args.located:
                print("\n".join(located(by_id[w], ref)))
            cited += [d for d in DECISION_ID.findall(by_id[w]["fields"].get("decide", ""))
                      if d not in cited]
    if cited:
        print("## Decisions these items cite\n")
        for d in cited:
            r = decisions.get(d)
            print(f"- {d}: " + (" | ".join(f"{k}: {v}" for k, v in r.items()) if r else "no row"))
    for m in missing:
        print(f"FAIL {m}: not an item")
    return 1 if missing else 0


def depends_on(cell: str, phase: str, order: list[str]) -> set[str]:
    c = cell.lower()
    if "all" in c:
        return set(order[: order.index(phase)])
    return set(re.findall(r"\b\d+[a-z]?\b", cell))


def cmd_coverage(args) -> int:
    _, items, _ = load_edits(args.edits)
    known = [it["id"] for it in items]
    cells, dep_cells, problems = phase_items(args.overview)
    if problems:
        print("\n".join(f"FAIL {p}" for p in problems))
        return 1
    order = list(cells)
    where: dict[str, list[str]] = {}
    for ph, cell in cells.items():
        for i in expand(cell, known):
            where.setdefault(i, []).append(ph)
    for i, phs in where.items():
        if i not in known:
            problems.append(f"phase {', '.join(phs)}: {i} is not an item")
        elif len(phs) > 1:
            problems.append(f"{i}: in phases {', '.join(phs)}; an item is landed by one phase")
    for i in known:
        if i not in where:
            problems.append(f"{i}: in no phase")
    reach = {}
    for ph in order:
        direct = depends_on(dep_cells.get(ph, ""), ph, order)
        r = set(direct)
        for d in direct:
            r |= reach.get(d, set())
        reach[ph] = r
    for it in items:
        mine = where.get(it["id"], [None])[0]
        for d in ids_in(it["fields"].get("depends", "")):
            theirs = where.get(d, [None])[0]
            if mine is None or theirs is None or mine == theirs:
                continue
            if theirs not in reach.get(mine, set()):
                problems.append(f"{it['id']} (phase {mine}) depends on {d} (phase {theirs}), "
                                f"and phase {mine} does not depend on phase {theirs}")
    for line in problems:
        print(f"FAIL {line}")
    if not problems:
        print(f"ok: {len(known)} items in {sum(1 for c in cells.values() if ids_in(c))} phases")
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("findings"); p.add_argument("dir"); p.set_defaults(fn=cmd_findings)
    p = sub.add_parser("check"); p.add_argument("edits")
    p.add_argument("--decided", action="store_true")
    p.add_argument("--findings", metavar="DIR"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("index"); p.add_argument("edits"); p.set_defaults(fn=cmd_index)
    p = sub.add_parser("show"); p.add_argument("edits"); p.add_argument("ids", nargs="*")
    p.add_argument("--phase"); p.add_argument("--overview")
    p.add_argument("--located", action="store_true"); p.add_argument("--at", metavar="REF")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("coverage"); p.add_argument("edits"); p.add_argument("overview")
    p.set_defaults(fn=cmd_coverage)
    args = ap.parse_args(argv)
    if not Path(getattr(args, "edits", getattr(args, "dir", "."))).exists():
        print(f"no such path: {getattr(args, 'edits', getattr(args, 'dir', ''))}")
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
