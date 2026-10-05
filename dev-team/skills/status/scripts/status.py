#!/usr/bin/env python3
"""Derive where every package and section stands from docs/ and the code. Nothing is stored.

Usage:  python3 status.py [pkg] [--run-gate [pkg]] [--rounds <pkg>/<section>|<pkg>/paths] [--surface <pkg> [--section <s>]] [--repo]
                          [--inputs <pkg>/<section>] [--fields <pkg>/<section>] [--scaffold <pkg>]
                          [--profile <pkg>/<section> [--defer]]
                          [--shape <pkg> --section <s>] [--paths <pkg> [--against-contract]]

A section is in exactly one state, decided in this order, first match wins:

1. **BLOCKED** — an open decision with no assumption binds the section (`docs/decisions.md`
   entry with `Status: open`, no `Assumption if unanswered:`, `Scope:` covering `repo`, the
   package or the section); or the newest review round says `request changes` and the cap is
   hit: round 3 or later, or round 2 whose `Convergence:` line has one or more prior unfixed;
   or the section has a README, no review round covers its code, and the stop gate's record
   for its current commit ends `result: blocked` or `result: letting the run stop after 3
   attempts …`; or a `stage:` source's newest round line, at round 2 or later, ends `new
   kinds: …` and a `spec-change:design` entry raised by the profiler is open.
2. **PLAN** — an open `spec-change:contract` names the section.
3. **PROBE** — a source in the row's `source` column needs probing: an `api:` source whose
   `docs/sources/<token>.md` lacks a `## <pkg>/<section>` heading, or a `dataset:` source
   with no `docs/sources/<token>.md` at all; or a `stage:` source whose profile
   `docs/sources/<token>.md` has no round line under its `## <pkg>/<section>` heading
   (**Sections served**), or whose newest round line ends `pending verify` or `revise: …`;
   or, for a section that would otherwise be DONE, a `stage:` source whose newest round
   line's commit is `none` or older than the section's code (rule 7's paths): the built
   section has not been profiled.
4. **DESIGN** — no design at `docs/packages/<pkg>/design/<section>.md`; or an open
   `spec-change:design` entry; or an open change file whose **Affected sections**
   names the section and is newer than the design; or a probe doc the row names lost or
   reworded a line the design was written against (added lines, the title line and other
   sections' entries do not count).
5. **TEST** — no `tests/intent/<section>/` under the package root; or the design is newer than
   the intent tree; or an open `spec-change:test` entry; or an `approved` deviation entry whose
   `Clause:` is cited by an intent test docstring that carries no `(deviation ` tag
   (regenerate).
6. **IMPLEMENT** — no README (`<section path>/README.md`; for `surface`,
   `docs/packages/<pkg>/interface.md`); or the intent tree, regeneration and `intent tests current with design`
   commits skipped, is newer than the README; or the section has a README, no review round
   covers its code, and the gate's record for its current commit ends `result: not done
   (attempt <n> of 3)`, a run that died between attempts.
7. **REVIEW** — no review round; or round 1 lacks its `a` or `b` report; or the section's code
   (its path, `tests/unit/<section>`, `tests/intent/<section>` less those same commits, its
   README) is newer than the newest round's `Commit:`; or the newest round's verdict is
   `spec-change` with no open spec-change left.
8. **FIX n** — the newest round `n` says `request changes`, the cap is not hit, and the code is
   not newer than its `Commit:`; or the newest round approves, the code is not newer than its
   `Commit:`, and the package's newest paths report is current, says `request changes`, is
   below its cap (round 3), and names the section on a line under **CRITICAL**; or the newest
   round approves, the code is not newer than its `Commit:`, and the package's integration
   record is current, fails, is below its cap (run 3), and names the section on its `reopens:`
   line (**Integration.** below).
9. **DONE** — the newest round approves and the code is not newer than its `Commit:`.

The **ledger** is one file per section, `docs/deviations/<pkg>/<section>.md`, so agents that
run in parallel on different sections never write the same file; a `docs/deviations.md` from
before that split is still read, and an entry moved out of it into its section's file keeps
the commit that first added it, so a move answers nothing and re-opens nothing.

Since 2.2 the section's ledger is `docs/packages/<pkg>/deviations/<section>.md`; the 2.0
location `docs/deviations/<pkg>/<section>.md` and the pre-2.0 `docs/deviations.md` are still
read, and an entry is edited in the file that holds it. Review reports are
`docs/packages/<pkg>/reviews/<section>/<date>-r<n>-<a|b|s>.md`, and a package's paths reports
`docs/packages/<pkg>/reviews/paths/<date>-r<n>-p.md`, letter `p`; the 2.0 names
`docs/reviews/<date>-<pkg>-<section>-r<n>-<letter>.md` are still read as round `n`. Change
files are `docs/packages/<pkg>/changes/<slug>.md`, one per affected package; a
`docs/changes/<slug>.md` is still read as naming every package its **Affected sections**
name. A ledger heading may end `— <k>`, the entry's 1-based sequence in its file; a heading
without it is a 2.x ledger and `k` is absent. The **inbox** is
`docs/packages/<pkg>/decisions/<section>.md`: `## D? — <question>` stubs and `## D<n>` entries
holding `Applied:` lines, merged into `docs/decisions.md` by `hooks/sync_decisions.py`. This
script never writes it; `--run-gate` fails on an inbox holding anything the central ledger
does not, and on a central `Applied: <pkg>/<section>, …` line the section's inbox entry for
that `D<n>` no longer holds (the hook mirrors a section's own lines), on a `stage:` row
whose `depends on` is empty, and on a data profile's `<token>.sample.json` over 200 KB.

An **open spec-change** is a ledger entry `spec-change:<level>` with `Status: open`, or a
review report of the newest round whose verdict is `spec-change`. A ledger entry whose heading
ends `— <k>` (written by 2.2 or later) is open until the agent that answers it sets its
`Status:` to `resolved` — the tester for `test`, the designer for `design`, the architect for
`contract` — and is never closed by commit order. A ledger entry without `— <k>`, and each
level a report's **Spec-change** heading names, keep the older rule: open until the document
the level names (the design, the intent tree, the package contract) is committed after it, or,
for a report's, until a ledger entry of that level for the section is committed with or after
the report (then the entry speaks). So a round-1 `b` reviewer, which never writes the ledger,
still re-opens the step. An older `spec-change:contract` ledger entry is closed by the
architect only.

Round 1 is a pair: a round whose reports carry letters and lack `a` or `b` is REVIEW (rule 7)
whatever the other says, so one reviewer's approval never ships a section alone.

A Sections `path` cell written as `…/<name>/` (or `.../<name>/`) is the default
`<package root>/src/<pkg>/<name>/`, the shorthand a contract's preamble explains.

Ready: a section whose state is neither DONE nor BLOCKED and whose every in-package `depends
on` is DONE. The `surface` row depends on every other row whatever its cell says — from
IMPLEMENT on. While the contract has a `## Call paths` heading (2.6), its PLAN, DESIGN and
TEST rows are ready whatever the other rows show, so the surface is designed and tested right
after PLAN from the contract; without the heading it waits for every other row at every
state, as before.
Shipped: the `surface` section is DONE, `--surface <pkg>` passes, the integration check
passes on the package's current code, and the paths review approves; otherwise the block
prints `shipped: no (surface <STATE>)`, `shipped: no (surface check FAIL)`, `shipped: no
(integration needed)`, `shipped: no (integration run <n> fail)`, `shipped: no (integration run
<n> incomplete)`, `shipped: no (paths needed)` or `shipped: no (paths round <n>)`. Rounds: the highest `n`
over the section's review reports, at either location; a round's verdict is the worst of its
reports (request changes > spec-change > approve); a report with no `-r<n>-` is round 1.

`--surface <pkg> --section <s>` checks one section's README, the per-section half the stop
gate runs for every section but `surface`: a row of **Entry points and interfaces** whose name
cell is not exactly one backticked Python identifier, and a `Public: yes` name the contract's
**Public surface (intent)** does not name as a whole word (skipped when it has no such item),
are each one reason; it prints `surface names <pkg>/<s>: PASS`, `FAIL` with one `  - <reason>`
line each (exit 1), or `n/a (no README)`.
`--rounds <pkg>/<section>` prints a third line, `commit: <short sha>`, the newest commit
touching the section's path, `tests/unit/<section>`, `tests/intent/<section>` and its README,
or `commit: none` — the reviewer copies it as its report's `Commit:` (F12).
`--rounds <pkg>/paths` prints the same three lines for the package's paths reports, `commit:`
the newest commit touching any section's code, then `previous:` and `diff base:` — the newest
paths report's path and its `Commit:` as `git rev-parse --short` gives it, each `none`
without one.

**Evidence.** The strings the driver copies out of a row's evidence cell:

1. **open** — `open <heading>; <heading>; …`: every open spec-change of the level that won
   the row (PLAN, DESIGN or TEST), ledger headings and `<report path> — spec-change:<level>`
   alike, `; `-separated.
2. **regenerate** — `regenerate: <heading>`: an approved deviation whose clause an untagged
   intent test cites.
3. **gate blocked** — `gate blocked: <the marker's reason>`.
4. **gate let through** — `gate let through after 3 attempts, <k> failures`.
5. **gate not done** — `gate not done (attempt <n> of 3)`.
6. **paths** — `paths r<m> request changes (<report path>)`: the package's paths report
   re-opened the section.
7. **stage** — `stage:<token> lacks ## <pkg>/<section>`; `stage:<token> r<n> pending
   verify`; `stage:<token> r<n> revise: K<a>, K<b>`; `stage:<token> r<n> not profiled on
   built code` (the newest round line's commit is `none`); `stage:<token> r<n> <sha> older
   than code <sha>`: the profiler's next run, which `--profile` prints.
8. **profile cap** — `profile r<n> new kinds (cap), open <heading>; <heading>`: every open
   `spec-change:design` ledger heading of the section.

**Gate record.** `.dev-team/gate/<pkg>/<section>.txt`, written by `hooks/gate_on_stop.py` on
every implementer stop. It speaks for the commit its `commit:` line names: the newest commit
touching the section's code, `tests/unit/<section>` and its README, the intent tree left out.
A record whose `commit:` is not that commit, a record with no `commit:` line (written before
2.4), a missing record, and a record read while those paths have uncommitted changes are all
treated as absent, and the row is derived without it. A record whose header slot is `report`
(`/dev-team:pair`'s wrap-up) or `spec-change` never holds a row. Once a review round's
`Commit:` covers the code the review speaks and the record is not read, which is what makes
the user's *review anyway* stick.

**Shape.** `--shape <pkg> --section <s>` prints the section's shape check, the lines the stop
gate copies into its record. It judges the functions and methods defined in the section's
non-test code (its path, nested sections excluded) whose `def` line the run added: a line
`git diff -U0 <base>` adds under the section's code, or any line of an untracked file, where
<base> is, in order:

1. the newest review round's `Commit:`, when it is an ancestor of `HEAD`;
2. else, when the section's design exists, its mode word (the `design mode:` of `--fields`) is
   `document`, and `git log --diff-filter=A` names the commit that added it: that commit, so
   code adopted before the design is measured and never failed;
3. else the empty tree.

Lines, in this order: the FAIL lines sorted by file then line, the one `indirect` line, the
`depth` lines, then `PASS`.

- `FAIL shape: <file>:<line> trivial-helper <name>` — a private function or method (`_name`,
  not a dunder) with three statements or fewer, the docstring not counted, that is referenced
  exactly once in the package's non-test code, by a call. Exempt: a function decorated
  `property`, `cached_property` or `<name>.setter`/`.getter`/`.deleter`; a method whose name is
  defined in more than one class of the package; a helper referenced anywhere other than as
  the function of a call (passed by name, stored, used as a decorator).
- `FAIL shape: <file>:<line> options-bag <name>` — a function or method, public or private,
  whose `**` parameter is annotated with a subscript of `Unpack` (`Unpack[...]` or
  `<module>.Unpack[...]`); `<name>` is `Class.method` for a method.
- `MEASURED shape indirect: <n>` — over every file judged, added lines or not: the lambdas that
  are an argument of a call (positional or keyword), the names passed as an argument that are
  functions nested in an enclosing function, and the calls whose function is a subscript
  (`_RUNNERS[stage](…)`). Printed whether or not anything failed; never a failure.
- `MEASURED shape depth <entry point>: <n>` — one per name in the section README's **Entry
  points and interfaces** table, in row order (the first identifier of each name cell); for
  `surface`, one per `[project.scripts]` command, named by the command. The value is the
  deepest effect below the entry point on the `--paths` call graph (**Paths.** below), the
  entry point's own frame at 0; a class's value is the largest over its public methods.
  `none` when no effect lies below it; `unresolved` when the name is not a function or class
  defined in the section's code. No `depth` line without a README, or for `surface` without
  commands. Never a failure.
- `PASS shape <pkg>/<s>` — when no FAIL line was printed.

Exit 1 on a FAIL line, else 0; 2 on a missing `--section` or a section the contract lacks.

**Paths.** `--paths <pkg>` prints one call tree per command in the `[project.scripts]` table of
`<package root>/pyproject.toml`, in the table's order, followed statically through the
package's own code. The module index is every non-test `.py` under the package's source root
(the `surface` row's path, else `<package root>/src/<pkg>`), each named by its dotted path from
the root's parent. Inside one function every call is read in source order, the bodies of
nested functions and lambdas left out (each is a frame of its own):

- a frame — a call to a function of the same module, to one imported from a module of the
  package, or to a function nested in the current one; `self.m(…)` or `cls.m(…)` when the class
  or a base class of the package defines `m` (`Class.m`); `mod.f(…)` or `pkg.mod.f(…)` through
  an imported package module; `C.m(…)`; and `C(…)`, a package class, as `C.__init__` when it
  has one (else nothing).
- `[indirect]` frames — `NAME[key](…)`, `NAME` a module-level dict literal of package
  functions: one frame per distinct value, in the dict's order. A lambda, a nested function's
  name or a package function's name passed as an argument: under the callee, after the callee's
  own calls, when the call resolved to a package function; else under the current function. A
  passed lambda or nested function whose own body makes no frame and no leaf is not printed.
- an effect leaf, `[effect: <callee as written>] (<file>:<line>)` — a call into a module
  outside the package whose root is not in `sys.stdlib_module_names` and is not `logging`,
  `loguru` or `structlog`; a call into `subprocess`, `socket`, `urllib`, `http`, `sqlite3` or
  `shutil`; or the builtin `open` or `print`. Any other outside call, builtin or method of a
  literal prints nothing, and so does a call on a module-level name assigned from a logging
  library's call (`log = logging.getLogger(__name__)`).
- an `[unresolved]` leaf, `<source text> (<file>:<line>) [unresolved]` — anything else: a
  parameter called, a local variable's method, `self.x.m(…)`, a subscript of something unknown.

Each block is `command: <name> = <target>`, then one line per frame, two spaces of indent per
level, `name (<file>:<line>)` at the line of the `def` or the lambda, marks after the
parenthesis: `[indirect]`, then `[seen]` for a function already printed in full or
`[recursive]` for one on the current path, neither expanded again (callables passed to it at
that call site still print under it). Then three footer lines, counted on the call graph from
the command function at depth 0, a callable passed to a callee two levels below the caller:
`depth to first effect: <n>` (the smallest depth of a frame that makes an effect call),
`deepest effect: <m>` (the largest, back edges ignored), each `none` without an effect, and
`indirect frames: <k>` (the `[indirect]` frames of the command's tree, each counted once). A
target whose module is not in the package prints `target outside the package`, and one whose
function the module lacks prints `target not found in the package`, with no footer. Blocks are
separated by a blank line; with no `[project.scripts]` table, an empty one, or no package
`pyproject.toml`, the one line `paths: no commands`. Exit 0; 2 with no package, or with no
`docs/packages/<pkg>/contract.md`.

**Call paths.** `--paths <pkg> --against-contract` prints, after each command's block and its
footer, the contract's **Call paths** entry for the command beside the tree. An open change
file naming the package (`open_changes`) that gives an entry for the command under **Contract
changes** — the last one it gives, the `to` after a `from` — is compared in the contract's
place, the first such file in path order: the code is built to the change before `sync-plan`
writes it into the contract. The first line is `contract: <command> (budget <n>)`, with `
from <change file path>` appended when the entry is a change file's, or `contract: no entry
for <command>` when the heading has no entry for it, or `contract: no Call paths heading`; the
last two end the block. Then,
per path of the entry, its kind on a line of its own (`  <kind>:`), then one line per
contract frame — `    <k> <owner>.<name>  match  <name> (<file>:<line>)` or `    <k>
<owner>.<name>  missing` — with every tree frame between two matched frames printed as `    -
<padding>  extra  <name> (<file>:<line>)` in tree order; then the effect line, `    effect
<callee>  reached`, `reached through <k> extra frame(s)` (those frames printed `extra` above
it) or `not reached`; then, once per command after its last path, `  summary: <k> match, <e>
extra, <m> missing; depth <d> of budget <n>` (`past budget` when `d > n`; `depth none of
budget <n>` when the block has no effect), the three counts counting the lines printed above
it, so a frame on two paths counts once per path. The frame column (`<k> <owner>.<name>`, or
`-` on an `extra` line) is padded to the entry's longest frame, then two spaces, then the
word. A frame matches when its file's section (`section_for_path`; `cli` for `cli.py` or
`cli/` and `pipelines` for `pipelines/` under the surface's path) is the frame's owner and its
printed name is the frame's name after the owner. Matching walks the printed tree depth-first
from the root, which must match frame 1, and never expands a `[seen]` or `[recursive]` frame;
a later frame is looked for below the last matched one, so a `missing` frame leaves the search
where it was. The effect is `reached` when an `[effect: …]` leaf is a direct child of the last
matched frame, whatever its callee: the contract's effect is named, not matched. A command
whose target is outside the package or not found has every frame `missing`. With no command
the line after `paths: no commands` is `contract: no Call paths heading`, `contract: none (no
commands)` when the heading says so, or `contract: entries for <command>, …, no command built`.
Exit codes as for `--paths`; `--against-contract` without `--paths` prints `--against-contract
needs --paths <pkg>` and exits 2.

**Paths review.** The package block's `paths:` line, printed after `integration:` and before
`shipped:` once every section row is DONE or a paths report exists, says where the package's
paths review stands, decided in this order:

- no `[project.scripts]` entry in `<package root>/pyproject.toml` (no file, no table, an empty
  table): approved, with no review to run;
- no paths report: needed;
- the newest report is stale when its `Commit:` is unreadable, or when any section's code (as
  rule 7 reads it) changed after that `Commit:`: needed;
- the newest report is current and approves: approved;
- otherwise a round: `n` is the report's round, its sections are the package's section names
  that start a line under its **CRITICAL** heading (`- <section>: …`, the name optionally
  backticked), in the Sections table's order, and the round is at its cap from round 3. Below
  the cap each named section that would otherwise be DONE is FIX n (rule 8); at the cap none
  is re-opened, and the driver asks first.

The line is `paths: needed`, `paths: approved (<report path>)` or `paths: approved (no
commands)`, or `paths: round <n> (request changes: <section>, …)`, with `no section named` in
place of the list when no CRITICAL line names a section, and ` (cap)` appended at the cap.

**Integration.** The package block's `integration:` line, printed after `scaffold:` and
before `paths:` once every section row is DONE or the record exists, says whether the whole
repo's checks pass with the package's current code. The record is
`.dev-team/integration/<pkg>.txt`, written by `hooks/gate_on_stop.py --integration <pkg>`
(run-package runs it once every section is DONE, before the paths review): a header
`dev-team integration — run <n> — <stamp> — package <pkg>`, then `commit: <short sha>` (`HEAD`
when it ran), `tree: clean` or `tree: uncommitted (<k> paths)`, one line per check, then
`reopens: <section>; …` (the package's sections a located failure lies in), `unowned: <path>;
…` (located failures no section of the package owns) and `unplaced: <check>; …` (failing checks
whose output names no file in the repo), each `none` when empty,, and `result: pass`, `result: fail (<k> failures)` or `result: incomplete (<k> out of
time)`. The record is current when its `tree:` is `clean`, its `commit:` is an ancestor of
`HEAD`, and nothing under the package root (for a package at the repo root, the repo less
`docs/`, `.dev-team/` and `.claude/`) has changed since, committed or not; otherwise the line
is `integration: needed`. A current record prints `integration: pass (<record>)`,
`integration: run <n> incomplete (<record>)`, or `integration: run <n> fail (reopens:
<section>, …)` — `no section named` in place of the list when `reopens:` names none of the
package's sections, ` (cap)` appended when it names one at run 3 or later. Below the cap each
named section that would otherwise be DONE is FIX n (rule 8); at the cap none is re-opened and
the driver asks. `<n>` is the writer's: one more than the previous record's when that record's
result was a fail, else 1.

**Scaffold.** A package is ready to be built in when its workspace exists: a root
`pyproject.toml`, and, when that root is a uv workspace (`[tool.uv.workspace]`), a
`pyproject.toml` at the package root and a CI workflow at `.github/workflows/ci.yml` holding,
verbatim, every command CI must run: the Floor and Enforced rows of `docs/constraints.md`,
else the Toolchain's lines less a trailing `# comment`, `<pkg>` written `$pkg`. `--scaffold
<pkg>` prints `scaffold: done` and exits 0, or `scaffold: needed (<reasons>)` and exits 1: `no
root pyproject.toml`, `no <package root>/pyproject.toml`, `no .github/workflows/ci.yml`,
``.github/workflows/ci.yml lacks `<cmd>`; …``. A root `pyproject.toml` that is not a uv
workspace is an adopted repo's own layout and needs nothing. The package block prints the
same `scaffold: needed` line, before `shipped:`, when it applies. run-package runs the
SCAFFOLD step on it before any other spawn, so every tester runs inside the workspace, under
the repo's own lint rules.

`--profile <pkg>/<section>` prints the profiler's spawn block, the one place its values are
resolved: run-package sends it verbatim. One block per `stage:` source of the row that
needs a run (every `stage:` source when none does), a blank line between blocks; one
`<Field>: <value>` line per field, in this order, `none` for a field with nothing to hold:

1. **Mode** — `profile`, or `verify` when the newest round line ends `pending verify`, or
   `defer` with `--defer`.
2. **Section** — `<pkg>/<section>`.
3. **Stage** — the token.
4. **Round** — the newest round line's round for `verify` and for a revision; that round plus
   one when a round over the built section is due, or when nothing is due and the section has
   a README; `0` with no round line.
5. **Revise** — the kinds after `revise:` on the newest round line.
6. **Commit** — the section's code commit, as `--rounds` prints it, at round 1 and later;
   else `none`.
7. **Contract** — `docs/packages/<pkg>/contract.md`.
8. **Repo contract** — `docs/architecture.md`.
9. **Dependency READMEs** — as line 7 of `--fields`.
10. **Source probes** — `docs/sources/<t>.md` per `api:` or `dataset:` source of each
    section in the row's `depends on`.
11. **Skills to invoke** — the row's `builds with`, less `dev-team:data-quality`.
12. **Data** — the contract's `## Package conventions` line for the stage.
13. **Profile** — `docs/sources/<token>.md`.
14. **Store** — `.dev-team/data/<token>/`.
15. **Run** — `run-package <pkg>`.

It prints `profile: no stage source in <pkg>/<section>` for a row with none, and exits 0;
2 on a target without `/` or a section the contract lacks, with the `--inputs` messages.
`--defer` prints, per `stage:` source whose newest round line ends `new kinds: …`, the block
with `Mode: defer`, that line's round and its commit (`profile: no new kinds to defer in
<pkg>/<section>` when none does); `--defer` without `--profile` prints `--defer needs
--profile <pkg>/<section>` and exits 2.

`--inputs <pkg>/<section>` prints the implementer's spawn block, the one place its values are
resolved: run-package sends it verbatim as the implementer's prompt, and pair reads the files
it names before touching the section. One `<Field>: <value>` line per field, in this order,
`none` for a field with nothing to hold:

1. **Section** — `<pkg>/<section>`.
2. **Design** — `docs/packages/<pkg>/design/<section>.md`.
3. **Contract** — `docs/packages/<pkg>/contract.md`.
4. **Repo contract** — `docs/architecture.md`.
5. **Dependency READMEs** — `<path>/README.md` per section in the row's `depends on`.
6. **Upstream interfaces** — per package in the Packages row's `depends on` that the
   design's `Upstream packages:` line names (every one when the design is missing or has no
   such line), `docs/packages/<dep>/interface.md` when it exists, else `provisional:
   docs/packages/<dep>/contract.md`.
7. **Source probes** — `docs/sources/<token>.md` per entry in the row's `source`.
8. **Intent tests** — `<package root>/tests/intent/<section>/` when it exists.
9. **Review** — from either location, the newest round's reports when its verdict is `request changes` (FIX n, or a
   cap granted one more round) or `spec-change` (a rebuild after the step it re-opened: its
   CRITICALs still stand), the package's paths report while it names the section and no
   review round of the section is newer than it, and the package's integration record while it
   is current, fails, and names the section on its `reopens:` line.
10. **Round** — the newest round plus one.
11. **Change file** — from either location, every open `docs/packages/<pkg>/changes/<slug>.md`
    or `docs/changes/<slug>.md` whose Affected sections names the section.
12. **Run** — `run-package <pkg>`.

`--fields <pkg>/<section>` prints the spawn fields run-package would otherwise resolve by
reading files, seven `key: value` lines in this order, and exits 0 (2 on a section the contract
lacks):

1. `mode: new | document | delta` — `delta` when an open change file names the section, or the
   state's evidence is `open <heading>` for a `spec-change:design`; `document` when the
   section's path holds a `.py` file (nested sections excluded; for `surface`, the package's
   own `__init__.py`, which the scaffold writes, does not count) and there is no design; else
   `new`. The designer's `Mode:` field.
2. `change file: <path>, … | none` — the open change files naming the section, as
   **Change file** in `--inputs`.
3. `design mode: <word> | none` — the word after `Mode:` on the design's first line (a title
   line above it is read past, up to the fifth line); `none` with no design or no such line.
   The tester's `Design mode:` field.
4. `diff base: <sha> | none` — from the newest round `n` ≥ 1, the `Commit:` of round `n`'s
   `-s` report, or its `-a` report when `n` is 1, or its one report when it has no letter;
   `none` with no round or no `Commit:`. The next reviewer's `Diff:` field is `<sha>..HEAD`.
5. `upstream interfaces: <path>, … | none` — as **Upstream interfaces** in `--inputs`. The
   tester's and the reviewer's field; the designer is sent every upstream package.
6. `paths report: <path> | none` — the package's newest paths report while its verdict is not
   `approve`, a line under its CRITICAL heading names the section, and the section's newest
   review round's `Commit:` is not newer than the report's: the same report `--inputs` adds to
   **Review**. The `full` reviewer's previous round after a paths FIX.
7. `dependency readmes: <path>/README.md, … | none` — the README of every section in the
   row's `depends on` (for `surface`, every other section) that exists on disk, in the
   Sections table's order; `none` when none does. Every role's **Dependency READMEs** field,
   so the early `surface` designer and tester are never sent a path to a file that is not
   there.
"""

