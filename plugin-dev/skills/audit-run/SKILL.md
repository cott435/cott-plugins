---
name: audit-run
description: Audit a real run of this plugin's workflow from its session transcripts - which agents were spawned with what, every tool call, hook block, commit and hand-back - against the plugin's own agent and skill files at the version that ran, and report every error with evidence on both sides. Draws the run as a flow chart showing what ran in parallel and what in series, how many runs and review rounds each section took, and what each review found. Checks each agent's inputs, procedure, write scope, error recovery and whether its claims are backed by its tool calls, the driver's branching on each return, and consistency across agents. Writes the report under evals/workspace/audit/ and logs the run with log-eval. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), after or during a workflow run in another project.
argument-hint: "[session-id | path.jsonl | latest] [--units risk|all|new|seg:N|U01,U05] [--full]"
disable-model-invocation: true
---

# Auditing a run

A plugin's files say what its workflow does. A run is what it actually did. The two drift
apart silently. An agent says "committed" when its commit failed, or a driver passes a stale
path to the next agent. A rule is broken in every run because it is stated once, three
screens from where it applies. None of that shows up in `check-contracts`, which reads the
files, or in the run itself, which reports success. It shows up only in the transcript.

This skill rebuilds a run from its transcripts into a trace, has `run-auditor` agents hold
each piece of it against the files that defined it, and reports what disagrees. It judges the
plugin's behavior, not the project the run built.

`T` below is `python3 ${CLAUDE_SKILL_DIR}/scripts/trace.py`. Run everything from the plugin's
own directory, the one under test.

## 1. The plugin and the session

1. Read `.claude-plugin/plugin.json`. Its `name` is **P**. With no manifest, stop: this skill
   runs inside the plugin whose run is being audited.
2. The session is the first argument that is not a flag:
   - a path to a `.jsonl`, or a session id or unique prefix: use it;
   - `latest`: the newest session that used **P**;
   - nothing: run `T find --plugin P`. With one hit, use it. With several, ask with
     `AskUserQuestion`, one option per session (its date, project, commands and spawn count),
     at most four, newest first.
3. The workspace is `evals/workspace/audit/<first 8 chars of the session id>/`. Check that
   `.gitignore` covers `evals/workspace/`, and add the line if it does not. The trace holds
   the project's file contents and must never be committed.

## 2. The trace

`T build <session> --plugin P --out <workspace>` (add `--full` if the argument has it). It
writes `run.md` (segments, a unit table, the whole main thread), `index.json`,
`driver/seg-<n>.md` (the main thread from each typed command of **P** to the next), and
`units/U<nn>.md` (one per spawned agent: the prompt it was sent, every step, what it handed
back), with `units/U<nn>.system.md` holding the system prompt it ran with, and `flow.html`.

`flow.html` is the run as a chart, and the first thing to show the user. Time runs down.
- **Rows:** each row is a wave, the agents one spawner started in one message. A shaded row
  ran in parallel; an unshaded row ran one agent alone.
- **Columns:** each column is one section's history, with every agent that touched it, its
  run and review-round counts, and arrows joining its runs in order.
- **Reviews:** a review box is coloured by its verdict and shows its critical and warning
  counts.
- **Bands:** a full-width band marks each time the driver stopped to ask the user, with the
  answer.
- **Summary:** above the chart, a table gives each section's runs, review rounds and
  reviews in order, and lists every review that found issues.

`run.md`'s **Flow** section is the same in text, for the auditors. The lanes and verdicts
are read heuristically: the lane is a `Section:` input, else the first `a/b` name in the
description, and the verdict is a `Verdict:` line in the return. So a plugin whose returns
say neither gets a chart of waves without review colours, which is still correct about
parallel and series.

Print the script's summary lines. Then settle **which version ran**, since every rule is
checked against that version:

- `index.json`'s `plugin_root` exists: the definitions are read from there.
- It does not exist (the cache was cleared or updated since): check out the tag for its
  `version` into `<workspace>/plugin/` with `git worktree add --detach <workspace>/plugin
  v<version>` from the repo root (or `<P>-v<version>` if that is the tag form `git tag`
  shows), and use `<workspace>/plugin/<P>` as the plugin root. Remove that worktree at the
  end.
- No root and no tag: use the working tree, and say in the report and the eval log that
  the rules were checked against a version that may not be the one that ran.

If `index.json` shows no units and no segments, the session never ran **P**'s workflow.
Say so and stop.

## 3. What to audit

`T select <workspace> --units <how>`, where `<how>` is the `--units` argument, default
`risk`:

- `risk`: the first unit of each agent type, plus every unit that stands out from its type:
  a different return, no commit where others committed, a commit that cannot be tied to its
  own files, many hook blocks or errors, or a spawn from below the driver. Capped at 12.
- `all`, `seg:<n>`, or a list such as `U03,U14`.
- `new`: every finished unit with no findings file yet. This is how a **running** workflow
  is watched: re-run this skill with `--units new` while the workflow runs in another chat,
  or put it on `/loop`, and each pass audits only the agents that finished since the last one.

