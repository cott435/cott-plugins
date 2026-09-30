# Audit · dev-team 2.0.0 · /dev-team:run-package data (×2) · session f1c390a1

> Added to the repo by `plugin-dev:plan-phases` for `site/notes/2.2-design.md`, which cites this path. The
> report's `flow.html` and `findings/*.md` were not carried in; the E/W/F items below are what 2.2 fixes.


**Run:** /Users/connorott/PycharmProjects/quant · data_build · 2026-09-29 14:27 → 17:30 (still running: U29) · claude-opus-5-5 · 29 units, 12 audited + 2 driver segments + cross
**Rules checked against:** /Users/connorott/.claude/plugins/cache/cott-plugins/dev-team/2.0.0 (the version that ran)
**Flow chart:** `flow.html`, beside this report
**Totals (as the auditors wrote them):** 48 ERROR · 26 WARN · 62 NOTE. **After merging:** 18 ERROR · 17 WARN · notes as filed

All `definition` faults below are **still at HEAD** (2.1.0): the rules they quote are unchanged in the working tree.

## Errors

### E1 · definition · reviewers split on design §10 contract-row deviations
cross F1 (covers U03 F1) · evidence `U03.S50–S55`, `U07.S66`, `U09.S85`, `c7a0260` vs `c263335` ledgers · rule `agents/reviewer.md:295-297` against `agents/designer.md:222-229` · still at HEAD
Fix 6 (2.0.0) had the designer file its §10 contract deviations as `deviation` entries for the round-1 `a` reviewer to rule on, but reviewer.md still says any entry whose Clause is a contract row is rejected. Four parallel `a` reviewers resolved the conflict differently. U05 rejected priceaudit's entries, which sent priceaudit alone through PLAN, a change file and a delta design. U03, U07 and U09 approved the same kind of entries for retrieval, financialaudit and ingest. Three reviewers also wrote contradictory rules into one memory file (cross F11), so the split will carry into later sessions. Fix: give reviewer.md an explicit rule for designer-raised §10 entries, saying which contract changes it may approve and which boundary changes it must reject or turn into `spec-change:contract`.

### E2 · definition · return messages ignore their forms and caps
cross F2 (covers U02 F2, U03 F2, U15 F5, U16 F3, U17 F1, U18 F5, U19 F5, U20 F2, U22 F3) · rule `agents/tester.md:209-229`, `agents/implementer.md:612`, `agents/reviewer.md:370` · still at HEAD
Nine audited units and several unaudited ones added fields the forms don't define (`Flags for designer:`, `For the driver:`, `Process note:`, `Suite:`, `Main WARNINGs`), ran past the line cap, or packed several values into one field. The added content is information the forms have no place for, and the driver reads only the first line, so it is lost (E14). Fix: add the fields the agents keep needing, or say where each kind of content goes (the report, `docs/followups.md`).

### E3 · definition · delta and fix runs skip the required reads
cross F3 (covers U12 F2, U15 F3, U15 F4, U16 F2, U18 F3, U18 F4, U19 F1, U20 F1, U22 F1) · rule `agents/implementer.md:56`, `agents/tester.md:132-133` and `:171`, `agents/designer.md:146-168` · still at HEAD
Every audited delta or round-2 agent worked from the design diff and the reviews. None read the package contract, the repo contract or `docs/decisions.md`, and most skipped their Dependency READMEs. The testers also skipped the TDD RED paragraph. The delta paragraphs say only which steps apply to the change, and they never say the full reads in step 1 still apply. Fix: add that sentence to each delta paragraph, or name the reads a delta may skip.

### E4 · definition · repo files written through Bash bypass both hooks
cross F4 (covers U12 F3, U15 F2, U01 F4, U19 F7, U22 F10) · rule `hooks/hooks.json:6,22` (`"matcher": "Write|Edit"`), `agents/tester.md:48` · still at HEAD
Six units wrote files with heredocs, `sed -i` or `cat >>`, so neither the ruff hook nor the write guard ran on those writes. Two implementers wrote their entire change this way, and three units rewrote shared memory files by shell. Fix: put the "no writes by shell" ban in implementer.md and designer.md too, or have the guard also inspect Bash.

### E5 · definition · shell paths outside the repo (harness tool-results, scratchpad)
cross F5 (covers U04 F2, U18 F2, U20 F4, U22 F4, part of U16 F1) · rule `agents/implementer.md:19-20`, `agents/reviewer.md:102`, `agents/tester.md:49` · still at HEAD
The harness itself pointed agents at `~/.claude/projects/…/tool-results/*.txt` for long outputs and at `/private/tmp/…/scratchpad` for throwaway files, and five units used those paths from Bash. No definition says how to handle either. Fix: read a persisted tool result with the Read tool, and put throwaway output in an ignored in-repo path such as `.dev-team/tmp/`.