from __future__ import annotations

import ast
import builtins
import heapq
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path.cwd().resolve()
DOCS = ROOT / "docs"

STATES = ("BLOCKED", "PLAN", "PROBE", "DESIGN", "TEST", "IMPLEMENT", "REVIEW", "FIX", "DONE")

# git-workflow-and-versioning §Project convention, Baseline: the files the user edits between
# runs, and agent memory, which agents write and nobody stages but the user. The one copy; a
# trailing slash exempts everything under it.
BASELINE_EXEMPT = ("docs/decisions.md", "docs/brief.md", "docs/constraints.md", ".claude/agent-memory/")

# A round's verdict is the worst of its reports; higher is worse.
VERDICT_RANK = {"approve": 0, "spec-change": 1, "request changes": 2}

UNCOMMITTED = "U"

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def set_root(path: Path) -> None:
    """Point every parser at the repo rooted at path. The default is the working directory."""
    global ROOT, DOCS
    ROOT = Path(path).resolve()
    DOCS = ROOT / "docs"


# ---------------------------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------------------------


def table_rows(md: str, must_have: tuple[str, ...]) -> list[dict[str, str]]:
    """Return the rows of the first markdown table whose header contains every name in must_have."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        header = [c.strip().lower().strip("`* ") for c in line.strip().strip("|").split("|")]
        if all(any(m in h for h in header) for m in must_have) and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                rows.append({h: (cells[k] if k < len(cells) else "") for k, h in enumerate(header)})
            return rows
    return []


def col(row: dict[str, str], name: str) -> str:
    """Fetch a cell by a loose header match, stripping backticks."""
    for h, v in row.items():
        if name in h:
            return v.strip("`* ")
    return ""


def _names(cell: str) -> list[str]:
    """A comma-separated cell as bare names; `—`, `-` and empty give none."""
    out = []
    for part in cell.split(","):
        name = part.strip().strip("`*_ ")
        if name and name not in ("—", "-", "–", "none"):
            out.append(name)
    return out


def _block(text: str, heading: str) -> str:
    """The body under a `##` heading named heading, up to the next `##` heading; empty when absent."""
    m = re.search(rf"^##\s+(?:\d+\.\s*)?{re.escape(heading)}\b.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def _item(text: str, name: str) -> str:
    """The body of a heading or a numbered bold item named name, up to the next of either.

    Lines inside fenced code blocks never end the body, so a `# comment` in a shell block does
    not read as a heading. A bold item is numbered (`5. **Call paths** —`): a prose line that
    wraps to start with the bold name (`**Call paths** names …`) is not the item.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"\s*(#+\s*(\d+\.\s*)?{re.escape(name)}\b|\d+\.\s*\*\*{re.escape(name)}\*\*)", line):
            start = i
            break
    if start is None:
        return ""
    body = [re.sub(rf"^.*?\*\*{re.escape(name)}\*\*\s*[—:-]?", "", lines[start])]
    fenced = False
    for line in lines[start + 1:]:
        if line.strip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"\s*(#+\s|\d+\.\s*\*\*)", line):
            break
        body.append(line)
    return "\n".join(body)


def _field(text: str, key: str) -> str:
    """The value of a `Key: value` line (bold, bulleted or numbered forms accepted); empty when absent."""
    m = re.search(rf"^[ \t]*(?:[-*][ \t]+|\d+\.[ \t]+)?\**{re.escape(key)}\**[ \t]*(?::|—)\**[ \t]*(.*)$", text, re.M | re.I)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------------------------


def git(*args: str) -> str | None:
    """Run a git command in the repo root; its stripped stdout, or None when git fails."""
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    except OSError:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _rel(path: Path | str) -> str:
    """A path as git sees it: relative to the root, posix; pathspec magic passed through."""
    s = str(path)
    if s.startswith(":("):
        return s
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(ROOT)
        except ValueError:
            return p.as_posix()
    return p.as_posix() or "."


def last_commit(*paths: Path | str) -> str | None:
    """Full SHA of the newest commit touching any of paths; None when not a repo or none does."""
    return git("log", "-1", "--format=%H", "--", *map(_rel, paths)) or None


def uncommitted(*paths: Path | str) -> bool:
    """True when any of paths has staged, unstaged or untracked changes."""
    return bool(git("status", "--porcelain", "--untracked-files=all", "--", *map(_rel, paths)))


def _untracked(paths: list[str] | None = None) -> list[str]:
    """Untracked, unignored files; under paths (git pathspecs) when given."""
    spec = ["--", *paths] if paths else []
    raw = git("ls-files", "--others", "--exclude-standard", "-z", *spec) or ""
    return [p for p in raw.split("\0") if p]


def diff_lines(base: str, paths: list[str] | None = None) -> list[tuple[str, str, int, str]]:
    """(path, '+' or '-', line number, text) for every added and removed line since base, under
    paths when given.

    Added lines carry their new line number, removed lines their old one. An untracked file
    counts as added in full.
    """
    out: list[tuple[str, str, int, str]] = []
    spec = ["--", *paths] if paths else []
    raw = git("diff", "-U0", "--no-color", "--no-ext-diff", base, *spec) or ""
    path, old, new = "", 0, 0
    for line in raw.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            old, new = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        elif path and line.startswith("+"):
            out.append((path, "+", new, line[1:]))
            new += 1
        elif path and line.startswith("-"):
            out.append((path, "-", old, line[1:]))
            old += 1
    for rel in _untracked(paths):
        try:
            text = (ROOT / rel).read_text()
        except (OSError, UnicodeDecodeError):
            continue
        out += [(rel, "+", i, t) for i, t in enumerate(text.splitlines(), 1)]
    return out


def _is_regen(summary: str, pkg: str, section: str) -> bool:
    return re.match(rf"{re.escape(pkg)}/{re.escape(section)}: (regenerate \d+ intent tests|intent tests current with design)", summary) is not None


def _log(paths: tuple[Path | str, ...], since: str | None = None) -> list[tuple[str, str]]:
    """(sha, summary) of every commit touching paths, newest first; only after since when given."""
    rng = [f"{since}..HEAD"] if since else []
    out = git("log", "--format=%H%x1f%s", *rng, "--", *map(_rel, paths)) or ""
    return [tuple(line.split("\x1f", 1)) for line in out.splitlines() if "\x1f" in line]  # type: ignore[misc]


def changed_since(sha: str, *paths: Path | str, skip_regen: tuple[str, str] | None = None) -> str | None:
    """The first commit after sha touching paths ('U' for uncommitted changes), or None.

    sha not in this history counts as changed: its sha is returned. With skip_regen=(pkg,
    section), commits whose summary is that section's `regenerate <k> intent tests` or `intent
    tests current with design` are skipped.
    """
    if uncommitted(*paths):
        return UNCOMMITTED
    if git("merge-base", "--is-ancestor", sha, "HEAD") is None:
        return sha
    for c, summary in reversed(_log(paths, since=sha)):
        if not (skip_regen and _is_regen(summary, *skip_regen)):
            return c
    return None


def _rev(*paths: Path | str, skip_regen: tuple[str, str] | None = None) -> str | None:
    """'U' when any path is uncommitted, else the newest commit touching them, else None."""
    if uncommitted(*paths):
        return UNCOMMITTED
    for c, summary in _log(paths):
        if not (skip_regen and _is_regen(summary, *skip_regen)):
            return c
    return None


def _newer(b: str | None, a: str | None) -> bool:
    """True when revision b is newer than revision a, by commit order ('U' is newest of all)."""
    if b is None or b == a:
        return False
    if b == UNCOMMITTED:
        return True
    if a == UNCOMMITTED:
        return False
    if a is None:
        return True
    return git("merge-base", "--is-ancestor", a, b) is not None


def _short(rev: str | None) -> str:
    return "uncommitted" if rev == UNCOMMITTED else rev[:7] if rev else "—"


# ---------------------------------------------------------------------------------------------
# Packages and sections
# ---------------------------------------------------------------------------------------------


def packages() -> list[tuple[str, Path]]:
    """(name, path) for every row of architecture.md's Packages table; docs/packages/* without one."""
    arch = DOCS / "architecture.md"
    out: list[tuple[str, Path]] = []
    if arch.exists():
        for row in table_rows(arch.read_text(), ("package", "path")):
            name, path = col(row, "package"), col(row, "path")
            if name and not name.startswith("-"):
                out.append((name, (ROOT / (path or ".")).resolve()))
    if not out and (DOCS / "packages").is_dir():
        out = [(d.name, ROOT / "packages" / d.name) for d in sorted((DOCS / "packages").glob("*")) if d.is_dir()]
    return out


def package_root(pkg: str) -> Path:
    """packages/<pkg>, or the path the Packages table gives it (the root for `.`)."""
    for name, path in packages():
        if name == pkg:
            return path
    return ROOT / "packages" / pkg


def contract_path(pkg: str) -> Path:
    return DOCS / "packages" / pkg / "contract.md"


def sections(pkg: str) -> list[dict[str, str]]:
    """The Sections table rows of the package contract, path resolved relative to the root.

    Keys: section, responsibility, path, owner doc, builds with, depends on, source. The
    `surface` row's `depends on` is every other section, whatever its cell says.
    """
    f = contract_path(pkg)
    if not f.exists():
        return []
    root = package_root(pkg)
    out = []
    for row in table_rows(f.read_text(), ("section", "path")):
        name = col(row, "section")
        if not name or name.startswith("-"):
            continue
        cell = col(row, "path")
        default = root / "src" / pkg / ("" if name == "surface" else name)
        short = re.fullmatch(r"(?:…|\.\.\.)/([\w.-]+)/?", cell or "")
        path = default.parent / short.group(1) if short else (ROOT / cell) if cell and cell not in ("—", "-") else default
        out.append({
            "section": name,
            "responsibility": col(row, "responsibility"),
            "path": _rel(path.resolve()).rstrip("/"),
            "owner doc": col(row, "owner"),
            "builds with": col(row, "builds"),
            "depends on": col(row, "depends"),
            "source": col(row, "source"),
        })
    names = [r["section"] for r in out]
    for r in out:
        if r["section"] == "surface":
            r["depends on"] = ", ".join(n for n in names if n != "surface")
    return out


def _row(pkg: str, section: str) -> dict[str, str] | None:
    return next((r for r in sections(pkg) if r["section"] == section), None)


def section_for_path(path: Path) -> tuple[str, str] | None:
    """(pkg, section) by longest section path prefix; the package top level → (pkg, "surface").

    A file under `<package root>/tests/intent/<section>/` or `tests/unit/<section>/` belongs to
    that section too.
    """
    p = Path(path)
    rel = _rel(p if p.is_absolute() else (ROOT / p).resolve())
    best: tuple[int, str, str] | None = None
    for pkg, root in packages():
        proot = _rel(root)
        for r in sections(pkg):
            prefixes = [r["path"]]
            for tree in ("intent", "unit"):
                prefixes.append(f"{proot}/tests/{tree}/{r['section']}" if proot != "." else f"tests/{tree}/{r['section']}")
            for pre in prefixes:
                if rel == pre or rel.startswith(pre.rstrip("/") + "/"):
                    if best is None or len(pre) > best[0]:
                        best = (len(pre), pkg, r["section"])
    return (best[1], best[2]) if best else None


def _paths(pkg: str, section: str) -> dict[str, object]:
    """Every path the state rules read for one section."""
    row = _row(pkg, section) or {"path": _rel(package_root(pkg) / "src" / pkg / section), "source": ""}
    root = package_root(pkg)
    spath = row["path"]
    nested = [r["path"] for r in sections(pkg) if r["section"] != section and r["path"].startswith(spath.rstrip("/") + "/")]
    code = [spath, *(f":(exclude){n}" for n in nested)]
    readme = (DOCS / "packages" / pkg / "interface.md") if section == "surface" else (ROOT / spath / "README.md")
    return {
        "row": row,
        "design": DOCS / "packages" / pkg / "design" / f"{section}.md",
        "intent": root / "tests" / "intent" / section,
        "unit": root / "tests" / "unit" / section,
        "code": code,
        "readme": readme,
    }


# ---------------------------------------------------------------------------------------------
# Ledgers: decisions, deviations, changes, reviews
# ---------------------------------------------------------------------------------------------


def _no_assumption(value: str) -> bool:
    return value.strip().strip("`*_ ").lower() in ("", "none", "—", "-", "–")


def decisions() -> list[dict[str, str]]:
    """Every `## D<n> — <question>` entry: n, question, scope, status, assumption."""
    f = DOCS / "decisions.md"
    if not f.exists():
        return []
    out = []
    for e in re.split(r"^## D(?=\d)", f.read_text(), flags=re.M)[1:]:
        head = e.splitlines()[0] if e.strip() else ""
        m = re.match(r"(\d+)\s*[—–-]?\s*(.*)", head)
        if not m:
            continue
        out.append({
            "n": m.group(1),
            "question": m.group(2).strip(),
            "scope": _field(e, "Scope") or _field(e, "Sections"),
            "status": _field(e, "Status").lower(),
            "assumption": _field(e, "Assumption if unanswered"),
        })
    return out


