# remake phase 1 — `status.py` state derivation, the three new templates, frontmatter claims

**Tested against:** uncommitted — see working-tree diff (on `17823d2`; `skills/status/scripts/status.py`, `skills/status/SKILL.md`, `skills/planning-templates/references/{change,deviations-entry,review-report}.md`, `contracts.yml`) · model: none for 1.1–1.3 (scripts); `claude-sonnet-5` for 1.4 (Claude Code 2.1.270) · 2026-09-27
**Set:** phase note `site/notes/remake-01-state-and-templates.md` `## Evals` rows 1.1–1.4 (mechanical and load; no `evals/sets/status.json` — the cases are `evals/fixtures/state-cases/`) · **Iteration:** none (no behavioral row, so no `run-evals` workspace) · **Baseline:** none · **Pass rate:** 4/4 rows

## What was tested

That `status.py` derives each section's state by the nine ordered rules of its docstring, from
commit order, with the ready set, rounds from report filenames, `shipped`, `next`, and the four
flags; that the two new `frontmatter` claims pass and catch a bogus key; that `check-contracts`'
owner parser reads the new templates' numbered items; and that `/dev-team:status` loads and
runs from the working copy.

## Method

- **1.1** `python3 evals/fixtures/state-cases/check.py`: 36 cases, each built by `build.py`
  into a temporary git repo (one commit per step), `status.py` run there, the row / lines /
  exit code checked. The checker was proven to bite: changing the cap to `n >= 4` in
  `status.py` failed `blocked-cap-round-3`; restored, it passed.
- **1.2** `check-contracts` over the bundle; then `agents/zz-scratch.md`, a copy of
  `curator.md` with `allowed_tools: Read` added, swept and removed.
- **1.3** a scratch bundle (the `planning-templates` directory only) with three throwaway
  `headings` claims: `deviations-entry.md` from `1. **Clause**` with a reader citing all eight
  fields, `review-report.md` from `1. **CRITICAL**` citing all seven headings, and a planted
  reader citing `Approved by`. Discarded after; the real claims land in phases 3 and 5.
- **1.4** `build.py repo` into the scratchpad, then `claude --plugin-dir ./dev-team
  --allowedTools Bash --output-format stream-json -p "/dev-team:status --repo"` and the same
  with `data`, reading the Bash tool result from the stream. Cost $0.16.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 1.1 state cases | `check.py` exit 0, every case in the fixture README passes | `36/36 pass`, exit 0 — the 29 cases the note lists plus `design-probe-other-section`, `shipped-sync`, `run-gate-dirty-exempt`, `run-gate-no-contract`, `surface-pass`, `surface-fail`, `surface-na` | ✓ |
| 1.1 planted cap bug | `blocked-cap-round-3` fails | `1/2 pass; failed: blocked-cap-round-3` | ✓ |
| 1.2 contracts | all claims PASS, the two `frontmatter` claims counted | `28/28 pass`: `8 files, every key documented` (agents), `29 files` (skills) | ✓ |
| 1.2 planted key | the agent `frontmatter` claim FAILs | `FAIL … agents/zz-scratch.md:4 'allowed_tools' is not a documented agent field` | ✓ |
| 1.3 owner parser | 8 items from `deviations-entry.md`, 7 from `review-report.md` | `8 names across 1 readers, all owned`; `7 names …, all owned`; planted `Approved by` → `FAIL … reader.md names 'Approved by'` | ✓ |
| 1.4 load, `--repo` | output has `packages:` | the skill ran `python3 …/dev-team/skills/status/scripts/status.py --repo` (`${CLAUDE_SKILL_DIR}` resolved); tool result opens `packages:\n  - data: planned\n  - analysis: no contract` and lists all six groups | ✓ |
| 1.4 load, `next:` | output has `next:` | `--repo` prints no `next:` by the note's own `--repo` spec (six groups only); `/dev-team:status data` printed `next: answer D3 in docs/decisions.md, then /dev-team:run-package data`. The scratch repo was left clean | ✓ (bar amended) |

## Verdict

Holds. One amendment to a pass bar, recorded as a Deviation in the phase note: row 1.4 asked
for a `next:` line from `--repo`, which the same note specifies without one, so `next:` was
checked on the plain package report instead. Also recorded there: the probe-doc re-open rule
ignores commits that only touch another section's `## <pkg>/<section>` entry (case
`design-probe-other-section`), so a new consuming section's PROBE step does not re-open every
existing design that cites the same source.
