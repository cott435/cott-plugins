---
id: <PREFIX>-<nnn>
plugin: <plugin name>
title: <one line>
fault: <agent | driver | definition>
severity: <ERROR | WARN | NOTE>
check: <inputs | procedure | scope | hooks | claims | shape | waste | handoffs | agreement | shared state | repeats | rework>
applies_to: <comma-separated: agent:<type>, driver:<command>, cross>
rule_file: <path relative to the plugin root, or none>
rule_line: <line number at found_version, or none>
rule_quote: <the rule, quoted short, or none>
found_version: <plugin version that ran>
found_session: <id8>
found_date: <YYYY-MM-DD>
---

## Finding

<one or two sentences: what happened against what should have>

## Found in

- <date> · <id8> · <version> · <unit | seg-<n> | cross> · <step id> — "<evidence, one short quote>" · <report path> <finding id>

## Fix

### Attempt <n>
- status: <fixed | wontfix>
- reason: <wontfix only>
- branch: <branch>
- commit: <sha>
- files: <comma-separated paths>
- evals: <comma-separated eval log paths>
- fixed_in: <version; blank until bump-version stamps it>
- Verify: watch <applies_to>; held when <what a trace shows>; recurred when <what a trace shows>

## Checks

- <date> · <id8> · <version> · attempt <n> · <held | recurred | not exercised | not testable> · <unit | —> · <step id | —> — "<evidence, or why not>"