def _binds(scope: str, pkg: str, section: str) -> bool:
    for t in _names(scope):
        if t in ("repo", pkg, f"{pkg}/{section}") or ("/" not in t and t == section):
            return True
    return False


def blocking_decisions(pkg: str, section: str) -> list[str]:
    """D<n> that are open, have no assumption, and bind repo, pkg, or pkg/section."""
    return [f"D{d['n']}" for d in decisions()
            if d["status"].startswith("open") and _no_assumption(d["assumption"]) and _binds(d["scope"], pkg, section)]


DEVIATION_FIELDS = ("Clause", "Said", "Did", "Found", "Why", "Status", "Raised by", "Resolved by")


LEGACY_LEDGER = "deviations.md"


def ledger_path(pkg: str, section: str) -> Path:
    """The section's ledger: `docs/packages/<pkg>/deviations/<section>.md`."""
    return DOCS / "packages" / pkg / "deviations" / f"{section}.md"


def old_ledger_path(pkg: str, section: str) -> Path:
    """The 2.0 location of the section's ledger, `docs/deviations/<pkg>/<section>.md`; read only."""
    return DOCS / "deviations" / pkg / f"{section}.md"


def ledger_files(pkg: str | None = None, section: str | None = None) -> list[Path]:
    """The ledger files that can hold pkg's (and section's) entries: the pre-split
    `docs/deviations.md` when it exists, then the 2.0 per-section files, then the 2.2 ones."""
    out = [DOCS / LEGACY_LEDGER] if (DOCS / LEGACY_LEDGER).exists() else []
    if pkg and section:
        out += [f for f in (old_ledger_path(pkg, section), ledger_path(pkg, section)) if f.exists()]
    elif pkg:
        out += sorted((DOCS / "deviations" / pkg).glob("*.md")) + sorted((DOCS / "packages" / pkg / "deviations").glob("*.md"))
    else:
        out += sorted((DOCS / "deviations").glob("*/*.md")) + sorted((DOCS / "packages").glob("*/deviations/*.md"))
    return out


def inbox_path(pkg: str, section: str) -> Path:
    """The section's decisions inbox, `docs/packages/<pkg>/decisions/<section>.md`."""
    return DOCS / "packages" / pkg / "decisions" / f"{section}.md"


def inbox_files(pkg: str | None = None) -> list[Path]:
    """Every inbox of one package, or of the repo."""
    return sorted((DOCS / "packages").glob(f"{pkg or '*'}/decisions/*.md"))


def _applied_lines(body: str) -> list[str]:
    """The stripped `Applied:` lines of an entry body, bulleted or bold forms included."""
    return [line.strip() for line in body.splitlines()
            if re.match(r"(?:[-*]\s+)?\**Applied\**\s*:", line.strip())]


def applied_owner(line: str) -> str | None:
    """The `<pkg>/<section>` an `Applied:` line names first, or None."""
    m = re.match(r"(?:[-*]\s+)?\**Applied\**\s*:\s*\**\s*([\w.-]+/[\w.-]+)\s*,", line.strip())
    return m.group(1) if m else None


def inbox_section(path: Path) -> str:
    """`<pkg>/<section>` of an inbox path, `docs/packages/<pkg>/decisions/<section>.md`."""
    return f"{Path(path).parent.parent.name}/{Path(path).stem}"


def inbox_entries(path: Path) -> list[dict[str, object]]:
    """The entries of one inbox: heading, n (`?` or digits), question, Applied, Status, raw."""
    try:
        text = Path(path).read_text()
    except OSError:
        return []
    out: list[dict[str, object]] = []
    for e in re.split(r"^## (?=D[?\d])", text, flags=re.M)[1:]:
        head = e.splitlines()[0].strip()
        m = re.match(r"D(\?|\d+)\s*(?:[—–-]+\s*(.*))?$", head)
        if not m:
            continue
        out.append({"heading": head, "n": m.group(1), "question": (m.group(2) or "").strip(),
                    "Applied": _applied_lines(e), "Status": _field(e, "Status"), "raw": e})
    return out


def _central_bodies() -> dict[str, str]:
    """n → body of every `## D<n>` entry of docs/decisions.md."""
    f = DOCS / "decisions.md"
    if not f.exists():
        return {}
    out = {}
    for e in re.split(r"^## D(?=\d)", f.read_text(), flags=re.M)[1:]:
        m = re.match(r"\d+", e)
        if m:
            out.setdefault(m.group(0), e)
    return out


def unsynced_inboxes() -> list[str]:
    """One reason per inbox entry the central ledger lacks, and per central `Applied:` line of
    the inbox's own section that the inbox entry no longer holds; [] when every inbox is merged."""
    central = _central_bodies()
    out = []
    for f in inbox_files():
        own = inbox_section(f)
        for e in inbox_entries(f):
            n = str(e["n"])
            if n == "?":
                out.append(f"{_rel(f)}: D? stub not yet numbered")
            elif n not in central:
                out.append(f"{_rel(f)}: D{n} not in docs/decisions.md")
            else:
                have = {line.strip() for line in central[n].splitlines()}
                for line in e["Applied"]:  # type: ignore[union-attr]
                    if line not in have:
                        out.append(f"{_rel(f)}: D{n} Applied: line not in docs/decisions.md")
                        break
                for line in _applied_lines(central[n]):
                    if applied_owner(line) == own and line not in e["Applied"]:  # type: ignore[operator]
                        out.append(f"{_rel(f)}: stale Applied: line — D{n}: {line}")
    return out


def deviation_entries(pkg: str, section: str | None = None) -> list[dict[str, str]]:
    """Ledger entries for pkg (and section): heading fields, the eight fields, and the file.

    Keys: heading, pkg, section, date, kind, k (the heading's `— <k>`, "" on a 2.x heading),
    file, and Clause, Said, Did, Found, Why, Status, Raised by, Resolved by.
    """
    out = []
    for f in ledger_files(pkg, section):
        for e in re.split(r"^## ", f.read_text(), flags=re.M)[1:]:
            head = e.splitlines()[0].strip()
            m = re.match(r"`?([\w.-]+)/([\w.-]+)`?\s+[—–-]+\s+(\S+)\s+[—–-]+\s+`?([\w:-]+)`?(?:\s+[—–-]+\s+(\d+))?\s*$", head)
            if not m or m.group(1) != pkg or (section is not None and m.group(2) != section):
                continue
            entry = {"heading": head, "pkg": m.group(1), "section": m.group(2), "date": m.group(3),
                     "kind": m.group(4).lower(), "k": m.group(5) or "", "file": _rel(f)}
            for k in DEVIATION_FIELDS:
                entry[k] = _field(e, k)
            out.append(entry)
    return out


def _status(entry: dict[str, str]) -> str:
    return entry.get("Status", "").strip("`*_ ").lower().split()[0] if entry.get("Status", "").strip("`*_ ") else ""


def open_spec_changes(pkg: str, section: str | None = None) -> list[dict[str, str]]:
    return [e for e in deviation_entries(pkg, section) if e["kind"].startswith("spec-change") and _status(e) == "open"]


def entry_rev(entry: dict[str, str]) -> str | None:
    """The commit that added the entry (its heading to its ledger file, or its report); 'U' when
    not yet committed."""
    if entry.get("source") == "report":
        return entry["rev"]
    # Every ledger path, not only the entry's file: an entry moved between docs/deviations.md,
    # docs/deviations/ and docs/packages/*/deviations/ keeps the commit that first added it.
    heading = f"## {entry['heading']}"
    sha = (git("log", "--reverse", "--format=%H", "-S", heading, "--", "docs/deviations.md", "docs/deviations",
               "docs/packages/*/deviations/*.md") or "").split("\n")[0]
    return sha or UNCOMMITTED


def answered(entry: dict[str, str], rev: str | None) -> bool:
    """True when a spec-change is answered. A ledger entry whose heading carries `— <k>` (2.2 or
    later) speaks through its `Status:`: it is live while that reads `open`, whatever was
    committed since. An older ledger entry and a report-raised one keep the commit-order rule:
    answered when rev (the design, the intent tree, or for a report's, the contract) was
    committed after it. An older contract-level ledger entry is closed by the architect only."""
    if entry.get("source") != "report" and entry.get("k"):
        return False
    if entry["kind"] == "spec-change:contract" and entry.get("source") != "report":
        return False
    return _newer(rev, entry_rev(entry))


SPEC_LEVELS = ("contract", "design", "test")


