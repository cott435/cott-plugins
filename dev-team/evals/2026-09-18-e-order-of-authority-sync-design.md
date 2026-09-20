# E — the reviewer's order of authority, the recorded-deviation rule, and `sync-design`

**Tested against:** uncommitted — see working-tree diff (phase 3 of the 0.5 overhaul, on top of
`29551f2`): `agents/reviewer.md`, `agents/implementer.md`, `agents/architect.md`,
`skills/sync-design/SKILL.md` (new), `skills/plan-change/SKILL.md`,
`skills/review-package/SKILL.md`, `contracts.yml` · model: `claude-sonnet-5` (the CLI default in
the headless runs; every agent on `inherit`) for the behavioral part; `claude-opus-5` ran the
mechanical script · Claude Code `2.1.270` · 2026-09-18

## What was tested

Note 09 eval E, three claims:

- **Mechanical.** The reviewer's order-of-authority list and the implementer's are the same
  list: the numbered, bolded item names extracted by regex from each agent's
  `## Order of authority` section are equal, in order, after whitespace normalization.
- **Behavioral, reviewer.** On a section with one deviation recorded in README item 7 with a
  reason and one it does not record, the report has exactly one WARNING that names
  `/dev-team:sync-design` (the recorded one) and exactly one CRITICAL (the unrecorded one).
- **Behavioral, sync-design.** `/dev-team:sync-design data` appends an **As shipped** section
  with exactly one row (the recorded deviation) to the design, changes nothing above it, and
  commits.

## Method

**Mechanical**: a 10-line script extracts `^\d+\. \*\*(.+?)\*\*` from `implementer.md` between
`## Order of authority` and `## The decisions file`, and from `reviewer.md` between
`## Order of authority` and `## Bash usage`, then compares the two lists. Negative controls run
on a scratch copy of the plugin: (1) rename reviewer item 2; (2) replace reviewer item 4's
path with item 5's. Both are run through the script and through `check-contracts`. The
`As shipped` heading contract is checked the same way by renaming sync-design's item. No model
cost.

**Behavioral**: real headless runs, `claude -p "<command>" --plugin-dir ./dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`, on a
`reset.sh --no-constraints` copy of the fixture on branch `build`. Instead of running
`plan-repo` → `plan-package` → `implement-section` ($5+, not what this eval tests), the planned
and built state is written by hand and committed as one commit: `docs/architecture.md`, a
three-section `data` contract, `design/ingest.md`, `integration.md`, and a built `data/ingest`
(`reader.py`, `errors.py`, 4 passing unit tests, README). Two deviations are seeded:

- **Recorded, with a reason**: the design says `Trade.price: float`, the code ships `Decimal`,
  and README item 7 says what the design said, what shipped, and why (VWAP precision; stdlib).
  No contract names the type.
- **Unrecorded**: the design says `read_trades` returns trades "in file order"; the code
  returns them sorted by `ts`. README item 7 says nothing about it.

| Run | Repo | Command | Cost |
|---|---|---|---|
| 1 | `eval-e` — the design's Tests section also lists "file order is preserved" | `/dev-team:review-section data/ingest` | $0.42 |
| 2 | `eval-e2` — a clone of run 1's repo with that test line dropped (**contaminated**, see below) | `/dev-team:review-section data/ingest` | $0.58 |
| 3 | `eval-e3` — a fresh `reset.sh` copy, the same seeded files, test line dropped | `/dev-team:review-section data/ingest` | $0.45 |
| 4 | `eval-e3`, after run 3's commit | `/dev-team:sync-design data` | $0.31 |

## Results

Mechanical:

| Case | Expected | Observed | Pass |
|---|---|---|---|
| lists as written | equal | both `docs/decisions.md` · `The integration doc for this run` · `docs/plans/<slug>/contract-delta.md` · `docs/packages/<pkg>/contract.md` · `docs/architecture.md` · `The section's design doc` | ✅ |
| control 1 — reviewer item 2 renamed | script DIFFERENT; check-contracts FAIL | DIFFERENT; `FAIL … reviewer.md names 'The integration document'` | ✅ |
| control 2 — reviewer item 4 made a duplicate of item 5 | script DIFFERENT; check-contracts FAIL | DIFFERENT; **check-contracts 15/15 PASS** | ⚠ known gap |
| control 3 — sync-design's `As shipped` item renamed | FAIL for all three readers | `FAIL … reviewer.md, plan-change, implementer.md name 'As shipped'` | ✅ |
| `check-contracts` on the real files | all pass | 15/15 | ✅ |

