#!/usr/bin/env python3
"""A phased plan, read and advanced without a model.

`plan-phases` writes a plan as an overview (`site/notes/<slug>/<slug>-00-overview.md`) and a
ledger (`<slug>-progress.md`); `run-phase` does one phase of it and `run-phases` keeps the
phases going. What those skills need from the two files is a lookup or a check, so it is
this script's: a chat reads its output, never the files whole, and never decides by reading
what a command can decide by exit code. Run from the plugin's own directory. Stdlib only.

  next [slug]         preflight (branch, tree) and the next phase on one line.
                      Exit 0 a phase to run · 1 something stops it · 3 the plan is done
  brief [slug] [--phase N]
                      what the phase's chat reads: its Phases row, its eval rows with the
                      exact `eval_workspace.py init` command for each behavioral one, its
                      ledger row, and the overview's prose without the other phases' rows.
                      Marks the phase as begun (the stop gate reads the mark); --phase N
                      prints another phase's and marks nothing
  finish [slug] --what TEXT [--log FILE]... [--iteration DIR]... [--notes TEXT]
               [--also PATH]... [--skip-row ID]... [--trailer TEXT]... [--no-commit]
                      checks the phase is whole — its note, its logs, every behavioral
                      row's ids laid out in the row's mode in the iterations given and none
                      left not run, contracts — fills its ledger row, resolves earlier
                      `(phase N)` cells to SHAs, stages the plugin and commits
                      `<plugin> <slug> (phase N): <what>`
  check [slug] N      phase N's commit is HEAD, the tree is clean, its row is `done`
  status [slug]       one line per phase; pass counts and tokens for the phases with evals
  touch [slug]        per eval target: the files it is made of, the phases that touch them,
                      the last one, and the checkpoint its evals belong at (edit-list plans)
  plan-check [slug]   the overview's eval rows against the checkpoint rule

Shapes read, all owned by `templates/phases/`: the ledger's table (`Phase | Note | Status |
Commit | Eval log(s) | Notes for the next chat`), the overview's `## Phases` table, every
table under `## Evals by phase` whose header starts `Phase | ID | Kind`, and the overview's
`**Checkpoints:** 4, 9, 12` line, and an optional `**Init flags:** --baseline <ref>` line
whose flags go on every `eval_workspace.py init` command `brief` prints.
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL_WORKSPACE = HERE.parent / "skills" / "run-evals" / "scripts" / "eval_workspace.py"
LEDGER_COLS = ["Phase", "Note", "Status", "Commit", "Eval log(s)", "Notes for the next chat"]
MAX_WAIT = 3        # phases a finished target may wait for its checkpoint before plan-check warns


class Stop(Exception):
    """A reason the command cannot go on; printed, exit 1."""


def sh(*args, cwd):
    return subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True)


def plugin_root():
    p = Path.cwd().resolve()
    for d in [p, *p.parents]:
        if (d / ".claude-plugin" / "plugin.json").is_file():
            return d
    raise Stop("not in a plugin: no .claude-plugin/plugin.json at or above the current directory")


def cells(line, want=None):
    """A table row's cells; an escaped pipe stays inside its cell, as written. When that
    gives the wrong count for the table, a pipe inside a code span is not a separator
    either: `Read|Glob|Grep` in a cell is one cell."""
    parts = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
    if want is None or len(parts) == want:
        return parts
    aware, buf, code = [], "", False
    for i, ch in enumerate(line.strip()):
        code ^= ch == "`"
        if ch == "|" and not code and line.strip()[i - 1:i] != "\\":
            aware.append(buf.strip())
            buf = ""
        else:
            buf += ch
    aware = aware[1:]
    return aware if len(aware) == want else parts


def is_rule(line):
    return bool(re.fullmatch(r"\|[\s:|-]+\|", line.strip()))


class Plan:
    def __init__(self, slug=None):
        self.root = plugin_root()
        self.plugin = json.loads((self.root / ".claude-plugin" / "plugin.json").read_text())["name"]
        notes = self.root / "site" / "notes"
        if slug:
            ledgers = [notes / slug / f"{slug}-progress.md"]
        else:
            ledgers = sorted(notes.glob("*/*-progress.md"))
            if len(ledgers) > 1:        # the one plan still running, when there is one
                open_ = [p for p in ledgers if any(
                    len(c) == len(LEDGER_COLS) and c[0].isdigit() and c[2] != "done"
                    for c in (cells(l, len(LEDGER_COLS)) for l in p.read_text().split("\n")))]
                ledgers = open_ if len(open_) == 1 else ledgers
            if len(ledgers) > 1:
                raise Stop("several plans here, name one: " + ", ".join(p.parent.name for p in ledgers))
        if not ledgers or not ledgers[0].is_file():
            raise Stop("no ledger under site/notes/<slug>/: plan-phases has not run")
        self.ledger = ledgers[0]
        self.dir = self.ledger.parent
        self.slug = self.dir.name
        self.overview = self.dir / f"{self.slug}-00-overview.md"
        self.edits = self.dir / f"{self.slug}-edits.md"
        if not self.overview.is_file():
            raise Stop(f"no overview at {self.overview}")
        self.ledger_lines = self.ledger.read_text().split("\n")
        self.ov_lines = self.overview.read_text().split("\n")
        self.top = Path(sh("git", "rev-parse", "--show-toplevel", cwd=self.root).stdout.strip())
        self.rel = self.root.relative_to(self.top.resolve()).as_posix()

    # ---- the ledger
    def rows(self):
        """[(line index, {column: cell})] of the ledger's table."""
        out, header = [], None
        for i, line in enumerate(self.ledger_lines):
            if not line.lstrip().startswith("|"):
                if header and out:
                    break
                continue
            c = cells(line, len(header) if header else None)
            if header is None:
                if c and c[0] == "Phase":
                    header = c
            elif not is_rule(line) and len(c) == len(header):
                out.append((i, dict(zip(header, c))))
        if header != LEDGER_COLS:
            raise Stop(f"{self.ledger.name}: the table's columns are not {' | '.join(LEDGER_COLS)}")
        return out

    def current(self):
        for i, row in self.rows():
            if row["Status"] != "done":
                return i, row
        return None, None

    def branch(self):
        m = re.search(r"Branch `([^`]+)`", "\n".join(self.ledger_lines[:12]))
        return m.group(1) if m else None

    # ---- the overview
    def section(self, name):
        """(start, end) line indexes of `## <name>`, end exclusive."""
        start = next((i for i, l in enumerate(self.ov_lines)
                      if re.fullmatch(rf"##\s+(\d+\.\s+)?{re.escape(name)}\s*", l)), None)
        if start is None:
            return None
        end = next((i for i in range(start + 1, len(self.ov_lines))
                    if self.ov_lines[i].startswith("## ")), len(self.ov_lines))
        return start, end

    def table_rows(self, name, first_cols):
        """[(line index, {column: cell})] of every table in a section whose header starts
        with first_cols."""
        span = self.section(name)
        out, header = [], None
        if not span:
            return out
        for i in range(*span):
            line = self.ov_lines[i]
            if not line.lstrip().startswith("|"):
                header = None
                continue
            c = cells(line, len(header) if header else None)
            if header is None:
                header = c if c[:len(first_cols)] == first_cols else []
            elif header and not is_rule(line) and len(c) == len(header):
                out.append((i, dict(zip(header, c))))
        return out

    def phase_row(self, n):
        for _, r in self.table_rows("Phases", ["Phase", "Note"]):
            if r["Phase"] == str(n):
                return r
        return None

    def eval_rows(self, n=None):
        """Eval rows, each with `phases` (a recurring row names a range such as 1–37)."""
        out = []
        for i, r in self.table_rows("Evals by phase", ["Phase", "ID", "Kind"]):
            m = re.fullmatch(r"(\d+)(?:\s*[–-]\s*(\d+))?", r["Phase"])
            if not m:
                continue
            lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
            r = dict(r, phases=range(lo, hi + 1), line=i, recurring=hi != lo)
            if n is None or n in r["phases"]:
                out.append(r)
        return out

    def checkpoints(self):
        for line in self.ov_lines:
            m = re.match(r"\*\*Checkpoints:\*\*\s*(.+)", line.strip())
            if m:
                return sorted({int(x) for x in re.findall(r"\d+", m.group(1).split(".")[0])})
        return []

    def init_flags(self):
        for line in self.ov_lines:
            m = re.match(r"\*\*Init flags:\*\*\s*(.+)", line.strip())
            if m:
                return m.group(1).strip().strip("`").split()
        return []

    def prefix(self, n):
        return f"{self.plugin} {self.slug} (phase {n}):"

    def marker(self):
        return self.root / "evals" / "workspace" / "run-phases" / self.slug / "active.json"