def _spec_levels(text: str) -> list[str]:
    """The levels a report's **Spec-change** heading names, one per bullet, in order; a bullet
    naming none is `design`."""
    block = re.search(r"^#+\s*\**Spec-change\**\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.S)
    out: list[str] = []
    for line in (block.group(1) if block else "").splitlines():
        line = line.strip()
        if not line.startswith(("-", "*")) or re.fullmatch(r"[-*]\s*none\.?", line, re.I):
            continue
        m = re.search(r"spec-change:(contract|design|test)\b", line, re.I) or re.search(r"\b(contract|design|test)\b", line, re.I)
        level = m.group(1).lower() if m else "design"
        if level not in out:
            out.append(level)
    return out


def report_spec_changes(pkg: str, section: str) -> list[dict[str, str]]:
    """The spec-changes the newest round's `spec-change` reports raise that no ledger entry of the
    same level, committed with or after the report, records."""
    reps = _reports(pkg, section)
    if not reps:
        return []
    ledger = deviation_entries(pkg, section)
    out = []
    for f in sorted(reps[max(reps)]):
        if _verdict(_report_fields(f).get("Verdict")) != "spec-change":
            continue
        rev = _rev(f)
        for level in _spec_levels(f.read_text()):
            kind = f"spec-change:{level}"
            if any(e["kind"] == kind and not _newer(rev, entry_rev(e)) for e in ledger):
                continue
            out.append({"heading": f"{_rel(f)} — {kind}", "pkg": pkg, "section": section, "kind": kind,
                        "file": _rel(f), "source": "report", "rev": rev or UNCOMMITTED, "Status": "open"})
    return out


def live_spec_changes(pkg: str, section: str) -> list[dict[str, str]]:
    """Open spec-changes for one section, from the ledger and from the newest round's reports,
    that no later design, intent-tree or (for a report's) contract commit answered."""
    p = _paths(pkg, section)
    revs = {"spec-change:design": _rev(p["design"]), "spec-change:test": _rev(p["intent"]),  # type: ignore[arg-type]
            "spec-change:contract": _rev(contract_path(pkg))}
    return [e for e in [*open_spec_changes(pkg, section), *report_spec_changes(pkg, section)]
            if not answered(e, revs.get(e["kind"]))]


def clause_key(text: str) -> tuple[str, str] | None:
    """(n, item) of a `design §<n> <item>` citation, case-insensitive; None when there is none.

    The item is the whole name up to the first `:`, `;`, `,`, closing backtick or line end,
    backticks and `*` stripped, whitespace collapsed, lowercased (W3): `design §5 load trades
    from csv: one dict` → ("5", "load trades from csv").
    """
    m = re.search(r"design\s*§\s*(\d+)\s+(`?)([^:;,`\n]*)", text, re.I)
    if not m:
        return None
    item = " ".join(m.group(3).replace("*", "").split()).lower()
    return (m.group(1), item) if item else None


def change_files() -> list[dict[str, object]]:
    """Every change file: `docs/changes/<slug>.md` (pkg None), then `docs/packages/<pkg>/changes/<slug>.md`.

    Keys: slug, path, pkg, status, and the sections **Affected sections** names.
    """
    found = [(None, f) for f in sorted((DOCS / "changes").glob("*.md"))]
    found += [(f.parent.parent.name, f) for f in sorted((DOCS / "packages").glob("*/changes/*.md"))]
    out = []
    for pkg, f in found:
        text = f.read_text()
        affected = _item(text, "Affected sections")
        out.append({
            "slug": f.stem,
            "path": f,
            "pkg": pkg,
            "status": _field(text, "Status").strip("`*_ ").lower(),
            "sections": set(re.findall(r"\b([\w.-]+/[\w.-]+)\b", affected)),
        })
    return out


def open_changes(pkg: str, section: str | None = None) -> list[dict[str, object]]:
    """Open change files naming pkg (or pkg/section); a per-package file names only its own package's sections."""
    out = []
    for c in change_files():
        if not str(c["status"]).startswith("open"):
            continue
        if c["pkg"] is not None and c["pkg"] != pkg:
            continue
        secs: set[str] = c["sections"]  # type: ignore[assignment]
        if (section and f"{pkg}/{section}" in secs) or (not section and any(s.startswith(f"{pkg}/") for s in secs)):
            out.append(c)
    return out


def _reports(pkg: str, section: str) -> dict[int, list[Path]]:
    """Review reports of one section grouped by round, from `docs/packages/<pkg>/reviews/<section>/`
    and the flat `docs/reviews/`. A 0.6-era report is round 1, suffix s."""
    stem = re.escape(f"{pkg}-{section}")
    new = re.compile(rf"\d{{4}}-\d{{2}}-\d{{2}}-{stem}-r(\d+)-([abs])\.md")
    old = re.compile(rf"(\d{{4}}-\d{{2}}-\d{{2}})-{stem}(?:-(\d+))?\.md")
    per_section = re.compile(r"\d{4}-\d{2}-\d{2}-r(\d+)-([abs])\.md")
    rounds_: dict[int, list[Path]] = {}
    olds: list[tuple[str, int, Path]] = []
    for f in (DOCS / "packages" / pkg / "reviews" / section).glob("*.md"):
        if m := per_section.fullmatch(f.name):
            rounds_.setdefault(int(m.group(1)), []).append(f)
    for f in (DOCS / "reviews").glob(f"*-{pkg}-{section}*.md"):
        if m := new.fullmatch(f.name):
            rounds_.setdefault(int(m.group(1)), []).append(f)
        elif m := old.fullmatch(f.name):
            olds.append((m.group(1), int(m.group(2) or 1), f))
    if olds and 1 not in rounds_:
        # Several same-scope 0.6 reports are one loop; the newest one speaks for it.
        rounds_[1] = [max(olds)[2]]
    return rounds_


REPORT_FIELDS = ("Scope", "Commit", "Verdict", "Round", "Focus", "Convergence", "Diff")


def _report_fields(f: Path) -> dict[str, str]:
    text = f.read_text()
    out = {}
    for k in REPORT_FIELDS:
        m = re.search(rf"^\**{k}:\**\s*(.*)$", text, re.M)
        if m:
            out[k] = m.group(1).strip()
    return out


def _verdict(value: str | None) -> str:
    """A Verdict: value normalized; absent or unrecognized reads as `request changes`."""
    v = (value or "").strip("`*_ ").lower()
    if v.startswith("approve"):
        return "approve"
    if v.startswith("spec-change") or v.startswith("spec change"):
        return "spec-change"
    return "request changes"


def rounds(pkg: str, section: str) -> int:
    """The newest review round of a section; 0 with none."""
    return max(_reports(pkg, section), default=0)


def newest_round(pkg: str, section: str) -> tuple[int, str, str | None, dict[str, str]]:
    """(n, verdict, Commit sha, header fields) of the newest round; (0, "", None, {}) with none.

    The verdict is the worst of the round's reports. The Commit is the earliest over its
    reports, and None when any report lacks one. Header fields are the worst report's.
    """
    reps = _reports(pkg, section)
    if not reps:
        return 0, "", None, {}
    n = max(reps)
    parsed = [_report_fields(f) for f in sorted(reps[n])]
    worst = max(parsed, key=lambda p: VERDICT_RANK[_verdict(p.get("Verdict"))])
    shas = [re.match(r"[0-9a-f]{7,40}", p.get("Commit", "").strip("`")) for p in parsed]
    sha: str | None = None
    if all(shas):
        sha = shas[0].group(0)  # type: ignore[union-attr]
        for m in shas[1:]:
            if git("merge-base", "--is-ancestor", m.group(0), sha) is not None:  # type: ignore[union-attr]
                sha = m.group(0)  # type: ignore[union-attr]
    return n, _verdict(worst.get("Verdict")), sha, worst


def review_base(pkg: str, section: str) -> str:
    """The newest review round's `Commit:` when it is an ancestor of `HEAD`, else the empty tree."""
    sha = newest_round(pkg, section)[2]
    if sha and git("merge-base", "--is-ancestor", sha, "HEAD") is not None:
        return sha
    return EMPTY_TREE


def _missing_letters(pkg: str, section: str) -> list[str]:
    """Round 1's missing half: `a` or `b` when its reports carry letters and one is absent."""
    letters = {m.group(1) for f in _reports(pkg, section).get(1, [])
               if (m := re.search(r"-r1-([abs])\.md$", f.name))}
    if not letters or "s" in letters:
        return []
    return [x for x in ("a", "b") if x not in letters]


def _prior_unfixed(fields: dict[str, str]) -> int:
    m = re.search(r"(\d+)\s+prior unfixed", fields.get("Convergence", ""))
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------------------------


# A data profile's title line (planning-templates' data-profile.md); hooks/guard_writes.py keeps a copy.
STAGE_TITLE = re.compile(r"# Source probe — .+ — stage — ")


def _sources(cell: str) -> list[tuple[str, str]]:
    """(kind, token) per entry of a `source` cell; a bare token is `api`."""
    out = []
    for name in _names(cell):
        kind, _, token = name.partition(":") if ":" in name else ("api", "", name)
        out.append((kind.strip().lower(), token.strip().lower()))
    return out


def _has_section_heading(text: str, pkg: str, section: str) -> bool:
    return re.search(rf"^##\s+`?{re.escape(pkg)}/{re.escape(section)}`?\s*$", text, re.M) is not None


def _strip_other_sections(text: str, pkg: str, section: str) -> str:
    """A probe doc less every `## <pkg>/<section>` block but this section's own."""
    parts = re.split(r"(?=^##\s)", text, flags=re.M)
    keep = []
    for part in parts:
        m = re.match(r"##\s+`?([\w.-]+)/([\w.-]+)`?\s*$", part.splitlines()[0]) if part.startswith("##") else None
        if m and (m.group(1), m.group(2)) != (pkg, section):
            continue
        keep.append(part.rstrip())
    return "\n".join(keep).strip()


def _shared_lines(text: str, pkg: str, section: str) -> list[str]:
    """A probe doc's non-blank lines, less its title line (the first line starting `# `) and
    every `## <pkg>/<section>` entry but this section's own."""
    lines = [line for line in _strip_other_sections(text, pkg, section).splitlines() if line.strip()]
    title = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if title is not None:
        del lines[title]
    return lines


def _is_subsequence(needle: list[str], hay: list[str]) -> bool:
    """True when every item of needle appears in hay, in order."""
    it = iter(hay)
    return all(any(x == y for y in it) for x in needle)


def _probe_newer(doc: Path, design_rev: str | None, pkg: str, section: str) -> str | None:
    """The probe doc's revision when it changed the design's view of the source, else None.

    The doc as it stood at the design's commit is compared with the doc now, line by line, each
    reduced by `_shared_lines`. Added lines, the title line (its date) and other sections'
    `## <pkg>/<section>` entries re-open nothing: a new consuming section makes that section
    need PROBE, not this design stale. A design-time line that is gone or reworded does.
    """
    doc_rev = _rev(doc)
    if not _newer(doc_rev, design_rev):
        return None
    if design_rev in (None, UNCOMMITTED):
        return doc_rev
    before = git("show", f"{design_rev}:{_rel(doc)}")
    if before is None:
        return doc_rev
    now = doc.read_text() if doc.exists() else ""
    if _is_subsequence(_shared_lines(before, pkg, section), _shared_lines(now, pkg, section)):
        return None
    return doc_rev


ROUND_LINE = re.compile(r"^Round (\d+) — \S+ — commit (\S+) — (.+)$", re.M)

# The one skill of a `stage:` row's `builds with` that is the designer's and implementer's, not the profiler's.
DATA_QUALITY = "dev-team:data-quality"


def _round_lines(text: str, pkg: str, section: str) -> list[tuple[int, str, str]]:
    """(round, commit, verdict) per round line inside the profile's `## <pkg>/<section>` block,
    from that heading to the next `## ` heading or the end, in file order."""
    m = re.search(rf"^##\s+`?{re.escape(pkg)}/{re.escape(section)}`?\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return []
    return [(int(r.group(1)), r.group(2), r.group(3).strip()) for r in ROUND_LINE.finditer(m.group(1))]


def profile_due(pkg: str, section: str, token: str) -> dict[str, object] | None:
    """The profiler's next run on a `stage:` source, by the newest round line, or None when none is due.

    Keys: mode, round, revise, evidence. No profile, no `## <pkg>/<section>` heading or no
    round line under it: a `profile` run at round 0. `pending verify`: a `verify` run at that
    round. `revise: <kinds>`: a `profile` run at that round revising those kinds.
    """
    doc = DOCS / "sources" / f"{token}.md"
    lines = _round_lines(doc.read_text(), pkg, section) if doc.exists() else []
    if not lines:
        return {"mode": "profile", "round": 0, "revise": "none", "evidence": f"stage:{token} lacks ## {pkg}/{section}"}
    n, _, verdict = lines[-1]
    if verdict == "pending verify":
        return {"mode": "verify", "round": n, "revise": "none", "evidence": f"stage:{token} r{n} pending verify"}
    if verdict.startswith("revise:"):
        kinds = verdict.removeprefix("revise:").strip() or "none"
        return {"mode": "profile", "round": n, "revise": kinds, "evidence": f"stage:{token} r{n} revise: {kinds}"}
    return None


def built_round_due(pkg: str, section: str, token: str) -> dict[str, object] | None:
    """A round over the built section, or None: the newest round line closed its round and its
    commit is `none` or older than the section's code (rule 7's paths). Same keys as `profile_due`.

    It does not look at the state; `section_state` asks only of a row that would be DONE.
    """
    doc = DOCS / "sources" / f"{token}.md"
    lines = _round_lines(doc.read_text(), pkg, section) if doc.exists() else []
    if not lines or profile_due(pkg, section, token) is not None:
        return None
    n, commit, _ = lines[-1]
    due = {"mode": "profile", "round": n + 1, "revise": "none"}
    if commit == "none":
        return {**due, "evidence": f"stage:{token} r{n} not profiled on built code"}
    if (after := _code_after_review(pkg, section, commit)) is None:
        return None
    code = after if after == UNCOMMITTED else section_commit(pkg, section)
    return {**due, "evidence": f"stage:{token} r{n} {_short(commit)} older than code {_short(code)}"}


def _profile_cap(pkg: str, section: str, row: dict[str, str], spec: list[dict[str, str]]) -> str | None:
    """Rule 1's profile cap: the evidence when a `stage:` source's newest round line, at round 2
    or later, ends `new kinds: …` and an open `spec-change:design` the profiler raised is live."""
    design = [e for e in spec if e["kind"] == "spec-change:design" and e.get("source") != "report"]
    if not any(e.get("Raised by", "").strip("`*_ ").startswith("profiler") for e in design):
        return None
    for kind, token in _sources(row.get("source", "")):
        doc = DOCS / "sources" / f"{token}.md"
        lines = _round_lines(doc.read_text(), pkg, section) if kind == "stage" and doc.exists() else []
        if lines and lines[-1][0] >= 2 and lines[-1][2].startswith("new kinds:"):
            return f"profile r{lines[-1][0]} new kinds (cap), open " + "; ".join(e["heading"] for e in design)
    return None


# ---------------------------------------------------------------------------------------------
# The state
# ---------------------------------------------------------------------------------------------


def intent_docstrings(tree: Path) -> dict[str, str]:
    """Test node id → first docstring line, for every test function under tree, via ast."""
    out: dict[str, str] = {}
    if not tree.is_dir():
        return out
    for f in sorted(tree.rglob("*.py")):
        if not (f.name.startswith("test_") or f.name.endswith("_test.py")):
            continue
        try:
            mod = ast.parse(f.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        rel = _rel(f.resolve())

        def visit(body: list[ast.stmt], prefix: str) -> None:
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                    doc = ast.get_docstring(node) or ""
                    out[f"{prefix}::{node.name}"] = doc.strip().splitlines()[0] if doc.strip() else ""
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    visit(node.body, f"{prefix}::{node.name}")

        visit(mod.body, rel)
    return out


def _cap_hit(n: int, verdict: str, fields: dict[str, str]) -> bool:
    return verdict == "request changes" and (n >= 3 or (n == 2 and _prior_unfixed(fields) >= 1))


# ---------------------------------------------------------------------------------------------
# The stop gate's record
# ---------------------------------------------------------------------------------------------


GATE_HEADER = re.compile(r"^dev-team gate — (attempt (\d+)|blocked|spec-change|report) — ")


def _gate_paths(pkg: str, section: str) -> list[Path | str]:
    """What the implementer writes for the section: its code (nested sections excluded),
    `tests/unit/<section>` and its README (`interface.md` for `surface`). Not the intent tree."""
    p = _paths(pkg, section)
    return [*p["code"], p["unit"], p["readme"]]  # type: ignore[list-item]


def gate_commit(pkg: str, section: str) -> str | None:
    """Full sha of the newest commit touching the section's code, unit tree and README: the commit
    a gate record speaks for. None when no commit does. The stop gate imports it, so the record's
    writer and its reader compute the same commit."""
    return last_commit(*_gate_paths(pkg, section))


def gate_record(pkg: str, section: str) -> dict[str, object] | None:
    """The stop gate's record for the section's current commit, parsed; None when it is absent or stale.

    Keys: slot (`attempt`, `blocked`, `spec-change` or `report`), attempt (int or None),
    result (the text after `result: ` on the last non-empty line), fails (every line starting
    `FAIL`), blocked (the text after `blocked: `, or "").
    """
    f = ROOT / ".dev-team" / "gate" / pkg / f"{section}.txt"
    try:
        lines = [line.rstrip("\n") for line in f.read_text().splitlines()]
    except (OSError, UnicodeDecodeError):
        return None
    if len(lines) < 3:
        return None
    head = GATE_HEADER.match(lines[0])
    if head is None:
        return None
    value = next((line[len("commit:"):].strip() for line in lines if line.startswith("commit:")), None)
    if value is None:
        return None
    if uncommitted(*_gate_paths(pkg, section)):
        return None
    sha = gate_commit(pkg, section)
    if value == "none":
        if sha is not None:
            return None
    elif len(value) < 7 or sha is None or not sha.startswith(value):
        return None
    last = next((line for line in reversed(lines) if line.strip()), "")
    slot = "attempt" if head.group(2) else head.group(1)
    return {
        "slot": slot,
        "attempt": int(head.group(2)) if head.group(2) else None,
        "result": last[len("result: "):].strip() if last.startswith("result: ") else "",
        "fails": [line for line in lines if line.startswith("FAIL")],
        "blocked": next((line[len("blocked: "):].strip() for line in lines if line.startswith("blocked: ")), ""),
    }


def _code_after_review(pkg: str, section: str, rsha: str) -> str | None:
    """The first change to the section's code (its path, `tests/unit/<section>`,
    `tests/intent/<section>` less regeneration commits, its README) after review commit rsha;
    None when there is none. Rule 7 and `_review_covers` both read it."""
    p = _paths(pkg, section)
    return changed_since(rsha, *p["code"], p["unit"], p["intent"], p["readme"], skip_regen=(pkg, section))  # type: ignore[misc]


def _review_covers(pkg: str, section: str) -> bool:
    """True when a review round exists, its `Commit:` is readable, and the section's code is not
    newer than it: rule 7's expression."""
    n, _, rsha, _ = newest_round(pkg, section)
    if n == 0 or rsha is None:
        return False
    return _code_after_review(pkg, section, rsha) is None


def _gate_hold(pkg: str, section: str, readme: Path) -> dict[str, object] | None:
    """The gate record that may hold the row: the README exists, no review round covers the
    code, and the record is current; else None."""
    if not readme.exists() or _review_covers(pkg, section):
        return None
    return gate_record(pkg, section)


def section_state(pkg: str, section: str, paths: dict[str, object] | None = None,
                  integration: dict[str, object] | None = None) -> tuple[str, str]:
    """(STATE, evidence) for one section: the first rule in the module docstring that fires.

    paths is the package's `paths_state` and integration its `integration_state`, each computed
    here when not given; `package_table` passes both once for every row. Rule 3's after-build
    round applies only where the rest would say DONE.
    """
    state, evidence = _state_before_built_round(pkg, section, paths, integration)
    if state != "DONE":
        return state, evidence
    row = _row(pkg, section) or {}
    for kind, token in _sources(row.get("source", "")):
        if kind == "stage" and (due := built_round_due(pkg, section, token)):
            return "PROBE", str(due["evidence"])
    return state, evidence


def _state_before_built_round(pkg: str, section: str, paths: dict[str, object] | None,
                              integration: dict[str, object] | None = None) -> tuple[str, str]:
    """`section_state` without rule 3's after-build round."""
    p = _paths(pkg, section)
    row: dict[str, str] = p["row"]  # type: ignore[assignment]
    design: Path = p["design"]  # type: ignore[assignment]
    intent: Path = p["intent"]  # type: ignore[assignment]
    readme: Path = p["readme"]  # type: ignore[assignment]
    code: list[str] = p["code"]  # type: ignore[assignment]
    regen = (pkg, section)

    # 1. BLOCKED
    if ds := blocking_decisions(pkg, section):
        return "BLOCKED", f"{', '.join(ds)} open, no assumption"
    n, verdict, rsha, fields = newest_round(pkg, section)
    if _cap_hit(n, verdict, fields):
        k = _prior_unfixed(fields)
        return "BLOCKED", f"review r{n} request changes" + (f", {k} prior unfixed" if k else "") + " (cap)"
    record = _gate_hold(pkg, section, readme)
    if record is not None:
        result = str(record["result"])
        if record["slot"] == "blocked" and result == "blocked":
            why = str(record["blocked"]).replace(" · ", ", ") or "(no reason given)"
            return "BLOCKED", f"gate blocked: {why}"
        if record["slot"] == "attempt" and result.startswith("letting the run stop"):
            m = re.search(r"with (\d+) failure", result)
            return "BLOCKED", f"gate let through after 3 attempts, {m.group(1) if m else '?'} failures"

    spec = live_spec_changes(pkg, section)
    if cap := _profile_cap(pkg, section, row, spec):
        return "BLOCKED", cap
    kinds = {e["kind"] for e in spec}

    # 2. PLAN
    if "spec-change:contract" in kinds:
        heads = [e["heading"] for e in spec if e["kind"] == "spec-change:contract"]
        return "PLAN", "open " + "; ".join(heads)

    # 3. PROBE
    for kind, token in _sources(row.get("source", "")):
        doc = DOCS / "sources" / f"{token}.md"
        if kind == "dataset" and not doc.exists():
            return "PROBE", f"dataset:{token} has no {_rel(doc)}"
        if kind == "api" and (not doc.exists() or not _has_section_heading(doc.read_text(), pkg, section)):
            return "PROBE", f"api:{token} lacks ## {pkg}/{section}"
        if kind == "stage" and (due := profile_due(pkg, section, token)):
            return "PROBE", str(due["evidence"])

    # 4. DESIGN
    if not design.exists():
        return "DESIGN", "no design"
    if "spec-change:design" in kinds:
        heads = [e["heading"] for e in spec if e["kind"] == "spec-change:design"]
        return "DESIGN", "open " + "; ".join(heads)
    design_rev = _rev(design)
    for c in open_changes(pkg, section):
        crev = _rev(c["path"])  # type: ignore[arg-type]
        if _newer(crev, design_rev):
            return "DESIGN", f"change {c['slug']} {_short(crev)} newer than design {_short(design_rev)}"
    for _, token in _sources(row.get("source", "")):
        doc = DOCS / "sources" / f"{token}.md"
        if doc.exists() and (prev := _probe_newer(doc, design_rev, pkg, section)):
            return "DESIGN", f"{_rel(doc)} {_short(prev)} newer than design {_short(design_rev)}"

    # 5. TEST
    if not intent.is_dir():
        return "TEST", f"no {_rel(intent)}"
    intent_rev = _rev(intent)
    if _newer(design_rev, intent_rev):
        if design_rev == UNCOMMITTED:
            return "TEST", f"uncommitted: {_rel(design)}"
        return "TEST", f"design {_short(design_rev)} newer than tests {_short(intent_rev)}"
    if "spec-change:test" in kinds:
        # every open one, so Regenerate names them all: a tester resolves only the entries it is sent
        heads = [e["heading"] for e in spec if e["kind"] == "spec-change:test"]
        return "TEST", "open " + "; ".join(heads)
    approved = [e for e in deviation_entries(pkg, section) if e["kind"] == "deviation" and _status(e) == "approved"]
    if approved:
        docs = intent_docstrings(intent)
        for e in approved:
            key = clause_key(e["Clause"])
            if key and any(clause_key(d) == key and "(deviation " not in d for d in docs.values()):
                return "TEST", f"regenerate: {e['heading']}"

    # 6. IMPLEMENT
    if not readme.exists():
        return "IMPLEMENT", f"no {_rel(readme)}"
    readme_rev = _rev(readme)
    intent_rev_nr = _rev(intent, skip_regen=regen)
    if _newer(intent_rev_nr, readme_rev):
        if intent_rev_nr == UNCOMMITTED:
            return "IMPLEMENT", f"uncommitted: {_rel(intent)}"
        return "IMPLEMENT", f"tests {_short(intent_rev_nr)} newer than README {_short(readme_rev)}"
    if record is not None and record["slot"] == "attempt" and str(record["result"]).startswith("not done (attempt "):
        return "IMPLEMENT", f"gate {record['result']}"

    # 7. REVIEW
    if n == 0:
        return "REVIEW", "no review"
    if n == 1 and (missing := _missing_letters(pkg, section)):
        return "REVIEW", f"review r1 lacks its {' and '.join(missing)} report"
    if rsha is None:
        return "REVIEW", f"review r{n} has no Commit:"
    if (after := _code_after_review(pkg, section, rsha)) is not None:
        if after == UNCOMMITTED:
            return "REVIEW", f"uncommitted: {code[0]}"
        return "REVIEW", f"code {_short(after)} newer than review r{n} {rsha[:7]}"
    if verdict == "spec-change":
        return "REVIEW", f"review r{n} spec-change, no open entry left"

    # 8. FIX n
    if verdict == "request changes":
        return f"FIX {n}", f"review r{n} request changes"
    if paths is None:
        paths = paths_state(pkg)
    if paths["kind"] == "round" and not paths["cap"] and section in paths["sections"]:  # type: ignore[operator]
        return f"FIX {n}", f"paths r{paths['n']} request changes ({_rel(paths['report'])})"  # type: ignore[arg-type]
    if integration is None:
        integration = integration_state(pkg)
    if integration["kind"] == "fail" and not integration["cap"] and section in integration["sections"]:  # type: ignore[operator]
        return f"FIX {n}", f"integration run {integration['n']} fail ({_rel(integration['record'])})"  # type: ignore[arg-type]

    # 9. DONE
    return "DONE", f"review r{n} approve @{rsha[:7]}"


def section_commit(pkg: str, section: str) -> str | None:
    """Short sha of the newest commit touching the section's code, unit tree, intent tree and
    README (not its design): the commit a reviewer reviews, and its report's `Commit:` (F12)."""
    p = _paths(pkg, section)
    return git("log", "-1", "--format=%h", "--", *map(_rel, (*p["code"], p["unit"], p["intent"], p["readme"]))) or None  # type: ignore[misc]


def package_commit(pkg: str) -> str | None:
    """Short sha of the newest commit touching any section's code, unit tree, intent tree or
    README, over every row of the Sections table: a paths report's `Commit:`."""
    paths: list[str] = []
    for r in sections(pkg):
        p = _paths(pkg, r["section"])
        # A section's code pathspec excludes its nested sections; across every row those are
        # covered by their own rows, and a global exclude would hide them, so it is dropped.
        code = [c for c in p["code"] if not c.startswith(":(")]  # type: ignore[union-attr]
        paths += map(_rel, (*code, p["unit"], p["intent"], p["readme"]))  # type: ignore[arg-type]
    if not paths:
        return None
    return git("log", "-1", "--format=%h", "--", *paths) or None


def paths_reports(pkg: str) -> dict[int, Path]:
    """A package's paths reports by round, `docs/packages/<pkg>/reviews/paths/<date>-r<n>-p.md`;
    the newest file name wins when two share a round."""
    out: dict[int, Path] = {}
    for f in sorted((DOCS / "packages" / pkg / "reviews" / "paths").glob("*.md")):
        if m := re.fullmatch(r"\d{4}-\d{2}-\d{2}-r(\d+)-p\.md", f.name):
            out[int(m.group(1))] = f
    return out


def paths_rounds(pkg: str) -> list[str]:
    """The five `--rounds <pkg>/paths` lines: rounds, next round, commit, previous, diff base."""
    reps = paths_reports(pkg)
    n = max(reps, default=0)
    prev = reps.get(n)
    base = None
    if prev is not None:
        m = re.match(r"[0-9a-f]{7,40}", _report_fields(prev).get("Commit", "").strip("`"))
        base = git("rev-parse", "--short", m.group(0)) if m else None
    return [
        f"rounds: {n}",
        f"next round: {n + 1}",
        f"commit: {package_commit(pkg) or 'none'}",
        f"previous: {_rel(prev) if prev else 'none'}",
        f"diff base: {base or 'none'}",
    ]


def _report_sha(fields: dict[str, str]) -> str | None:
    """A report's `Commit:` value as a sha, None when it is unreadable."""
    m = re.match(r"[0-9a-f]{7,40}", fields.get("Commit", "").strip("`"))
    return m.group(0) if m else None


def _critical_sections(pkg: str, report: Path) -> list[str]:
    """The package's section names that start a line under the report's **CRITICAL** heading,
    in the Sections table's order."""
    body = _block(report.read_text(), "CRITICAL")
    return [s for s in (r["section"] for r in sections(pkg))
            if re.search(rf"^\s*(?:[-*]\s+)?`?{re.escape(s)}`?:\s", body, re.M)]


def paths_state(pkg: str) -> dict[str, object]:
    """Where the package's paths review stands; the module docstring's **Paths review.**.

    Keys: kind (`approved`, `needed` or `round`), n (the newest report's round, 0 without
    one), verdict, report (its path, or None), sections (the names its CRITICAL lines start
    with, for `round`), cap (`round` at round 3 or later).
    """
    out: dict[str, object] = {"kind": "needed", "n": 0, "verdict": "", "report": None, "sections": [], "cap": False}
    if not package_scripts(pkg):
        return {**out, "kind": "approved"}
    reps = paths_reports(pkg)
    if not reps:
        return out
    n = max(reps)
    report = reps[n]
    fields = _report_fields(report)
    sha = _report_sha(fields)
    if sha is None or any(_code_after_review(pkg, r["section"], sha) is not None for r in sections(pkg)):
        return out
    verdict = _verdict(fields.get("Verdict"))
    if verdict == "approve":
        return {**out, "kind": "approved", "n": n, "verdict": verdict, "report": report}
    return {**out, "kind": "round", "n": n, "verdict": verdict, "report": report,
            "sections": _critical_sections(pkg, report), "cap": n >= 3}


def paths_line(state: dict[str, object]) -> str:
    """The package block's `paths:` line for a `paths_state`."""
    report = state["report"]
    if state["kind"] == "approved":
        return f"paths: approved ({_rel(report) if report else 'no commands'})"  # type: ignore[arg-type]
    if state["kind"] == "needed":
        return "paths: needed"
    named = ", ".join(state["sections"]) or "no section named"  # type: ignore[arg-type]
    return f"paths: round {state['n']} (request changes: {named})" + (" (cap)" if state["cap"] else "")


def section_paths_report(pkg: str, section: str) -> Path | None:
    """The newest paths report while it speaks to the section: its verdict is not `approve`, a
    CRITICAL line names the section, and no review round of the section is newer than its
    `Commit:`. `--inputs`' Review and `--fields`' `paths report:` both read it."""
    reps = paths_reports(pkg)
    if not reps:
        return None
    report = reps[max(reps)]
    fields = _report_fields(report)
    psha = _report_sha(fields)
    if psha is None or _verdict(fields.get("Verdict")) == "approve" or section not in _critical_sections(pkg, report):
        return None
    rsha = newest_round(pkg, section)[2]
    if rsha and git("merge-base", "--is-ancestor", psha, rsha) is not None and git("rev-parse", psha) != git("rev-parse", rsha):
        return None
    return report


INTEGRATION_HEADER = re.compile(r"^dev-team integration — run (\d+) — ")


def integration_path(pkg: str) -> Path:
    """The package's integration record, `.dev-team/integration/<pkg>.txt`."""
    return ROOT / ".dev-team" / "integration" / f"{pkg}.txt"


def integration_pathspec(pkg: str) -> list[str]:
    """What an integration record speaks for: the package root; for a package at the repo root,
    the repo less `docs/`, `.dev-team/` and `.claude/`."""
    rel = _rel(package_root(pkg))
    if rel != ".":
        return [rel]
    return [".", ":(exclude)docs", ":(exclude).dev-team", ":(exclude).claude"]


def read_integration(pkg: str) -> dict[str, object] | None:
    """The package's integration record parsed, current or not; None when absent or unreadable.

    Keys: n (the header's run), commit, clean (the `tree:` line reads `clean`), result (the text
    after `result: ` on the last non-empty line), reopens, unowned and unplaced (the `; `-separated
    values of those lines, `none` read as empty).
    """
    try:
        lines = integration_path(pkg).read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    head = INTEGRATION_HEADER.match(lines[0]) if lines else None
    if head is None:
        return None

    def value(key: str) -> str:
        return next((line[len(key) + 1:].strip() for line in lines if line.startswith(f"{key}:")), "")

    def items(key: str) -> list[str]:
        return [v.strip() for v in value(key).split(";") if v.strip() and v.strip() != "none"]

    last = next((line for line in reversed(lines) if line.strip()), "")
    return {
        "n": int(head.group(1)),
        "commit": value("commit"),
        "clean": value("tree") == "clean",
        "result": last[len("result: "):].strip() if last.startswith("result: ") else "",
        "reopens": items("reopens"),
        "unowned": items("unowned"),
        "unplaced": items("unplaced"),
    }


def integration_state(pkg: str) -> dict[str, object]:
    """Where the package's integration check stands; the module docstring's **Integration.**.

    Keys: kind (`needed`, `pass`, `fail` or `incomplete`), n (the record's run, 0 without a
    current one), record (its path, or None), sections (the package's sections its `reopens:`
    line names, in the Sections table's order), unowned, unplaced, cap (`fail` naming a section
    at run 3 or later).
    """
    out: dict[str, object] = {"kind": "needed", "n": 0, "record": None, "sections": [], "unowned": [],
                              "unplaced": [], "cap": False}
    rec = read_integration(pkg)
    if rec is None or not rec["clean"]:
        return out
    sha = str(rec["commit"])
    if not re.fullmatch(r"[0-9a-f]{7,40}", sha) or git("rev-parse", "--verify", "-q", f"{sha}^{{commit}}") is None:
        return out
    if changed_since(sha, *integration_pathspec(pkg)) is not None:
        return out
    result = str(rec["result"])
    current = {**out, "n": rec["n"], "record": integration_path(pkg)}
    if result.startswith("pass"):
        return {**current, "kind": "pass"}
    if result.startswith("incomplete"):
        return {**current, "kind": "incomplete"}
    if not result.startswith("fail"):
        return out
    named = [r["section"] for r in sections(pkg) if r["section"] in rec["reopens"]]  # type: ignore[operator]
    return {**current, "kind": "fail", "sections": named, "unowned": rec["unowned"], "unplaced": rec["unplaced"],
            "cap": bool(named) and int(rec["n"]) >= 3}  # type: ignore[call-overload]


def integration_line(state: dict[str, object]) -> str:
    """The package block's `integration:` line for an `integration_state`."""
    record = _rel(state["record"]) if state["record"] else ""  # type: ignore[arg-type]
    if state["kind"] == "needed":
        return "integration: needed"
    if state["kind"] == "pass":
        return f"integration: pass ({record})"
    if state["kind"] == "incomplete":
        return f"integration: run {state['n']} incomplete ({record})"
    named = ", ".join(state["sections"]) or "no section named"  # type: ignore[arg-type]
    return f"integration: run {state['n']} fail (reopens: {named})" + (" (cap)" if state["cap"] else "")


def section_integration_record(pkg: str, section: str) -> Path | None:
    """The integration record while it is current, fails and names the section on its `reopens:`
    line: `--inputs`' Review carries it."""
    state = integration_state(pkg)
    if state["kind"] == "fail" and section in state["sections"]:  # type: ignore[operator]
        return state["record"]  # type: ignore[return-value]
    return None


def _section_rev(pkg: str, section: str) -> str | None:
    p = _paths(pkg, section)
    return _rev(p["design"], p["intent"], p["unit"], p["readme"], *p["code"])  # type: ignore[arg-type]


def package_table(pkg: str) -> list[dict[str, object]]:
    """One dict per section: section, state, evidence, ready, round, spec, commit."""
    rows = sections(pkg)
    paths = paths_state(pkg)
    integration = integration_state(pkg)
    states = {r["section"]: section_state(pkg, r["section"], paths, integration) for r in rows}
    names = set(states)
    out = []
    for r in rows:
        sec = r["section"]
        state, ev = states[sec]
        deps = [d for d in _names(r["depends on"]) if d in names and d != sec]
        early = sec == "surface" and state in ("PLAN", "DESIGN", "TEST") and has_call_paths(pkg)
        ready = state not in ("DONE", "BLOCKED") and (early or all(states[d][0] == "DONE" for d in deps))
        n = rounds(pkg, sec)
        spec = ", ".join(sorted({e["kind"] for e in live_spec_changes(pkg, sec)})) or "—"
        out.append({"section": sec, "state": state, "evidence": ev, "ready": ready,
                    "round": n, "spec": spec, "commit": _short(_section_rev(pkg, sec))})
    return out


# ---------------------------------------------------------------------------------------------
# next
# ---------------------------------------------------------------------------------------------


def _to_sync(pkg: str) -> bool:
    approved = [e for e in deviation_entries(pkg) if e["kind"] == "deviation" and _status(e) == "approved"]
    return bool(approved or open_changes(pkg))


def next_command(pkg: str, table: list[dict[str, object]] | None = None) -> str:
    """The one command to type next for pkg, every name filled in."""
    if not contract_path(pkg).exists():
        return f"/dev-team:plan-package {pkg}"
    table = package_table(pkg) if table is None else table
    for r in table:
        if r["state"] == "BLOCKED" and str(r["evidence"]).startswith("D"):
            d = str(r["evidence"]).split(",")[0].split()[0]
            return f"answer {d} in docs/decisions.md, then /dev-team:run-package {pkg}"
    for r in table:
        if r["state"] == "BLOCKED" and str(r["evidence"]).startswith("gate "):
            return (f"/dev-team:run-package {pkg} {r['section']} --step IMPLEMENT (run it again) or "
                    f"/dev-team:run-package {pkg} {r['section']} --step REVIEW (review anyway)")
    for r in table:
        if r["state"] == "BLOCKED":
            return f"/dev-team:run-package {pkg} {r['section']} --step REVIEW (one more round) or /dev-team:run-package {pkg} --defer"
    if any(r["ready"] for r in table):
        return f"/dev-team:run-package {pkg}"
    if any(r["state"] != "DONE" for r in table):
        return f"/dev-team:run-package {pkg}"
    if shipped_line(pkg, table) == "shipped: no (surface check FAIL)":
        return f"correct the README rows status.py --surface {pkg} names, then /dev-team:run-package {pkg}"
    if integration_state(pkg)["kind"] != "pass":
        return f"/dev-team:run-package {pkg}"
    paths = paths_state(pkg)
    if paths["kind"] == "round" and paths["cap"]:
        return f"/dev-team:run-package {pkg} or /dev-team:run-package {pkg} --defer"
    if paths["kind"] != "approved":
        return f"/dev-team:run-package {pkg}"
    if _to_sync(pkg):
        return f"/dev-team:sync-plan {pkg}"
    others = [name for name, _ in packages() if name != pkg]
    for other in others:
        if contract_path(other).exists() and any(r["state"] != "DONE" for r in package_table(other)):
            return f"/dev-team:run-package {other}"
    for other in others:
        if not contract_path(other).exists():
            return f"/dev-team:plan-package {other}"
    return "/dev-team:finalize-project"


CI_WORKFLOW = ".github/workflows/ci.yml"


def ci_commands() -> list[str]:
    """The commands the CI workflow must run: the Floor and Enforced rows of
    `docs/constraints.md`, else the Toolchain's lines less a trailing `# comment`, `<pkg>` written
    `$pkg` (the workflow's loop variable over the packages); each once, in order."""
    if (DOCS / "constraints.md").exists():
        cmds = [cmd for heading, _, cmd, _ in constraints_rows("$pkg") if heading != "Measured"]
    else:
        cmds = [re.sub(r"\s+#.*$", "", c).replace("<pkg>", "$pkg") for c in toolchain_commands()]
    return list(dict.fromkeys(cmds))


def ci_needed() -> list[str]:
    """What the CI workflow lacks: `no .github/workflows/ci.yml`, or the one reason naming every
    `ci_commands` line its text does not hold verbatim; [] when nothing."""
    f = ROOT / CI_WORKFLOW
    try:
        text = f.read_text()
    except (OSError, UnicodeDecodeError):
        return [f"no {CI_WORKFLOW}"]
    missing = [c for c in ci_commands() if c not in text]
    return [f"{CI_WORKFLOW} lacks " + "; ".join(f"`{c}`" for c in missing)] if missing else []


def scaffold_needed(pkg: str) -> list[str]:
    """What the SCAFFOLD step must create before pkg is built in: [] when nothing."""
    root_py = ROOT / "pyproject.toml"
    if not root_py.exists():
        return ["no root pyproject.toml"]
    try:
        is_workspace = "[tool.uv.workspace]" in root_py.read_text()
    except OSError:
        return []
    if not is_workspace:
        return []
    pkg_py = package_root(pkg) / "pyproject.toml"
    return ([f"no {_rel(pkg_py)}"] if not pkg_py.exists() else []) + ci_needed()


def shipped_line(pkg: str, table: list[dict[str, object]]) -> str:
    """The block's `shipped:` line: yes only when `surface` is DONE, `--surface <pkg>` passes, the
    integration check passes on the package's current code and the paths review approves. The
    check runs only once `surface` is DONE."""
    surface = next((r for r in table if r["section"] == "surface"), None)
    if surface is None:
        return "shipped: no (no surface row)"
    if surface["state"] != "DONE":
        return f"shipped: no (surface {surface['state']})"
    if surface_check(pkg)[0] != "PASS":
        return "shipped: no (surface check FAIL)"
    integration = integration_state(pkg)
    if integration["kind"] == "needed":
        return "shipped: no (integration needed)"
    if integration["kind"] != "pass":
        return f"shipped: no (integration run {integration['n']} {integration['kind']})"
    paths = paths_state(pkg)
    if paths["kind"] == "approved":
        return "shipped: yes"
    if paths["kind"] == "needed":
        return "shipped: no (paths needed)"
    return f"shipped: no (paths round {paths['n']})"


def package_report(pkg: str) -> list[str]:
    lines = [f"## {pkg}", "section · state · evidence · ready · round · open spec-change · last commit"]
    if not contract_path(pkg).exists():
        lines += [f"shipped: no (no {_rel(contract_path(pkg))})", f"next: {next_command(pkg)}"]
        return lines
    table = package_table(pkg)
    for r in table:
        lines.append(" · ".join([str(r["section"]), str(r["state"]), str(r["evidence"]),
                                 "yes" if r["ready"] else "no", str(r["round"] or "—"),
                                 str(r["spec"]), str(r["commit"])]))
    if needed := scaffold_needed(pkg):
        lines.append(f"scaffold: needed ({', '.join(needed)})")
    if all(r["state"] == "DONE" for r in table) or integration_path(pkg).exists():
        lines.append(integration_line(integration_state(pkg)))
    if all(r["state"] == "DONE" for r in table) or paths_reports(pkg):
        lines.append(paths_line(paths_state(pkg)))
    lines.append(shipped_line(pkg, table))
    lines.append(f"next: {next_command(pkg, table)}")
    return lines


# ---------------------------------------------------------------------------------------------
# docs/constraints.md and the Toolchain
# ---------------------------------------------------------------------------------------------


def constraints_rows(pkg: str) -> list[tuple[str, str, str, str]]:
    """(heading, dimension, command with <pkg> filled, scope) over Floor, Enforced and Measured."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    text = f.read_text()
    out = []
    for heading in ("Floor", "Enforced", "Measured"):
        for row in table_rows(_block(text, heading), ("command", "scope")):
            cmd = col(row, "command")
            if cmd:
                dim = col(row, "check") or col(row, "dimension")
                out.append((heading, dim, cmd.replace("<pkg>", pkg), col(row, "scope").lower() or "package"))
    return out


def guarded_items() -> list[str]:
    """The Guarded bullet texts of docs/constraints.md."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    return [m.group(1).strip() for m in re.finditer(r"^\s*[-*]\s+(.+)$", _block(f.read_text(), "Guarded"), re.M)]


def exceptions_rows() -> list[dict[str, str]]:
    """The Exceptions table rows of docs/constraints.md."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    return table_rows(_block(f.read_text(), "Exceptions"), ("path", "check"))


def toolchain_commands() -> list[str]:
    """One command per line of every fenced block under architecture.md's Toolchain heading."""
    f = DOCS / "architecture.md"
    if not f.exists():
        return []
    body = _item(f.read_text(), "Toolchain")
    out = []
    for block in re.findall(r"^\s*```[^\n]*\n(.*?)^\s*```", body, re.M | re.S):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


# ---------------------------------------------------------------------------------------------
# Subagent transcripts: which section an agent run is for
# ---------------------------------------------------------------------------------------------


def _transcript_target(path: Path | str) -> tuple[str, str] | str | None:
    """(pkg, section), "scaffold", or "none" from a transcript's first `user` record; None when
    the file cannot be read."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(rec, dict) or rec.get("type") != "user":
                    continue
                content = (rec.get("message") or {}).get("content", "")
                if isinstance(content, list):
                    content = "\n".join(str(c.get("text", "")) for c in content if isinstance(c, dict))
                lines = str(content).splitlines()
                if any(ln.startswith("Scaffold:") for ln in lines):
                    return "scaffold"
                for ln in lines:
                    if m := re.match(r"^Section:\s+([\w.-]+)/([\w.-]+)\s*$", ln):
                        return m.group(1), m.group(2)
                return "none"
    except OSError:
        return None
    return "none"


def section_from_transcript(path: Path | str) -> tuple[str, str] | None:
    """(pkg, section) from the first `Section: <pkg>/<section>` line of a subagent transcript's
    first `user` record (the spawn prompt, verbatim — F2); None for a `Scaffold:` run, no
    `Section:` line, or an unreadable file."""
    target = _transcript_target(path)
    return target if isinstance(target, tuple) else None


def subagent_transcript(event: dict) -> Path | None:
    """The subagent transcript a hook event belongs to: `agent_transcript_path` when the event
    carries it (SubagentStop), else derived from `transcript_path` and `agent_id` (F1)."""
    if event.get("agent_transcript_path"):
        return Path(event["agent_transcript_path"])
    tp, aid = event.get("transcript_path"), event.get("agent_id")
    if tp and aid:
        return Path(tp).with_suffix("") / "subagents" / f"agent-{aid}.jsonl"
    return None


def cached_section(event: dict) -> tuple[str, str] | None:
    """section_from_transcript for a hook event, cached per agent under
    `${CLAUDE_PLUGIN_DATA}/section/<agent_id>` (else `<cwd>/.dev-team/section/<agent_id>`) as
    `<pkg>/<section>`, `scaffold` or `none`. An unreadable transcript is not cached."""
    aid = event.get("agent_id")
    base = Path(os.environ["CLAUDE_PLUGIN_DATA"]) if os.environ.get("CLAUDE_PLUGIN_DATA") else Path(event.get("cwd") or ROOT) / ".dev-team"
    cache = base / "section" / str(aid) if aid else None
    if cache is not None:
        try:
            value = cache.read_text().strip()
        except OSError:
            value = ""
        if value:
            pkg, _, sec = value.partition("/")
            return (pkg, sec) if sec else None
    path = subagent_transcript(event)
    target = _transcript_target(path) if path else None
    if target is None:
        return None
    if cache is not None:
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text("/".join(target) if isinstance(target, tuple) else target)
        except OSError:
            pass
    return target if isinstance(target, tuple) else None


# ---------------------------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------------------------


def run_gate(pkg: str | None) -> list[str]:
    """Reasons a run may not start; empty when it may."""
    if git("rev-parse", "--is-inside-work-tree") is None:
        return ["not a git repository; git init, create a branch, and re-run"]
    fails = []
    branch = git("branch", "--show-current") or ""
    if branch in ("main", "master"):
        fails.append(f"on `{branch}`; create a feature branch and re-run")
    # -z: NUL-separated and unquoted, read unstripped. A rename or copy entry is followed by
    # its source path, skipped.
    raw = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    entries = iter(raw.split("\0"))
    dirty = []
    for entry in entries:
        if len(entry) < 4:
            continue
        if entry[0] in "RC":
            next(entries, None)
        path = entry[3:]
        if not any(path == e or (e.endswith("/") and path.startswith(e)) for e in BASELINE_EXEMPT):
            dirty.append(path)
    if dirty:
        fails.append(f"uncommitted changes outside the user-edited files: {', '.join(dirty)}; commit or stash them and re-run")
    plugin = Path(__file__).resolve().parents[3]
    for r in unsynced_inboxes():
        fails.append(f"unsynced inbox — {r}; run python3 {plugin}/hooks/sync_decisions.py --all and commit it")
    if pkg and not contract_path(pkg).exists():
        fails.append(f"{pkg}: missing docs/packages/{pkg}/contract.md — run /dev-team:plan-package {pkg}")
    if pkg and contract_path(pkg).exists():
        for r in sections(pkg):
            stages = [t for k, t in _sources(r.get("source", "")) if k == "stage"]
            if stages and not _names(r.get("depends on", "")):
                fails.append(f"{pkg}/{r['section']}: stage:{stages[0]} has no depends on; nothing produces its data")
    for f in sorted((DOCS / "sources").glob("*.sample.json")):
        doc = f.with_name(f.name.removesuffix(".sample.json") + ".md")
        text = doc.read_text() if doc.exists() else ""
        if text and STAGE_TITLE.match(text.splitlines()[0]) and f.stat().st_size > 200 * 1024:
            fails.append(f"{_rel(f)}: {f.stat().st_size // 1024} KB, over 200 KB; keep five rows per kind")
    return fails


def _dunder_all(init: Path) -> set[str] | None:
    try:
        mod = ast.parse(init.read_text())
    except (OSError, SyntaxError):
        return None
    for node in mod.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets) and node.value is not None:
            try:
                return set(ast.literal_eval(node.value))
            except ValueError:
                return None
    return set()


def _name_cell(row: dict[str, str]) -> str:
    """An interface.md **Public names** row's name: the first backticked span of its `name` cell
    (`` `Trade` (`models.py`) `` is `Trade`), else the cell up to its first `(`. A section
    README's rows are read by `_name_cells`."""
    raw = next((v for h, v in row.items() if "name" in h), "")
    m = re.match(r"\s*`([^`]+)`", raw)
    return (m.group(1) if m else raw.split("(")[0]).strip("`* ").strip()


ONE_NAME = re.compile(r"^\s*`[A-Za-z_]\w*`\s*$")


def _name_cells(row: dict[str, str]) -> tuple[list[str], str | None]:
    """A README row's names: every backticked span of its `name` cell that is a Python identifier,
    and a reason when the cell is not exactly one backticked identifier, else None.

    One exported name per row: `` `load_trades`, `Trade` `` and `` `Loader.load` `` each give a
    reason, and so does a file hint, `` `load_trades` (`__init__.py`) ``.
    """
    raw = next((v for h, v in row.items() if "name" in h), "")
    names = [s for s in re.findall(r"`([^`]+)`", raw) if s.isidentifier()]
    reason = None if ONE_NAME.match(raw) else f"{raw.strip()}: name cell is not one backticked identifier"
    return names, reason


def _public_intent(pkg: str) -> str | None:
    """The body of the contract's **Public surface (intent)** item, or None when it has none."""
    f = contract_path(pkg)
    if not f.exists():
        return None
    text = f.read_text()
    body = _item(text, "Public surface (intent)") or _item(text, "Public surface")
    if not body:
        return None
    lines = body.splitlines()
    if lines and lines[0].lstrip().startswith("#"):  # the heading line itself names nothing
        lines = lines[1:]
    return "\n".join(lines)


def has_call_paths(pkg: str) -> bool:
    """True when the package contract has a `## Call paths` heading (2.6), whatever its body."""
    f = contract_path(pkg)
    return f.exists() and bool(_item(f.read_text(), "Call paths"))


CALL_PATH_COMMAND = re.compile(r"^\s*- `(?P<cmd>[^`]+)` \(budget (?P<n>\d+)(?:, D\d+)?\)")


def call_paths(pkg: str) -> dict[str, dict[str, object]] | None:
    """The contract's Call paths: command -> {"budget": int, "paths": [{"kind", "frames", "effect"}]};
    None without the heading, {} for `- none (no commands)`.

    `frames` is `[(k, "<owner>.<name>"), …]` in the line's order; `effect` is the last backticked
    token on the path line when no `<k> ` precedes it, else None.
    """
    if not has_call_paths(pkg):
        return None
    return _call_path_entries(_item(contract_path(pkg).read_text(), "Call paths"))


def _call_path_entries(text: str) -> dict[str, dict[str, object]]:
    """The Call paths entries in text, as `call_paths` returns them.

    A path is a bullet indented deeper than its command's line; a shallower bullet ends the
    entry, so the entries can be read out of a change file's nested **Contract changes**. A
    command listed twice keeps its last entry: a change file gives the entry `from` and then
    `to`.
    """
    out: dict[str, dict[str, object]] = {}
    current: dict[str, object] | None = None
    indent = 0
    for line in text.splitlines():
        m = CALL_PATH_COMMAND.match(line)
        if m:
            current = {"budget": int(m.group("n")), "paths": []}
            out[m.group("cmd")] = current
            indent = len(line) - len(line.lstrip())
            continue
        bullet = re.match(r"^(\s*)- (.*)$", line)
        if current is None or not bullet:
            continue
        if len(bullet.group(1)) <= indent:
            current = None
            continue
        body = bullet.group(2)
        tokens = list(re.finditer(r"`([^`]+)`", body))
        last = tokens[-1] if tokens else None
        effect = last.group(1) if last and not re.search(r"\d+ $", body[: last.start()]) else None
        current["paths"].append({"kind": body.partition(":")[0].strip(),  # type: ignore[union-attr]
                                 "frames": re.findall(r"(\d+) `([^`]+)`", body), "effect": effect})
    return out


def _contract_changes(text: str) -> str:
    """A change file's **Contract changes**, through its `###` groups, up to **Downstream impact**."""
    lines = text.splitlines()

    def at(name: str, after: int = 0) -> int | None:
        pattern = rf"\s*(#+\s*(\d+\.\s*)?{re.escape(name)}\b|\d+\.\s*\*\*{re.escape(name)}\*\*)"
        return next((i for i in range(after, len(lines)) if re.match(pattern, lines[i])), None)

    start = at("Contract changes")
    if start is None:
        return ""
    end = at("Downstream impact", start + 1)
    return "\n".join(lines[start:end])


def change_call_paths(pkg: str) -> dict[str, tuple[dict[str, object], Path]]:
    """command -> (entry, change file) for each Call paths entry an open change file naming pkg
    gives under **Contract changes**; the first such file in path order wins."""
    out: dict[str, tuple[dict[str, object], Path]] = {}
    for c in open_changes(pkg):
        path: Path = c["path"]  # type: ignore[assignment]
        for command, entry in _call_path_entries(_contract_changes(path.read_text())).items():
            out.setdefault(command, (entry, path))
    return out


def surface_names(pkg: str, section: str) -> tuple[str, list[str]]:
    """(PASS | FAIL | n/a, reasons): one section README's **Entry points and interfaces** rows,
    each name cell exactly one backticked identifier, and each `Public: yes` name one the
    contract's **Public surface (intent)** names as a whole word."""
    readme: Path = _paths(pkg, section)["readme"]  # type: ignore[assignment]
    if not readme.exists():
        return "n/a", []
    intent = _public_intent(pkg)
    fails = []
    for er in table_rows(_item(readme.read_text(), "Entry points and interfaces"), ("name",)):
        names, reason = _name_cells(er)
        if reason:
            fails.append(reason)
        if intent is not None and col(er, "public").lower().startswith("yes"):
            for name in names:
                if not re.search(rf"(?<!\w){re.escape(name)}(?!\w)", intent):
                    fails.append(f"{name}: Public: yes, not in the contract's Public surface (intent)")
    return ("FAIL" if fails else "PASS"), fails


def surface_check(pkg: str) -> tuple[str, list[str]]:
    """(PASS | FAIL | n/a, reasons): __all__ vs interface.md Public names vs READMEs' Public: yes rows, and lazy import."""
    iface = DOCS / "packages" / pkg / "interface.md"
    if not iface.exists():
        return "n/a", []
    fails = []
    root = package_root(pkg)
    rows = sections(pkg)
    surface_row = next((r for r in rows if r["section"] == "surface"), None)
    top = ROOT / (surface_row["path"] if surface_row else _rel(root / "src" / pkg))
    all_names = _dunder_all(top / "__init__.py")
    if all_names is None:
        fails.append(f"no readable __all__ in {_rel(top / '__init__.py')}")
        all_names = set()
    iface_rows = table_rows(_item(iface.read_text(), "Public names"), ("name",))
    public = {_name_cell(r) for r in iface_rows if _name_cell(r)}
    # A name whose providing module lies outside every other section (a pipeline, the CLI) is the
    # surface section's own: no section README can carry its row.
    section_mods = []
    for r in rows:
        if r["section"] != "surface":
            try:
                section_mods.append(".".join((ROOT / r["path"]).resolve().relative_to(top.resolve().parent).parts))
            except ValueError:
                section_mods.append(f"{pkg}.{r['section']}")
    surface_own = {_name_cell(r) for r in iface_rows
                   if (mod := col(r, "providing")) and not any(mod == m or mod.startswith(m + ".") for m in section_mods)}
    readmes: set[str] = set()
    for r in rows:
        if r["section"] == "surface":
            continue
        f = ROOT / r["path"] / "README.md"
        if f.exists():
            for er in table_rows(_item(f.read_text(), "Entry points and interfaces"), ("name",)):
                names, reason = _name_cells(er)
                if reason:
                    fails.append(f"{pkg}/{r['section']} README: {reason}")
                # Every name the cell holds counts, so a grouped cell's second name is not lost.
                if col(er, "public").lower().startswith("yes"):
                    readmes.update(names)
    for a, an, b, bn in ((all_names, "__all__", public, "interface.md Public names"),
                         (public - surface_own, "interface.md Public names", readmes, "README Public: yes rows"),
                         (readmes, "README Public: yes rows", all_names, "__all__")):
        for name in sorted(a - b):
            fails.append(f"{name}: in {an}, not in {bn}")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": os.pathsep.join(filter(None, [str(top.parent), os.environ.get("PYTHONPATH", "")]))}
    try:
        res = subprocess.run([sys.executable, "-X", "importtime", "-c", f"import {pkg}"],
                             capture_output=True, text=True, cwd=ROOT, env=env, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fails.append(f"import {pkg} did not run: {exc}")
    else:
        if res.returncode != 0:
            last = (res.stderr.strip().splitlines() or ["?"])[-1]
            fails.append(f"import {pkg} failed: {last}")
        else:
            eager = sorted({m.group(1) for m in re.finditer(rf"\|\s*({re.escape(pkg)}\.[\w.]+)\s*$", res.stderr, re.M)
                            if m.group(1).split(".")[1] in {r['section'] for r in rows if r['section'] != 'surface'}})
            for mod in eager:
                fails.append(f"import {pkg} loads section module {mod} (not lazy)")
    return ("FAIL" if fails else "PASS"), fails


PROPERTY_DECORATORS = ("property", "cached_property", "setter", "getter", "deleter")


def _is_test_file(rel: str) -> bool:
    """True for a test file: a `tests` directory in its path, or a `test_*` / `*_test.py` name."""
    parts = rel.split("/")
    return "tests" in parts[:-1] or parts[-1].startswith("test_") or parts[-1].endswith("_test.py")


def _py_files(top: Path, skip: tuple[str, ...] = ()) -> list[str]:
    """Repo-relative paths of the non-test `.py` files under top, none under a path in skip."""
    if not top.is_dir():
        return []
    out = []
    for f in sorted(top.rglob("*.py")):
        rel = _rel(f)
        if not _is_test_file(rel) and not any(rel.startswith(s.rstrip("/") + "/") for s in skip):
            out.append(rel)
    return out


def _parse(rel: str) -> ast.Module | None:
    try:
        return ast.parse((ROOT / rel).read_text())
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return None


def _statements(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """The statements inside fn, nested ones included, its leading docstring not counted."""
    n = sum(1 for node in ast.walk(fn) if isinstance(node, ast.stmt)) - 1
    first = fn.body[0] if fn.body else None
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        n -= 1
    return n


def _is_property(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for d in fn.decorator_list:
        if (isinstance(d, ast.Name) and d.id in PROPERTY_DECORATORS) or (
                isinstance(d, ast.Attribute) and d.attr in PROPERTY_DECORATORS):
            return True
    return False


def _definitions(tree: ast.Module) -> list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.AST]]:
    """(function, its nearest enclosing module, class or function) for every def in tree."""
    out = []
    stack: list[tuple[ast.AST, ast.AST]] = [(tree, tree)]
    while stack:
        node, scope = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append((child, scope))
                stack.append((child, child))
            elif isinstance(child, ast.ClassDef):
                stack.append((child, child))
            else:
                stack.append((child, scope))
    return out


def _loads(tree: ast.AST, name: str, attribute: bool) -> list[ast.AST]:
    """Every load of name in tree: `ast.Attribute` nodes whose attr it is, or `ast.Name` nodes."""
    if attribute:
        return [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == name
                and isinstance(n.ctx, ast.Load)]
    return [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, ast.Load)]


def _imported_as(tree: ast.Module, name: str) -> list[str]:
    """The names a `from … import name` in tree binds it to."""
    return [a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
            for a in n.names if a.name == name]


def _references(fn: ast.FunctionDef | ast.AsyncFunctionDef, scope: ast.AST, rel: str,
                trees: dict[str, ast.Module]) -> list[ast.AST]:
    """Every reference to fn's name the shape check counts, by the note's rules: by name, never
    resolved, so a second caller it cannot place still counts."""
    name = fn.name
    if isinstance(scope, ast.ClassDef):
        return [n for tree in trees.values() for n in _loads(tree, name, attribute=True)]
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _loads(scope, name, attribute=False)
    refs = _loads(trees[rel], name, attribute=False)
    for other, tree in trees.items():
        if other != rel:
            refs += [n for bound in _imported_as(tree, name) for n in _loads(tree, bound, attribute=False)]
        refs += _loads(tree, name, attribute=True)
    return refs


def shape_base(pkg: str, section: str) -> str:
    """The commit the shape check reads added lines from: `review_base` when a review round
    covers the section; else, for a design whose mode word is `document`, the commit that added
    the design; else the empty tree."""
    base = review_base(pkg, section)
    if base != EMPTY_TREE:
        return base
    design: Path = _paths(pkg, section)["design"]  # type: ignore[assignment]
    if _design_mode(design) == "document":
        added = git("log", "--diff-filter=A", "--format=%H", "-1", "--", _rel(design))
        if added:
            return added
    return EMPTY_TREE


def _is_options_bag(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True when fn's `**` parameter is annotated `Unpack[...]` or `<module>.Unpack[...]`."""
    annotation = fn.args.kwarg.annotation if fn.args.kwarg else None
    if not isinstance(annotation, ast.Subscript):
        return False
    value = annotation.value
    return (isinstance(value, ast.Name) and value.id == "Unpack") or (
        isinstance(value, ast.Attribute) and value.attr == "Unpack")


def _own_defs(node: ast.AST) -> set[str]:
    """The names of the functions defined directly in a function's body, not inside a nested
    function, lambda or class."""
    names: set[str] = set()
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(child.name)
        elif not isinstance(child, (ast.Lambda, ast.ClassDef)):
            stack.extend(ast.iter_child_nodes(child))
    return names


def _indirect_count(tree: ast.Module) -> int:
    """The module's lambdas passed as an argument, names of nested functions passed as an
    argument, and calls through a subscript."""
    n = 0
    stack: list[tuple[ast.AST, frozenset[str]]] = [(tree, frozenset())]
    while stack:
        node, closures = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            closures = closures | _own_defs(node)
        if isinstance(node, ast.Call):
            n += isinstance(node.func, ast.Subscript)
            for arg in [*node.args, *(k.value for k in node.keywords)]:
                n += isinstance(arg, ast.Lambda) or (isinstance(arg, ast.Name) and arg.id in closures)
        stack.extend((child, closures) for child in ast.iter_child_nodes(node))
    return n


def _deepest(graph: _CallGraph, roots: list[str]) -> str:
    """The largest deepest-effect depth over roots, or `none` when no effect lies below any."""
    found = [d for root in roots if (d := graph.effect_depths(root)[1]) is not None]
    return str(max(found)) if found else "none"


def shape_depths(pkg: str, section: str, judged: list[str]) -> list[str]:
    """One `MEASURED shape depth` line per README entry point, or per command for `surface`."""
    if section == "surface":
        scripts = package_scripts(pkg)
        if not scripts:
            return []
        graph = _CallGraph(pkg)
        values = []
        for name, target in scripts.items():
            root = graph.command(target)
            values.append((name, "unresolved" if root is None else _deepest(graph, [root])))
        return [f"MEASURED shape depth {name}: {value}" for name, value in values]
    readme: Path = _paths(pkg, section)["readme"]  # type: ignore[assignment]
    if not readme.exists():
        return []
    rows = table_rows(_item(readme.read_text(), "Entry points and interfaces"), ("name",))
    names = [cells[0] for row in rows if (cells := _name_cells(row)[0])]
    if not names:
        return []
    graph = _CallGraph(pkg)
    modules = [m for m in graph.modules.values() if m.rel in judged]
    out = []
    for name in names:
        value = "unresolved"
        for module in modules:
            if name in module.functions:
                value = _deepest(graph, [graph.fn_for(module.functions[name], module, None, None).key])
            elif name in module.classes:
                methods = [graph.fn_for(item, module, name, None).key for item in module.classes[name].body
                           if isinstance(item, DEFS) and not item.name.startswith("_")]
                value = _deepest(graph, methods)
            else:
                continue
            break
        out.append(f"MEASURED shape depth {name}: {value}")
    return out


SHAPE_KINDS = ("trivial-helper", "options-bag")


def shape_check(pkg: str, section: str) -> list[str]:
    """The section's shape check, the lines the module docstring's **Shape.** lists: a `FAIL
    shape: …` line per trivial single-use helper or options bag whose `def` line was added since
    `shape_base`, then the two `MEASURED` kinds, then `PASS shape` when nothing failed."""
    p = _paths(pkg, section)
    code: list[str] = p["code"]  # type: ignore[assignment]
    spath, nested = code[0], [c.removeprefix(":(exclude)") for c in code[1:]]
    rows = sections(pkg)
    surface_row = next((r for r in rows if r["section"] == "surface"), None)
    top = ROOT / (surface_row["path"] if surface_row else _rel(package_root(pkg) / "src" / pkg))
    judged = _py_files(ROOT / spath, tuple(nested))
    trees = {rel: t for rel in dict.fromkeys([*_py_files(top), *judged]) if (t := _parse(rel)) is not None}
    added = {(path, n) for path, sign, n, _ in diff_lines(shape_base(pkg, section), code) if sign == "+"}
    classes: dict[str, int] = {}
    for tree in trees.values():
        for fn, scope in _definitions(tree):
            if isinstance(scope, ast.ClassDef):
                classes[fn.name] = classes.get(fn.name, 0) + 1
    calls = {id(n.func) for tree in trees.values() for n in ast.walk(tree) if isinstance(n, ast.Call)}
    fails: list[tuple[str, int, int, str]] = []
    for rel in judged:
        if rel not in trees:
            continue
        for fn, scope in _definitions(trees[rel]):
            if (rel, fn.lineno) not in added:
                continue
            name = fn.name
            if _is_options_bag(fn):
                shown = f"{scope.name}.{name}" if isinstance(scope, ast.ClassDef) else name
                fails.append((rel, fn.lineno, SHAPE_KINDS.index("options-bag"), shown))
            if not name.startswith("_") or (name.startswith("__") and name.endswith("__")):
                continue
            if _statements(fn) > 3 or _is_property(fn):
                continue
            if isinstance(scope, ast.ClassDef) and classes.get(name, 0) > 1:
                continue
            refs = _references(fn, scope, rel, trees)
            if len(refs) == 1 and id(refs[0]) in calls:
                fails.append((rel, fn.lineno, SHAPE_KINDS.index("trivial-helper"), name))
    out = [f"FAIL shape: {rel}:{n} {SHAPE_KINDS[kind]} {name}" for rel, n, kind, name in sorted(fails)]
    out.append(f"MEASURED shape indirect: {sum(_indirect_count(trees[rel]) for rel in judged if rel in trees)}")
    out += shape_depths(pkg, section, judged)
    if not fails:
        out.append(f"PASS shape {pkg}/{section}")
    return out


# ---------------------------------------------------------------------------------------------
# Paths: the static call tree of each [project.scripts] command
# ---------------------------------------------------------------------------------------------

LOGGING_LIBRARIES = frozenset({"logging", "loguru", "structlog"})
IO_MODULES = frozenset({"subprocess", "socket", "urllib", "http", "sqlite3", "shutil"})
IO_BUILTINS = frozenset({"open", "print"})
LITERALS = (ast.Constant, ast.JoinedStr, ast.List, ast.Dict, ast.Set, ast.Tuple,
            ast.ListComp, ast.DictComp, ast.SetComp)
DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)
UNRESOLVED_WIDTH = 80

Resolved = tuple[str, object] | None


class _Module:
    """One module of the package as the resolver reads it: its functions, classes, imports,
    name-valued dict literals and module-level names assigned from a call."""

    def __init__(self, name: str, rel: str, source: str, tree: ast.Module, is_init: bool) -> None:
        self.name, self.rel, self.source = name, rel, source
        self.package = name if is_init else name.rpartition(".")[0]
        self.functions = {n.name: n for n in tree.body if isinstance(n, DEFS)}
        self.classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        self.dicts: dict[str, ast.Dict] = {}
        self.assigned_calls: dict[str, ast.Call] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
            elif isinstance(node, ast.AnnAssign):
                target = node.target
            else:
                continue
            if not isinstance(target, ast.Name):
                continue
            if isinstance(node.value, ast.Dict) and node.value.values and all(
                    isinstance(v, ast.Name) for v in node.value.values):
                self.dicts[target.id] = node.value
            elif isinstance(node.value, ast.Call):
                self.assigned_calls[target.id] = node.value
        # local name -> (module, attribute), attribute None for `import a.b`. A module-level
        # import wins over the same name imported inside a function.
        self.imports: dict[str, tuple[str, str | None]] = {}
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        top_ids = {id(n) for n in top}
        nested = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and id(n) not in top_ids]
        for node in [*top, *nested]:
            if isinstance(node, ast.Import):
                for a in node.names:
                    local = a.asname or a.name.split(".")[0]
                    self.imports.setdefault(local, (a.name if a.asname else local, None))
            else:
                source_module = self.absolute(node)
                for a in node.names:
                    if a.name != "*":
                        self.imports.setdefault(a.asname or a.name, (source_module, a.name))

    def absolute(self, node: ast.ImportFrom) -> str:
        """The dotted module a `from … import` names, a relative one resolved against this
        module's package."""
        if not node.level:
            return node.module or ""
        parts = self.package.split(".")
        base = parts[: len(parts) - (node.level - 1)]
        return ".".join([*base, *([node.module] if node.module else [])])


class _Fn:
    """A function, method, nested function or lambda: a frame of the call tree, with the names
    its own body defines (nested functions, parameters, assigned variables)."""

    def __init__(self, node: ast.AST, name: str, module: _Module, cls: str | None, parent: _Fn | None) -> None:
        self.node, self.name, self.module, self.cls, self.parent = node, name, module, cls, parent
        self.key = f"{module.rel}:{node.lineno}:{node.col_offset}"
        self.line = node.lineno
        # The function's own body: nested functions, lambdas and classes are listed but not
        # entered, since each is a frame (or a scope) of its own.
        stack = list(node.body) if isinstance(node, DEFS) else [node.body]
        self.own: list[ast.AST] = []
        while stack:
            n = stack.pop()
            self.own.append(n)
            if not isinstance(n, (*DEFS, ast.Lambda, ast.ClassDef)):
                stack.extend(ast.iter_child_nodes(n))
        self.nested = {n.name: n for n in self.own if isinstance(n, DEFS)}
        args = node.args
        self.locals = {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg] if a}
        self.locals |= {n.id for n in self.own if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}


class _CallGraph:
    """The package's module index, and the call graph `--paths` prints, built per function on
    first use.

    A name resolves to a pair: ("function", key), ("class", (module, name)), ("module", dotted
    name), ("dict", (module, name)), ("outside", root module), ("logger", None) or ("builtin",
    name); None is a name the resolver does not follow.
    """

    def __init__(self, pkg: str) -> None:
        surface = _row(pkg, "surface")
        top = (ROOT / surface["path"]) if surface else package_root(pkg) / "src" / pkg
        self.root_name = top.name
        self.modules: dict[str, _Module] = {}
        for rel in _py_files(top):
            parts = list((ROOT / rel).relative_to(top.parent).with_suffix("").parts)
            is_init = parts[-1] == "__init__"
            name = ".".join(parts[:-1] if is_init else parts)
            try:
                source = (ROOT / rel).read_text()
                self.modules[name] = _Module(name, rel, source, ast.parse(source), is_init)
            except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
                continue
        # every module and every package above one, `__init__.py` or not
        self.known = {".".join(n.split(".")[:i]) for n in self.modules for i in range(1, n.count(".") + 2)}
        self.fns: dict[str, _Fn] = {}
        self._by_node: dict[int, _Fn] = {}
        self._entries: dict[str, list[dict[str, object]]] = {}
        self._building: set[str] = set()
        self._resolving: set[tuple[str, str]] = set()

    def fn_for(self, node: ast.AST, module: _Module, cls: str | None, parent: _Fn | None) -> _Fn:
        """The one _Fn for node, made on first sight."""
        if id(node) not in self._by_node:
            if isinstance(node, ast.Lambda):
                name = "lambda"
            elif parent is None and cls:
                name = f"{cls}.{node.name}"
            else:
                name = node.name
            fn = _Fn(node, name, module, cls, parent)
            self._by_node[id(node)] = fn
            self.fns[fn.key] = fn
        return self._by_node[id(node)]

    def method(self, module: _Module, cls: str, attr: str, seen: frozenset[tuple[str, str]] = frozenset()) -> str | None:
        """The key of the method attr of class cls, from cls or else its package base classes."""
        node = module.classes[cls]
        for item in node.body:
            if isinstance(item, DEFS) and item.name == attr:
                return self.fn_for(item, module, cls, None).key
        seen = seen | {(module.name, cls)}
        for base in node.bases:
            found = self.resolve(module, None, base)
            if found and found[0] == "class" and found[1] not in seen:
                key = self.method(self.modules[found[1][0]], found[1][1], attr, seen)
                if key:
                    return key
        return None

    def resolve(self, module: _Module, fn: _Fn | None, node: ast.AST) -> Resolved:
        """What the expression node names, read inside fn, or at module level when fn is None."""
        if isinstance(node, ast.Name):
            return self.lookup(fn, node.id) if fn else self.resolve_name(module, node.id, with_builtins=True)
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in ("self", "cls") and fn and fn.cls:
                key = self.method(module, fn.cls, node.attr)
                return ("function", key) if key else None
            return self.attribute(self.resolve(module, fn, node.value), node.attr)
        if isinstance(node, LITERALS):
            return ("builtin", "literal")
        return None

    def lookup(self, fn: _Fn, name: str) -> Resolved:
        """name read inside fn: a function nested in fn or in a function around it; None for any
        other local name (a parameter, an assigned variable); else the module's own name."""
        scope: _Fn | None = fn
        while scope is not None:
            if name in scope.nested:
                return ("function", self.fn_for(scope.nested[name], scope.module, scope.cls, scope).key)
            if name in scope.locals:
                return None
            scope = scope.parent
        return self.resolve_name(fn.module, name, with_builtins=True)

    def resolve_name(self, module: _Module, name: str, *, with_builtins: bool) -> Resolved:
        """name at the top level of module, followed through its imports."""
        if name in module.functions:
            return ("function", self.fn_for(module.functions[name], module, None, None).key)
        if name in module.classes:
            return ("class", (module.name, name))
        if name in module.dicts:
            return ("dict", (module.name, name))
        if name in module.assigned_calls:
            maker = self.resolve(module, None, module.assigned_calls[name].func)
            return ("logger", None) if maker and maker[0] == "outside" and maker[1] in LOGGING_LIBRARIES else None
        if name in module.imports and (module.name, name) not in self._resolving:
            self._resolving.add((module.name, name))
            try:
                return self.binding(*module.imports[name])
            finally:
                self._resolving.discard((module.name, name))
        if with_builtins and hasattr(builtins, name):
            return ("builtin", name)
        return None

    def binding(self, source: str, attr: str | None) -> Resolved:
        """What an import of attr from module source binds, or of source itself when attr is None."""
        if attr is None:
            return ("module", source) if source in self.known else self.outside(source)
        if f"{source}.{attr}" in self.known:
            return ("module", f"{source}.{attr}")
        if source in self.modules:
            return self.resolve_name(self.modules[source], attr, with_builtins=False)
        return self.outside(source)

    def outside(self, source: str) -> Resolved:
        """An import from source, not a module of the package: ("outside", its root module), or
        None when that root is the package's own name (a module the index lacks)."""
        root = source.split(".")[0]
        return ("outside", root) if root and root != self.root_name else None

    def attribute(self, target: Resolved, attr: str) -> Resolved:
        """What `<target>.attr` names."""
        if target is None:
            return None
        kind, value = target
        if kind == "module":
            if f"{value}.{attr}" in self.known:
                return ("module", f"{value}.{attr}")
            return self.resolve_name(self.modules[value], attr, with_builtins=False) if value in self.modules else None
        if kind == "class":
            key = self.method(self.modules[value[0]], value[1], attr)
            return ("function", key) if key else None
        if kind in ("outside", "logger", "builtin"):
            return target
        return None

    def entries(self, fn: _Fn) -> list[dict[str, object]]:
        """fn's children, in the source order of its calls: `{"frame": key, "indirect": bool,
        "under": [keys]}` (under: the callables passed to that callee at this call site) or
        `{"leaf": text, "effect": bool}`."""
        if fn.key in self._entries:
            return self._entries[fn.key]
        self._building.add(fn.key)
        calls = sorted((n for n in fn.own if isinstance(n, ast.Call)), key=lambda c: (c.lineno, c.col_offset))
        out: list[dict[str, object]] = []
        for call in calls:
            callee, own = self.callee(fn, call)
            passed = [self.passed(fn, arg) for arg in [*call.args, *(k.value for k in call.keywords)]]
            passed = [key for key in passed if key and self.worth_printing(key)]
            if callee:
                out.append({"frame": callee, "indirect": False, "under": passed})
            else:
                out += own
                out += [{"frame": key, "indirect": True, "under": []} for key in passed]
        self._building.discard(fn.key)
        self._entries[fn.key] = out
        return out

    def callee(self, fn: _Fn, call: ast.Call) -> tuple[str | None, list[dict[str, object]]]:
        """(the package function call resolves to, or None; the entries it makes otherwise)."""
        module, func = fn.module, call.func
        if isinstance(func, ast.Subscript):
            table = self.resolve(module, fn, func.value)
            if table and table[0] == "dict":
                owner = self.modules[table[1][0]]
                keys: list[str] = []
                for value in owner.dicts[table[1][1]].values:
                    found = self.resolve(owner, None, value)
                    if found and found[0] == "function" and found[1] not in keys:
                        keys.append(found[1])
                if keys:
                    return None, [{"frame": key, "indirect": True, "under": []} for key in keys]
            return None, [self.unresolved(fn, call)]
        found = self.resolve(module, fn, func)
        if found is None or found[0] in ("module", "dict"):
            return None, [self.unresolved(fn, call)]
        kind, value = found
        if kind == "function":
            return value, []
        if kind == "class":
            return self.method(self.modules[value[0]], value[1], "__init__"), []
        effect = (kind == "outside" and (value in IO_MODULES or (
            value not in sys.stdlib_module_names and value not in LOGGING_LIBRARIES))) or (
            kind == "builtin" and isinstance(func, ast.Name) and value in IO_BUILTINS)
        leaf = {"leaf": f"[effect: {ast.unparse(func)}] ({module.rel}:{call.lineno})", "effect": True}
        return None, [leaf] if effect else []

    def unresolved(self, fn: _Fn, call: ast.Call) -> dict[str, object]:
        """The `[unresolved]` leaf for call: its source text on one line, then where it is."""
        text = " ".join((ast.get_source_segment(fn.module.source, call) or ast.unparse(call)).split())
        if len(text) > UNRESOLVED_WIDTH:
            text = text[: UNRESOLVED_WIDTH - 1] + "…"
        return {"leaf": f"{text} ({fn.module.rel}:{call.lineno}) [unresolved]", "effect": False}

    def passed(self, fn: _Fn, arg: ast.AST) -> str | None:
        """The key of the callable arg hands over: a lambda, or a name of a package function."""
        if isinstance(arg, ast.Lambda):
            return self.fn_for(arg, fn.module, fn.cls, fn).key
        found = self.resolve(fn.module, fn, arg) if isinstance(arg, (ast.Name, ast.Attribute)) else None
        return found[1] if found and found[0] == "function" else None

    def worth_printing(self, key: str) -> bool:
        """False for a passed lambda or nested function whose body makes no frame and no leaf."""
        fn = self.fns[key]
        if fn.parent is None or key in self._building:
            return True
        return bool(self.entries(fn))

    def edges(self, key: str) -> list[tuple[str, int, bool]]:
        """(child, depth added, indirect) per frame under key; a callable passed to a callee sits
        under that callee, two levels down."""
        out = []
        for entry in self.entries(self.fns[key]):
            if "frame" in entry:
                out.append((entry["frame"], 1, entry["indirect"]))
                out += [(under, 2, True) for under in entry["under"]]
        return out

    def footer(self, root: str) -> list[str]:
        """The three footer lines, from the call graph rather than the printed tree."""
        first, last = self.effect_depths(root)
        indirect = sum(1 for key in self.reachable(root) for _, _, ind in self.edges(key) if ind)
        return [f"depth to first effect: {'none' if first is None else first}",
                f"deepest effect: {'none' if last is None else last}",
                f"indirect frames: {indirect}"]

    def effect_depths(self, root: str) -> tuple[int | None, int | None]:
        """(shallowest, deepest) depth below root of a frame that makes an effect call, root at
        0 and back edges ignored; None for each when no effect lies below root."""
        makes_effect = {key: any(e.get("effect") for e in self.entries(self.fns[key])) for key in self.reachable(root)}
        dist, heap, first = {root: 0}, [(0, root)], None
        while heap:
            d, key = heapq.heappop(heap)
            if d > dist[key]:
                continue
            if makes_effect[key]:
                first = d
                break
            for child, step, _ in self.edges(key):
                if d + step < dist.get(child, d + step + 1):
                    dist[child] = d + step
                    heapq.heappush(heap, (d + step, child))
        longest: dict[str, int | None] = {}
        on_path: set[str] = set()

        def deepest(key: str) -> int | None:
            on_path.add(key)
            best = 0 if makes_effect[key] else None
            for child, step, _ in self.edges(key):
                if child in on_path:
                    continue
                below = longest[child] if child in longest else deepest(child)
                if below is not None and (best is None or step + below > best):
                    best = step + below
            on_path.discard(key)
            longest[key] = best
            return best

        return first, deepest(root)

    def reachable(self, root: str) -> list[str]:
        seen, stack = [root], [root]
        while stack:
            for child, _, _ in self.edges(stack.pop()):
                if child not in seen:
                    seen.append(child)
                    stack.append(child)
        return seen

    def node(self, key: str, indirect: bool, path: list[str], seen: set[str],
             under: list[str] | tuple[str, ...] = ()) -> dict[str, object]:
        """key's frame as the tree prints it: `{"fn", "mark", "children"}`, the children (frames
        and `{"leaf", "effect"}` leaves) present only the first time key is met, then the
        callables handed to it at this call site."""
        fn = self.fns[key]
        mark = " [indirect]" if indirect else ""
        if key in path:
            mark += " [recursive]"
        elif key in seen:
            mark += " [seen]"
        children: list[dict[str, object]] = []
        expand = key not in path and key not in seen
        path.append(key)
        if expand:
            seen.add(key)
            for entry in self.entries(fn):
                if "leaf" in entry:
                    children.append({"leaf": entry["leaf"], "effect": entry["effect"]})
                else:
                    children.append(self.node(entry["frame"], entry["indirect"], path, seen, entry["under"]))
        children += [self.node(child, True, path, seen) for child in under]
        path.pop()
        return {"fn": fn, "mark": mark, "children": children}

    def tree(self, root: str) -> list[str]:
        """The printed tree below root, one line per frame and leaf, two spaces per level."""
        out: list[str] = []

        def walk(n: dict[str, object], depth: int) -> None:
            if "leaf" in n:
                out.append(f"{'  ' * depth}{n['leaf']}")
                return
            fn = n["fn"]
            out.append(f"{'  ' * depth}{fn.name} ({fn.module.rel}:{fn.line}){n['mark']}")
            for child in n["children"]:
                walk(child, depth + 1)

        walk(self.node(root, False, [], set()), 0)
        return out

    def command(self, target: str) -> str | None:
        """The key of the function a `module:attr` script target names, None when it names none."""
        module_name, _, attr = target.strip().partition(":")
        module = self.modules.get(module_name)
        if module is None or not attr:
            return None
        first, *rest = attr.strip().split(".")
        found = self.resolve_name(module, first, with_builtins=False)
        for part in rest:
            found = self.attribute(found, part)
        return found[1] if found and found[0] == "function" else None


def package_scripts(pkg: str) -> dict[str, str]:
    """The package `pyproject.toml`'s `[project.scripts]` table; empty when it has none."""
    pyproject = package_root(pkg) / "pyproject.toml"
    try:
        return tomllib.loads(pyproject.read_text()).get("project", {}).get("scripts", {})
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _frame_owner(rel: str, pkg: str) -> str:
    """`cli`, `pipelines`, or the section whose path holds rel."""
    surface = _row(pkg, "surface")
    top = (surface["path"] if surface else _rel(package_root(pkg) / "src" / pkg)).rstrip("/")
    if rel == f"{top}/cli.py" or rel.startswith(f"{top}/cli/"):
        return "cli"
    if rel.startswith(f"{top}/pipelines/"):
        return "pipelines"
    found = section_for_path(Path(rel))
    return found[1] if found else "surface"


def against_contract(pkg: str, graph: _CallGraph, root: str | None, command: str) -> list[str]:
    """The comparison lines for one command, per the docstring's **Call paths.** paragraph."""
    changed = change_call_paths(pkg)
    source = ""
    if command in changed:
        entry, path = changed[command]
        source = f" from {_rel(path)}"
    else:
        entries = call_paths(pkg)
        if entries is None:
            return ["contract: no Call paths heading"]
        found = entries.get(command)
        if found is None:
            return [f"contract: no entry for {command}"]
        entry = found
    budget, paths = int(entry["budget"]), entry["paths"]  # type: ignore[arg-type]
    tree = graph.node(root, False, [], set()) if root else None
    width = max([len(f"{k} {frame}") for p in paths for k, frame in p["frames"]] + [1])  # type: ignore[index]

    def where(n: dict[str, object]) -> str:
        fn = n["fn"]
        return f"{fn.name} ({fn.module.rel}:{fn.line})"  # type: ignore[attr-defined]

    def agrees(n: dict[str, object], frame: str) -> bool:
        owner, _, name = frame.partition(".")
        fn = n["fn"]
        return fn.name == name and _frame_owner(fn.module.rel, pkg) == owner  # type: ignore[attr-defined]

    def extra(n: dict[str, object]) -> str:
        return f"    {'-'.ljust(width)}  extra  {where(n)}"

    def below(n: dict[str, object], test) -> list[dict[str, object]] | None:
        """The tree path from n (excluded) down to the first node, depth-first, test accepts."""
        for child in n["children"]:  # type: ignore[union-attr]
            if test(child):
                return [child]
            if "fn" in child:
                found = below(child, test)
                if found:
                    return [child, *found]
        return None

    lines = [f"contract: {command} (budget {budget}){source}"]
    counts = {"match": 0, "extra": 0, "missing": 0}
    # Above the root sits an anchor whose one child is the root, so frame 1 is tried at the
    # root only and a later frame is looked for below the last matched one.
    top = {"children": [tree] if tree else []}
    for p in paths:
        lines.append(f"  {p['kind']}:")
        anchor = top
        for k, frame in p["frames"]:  # type: ignore[union-attr]
            label = f"{k} {frame}".ljust(width)
            if anchor is top:
                hit = [tree] if tree and agrees(tree, frame) else None
                hit = hit if hit or k == "1" else below(top, lambda n, f=frame: "fn" in n and agrees(n, f))
            else:
                hit = below(anchor, lambda n, f=frame: "fn" in n and agrees(n, f))
            if not hit:
                lines.append(f"    {label}  missing")
                counts["missing"] += 1
                continue
            for n in hit[:-1]:
                lines.append(extra(n))
            counts["extra"] += len(hit) - 1
            lines.append(f"    {label}  match  {where(hit[-1])}")
            counts["match"] += 1
            anchor = hit[-1]
        effect = p["effect"] or "—"
        if any(c.get("effect") for c in anchor["children"]):  # type: ignore[union-attr]
            lines.append(f"    effect {effect}  reached")
            continue
        down = below(anchor, lambda n: bool(n.get("effect")))
        if down:
            lines += [extra(n) for n in down[:-1]]
            counts["extra"] += len(down) - 1
            lines.append(f"    effect {effect}  reached through {len(down) - 1} extra frame(s)")
        else:
            lines.append(f"    effect {effect}  not reached")
    first = graph.effect_depths(root)[0] if root else None
    depth = "depth none of" if first is None else f"depth {first} {'past' if first > budget else 'of'}"
    lines.append(f"  summary: {counts['match']} match, {counts['extra']} extra, {counts['missing']} missing; "
                 f"{depth} budget {budget}")
    return lines


def paths_report(pkg: str, against: bool = False) -> list[str]:
    """`--paths <pkg>`: one call tree per `[project.scripts]` command, or `paths: no commands`;
    with against, each followed by its comparison with the contract's **Call paths**."""
    scripts = package_scripts(pkg)
    if not scripts:
        if not against:
            return ["paths: no commands"]
        entries = call_paths(pkg)
        if entries is None:
            return ["paths: no commands", "contract: no Call paths heading"]
        listed = ", ".join(entries) if entries else ""
        return ["paths: no commands", f"contract: entries for {listed}, no command built" if listed
                else "contract: none (no commands)"]
    graph = _CallGraph(pkg)
    blocks = []
    for name, target in scripts.items():
        lines = [f"command: {name} = {target}"]
        root = graph.command(target)
        if target.partition(":")[0].strip() not in graph.modules:
            lines.append("target outside the package")
        elif root is None:
            lines.append("target not found in the package")
        else:
            lines += graph.tree(root)
            lines += graph.footer(root)
        if against:
            lines += against_contract(pkg, graph, root, name)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks).split("\n")


