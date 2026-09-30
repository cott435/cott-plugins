#!/usr/bin/env python3
"""PostToolUse hook on Write|Edit: fold a section's decisions inbox into `docs/decisions.md`.

Input: the hook JSON on stdin (`cwd`, `tool_input.file_path`). Exit 0 unless
`<cwd>/docs/architecture.md` exists and the path, made relative to `cwd`, matches
`docs/packages/*/decisions/*.md`. Any role or the main thread may have written it.

Under `.dev-team/locks/decisions/` (mkdir; wait ≤ 60 s; a lock older than 600 s is removed),
read the whole inbox and the central ledger, then, entry by entry in file order:

- `## D? — <question>`: the next free number (one more than the highest `## D<n>` in the
  central ledger, counting numbers assigned earlier in this run); append the entry whole to the
  central ledger with the heading renumbered; rewrite the inbox heading to `## D<n> —
  <question>`.
- `## D<n>` or `## D<n> — <question>` whose `n` exists centrally and whose question, when
  given, equals the central one (whitespace-normalized): the central entry's `Applied:` lines
  naming the inbox's own `<pkg>/<section>` are made equal to the inbox entry's (inbox order, at
  the position of the first such central line, else after the last `Applied:` line, else at
  the entry's end), so an `Applied:` line the inbox edits or removes is edited or removed
  centrally; an inbox line naming another section is copied once when the central entry lacks
  it (exact line match, stripped) and never removed. Other sections' central lines are
  untouched, and nothing else flows: `Decision:`, `Status:`, `Recommendation:` in the inbox
  are ignored.
- `## D<n>` whose `n` is absent centrally, or whose question differs: a stub; renumber as above.

Idempotent: a second run merges nothing. Creates `docs/decisions.md` (`# Decisions`) when it is
missing and there is something to append. On any change, prints JSON on stdout:
`{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "dev-team
decisions: <one clause per change, `; `-joined>"}}` — clauses `D? → D14`, `D14 → D15
(renumbered: not the central D14)`, `D7: 1 Applied: line added`, `D7: Applied: lines for
data/ingest set to the inbox's (2)` (a line edited or removed). No change: no stdout. Always
exit 0; any error is reported on stderr (`dev-team decisions sync: error — …`) and the inbox is
left as it was.

By hand, `python3 sync_decisions.py --all` from the repo root merges every inbox the same way,
prints one line per change, and exits 0 — the repair `status.py --run-gate` names when a
session without the hook (an interactive `claude --agent`, a harness that dropped it) left an
inbox unsynced.

The inbox parser is status.py's `inbox_entries`, imported; the central ledger is split on
`^## D(?=\\d)` as `status.decisions()` does, keeping each entry's raw text for rewriting.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[1])
STATUS_PY = PLUGIN_ROOT / "skills" / "status" / "scripts" / "status.py"
sys.path.insert(0, str(STATUS_PY.parent))
sys.dont_write_bytecode = True  # no __pycache__ inside the installed plugin
import status  # noqa: E402

INBOX = re.compile(r"docs/packages/[^/]+/decisions/[^/]+\.md")
HEAD = re.compile(r"D(\?|\d+)\s*(?:[—–-]+\s*(.*))?$")  # an inbox heading, as status.inbox_entries reads it
WAIT = 60.0
POLL = 0.2
STALE = 600.0


class Busy(Exception):
    """The lock was not free within WAIT."""


def _norm(question: str) -> str:
    return " ".join(question.split())


def _lock(root: Path) -> Path:
    lock = root / ".dev-team" / "locks" / "decisions"
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + WAIT
    while True:
        try:
            os.mkdir(lock)
            return lock
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > STALE:
                    os.rmdir(lock)
                    continue
            except OSError:
                continue
        if time.monotonic() >= deadline:
            raise Busy(f"{lock} held for more than {WAIT:.0f}s")
        time.sleep(POLL)


class Ledger:
    """docs/decisions.md as a preamble and a list of raw `## D<n>` entries, edited in memory."""

    def __init__(self, path: Path):
        self.path = path
        self.existed = path.exists()
        text = path.read_text() if self.existed else ""
        starts = [m.start() for m in re.finditer(r"^## D(?=\d)", text, flags=re.M)]
        self.preamble = text[:starts[0]] if starts else text
        self.entries = [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]
        self.changed = False

    def _find(self, n: str) -> int | None:
        for i, e in enumerate(self.entries):
            m = re.match(r"## D(\d+)", e)
            if m and m.group(1) == n:
                return i
        return None

    def question(self, n: str) -> str | None:
        """The central D<n>'s question, or None when the ledger has no D<n>."""
        i = self._find(n)
        if i is None:
            return None
        m = re.match(r"## D\d+\s*[—–-]?\s*(.*)", self.entries[i].splitlines()[0])
        return m.group(1).strip() if m else ""

    def next_free(self) -> int:
        nums = [int(m.group(1)) for e in self.entries if (m := re.match(r"## D(\d+)", e))]
        return max(nums, default=0) + 1

    def append(self, heading: str, body: str) -> None:
        if not self.existed and not self.entries and not self.preamble.strip():
            self.preamble = "# Decisions\n\n"
        if self.entries:
            last = self.entries[-1].rstrip("\n") + "\n\n"
            self.entries[-1] = last
        elif self.preamble.strip():
            self.preamble = self.preamble.rstrip("\n") + "\n\n"
        self.entries.append(f"## {heading}\n" + body.strip("\n") + "\n")
        self.changed = True

    def mirror_applied(self, n: str, owner: str, want: list[str]) -> tuple[int, bool]:
        """Make D<n>'s Applied: lines naming owner equal want; (lines added, whether any existing
        line of owner's was edited or removed)."""
        i = self._find(n)
        rows = self.entries[i].split("\n")
        own = [k for k, line in enumerate(rows) if status._applied_lines(line) and status.applied_owner(line) == owner]
        want = list(dict.fromkeys(want))
        if [rows[k].strip() for k in own] == want:
            return 0, False
        if own:
            at = own[0]
            for k in reversed(own):
                del rows[k]
        else:
            applied = [k for k, line in enumerate(rows) if status._applied_lines(line)]
            if applied:
                at = applied[-1] + 1
            else:
                at = len(rows)
                while at > 1 and not rows[at - 1].strip():
                    at -= 1
        rows[at:at] = want
        self.entries[i] = "\n".join(rows)
        self.changed = True
        return len(want), bool(own)

    def add_applied(self, n: str, lines: list[str]) -> int:
        """Add the Applied: lines D<n> lacks; how many were added."""
        i = self._find(n)
        entry = self.entries[i]
        have = {line.strip() for line in entry.splitlines()}
        new = [line for line in dict.fromkeys(lines) if line not in have]
        if not new:
            return 0
        rows = entry.split("\n")
        applied = [k for k, line in enumerate(rows) if status._applied_lines(line)]
        if applied:
            at = applied[-1] + 1
        else:
            at = len(rows)
            while at > 1 and not rows[at - 1].strip():
                at -= 1
        rows[at:at] = new
        self.entries[i] = "\n".join(rows)
        self.changed = True
        return len(new)

    def write(self) -> None:
        if self.changed:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(self.path.name + ".sync-tmp")
            tmp.write_text(self.preamble + "".join(self.entries))
            os.replace(tmp, self.path)