def target_of(row):
    return set_evals(row)[0] or row["Target"].strip("` ")


def set_evals(row):
    """(set name, eval ids) from a row's Set evals cell: `evals/sets/x.json` 1, 4–6."""
    m = re.search(r"evals/sets/([\w.-]+)\.json`?\s*(.*)", row.get("Set evals", ""))
    if not m:
        return None, []
    ids = []
    for part in re.split(r"[,;]", m.group(2)):
        r = re.fullmatch(r"\s*(\d+)(?:\s*[–-]\s*(\d+))?\s*", part)
        if r:
            ids += range(int(r.group(1)), int(r.group(2) or r.group(1)) + 1)
    return m.group(1), sorted(set(ids))


def compared(row):
    """A row whose baseline runs beside the working tree; `working tree only` starts none."""
    return "working tree only" not in row["Baseline"].lower()


def init_command(plan, row):
    """The one `init` command that lays out a behavioral row's runs, flags and ids exact."""
    name, ids = set_evals(row)
    if not name or not ids:
        return None
    cmd = ["python3", str(EVAL_WORKSPACE), "init", ".", name, "--quiet",
           "--evals", ",".join(map(str, ids))]
    base = row["Baseline"].strip("` ")
    flags = plan.init_flags()
    if not compared(row):
        cmd.append("--working-tree-only")
    elif base not in ("none", "previous") and "--baseline" not in flags:
        cmd += ["--baseline", base]
    return " ".join(cmd + flags)