def repo_report() -> list[str]:
    """The repo-wide gap list, six groups, for the documenter's Known gaps."""
    pk, secs, specs, chg = [], [], [], []
    for pkg, _ in packages():
        if not contract_path(pkg).exists():
            pk.append(f"{pkg}: no contract")
            continue
        table = package_table(pkg)
        done = sum(1 for r in table if r["state"] == "DONE")
        shipped = shipped_line(pkg, table)
        if shipped == "shipped: yes":
            pk.append(f"{pkg}: shipped")
        elif shipped == "shipped: no (surface check FAIL)":
            pk.append(f"{pkg}: building ({done}/{len(table)} DONE, surface check FAIL)")
        elif shipped.startswith(("shipped: no (paths ", "shipped: no (integration ")):
            pk.append(f"{pkg}: building ({done}/{len(table)} DONE, {shipped[len('shipped: no ('):-1]})")
        elif not any(_paths(pkg, str(r["section"]))["design"].exists() for r in table):  # type: ignore[union-attr]
            pk.append(f"{pkg}: planned")
        else:
            pk.append(f"{pkg}: building ({done}/{len(table)} DONE)")
        secs += [f"{pkg}/{r['section']}: {r['state']}" for r in table if r["state"] != "DONE"]
        specs += [e["heading"] for r in table for e in live_spec_changes(pkg, str(r["section"]))]
    for c in change_files():
        if str(c["status"]).startswith("open"):
            chg.append(str(c["slug"]))
    decs = [f"D{d['n']}: {d['question']}" for d in decisions() if d["status"].startswith(("open", "deferred"))]
    backlog: dict[str, int] = {}
    fu = DOCS / "followups.md"
    if fu.exists():
        for m in re.finditer(r"^- \[ \]\s*`?([^:`]+?)`?\s*:", fu.read_text(), re.M):
            backlog[m.group(1).strip()] = backlog.get(m.group(1).strip(), 0) + 1
    groups = [("packages", pk), ("sections", secs), ("decisions", decs), ("spec-changes", specs),
              ("changes", chg), ("backlog", [f"{t}: {n}" for t, n in backlog.items()])]
    lines = []
    for label, items in groups:
        lines.append(f"{label}:")
        lines += [f"  - {i}" for i in items] or ["  - none"]
    return lines


