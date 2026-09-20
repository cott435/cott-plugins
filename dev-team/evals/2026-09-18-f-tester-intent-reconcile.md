# F — the tester: never reads source, intent tests red, commits only its tree, reconcile touches only cited tests

**Tested against:** uncommitted — see working-tree diff (phase 4 of the 0.5 overhaul, on top of
`cfe974a`): `agents/tester.md` (new), `skills/test-section/SKILL.md` (new),
`agents/implementer.md`, `agents/reviewer.md`, `agents/designer.md`,
`skills/status/scripts/status.py`, `contracts.yml` · model: `claude-sonnet-5` (the CLI default
in the headless runs; every agent on `inherit`, and every fork's transcript shows
`claude-sonnet-5`); `claude-opus-5` ran the checks · Claude Code `2.1.270` · 2026-09-18

## What was tested

Note 09 eval F, the four checks in note 04 §Steps 5, on the fixture's `data/ingest`:

1. In intent mode the tester makes no Read/Grep/Bash call touching `src/data/ingest/` except
   `README.md`.
2. Every intent test it writes fails before the section exists.
3. Its commit stages only `tests/intent/ingest/` and fixtures.
4. In reconcile mode, with one recorded deviation, exactly the tests citing that design item
   change, and every other intent file's diff is empty.

Also checked along the way: the implementer runs the intent suite before writing code and
reports `Intent tests:`; the `status.py` intent column; the three new `contracts.yml` claims
fail when violated.

## Method

**Behavioral**: real headless runs, `claude -p "<command>" --plugin-dir <abs>/dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`, on a
`reset.sh --no-constraints` copy of the fixture on branch `build`. The planned state is written
by hand and committed as one commit, as in eval E: `docs/architecture.md`, `contract.md` and
`integration.md` copied from eval E's repo, and a new `design/ingest.md` in the designer's
numbered template (11 headings, a **Module plan** naming the interfaces each file defines,
a §5 table, §6 error cases, and §7 tests including "order is preserved"). The scaffold
(`pyproject.toml`, `data/__init__.py`, `data/errors.py`) is committed with it. Evidence comes
from each fork's own transcript (`subagents/agent-*.jsonl`, `agentType: dev-team:<agent>`) and
from git.

| Run | Command | Cost |
|---|---|---|
| 1 | `/dev-team:test-section data/ingest` (intent) | $0.60 |
| 2 | `/dev-team:implement-section data/ingest` | $0.65 |
| — | hand-seeded commit: `Trade.price` `float` → `Decimal`, recorded in README item 7 with a reason; unit test updated | — |
| 3 | `/dev-team:test-section data/ingest` (reconcile) | $0.31 |

Run 2 recorded no deviations, so the deviation for check 4 was seeded by hand. It is the same
one eval E used. With it, exactly one intent test goes red:
`test_first_row_fields_parsed_to_documented_types`, `pytest.approx(49.74)` against a `Decimal`.

**Mechanical**: `contract_sweep.py` on the real files, then on a scratch copy with one planted
violation per new claim. `status.py data` was run in detached worktrees of the eval repo at
four commits. No model cost.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 1 — intent run touches no section source | no call reads under `src/data/ingest/` | 30 tool calls; none reads under `src/data/ingest/` (it did not exist yet). One `find packages -maxdepth 5` listed the package tree | ✅ |
| 2 — all intent tests red | every test fails | 23 written, `23 failed` (`ModuleNotFoundError: data.ingest`); none deleted for passing | ✅ |
| 3 — commit is only its tree | `tests/intent/ingest/` + fixtures | `conftest.py`, 3 test files, `tests/fixtures/trades.csv`; trailer `Dev-Team-Run: test-section data/ingest`. It staged `__pycache__/` by directory first, then unstaged it before committing | ✅ |
| docstrings trace to the design | `Design §<n> …` on every test | 23/23 | ✅ |
| imports per Module plan | `from data.ingest.reader import …` inside each test | yes | ✅ |
| implementer runs intent suite first | run before the first Write under the section | `pytest packages/data/tests/intent/ingest` ran before `mkdir …/ingest`; `tests/intent/` untouched by its commit | ✅ |
| implementer return | `Intent tests: <pass>/<total>` | `Intent tests: 23/23` | ✅ |
| 4 — reconcile edits only tests citing the deviated item | only §3 `price` tests change | 2 functions changed: `test_trade_holds_the_five_documented_fields` (§3) and `test_first_row_fields_parsed_to_documented_types` (§7 "parsed to the §3 types"). Each gains `(deviation: README item 7)`. `conftest.py` and `test_workflow.py` are byte-identical, and so are the other 18 functions. 23/23 pass after; no follow-ups filed | ✅ |
| 4 — reconcile reads no section source | only `README.md` under `src/data/ingest/` | Read: `README.md` only. One `find packages/data -maxdepth 5` listed `reader.py` by name; no call read its content | ✅ (names listed) |
| reconcile commit | message and trailer per §Project convention | `data/ingest: reconcile 2 intent tests with deviations`, trailer present | ✅ |
| `status.py` intent column | `—` / `0/23` / `22/23` / `23/23` at plan / intent / seeded / reconciled | exactly those | ✅ |
| `status.py` leaves no files | clean tree after a run | **first version left `__pycache__/` under the section**, which the next run reads as `uncommitted`. Fixed with `PYTHONDONTWRITEBYTECODE=1`; re-run leaves nothing | ✅ after fix |
| contracts on the real files | 17/17 | 17/17 | ✅ |
| control — `tests/unit/<section>` planted in tester.md | forbid FAIL | `FAIL … agents/tester.md:139` | ✅ |
| control — designer's **Tests** renamed | heading FAIL | `FAIL … tester.md names 'Tests'` | ✅ |
| control — implementer's **Implementation notes** renamed | heading FAIL | `FAIL … tester.md names 'Implementation notes'` | ✅ |

Seen but outside the four checks:

- **Reconcile checked the baseline after editing, not before.** It invoked
  `git-workflow-and-versioning` and ran `git status` after both Edits. The intent run did it in
  the right order. The result was harmless here, because the tree was clean apart from
  untracked `__pycache__/`, but the order is what the rule asks for.
- **Untracked `__pycache__/` did not trip the baseline rule** in any run. Neither agent treated
  it as a blocker, and a strict reading of **Baseline** says it is one. The fixture has no
  `.gitignore`, so every run leaves these directories behind.
- **Commit bodies carry prose.** Both the implementer's commit and the reconcile commit put a
  sentence before the trailer. §Project convention **Message** says the body is trailers only.
  This predates phase 4.
- **The tester's `uv run pytest` from `packages/data/` wrote an untracked
  `packages/data/uv.lock`.** The repo's Toolchain command is `python3 -m pytest`. That is the
  command `status.py` now uses when the repo has no `uv.lock`.

## Verdict

All four checks in note 04 hold. The implementer's intent-suite step and return line hold, and
so does the `status.py` column, after one fix: the first version left bytecode behind, and the
next run read it as uncommitted changes. The fix was re-run and confirmed on the same repo.
Check 4 used a hand-seeded deviation, because the real implementer run recorded none.

Watch in phase 9: the tester lists the package tree with `find`, which shows the section's
file names without reading them; the reconcile baseline order; the pre-existing
commit-body prose; and untracked bytecode against the baseline rule.
