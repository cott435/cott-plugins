# 02 — hooks

Phase 02. Adds the plugin's hooks: `hooks/hooks.json` and three scripts. `format_on_edit.py`
runs `ruff` after every `.py` edit by the implementer or the tester; `gate_on_stop.py` refuses
to let an implementer finish until the `docs/constraints.md` rows, the section's intent suite
(with the deviation-ledger tolerance), a Guarded grep of the run's diff and, for the `surface`
section, `status.py --surface` are green, with a marker file and an attempt counter as the way
out; `guard_writes.py` refuses a write outside each role's allowed paths. The gap it closes:
every mechanical failure that reached a 0.6 review cost a reviewer run to discover, and "write
only under `docs/`" was an instruction nothing enforced. The platform facts this phase depends
on (PF-1, PF-2 in phase 0) must be logged before it starts; if PF-1 came out false, the gate
cannot exist as designed and this phase stops with a Deviation for the user.

`guard_writes.py` is the design's accepted suggestion: it is an optional addition to this
phase, and nothing later depends on it. Build it last.

## Decisions

- **Exec form, `python3` as the command.** Each hook is `"command": "python3", "args":
  ["${CLAUDE_PLUGIN_ROOT}/hooks/<script>.py"]`, so a path with spaces stays one argument
  (`plugin-anatomy` `hooks.md`). The scripts are not executables and need no mode bit.
- **Scope test, every script, first thing:** exit 0 unless the input's `cwd` contains
  `docs/architecture.md` and, where the script is role-specific, `agent_type` is one of its
  roles. Reason: plugin hooks run in every session the plugin is enabled in.
- **The parsers come from `status.py`** via `sys.path.insert(0, os.path.join(os.environ
  ["CLAUDE_PLUGIN_ROOT"], "skills", "status", "scripts"))` then `import status; status.set_root
  (cwd)`. The variable is exported to hook processes (`hooks.md`). No copy of any parser.
- **The gate identifies the run's work from git**, not from the driver: the run's commit is
  `HEAD` when `HEAD`'s body carries a `Dev-Team-Run:` trailer and the tree is clean but for the
  baseline exemptions; the run's diff is `HEAD~1..HEAD` plus the working tree. The section is
  `status.section_for_path()` over every path in that diff, longest section path wins; files
  directly under the package top level map to `surface`. Several sections → every one is
  gated. Reason: the hook gets only the hook input, and the driver relays nothing to hooks.
- **The diff includes untracked files**: the working-tree part is `git status --porcelain
  --untracked-files=all` (every listed path counts as added in full) plus `git diff HEAD`;
  the `HEAD~1..HEAD` part is included whenever `HEAD`'s body carries the trailer, dirty tree or
  not. Files directly under a package's top level map to `surface` only when
  `docs/packages/<pkg>/design/surface.md` exists; before the surface has entered the loop
  (the scaffold step touching `src/<pkg>/__init__.py`), they map to no section and are
  ignored for gating.
- **`${CLAUDE_PLUGIN_DATA}` unset** (a `--plugin-dir` session may not export it): the counter
  falls back to `<cwd>/.dev-team/gate-attempts/<agent_id>`; `.dev-team/` is gitignored.
- **`gate.txt` lists every check** as its own `PASS`/`FAIL` line, one per constraints row, one
  per intent test node id, one per Guarded item checked, one for `surface`.
- **A gate failure is fixed into the same commit.** The implementer (phase 4) stages its fix
  and runs `git commit --amend --no-edit`: the commit is this run's own and unpushed, and one
  commit per run holds. The gate re-derives the diff from the amended `HEAD`.
- **The gate writes its last output to `.dev-team/gate.txt`** in the repo (gitignored by the
  implementer's scaffold step) so the reviewer can read Measured values and the pass list
  without any command. **Measured** rows are run and printed, never failed on.
- **Attempt counter:** `${CLAUDE_PLUGIN_DATA}/gate/<agent_id>` holds an integer. Attempt 1 and
  2 exit 2 on failure; attempt 3 prints the failures, deletes the counter and exits 0. From
  attempt 2 the exit-2 text names `debugging-and-error-recovery`. A passing gate deletes the
  counter. Reason: the design's loop guard.
- **Marker:** `.dev-team/stop` under `cwd`, first line `blocked` or `spec-change` (the
  implementer writes it before returning either); the gate deletes it, deletes the counter,
  and exits 0 without running anything. Any other first line is ignored (the gate runs).
- **Ruff invocation:** `uv run ruff` when `<cwd>/uv.lock` exists, else `ruff` on `PATH`; when
  neither runs (exit 127 or `OSError`), exit 0 — a `PostToolUse` hook cannot block anyway.
- **Guard allowlists resolve `<pkg>` as `*`:** the guard knows the role, not the section, so
  `docs/packages/*/design/**` is the designer's, and `**/tests/intent/**` the tester's. The
  design lists `deviations.md` under the architect's exclusions and not under the tester's
  paths; both contradict the design's own writer table (the architect writes `synced`, the
  tester raises `spec-change:design`), so the allowlist follows the writer table.