def upstream_packages(pkg: str) -> list[str]:
    """The `depends on` names of pkg's row in architecture.md's Packages table."""
    arch = DOCS / "architecture.md"
    if not arch.exists():
        return []
    for row in table_rows(arch.read_text(), ("package", "path")):
        if col(row, "package") == pkg:
            return _names(col(row, "depends"))
    return []


def dependent_packages(pkg: str) -> list[str]:
    """Every other package whose `depends on`, followed through the Packages table, reaches pkg;
    in the table's order. The stop gate runs the finished ones' suites (its regression check)."""
    ups = {name: upstream_packages(name) for name, _ in packages()}
    out = []
    for name, direct in ups.items():
        seen: set[str] = set()
        stack = list(direct)
        while stack and name != pkg:
            dep = stack.pop()
            if dep == pkg:
                out.append(name)
                break
            if dep not in seen:
                seen.add(dep)
                stack += ups.get(dep, [])
    return out


def design_upstream(pkg: str, section: str) -> list[str] | None:
    """The names on the design's `Upstream packages:` line, the first match; `none` gives [].

    None when there is no design or no such line.
    """
    design: Path = _paths(pkg, section)["design"]  # type: ignore[assignment]
    if not design.exists():
        return None
    m = re.search(r"^\**Upstream packages:\**\s*(.*)$", design.read_text(), re.M)
    return _names(m.group(1)) if m else None


