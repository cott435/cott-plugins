---
name: status
description: Print where every package and section stands — one state per section (PROBE, DESIGN, TEST, IMPLEMENT, REVIEW, FIX n, PLAN, DONE, BLOCKED), the ready set, whether the package shipped, and the exact next command — derived from docs/ and the code every time, never from a status file. Use whenever you have lost track, before planning the next package, or to see why run-package stopped.
argument-hint: "[pkg] [--run-gate [pkg]] [--rounds <pkg>/<section>|<pkg>/paths] [--surface <pkg>] [--shape <pkg> --section <s>] [--paths <pkg> [--against-contract]] [--repo] [--inputs <pkg>/<section>] [--fields <pkg>/<section>] [--scaffold <pkg>] [--profile <pkg>/<section> [--defer]]"
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
open spec-change · last commit` row per row of the contract's Sections table, then `scaffold:
needed (<reasons>)` when it applies, then `paths: needed`, `paths: round <n> (request changes:
<sections>)` (ending ` (cap)` from round 3) or `paths: approved (<report>)` once every section
is DONE or a paths report exists, then `shipped: yes` or `shipped: no (<why>)`, then `next:
<exact command>`. Each state is the first
of the nine rules in the script's docstring that fires, and the evidence names the file or
commit it fired on. "Newer than" is commit order, never file times; a path with uncommitted
changes counts as newest of all and says so in the evidence. A section is ready when it is
neither DONE nor BLOCKED and every section it depends on in its package is DONE; the `surface`
section depends on all of them; the `surface` row is ready at PLAN, DESIGN and TEST as soon as
the contract has **Call paths**, and waits for every other section from IMPLEMENT on. Nothing is counted from `docs/followups.md`.

`--run-gate [pkg]` prints `run gate: PASS` or `run gate: FAIL` with one reason per line and
exits 1 on FAIL: not a git repository; on `main` or `master`; uncommitted changes outside the
user-edited files (`docs/decisions.md`, `docs/brief.md`, `docs/constraints.md`,
`.claude/agent-memory/`); an inbox `docs/packages/<pkg>/decisions/<section>.md` holding a
`D?` stub, a `D<n>` or an `Applied:` line that `docs/decisions.md` does not (the sync hook did
not run; `python3 <plugin>/hooks/sync_decisions.py --all` repairs it), or a central
`Applied: <pkg>/<section>, …` line that section's inbox entry no longer holds (`stale Applied:
line`, the same repair); and, with a package, no
`docs/packages/<pkg>/contract.md`, or a `stage:` row whose `depends on` is empty (nothing
produces its data). It is the
check a run makes once, before its first agent.

`--rounds <pkg>/<section>` prints `rounds: <n>` — the newest review round, from the
`-r<n>-` in the report filenames, 0 with none — `next round: <n+1>`, and `commit: <short sha>`
— the newest commit touching the section's code, unit tests, intent tests and README, or
`none`; the reviewer copies it as its report's `Commit:`. Nothing else runs; the reviewer names
its report from it. `--rounds <pkg>/paths` prints the same three lines for the package's paths
reports, `commit:` the newest commit touching any section's code, then `previous:` and `diff
base:` — the newest paths report's path and its `Commit:`, each `none` without one.

`--surface <pkg>` prints `surface: PASS` or `surface: FAIL` with reasons: every name must be in
all three of `__all__` in the package's `__init__.py`, the **Public names** table of
`docs/packages/<pkg>/interface.md`, and the `Public: yes` rows of the section READMEs' **Entry
points and interfaces** tables — except a name whose providing module lies outside every other
section (a pipeline, the CLI), which is the `surface` section's own and has no section README
row; a name cell is read as its first backticked span (`` `Trade` (`models.py`) `` is `Trade`); and `import <pkg>` must load no section module. Before
`interface.md` exists it prints `surface: n/a (no interface.md)` and exits 0.

`--shape <pkg> --section <s>` prints the section's shape check, the lines the stop gate copies
into its record. `FAIL shape: <file>:<line> trivial-helper <name>` is a private helper with one
call site in the package and three statements or fewer; `FAIL shape: <file>:<line> options-bag
<name>` is a signature taking `**name: Unpack[...]`. Both are judged only on lines added since
the section's last review (for an adopted section not yet reviewed, since its `Mode: document`
design was committed). `MEASURED shape indirect: <n>` counts the section's lambdas and closures
passed as arguments and its calls through a mapping, and `MEASURED shape depth <entry point>:
<n>` gives the deepest path from each README entry point to a call that leaves the package;
neither fails. `PASS shape <pkg>/<s>` follows when nothing failed. Exit 1 on a FAIL line.

`--paths <pkg>` prints one call tree per `[project.scripts]` command of the package, followed
statically through the package's own code: a frame per line, `[indirect]` on a frame reached
through a lambda, a closure or a mapping, `[effect: <callee>]` on a call that leaves the
package for a third-party module or for I/O, `[unresolved]` on a call the script could not
follow, then `depth to first effect`, `deepest effect` and `indirect frames`. The paths
reviewer reads it. With no commands it prints `paths: no commands`. With `--against-contract`
each block is followed by the contract's **Call paths** entry for the command: `contract:
<command> (budget <n>)`, then per path its kind, each contract frame `match` (with the built
frame) or `missing`, each built frame between two matched ones `extra`, the effect `reached`,
`reached through <k> extra frame(s)` or `not reached`, and a `summary: <k> match, <e> extra,
<m> missing; depth <d> of budget <n>` line (`past budget` when deeper). A contract with no
entry for the command prints `contract: no entry for <command>`, one with no heading
`contract: no Call paths heading`, and the block ends there. `--against-contract` without
`--paths` exits 2. An open change file naming the package that gives an entry for the command
under **Contract changes** is compared in the contract's place (its `to` entry, after a
`from`), and the first line reads `contract: <command> (budget <n>) from <change file path>`:
code built to a change is judged against the change until `sync-plan` writes it into the
contract.

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
table, and the review reports and open change files at either location. `/dev-team:run-package` sends it verbatim
to the implementer, and `/dev-team:pair` reads the files it names. The script's docstring lists
the fields and how each resolves. A section the contract lacks prints one line and exits 2.

`--fields <pkg>/<section>` prints the other spawn fields run-package would otherwise read files
for, seven lines: `mode: new | document | delta` (the designer's **Mode**), `change file: <path>
| none`, `design mode: <word> | none` (the tester's **Design mode**, from the design's `Mode:`
line), `diff base: <sha> | none` (the `Commit:` a round-2-or-later reviewer's **Diff**
starts from), `upstream interfaces: <path>, … | none`, `paths report: <path> | none` (the
package's paths report while it names the section and no review of the section is newer, the
`full` reviewer's **Previous round** after a paths FIX) and `dependency readmes: <path>/README.md, … |
none` (the dependency READMEs that exist on disk — every role's **Dependency READMEs**; `none`
for the `surface` section before its siblings ship). The docstring gives each rule. A section the contract lacks exits 2.

`--profile <pkg>/<section>` prints the profiler's spawn block for a row whose `source` names a
`stage:<token>` — fifteen `<Field>: <value>` lines per stage, from `Mode:` (`profile`,
`verify` or `defer`) to `Run:`, blocks separated by a blank line. Such a row is PROBE until the newest
round line under `## <pkg>/<section>` in its profile `docs/sources/<token>.md` is neither
`pending verify` nor `revise: …`, and PROBE again once its reviewers approve it while that
line's commit is `none` or older than the section's code: a round over the built section, at
the newest round plus one with `Commit:` the section's commit. With nothing due it prints the
next `profile` block, the hand re-profile `--step PROBE` sends: round 0 before the section has
a README, else the newest round plus one. `/dev-team:run-package` sends it verbatim to the
profiler. When a round 2 or later closes `new kinds: …` while the profiler's
`spec-change:design` entry is open, the row is BLOCKED at the profile cap; `--profile
<pkg>/<section> --defer` then prints the `Mode: defer` block for that round and its commit, and
nothing defers without the flag. A row with no stage prints `profile: no stage source in
<pkg>/<section>`; a section the contract lacks exits 2.

The script runs no test and no constraint command. The stop hook runs `docs/constraints.md`'s
**Floor** and **Enforced** rows through the same parser this script exposes, so the rows the
hook runs and the rows this script reads are one list.
