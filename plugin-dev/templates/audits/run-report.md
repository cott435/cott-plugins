# Audit · <P> <version> · <command(s)> · session <id8>

**Run:** <project> · <branch> · <span> · <models> · <n> units, <n> audited
**Rules checked against:** <plugin root> (<the version that ran | working tree — see note>)
**Flow chart:** `runs/<project>/<run>/<id8>/flow.html` (gitignored; rebuilt with `/plugin-dev:run-flow <id8>`)
**Totals:** <n> ERROR · <n> WARN · <n> NOTE · issues: <n> new, <n> seen again · prior: <n> held, <n> recurred, <n> not exercised, <n> not testable

## Errors
### E1 · <issue id> (<new | seen>) · <fault> · <one-line finding>
<unit or segment> · evidence `<step>` · rule `<file:line>` · <still at HEAD | changed since <version>>
<two or three sentences: what happened, why it matters, and — for definition faults — the edit that would fix it>

## Warnings
### W1 · <issue id> (<new | seen>) · <fault> · <one-line finding>
<same shape, one short paragraph>

## Notes
- N1 · <issue id> (<new | seen>) · definition · <one line>
- N2 · — · <fault> · <one line>

## Prior issues
| Issue | Title | Attempt | Verdict | Unit · step | Evidence |
|---|---|---|---|---|---|

## Audited
| Unit | Type | Description | Verdict | E/W/N |
|---|---|---|---|---|

## Not audited
<units not selected and why, units still running, auditors that failed>

## Dropped on spot-check
<finding, and why its evidence did not hold — or "none">