def _upstream_interfaces(pkg: str, section: str) -> list[str]:
    """Per upstream package the design's `Upstream packages:` line names (every one when the
    design is missing or has no such line): its interface.md, else `provisional: <contract>`.

    A name on the line that is not in the Packages row's `depends on` is ignored: the line
    narrows the row and cannot widen it.
    """
    named = design_upstream(pkg, section)
    ups = []
    for dep in upstream_packages(pkg):
        if named is not None and dep not in named:
            continue
        iface = DOCS / "packages" / dep / "interface.md"
        ups.append(_rel(iface) if iface.exists() else f"provisional: {_rel(contract_path(dep))}")
    return ups


def dependency_readmes(pkg: str, section: str) -> list[str]:
    """`<path>/README.md` per section in the row's `depends on` that exists, Sections order."""
    row = _row(pkg, section)
    if row is None:
        return []
    deps = set(_names(row["depends on"])) - {section}
    out = []
    for d in sections(pkg):  # Sections order, whatever order the `depends on` cell lists
        readme = ROOT / d["path"] / "README.md"
        if d["section"] in deps and readme.exists():
            out.append(_rel(readme))
    return out


def implementer_inputs(pkg: str, section: str) -> list[str]:
    """The implementer's spawn block for one section, one `<Field>: <value>` line per field.

    The fields and how each resolves are the module docstring's `--inputs` list.
    """
    row = _row(pkg, section) or {}
    rows = {r["section"]: r for r in sections(pkg)}
    p = _paths(pkg, section)
    deps = [f"{rows[d]['path']}/README.md" for d in _names(row.get("depends on", "")) if d in rows and d != section]
    ups = _upstream_interfaces(pkg, section)
    probes = [f"docs/sources/{token}.md" for _, token in _sources(row.get("source", ""))]
    intent: Path = p["intent"]  # type: ignore[assignment]
    n, verdict, _, _ = newest_round(pkg, section)
    review = sorted(_rel(f) for f in _reports(pkg, section).get(n, [])) if verdict in ("request changes", "spec-change") else []
    if (report := section_paths_report(pkg, section)) is not None:
        review.append(_rel(report))
    if (record := section_integration_record(pkg, section)) is not None:
        review.append(_rel(record))
    changes = [_rel(c["path"]) for c in open_changes(pkg, section)]  # type: ignore[arg-type]

    def cell(values: list[str]) -> str:
        return ", ".join(values) or "none"

    return [
        f"Section: {pkg}/{section}",
        f"Design: {_rel(p['design'])}",  # type: ignore[arg-type]
        f"Contract: {_rel(contract_path(pkg))}",
        "Repo contract: docs/architecture.md",
        f"Dependency READMEs: {cell(deps)}",
        f"Upstream interfaces: {cell(ups)}",
        f"Source probes: {cell(probes)}",
        f"Intent tests: {_rel(intent) + '/' if intent.is_dir() else 'none'}",
        f"Review: {cell(review)}",
        f"Round: {n + 1}",
        f"Change file: {cell(changes)}",
        f"Run: run-package {pkg}",
    ]


