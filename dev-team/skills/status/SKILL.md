---
name: status
description: Print where every package and section stands — one state per section (PROBE, DESIGN, TEST, IMPLEMENT, REVIEW, FIX n, PLAN, DONE, BLOCKED), the ready set, whether the package shipped, and the exact next command — derived from docs/ and the code every time, never from a status file. Use whenever you have lost track, before planning the next package, or to see why run-package stopped.
argument-hint: "[pkg] [--run-gate [pkg]] [--rounds <pkg>/<section>] [--surface <pkg>] [--repo] [--inputs <pkg>/<section>] [--scaffold <pkg>]"
disable-model-invocation: true
---

Run the status script from the repo root and show its output verbatim:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/status.py $ARGUMENTS
```

Then, in two or three lines, say what the `next:` line means: which section it runs, or which
decision it waits on, and why that one — the evidence column of the row it comes from. Do
nothing else — no edits, no fixes, no command run on the user's behalf.

With no flag, the script prints one block per package in `docs/architecture.md`'s Packages
table (with a package name, only that one): a `section · state · evidence · ready · round ·
open spec-change · last commit` row per row of the contract's Sections table, then `shipped:
yes` or `shipped: no (surface <STATE>)`, then `next: <exact command>`. Each state is the first
of the nine rules in the script's docstring that fires, and the evidence names the file or
commit it fired on. "Newer than" is commit order, never file times; a path with uncommitted
changes counts as newest of all and says so in the evidence. A section is ready when it is
neither DONE nor BLOCKED and every section it depends on in its package is DONE; the `surface`
section depends on all of them. Nothing is counted from `docs/followups.md`.

`--run-gate [pkg]` prints `run gate: PASS` or `run gate: FAIL` with one reason per line and
exits 1 on FAIL: not a git repository; on `main` or `master`; uncommitted changes outside the
user-edited files (`docs/decisions.md`, `docs/brief.md`, `docs/constraints.md`,
`.claude/agent-memory/`); and, with a package, no `docs/packages/<pkg>/contract.md`. It is the
check a run makes once, before its first agent.

`--rounds <pkg>/<section>` prints `rounds: <n>` — the newest review round, from the
`-r<n>-` in the report filenames, 0 with none — and `next round: <n+1>`. Nothing else runs; the
reviewer names its report from it.

`--surface <pkg>` prints `surface: PASS` or `surface: FAIL` with reasons: every name must be in
all three of `__all__` in the package's `__init__.py`, the **Public names** table of
`docs/packages/<pkg>/interface.md`, and the `Public: yes` rows of the section READMEs' **Entry
points and interfaces** tables; and `import <pkg>` must load no section module. Before
`interface.md` exists it prints `surface: n/a (no interface.md)` and exits 0.

`--repo` prints the repo-wide gap list the documenter copies under **Known gaps**: `packages:`,
`sections:` (every section not DONE), `decisions:` (every `D<n>` open or deferred),
`spec-changes:`, `changes:` (open change files) and `backlog:` (unchecked `docs/followups.md`
lines per target), each item on a `  - ` line, `  - none` for an empty group.

`--scaffold <pkg>` prints `scaffold: done` (exit 0) or `scaffold: needed (<reasons>)` (exit 1):
no root `pyproject.toml`, or a uv workspace root with no `pyproject.toml` at the package root.
A root that is not a uv workspace is an adopted repo's own layout and needs nothing. The
package block shows the same `scaffold: needed` line, before `shipped:`. run-package's SCAFFOLD
step reads it.

`--inputs <pkg>/<section>` prints the implementer's spawn block — twelve `<Field>: <value>`
lines, `none` where a field has nothing to hold — resolved from the contract, the Packages
table, the review reports and the open change files. `/dev-team:run-package` sends it verbatim
to the implementer, and `/dev-team:pair` reads the files it names. The script's docstring lists
the fields and how each resolves. A section the contract lacks prints one line and exits 2.

The script runs no test and no constraint command. The stop hook runs `docs/constraints.md`'s
**Floor** and **Enforced** rows through the same parser this script exposes, so the rows the
hook runs and the rows this script reads are one list.
