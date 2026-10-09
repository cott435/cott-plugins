# <UNIT> — <scope in five words>

Read: <each file read, with its line count; sections named where the row named one>

<!-- One file per unit, at site/notes/<slug>/findings/<UNIT>.md. scripts/edits.py findings
     checks it: the two required sections below exist; every block under Findings has every
     field; kind and severity come from the lists below; ids are unique across all units. -->

## Context budget

<Optional: what this unit's part loads before it reads a repo file, in lines, now and after
the findings below.>

| What | Lines now | Lines after | Note |
|---|---|---|---|

## Findings

<One block per finding, twelve lines or fewer, ERROR first.>

### F-<UNIT>-01 <the defect, in one line>
- kind: contradiction | underspecified | prose-to-script | script-defect | missing-check | duplication | bloat | missing-test
- severity: ERROR | WARN | NOTE
- files: <path:line, path:line>
- issues: <audit issue ids | none>
- mechanism: prose | hook | script | contracts.yml | eval
- claim: <what is wrong, one or two sentences; a contradiction quotes both sides>
- fix: <one edit a fresh chat can make; a script: the input, the exact line it prints or refuses, the exit code; prose: the lines that go and the line that stays>
- saves: <always-loaded lines removed, or 0>
- evals: <set and ids a comparator re-runs | none>
- proof: <what differs between baseline and the fix: an eval's observable, a fixture input → output, or the contracts.yml claim>

`severity`: ERROR when a run goes wrong because of it; WARN when it costs a round, a re-spawn
or a wrong document; NOTE for context cost and clarity. A finding that is two kinds is two
findings.

## Rules a script could enforce

| Rule (quote, path:line) | Enforced now by | Mechanism proposed | Other files stating it |
|---|---|---|---|

## Issues reviewed

| Id | Status | Rule still at its line | Note |
|---|---|---|---|

## Checked, no finding

<One line per thing checked that held, so the reconciler knows what was covered.>