def dirty(plan):
    """Changed paths, repo-relative, from `git status --porcelain`."""
    out = sh("git", "status", "--porcelain", cwd=plan.top).stdout.splitlines()
    return [l[3:].split(" -> ")[-1].strip('"') for l in out if l.strip()]


# ---------------------------------------------------------------- next

def cmd_next(args):
    plan = Plan(args.slug)
    want, have = plan.branch(), sh("git", "branch", "--show-current", cwd=plan.root).stdout.strip()
    if want and have != want:
        raise Stop(f"on branch `{have}`, the ledger names `{want}`: switch branches yourself, then rerun")
    rows = plan.rows()
    _, row = plan.current()
    if row is None:
        print(f"plan done: {len(rows)} of {len(rows)} phases")
        return 3
    changed = dirty(plan)
    if changed:
        stray = [p for p in changed if row["Status"] != "in progress"
                 or p.split("/")[-1] not in row["Notes for the next chat"]]
        if stray:
            raise Stop("the tree is not clean and the ledger's row does not name these paths:\n  "
                       + "\n  ".join(stray))
    n = int(row["Phase"])
    done = sum(1 for _, r in rows if r["Status"] == "done")
    note = (plan.phase_row(n) or {}).get("Note", row["Note"])
    print(f"phase {n} · {note} · {row['Status']} · "
          f"{'checkpoint' if n in plan.checkpoints() else 'no behavioral evals'} · "
          f"{done} of {len(rows)} done")
    return 0


# ---------------------------------------------------------------- brief