Units still running are never selected; the script lists them. Show the selection with its
reasons. If it is more than 12 units, ask before spawning: each auditor reads a whole trace
and its definition, so an audit of 50 units costs about as much as the run did.

Every segment that spawned a selected unit is audited in `driver` mode too. With `--units
new`, audit a segment only once it has finished, meaning a later segment has begun or its
last step is the driver's summary after every unit returned.

## 4. The auditors

Spawn one `plugin-dev:run-auditor` per selected unit and one per selected segment, all in
one message so they run in parallel, in the foreground. Each gets exactly this block, every
path absolute:

```
Mode: unit | driver
Trace: <workspace>/units/U<nn>.md | <workspace>/driver/seg-<n>.md
Workspace: <workspace>
Definition: <index.json's definition for the unit or segment, re-rooted if §2 moved the root | none>
Plugin root: <the root from §2>
Spawner: <trace> · <definition> of what spawned it (a segment or another unit) | none
Project: <index.json project>
Findings: <workspace>/findings/<U<nn> | seg-<n>>.md
```

When they have all returned, spawn one more with `Mode: cross`, `Trace: <workspace>/run.md`,
`Definition: none`, `Spawner: none`, `Findings: <workspace>/findings/cross.md`. It reads the
others' findings files, so it runs last. With `--units new`, skip `cross` until the whole run
has finished.

If an auditor's return is not its one `Findings:` line, or its file is missing, re-spawn that
one once. If it fails a second time, list it under **Not audited**.

## 5. The report

Run `T flow <workspace>`. It re-renders `flow.html` with a badge on every audited box: that
unit's ERROR count, or ✓. Then read every findings file, and:

1. **Merge.** When `cross` wrote a systemic finding covering units' findings, keep the
   systemic one and list the units under it. Otherwise keep every finding as written. Never
   raise or lower an auditor's severity. If you disagree, add a sentence saying why.
2. **Spot-check** every ERROR before it goes in the report. Open the trace at the step it
   cites and the definition at the line it cites, and confirm both say what the finding says.
   An ERROR whose evidence does not hold is dropped and listed under **Dropped on
   spot-check**, with the reason. A checker that reports false errors will stop being read.
3. **Still true?** For each `definition` fault, grep the working tree's copy of the cited file
   for the quoted rule. Mark it `still at HEAD` or `changed since <version>`. A `changed since`
   finding may already be fixed. Say so rather than dropping it.
4. Write `<workspace>/report.md`:

```markdown
# Audit · <P> <version> · <command(s)> · session <id8>

**Run:** <project> · <branch> · <span> · <models> · <n> units, <n> audited
**Rules checked against:** <plugin root> (<the version that ran | working tree — see note>)
**Flow chart:** `flow.html`, beside this report
**Totals:** <n> ERROR · <n> WARN · <n> NOTE

## Errors
### <E1> · <fault> · <one-line finding>
<unit or segment> · evidence `<step>` · rule `<file:line>` · <still at HEAD | changed since>
<two or three sentences: what happened, why it matters, and — for definition faults — the
edit that would fix it>

## Warnings
<same shape, one short paragraph each>

## Notes
<one line each>

## Audited
| Unit | Type | Description | Verdict | E/W/N |

## Not audited
<units not selected and why, units still running, auditors that failed>

## Dropped on spot-check
<finding, and why its evidence did not hold — or "none">
```

## 6. Log it, then report

Invoke `log-eval` before saying anything about the results. The entry is
`evals/<date>-audit-<command skill>-<id8>.md` in this plugin:

- **Tested against**: the version that ran and its tag's short SHA, not HEAD. The model or
  models from `index.json`.
- **What was tested**: the workflow command(s) the session ran, and that this is an audit of a
  real run rather than a set eval.
- **Method**: the session id and project, how units were selected, how many auditors ran,
  and that the report is `<workspace>/report.md` (gitignored, so the entry carries the
  findings table itself).
- **Results**: the ERROR and WARN findings as a table: id, unit, fault, finding, rule.
- **Verdict**: clean, or the count by fault, and which `definition` findings are still at
  HEAD.

Then tell the user, in this order and briefly:

1. One line: the run, the version, the totals, and the path to `flow.html`. Offer to open it.
   A local page opens in the browser pane only when it is served, e.g. `python3 -m http.server`
   from the workspace.
2. Each ERROR: what happened, its evidence step and its rule, as a clickable `file:line`
   into the working tree when it is still at HEAD.
3. How many WARN and NOTE findings there are, plus the report's path.
4. For `definition` faults still at HEAD, offer to make the edits. Do not make them unasked.
   An edit to an agent or skill here is a change like any other: `check-contracts`,
   `build-site`, and a re-run of the evals that cover it.

## What this skill never does

- Edit the plugin, the audited project, or the transcripts. The report and the eval log are
  its only writes, plus a `.gitignore` line when one is missing.
- Commit anything except what `log-eval` commits.
- Re-run the workflow to check a finding. The trace is the evidence. A finding the trace
  cannot settle is a WARN that says what would settle it.
