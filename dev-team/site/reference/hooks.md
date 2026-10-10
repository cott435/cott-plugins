# The hooks

`hooks/hooks.json` registers five, and each exits 0 outside a repo with `docs/architecture.md`.
The two guards also act in a repo with only `docs/brief.md`, so `plan-repo`'s agents are
guarded before the repo contract exists:

- **`format_on_edit.py`** (`PostToolUse` on `Write|Edit`) — for the implementer and the tester,
  on a `.py` file: `ruff format`, `ruff check --fix`, `ruff format`, then `ruff check`. What
  remains is shown to the agent; the edit stands. Until the repo has a ruff config of its own,
  it lints with `pyproject-lint-config.toml`, so intent tests written before the first
  implementer merges that block already meet it.
- **`sync_decisions.py`** (`PostToolUse` on `Write|Edit`) — on a write to a decisions inbox,
  `docs/packages/<pkg>/decisions/<section>.md`, by anyone: under the lock
  `.dev-team/locks/decisions/`, a `## D?` stub gets the next free number, is appended to
  `docs/decisions.md` and renumbered in the inbox; the central entry's `Applied:` lines that
  name the inbox's own section are made equal to the inbox's, so a line the section edits or
  removes is edited or removed centrally, while other sections' lines are untouched. Nothing
  else flows, and `Decision:` and `Status:` never flow at all.
  The numbering comes back to the agent as context (`D? → D14`). `--all` by hand merges every
  inbox ([Decisions](decisions-deviations-reviews.md)).