def cmd_brief(args):
    plan = Plan(args.slug)
    _, row = plan.current()
    if args.phase is not None:      # a look at another phase: nothing is marked as begun
        row = next((r for _, r in plan.rows() if r["Phase"] == str(args.phase)), None)
        if row is None:
            raise Stop(f"the ledger has no phase {args.phase}")
    if row is None:
        print("plan done")
        return 3
    n = int(row["Phase"])
    ph = plan.phase_row(n) or {}
    out = [f"# {plan.plugin} {plan.slug} — phase {n}: {ph.get('Note', row['Note'])}", "",
           f"Branch `{plan.branch()}`. Commit through `phases.py finish`, which writes "
           f"`{plan.prefix(n)} <what>`.",
           f"Note file: `site/notes/{plan.slug}/{plan.slug}-{ph.get('Note', row['Note'])}.md`"
           f"{'' if n else ' (phase 0: the overview is its note)'}.", "",
           "## This phase, from the overview's Phases table", ""]
    out += [f"- **{k}:** {v}" for k, v in ph.items() if k not in ("Phase", "Note") and v]
    rows = plan.eval_rows(n)
    out += ["", "## Its eval rows", "",
            "| ID | Kind | Target | Baseline | Set evals | Pass bar |", "|---|---|---|---|---|---|"]
    out += [f"| {r['ID']} | {r['Kind']} | {r['Target']} | {r['Baseline']} | {r['Set evals']} | {r['Pass bar']} |"
            for r in rows]
    cps = plan.checkpoints()
    behavioral = [r for r in rows if r["Kind"] == "behavioral"]
    commands = [(r["ID"], init_command(plan, r)) for r in behavioral]
    if commands:
        out += ["", "Run each behavioral row with exactly this command, then start "
                f"`python3 {EVAL_WORKSPACE} run <the iteration it prints>` for every one of them, "
                "in the background, in one message. `finish` checks each row's ids and mode "
                "against the iterations it is given.", ""]
        out += [f"- {rid}: `{cmd}`" if cmd else f"- {rid}: its Set evals cell names no set and ids; "
                "lay it out by hand and say so under Deviations" for rid, cmd in commands]
    out += ["", f"Checkpoints of this plan: {', '.join(map(str, cps)) or 'none named'}. This phase is "
            + ("one: its behavioral rows run here." if n in cps else
               "not one" + (", yet it has behavioral rows: run them and say so in the note."
                            if behavioral else ": mechanical rows only.")),
            "", "## Its ledger row", "", f"- **Status:** {row['Status']}",
            f"- **Notes for this chat:** {row['Notes for the next chat'] or '—'}"]
    # The overview's prose, without the rows of other phases: the two big tables are what
    # make it long, and this phase's rows are above.
    for name in ("Phases", "Evals by phase"):
        span = plan.section(name)
        if span:
            prose = [l for l in plan.ov_lines[span[0] + 1:span[1]] if not l.lstrip().startswith("|")]
            out += ["", f"## The overview's {name}: its conventions", ""] + \
                   [l for i, l in enumerate(prose) if l.strip() or (i and prose[i - 1].strip())]
    rest = []
    for i, line in enumerate(plan.ov_lines):
        m = re.fullmatch(r"##\s+(.+?)\s*", line)
        if m and m.group(1) not in ("Phases", "Evals by phase"):
            a, b = plan.section(m.group(1)) or (i, i)
            rest.append(f"- {m.group(1)}: `sed -n '{a + 1},{b}p' site/notes/{plan.slug}/{plan.overview.name}`")
    out += ["", "## The rest of the overview, read only as a step needs it", ""] + rest
    print("\n".join(out))
    if args.phase is not None:
        return 0
    head = sh("git", "rev-parse", "HEAD", cwd=plan.root).stdout.strip()
    plan.marker().parent.mkdir(parents=True, exist_ok=True)
    plan.marker().write_text(json.dumps({"phase": n, "head": head}) + "\n")
    return 0


# ---------------------------------------------------------------- finish