### E6 · definition · testers execute code with `python -c`, including the section's own
cross F6 (covers U16 F1, U18 F1, U15 F6, U16 F7) · rule `agents/tester.md:32`, `:45-48` · still at HEAD
All three first-run delta testers ran code to learn facts for their tests, and U16 and U18 ran the section under test itself, which breaks the "tests from the documents, never from the source" rule. Each was following a tester memory note that recommends the practice. Fix: say Python runs only through the test command, and that a memory note contradicting the Hard rules is wrong.

### E7 · driver · relays return bodies to the user
seg-1 F1 + seg-2 F1 · evidence `D9`, `D59`, `D73`, `D77`, `D81`, `D97` · rule `skills/run-package/SKILL.md:28`, `:215-217` · agent fault
The driver told you things found only after a return's first line: failure counts, "an exact float comparison", "all 261 intent tests green". The skill forbids reading a `done` or `spec-change` body. Auditor's comment: the harm is low here, and the relayed facts were true. But the rule exists because a summary can be wrong, and E9 to E13 show the returns do contain false claims.

### E8 · driver · re-derive filters the status table and narrates instead of printing changed rows
seg-1 F2 + seg-2 F2 · evidence `D14`, `D32`, `D36`, `D47`, `D68`–`D106` · rule `skills/run-package/SKILL.md:246` (2.0.0 `:226`) · agent fault
Every re-derive after the first ran `status.py data | grep <sections>`, which hides the 11 DONE rows and the `shipped:` line, and the driver then narrated in prose. If a batch had re-opened an upstream section, the driver would not have seen it. It cost nothing this time.

### E9 · agent · U15 did not return `design-gap` for a row with no signature
U15 F1 · evidence `U15.S66`, design `7ba82bd` line 190 · rule `agents/tester.md:114-119` · agent fault
The retrieval delta design's Interfaces row `empty_indicator_panel / empty_coverage / fill_absent | selection.*` has no signature. The rule says to write nothing and return `design-gap`. The tester listed the row under `Not written:` and wrote and committed the rest anyway.

### E10 · agent · design Skills used were never invoked
U19 F2 + U22 F2 · evidence `skills invoked: none` in both headers, and the designs' §9 · rule `agents/implementer.md:233` · agent fault
retrieval's round-2 fix (provider symbol spelling) is exactly what the project skill `database_retreival` covers, and priceaudit's design names `data_validation`. Neither implementer invoked the skill its design named.

### E11 · agent · U19 fixed bugs before writing a failing test
U19 F3 · evidence `U19.S28`, `S31`, then `S40` · rule `agents/implementer.md:297` (Prove-It) · agent fault
U19 fixed two review WARNINGs that were bugs in code first. Their tests were written afterwards and passed on the first run, so neither test was ever seen failing.

### E12 · agent · false or unbacked claims in returns
- U04 F1: "8 warning", but its committed report has 9 WARNING bullets (verified).
- U12 F1: "OQ-1 to OQ-11 carry over unchanged", but OQ-6 and OQ-11 changed in 7ba82bd (verified).
- U16 F4: "5 §5 build_context tests" tagged, but the commit tags 6.
- U19 F4: "the unbuilt ingest/financialaudit/priceaudit intent suites fail it" came from memory, was never checked, and is wrong for financialaudit, which was DONE.
- U20 F3: "no D<n> binds this section", while its own grep shows D4 `Scope: repo`, `Status: open` (U22 F7, a WARN, repeats this).

### E13 · agent · process rule breaks by single units
- U02 F1: the regenerate tester ran `git show --stat HEAD`, which printed the file names under the section's source path.
- U03 F3: the reviewer used `cat`, `grep`, `sed` and `ls` in Bash, which are outside its closed list of Bash uses.
- U03 F4: the reviewer read the deviations template with `cat` and only after reading the ledger, which is the reverse of the required order.

## Warnings