def _stage_line(pkg: str, token: str) -> str:
    """The contract's **Package conventions** line for a stage, its leading `- ` removed; `none` without one."""
    f = contract_path(pkg)
    body = _block(f.read_text(), "Package conventions") if f.exists() else ""
    for line in body.splitlines():
        line = line.strip().removeprefix("- ").strip()
        if line.startswith(f"`stage:{token}` —"):
            return line
    return "none"


def _next_round(pkg: str, section: str, token: str, built: bool) -> dict[str, object]:
    """The `profile` run `--profile` prints when none is due: the newest round plus one once the
    section has a README, else round 0 — the hand re-profile `--step PROBE` sends."""
    doc = DOCS / "sources" / f"{token}.md"
    lines = _round_lines(doc.read_text(), pkg, section) if doc.exists() else []
    return {"mode": "profile", "round": lines[-1][0] + 1 if built and lines else 0, "revise": "none"}


def _defer_due(pkg: str, section: str, token: str) -> dict[str, object] | None:
    """The `defer` run on a `stage:` source whose newest round line ends `new kinds: …`: that
    line's round and its commit; None otherwise. Same keys as `profile_due`, plus commit."""
    doc = DOCS / "sources" / f"{token}.md"
    lines = _round_lines(doc.read_text(), pkg, section) if doc.exists() else []
    if not lines or not lines[-1][2].startswith("new kinds:"):
        return None
    n, commit, _ = lines[-1]
    return {"mode": "defer", "round": n, "revise": "none", "commit": commit, "evidence": ""}


def profiler_inputs(pkg: str, section: str, defer: bool = False) -> list[str]:
    """The profiler's spawn blocks for one section, blank-line separated; the module docstring's
    `--profile` list is the one list of the fields. Empty for a row with no `stage:` source, and
    with defer for a row with no `stage:` source at `new kinds: …`."""
    row = _row(pkg, section) or {}
    stages = [token for kind, token in _sources(row.get("source", "")) if kind == "stage"]
    built = _paths(pkg, section)["readme"].exists()  # type: ignore[union-attr]
    if defer:
        dues = {token: _defer_due(pkg, section, token) for token in stages}
        stages = [token for token in stages if dues[token] is not None]
    else:
        dues = {token: profile_due(pkg, section, token) or (built_round_due(pkg, section, token) if built else None)
                for token in stages}
    runs = [t for t in stages if dues[t] is not None] or stages
    rows = sections(pkg)
    deps = set(_names(row.get("depends on", ""))) - {section}
    probes: list[str] = []
    for r in rows:  # Sections order, deduplicated
        if r["section"] not in deps:
            continue
        for kind, token in _sources(r["source"]):
            if kind in ("api", "dataset") and (doc := f"docs/sources/{token}.md") not in probes:
                probes.append(doc)
    skills = [s for s in _names(row.get("builds with", "")) if s != DATA_QUALITY]
    readmes = dependency_readmes(pkg, section)

    def cell(values: list[str]) -> str:
        return ", ".join(values) or "none"

    out: list[str] = []
    for token in runs:
        due = dues[token] or _next_round(pkg, section, token, built)
        commit = (str(due.get("commit") or section_commit(pkg, section) or "none")
                  if int(due["round"]) > 0 else "none")  # type: ignore[call-overload]
        if out:
            out.append("")
        out += [
            f"Mode: {due['mode']}",
            f"Section: {pkg}/{section}",
            f"Stage: {token}",
            f"Round: {due['round']}",
            f"Revise: {due['revise']}",
            f"Commit: {commit}",
            f"Contract: {_rel(contract_path(pkg))}",
            "Repo contract: docs/architecture.md",
            f"Dependency READMEs: {cell(readmes)}",
            f"Source probes: {cell(probes)}",
            f"Skills to invoke: {cell(skills)}",
            f"Data: {_stage_line(pkg, token)}",
            f"Profile: docs/sources/{token}.md",
            f"Store: .dev-team/data/{token}/",
            f"Run: run-package {pkg}",
        ]
    return out


def _holds_code(pkg: str, section: str) -> bool:
    """True when the section's path holds a `.py` file, nested sections excluded; for `surface`
    the package's own `__init__.py` (the scaffold's) does not count."""
    p = _paths(pkg, section)
    code: list[str] = p["code"]  # type: ignore[assignment]
    base = ROOT / code[0]
    nested = [ROOT / c.removeprefix(":(exclude)") for c in code[1:]]
    if not base.is_dir():
        return False
    scaffold = base / "__init__.py" if section == "surface" else None
    return any(f != scaffold and not any(n == f or n in f.parents for n in nested)
               for f in base.rglob("*.py"))


def _design_mode(design: Path) -> str:
    """The word after `Mode:` in the design's first five lines; `none` with no design or no word."""
    if not design.exists():
        return "none"
    head = design.read_text().strip().splitlines()[:5]
    m = next((m for line in head if (m := re.match(r"\**Mode:\**\s*`?(\w+)", line.strip()))), None)
    return m.group(1) if m else "none"


def spawn_fields(pkg: str, section: str) -> list[str]:
    """The `--fields` lines for one section; the module docstring lists them."""
    p = _paths(pkg, section)
    design: Path = p["design"]  # type: ignore[assignment]
    changes = [_rel(c["path"]) for c in open_changes(pkg, section)]  # type: ignore[arg-type]
    state, evidence = section_state(pkg, section)
    if changes or ("open " in evidence and "spec-change:design" in evidence):
        mode = "delta"
    elif _holds_code(pkg, section) and not design.exists():
        mode = "document"
    else:
        mode = "new"
    design_mode = _design_mode(design)
    base = "none"
    reps = _reports(pkg, section)
    if reps:
        n = max(reps)
        files = sorted(reps[n])
        pick = (next((f for f in files if f.name.endswith("-s.md")), None)
                or (next((f for f in files if f.name.endswith("-a.md")), None) if n == 1 else None)
                or (files[0] if len(files) == 1 and not re.search(r"-r\d+-[abs]\.md$", files[0].name) else None))
        if pick and (m := re.match(r"[0-9a-f]{7,40}", _report_fields(pick).get("Commit", "").strip("`"))):
            base = git("rev-parse", "--short", m.group(0)) or m.group(0)
    return [
        f"mode: {mode}",
        f"change file: {', '.join(changes) or 'none'}",
        f"design mode: {design_mode}",
        f"diff base: {base}",
        f"upstream interfaces: {', '.join(_upstream_interfaces(pkg, section)) or 'none'}",
        f"paths report: {_rel(report) if (report := section_paths_report(pkg, section)) else 'none'}",
        f"dependency readmes: {', '.join(dependency_readmes(pkg, section)) or 'none'}",
    ]


def _flag_value(argv: list[str], flag: str) -> tuple[bool, str | None]:
    """(present, value) for a flag with an optional non-flag value after it; removes both from argv."""
    if flag not in argv:
        return False, None
    i = argv.index(flag)
    argv.pop(i)
    if i < len(argv) and not argv[i].startswith("--"):
        return True, argv.pop(i)
    return True, None


def main() -> int:
    argv = sys.argv[1:]
    has_rounds, rounds_target = _flag_value(argv, "--rounds")
    has_surface, surface_pkg = _flag_value(argv, "--surface")
    has_shape, shape_pkg = _flag_value(argv, "--shape")
    has_paths, paths_pkg = _flag_value(argv, "--paths")
    has_section, section_name = _flag_value(argv, "--section")
    has_gate, gate_pkg = _flag_value(argv, "--run-gate")
    has_inputs, inputs_target = _flag_value(argv, "--inputs")
    has_scaffold, scaffold_pkg = _flag_value(argv, "--scaffold")
    has_fields, fields_target = _flag_value(argv, "--fields")
    has_profile, profile_target = _flag_value(argv, "--profile")
    has_defer = "--defer" in argv
    has_repo = "--repo" in argv
    has_against = "--against-contract" in argv
    argv = [a for a in argv if a not in ("--repo", "--against-contract", "--defer")]
    unknown = [a for a in argv if a.startswith("--")]
    if unknown:
        print(f"unknown flag: {' '.join(unknown)}")
        return 2
    if has_against and not has_paths:
        print("--against-contract needs --paths <pkg>")
        return 2
    if has_defer and not has_profile:
        print("--defer needs --profile <pkg>/<section>")
        return 2
    only = argv[0] if argv else None
    code = 0
    if has_rounds:
        pkg, _, sec = (rounds_target or "").partition("/")
        if not pkg or not sec:
            print("--rounds needs a target: status.py --rounds <pkg>/<section> or <pkg>/paths")
            return 2
        if sec == "paths":
            print("\n".join(paths_rounds(pkg)))
        else:
            n = rounds(pkg, sec)
            print(f"rounds: {n}")
            print(f"next round: {n + 1}")
            print(f"commit: {section_commit(pkg, sec) or 'none'}")
    if has_gate:
        fails = run_gate(gate_pkg or only)
        print("run gate: PASS" if not fails else "run gate: FAIL")
        for f in fails:
            print(f"  - {f}")
        code |= 1 if fails else 0
    if has_section and not has_surface and not has_shape:
        print("--section needs --surface <pkg> or --shape <pkg>")
        return 2
    if has_shape:
        if not shape_pkg or not section_name:
            print("--shape needs a package and --section a section: status.py --shape <pkg> --section <s>")
            return 2
        if _row(shape_pkg, section_name) is None:
            print(f"no section {section_name} in {_rel(contract_path(shape_pkg))}")
            return 2
        lines = shape_check(shape_pkg, section_name)
        print("\n".join(lines))
        code |= 1 if any(ln.startswith("FAIL") for ln in lines) else 0
    if has_paths:
        if not paths_pkg:
            print("--paths needs a package: status.py --paths <pkg>")
            return 2
        if not contract_path(paths_pkg).exists():
            print(f"{paths_pkg}: missing {_rel(contract_path(paths_pkg))}")
            return 2
        print("\n".join(paths_report(paths_pkg, has_against)))
    if has_surface and has_section:
        if not surface_pkg or not section_name:
            print("--surface needs a package and --section a section: status.py --surface <pkg> --section <s>")
            return 2
        if section_name == "surface":
            print(f"--section surface is the package-wide check: status.py --surface {surface_pkg}")
            return 2
        if _row(surface_pkg, section_name) is None:
            print(f"no section {section_name} in {_rel(contract_path(surface_pkg))}")
            return 2
        verdict, fails = surface_names(surface_pkg, section_name)
        print(f"surface names {surface_pkg}/{section_name}: {verdict}" + (" (no README)" if verdict == "n/a" else ""))
        for f in fails:
            print(f"  - {f}")
        code |= 1 if verdict == "FAIL" else 0
    elif has_surface:
        if not surface_pkg:
            print("--surface needs a package: status.py --surface <pkg>")
            return 2
        verdict, fails = surface_check(surface_pkg)
        print(f"surface: {verdict}" + (" (no interface.md)" if verdict == "n/a" else ""))
        for f in fails:
            print(f"  - {f}")
        code |= 1 if verdict == "FAIL" else 0
    if has_repo:
        if not DOCS.exists():
            print("no docs/ directory here — run from the repo root")
            return 2
        print("\n".join(repo_report()))
    if has_inputs:
        pkg, _, sec = (inputs_target or "").partition("/")
        if not pkg or not sec:
            print("--inputs needs a target: status.py --inputs <pkg>/<section>")
            return 2
        if _row(pkg, sec) is None:
            print(f"no section {sec} in {_rel(contract_path(pkg))}")
            return 2
        print("\n".join(implementer_inputs(pkg, sec)))
    if has_fields:
        pkg, _, sec = (fields_target or "").partition("/")
        if not pkg or not sec:
            print("--fields needs a target: status.py --fields <pkg>/<section>")
            return 2
        if _row(pkg, sec) is None:
            print(f"no section {sec} in {_rel(contract_path(pkg))}")
            return 2
        print("\n".join(spawn_fields(pkg, sec)))
    if has_profile:
        pkg, _, sec = (profile_target or "").partition("/")
        if not pkg or not sec:
            print("--profile needs a target: status.py --profile <pkg>/<section>")
            return 2
        if _row(pkg, sec) is None:
            print(f"no section {sec} in {_rel(contract_path(pkg))}")
            return 2
        blocks = profiler_inputs(pkg, sec, has_defer)
        if not blocks and has_defer and profiler_inputs(pkg, sec):
            blocks = [f"profile: no new kinds to defer in {pkg}/{sec}"]
        print("\n".join(blocks) or f"profile: no stage source in {pkg}/{sec}")
    if has_scaffold:
        if not scaffold_pkg:
            print("--scaffold needs a package: status.py --scaffold <pkg>")
            return 2
        needed = scaffold_needed(scaffold_pkg)
        print(f"scaffold: needed ({', '.join(needed)})" if needed else "scaffold: done")
        code |= 1 if needed else 0
    if (has_rounds or has_gate or has_surface or has_shape or has_paths or has_repo or has_inputs or has_scaffold
            or has_fields or has_profile):
        return code
    if not DOCS.exists():
        print("no docs/ directory here — run from the repo root")
        return 2
    pkgs = packages()
    if not pkgs:
        print("no packages: docs/architecture.md has no Packages table and docs/packages/ is empty")
        print("next: /dev-team:plan-repo")
        return 0
    if only and only not in {name for name, _ in pkgs}:
        pkgs = [(only, package_root(only))]
    blocks = [package_report(pkg) for pkg, _ in pkgs if not only or pkg == only]
    print("\n\n".join("\n".join(b) for b in blocks))
    return code


if __name__ == "__main__":
    sys.exit(main())