def coverage(iterations):
    """{set name: {eval id: {configurations laid out}}} from the iterations' manifests."""
    out = {}
    for it in iterations:
        try:
            m = json.loads((Path(it) / "manifest.json").read_text())
        except (OSError, ValueError):
            continue
        name = m.get("target") or Path(it).parent.name
        for r in m.get("runs", []):
            out.setdefault(name, {}).setdefault(r.get("eval_id"), set()).add(r.get("config"))
    return out


def unfinished_runs(iteration):
    return sorted(str(p.parent.relative_to(iteration)) for name in ("not-run.json", "not-graded.json")
                  for p in Path(iteration).glob(f"eval-*/*/run-*/{name}"))


def resolve_shas(plan, rows):
    """`(phase k)` in a done row's Commit cell → the short SHA of that phase's newest commit."""
    for i, row in rows:
        m = re.fullmatch(r"\(phase (\d+)\)", row["Commit"])
        if row["Status"] == "done" and m:
            sha = sh("git", "log", "--format=%h", "-1", "-F", f"--grep=(phase {m.group(1)}):",
                     cwd=plan.root).stdout.strip()
            if sha:
                row["Commit"] = sha
                plan.ledger_lines[i] = "| " + " | ".join(row[c] for c in LEDGER_COLS) + " |"


def cmd_finish(args):
    plan = Plan(args.slug)
    i, row = plan.current()
    if row is None:
        raise Stop("every phase is done")
    n = int(row["Phase"])
    ph = plan.phase_row(n) or {}
    problems = []
    note = plan.dir / f"{plan.slug}-{ph.get('Note', row['Note'])}.md"
    if n and not note.is_file():
        problems.append(f"no phase note at {note.relative_to(plan.root)}")
    index = (plan.root / "evals" / "README.md")
    index = index.read_text() if index.is_file() else ""
    logs = []
    for log in args.log:
        p = (plan.root / log) if not Path(log).is_absolute() else Path(log)
        if not p.is_file():
            problems.append(f"no eval log at {log}")
        elif p.name not in index:
            problems.append(f"evals/README.md has no row for {p.name}")
        logs.append(p.name)
    iterations, dirs = [], []
    for it in args.iteration:
        p = (plan.root / it).resolve()
        if not (p / "report.md").is_file():
            problems.append(f"{it}: no report.md — `eval_workspace.py run` has not finished there")
        for run in unfinished_runs(p):
            problems.append(f"{it}: {run} was not run or not graded")
        iterations.append(p.relative_to(plan.root).as_posix() if plan.root in p.parents else str(p))
        dirs.append(p)
    ran = coverage(dirs)
    for r in plan.eval_rows(n):
        if r["Kind"] == "behavioral" and not r["recurring"] and r["ID"] not in args.skip_row:
            name, ids = set_evals(r)
            if not any(f"/workspace/{target_of(r)}/" in f"/{x}/" for x in iterations):
                problems.append(f"row {r['ID']} ({target_of(r)}) has no --iteration; run it, or "
                                f"--skip-row {r['ID']} and say why under Deviations")
                continue
            # The row's ids, each laid out in the mode the row names. A working tree only row
            # run compared is more than was asked and stands; the other way round does not.
            got = ran.get(name, {})
            missing = [i for i in ids if "with_skill" not in got.get(i, ())]
            one_sided = [i for i in ids if i not in missing and compared(r) and got[i] == {"with_skill"}]
            if missing:
                problems.append(f"row {r['ID']}: {name} eval(s) {missing} are in none of its "
                                f"iterations: {init_command(plan, r)}")
            if one_sided:
                problems.append(f"row {r['ID']}: {name} eval(s) {one_sided} ran working tree only "
                                f"and the row runs them compared: {init_command(plan, r)}")
    if (plan.root / "contracts.yml").is_file():
        sweep = sh(sys.executable, HERE / "contract_sweep.py", cwd=plan.root)
        if sweep.returncode != 0:
            fails = [l for l in sweep.stdout.splitlines() if l.startswith("FAIL")]
            problems += [f"check-contracts: {l}" for l in fails] or ["check-contracts failed"]
    also = {Path(a).as_posix().strip("/") for a in args.also}
    outside = [p for p in dirty(plan)
               if not (p == plan.rel or p.startswith(plan.rel + "/") or plan.rel == ".")
               and not any(p == a or p.startswith(a + "/") for a in also)]
    if outside:
        problems.append("changed outside the plugin and not named with --also: " + ", ".join(outside))
    if problems:
        raise Stop(f"phase {n} is not whole:\n  " + "\n  ".join(problems))

    rows = plan.rows()
    resolve_shas(plan, rows)
    skipped = f" Not run: {', '.join(args.skip_row)} (see the note's Deviations)." if args.skip_row else ""
    row.update({"Status": "done", "Commit": f"(phase {n})",
                "Eval log(s)": " · ".join([f"`{x}`" for x in logs + iterations]),
                "Notes for the next chat": (args.notes or "").replace("\n", " ").strip() + skipped})
    plan.ledger_lines[i] = "| " + " | ".join(row[c] for c in LEDGER_COLS) + " |"
    plan.ledger.write_text("\n".join(plan.ledger_lines))
    plan.marker().unlink(missing_ok=True)

    subject = f"{plan.prefix(n)} {args.what.strip()}"
    add = sh("git", "add", "--", plan.rel, *sorted(also), cwd=plan.top)
    if add.returncode != 0:
        raise Stop(f"git add failed: {add.stderr.strip()}")
    if args.no_commit:
        print(f"staged; commit with the subject:\n{subject}")
        return 0
    message = ["-m", subject] + (["-m", "\n".join(args.trailer)] if args.trailer else [])
    commit = sh("git", "commit", "-q", *message, cwd=plan.top)
    if commit.returncode != 0:
        raise Stop(f"git commit failed: {(commit.stderr or commit.stdout).strip()}")
    sha = sh("git", "log", "-1", "--format=%h", cwd=plan.root).stdout.strip()
    print(f"phase {n} committed: {sha} — {subject}")
    _, nxt = Plan(plan.slug).current()
    print(f"next: phase {nxt['Phase']} ({nxt['Note']})" if nxt else "next: none — the plan is done")
    return 0


