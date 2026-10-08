# audit-run phase 4 — the two template `headings` claims, planted to fail and then passing (M4.1)

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `1465e84`): `contracts.yml`, `skills/audit-run/SKILL.md` · model: none (a script, checked by script) · 2026-10-07
**Set:** none — M4.1 is a row of `site/notes/0.16-audit-ledger-04-audit-writes-ledger.md` **Evals** with no set · **Iteration:** none, run in the phase chat · **Baseline:** none · **Pass rate:** M4.1 2/2 (negative run FAILs both new claims; real bundle 10/10)

## What was tested

That the two claims appended to `contracts.yml` — *audit-run names only issue-file sections the
issue template defines* and *audit-run names only run-report sections the report template
defines* — fail when audit-run's cited sections are not the templates' `##` headings, and pass on
the real bundle after audit-run §5 and §6 were rewritten.

## Method

- Note 04 step 1 expected `check-contracts` to FAIL right after the claims were appended,
  "audit-run does not yet name the sections". It did not: the run printed 10/10 PASS. The
  `headings` check (`scripts/contract_sweep.py` `check_headings`) compares each reader's `cites`
  list against the owner's headings; it never reads the reader file for those names, so a claim
  whose `cites` are all template headings passes whatever audit-run says. (A Deviation in note
  04.)
- The negative half was therefore run the way `check-contracts` says a new claim is proven: a
  planted defect in a copy. `rsync` of the plugin (minus `evals/workspace`, `site/docs`) to a
  scratch directory; in the copy, `templates/audits/issue.md`'s `## Checks` renamed
  `## Rerun checks` and `templates/audits/run-report.md`'s `## Prior issues` renamed
  `## Prior fixes` — a template heading renamed with audit-run left naming the old one, the
  drift these claims exist to catch. `python3 scripts/contract_sweep.py` in the copy.
- The positive half: `python3 scripts/contract_sweep.py` in the real plugin directory after
  audit-run's edit.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Claims appended, audit-run unedited (note's step 1) | FAIL on the two new claims | 10/10 PASS — the check does not read the reader | ❌ as specified (see Method) |
| Planted: issue template `## Checks` renamed | FAIL naming audit-run's `Checks` | `FAIL audit-run names only issue-file sections the issue template defines — skills/audit-run/SKILL.md names 'Checks'` | ✅ |
| Planted: report template `## Prior issues` renamed | FAIL naming audit-run's `Prior issues` | `FAIL audit-run names only run-report sections the report template defines — skills/audit-run/SKILL.md names 'Prior issues'` | ✅ |
| Planted copy, everything else | the other 8 claims PASS | 8/10 pass, exit 1 | ✅ |
| Real bundle after audit-run's edit | 10/10 PASS | 10/10 PASS, exit 0 (`3 names across 1 readers`, `7 names across 1 readers`) | ✅ |

## Verdict

Held, with one correction to the plan: the two claims catch a template heading renamed under
audit-run, and the real bundle passes. They do not catch audit-run *failing to mention* a
section — no `headings` claim does — so the note's "must FAIL before step 2" could not be
observed. Recorded as a Deviation in note 04; the checker is unchanged.
