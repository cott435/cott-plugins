# prior-issues loop phase 7 — `select --cover`, issue marks on the chart, the verdict-words claim

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `6974d1e`): `skills/run-flow/scripts/trace.py`, `skills/run-flow/scripts/flow.py`, `agents/run-auditor.md`, `contracts.yml` · model: none (scripts, checked by script) · 2026-10-07
**Set:** none — M7.1–M7.3 are rows of `site/notes/0.16-audit-ledger-07-prior-issues.md` **Evals** with no set · **Iteration:** none, run in the phase chat (harness kept at `evals/workspace/prior-issues/m7.sh`, output `m7.out`, gitignored) · **Baseline:** none · **Pass rate:** M7.1 8/8 · M7.2 8/8 · M7.3 4/4

## What was tested

That `trace.py select --cover` adds the first finished unit of each uncovered `agent:<type>`,
names the segments that ran each `driver:<command>`, and reports what nothing matches; that
`flow.py` draws a session's issue marks (found, held) on its boxes and unit pages from the
ledger four levels above the workspace, or from `--issues DIR`, and draws nothing with no
ledger; and that the new `headings` claim holds the prior-issue verdict words to
`run-auditor`'s numbered list.

## Method

- One bash harness, every check a string or exit-code comparison. The fixture is
  `evals/fixtures/audit-run/make_session.py` into a `mktemp -d`, with
  `AUDIT_RUN_PROJECTS` pointed at it; the planted session (`0a0d17f0`, one writer unit, one
  `/toy:ship` segment) and the flow session (`0f10d17f`, writers U01/U02/U04, reviewers
  U03/U05) are built with `trace.py build`.
- M7.2's ledger is a scratch plugin `toy` at `$TMP/p`, the workspace at
  `$TMP/p/evals/workspace/audit/0a0d17f0`. `TO-001` is made by `issues.py new` with Found in
  `0a0d17f0 · U01 · U01.S3`; `TO-002` by `new` (found in another session), `fix`, and
  `check-result --verdict held --unit U01 --step U01.S4` for `0a0d17f0`.
- M7.3's negative copy is the plugin rsynced to a temp dir (minus `evals/workspace/` and
  `site/docs/`) with `1. **held**` renamed `1. **kept**` in `agents/run-auditor.md`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M7.1a | `select ws --units U01 --cover agent:writer,driver:ship` prints `U01  named` | as expected | ✓ |
| M7.1b | … and `cover segments: seg-1` | as expected | ✓ |
| M7.1c | the writer is not added a second time | one unit line | ✓ |
| M7.1d | `--units risk --cover agent:nobody` prints `uncovered: agent:nobody` | as expected | ✓ |
| M7.1e | flow workspace `--units U01 --cover agent:reviewer` adds `U03  covers agent:reviewer` | as expected | ✓ |
| M7.1f | the same with `--cap 1` prints `over cap: U03 (agent:reviewer)` and adds nothing | as expected | ✓ |
| M7.1g | no `--cover`: output unchanged, no cover lines | `U01  first toy:writer`, `U03  first toy:reviewer`, summary | ✓ |
| M7.1h | `select --help` lists `--cover` | yes | ✓ |
| M7.2a | `trace.py flow $WS` exits 0 | 0 | ✓ |
| M7.2b | `flow.html` has `+ TO-001` | `<tspan class="badge idle">+ TO-001</tspan>` | ✓ |
| M7.2c | `flow.html` has `✓ TO-002` | `<tspan class="badge ok">✓ TO-002</tspan>` | ✓ |
| M7.2d | `units/U01.html` names both, linked to `../../../../../audits/issues/<ID>.md` | an **Issues** row with both links | ✓ |
| M7.2e | a workspace with no ledger: `flow` exits 0 | 0 | ✓ |
| M7.2f | … and no marks, no marks line, no Issues row | none | ✓ |
| M7.2g | `flow NL --issues $P/audits/issues` marks the no-ledger workspace | both marks | ✓ |
| M7.2h | `flow --help` lists `--issues` | yes | ✓ |
| M7.3a | `check-contracts` on the real bundle: every claim PASS | 11/11, exit 0 | ✓ |
| M7.3b | the copy with `**held**` renamed: exit 1 | 1 | ✓ |
| M7.3c | … the new verdict-words claim FAILs | `skills/audit-run/SKILL.md names 'held'; skills/fix-issues/SKILL.md names 'held'` | ✓ |
| M7.3d | … and only that claim | 1 FAIL | ✓ |

## Verdict

Held, 20/20. Found and fixed while writing the harness: an `--issues` path that was not
resolved gave unit-page links through `/var` rather than `/private/var` on macOS; `flow.py` now
resolves the ledger directory before computing links. The box layout with marks (a 14 px line
under the label, the boxes 68 px tall when any unit in the run has a mark) was not checked by
eye: the browser pane would not render the static file.