# ---------------------------------------------------------------- check

def check(plan, n):
    """Why phase n does not stand as committed; empty when it does."""
    problems = []
    subject = sh("git", "log", "-1", "--format=%s", cwd=plan.root).stdout.strip()
    if not subject.startswith(plan.prefix(n)):
        problems.append(f"HEAD is `{subject}`, not a commit starting `{plan.prefix(n)}`")
    changed = dirty(plan)
    if changed:
        problems.append("the tree is not clean: " + ", ".join(changed[:8]))
    row = next((r for _, r in plan.rows() if r["Phase"] == str(n)), None)
    if row is None:
        problems.append(f"the ledger has no phase {n}")
    elif row["Status"] != "done":
        problems.append(f"the ledger's phase {n} is `{row['Status']}`, not `done`")
    return problems


def cmd_check(args):
    plan = Plan(args.slug)
    problems = check(plan, args.phase)
    if problems:
        raise Stop(f"phase {args.phase} does not stand:\n  " + "\n  ".join(problems))
    sha = sh("git", "log", "-1", "--format=%h — %s", cwd=plan.root).stdout.strip()
    print(f"phase {args.phase} committed: {sha}")
    return 0


# ---------------------------------------------------------------- status

def iteration_stats(it):
    """(passed, total, tokens) of an iteration: the working tree's grades, every session's tokens."""
    passed = total = tokens = 0
    for g in Path(it).glob("eval-*/with_skill/run-*/grading.json"):
        try:
            s = json.loads(g.read_text()).get("summary", {})
            passed, total = passed + int(s.get("passed", 0)), total + int(s.get("total", 0))
        except (ValueError, OSError):
            pass
    for name in ("timing.json", "grader-timing.json"):
        for t in Path(it).glob(f"eval-*/*/run-*/{name}"):
            try:
                tokens += int(json.loads(t.read_text()).get("total_tokens") or 0)
            except (ValueError, OSError):
                pass
    return passed, total, tokens


