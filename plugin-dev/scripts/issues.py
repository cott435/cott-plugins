#!/usr/bin/env python3
"""The audit ledger: issue files under a plugin's `runs/audits/issues/`, and `runs/audits/INDEX.md`.

An audit finding that a plugin can fix becomes an issue with an id that stays the same across
audits (`<PREFIX>-<nnn>`). Each issue is one file, shaped by `templates/audits/issue.md` in
this bundle, whose sections each have one writer: audit-run writes the frontmatter, Finding,
Found in and Checks; fix-issues writes Fix attempts; bump-version writes only `fixed_in`. All of
them write through this script, and nothing writes an issue file by hand.

An issue's status is never stored. It is derived from the file, in this order:

  wontfix   the latest attempt is a wontfix
  open      there is no attempt
  recurred  the latest held-or-recurred Check on the latest attempt is `recurred`
  verified  ... is `held`
  released  the latest attempt's `fixed_in` is set
  fixed     otherwise

A Check of `not exercised` or `not testable` changes nothing.

The plugin is the directory given by --dir (default: the working directory); its name, and so
the id prefix, comes from `<dir>/.claude-plugin/plugin.json`. The ledger is `<dir>/runs/audits/`,
created on the first write. Every writing command re-renders `runs/audits/INDEX.md` before it exits.

Usage:  python3 issues.py <command> [--dir DIR] ...   (`--help` on any command for its flags)

Commands: new, candidates, seen, check-result, fix, wontfix, stamp, list, status, index, check.
Exit 0 on success; 1 with one line per problem on stderr otherwise.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "audits" / "issue.md"

STATUS_ORDER = ["recurred", "open", "fixed", "released", "verified", "wontfix"]
DASH = "—"
SEP = " · "

FOUND_RE = re.compile(
    r'^- (?P<date>\S+) · (?P<session>\S+) · (?P<version>\S+) · (?P<unit>.+?) · (?P<step>\S+)'
    r' — "(?P<evidence>.*)" · (?P<report>\S+) (?P<finding_id>\S+)$')
BULLET_RE = re.compile(r"^- (?P<key>[A-Za-z_]+):(?: (?P<value>.*))?$")
ATTEMPT_RE = re.compile(r"^### Attempt (?P<n>\d+)\s*$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
APPLIES_RE = re.compile(r"^(agent:\S+|driver:\S+|cross)$")


class LedgerError(Exception):
    """One or more problems, one per line, that end the command with exit 1."""

    def __init__(self, *problems: str):
        super().__init__("\n".join(problems))
        self.problems = list(problems)


# --- the template ------------------------------------------------------------------------

def load_template() -> dict:
    """Read the frontmatter keys, the word lists, the sections and attempt keys from the template.

    The template is the one place these are defined; nothing here repeats them.
    """
    text = TEMPLATE.read_text()
    fm, body = split_frontmatter(text)
    keys = [k for k, _ in fm]
    enums = {}
    for key, value in fm:
        m = re.fullmatch(r"<([^<>:]+)>", value)
        if m and " | " in m.group(1):
            enums[key] = [w.strip() for w in m.group(1).split("|")]
    sections = [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]
    attempt_keys = [m.group("key") for line in body.splitlines()
                    if (m := BULLET_RE.match(line))]
    verdicts = []
    checks_part = body.split("## Checks", 1)[1]
    m = re.search(r"<(held[^<>]*)>", checks_part)
    if m:
        verdicts = [w.strip() for w in m.group(1).split("|")]
    status_m = re.search(r"^- status: <([^<>]+)>", body, re.M)
    attempt_statuses = [w.strip() for w in status_m.group(1).split("|")] if status_m else []
    return {"keys": keys, "enums": enums, "sections": sections,
            "attempt_keys": attempt_keys, "verdicts": verdicts,
            "attempt_statuses": attempt_statuses}


def split_frontmatter(text: str) -> tuple[list[tuple[str, str]], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    try:
        end = lines.index("---", 1)
    except ValueError:
        return [], text
    pairs = []
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        pairs.append((key.strip(), value.strip()))
    return pairs, "\n".join(lines[end + 1:])


# --- the plugin and its ledger ------------------------------------------------------------

def plugin_name(root: Path) -> str:
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        raise LedgerError(f"no .claude-plugin/plugin.json in {root}")
    try:
        name = json.loads(manifest.read_text())["name"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise LedgerError(f"{manifest}: cannot read its name ({exc})") from exc
    return name


def prefix_of(name: str) -> str:
    """`dev-team` → DT, `plugin-dev` → PD, `a-b-c` → ABC, `toy` → TO."""
    parts = [p for p in name.split("-") if p]
    if len(parts) > 1:
        return "".join(p[0] for p in parts).upper()
    return name[:2].upper()


def ledger_dir(root: Path) -> Path:
    return root / "runs" / "audits"


def issues_dir(root: Path) -> Path:
    return ledger_dir(root) / "issues"


# --- one issue file -----------------------------------------------------------------------

class Issue:
    """An issue file, parsed. Section bodies are kept as lines so writes preserve them."""

    def __init__(self, path: Path, text: str):
        self.path = path
        fm, body = split_frontmatter(text)
        self.frontmatter = dict(fm)
        self.frontmatter_order = [k for k, _ in fm]
        self.sections: dict[str, list[str]] = {}
        self.section_order: list[str] = []
        current = None
        for line in body.splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                self.section_order.append(current)
                self.sections[current] = []
            elif current is not None:
                self.sections[current].append(line)
        for name in self.sections:
            self.sections[name] = trim(self.sections[name])

    @property
    def id(self) -> str:
        return self.frontmatter.get("id", "")

    # parsed views

    def found_in(self) -> list[dict]:
        return [m.groupdict() for line in self.sections.get("Found in", [])
                if (m := FOUND_RE.match(line))]

    def attempts(self) -> list[dict]:
        out: list[dict] = []
        for line in self.sections.get("Fix", []):
            if m := ATTEMPT_RE.match(line):
                out.append({"n": int(m.group("n"))})
            elif out and (m := BULLET_RE.match(line)):
                out[-1][m.group("key")] = (m.group("value") or "").strip()
        return out

    def checks(self, verdicts: list[str]) -> list[dict]:
        rx = checks_re(verdicts)
        return [dict(m.groupdict(), attempt=int(m.group("attempt")))
                for line in self.sections.get("Checks", []) if (m := rx.match(line))]

    def status(self, verdicts: list[str]) -> str:
        attempts = self.attempts()
        if not attempts:
            return "open"
        latest = attempts[-1]
        if latest.get("status") == "wontfix":
            return "wontfix"
        decisive = [c["verdict"] for c in self.checks(verdicts)
                    if c["attempt"] == latest["n"] and c["verdict"] in ("held", "recurred")]
        if decisive:
            return "recurred" if decisive[-1] == "recurred" else "verified"
        if latest.get("fixed_in"):
            return "released"
        return "fixed"

    def record(self, verdicts: list[str]) -> dict:
        return {"id": self.id, "path": str(self.path), "frontmatter": self.frontmatter,
                "finding": "\n".join(self.sections.get("Finding", [])),
                "found_in": self.found_in(), "attempts": self.attempts(),
                "checks": self.checks(verdicts), "status": self.status(verdicts)}

    def applies_to(self) -> list[str]:
        return [a.strip() for a in self.frontmatter.get("applies_to", "").split(",") if a.strip()]

    # writing

    def render(self, template: dict) -> str:
        keys = template["keys"] + [k for k in self.frontmatter_order if k not in template["keys"]]
        out = ["---"] + [f"{k}: {self.frontmatter[k]}" for k in keys if k in self.frontmatter]
        out += ["---", ""]
        names = self.section_order or template["sections"]
        blocks = []
        for name in names:
            body = trim(self.sections.get(name, []))
            blocks.append("\n".join([f"## {name}", ""] + body) if body else f"## {name}")
        return "\n".join(out) + "\n" + "\n\n".join(blocks) + "\n"

    def append(self, section: str, lines: list[str], gap: bool = False) -> None:
        body = trim(self.sections.setdefault(section, []))
        if section not in self.section_order:
            self.section_order.append(section)
        if body and gap:
            body.append("")
        self.sections[section] = body + lines


def checks_re(verdicts: list[str]) -> re.Pattern:
    words = "|".join(re.escape(v) for v in sorted(verdicts, key=len, reverse=True))
    return re.compile(
        r'^- (?P<date>\S+) · (?P<session>\S+) · (?P<version>\S+) · attempt (?P<attempt>\d+)'
        rf' · (?P<verdict>{words}) · (?P<unit>.+?) · (?P<step>\S+) — "(?P<evidence>.*)"$')


def trim(lines: list[str]) -> list[str]:
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def load_issues(root: Path) -> list[Issue]:
    folder = issues_dir(root)
    if not folder.is_dir():
        return []
    return [Issue(p, p.read_text()) for p in sorted(folder.glob("*.md"))]


def get_issue(root: Path, issue_id: str) -> Issue:
    path = issues_dir(root) / f"{issue_id}.md"
    if not path.is_file():
        raise LedgerError(f"no issue {issue_id} ({path})")
    return Issue(path, path.read_text())


def save(issue: Issue, template: dict) -> None:
    issue.path.parent.mkdir(parents=True, exist_ok=True)
    issue.path.write_text(issue.render(template))


# --- the index ----------------------------------------------------------------------------

def cell(text: str) -> str:
    return text.replace("|", "\\|")


def sort_key(issue: Issue, verdicts: list[str]) -> tuple:
    status = issue.status(verdicts)
    rank = STATUS_ORDER.index(status) if status in STATUS_ORDER else len(STATUS_ORDER)
    return (rank, issue.id, issue.path.name)


def render_index(root: Path, name: str, template: dict) -> str:
    verdicts = template["verdicts"]
    issues = sorted(load_issues(root), key=lambda i: sort_key(i, verdicts))
    out = ["<!-- generated by issues.py — do not edit by hand; `issues.py index` rewrites it -->",
           f"# {name} · audit issues", "",
           "| Id | Title | Fault | Severity | Status | Found | Seen | Fixed in | Last check |",
           "|---|---|---|---|---|---|---|---|---|"]
    for issue in issues:
        fm = issue.frontmatter
        attempts = issue.attempts()
        fixed_in = (attempts[-1].get("fixed_in") if attempts else "") or DASH
        checks = issue.checks(verdicts)
        last = f"{checks[-1]['date']} {checks[-1]['verdict']}" if checks else DASH
        out.append("| " + " | ".join([
            f"[{issue.id}](issues/{issue.path.name})", cell(fm.get("title", "")),
            fm.get("fault", ""), fm.get("severity", ""), issue.status(verdicts),
            f"{fm.get('found_date', '')} {fm.get('found_session', '')}",
            str(len(issue.found_in())), fixed_in, last]) + " |")
    return "\n".join(out) + "\n"


def write_index(root: Path, name: str, template: dict) -> None:
    path = ledger_dir(root) / "INDEX.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_index(root, name, template))


# --- validation ---------------------------------------------------------------------------

def one_line(**fields: str | None) -> None:
    bad = [f"--{k.replace('_', '-')} must be one line" for k, v in fields.items()
           if v is not None and ("\n" in v or "\r" in v)]
    if bad:
        raise LedgerError(*bad)


def check_enum(template: dict, key: str, value: str) -> list[str]:
    allowed = template["enums"].get(key)
    if allowed and value not in allowed:
        return [f"--{key.replace('_', '-')} {value!r} is not one of: {', '.join(allowed)}"]
    return []


def check_applies(value: str) -> list[str]:
    entries = [a.strip() for a in value.split(",") if a.strip()]
    if not entries:
        return ["--applies-to names nothing"]
    return [f"--applies-to entry {a!r} is not agent:<type>, driver:<skill> or cross"
            for a in entries if not APPLIES_RE.match(a)]


def check_date(flag: str, value: str) -> list[str]:
    return [] if DATE_RE.match(value) else [f"{flag} {value!r} is not YYYY-MM-DD"]


def agent_role(entry: str) -> str:
    """`agent:dev-team:profiler` and `agent:profiler` both match as `agent:profiler`."""
    if entry.startswith("agent:"):
        return "agent:" + entry.split(":")[-1]
    return entry


def shares_applies(issue: Issue, wanted: str) -> bool:
    want = {agent_role(a.strip()) for a in wanted.split(",") if a.strip()}
    return bool(want & {agent_role(a) for a in issue.applies_to()})


# --- git ----------------------------------------------------------------------------------

def in_git(root: Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True)
    except FileNotFoundError:
        return False
    return r.returncode == 0 and r.stdout.strip() == "true"


def is_ancestor(root: Path, commit: str) -> bool:
    r = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"],
                       capture_output=True, text=True)
    return r.returncode == 0


# --- commands -----------------------------------------------------------------------------

def cmd_new(a, root, name, t) -> list[str]:
    one_line(title=a.title, rule_quote=a.rule_quote, evidence=a.evidence, unit=a.unit,
             step=a.step, report=a.report, finding_id=a.finding_id, rule_file=a.rule_file,
             found_version=a.found_version, found_session=a.found_session)
    problems = (check_enum(t, "fault", a.fault) + check_enum(t, "severity", a.severity)
                + check_enum(t, "check", a.check) + check_applies(a.applies_to)
                + check_date("--found-date", a.found_date))
    if a.rule_line != "none" and not a.rule_line.isdigit():
        problems.append(f"--rule-line {a.rule_line!r} is not a line number or none")
    if not a.finding.strip():
        problems.append("--finding is empty")
    if problems:
        raise LedgerError(*problems)
    prefix = prefix_of(name)
    numbers = [int(m.group(1)) for p in issues_dir(root).glob(f"{prefix}-*.md")
               if (m := re.fullmatch(rf"{re.escape(prefix)}-(\d+)\.md", p.name))]
    issue_id = f"{prefix}-{max(numbers, default=0) + 1:03d}"
    values = {"id": issue_id, "plugin": name, "title": a.title, "fault": a.fault,
              "severity": a.severity, "check": a.check,
              "applies_to": ", ".join(x.strip() for x in a.applies_to.split(",") if x.strip()),
              "rule_file": a.rule_file, "rule_line": a.rule_line, "rule_quote": a.rule_quote,
              "found_version": a.found_version, "found_session": a.found_session,
              "found_date": a.found_date}
    missing = [k for k in t["keys"] if k not in values]
    if missing:
        raise LedgerError(f"the template has keys this script does not fill: {', '.join(missing)}")
    issue = Issue(issues_dir(root) / f"{issue_id}.md", "")
    issue.frontmatter = values
    issue.frontmatter_order = list(t["keys"])
    issue.section_order = list(t["sections"])
    issue.sections = {s: [] for s in t["sections"]}
    issue.sections["Finding"] = trim(a.finding.strip().splitlines())
    issue.sections["Found in"] = [found_line(a.found_date, a.found_session, a.found_version,
                                             a.unit, a.step, a.evidence, a.report, a.finding_id)]
    save(issue, t)
    return [issue_id]


def found_line(date, session, version, unit, step, evidence, report, finding_id) -> str:
    return (f"- {date}{SEP}{session}{SEP}{version}{SEP}{unit}{SEP}{step} — \"{evidence}\""
            f"{SEP}{report} {finding_id}")


def cmd_seen(a, root, name, t) -> list[str]:
    one_line(session=a.session, version=a.version, unit=a.unit, step=a.step,
             evidence=a.evidence, report=a.report, finding_id=a.finding_id)
    problems = check_date("--date", a.date)
    if problems:
        raise LedgerError(*problems)
    issue = get_issue(root, a.id)
    issue.append("Found in", [found_line(a.date, a.session, a.version, a.unit, a.step,
                                         a.evidence, a.report, a.finding_id)])
    save(issue, t)
    return []


def cmd_check_result(a, root, name, t) -> list[str]:
    one_line(session=a.session, version=a.version, unit=a.unit, step=a.step, evidence=a.evidence)
    problems = check_date("--date", a.date)
    if a.verdict not in t["verdicts"]:
        problems.append(f"--verdict {a.verdict!r} is not one of: {', '.join(t['verdicts'])}")
    if a.verdict == "held" and not a.step:
        problems.append("--verdict held needs --step: a held check cites the step that shows it")
    issue = get_issue(root, a.id)
    numbers = [x["n"] for x in issue.attempts()]
    if a.attempt not in numbers:
        problems.append(f"{a.id} has no attempt {a.attempt}"
                        + (f" (attempts: {', '.join(map(str, numbers))})" if numbers else ""))
    if problems:
        raise LedgerError(*problems)
    line = (f"- {a.date}{SEP}{a.session}{SEP}{a.version}{SEP}attempt {a.attempt}{SEP}{a.verdict}"
            f"{SEP}{a.unit or DASH}{SEP}{a.step or DASH} — \"{a.evidence}\"")
    issue.append("Checks", [line])
    save(issue, t)
    return []


def next_attempt(issue: Issue) -> int:
    return max((x["n"] for x in issue.attempts()), default=0) + 1


def cmd_fix(a, root, name, t) -> list[str]:
    one_line(branch=a.branch, commit=a.commit, files=a.files, evals=a.evals, verify=a.verify)
    problems = []
    if not a.commit:
        problems.append("fix needs --commit: a fixed attempt names the commit that fixed it")
    elif not COMMIT_RE.match(a.commit):
        problems.append(f"--commit {a.commit!r} is not 7-40 hex characters")
    if "held when" not in a.verify:
        problems.append("--verify must say what a trace shows when the fix held: 'held when …'")
    if "recurred when" not in a.verify:
        problems.append("--verify must say what a trace shows when it recurred: 'recurred when …'")
    issue = get_issue(root, a.id)
    if problems:
        raise LedgerError(*problems)
    lines = [f"### Attempt {next_attempt(issue)}", "- status: fixed", f"- branch: {a.branch}",
             f"- commit: {a.commit}", f"- files: {a.files}", f"- evals: {a.evals}",
             "- fixed_in:", f"- Verify: {a.verify}"]
    issue.append("Fix", lines, gap=True)
    save(issue, t)
    return []


def cmd_wontfix(a, root, name, t) -> list[str]:
    one_line(reason=a.reason)
    if not a.reason.strip():
        raise LedgerError("--reason is empty")
    issue = get_issue(root, a.id)
    issue.append("Fix", [f"### Attempt {next_attempt(issue)}", "- status: wontfix",
                         f"- reason: {a.reason}"], gap=True)
    save(issue, t)
    return []


def cmd_stamp(a, root, name, t) -> list[str]:
    one_line(version=a.version)
    git = in_git(root)
    stamped, skipped = [], []
    for issue in load_issues(root):
        if issue.status(t["verdicts"]) != "fixed":
            continue
        latest = issue.attempts()[-1]
        commit = latest.get("commit", "")
        if git and not (commit and is_ancestor(root, commit)):
            skipped.append(f"not stamped: {issue.id} — its commit {commit or '(none)'} is not "
                           "an ancestor of HEAD")
            continue
        fix = issue.sections["Fix"]
        start = max(i for i, line in enumerate(fix) if ATTEMPT_RE.match(line))
        for i in range(start + 1, len(fix)):
            if ATTEMPT_RE.match(fix[i]):
                break
            if re.match(r"^- fixed_in:\s*$", fix[i]):
                fix[i] = f"- fixed_in: {a.version}"
                break
        else:
            fix.insert(start + 1, f"- fixed_in: {a.version}")
        save(issue, t)
        stamped.append(issue.id)
    for line in skipped:
        print(line, file=sys.stderr)
    return stamped or ["none"]


def selected(a, root, t) -> list[Issue]:
    verdicts = t["verdicts"]
    issues = sorted(load_issues(root), key=lambda i: sort_key(i, verdicts))
    if a.status:
        wanted = [s.strip() for s in a.status.split(",") if s.strip()]
        bad = [s for s in wanted if s not in STATUS_ORDER]
        if bad:
            raise LedgerError(*[f"--status {s!r} is not one of: {', '.join(STATUS_ORDER)}"
                                for s in bad])
        issues = [i for i in issues if i.status(verdicts) in wanted]
    if a.applies_to:
        issues = [i for i in issues if shares_applies(i, a.applies_to)]
    if a.session:
        id8 = a.session[:8]
        issues = [i for i in issues if any(f["session"][:8] == id8 for f in i.found_in())]
    return issues


def cmd_list(a, root, name, t) -> list[str]:
    issues = selected(a, root, t)
    v = t["verdicts"]
    if a.format == "json":
        return [json.dumps([i.record(v) for i in issues], indent=2, ensure_ascii=False)]
    lines = [SEP.join([i.id, i.status(v), i.frontmatter.get("severity", ""),
                       i.frontmatter.get("fault", ""), i.frontmatter.get("applies_to", ""),
                       i.frontmatter.get("title", "")]) for i in issues]
    return lines or ["none"]


def cmd_candidates(a, root, name, t) -> list[str]:
    v = t["verdicts"]
    out = []
    for issue in sorted(load_issues(root), key=lambda i: i.id):
        fm = issue.frontmatter
        if fm.get("rule_file") != a.rule_file or fm.get("fault") != a.fault:
            continue
        if a.applies_to and not shares_applies(issue, a.applies_to):
            continue
        out.append(SEP.join([issue.id, fm.get("severity", ""), issue.status(v),
                             f"\"{fm.get('rule_quote', '')}\"", fm.get("title", "")]))
    return out or ["none"]


def cmd_status(a, root, name, t) -> list[str]:
    return [get_issue(root, a.id).status(t["verdicts"])]


def cmd_index(a, root, name, t) -> list[str]:
    return []  # main() re-renders the index after every writing command


def cmd_check(a, root, name, t) -> list[str]:
    problems = []
    verdicts = t["verdicts"]
    seen: dict[str, list[str]] = {}
    issues = load_issues(root)
    for issue in issues:
        f = issue.path.name
        seen.setdefault(issue.id, []).append(f)
        if issue.id != issue.path.stem:
            problems.append(f"{f}: file name is not its id ({issue.id or 'no id'})")
        missing = [k for k in t["keys"] if k not in issue.frontmatter]
        extra = [k for k in issue.frontmatter if k not in t["keys"]]
        if missing:
            problems.append(f"{f}: frontmatter key(s) missing: {', '.join(missing)}")
        if extra:
            problems.append(f"{f}: frontmatter key(s) not in the template: {', '.join(extra)}")
        for key in t["enums"]:
            if key in issue.frontmatter:
                problems += [f"{f}: {p.lstrip('-')}"
                             for p in check_enum(t, key, issue.frontmatter[key])]
        for section in t["sections"]:
            if section not in issue.sections:
                problems.append(f"{f}: missing section ## {section}")
        for line in issue.sections.get("Found in", []):
            if line.strip() and not FOUND_RE.match(line):
                problems.append(f"{f}: Found in line does not parse: {line[:80]}")
        rx = checks_re(verdicts)
        for line in issue.sections.get("Checks", []):
            if line.strip() and not rx.match(line):
                problems.append(f"{f}: Checks line does not parse: {line[:80]}")
        for c in issue.checks(verdicts):
            if c["verdict"] == "held" and c["step"] in ("", DASH):
                problems.append(f"{f}: a held check on {c['date']} ({c['session']}) has no step")
        for attempt in issue.attempts():
            if attempt.get("status") == "fixed" and not attempt.get("commit"):
                problems.append(f"{f}: attempt {attempt['n']} is fixed with no commit")
            if attempt.get("status") not in t["attempt_statuses"]:
                problems.append(f"{f}: attempt {attempt['n']} has status "
                                f"{attempt.get('status')!r}")
    for issue_id, files in seen.items():
        if len(files) > 1:
            problems.append(f"duplicate id {issue_id}: {', '.join(files)}")
    index = ledger_dir(root) / "INDEX.md"
    if issues or index.exists():
        if not index.exists():
            problems.append("runs/audits/INDEX.md is missing; run issues.py index")
        elif index.read_text() != render_index(root, name, t):
            problems.append("runs/audits/INDEX.md differs from a fresh render; run issues.py index")
    if problems:
        raise LedgerError(*problems)
    return [f"ok: {len(issues)} issues"]


WRITES = {"new", "seen", "check-result", "fix", "wontfix", "stamp", "index"}


# --- arguments ----------------------------------------------------------------------------

class Parser(argparse.ArgumentParser):
    def error(self, message):  # exit 1, not argparse's 2: one exit code for every problem
        self.print_usage(sys.stderr)
        print(f"{self.prog}: {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> Parser:
    common = Parser(add_help=False)
    common.add_argument("--dir", default=argparse.SUPPRESS,
                        help="the plugin directory (default: the working directory)")
    p = Parser(prog="issues.py", description=__doc__.split("\n\n")[0],
               formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default=None, help="the plugin directory (default: the working directory)")
    sub = p.add_subparsers(dest="command", required=True, parser_class=Parser)

    def cmd(name, help_):
        return sub.add_parser(name, parents=[common], help=help_)

    s = cmd("new", "write a new issue file and print its id")
    for flag in ["title", "fault", "severity", "check", "applies-to", "rule-file", "rule-line",
                 "rule-quote", "found-version", "found-session", "found-date", "finding",
                 "unit", "step", "evidence", "report", "finding-id"]:
        s.add_argument(f"--{flag}", required=True)

    s = cmd("candidates", "issues with this rule file and fault, to match a new finding against")
    s.add_argument("--rule-file", required=True)
    s.add_argument("--fault", required=True)
    s.add_argument("--applies-to")

    s = cmd("seen", "append a Found in line")
    s.add_argument("id")
    for flag in ["session", "version", "date", "unit", "step", "evidence", "report", "finding-id"]:
        s.add_argument(f"--{flag}", required=True)

    s = cmd("check-result", "append a Checks line")
    s.add_argument("id")
    s.add_argument("--attempt", type=int, required=True)
    for flag in ["verdict", "session", "version", "date", "evidence"]:
        s.add_argument(f"--{flag}", required=True)
    s.add_argument("--unit")
    s.add_argument("--step")

    s = cmd("fix", "append a fixed attempt")
    s.add_argument("id")
    s.add_argument("--commit")
    for flag in ["branch", "files", "evals", "verify"]:
        s.add_argument(f"--{flag}", required=True)

    s = cmd("wontfix", "append a wontfix attempt")
    s.add_argument("id")
    s.add_argument("--reason", required=True)

    s = cmd("stamp", "set fixed_in on every fixed issue whose commit is in HEAD")
    s.add_argument("--version", required=True)

    s = cmd("list", "one line per issue, filtered")
    s.add_argument("--status")
    s.add_argument("--applies-to")
    s.add_argument("--session")
    s.add_argument("--format", choices=["text", "json"], default="text")

    s = cmd("status", "print an issue's derived status")
    s.add_argument("id")

    cmd("index", "rewrite runs/audits/INDEX.md")
    cmd("check", "check every issue file and the index")
    return p


COMMANDS = {"new": cmd_new, "candidates": cmd_candidates, "seen": cmd_seen,
            "check-result": cmd_check_result, "fix": cmd_fix, "wontfix": cmd_wontfix,
            "stamp": cmd_stamp, "list": cmd_list, "status": cmd_status, "index": cmd_index,
            "check": cmd_check}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.dir or ".").resolve()
    try:
        name = plugin_name(root)
        template = load_template()
        output = COMMANDS[args.command](args, root, name, template)
        if args.command in WRITES:
            write_index(root, name, template)
    except LedgerError as exc:
        for problem in exc.problems:
            print(problem, file=sys.stderr)
        return 1
    for line in output:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