## Files

| Path | Change |
|---|---|
| `hooks/hooks.json` | new — verbatim below |
| `hooks/format_on_edit.py` | new — specification below |
| `hooks/gate_on_stop.py` | new — specification below |
| `hooks/guard_writes.py` | new — specification below (optional addition) |
| `evals/fixtures/hook-events/` | new: recorded event JSON per path, a repo builder and `check.py` |
| `contracts.yml` | one `forbid` claim: every `SubagentStop` matcher and every `agent_type` string in `hooks/` names a file under `agents/` |
| `.gitignore` (plugin root) | none — `.dev-team/` is the built repo's ignore, added by the implementer in phase 4 |

## Specification

### `hooks/hooks.json`

```json
{
  "description": "dev-team: ruff after every .py edit by the implementer or tester; a stop gate the implementer must pass; a per-role write guard. Every script exits 0 outside a repo that has docs/architecture.md.",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/format_on_edit.py"], "timeout": 120 }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "^dev-team:implementer$",
        "hooks": [
          { "type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/gate_on_stop.py"], "timeout": 600 }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/guard_writes.py"], "timeout": 30 }
        ]
      }
    ]
  }
}
```

### `format_on_edit.py`

Input: the hook JSON on stdin (`cwd`, `agent_type`, `tool_input.file_path`). Steps:

1. Exit 0 unless `agent_type` is `dev-team:implementer` or `dev-team:tester`, `cwd` has
   `docs/architecture.md`, the path ends with `.py`, and the path resolves under `cwd` and
   not under `docs/`.
2. Run `<ruff> format <path>` then `<ruff> check --fix <path>` from `cwd`.
3. If the check exits non-zero: print its stdout to stderr, prefixed with one line
   `dev-team format hook: ruff check left these in <path relative to cwd>:`, and exit 2 (the
   model sees the text; the edit stands). Otherwise exit 0 silently.
4. Malformed or empty stdin: exit 0.

### `gate_on_stop.py`

Input: the hook JSON (`cwd`, `agent_id`, `agent_type`, `stop_hook_active`). Steps:

1. Scope: exit 0 unless `agent_type == "dev-team:implementer"` and `<cwd>/docs/architecture.md`
   exists.
2. Marker: if `<cwd>/.dev-team/stop` exists, read its first line; if it is `blocked` or
   `spec-change`, delete the file and the counter and exit 0.
3. Counter: read `${CLAUDE_PLUGIN_DATA}/gate/<agent_id>` (0 when absent), add one, write it.
   `n` is this attempt.
4. The run's diff and sections, per **Decisions**. No section → print `dev-team gate: no
   section in this run's diff` to stderr and exit 0.
