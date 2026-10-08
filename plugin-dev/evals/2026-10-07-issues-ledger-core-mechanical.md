# issues.py phase 3 — the audit ledger's issue files, derived status, index, stamp and check

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `23b3b69`): `scripts/issues.py`, `templates/audits/issue.md`, `templates/audits/run-report.md` · model: none (a script, checked by script) · 2026-10-07
**Set:** none — M3.1–M3.6 are rows of `site/notes/0.16-audit-ledger-03-ledger-core.md` **Evals** with no set · **Iteration:** none, run in the phase chat (harness kept at `evals/workspace/issues/m3.sh`, gitignored) · **Baseline:** none (new script) · **Pass rate:** M3.1 10/10 · M3.2 7/7 · M3.3 4/4 · M3.4 6/6 · M3.5 5/5 · M3.6 5/5

## What was tested

That `issues.py` writes issue files with exactly the template's frontmatter keys and sections
and ids from the plugin name's prefix; derives `open → fixed → released → verified → recurred`
and `wontfix` as note 03's precedence says; refuses a `held` check with no step and a fix with
no commit or an incomplete Verify; `check` catches a duplicate id and a stale index; `candidates`
and `list` filter as specified; and `stamp`, in a git checkout, stamps only a fix whose commit is
an ancestor of HEAD.

## Method

- One bash harness ran the note's commands as written, with `I = python3 scripts/issues.py
  --dir $L`, `$L` a `mktemp -d` scratch plugin whose `plugin.json` says `"name": "toy"`, and a
  second scratch plugin named `dev-team` for the prefix. Each expectation was a string or
  exit-code comparison; nothing was judged by eye.
- M3.6 used a third scratch dir made a git repo (`git init -b main`): two issues, one fixed with
  a commit on `main`, one with a commit on an unmerged branch `side`, then `stamp` from `main`.
- Beyond the pass bar, by hand: bad `--fault`, a bad `--applies-to` entry and a malformed date
  each give one stderr line and exit 1; `agent:profiler` matches `agent:dev-team:profiler` in
  `candidates`; `--status nope` and `check-result --attempt 4` on a one-attempt issue exit 1; a
  directory with no `plugin.json` exits 1; a `wontfix` attempt holds only `status` and `reason`.
- `grep -E '^(import|from) ' scripts/issues.py`: `__future__`, `argparse`, `json`, `re`,
  `subprocess`, `sys`, `pathlib` — standard library only.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M3.1 ids | two `new` calls print `TO-001`, `TO-002` | exact | ✅ |
| M3.1 files | 13 template keys in order; `## Finding`, `## Found in`, `## Fix`, `## Checks` | exact, both files | ✅ |
| M3.1 status/index | `status TO-001` → `open`; `INDEX.md` two rows, both `open` | exact | ✅ |
| M3.1 prefix | plugin `dev-team` → `DT-001` | `DT-001` | ✅ |
| M3.2 fix | `fix TO-001 …` → `fixed` | `fixed` | ✅ |
| M3.2 stamp | not a git dir: prints `TO-001`; → `released` | exact; `- fixed_in: 0.2.0` | ✅ |
| M3.2 checks | `held` with step → `verified`; then `recurred` → `recurred` | exact | ✅ |
| M3.2 wontfix | `wontfix TO-002 --reason platform` → `wontfix` | exact | ✅ |
| M3.2 order | `INDEX.md` TO-001 (recurred) before TO-002 (wontfix) | exact | ✅ |
| M3.3 | held without `--step`; Verify without `recurred when`; fix without `--commit` — each exits 1 | each exits 1 with one stderr line naming the problem; TO-002 unchanged | ✅ |
| M3.4 clean | `check` → `ok: 2 issues` | exact | ✅ |
| M3.4 duplicate | copy TO-002 to TO-003 → exit 1 naming the duplicate id | exit 1: `duplicate id TO-002: TO-002.md, TO-003.md`, plus the file-name and stale-index lines | ✅ |
| M3.4 index | a character appended to `INDEX.md` → exit 1 naming it; `index` then `check` → 0 | exact | ✅ |
| M3.5 candidates | `agents/x.md` + `agent` → TO-001 with `"Write only under out/"`; `other.md` → `none` | exact | ✅ |
| M3.5 list | `--status recurred,open` → exactly TO-001; `--session 1234abcd` → TO-001; `--format json` parses | exact | ✅ |
| M3.6 | in git: the `main` fix stamped, the `side` fix not, and `stamp` says so | stdout `TO-001`; stderr `not stamped: TO-002 — its commit 38038ea is not an ancestor of HEAD`; TO-001 `released`, TO-002 `fixed`; `check` ok | ✅ |

## Verdict

Held, 37/37. The ledger's formats and every command in note 03's table behave as specified.
Nothing uses them yet: phase 4 makes audit-run write through them.
