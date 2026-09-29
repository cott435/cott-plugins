# Audit fixes 4–8 and the notes: one ledger per section, report-raised spec-changes, §10 into the ledger, researcher `Result:`, redesign as `delta`, and the smaller definition gaps

**Tested against:** uncommitted, see the working-tree diff on branch `gate-fixes` (on `eda16c0`): `skills/status/scripts/status.py`, `hooks/guard_writes.py`, every agent, `run-package`, `pair`, `sync-plan`, `plan-package`, `finalize-project`, `planning-templates`, `git-workflow-and-versioning`, `pyproject-lint-config.toml`, README, site pages, eval sets · model: `claude-opus-5-5` · 2026-09-29
**Set:** `evals/fixtures/state-cases` (52 cases, 8 new) and `evals/fixtures/hook-events` (64 cases, 5 new) · **Baseline:** `eda16c0` · **Pass rate:** 52/52 and 64/64; 6 of the 8 new state cases fail on the baseline, and the other 2 are guards that must pass either way

## What was tested

These are the rest of the audit's definition faults (`2026-09-28-audit-run-package-1493ed56.md`, E4–E8) and the notes and warnings it filed against the plugin's files.

- **E4 (the shared ledger).** The ledger is one file per section, `docs/deviations/<pkg>/<section>.md`. A pre-split `docs/deviations.md` is still read, and its entries are edited in place.
- **E5 (b's spec-change had no route).** A newest-round report with `Verdict: spec-change` counts as an open spec-change of each level its **Spec-change** heading names. That lasts until a ledger entry records it, or until the named document is committed after it. Round 1 also needs both `a` and `b`.
- **E6 (§10 never reached the contract).** Each design §10 contract deviation is a `proposed` ledger entry, which A approves and `sync-plan` folds in.
- **E7 (researcher returns had no `Result:`).** Every researcher return starts `Result: done | blocked`.
- **E8 (a redesign ran as `new`).** An open `spec-change:design` makes the designer's mode `delta`, and a new `Spec-change:` field carries it. The tester and architect take report-raised headings too.
- **Notes and warnings:**
  - `status.py`: `…/<name>/` path cells resolve; `--inputs` gives a post-spec-change implementer its round's reports.
  - The driver: allowed reads include Shared conventions and the inventory; the first-line rule sits at Branch; a row that did not move after `done` goes to Asking; `Access: none`.
  - The reviewer: ledger edits one line at a time with Edit; a refused edit still gets a report and `done`.
  - The implementer: reads the backlog before coding; runs step 0 after the first scaffold; creates `configs.py` only when given.
  - The tester: tags approved clauses on every run.
  - The researcher: a per-run scratch subdirectory; a bad request for fixed-path files.
  - Every agent's memory: unique names, index edits only.
  - The `Co-Authored-By` line is allowed after the trailer, and `.claude/` is excluded from lint.

## Method

- **State cases, new:**
  - `ledger-legacy`: an entry in the old single file still counts.
  - `report-spec-change-b`, `-answered`, `-recorded` and `-contract`: b's report re-opens DESIGN; a design rewrite answers it; a later ledger entry takes over; a contract-level one goes to PLAN.
  - `review-half-pair`: round 1 with only `b` is REVIEW.
  - `path-shorthand`: a `…/ingest/` cell resolves.
  - `inputs-spec-change-review`: the implementer's `Review:` carries the spec-change round.
- **Fixture changes.** The builder writes per-section ledgers by default, with a `legacy` switch. So all 44 old cases now run on the new layout, and they pass.
- **Hook cases.** Four roles may write `docs/deviations/data/ingest.md` and the researcher may not. The gate's tolerated-deviation case now reads the per-section ledger.
- **Baseline runs.** The 8 new state cases were run against `eda16c0`'s `status.py`.
- **Replay on real data**, in the scratchpad clone of the quant repo (session 1493ed56, "Project architecture migration"), old against new `status.py`:
  - At `051be32` (edgar round 1, where `a` returned `blocked` and wrote no report and `b` approved), on the committed tree, and again with the driver's uncommitted path edit applied, which is what the run saw.
  - At `01553a2` (identity round 1, where `a` approved and `b` said spec-change with no ledger entry).
- **Eval sets.** Seven fixture ledgers were split by section, and 30 mentions in six sets were repointed at the ledger of the section each eval's prompt names. One wrong automatic repoint (the architect close, no `Section:` line) was corrected by hand. Every set validates.
- **Contracts:** dev-team 36/36, plugin-dev 8/8.
- **Not run:** behavioral runs of the edited agents. The prose changes are checked by the contracts and by reading them, not by an agent run.

## Results

| Case | Baseline `eda16c0` | Now |
|---|---|---|
| state-cases, 44 existing on per-section ledgers | — | 44/44 |
| `report-spec-change-b` | FAIL | PASS: DESIGN from `…-r1-b.md — spec-change:design` |
| `report-spec-change-recorded` | FAIL | PASS |
| `report-spec-change-contract` | FAIL | PASS: PLAN |
| `review-half-pair` | FAIL | PASS: REVIEW, `lacks its a report` |
| `path-shorthand` | FAIL | PASS: DONE |
| `inputs-spec-change-review` | FAIL | PASS |
| `ledger-legacy`, `report-spec-change-answered` | PASS (guards) | PASS |
| hook-events | 59/59 | 64/64 |
| Replay: edgar at `051be32`, committed tree | IMPLEMENT (`no …/edgar/README.md`: the shorthand never resolved) | REVIEW, `review r1 lacks its a report` |
| Replay: edgar at `051be32`, with the driver's path edit | **DONE**: edgar would have shipped with no conformance review | REVIEW, `review r1 lacks its a report` |
| Replay: identity at `01553a2` | REVIEW, `spec-change, no open entry left`: the dead end behind U46 and U47 | **DESIGN**, `open docs/reviews/2026-09-28-data-identity-r1-b.md — spec-change:design` |

## Verdict

The state and hook changes hold on the fixtures and on the real history. Both replayed failures from the quant run now route correctly.

The ledger path change breaks a contract other files read, so it is a MAJOR release for dev-team. Repos already midway through a run keep working, because the old file is still read and its entries are edited in place.

The agent-prose changes are not yet proven behaviorally. The next real `run-package`, audited with `/plugin-dev:audit-run`, is their test.