5. Checks, all run, all results collected as lines `PASS <what>` / `FAIL <what>: <detail>`:
   - every **Floor** and **Enforced** row of `docs/constraints.md` for each `<pkg>` (a `repo`
     row once), via `status.constraints_rows`; without `docs/constraints.md`, every command
     from `status.toolchain_commands()`;
   - every **Measured** row, printed as `MEASURED <dimension>: <last line of stdout>`, never a
     FAIL;
   - the intent suite: `<runner> pytest tests/intent/<section> -q -p no:cacheprovider
     --tb=line -rf` from the package root, `<runner>` = `uv run` with `uv.lock` else `python3
     -m`; each failed node id is tolerated when `status.intent_docstrings` gives it a docstring
     whose text between `Design ` and the first `:` (whitespace-normalized) is contained in, or
     contains, the `Clause:` of a `proposed` or `approved` `deviation` entry for that section
     (`status.deviation_entries`); every other failure is `FAIL intent <node id>`; a tolerated
     one is `TOLERATED intent <node id> (<entry heading>)`;
   - the Guarded grep over the diff's added lines: `# noqa`, `# type: ignore`, `# pragma: no
     cover`, `@pytest.mark.skip`, `xfail` whose line has no `D\d+`, and removed lines starting
     with `assert ` or containing `pytest.raises` in a test file that still exists; a change to
     `docs/constraints.md` that lowers a number in a threshold cell; each hit is `FAIL guarded
     <item> at <file:line>` unless an **Exceptions** row's glob matches the path, its check
     names the item, and its expiry is not past;
   - for a `surface` section: `python3 <status.py> --surface <pkg>` must exit 0, else
     `FAIL surface: <its output>`.
6. Write every line to `<cwd>/.dev-team/gate.txt` (overwriting), with a first line
   `dev-team gate — attempt <n> — <date time> — sections <list>`.
7. No FAIL: delete the counter, exit 0. Any FAIL and `n < 3`: print the FAIL lines to stderr
   under `dev-team gate: not done — fix these, stage the fix, `git commit --amend --no-edit`,
   and finish again (attempt <n> of 3):`, and when `n == 2` add the line `Two attempts: invoke
   `debugging-and-error-recovery` with the Skill tool before the third.`; exit 2. `n >= 3`:
   print the FAIL lines under `dev-team gate: letting the run stop after 3 attempts with these
   failures — the reviewer will see them in .dev-team/gate.txt:`, delete the counter, exit 0.
8. Malformed stdin, or any exception: print `dev-team gate: error — <exception>` to stderr and
   exit 0 (fail open, reported).

### `guard_writes.py`

Input: the hook JSON (`cwd`, `agent_type`, `tool_input.file_path`). Exit 0 unless `cwd` has
`docs/architecture.md` and `agent_type` is in the table; a role not in the table (the main
thread, `Explore`, `general-purpose`) is never guarded. The path is made relative to `cwd`; a
path outside `cwd` is refused for every role. Allowed globs (`fnmatch` on the relative path,
`**` matching any depth):

| `agent_type` | allowed |
|---|---|
| `dev-team:architect` | `docs/**` except `docs/packages/*/design/**` and `docs/reviews/**`; `docs/deviations.md` allowed |
| `dev-team:designer` | `docs/packages/*/design/**`, `docs/deviations.md`, `docs/decisions.md` |
| `dev-team:researcher` | `docs/sources/**`, `.claude/skills/*/**` |
| `dev-team:tester` | `**/tests/intent/**`, `**/tests/fixtures/**`, `docs/deviations.md` |
| `dev-team:reviewer` | `docs/reviews/**`, `docs/deviations.md`, `docs/followups.md` |
| `dev-team:documenter` | `README.md`, `packages/*/README.md`, `docs/index.md`, `docs/readme-previous.md`, `docs/packages/*/readme-previous.md` |
| `dev-team:curator` | `docs/legacy/**`, `.claude/skills/*/**` |
| `dev-team:implementer` | everything except `docs/**` and `**/tests/intent/**`; under `docs/` only `docs/deviations.md`, `docs/decisions.md`, `docs/packages/*/interface.md`, `docs/api/*.md` |

`**/tests/intent/**` is allowed to `dev-team:tester` only, whatever the row says. Refusal: exit
2 with stderr `dev-team write guard: <agent_type> may not write <relative path>. Allowed:
<the row's globs>.` Malformed stdin: exit 0.

### `contracts.yml` claim

```yaml
  - name: every hook matcher and agent_type names an agent this plugin ships
    # A SubagentStop matcher or an agent_type test on a name with no agents/<name>.md never
    # fires, and the gate it implements silently does not exist.
    pattern: 'dev-team:(?!architect|designer|researcher|tester|implementer|reviewer|documenter|curator)[a-z-]+'
    files: ['hooks/hooks.json', 'hooks/*.py']
```

(Under `forbid`. The alternation is the one list of agent names in the bundle outside
`agents/`; phase 11's `names_listed`-style check for `agents/*` is this claim.)

### `evals/fixtures/hook-events/`

`build.py <dest>` builds a repo from `two-package/` with one built section (`data/ingest`:
code, README, `tests/intent/ingest/` with two tests, one of which fails and cites `Design §5
load_trades`), `docs/constraints.md`, a `docs/deviations.md` with one `proposed` entry whose
`Clause:` is `design §5 load_trades`, and one commit carrying `Dev-Team-Run: run-package data`.
`events/*.json` are recorded hook inputs, one per case. `check.py` pipes each event into the
named script with `CLAUDE_PLUGIN_ROOT` set to the plugin and `CLAUDE_PLUGIN_DATA` to a temp
dir, and exits 1 naming each case whose exit code or stderr does not match:

| Case | Script | Event | Expect |
|---|---|---|---|
| `fmt-out-of-scope-agent` | format | `agent_type: dev-team:reviewer`, a `.py` | exit 0, no stderr |
| `fmt-out-of-scope-cwd` | format | implementer, `cwd` without `docs/architecture.md` | exit 0 |
| `fmt-clean` | format | implementer, a clean `.py` | exit 0; file unchanged |
| `fmt-fixable` | format | implementer, a `.py` with an unused import | exit 0; the import is gone |
| `fmt-unfixable` | format | implementer, a `.py` with an undefined name | exit 2; stderr names the file |
| `fmt-malformed` | format | `{` | exit 0 |
| `gate-out-of-scope` | gate | `agent_type: dev-team:tester` | exit 0 |
| `gate-marker` | gate | implementer, `.dev-team/stop` = `blocked` | exit 0; marker deleted; counter absent |
| `gate-pass` | gate | implementer, suite green, rows green | exit 0; `.dev-team/gate.txt` has only PASS lines; counter absent |
| `gate-tolerated` | gate | implementer, the failing test cites the proposed clause | exit 0; `TOLERATED intent` line present |
| `gate-fail-attempt-1` | gate | implementer, a second failing test with no entry | exit 2; stderr `attempt 1 of 3`; counter = 1 |
| `gate-fail-attempt-2` | gate | same, counter pre-set to 1 | exit 2; stderr names `debugging-and-error-recovery`; counter = 2 |
| `gate-fail-attempt-3` | gate | same, counter pre-set to 2 | exit 0; stderr `after 3 attempts`; counter absent |
| `gate-guarded` | gate | implementer, diff adds `# noqa` | exit 2; `FAIL guarded # noqa at <file:line>` |
| `gate-guarded-exception` | gate | same, an Exceptions row covering the path, not expired | exit 0 |
| `gate-constraints-fail` | gate | implementer, coverage floor above real coverage | exit 2; `FAIL <dimension>` |
| `gate-measured` | gate | implementer, a Measured row | exit 0; `MEASURED` line present |
| `gate-surface` | gate | implementer, diff under `src/data/__init__.py`, `interface.md` disagreeing with `__all__` | exit 2; `FAIL surface` |
| `gate-malformed` | gate | `{` | exit 0; stderr starts `dev-team gate: error` |
| `guard-<role>-allowed` ×8 | guard | one allowed path per role | exit 0 |
| `guard-<role>-refused` ×8 | guard | one refused path per role (the tester's tree for the implementer; `docs/reviews/` for the designer; …) | exit 2; stderr names the role and the path |
| `guard-main-thread` | guard | no `agent_type` | exit 0 |
| `guard-outside-cwd` | guard | implementer, `/tmp/x.py` | exit 2 |
| `guard-malformed` | guard | `{` | exit 0 |

## Steps

1. `hooks/hooks.json`.
2. `format_on_edit.py`; its cases in `check.py` pass.
3. `gate_on_stop.py`; its cases pass.
4. `guard_writes.py`; its cases pass.
5. The `contracts.yml` claim; plant `dev-team:implementor` in a scratch copy and watch it fail.
6. The plugin's own rules (no skill added or removed).
7. `check-contracts`; `build-site`.
8. Evals — the table below, through `run-evals`, logged with `log-eval`.
9. Commit: `dev-team remake (phase 02): hooks — ruff on edit, implementer stop gate, per-role write guard`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 2.1 | mechanical | `hooks/*.py` | — | `evals/fixtures/hook-events/check.py` | exit 0; every case in the table above passes |
| 2.2 | load | `hooks/hooks.json` | — | `/hooks` in an interactive session started with `claude --plugin-dir ./dev-team` (run-phase asks the user for the listing) | the three events list one dev-team hook each |
| 2.3 | behavioral | `hooks` | none | `evals/sets/hooks.json` 1, 2 | every expectation passes for `with_skill`: the format hook's effect shows in the in-scope transcript and not in the out-of-scope one; the gate blocks a stop with a failing intent test in scope (the transcript shows a second turn after the stderr) and lets it through outside |
| 2.4 | mechanical | `contracts.yml` | — | the planted `dev-team:implementor` | the new claim FAILs on the plant and PASSes without |

## Done when

- `python3 evals/fixtures/hook-events/check.py` exits 0.
- `hooks/hooks.json` parses and every `args` path exists under `hooks/`.
- `check-contracts` prints all PASS including the hook claim; `build-site` exits 0.
- Eval log rows for 2.1–2.4 exist in `evals/README.md`; 2.3's iteration directory is named.
- The ledger row for phase 2 reads `done`.