Control 2 is the gap the note predicted: `check-contracts`' reader side collects only bolded
names that start with a capital letter, so the four items that open with a backticked path are
invisible to it. The contract checks the two plain-word items and that the reviewer's section
exists; the order and the four path items are held by this script, not by `check-contracts`.

Behavioral:

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 1 — recorded deviation | one WARNING naming sync-design | WARNING: "recorded deviation and WARNING at most: confirm `/dev-team:sync-design` has run" | ✅ |
| 1 — unrecorded deviation | one CRITICAL | CRITICAL on `reader.py:54`, "the failure is the silence, not the sort" — **plus a second CRITICAL** for the design-listed "file order is preserved" test being absent | ⚠ seeding error |
| 3 — recorded deviation | one WARNING naming sync-design | WARNING at `reader.py:32`: "recorded … with a reason … flagged only so `/dev-team:sync-design` runs" | ✅ |
| 3 — unrecorded deviation | exactly one CRITICAL | exactly one: `reader.py:54`, "silently unrecorded in the README's Implementation notes" | ✅ |
| 3 — other findings | — | two unrelated WARNINGs (one-line module docstrings; no `__init__` docstring on `IngestError`), one SUGGESTION | n/a |
| 3 — commit | `review data/ingest: …` + trailer | `4e8da55 review data/ingest: request changes (1 critical)` / `Dev-Team-Run: review-section data/ingest` | ✅ |
| 4 — As shipped rows | exactly one, the `Decimal` deviation | one row: `Trade.price: float` → `Decimal`, the README's reason, "README item 7"; `Source:` line cites the README and `73962ea` (the section's last commit) | ✅ |
| 4 — the unrecorded sort | not folded | not folded | ✅ |
| 4 — nothing above the heading changes | 0 removed lines | `git diff HEAD~1` on the design: 16 insertions, 0 deletions; one file in the commit | ✅ |
| 4 — commit and return | `plan data: sync-design, …` + trailer; next command `/dev-team:implement-section data/clean` (no `interface.md`) | `7f46ae7 plan data: sync-design, 1 section, 1 deviation folded` / `Dev-Team-Run: sync-design data`; next command as expected | ✅ |
| 4 — fork | architect runs as the forked agent | 0 tool calls in the main thread | ✅ |
| 4 — template adherence | the template and nothing else | the template, plus a trailing `Note:` paragraph pointing at the unfolded, unrecorded sort and its open CRITICAL | ⚠ minor |

**Run 1's second CRITICAL is a seeding error, not a split failure.** The design listed a test
that the code could not pass, and "every listed test exists" is its own spec-conformance item.
Run 3 removes that line and the count is exactly one. **Run 2 is discarded**: it cloned run 1's
repo, so `origin/build` still held run 1's review commit. The reviewer found it and said so ("I
independently re-derived the same finding"), and it still filed the missing-coverage CRITICAL.
Its report agrees with runs 1 and 3 on the split, but it is not a clean reading.

**Worth noting from runs 1 and 2:** both times, the reviewer added unprompted that recording
the sort would not have saved it, because the contract gives sorting to `clean` (rule (a)). Run 3
cited the integration doc's resolution instead. Both are the order of authority working as
written.

## Verdict

**Holds.** Mechanical: the two lists are identical. `check-contracts` catches a renamed item.
It does not catch a reordered or swapped path item, so that stays this eval's job. Behavioral,
on the clean run: 1 WARNING naming `sync-design` and 1 CRITICAL, as the rule requires, and
`sync-design` appended exactly one As shipped row, append-only, in one commit with the trailer.
Two small observations, neither changed in this phase: `sync-design` wrote one explanatory
paragraph outside its template, and the reviewer may file a missing listed test as a second
CRITICAL next to an unrecorded deviation. Both are logged here for phase 9's end-to-end run to
watch.
