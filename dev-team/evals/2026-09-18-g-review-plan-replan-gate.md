# G — review-plan finds seeded defects; plan-package re-plans only the affected section; the plan gate passes after

**Tested against:** uncommitted — see working-tree diff (phase 5 of the 0.5 overhaul, on top of
`f81b6bd`): `skills/review-plan/SKILL.md` (new), `agents/reviewer.md`, `agents/architect.md`,
`agents/designer.md`, `agents/implementer.md`, `skills/plan-package/SKILL.md`,
`skills/status/scripts/status.py`, `skills/status/SKILL.md`, `contracts.yml` · model:
`claude-sonnet-5` (the CLI default in the headless runs; every agent on `inherit`, and every
run's `modelUsage` shows only `claude-sonnet-5`); `claude-opus-5` ran the checks · Claude Code
`2.1.270` · 2026-09-18

## What was tested

Note 09 eval G, the three-run sequence in note 05 §Steps 5. A plan seeded with two defects
must produce exactly two CRITICALs and two `data/plan` follow-ups:

- a consumed name that no design provides;
- an `OQ` with no `D`.

A `plan-package` re-run must then re-delegate exactly one designer and tick both follow-ups.
A second `review-plan` must approve, and `status.py --plan-gate data` must pass. Also from
note 05 §Done when: the implementer blocks on an open plan finding.

## Method

**Behavioral**: real headless runs, `claude -p "<command>" --plugin-dir <abs>/dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`, on a
`reset.sh --no-constraints` copy of the fixture on branch `build`. Unlike evals E and F, the
planned state is real: `plan-repo`, then `plan-package data`, with no hand-written documents.

| Run | Command | Cost | Result |
|---|---|---|---|
| 0 | `/dev-team:plan-repo` | $0.68 | `5ee5621`, probe `trades` readable, 0 decisions |
| 1 | `/dev-team:plan-package data` | $1.10 | `edba338`. 3 designers. **6 designer `OQ-…` tags, 0 `D<n>` stubs, no `decisions.md`.** The architect applied its "stub what matters" cost test to designers' questions |
| 1b | same, after tightening step 8 | $0.24 | no-op: designs were current, so it skipped to "nothing to write" and never reached step 8. Discarded |
| 1c | same, from `5ee5621` again | $1.20 | `731d970`. 7 OQs: 4 → D1–D4, 3 resolved *by tag* in `integration.md` §2 (the shared `Trade` home). The **baseline** |
| seed | hand commit `5322766` | — | `clean.md` §2/§4/§7: `ingest.load_rows` → `ingest.read_trades` (ingest §5 provides only `load_rows`); `storage.md` §11 gains `OQ-data-storage-3` (optional `symbol` filter), with no `D` |
| 2 | `/dev-team:review-plan data` | $0.63 | request changes, 2 CRITICAL |
| 2b | `/dev-team:implement-section data/ingest` | $0.30 | blocked |
| 3 | `/dev-team:plan-package data` (re-plan) | $0.41 | **0 designers**; answered both findings in `integration.md` §2 and D5. Kept on branch `replan-integration-only`, then reset |
| 3b | same, after the "a design's own defect is answered by its revision" rule; `.claude/agent-memory/` moved aside | $0.66 | 1 designer (`data/clean`) |
| 4 | `/dev-team:review-plan data` | $0.62 | approve with fixes, 0 CRITICAL |

Total $5.84. Evidence comes from each run's result event (`subagent_stats.by_type`) and from
git.

**Mechanical**: `status.py --plan-gate data` on the eval repo after every run, then on a
clone with one condition changed at a time (ten cases below). `contract_sweep.py` on the real
files, then on a scratch copy with three planted renames. No model cost.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| run 2 — CRITICALs | exactly the two seeded | 2: `design/clean.md#2`/`#4` consumes `ingest.read_trades`, which nobody provides, and `integration.md` §2 doesn't resolve it; `design/storage.md#11` `OQ-data-storage-3` has neither a `D` nor a resolution. Plus 1 WARNING (surface `Trade` row has no design `Public: yes`), which is real and non-blocking | ✅ |
| run 2 — follow-ups | two `- [ ] data/plan: … — review <date>, see …` | exactly two, in that form | ✅ |
| run 2 — report and commit | `Commit:` = HEAD at start; one commit `review data/plan: …`, trailer | `Commit: 5322766…`; `4496713 review data/plan: request changes (2 critical)`, `Dev-Team-Run: review-plan data`; staged report + `followups.md` only | ✅ |
| run 2 — findings cite `<document>#<heading>` | yes | yes | ✅ |
| implementer blocked by an open plan finding | blocker naming `plan-package data` and the review | "Blocked: open plan finding", both entries quoted, names `/dev-team:plan-package data` and the review file. Nothing written, no commit | ✅ |
| gate after run 2 | FAIL: verdict + open findings | `plan review verdict is request changes`, `2 open plan finding(s)` | ✅ |
| run 3 — re-delegates exactly one designer | 1 (`clean`) | **0**. Patched the seam in `integration.md` §2 ("clean's §5 never uses the name, only prose") | ❌ → fixed |
| run 3b — re-delegates exactly one designer | 1 (`clean`) | `{'dev-team:designer': 1}`. `clean.md` names `load_rows` everywhere and has a final **Revision** heading citing the finding. `storage` was not re-delegated: its OQ was answered by the D5 stub | ✅ |
| run 3b — ticks both | `[x] <date>` on both | both `- [x] 2026-09-18 data/plan: …`, with a resolution note appended | ✅ |
| run 3b — D5 | `Raised by: OQ-data-storage-3` | yes, with `Assumption if unanswered:` | ✅ |
| run 3b — return | names the review answered; next `/dev-team:review-plan data` | yes | ✅ |
| run 4 — approves | `approve` or `approve with fixes` | `approve with fixes`, 0 CRITICAL, 2 WARNING, 1 Carried. Reviewed by diff from the previous report's `Commit:` | ✅ |
| run 4 — report path | today's path | **`2026-09-18-data-plan-2.md`**: today's file existed, so the reviewer did not overwrite it | ✅ (see gate) |
| gate after run 4 | PASS | **FAIL, "plan not reviewed since last change"**: `latest_review` globbed only `<date>-<stem>.md` and never saw `-2` | ❌ → fixed |
| gate after fix | PASS | `plan gate: PASS`, `plan: reviewed 2026-09-18 approve with fixes @4529807` | ✅ |
| mech — clean | PASS | PASS | ✅ |
| mech — uncommitted design edit | FAIL not reviewed | FAIL not reviewed | ✅ |
| mech — D6 open, no assumption, `Scope: data/clean` | FAIL | FAIL `D6 is open with no assumption` | ✅ |
| mech — same, `Scope: analysis` | PASS | PASS | ✅ |
| mech — same, `Scope: repo` | FAIL | FAIL | ✅ |
| mech — `0. **Spine**` … `Status: spine only`, committed | FAIL spine-only (+ not reviewed) | both | ✅ |
| mech — spine `complete` | only not reviewed | only not reviewed | ✅ |
| mech — `-10` beside `-2` (request changes) | `-10` wins | `verdict is request changes` | ✅ |
| mech — open `data/plan` follow-up | FAIL | FAIL `1 open plan finding(s)` | ✅ |
| mech — no `surface.md` | FAIL incomplete | FAIL `missing surface.md` | ✅ |
| `--gate` unchanged | finalize gate still runs | FAIL on 3 unbuilt sections, as expected | ✅ |
| contracts on the real files | 19/19 | 19/19 | ✅ |
| control — integration `Dependency order` renamed | FAIL | `FAIL … reviewer.md names 'Dependency order'` | ✅ |
| control — surface `Public names` renamed | FAIL | FAIL (owner span marker not found) | ✅ |
| control — designer `Skills used` renamed | FAIL | `FAIL … reviewer.md names 'Skills used'` | ✅ |

What was changed in response to the failures:

1. **Run 1 left designer OQs unstubbed.** This is not a review-plan failure: it is the defect
   review-plan exists to catch. But on a real plan it would have added six CRITICALs to every
   run. The architect's "Stub what matters" now separates the questions *it* raises from a
   designer's `OQ-…` tag. The tag gets a `D<n>` or a resolution in the integration doc that
   names it, never neither. `plan-package` step 8 says the same. The reviewer's item 5 accepts
   a named integration resolution, since the integration doc outranks the design. Run 1c
   confirmed the change (4 stubs + 3 named resolutions).
2. **Run 3 re-delegated nothing.** The first draft of **Plan findings** let the architect pick
   any document. It patched a design's own error in the integration doc, where the tester,
   which reads the design, would never see it. Now a finding whose object is a design is
   answered by that design's revision, and an `OQ` with no `D` is answered by the ledger.
   Run 3b confirmed it.
3. **Same-day re-review.** The reviewer's Output now says to write `-2`, `-3`, … and never
   overwrite a report. `status.py`'s `latest_review` ranks by date, then suffix, for section,
   package and plan reviews alike.

Seen but outside the checks:

- The re-delegated designer also brought `clean.md` in line with the earlier `Trade`
  resolution: it dropped a local `Trade` and `OQ-data-clean-1`. This is listed under
  **Revision** as "non-follow-up alignment". It is useful, but broader than "address each
  finding". `ingest.md` and `storage.md` stay pre-resolution, and run 4 flagged that as a
  WARNING.
- Run 3b's commit body carries prose and a `Co-Authored-By:` line beside the trailer. Same
  pre-existing drift as eval F.
- Run 4's integration §6 still lists D1–D4 without D5. The reviewer caught it as a WARNING.
  Unify was not re-run, because only `clean` was re-delegated.
- Run 1b: a `plan-package` re-run with every design current and no findings commits nothing
  and never re-checks step 8. That is harmless now, because review-plan catches the gap.

## Verdict

Holds after three fixes, each confirmed by a re-run on the same repo:

- the seeded defects gave exactly two CRITICALs and two `data/plan` follow-ups;
- the implementer blocked;
- the re-plan re-delegated exactly `data/clean` and ticked both follow-ups;
- the second review approved;
- `--plan-gate` passed.

The first re-plan re-delegated nothing, and the first gate after approval failed on a
same-day `-2` report; both are fixed. A real `plan-package` also showed the architect
dropping designer OQs, which is fixed at the source.