def cmd_status(args):
    plan = Plan(args.slug)
    cps, rows = plan.checkpoints(), plan.rows()
    all_tokens = 0
    for _, r in rows:
        line = f"{r['Phase']:>3}  {r['Status']:<11} {r['Commit'] or '—':<10} {r['Note']}"
        if int(r["Phase"]) in cps:
            line += "  [checkpoint]"
        its = re.findall(r"evals/workspace/[\w.-]+/iteration-\d+", r["Eval log(s)"])
        stats = [iteration_stats(plan.root / it) for it in dict.fromkeys(its) if (plan.root / it).is_dir()]
        if stats and sum(s[1] for s in stats):
            tokens = sum(s[2] for s in stats)
            all_tokens += tokens
            line += f"  evals {sum(s[0] for s in stats)}/{sum(s[1] for s in stats)}, {tokens / 1e6:.1f}M tokens"
        print(line)
    done = sum(1 for _, r in rows if r["Status"] == "done")
    print(f"{done} of {len(rows)} phases done"
          + (f"; evals so far {all_tokens / 1e6:.1f}M tokens" if all_tokens else ""))
    return 0


# ---------------------------------------------------------------- touch, plan-check

def made_of(root, target_path, depends_on=()):
    """The path prefixes a target is made of: its own file or directory, the skills an agent
    preloads, and whatever its set lists under `depends_on`."""
    parts = Path(target_path).parts
    out = [target_path]
    if parts[0] == "skills" and len(parts) > 2:
        out = [f"skills/{parts[1]}/"]
    elif parts[0] == "hooks":
        out = ["hooks/"]
    elif parts[0] == "agents" and (root / target_path).is_file():
        fm = re.match(r"---\n(.*?)\n---", (root / target_path).read_text(), re.S)
        m = re.search(r"^skills:[ \t]*(\[.*?\]|(?:\n[ \t]+-[^\n]+)+)", fm.group(1) if fm else "", re.M)
        for name in re.findall(r"[A-Za-z][\w:-]*", m.group(1) if m else ""):
            out.append(f"skills/{name.split(':')[-1]}/")
    return out + [str(d) for d in depends_on]


def touches(plan):
    """{target: {"files": [...], "phases": [...]}} from the edit list and the Phases table."""
    if not plan.edits.is_file():
        return None
    spec = importlib.util.spec_from_file_location("edits", HERE / "edits.py")
    edits = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edits)
    _, items, _ = edits.load_edits(str(plan.edits))
    files = {it["id"]: [p.strip() for p in edits.paths_of(it["fields"].get("files", "")).split(",") if p.strip()]
             for it in items}
    by_phase, _, _ = edits.phase_items(str(plan.overview))
    phase_files = {int(ph): {f for i in edits.expand(cell, list(files)) for f in files.get(i, [])}
                   for ph, cell in by_phase.items() if ph.isdigit()}
    out = {}
    for s in sorted((plan.root / "evals" / "sets").glob("*.json")):
        if s.name.endswith(".trigger.json"):
            continue
        data = json.loads(s.read_text())
        prefixes = made_of(plan.root, data.get("target_path", ""), data.get("depends_on", ()))
        hit = sorted(ph for ph, fs in phase_files.items()
                     if any(f == p or (p.endswith("/") and f.startswith(p)) for f in fs for p in prefixes))
        out[data["target"]] = {"files": prefixes, "phases": hit}
    return out


def checkpoint_for(phase, cps):
    return next((c for c in cps if c >= phase), None)


def cmd_touch(args):
    plan = Plan(args.slug)
    t = touches(plan)
    if t is None:
        raise Stop(f"no edit list at {plan.edits.name}: touch needs each item's files")
    cps = plan.checkpoints()
    _, row = plan.current()
    start = int(row["Phase"]) if row and args.remaining else 0
    for target, d in t.items():
        phases = [p for p in d["phases"] if p >= start]
        last = phases[-1] if phases else None
        at = checkpoint_for(last, cps) if last is not None else None
        print(f"{target}\tlast touched: {last if last is not None else '—'}\t"
              f"evals at: {at if at is not None else '—'}\t"
              f"touched in: {', '.join(map(str, phases)) or '—'}\t{', '.join(d['files'])}")
    return 0


