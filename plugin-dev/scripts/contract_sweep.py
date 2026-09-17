#!/usr/bin/env python3
"""Check the cross-file claims a plugin's agents act on and nothing else verifies.

A plugin is a set of prompts that reference each other by name: one agent owns a document
template, others parse it by heading; one skill forbids something another still describes.
Nothing fails when those drift — the agent just reads for a heading that is never written.
This runner checks the claims a bundle declares in its own `contracts.yml`.

Three kinds of claim, all of them about file contents, so all of them decidable without
running a model:

  forbid        a pattern that must not appear (a rule one file states and another breaks)
  headings      every heading a reader parses is one the owner's template defines
  names_listed  every directory under <dirs> has its name in <file> (a list that goes stale)

Usage:  python3 contract_sweep.py [bundle] [--quiet]
Exits 1 if any case fails, 0 if all pass, 2 if the bundle has no contracts.yml.

`contracts.yml` lives at the bundle root. See the check-contracts skill for the schema and a
worked example; `--help` prints it too.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

# Authored files only. Generated mirrors (site/docs/) would double every finding, and a
# finding there is fixed in the source anyway.
DEFAULT_FILES = ["agents/*.md", "skills/**/*.md", "rules/*.md", "README.md", "CLAUDE.md",
                 "site/*.md", "site/workflows/*.md", "site/notes/*.md"]


def authored(bundle: Path, globs: list[str]) -> list[Path]:
    """Every existing file matching any glob, once, in a stable order."""
    out: dict[Path, None] = {}
    for g in globs:
        for p in sorted(bundle.glob(g)):
            if p.is_file() and "/site/docs/" not in p.as_posix():
                out[p] = None
    return list(out)


def span(text: str, bounds: list | None, where: str) -> str:
    """The slice of text between two literal markers. bounds is [start, end]; end may be null."""
    if not bounds:
        return text
    start, end = (bounds + [None])[:2]
    if start not in text:
        raise LookupError(f"{where}: marker not found: {start!r}")
    i = text.index(start)
    if not end:
        return text[i:]
    if end not in text[i:]:
        raise LookupError(f"{where}: end marker not found after start: {end!r}")
    return text[i:text.index(end, i)]


def template_items(block: str) -> set[str]:
    """Names of a numbered, bolded template: `3. **CLI commands** — table: …` -> {CLI commands}."""
    return {" ".join(m.group(1).split()) for m in re.finditer(r"^\d+\. \*\*(.+?)\*\*", block, re.M)}


def bolded(block: str) -> set[str]:
    """Every **Bolded Name** in a block, whitespace collapsed so a line break does not hide one."""
    return {" ".join(m.group(1).split()) for m in re.finditer(r"\*\*([A-Z][^*]{2,40})\*\*", block)}


def check_forbid(bundle: Path, spec: dict) -> tuple[bool, str]:
    """A line matching `pattern` (and containing every `all_of`) is a failure unless `unless`."""
    pattern = re.compile(spec["pattern"])
    unless = [re.compile(u) for u in spec.get("unless", [])]
    all_of = spec.get("all_of", [])
    hits = []
    for p in authored(bundle, spec.get("files", DEFAULT_FILES)):
        for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if not pattern.search(line):
                continue
            if any(a not in line for a in all_of) or any(u.search(line) for u in unless):
                continue
            hits.append(f"{p.relative_to(bundle)}:{n}")
    return not hits, ", ".join(hits) or "0 matches"


def check_headings(bundle: Path, spec: dict) -> tuple[bool, str]:
    """Every heading a reader names is one the owner's template defines."""
    owner = bundle / spec["owner"]
    owned = template_items(span(owner.read_text(), spec.get("owner_span"), spec["owner"]))
    if not owned:
        return False, f"{spec['owner']}: no numbered template items found in the owner span"
    bad, counted = [], 0
    for reader in spec["readers"]:
        path = bundle / reader["file"]
        text = path.read_text()
        named = bolded(span(text, reader.get("span"), reader["file"])) if reader.get("span") else set()
        named |= {" ".join(c.split()) for c in reader.get("cites", [])}
        counted += len(named)
        for h in sorted(named):
            if not any(h.lower() == o.lower() for o in owned):
                bad.append(f"{reader['file']} names '{h}'")
    return not bad, "; ".join(bad) or f"{counted} names across {len(spec['readers'])} readers, all owned"


def check_names_listed(bundle: Path, spec: dict) -> tuple[bool, str]:
    """Every directory matching `dirs` has its name inside `file` (optionally within a span)."""
    listing = bundle / spec["file"]
    block = span(listing.read_text(), spec.get("span"), spec["file"])
    names = sorted({p.name for g in [spec["dirs"]] for p in bundle.glob(g.rstrip("/")) if p.is_dir()})
    missing = [n for n in names if not re.search(rf"`{re.escape(n)}`", block)]
    extra = [w for w in re.findall(r"`([a-z][a-z0-9-]{2,})`", block) if w not in names]
    detail = []
    if missing:
        detail.append(f"not listed in {spec['file']}: {', '.join(missing)}")
    if extra:
        detail.append(f"listed but no such directory: {', '.join(sorted(set(extra)))}")
    return not detail, "; ".join(detail) or f"{len(names)} names, all listed"


CHECKS = {"forbid": check_forbid, "headings": check_headings, "names_listed": check_names_listed}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0
    quiet = "--quiet" in sys.argv
    bundle = Path(args[0] if args else ".").resolve()
    config = bundle / "contracts.yml"
    if not config.exists():
        print(f"no contracts.yml in {bundle.name} — nothing declared to check")
        return 2
    try:
        import yaml
    except ImportError:
        sys.exit("contracts.yml needs PyYAML — `pip install pyyaml` (mkdocs pulls it in).")
    declared = yaml.safe_load(config.read_text()) or {}

    rows = []
    for kind, specs in declared.items():
        if kind not in CHECKS:
            rows.append((f"[{kind}]", "ERROR", f"unknown check kind; known: {', '.join(CHECKS)}"))
            continue
        for spec in specs:
            try:
                ok, detail = CHECKS[kind](bundle, spec)
            except (LookupError, OSError) as e:
                ok, detail = False, f"could not run: {e}"
            rows.append((spec.get("name", kind), "PASS" if ok else "FAIL", detail))

    if not rows:
        print("contracts.yml declares no checks")
        return 2
    width = max(len(r[0]) for r in rows)
    for name, verdict, detail in rows:
        if verdict != "PASS" or not quiet:
            print(f"{verdict}  {name:<{width}}  {detail}")
    failed = [r for r in rows if r[1] != "PASS"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
