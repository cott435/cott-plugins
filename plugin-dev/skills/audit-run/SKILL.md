---
name: audit-run
description: Audit a real run of this plugin's workflow from its session transcripts - which agents were spawned with what, every tool call, hook block, commit and hand-back - against the plugin's own agent and skill files at the version that ran, and report every error with evidence on both sides. Draws the run as a flow chart showing what ran in parallel and what in series, how many runs and review rounds each section took, and what each review found. Checks each agent's inputs, procedure, write scope, error recovery and whether its claims are backed by its tool calls, the driver's branching on each return, and consistency across agents. Files what it finds as issues in the plugin's committed ledger under runs/audits/, with a run report beside them, and logs the run with log-eval. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), after or during a workflow run in another project.
argument-hint: "[chat title words | session-id | path.jsonl | latest] [--units risk|all|new|seg:N|U01,U05] [--full]"
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

`T` below is `python3 ${CLAUDE_PLUGIN_ROOT}/skills/run-flow/scripts/trace.py`. Run everything from the plugin's
own directory, the one under test.

`I` is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/issues.py` (the ledger: `templates/audits/issue.md` is the shape of what it writes).

## 1. The plugin and the session

1. Read `.claude-plugin/plugin.json`. Its `name` is **P**. With no manifest, stop: this skill
   runs inside the plugin whose run is being audited.
2. The session is everything in the arguments before the first flag:
   - a path to a `.jsonl`, or a session id or unique prefix: use it;
   - `latest`: the newest session that used **P**;
   - words from the chat's title, as the app's sidebar shows it (`architecture migration`):
     `T build` resolves them when exactly one chat matches, and otherwise prints the matches
     and exits 1 — show them and ask as below;
   - nothing: run `T find --plugin P`. With one hit, use it. With several, ask with
     `AskUserQuestion`, one option per session, at most four, newest first. The label is the
     chat's title in quotes; the description is its project, its span and length, its agent
     count and commands, and `fork of <id8>` when it is one.

   `find` prints each session as two lines: the id and the title the user sees, then the
   project, the span, the agents and the commands. It hides headless runs in temp directories
   (eval harnesses, never in the sidebar); `--all` shows them.

   **Forks.** A forked or resumed chat is a new session whose history up to the fork is a copy
   of the original's, while the transcripts of agents spawned before the fork stay under the
   original. `find` marks it `fork of <id8>`, and `T build` on the fork still finds those
   agents under the original. So auditing the fork audits everything, and it is the one to
   pick when the work went on after the split. Two chats with the same title are usually a
   chat and its fork.
3. The workspace is `W=$(T where <session> --plugin P --root .)`, which prints
   `runs/<project>/<command> <title>/<first 8 chars of the session id>/`: the project's
   directory name, the first command of **P** the chat ran, and the chat's title as lowercase
   words. A session already built keeps its folder even when the chat has been renamed since.
   Nothing under `runs/` is committed except `runs/audits/` (the ledger and the run reports).
   Check that `.gitignore` holds `runs/*` and `!runs/audits/`, and add the lines if it does not.
   The trace holds the project's file contents and must never be committed.

## 2. The trace

`T build <session> --plugin P --out <workspace>` (add `--full` if the argument has it). It
writes `run.md` (segments, a unit table, the whole main thread), `index.json`,
`driver/seg-<n>.md` (the main thread from each typed command of **P** to the next), and
`units/U<nn>.md` (one per spawned agent: the prompt it was sent, every step, what it handed
back), with `units/U<nn>.system.md` holding the system prompt it ran with,
`units/U<nn>.json` holding every step with its full input and output (the `.md` is the
clipped copy auditors read), `units/U<nn>.html` as a page per unit, and `flow.html`.

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

Print the script's summary lines. They give the plugin version per segment. When they warn
that the run spans versions (a long chat resumed after `/plugin` updated it), nothing changes
below: each segment's and unit's `definition` in `index.json` already points at the version
that ran it. Then settle **which version ran**, since every rule is checked against that
version:

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

**Prior issues.** A rerun's audit also checks each earlier fix, and widens the selection so
every fix is exercised. With no `runs/audits/issues/` in the plugin, skip this: every block in §4
says `Prior issues: none`.

1. **Which issues.** `I list --status fixed,released,verified --format brief`: one line per
   issue, `<ID> · attempt <n> · commit <sha> · fixed_in <v | —> · watch <applies_to> · held
   when <…> · recurred when <…>`, the latest attempt's, which is all this skill needs of an
   issue. A `recurred` issue's fix already failed and its next attempt is what gets checked; an
   `open` or `wontfix` one has nothing to check, and a `settled` one (held in three sessions,
   not found again since) is no longer checked at all: `issues.py` leaves it out of this list
   and `INDEX.md` shows it as one line. Never load an issue's full record to do this.
2. **Once per session.** Skip an issue that already has a `held` or `recurred` Checks line for
   this `<id8>`, or a row in the Prior issues table of this session's run report
   (`runs/audits/reports/*-<id8>.md`), if it exists (a re-pass with `--units new`).
3. **Was the fix in the code that ran?** Per issue, with `index.json`'s `plugin_root` and
   `version`:
   - when `git -C <plugin_root> rev-parse --git-dir` succeeds, the root is a git checkout:
     testable when `git -C <plugin_root> merge-base --is-ancestor <commit> HEAD` exits 0;
   - otherwise, by version: testable when the attempt's `fixed_in` is set and `version` ≥
     `fixed_in`, compared as dotted integers (`0.10.0` is above `0.9.0`).

   An issue that is not testable is given to no auditor. §5 puts it in the report's Prior
   issues table as **not testable**, with `—` for the unit and the step and evidence that says
   why: `fix <commit> not an ancestor of <plugin_root> HEAD <sha>`, `fixed_in blank`, or `run
   version <v> below fixed_in <w>`; it has no Checks line. *not testable* is this skill's own
   word, for an issue no auditor was given; every other verdict is one run-auditor defines.
4. **Coverage.** Run the selection as `T select <workspace> --units <how> --cover <entries>`,
   where `<entries>` is every `applies_to` entry of the testable issues, comma-separated,
   once each. It adds the first finished unit of each `agent:<type>` the selection lacks
   (reason `covers agent:<type>`); prints `cover segments: seg-<n>, …` for the segments that
   ran each `driver:<command>`; prints `uncovered: …` for entries nothing in this run
   matches; and prints `over cap: …` for units the cap kept out. The cap of 12 and the
   question beyond it apply to the widened selection. Segments on the `cover segments:` line
   are audited in `driver` mode even when none of their units was selected. A `cross` entry
   is covered by the cross auditor. An issue whose entries are all uncovered goes to no
   auditor and ends **not exercised** in §5, with `no <entry> in this run` as its evidence.
5. Show the issues as a table beside the selection: id, attempt, testable (and how: `git
   ancestor`, `version 0.2.0 ≥ 0.1.0`, or why not), covered by (the units and segments whose
   auditors will be given it, or `—`).

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
Prior issues: none | one line per issue below
```

**Prior issues** is the block's last field and always present. It is `none`, or
`Prior issues:` followed by one line per testable issue from §3 whose `applies_to` names this
unit's agent type (`agent:<role>`), this segment's skill (`driver:<skill>`), or, for the cross
auditor, `cross`. Each line is indented two spaces, in the form run-auditor's Inputs give:
`<ID> · attempt <n> · watch <applies_to> · held when <…> · recurred when <…>`, taken from the
attempt's `Verify:` line with its `; ` separators written as ` · `.

When they have all returned, spawn one more with `Mode: cross`, `Trace: <workspace>/run.md`,
`Definition: none`, `Spawner: none`, `Findings: <workspace>/findings/cross.md`, and the
`Prior issues` whose `applies_to` names `cross`. It reads the
others' findings files, so it runs last. With `--units new`, skip `cross` until the whole run
has finished.

If an auditor's return is not its one `Findings:` line, or its file is missing, re-spawn that
one once. If it fails a second time, list it under **Not audited**.

## 5. The report

Run `T flow <workspace>`. It re-renders `flow.html` with a badge on every audited box: that
unit's ERROR count, or ✓. Run it once more after step 5, when the ledger holds this audit's
lines: each box then also shows the issues first found there and the prior issues that held
(✓) or recurred (✗) there. Then read every findings file, and:

1. **Merge.** When `cross` wrote a systemic finding covering units' findings, keep the
   systemic one and list the units under it. A `cross` finding that restates one unit's or
   segment's finding — the same act against the same rule, seen from the whole run — is
   merged the same way, whatever fault each auditor gave it: keep one, and list the other's
   unit and steps under it. Otherwise keep every finding as written. Never raise or lower an
   auditor's severity. If you disagree, add a sentence saying why.
2. **Spot-check** every ERROR before it goes in the report. Open the trace at the step it
   cites and the definition at the line it cites, and confirm both say what the finding says.
   An ERROR whose evidence does not hold is dropped and listed under **Dropped on
   spot-check**, with the reason. A checker that reports false errors will stop being read.
3. **Still true?** For each `definition` fault, grep the working tree's copy of the cited file
   for the quoted rule. Mark it `still at HEAD` or `changed since <version>`. A `changed since`
   finding may already be fixed. Say so rather than dropping it.
4. **Verdicts.** Read the `## Prior issues` section of every findings file that has one:
   `P · <ID> · <verdict> · <step> — <evidence>` lines. Ignore a P line for an issue that
   auditor was not given.
   - **Spot-check** every **held** and **recurred** at its step: open the trace there and
     confirm the step shows what the issue's `Verify:` line says for that verdict. One that
     does not is dropped to **not exercised** and listed under **Dropped on spot-check** with
     the reason.
   - **Combine** per issue: **recurred** if any auditor said so and the spot-check held; else
     **held** if any did; else **not exercised**. Keep the unit and step of the line whose
     verdict you keep.
   - **Write** a Checks line for each issue whose combined verdict is **held** or
     **recurred**, from the plugin's own directory: `I check-result <ID> --attempt <n>
     --verdict <held | recurred> --session <id8> --version <version> --date <today> --unit
     <U<nn> | seg-<n> | cross> --step <step> --evidence "<short quote>"`. A **not exercised**
     or **not testable** issue gets no line: it changes no status, and it is the run report's
     Prior issues table that records it. Held lines are what settle an issue: three, from three
     sessions, and `issues.py` stops handing it to auditors.
   - A **recurred** issue also gets `I seen <ID>` with the same unit and step, `--report
     runs/audits/reports/<date>-<id8>.md` and `--finding-id P`, since it has no F finding. File no new
     issue for it in the next step: if an auditor wrote an F finding for the same act as well,
     fold it into the P verdict and leave it out of the report's findings and counts. A
     recurrence is counted once, under `prior: … recurred`, never in `seen again` or the
     commit's `<n> seen`. A different F finding that step 5 matches to the same issue (another
     act against the same rule) is an ordinary `seen` and counts in `seen again` as usual.
5. **Issues.** Each finding that is an ERROR or WARN with a fault other than `platform`, or
   a `definition` NOTE, becomes an issue; other NOTEs, and `platform` faults, get none. Take
   them in report order (E1…, W1…, N1…) so the ids read in the same order. For each, from
   the plugin's own directory: `I candidates --rule-file <rule file> --fault <fault>`. If a
   listed issue's `rule_quote` is the same rule as this finding's (the same sentence,
   whatever its line number now), it is the same issue: `I seen <ID> --session <id8>
   --version <version> --date <today> --unit <U<nn> | seg-<n> | cross> --step <step>
   --evidence "<short quote>" --report runs/audits/reports/<date>-<id8>.md --finding-id <E1 | W1 |
   N1>`. A different quote is a different issue, even in the same file: line numbers drift
   between versions, the quoted rule does not. `seen` is only for an issue that existed
   before this audit, and **seen again** counts only those: when the match is an issue this
   audit has just filed, the two findings are one problem found twice, so fold this one into
   that finding's heading as in step 1 and file nothing for it. Otherwise `I new` with the
   same Found in fields (`--unit`, `--step`, `--evidence`, `--report`, `--finding-id`) plus:
   - `--title`: the finding's one line;
   - `--fault` and `--severity` as the auditor gave them, and `--check`: its check word;
   - `--applies-to`: `agent:<type>` for a unit, `driver:<command skill>` for a segment,
     `cross` plus the agents it names for a cross finding (`cross,agent:<a>,agent:<b>`);
   - `--rule-file`, `--rule-line`, `--rule-quote`: from the finding's `Rule:`, the file
     relative to the plugin root; `none` for each that a cross contradiction lacks;
   - `--found-version <version>`, `--found-session <id8>`, `--found-date <today>`;
   - `--finding`: one or two sentences, what happened against what should have.

   `I new` prints the new id. Record each finding's issue id and whether it was new or seen.
   `issues.py` writes the issue's frontmatter, **Finding**, **Found in** and **Checks** and
   re-renders `runs/audits/INDEX.md`; never write or edit a file under `runs/audits/issues/`, or
   `INDEX.md`, by hand.
6. **The run report.** Write `runs/audits/reports/<YYYY-MM-DD>-<id8>.md` from
   `${CLAUDE_PLUGIN_ROOT}/templates/audits/run-report.md`: its header lines and its headings
   (**Errors**, **Warnings**, **Notes**, **Prior issues**, **Audited**, **Not audited**,
   **Dropped on spot-check**) in its order, and nothing it does not define.
   - Each `### E<n>` and `### W<n>` heading carries the issue id and `(new)` or `(seen)`;
     a `platform` one carries `—` in its place. Each `definition` N line carries its issue
     id the same way; other N lines carry `—`.
   - Each finding's body is two or three sentences: what happened, why it matters, and, for
     a `definition` fault, the edit that would fix it.
   - **Totals:** `<n> ERROR · <n> WARN · <n> NOTE · issues: <n> new, <n> seen again · prior:
     <n> held, <n> recurred, <n> not exercised, <n> not testable`, the prior counts from
     step 4.
   - **Prior issues:** the template's table, one row per issue §3 took, **not exercised**
     and **not testable** ones included: `| <ID> | <title> | <attempt> | <verdict> | <unit> ·
     <step>, or — | <evidence, or why not> |`. With none, the empty table and then the line
     `none: no fixed issue to check`.
   - **Flow chart:** the template's line, naming the workspace's `flow.html` and
     `/plugin-dev:run-flow <id8>`.
7. **Commit the ledger.** `I check` must print `ok`; if it does not, fix what it names
   through `issues.py` and run it again. Then `git add audits && git commit -m "<P> audits:
   <id8> — <n> new, <n> seen, <n> checked" -- audits`, where `<n> checked` is the number of
   issues step 4 reached (the rows of the Prior issues table), staging nothing outside `runs/audits/`
   because the checkout may hold other work. This is the one commit this skill makes
   itself. When the plugin directory is not in a git checkout (a cache copy, a fixture), the
   files are still the record: print the message you would have used and say the commit was
   skipped.

## 6. Log it, then report

Invoke `log-eval` before saying anything about the results. The entry is
`evals/<date>-audit-<command skill>-<id8>.md` in this plugin:

- **Tested against**: the version that ran and its tag's short SHA, not HEAD. The model or
  models from `index.json`.
- **What was tested**: the workflow command(s) the session ran, and that this is an audit of a
  real run rather than a set eval.
- **Method**: the session id and project, how units were selected, and how many auditors
  ran.
- **Results**: the issue ids by outcome, as `new: <ids | none>; seen again: <ids | none>;
  prior: held <ids | none>, recurred <ids | none>, not exercised <ids | none>, not testable
  <ids | none>`. The findings themselves are in the committed run report, so the entry does
  not repeat them as a table.
- **Verdict**: clean, or the count by fault, and which `definition` findings are still at
  HEAD.
- A last line: `Report: runs/audits/reports/<date>-<id8>.md`.

Then tell the user, in this order and briefly:

1. One line: the run, the version, the totals, the issue counts (`<n> new, <n> seen
   again`), the prior counts (`<n> held, <n> recurred, <n> not exercised, <n> not
   testable`), the report path `runs/audits/reports/<date>-<id8>.md`, and the path to `flow.html`. Say
   that `/plugin-dev:run-flow <id8>` opens it in the browser pane.
2. Each ERROR: what happened, its evidence step and its rule, as a clickable `file:line`
   into the working tree when it is still at HEAD.
3. How many WARN and NOTE findings there are, with their issue ids.
4. Issues were filed for the findings above. Tell the user that
   `/plugin-dev:fix-issues run:<id8>` fixes them from any chat, and, when any prior issue
   recurred, that `/plugin-dev:fix-issues recurred` takes those; this skill cannot start it
   (a typed skill is started only by a person). Do not make the edits unasked.

## What this skill never does

- Edit the plugin, the audited project, or the transcripts. The run report, the issue files
  and `INDEX.md` (through `issues.py`) and the eval log are its only writes, plus a
  `.gitignore` line when one is missing.
- Commit anything except the one `runs/audits/` commit and what `log-eval` commits.
- Re-run the workflow to check a finding. The trace is the evidence. A finding the trace
  cannot settle is a WARN that says what would settle it.