def merge(inbox: Path, ledger: Ledger) -> tuple[str | None, list[str]]:
    """Merge one inbox into the ledger; (the inbox's new text or None, one clause per change)."""
    text = inbox.read_text()
    entries = status.inbox_entries(inbox)
    owner = status.inbox_section(inbox)
    # The heading lines inbox_entries accepted, in the same order, so each can be rewritten.
    heads = [m for m in re.finditer(r"^## (?=D[?\d])(.*)$", text, flags=re.M) if HEAD.match(m.group(1).strip())]
    edits: list[tuple[int, int, str]] = []
    clauses: list[str] = []
    for e, h in zip(entries, heads):
        n, question = str(e["n"]), str(e["question"])
        central = None if n == "?" else ledger.question(n)
        if central is not None and (not question or _norm(question) == _norm(central)):
            lines = list(e["Applied"])  # type: ignore[arg-type]
            mine = [line for line in lines if status.applied_owner(line) == owner]
            count, replaced = ledger.mirror_applied(n, owner, mine)
            added = ledger.add_applied(n, [line for line in lines if status.applied_owner(line) != owner])
            if replaced:
                clauses.append(f"D{n}: Applied: lines for {owner} set to the inbox's ({count})")
            added += 0 if replaced else count
            if added:
                clauses.append(f"D{n}: {added} Applied: line{'s' if added > 1 else ''} added")
            continue
        new = ledger.next_free()
        heading = f"D{new} — {question}" if question else f"D{new}"
        ledger.append(heading, str(e["raw"]).split("\n", 1)[1] if "\n" in str(e["raw"]) else "")
        edits.append((h.start(1), h.end(1), heading))
        clauses.append(f"D? → D{new}" if n == "?" else f"D{n} → D{new} (renumbered: not the central D{n})")
    for a, b, heading in reversed(edits):
        text = text[:a] + heading + text[b:]
    return (text if edits else None), clauses


def sync(root: Path, inboxes: list[Path]) -> list[tuple[Path, str]]:
    """Merge the inboxes in order under the lock; (inbox, clause) per change."""
    lock = _lock(root)
    try:
        ledger = Ledger(root / "docs" / "decisions.md")
        rewrites, out = [], []
        for inbox in inboxes:
            new_text, clauses = merge(inbox, ledger)
            if new_text is not None:
                rewrites.append((inbox, new_text))
            out += [(inbox, c) for c in clauses]
        ledger.write()
        for inbox, new_text in rewrites:
            tmp = inbox.with_name(inbox.name + ".sync-tmp")
            tmp.write_text(new_text)
            os.replace(tmp, inbox)
        return out
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


def main(argv: list[str]) -> int:
    try:
        if argv == ["--all"]:
            root = Path.cwd().resolve()
            if not (root / "docs" / "architecture.md").exists():
                return 0
            status.set_root(root)
            for inbox, clause in sync(root, status.inbox_files()):
                print(f"{inbox.relative_to(root).as_posix()}: {clause}")
            return 0
        if argv:
            print("dev-team decisions sync: error — usage: sync_decisions.py [--all]", file=sys.stderr)
            return 0
        event = json.loads(sys.stdin.read())
        cwd = Path(event["cwd"])
        raw = (event.get("tool_input") or {}).get("file_path") or ""
        if not raw or not (cwd / "docs" / "architecture.md").exists():
            return 0
        root = Path(os.path.realpath(cwd))
        path = Path(os.path.realpath(raw if os.path.isabs(raw) else os.path.join(cwd, raw)))
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if not INBOX.fullmatch(rel) or not path.exists():
            return 0
        status.set_root(root)
        clauses = [c for _, c in sync(root, [path])]
        if clauses:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "dev-team decisions: " + "; ".join(clauses),
            }}, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 — a hook fails open, reported
        print(f"dev-team decisions sync: error — {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
