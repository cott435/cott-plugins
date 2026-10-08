# audit-run phase 4 — a first audit files the planted defects as issues, writes the run report, and commits `audits/` once (B4.1, B4.2)

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `1465e84`): `skills/audit-run/SKILL.md` · model: Sonnet 5.5 (`sonnet`) for executors and graders · 2026-10-07
**Set:** `evals/sets/audit-run.json` evals 5 (B4.1), 2 (B4.2) · **Iteration:** `evals/workspace/audit-run/iteration-3` (both), `evals/workspace/audit-run/iteration-4` (B4.1 after the fix) · **Baseline:** previous = `359f45e` (`old_skill`) for both · **Pass rate:** iteration 3: B4.1 with_skill 8/13 (62%) vs old_skill 1/13 (8%), B4.2 with_skill 8/8 vs old_skill 8/8; iteration 4 (revised set, 16 expectations): B4.1 with_skill 15/16 (94%) vs old_skill 1/16 (6%) · **Blind:** not run (pass rates 27 and 88 points apart)

## What was tested

B4.1: that `/plugin-dev:audit-run 0a0d17f0`, run from the toy plugin, files each planted
defect as an issue through `issues.py`, writes `audits/runs/<date>-0a0d17f0.md` from the report
template with issue ids on its headings, keeps `INDEX.md` in step, makes exactly one `audits/`
commit, logs the short form and says so in its first line — and that the 0.15 skill does not.
B4.2 (regression): that the two run-auditors audit-run §4 spawns still find P1–P5.

## Method

- One iteration, both rows, `--baseline previous` (the note's value; the set says `none` for
  eval 2, and `S init` refuses mixed baselines). One run per configuration; executors and
  graders on Sonnet 5.5; skill-creator's grader and `aggregate_benchmark`.
- **Voided and rerun:** eval 5 `with_skill`'s first executor broke a harness rule — a
  mistyped `cd` ran three `issues.py new` calls in the real plugin directory, creating
  `audits/PD-001..003` and `INDEX.md`, which it then deleted (the tree was confirmed clean,
  no `audits/`). Its run was voided and rerun with the same prompt. Eval 2's first two
  executors stopped without running: the set's prompt says "the trace from eval 1" and
  `$TMP` with no setup. They were rerun with eval 1's build spelled out (the fixture,
  `trace.py build … --out $TMP/ws`), as phase 1's B1.2 did, and told to copy `findings/` and
  the returns into `outputs/`. Both reruns finished; nothing was recorded as not run.
- Both eval 2 executors spawned run-auditor as general-purpose agents told to follow their
  plugin root's `agents/run-auditor.md`, so each side ran its own version of the agent.
- Cost: about 0.63M executor tokens (including the voided runs) and 0.29M grader tokens.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| B4.1 with_skill: issues for P1–P5 | ≥5 `TO-nnn` files covering all five | 14 files; P1 TO-003, P2 TO-002, P3 TO-001, P4 TO-004, P5 TO-005 | ✅ |
| B4.1 with_skill: frontmatter, sections, Found in lines | template keys and sections; unit, step, quote, report path + finding id | all 14 | ✅ |
| B4.1 with_skill: `issues.py check`, INDEX | `ok: 14 issues`, exit 0; 14 rows, all open | exact | ✅ |
| B4.1 with_skill: report headings | template order; every E/W heading `(new)` | order right; `### E8 · TO-001 (seen)` | ❌ |
| B4.1 with_skill: Totals | `… 0 seen again · prior: 0 …` | `issues: 14 new, 1 seen again` | ❌ |
| B4.1 with_skill: Prior issues, Flow chart line | empty table + `none: …`; workspace path + run-flow | exact | ✅ |
| B4.1 with_skill: no hand-written ledger, no workspace `report.md` | issues.py only | consistent, from a prose transcript | ✅ (weak) |
| B4.1 with_skill: one `audits/` commit | `toy audits: 0a0d17f0 — <n> new, 0 seen, 0 checked`, files only under `audits/` | one commit, 16 files under `audits/`, message says `1 seen` | ❌ |
| B4.1 with_skill: toy agents/skills untouched | nothing changed | nothing changed | ✅ |
| B4.1 with_skill: short eval log | headings, ids by outcome, `seen again: none`, `Report:` last line, no table | all but `seen again: TO-001 (in the same run, from the cross finding)` | ❌ |
| B4.1 with_skill: closing line | counts with `0 seen again`, report path, run-flow | `14 new, 1 seen again` | ❌ |
| B4.1 old_skill | fails at least one | 1/13: no `audits/`, no issues.py, a workspace `report.md`, the full findings table in the log | ✅ (bar) |
| B4.2 with_skill | 8/8 | 8/8: P1–P4 in `U01.md`, P5 and the `shipped:` relay in `seg-1.md`, one-line returns | ✅ |
| B4.2 old_skill | — | 8/8 | — |