def cmd_plan_check(args):
    plan = Plan(args.slug)
    cps = plan.checkpoints()
    phases = [int(r["Phase"]) for _, r in plan.table_rows("Phases", ["Phase", "Note"]) if r["Phase"].isdigit()]
    _, row = plan.current()
    start = int(row["Phase"]) if row and args.remaining else 0
    problems, warnings = [], []
    if not cps:
        problems.append("the overview names no checkpoints: add `**Checkpoints:** <phases>` under Evals by phase")
    elif phases and cps[-1] != max(phases):
        problems.append(f"the last phase ({max(phases)}) is not a checkpoint")
    t = touches(plan)
    behavioral = [r for r in plan.eval_rows() if r["Kind"] == "behavioral" and not r["recurring"]
                  and r["phases"][0] >= start]
    for r in behavioral:
        n, target = r["phases"][0], target_of(r)
        if cps and n not in cps:
            problems.append(f"row {r['ID']}: a behavioral row in phase {n}, which is not a checkpoint")
        later = [p for p in (t or {}).get(target, {}).get("phases", []) if p > n]
        if later:   # an item's `files:` also lists lines it only cites, so this is a question
            warnings.append(f"row {r['ID']}: the edit list has {target} touched again in phase "
                            f"{later[-1]}; if that phase edits it, its evals belong at checkpoint "
                            f"{checkpoint_for(later[-1], cps)}")
    if t is not None:
        rowed = {target_of(r) for r in behavioral}
        for target, d in t.items():
            ph = [p for p in d["phases"] if p >= start]
            if not ph:
                continue
            at = checkpoint_for(ph[-1], cps)
            if target not in rowed:
                warnings.append(f"{target} is touched in {', '.join(map(str, ph))} and has no behavioral row")
            elif at is not None and at - ph[-1] > MAX_WAIT:
                warnings.append(f"{target} is last touched in phase {ph[-1]} and waits until {at} "
                                f"(more than {MAX_WAIT} phases)")
    for w in warnings:
        print(f"warning: {w}")
    for p in problems:
        print(f"FAIL {p}")
    print(f"{'ok' if not problems else 'not ok'}: {len(behavioral)} behavioral rows, "
          f"checkpoints {', '.join(map(str, cps)) or 'none'}"
          + ("" if t is not None else "; no edit list, so last-touch placement was not checked"))
    return 1 if problems else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("next", cmd_next), ("brief", cmd_brief), ("status", cmd_status),
                     ("touch", cmd_touch), ("plan-check", cmd_plan_check)):
        p = sub.add_parser(name)
        p.add_argument("slug", nargs="?")
        if name == "brief":
            p.add_argument("--phase", type=int, help="print another phase's brief; marks nothing")
        if name in ("touch", "plan-check"):
            p.add_argument("--remaining", action="store_true",
                           help="only the phases from the next unfinished one on")
        p.set_defaults(fn=fn)
    p = sub.add_parser("check")
    p.add_argument("args", nargs="+", metavar="[slug] N")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("finish")
    p.add_argument("slug", nargs="?")
    p.add_argument("--what", required=True)
    for flag in ("--log", "--iteration", "--also", "--skip-row", "--trailer"):
        p.add_argument(flag, action="append", default=[])
    p.add_argument("--notes", default="")
    p.add_argument("--no-commit", action="store_true")
    p.set_defaults(fn=cmd_finish)
    args = ap.parse_args(argv)
    if args.cmd == "check":
        if len(args.args) > 2 or not args.args[-1].isdigit():
            ap.error("check [slug] N")
        args.slug, args.phase = (args.args[0] if len(args.args) == 2 else None), int(args.args[-1])
    try:
        return args.fn(args)
    except Stop as e:
        print(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