- **`gate_on_stop.py`** (`SubagentStop`, `^dev-team:implementer$`) — the implementer may not
  finish while its section is red. It reads the section from the spawn prompt's `Section:`
  line in the agent's transcript, and its diff is that section's paths since the section's
  last review `Commit:` (else the empty tree), so a sibling's work under parallel implementers
  is never its own. It runs the section's intent and unit suites — an intent failure tolerated
  only when the test cites the clause of a `proposed` or `approved` deviation — a **Guarded**
  grep of that diff, `status.py --surface` for the `surface` section and, for every other
  section, the per-section name check `status.py --surface <pkg> --section <section>` (each
  row of the README's **Entry points and interfaces** names one exported identifier, in
  backticks, and every `Public: yes` name is one the contract's **Public surface (intent)**
  names), so a README's author meets a bad row in its own run; then the **Floor** and
  **Enforced** rows of `docs/constraints.md` for the package (else the Toolchain commands of
  `docs/architecture.md`). A `repo`-scope pytest row is the integration check's: the record
  says `SKIPPED <row>: repo-scope pytest is the integration check's` and never runs it. Then
  the regression check: the whole suite of every finished package (every section DONE) that
  depends on this one, one `regression <dep>` line each — `FAIL` when the failure's output
  traces into the section's files (a traceback frame, or an `ImportError` naming one of its
  modules), else `ELSEWHERE`, since a sibling in the same batch may be the cause. A check
  whose every located failure lies outside the section's paths, or in an intent-test file (a
  lint, type or Guarded hit in the tester's lines), is `ELSEWHERE`, not `FAIL`: the implementer may not edit there, and the
  reviewer carries each such line to `docs/followups.md`. A failing
  intent test is still `FAIL`, since what fails is the code. Guarded's removed items are a
  test file that lost more `assert` lines than it gained, or more `pytest.raises`, counted per
  file, so a rewritten or moved assert is not a removal. An `xfail` cites a decision when its
  `xfail(` call, read to its closing bracket, holds a `D<n>` not followed by a digit (`D5:`,
  `D5_OPEN`), so a formatter's wrap is harmless.
  The package-wide rows share a time budget under the hook's timeout: a row that runs out of
  time is `TIMEOUT`, not `FAIL`. Every line goes to the section's own record,
  `.dev-team/gate/<pkg>/<section>.txt`: the header `dev-team gate — attempt n — <stamp> —
  section <pkg>/<section>`, then `commit: <short sha>` (the newest commit touching the
  section's code, unit tests and README), the check lines, and a last `result:` line. The
  reviewer reads it as its evidence, and `status.py` derives the row from it ([The states](running-a-package.md));
  a record whose `commit:` is not the section's current commit is ignored. It lets the agent
  stop on a green run; on its section's marker `.dev-team/stop/<pkg>/<section>` (the
  implementer writes it when it stops `blocked` or `spec-change`; a sibling's marker is never
  read), which is recorded, not silent: `blocked` or `spec-change` in the header's attempt
  slot, the earlier attempt's check lines, a `blocked: <reason>` or `spec-change: <heading>`
  line, and `result: blocked` or `result: spec-change`; or on the third red attempt, counted
  per agent under `${CLAUDE_PLUGIN_DATA}/gate/`, which leaves the section BLOCKED until you
  answer. A FAIL the implementer cannot clear — in a file it may not edit, or false in its own
  file — is a block, with the gate line quoted in the marker. The implementer hands back once:
  after a retry it fixes, commits and ends its turn with the one line `Result: done`, and the
  record is what the driver reads. A retry amends only when
  `git log -1 --format=%s` starts with the section's own scope, else it is a second commit with
  the same trailer; from the second attempt the message names `debugging-and-error-recovery`.
  By hand, `gate_on_stop.py --report [--base <rev>]` runs the same checks over
  `<rev>`..working tree with no counter and no marker, writes the same records, and exits 1 on
  a FAIL; `/dev-team:pair` runs it at wrap-up. `gate_on_stop.py --integration <pkg>` is the
  integration check ([Running a package](running-a-package.md), step 6), run by the driver from the Bash tool rather than
  the hook, so its rows share `DEV_TEAM_INTEGRATION_BUDGET` (570 s by default, under the Bash
  tool's limit) instead of the hook's 600 s.
- **`guard_writes.py`** (`PreToolUse` on `Write|Edit`) — each role writes only where its job
  is: the architect under `docs/` but not designs or reviews; the designer to designs, the
  ledgers and its section's decisions inbox; the researcher to `docs/sources/` and
  `.claude/skills/`; the profiler to `docs/sources/`, `.dev-team/data/`, the ledgers, the
  inboxes and `docs/followups.md`; the tester to `tests/intent/` and fixtures; the reviewer to review reports
  and the ledgers it edits; the documenter to the READMEs and `docs/index.md`; the implementer
  everywhere but `docs/`, except the ledgers, the inboxes, its `interface.md` and its API page.
  An implementer with a `Section:` line is confined to its section's files — its code,
  `tests/unit/<section>/`, fixtures, its ledger and inbox, `.dev-team/tmp/`, and for `surface`
  also `interface.md`, the API page `docs/api/<pkg>/index.md`, the package `pyproject.toml` (its
  `[project.scripts]`), the root `pyproject.toml` and `mkdocs.yml`. A path under another
  section's `path` is that section's and is refused first, which stops `surface` at its
  siblings and a parent section at its nested ones. An entry-point line in the package
  `pyproject.toml` goes through `locked.py` and `entry_point.py`, so no section but `surface`
  has that file in scope. A scaffold run or an unreadable transcript falls back to the
  role-wide rule. Every role's globs cover the 2.2 paths, and the old locations stay writable
  for status edits. Nobody but the tester writes under `tests/intent/`, and a Write or Edit
  there that adds `# noqa`, `# type: ignore` or `# pragma: no cover` is refused. A Write of an
  existing `.claude/agent-memory/<role>/MEMORY.md` that would drop a line is refused too:
  parallel runs of one role each add their line with Edit.
- **`guard_bash.py`** (`PreToolUse` on `Bash`) — no dev-team agent writes a repo file from the
  shell: a redirect (`>`, `>>`) to anything but `/dev/null` or a path under `.dev-team/tmp/`
  (refused as `may not redirect to <target>: it is outside .dev-team/tmp/`; a researcher may
  also redirect to a path outside the repo, its scratch), `sed -i`, `tee`, and python code
  that opens a file for writing — as `python -c`, or as a
  here-document script (`python3 - <<'EOF'`) — are refused, with the rule on stderr; an
  `sh -c` script is checked like a command of its own. `locked.py` is the one way an
  implementer runs `uv add`, `uv remove`, `uv lock` or `uv sync`, or appends the `.gitignore`
  block (`sh -c "printf … >> .gitignore"`), holding `.dev-team/locks/<name>/` while the command
  runs; those are let through, and any other command wrapped in `locked.py` is checked as if it
  were not. The third shared edit is an entry point: `locked.py deps -- python3
  …/entry_point.py <pkg> <group> <name> <target>` is let through for the caller's own package
  (the `<pkg>` of its spawn prompt's `Section:` line) and refused unwrapped, under another
  lock, or for another package. A command it cannot parse is let through with the rule on
  stderr.