All five B4.1 failures are one behavior: the cross auditor's finding that `abc1234` travelled
to the user (E8) cites the same writer rule as the unit finding E1, so step 4's `candidates`
listed TO-001 — filed a minute earlier in the same audit — and the run called it `seen`. §5
step 4 says what to do when a candidate matches, but not that an issue this audit just filed
is not "seen again", and step 1's merge did not fold the cross finding into E1.

## Verdict

B4.2 held (no regression in §4). **B4.1 missed its pass bar** — 8/13, with every miss from
one cause: a same-audit duplicate counted as `seen again`. The old skill fails as required
(1/13). Graders also noted, for the set: the four "0 seen" expectations over-weight one
behavior; nothing bounds the issue count (14 issues for 5 defects) or checks fault labels
(TO-005..007 are driver acts filed `fault: agent`); the "issues.py new in transcript.md"
expectation cannot be checked against a prose transcript; eval 2's citation check depends on
trace files outside `outputs/`. Stopped for review before the one fix the note allows.

## Iteration 4 — after the one fix

**The fix** (at the reviewer's choice, inside the note's Files): audit-run §5 step 1 now merges
a `cross` finding that restates one unit's or segment's finding (the same act against the same
rule, whatever fault each auditor gave it); step 4 says `seen` is only for an issue that
existed before this audit, so a match against an issue this audit just filed is folded into
that finding and nothing is filed for it; and `--fault`/`--severity` are taken as the auditor
gave them.

**The set fixes** (run-evals step 7, all the graders' points, at the reviewer's choice):
eval 5's four "0 seen" checks became one expectation and the others take `<s>` from the
Totals line; new expectations that no planted act is filed twice, and that each issue keeps
its finding's fault and severity with an `applies_to` matching where it was first found;
the transcript expectation now relies on a harness line requiring every shell command
verbatim. Eval 2 gained a harness file (`evals/sets/files/audit-run/auditors-on-fixture.md`)
that spells out building "the trace from eval 1" and copies the trace and toy definitions into
`outputs/`, and its last two expectations point there. Eval 2 was not rerun: the rewrite
changes no verdict.

**Result:** with_skill 15/16, old_skill 1/16. The run filed 8 issues for 7 ERROR and 2 NOTE
(the cross restatements merged into E1, E2 and E6), `0 seen again` everywhere, the commit
`toy audits: 0a0d17f0 — 8 new, 0 seen, 0 checked` touching only `audits/`, the short log
and the right closing line. The one miss is the transcript expectation: the executor ran the
filing loop as a script (`bash file-issues.sh`), listed it as one line, and did not keep the
script, so the eight `issues.py new` commands cannot be read from `transcript.md`. The outputs
are consistent with issues.py having written everything (`INDEX.md`'s generated header,
`issues.py check` → `ok: 8 issues`, Found in lines in its format) but that is not the evidence
the expectation asks for. After grading, the harness gained "paste a script's whole body into
`transcript.md` and keep the file", and the eval-log expectation now says *the Tested against
field* (log-eval writes it as a bold field, not a heading); neither changes a verdict, so no
rerun. The old skill's one pass is still the trivially-true "agents/ and skills/ unchanged".

**Verdict after the fix:** B4.1's bar (every expectation passes) is still missed by one
expectation, and that one is about the executor's transcript, not the skill's behavior. A
Deviation in note 04; committed as it stands at the reviewer's choice.