- **W1 · cross F7 · a known design defect shipped.** U16 found that priceaudit's `may_snap` pre-filter rejects ratios in [1.2250, 1.2255) that `snap` accepts, but reported it in an invented field no one reads. U22 built it as designed, and U25 re-found it as a WARNING and approved. priceaudit is DONE with the defect recorded only in a review report. No role has a way to send a design defect that isn't a gap back to the designer. Still at HEAD.
- **W2 · cross F8 · no owner for resolving `spec-change:design|test` entries.** The agents named five different owners. retrieval's and priceaudit's entries are still `open` on DONE sections. Rule `deviations-entry.md:26`, still at HEAD.
- **W3 · cross F9 · deviation tags churn.** The tag matches only `§<n>` plus the first word of the item, so testers tagged 9, 10 or 17 tests for one clause, and reviewers then flagged the extra tags. In retrieval the count grew across rounds instead of converging. Rule `tester.md:192`, still at HEAD.
- **W4 · cross F10 · `Mode: delta` with `Adopted code: no` is undefined for testers.** All three kept tests that already pass, against the red-by-construction rule. Rules `tester.md:152-154` and run-package's Adopted-code mapping, still at HEAD.
- **W5 · the implementers' security check was thin or missing.** U01 F3 ran only `ruff --select S` but claimed "nothing logs secrets". U19 F6 recorded no security decision at all on code that sends caller input into DuckDB. U20 F5 understated what it had run.
- **W6 · test and lint claims.** U01 F1: the test command reported was not the one that ran. U01 F2: "pylint 10.00" came from a run with only 2 checks enabled.
- **W7 · memory index rewritten by shell** (U01 F4, U19 F7), part of E4.
- **W8 · U03 F5 · public-shape changes approved as internal.** Three approved §10 entries change public shapes (`DataSelection.fundamentals_lineage`, a `resolve` status value, and a `settings` kwarg on every public function). This is part of E1.
- **W9 · U12 F4 · delta scope creep.** The retrieval delta designer re-based §3–§5 and answered a spec-change it was not sent.
- **W10 · U16 F6 · unbacked classification.** U16 said all 49 failures were delta items, but the trace never shows them classified.
- **W11 · U16 F8 · hook feedback left unfixed.** Format-hook feedback sat unaddressed for a few steps before the tester fixed it.
- **W12 · U18 F6 · two counts in the return don't match the run.**
- **W13 · U22 F5 · whole directories committed.** U22 staged whole directories instead of named files. It was harmless this time.
- **W14 · U22 F6 · PLR0913 dodged.** U22 cleared the too-many-arguments check by packing three parameters into a tuple.
- **W15 · U02 F2 and U12 F5 · return fields over the template** (part of E2).
- **W16 · seg-1 F3 · the final message was prose before the Summary block.**
- **W17 · seg-2 F3 · filtered status output** (part of E8).

## Notes

- **Not audited, observed while spot-checking:** every gate record in quant has `TIMEOUT` for `uv run --package data pytest packages/data/tests` (240 s) and `uv run pytest packages/*/tests`, and several say `mkdocs build --strict not run: the gate's 540s budget was spent`. The package-wide suites never finished inside any gate, so fix 1's ELSEWHERE path was never exercised: no gate record has an ELSEWHERE line.
- **Fixes 2.0.0 exercised and working:**
  - fix 3: per-section gate files (`.dev-team/gate/data/<section>.txt`);
  - fix 4: per-section ledgers, with parallel commits holding only their own files;
  - fix 5: `b`'s report re-opened DESIGN (`ingest · DESIGN · open docs/reviews/…-ingest-r1-b.md — spec-change:design`);
  - fix 6: designer §10 ledger entries, but see E1;
  - fix 8: delta designers.
- **Not exercised:** no stop gate exited 2 in this run (every hook block was the format hook), so the gate-retry handback was not tested.
- cross F12: a reviewer's `Commit:` is HEAD at write time, which in a parallel batch is often a sibling's report commit.
- cross F13: every same-day entry for a section shares one heading, so "by heading" citations are ambiguous.
- cross F14: the ` (deviation <date>)` tag pushes docstring first lines past 88 characters.
- cross F15: the rework loops, with their causes (priceaudit PLAN detour from E1; a float `==` intent test from U16 that can never pass).
- The per-unit NOTE findings (62 total) are in `findings/*.md`. Most are definition gaps already folded into E1–E6 and W1–W4.

## Audited

| Unit | Type | Description | Verdict | E/W/N |
|---|---|---|---|---|
| U01 | implementer | Implement data/ingest | spec-change | 0/4/6 |
| U02 | tester | Regenerate ingest intent test | done | 1/1/3 |
| U03 | reviewer | Review retrieval conformance r1 | spec-change | 4/1/2 |
| U04 | reviewer | Review retrieval correctness r1 | spec-change | 2/0/3 |
| U12 | designer | Design delta retrieval | done | 3/2/7 |
| U15 | tester | Tests for retrieval | done | 5/1/5 |
| U16 | tester | Tests for priceaudit | done | 4/4/5 |
| U17 | tester | Tests for financialaudit | done | 1/0/3 |
| U18 | tester | Tests for ingest | done | 5/1/5 |
| U19 | implementer | Implement data/retrieval delta | done | 5/2/4 |
| U20 | implementer | Implement data/priceaudit delta | spec-change | 4/1/5 |
| U22 | implementer | Implement data/priceaudit delta | done | 4/3/3 |
| seg-1 | driver | run-package data D1–D59 | — | 2/1/4 |
| seg-2 | driver | run-package data D60–D107 (partial) | — | 2/1/2 |
| cross | — | whole run | — | 6/4/5 |

## Not audited

- U05–U11, U13, U14, U21 and U23–U28 were not selected by `risk` (the first unit of each type was already selected, and these did not stand out). The cross auditor used their returns as supporting evidence.
- U29 (tester, data/digest) was still running when the trace was built.
- Every auditor returned on the first try.

## Dropped on spot-check

None. I checked the cited step and rule for U02 F1, U04 F1, U12 F1, U15 F1, U16 F4, U19 F2/F4, U20 F3, U22 F2, seg-1 F1/F2 and cross F1 against the trace, the quant repo and the 2.0.0 files. All held.
