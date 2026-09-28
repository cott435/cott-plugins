# `pair` — `status.py --inputs`, `gate_on_stop.py --report`, and the pairing skill's mechanical path

**Tested against:** uncommitted — see working-tree diff (on `84a4f0a`): `skills/pair/SKILL.md` (new), `skills/status/scripts/status.py`, `hooks/gate_on_stop.py`, `skills/run-package/SKILL.md`, `contracts.yml` · model: `claude-opus-5-5` (ran the checks by hand; no agent session) · 2026-09-28
**Set:** none, ad hoc · **Baseline:** `84a4f0a` for the pre-existing fixture suites

## What was tested

1. `status.py --inputs <pkg>/<section>` prints the implementer's twelve-field block in its
   **Inputs** order. It resolves the dependency READMEs, upstream interfaces (provisional
   before `interface.md`), probe docs, the review reports at FIX n, the round and open change
   files, and refuses a section the contract lacks.
2. `gate_on_stop.py --report [--base <rev>]` runs the stop gate's checks by hand over
   `<rev>`..working tree with no counter and no marker. It writes `.dev-team/gate.txt` and
   exits 1 on a FAIL, 2 on a bad flag or base. With no arguments, the hook behaves exactly as
   before.
3. The bundle's contracts hold after the implementer's driver table moves into
   `status.py`'s docstring and `pair` joins the ledger, README and interface readers.
4. `pair`'s mechanical path works on a real built section. From DONE, it runs the run gate,
   `--inputs`, a hand edit plus a README line, `--report --base <start>` and one trailered
   commit. The section re-derives to REVIEW, with the next round 2.

## Method

- Four new `state-cases` (`inputs-first-build`, `inputs-fix-round`, `inputs-upstream-change`,
  `inputs-bad-target`) and four new `hook-events` cases (`gate-report-base`,
  `gate-report-fail`, `gate-report-usage`, `gate-report-bad-base`). `hook-events/check.py`
  gained `args` and `stdout_contains` for them. Both full suites were run, so every
  pre-existing case doubles as the regression check for the refactor of `gate()` into
  `run_checks()`.
- `plugin-dev/scripts/contract_sweep.py .` over the bundle.
- The walkthrough ran by hand in the scratchpad on `hook-events/build.py`'s repo, with a
  design committed before the build commit and an approving round-1 `-a`/`-b` pair seeded so
  `ingest` reads DONE. The edit made `load_trades` skip blank rows and added one README line.
- **Not tested:** a live `/dev-team:pair` conversation. The skill is inline and interactive
  (the user judges each turn), and no headless harness drives that. Its classification,
  briefing and wrap-up prose are unverified by a run. Cost: $0, no model calls beyond this
  session.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| state-cases, all | 44/44 | 44/44 (40 existing + 4 new) | ✅ |
| `inputs-first-build` | the whole block, in order, for `data/clean` | exact 12-line match; `Dependency READMEs: packages/data/src/data/ingest/README.md`, `Round: 1` | ✅ |
| `inputs-fix-round` | both r1 reports, `Round: 2`, the trades probe | as expected | ✅ |
| `inputs-upstream-change` | `provisional: docs/packages/data/contract.md`, `Intent tests: none`, the open change file | as expected | ✅ |
| `inputs-bad-target` | exit 2, one line | `no section nope in docs/packages/data/contract.md`, exit 2 | ✅ |
| hook-events, all | 51/51 | 51/51 (47 existing + 4 new) | ✅ |
| `gate-report-fail` | exit 1, FAIL lines, no attempt wording | exit 1, `result: fail (2 failures, report since HEAD)`. The expectation first said 1 failure: the planted test file is also unformatted, which is a real second FAIL, so the expectation was corrected | ✅ |
| contract sweep | all pass | 35/36 first: the hook docstring's `/dev-team:pair` matched the "every agent_type names a shipped agent" pattern. Reworded to "the pair skill"; 36/36 | ✅ after fix |
| walkthrough: start | DONE, run gate PASS, `--inputs` `Round: 2` | `ingest · DONE · review r1 approve`; `run gate: PASS`; block as expected | ✅ |
| walkthrough: `--report --base <start>` | the gate's checks over the hand edit | `sections data/ingest`; `FAIL format (data)` on the edited `loader.py`; `TOLERATED` for the seeded deviation; exit 1 | ✅ (the FAIL is the finding below) |
| walkthrough: after the commit | REVIEW, next round 2, tree clean | `ingest · REVIEW · code d26728e newer than review r1 0cb8744`; `Round: 2`; `run gate: PASS` | ✅ |

## Verdict

Claims 1–4 hold. The walkthrough found a real gap. `format_on_edit.py` formats only the
implementer's and tester's edits, so code written in the main conversation reaches wrap-up
unformatted, and the gate fails it. Fixed in `skills/pair/SKILL.md` **While pairing**: run
`ruff format` / `ruff check --fix` / `ruff format` after every `.py` edit. This fix is prose
and was not re-run by a live session.

Open: a live pairing session is the untested part, above all the wrap-up's classification
against the implementer's table and the ledger entries it writes. The first real use should
be logged here.
