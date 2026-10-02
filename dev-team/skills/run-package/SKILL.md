---
name: run-package
description: Drive one package to shipped - scaffold its workspace first when it has none, derive every section's state from disk, run every ready row's step in one message (designers, testers, implementers in parallel, two reviewers in round 1; the architect alone at PLAN), route design-gap and spec-change, ask you on a block and record the answer, review the package's paths once every section is DONE, close the package with sync-plan, and end with a summary and the exact next command. Optional section and --step run one section or one step by hand; --defer moves a stuck review's findings to the backlog instead of asking; --serial runs one kind of step per batch and one implementer at a time.
argument-hint: "<pkg> [<section>] [--step PROBE|DESIGN|TEST|IMPLEMENT|REVIEW] [--defer] [--serial]"
arguments: [pkg, rest]
disable-model-invocation: true
---

Run package **$pkg**. The whole command line was: **`$ARGUMENTS`**.

If the package name above reached you unsubstituted, as a literal dollar-sign placeholder,
take the first word of the command line as the package name.

This skill runs in your conversation, not in a fork. You are the driver: you spawn every agent
yourself with the Agent tool, so each one is layer 1. No state is kept anywhere but on disk:
`status.py` derives every section's state from the documents, the code and git on every call,
and you re-run it after every batch. A re-run of this command a week later, after hand edits or
a crash, therefore picks up exactly where the files say.

Every `status.py` below is `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py`,
run from the repo root. It exits 1 on a failing gate; that is the answer, not an error.

## What you never do

- Edit a file other than `docs/decisions.md`, and that one only as **Asking** says.
- Run a git command that writes. The only git you run is `git rev-parse --short HEAD`, at the
  start and at the end, `git rev-list --count <start>..HEAD` for the summary, and `git status
  --porcelain -- docs/decisions.md` for the summary's `uncommitted:` line.
- Read a return past its first line, except a tester's `design-gap` return, which you relay
  in full to the designer, and a `blocked` or `stopped` return, which is the question you
  ask. A `spec-change` return is not relayed: its entry is on disk, and `status.py` names it.
  And never tell the user what a return says past its first line — a failure count, a
  phrase, a claim that a suite is green: a summary can be wrong, and the audited returns
  held false ones. What a run did is on disk, and the next `status.py` shows it.
- Open the files the agents wrote to check their work. Read only with the Read tool, and only:
  the Sections table of `docs/packages/<pkg>/contract.md`, the `<pkg>` row of
  `docs/architecture.md` and its **Shared conventions** (a source's access variable), the
  `docs/legacy/inventory.md` row for a source token, and the gate record
  `.dev-team/gate/<pkg>/<section>.txt` of a row whose evidence starts `gate `, for the question
  you ask about it (**Asking**). Every other spawn field comes from
  `status.py --fields <pkg>/<section>`, and a reviewer's **Previous round** from the file names
  the Glob tool finds under `docs/packages/<pkg>/reviews/<section>/` (or the older
  `docs/reviews/`). Never `ls`, `grep`, `find`, `cat` or `head` a repo file, except that a session without the Glob
  tool lists `docs/packages/<pkg>/reviews/<section>/` with `find` and tests a file for existence
  with a one-line Read (`limit=1`), and nothing else; the Sections table is a Read, never a
  `grep | head`. Judging the work
  is the reviewer's. `status.py`'s source is not yours to read either: a state you do not
  understand is **Asking**, with the row.
- Spawn anything in the background. Every Agent call is `run_in_background: false`; the next
  batch needs the last one's commits.
- Spawn with a bare agent name. `architect` does not resolve to the plugin agent; it silently
  runs a general-purpose agent that never loads the role's prompt.

## Arguments

The first word is `<pkg>`. After it, in any order:

- `<section>` — a word not starting with `--`: walk that section alone.
- `--step <STEP>` — one of `PROBE`, `DESIGN`, `TEST`, `IMPLEMENT`, `REVIEW`: run that one step
  for the named section and stop.
- `--defer` — at a review cap or the paths cap, defer instead of asking.
- `--serial` — one kind of step per batch and one implementer at a time, the 2.1 loop, for a
  repo whose sections share a file the write guard cannot separate.

`--step` without `<section>`, a `--step` value not in that list, or any other `--` word: print
one line saying which, and stop — no spawn, no summary.

## Spawning an agent

One Agent call per spawn, `subagent_type: "dev-team:<agent>"`, `run_in_background: false`.
The prompt is exactly the block for that role below: one `<Field>: <value>` line per row, in
the row order, every value resolved, a field with nothing to hold written `none`, and nothing
else. The implementer's block is not a table here: `status.py --inputs` prints it whole. Each block's fields are the ones that agent's own **Inputs** defines; the agent owns
what they mean, and every procedure lives in the agent, never in the prompt.

If the first Agent call fails because the agent type is unknown, stop: the dev-team agents are
not registered. Tell the user to run `/reload-plugins` (or restart Claude Code), verify with
`/agents`, and re-run the same `/dev-team:run-package` command.

Resolving values. `<path>` is the section's `path` cell in the Sections table; `<package
root>` is the `<pkg>` row's `path` in the Packages table. A section's dependencies are its
`depends on` cell, and for `surface` every other section. Upstream packages are the `<pkg>`
row's `depends on` in the Packages table: each is `docs/packages/<dep>/interface.md` when that
file exists, else `provisional: docs/packages/<dep>/contract.md`. The designer is sent every
one. The tester and the reviewer are sent the `upstream interfaces:` line of `status.py
--fields`, which holds only the packages the section's design says it consumes (every one,
when the design does not say), and the implementer's block resolves it the same way. Sources
are the row's `source` cell, `<kind>:<token>` each. `status.py --fields <pkg>/<section>`
prints six lines — `mode:`, `change file:`, `design mode:`, `diff base:`, `upstream
interfaces:` and `paths report:` — run once per section you spawn for, and each table below names the line a
field copies. Rounds are the row's `round` column (`—` is 0); a
round's reports are `docs/packages/<pkg>/reviews/<section>/*-r<n>-*.md`,
or the older `docs/reviews/*-<pkg>-<section>-r<n>-*.md`, and a report with no `-r<n>-` in its
name is round 1.

### Researcher — PROBE

`subagent_type: "dev-team:researcher"`, one per source that lacks this section's entry: an
`api:` token whose `docs/sources/<token>.md` has no `## <pkg>/<section>` line, or a `dataset:`
token with no doc. One researcher per source per batch: two sections waiting on one source
take turns, since both extend one file.

| Field | Value |
|---|---|
| **Kind** | `api` or `dataset`, from the token |
| **Source** | the token |
| **Purpose** | the section's row, its `responsibility` cell verbatim |
| **Access** | the env var or location the repo contract's Shared conventions names for the token; `none` when they say the source needs no credential; else `discover` |
| **Extracted skill** | the `.claude/skills/<name>/` a `docs/legacy/inventory.md` row names for the token, else `none` |
| **Section** | `<pkg>/<section>` |
| **Write to** | `docs/sources/<token>.md` |
| **Run** | `run-package <pkg>` |

### Designer — DESIGN

`subagent_type: "dev-team:designer"`, one per section.

| Field | Value |
|---|---|
| **Section** | `<pkg>/<section>` |
| **Mode** | the `mode:` line of `status.py --fields`: `new`, `document` or `delta` |
| **Contract** | `docs/packages/<pkg>/contract.md` |
| **Repo contract** | `docs/architecture.md` |
| **Dependency READMEs** | `<dep path>/README.md` per dependency, comma-separated; in `delta` and `document` modes `own: <path>/README.md` first when it exists |
| **Upstream interfaces** | per upstream package, as resolved above |
| **Source probes** | `docs/sources/<token>.md` per source |
| **Change file** | the `change file:` line of `status.py --fields` (`delta` only; else `none`) |
| **Spec-change** | every heading the row's evidence lists when it reads `open <heading>; <heading>; …` and names `spec-change:design`, one per line, the first after the field's name and each further one on a line of its own below it; else `none` |
| **Design-gap** | the tester's `design-gap` return, verbatim, when this run's tester returned one for the section |
| **Skills to invoke** | the row's `builds with`; `none` when the cell is empty or `—` |
| **Write to** | `docs/packages/<pkg>/design/<section>.md` |
| **Run** | `run-package <pkg>` |

### Tester — TEST

`subagent_type: "dev-team:tester"`, one per section.

| Field | Value |
|---|---|
| **Section** | `<pkg>/<section>` |
| **Design** | `docs/packages/<pkg>/design/<section>.md` |
| **Contract** | `docs/packages/<pkg>/contract.md` |
| **Repo contract** | `docs/architecture.md` |
| **Dependency READMEs** | `<dep path>/README.md` per dependency, comma-separated |
| **Upstream interfaces** | the `upstream interfaces:` line of `status.py --fields` |
| **Source probes** | `docs/sources/<token>.md` per source |
| **Regenerate** | the entry heading from the row's evidence when it reads `regenerate: <heading>` or `open <heading>` (a `spec-change:test`); when `open` names several, `; `-separated, every heading, one per line; else `none` |
| **Design mode** | the `design mode:` line of `status.py --fields`: `new`, `document` or `delta` |
| **Write to** | `tests/intent/<section>/ under <package root>` |
| **Run** | `run-package <pkg>` |

### Implementer — IMPLEMENT and FIX n

`subagent_type: "dev-team:implementer"`, one per ready IMPLEMENT or FIX row, all in the
batch's one message: implementers run in parallel like every other role. The write guard
confines each to its section from its prompt's `Section:` line, the stop gate judges each on
its own section, the marker and the decisions inbox are per section, and the two shared edits
go through `locked.py`. With `--serial`, one at a time: the first such row only, as 2.1 did.

The prompt is the output of `status.py --inputs <pkg>/<section>`, verbatim: the script
resolves every field of the implementer's **Inputs** — the review reports at FIX `n` and at a
cap granted *one more round*, the round, the open change file — and its docstring is the one
list of them. `/dev-team:pair` reads the files the same block names, so a section built here
and a section paired on by hand start from the same documents. Do not add, drop or rewrite a
line of it.

### Implementer — SCAFFOLD

`subagent_type: "dev-team:implementer"`, once, before any other spawn, when `status.py
--scaffold <pkg>` prints `scaffold: needed`. It builds the workspace root (when the repo has
none) and the package skeleton, runs `uv sync` and the empty workspace's checks, and commits
them with `uv.lock`, so every tester after it runs inside the workspace under the repo's own
lint rules.

| Field | Value |
|---|---|
| **Scaffold** | `<pkg>` |
| **Run** | `run-package <pkg>` |

### Reviewer — REVIEW

`subagent_type: "dev-team:reviewer"`. The round is `r`, the row's round plus one. Round 1 is
two reviewers, `Focus: conformance` with `Letter: a` and `Focus: correctness` with `Letter: b`,
sent as two Agent calls in the same assistant message: never one, then its return, then the
other. They read the same commit and write different files, and running them one after the
other doubles the wait for nothing. If only one went out, spawn the other next, before any
other spawn or `status.py` run, with the same round and `Diff:`: the pair must see the same
code, and neither may be handed the other's report. Round 2 and later is one: `Focus: full`,
`Letter: s`. At a review cap the user's *defer* (or `--defer`) is one: `Focus: defer`,
`Letter: s`.

| Field | Value |
|---|---|
| **Section** | `<pkg>/<section>` |
| **Focus** | `conformance`, `correctness`, `full` or `defer`, as above |
| **Round** | `r` |
| **Letter** | `a`, `b` or `s`, as above |
| **Design** | `docs/packages/<pkg>/design/<section>.md` |
| **Contract** | `docs/packages/<pkg>/contract.md` |
| **Repo contract** | `docs/architecture.md` |
| **Dependency READMEs** | `<dep path>/README.md` per dependency, comma-separated |
| **Upstream interfaces** | the `upstream interfaces:` line of `status.py --fields` |
| **Source probes** | `docs/sources/<token>.md` per source |
| **Intent tests** | `tests/intent/<section>/` |
| **Previous round** | from round 2: round `r-1`'s report paths, comma-separated, then the `paths report:` line of `status.py --fields` when it is not `none`; else `none` |
| **Diff** | from round 2: `<sha>..HEAD`, `<sha>` the `diff base:` line of `status.py --fields` (round `r-1`'s `-s` report's `Commit:`, or its `-a` report's when `r-1` is 1); else `none` |
| **Gate** | `.dev-team/gate/<pkg>/<section>.txt` |
| **Run** | `run-package <pkg>` |

### Reviewer — PATHS

`subagent_type: "dev-team:reviewer"`, one per package, alone in its batch, when every section
is DONE and `status.py <pkg>` prints `paths: needed` (step 7 of the loop). Run `status.py
--rounds <pkg>/paths` once (five lines: `rounds:`, `next round:`, `commit:`, `previous:`,
`diff base:`): the round is `r`, its `next round:` line. At the paths cap the
user's *defer* (or `--defer`) is this block with `Focus: defer`.

| Field | Value |
|---|---|
| **Package** | `<pkg>` |
| **Focus** | `paths`; `defer` at the paths cap |
| **Round** | `r` |
| **Letter** | `p` |
| **Contract** | `docs/packages/<pkg>/contract.md` |
| **Repo contract** | `docs/architecture.md` |
| **Previous round** | the `previous:` line of `status.py --rounds <pkg>/paths` (`none` at round 1) |
| **Diff** | from round 2: `<sha>..HEAD`, `<sha>` the `diff base:` line of `status.py --rounds <pkg>/paths`; else `none` |
| **Run** | `run-package <pkg>` |

### Architect — PLAN and the close

`subagent_type: "dev-team:architect"`, one per package: at PLAN it does what
`/dev-team:plan-package <pkg>` does, and at the close what `/dev-team:sync-plan <pkg>` does.

| Field | Value |
|---|---|
| **Package** | `<pkg>` |
| **Run** | `run-package <pkg>` |
| **Spec-change** | at PLAN only: every heading every PLAN row's evidence lists (`open <heading>; <heading>; …`), one per line. At the close the block ends after `Run:` |

## Loop

Record `git rev-parse --short HEAD` as the start commit. Keep three counts for this run, in
your own memory only: agent runs per role; `design-gap` returns per section; and the sections
granted *one more round* at a cap.

1. **Run gate.** `status.py --run-gate <pkg>`. FAIL → **Summary** with its lines.
   Then **scaffold**: `status.py --scaffold <pkg>`. On `scaffold: needed`, spawn the SCAFFOLD
   implementer and branch on its return (step 5) before anything else: `done` → re-run the
   check, which must now print `scaffold: done` (a second `needed` is **Asking**, with both
   lines); `blocked` → **Asking**. This holds for a `<section>` walk and `--step` too: no agent
   runs in a package whose workspace does not exist.
2. **State.** `status.py <pkg>`; keep the rows. With `--step`, go to **One step**. With a
   `<section>`, only that row counts from here on; if one of its in-package dependencies is not
   DONE, print which and why, and go to **Summary**. When every row that counts is DONE → step
   7.
3. **BLOCKED rows.** For each BLOCKED row that counts, **Asking**. A row granted *one more
   round*, *defer*, *run the implementer again* or *review anyway* this run is not asked
   again: step 4 runs it. After the answers, re-run step 2.
4. **The ready set.** The rows that count with `ready` `yes`, plus the rows granted a round, a
   defer, an implementer run or a review. When any of them is PLAN, the batch is one architect
   for the package, with every open heading of every PLAN row in `Spec-change:`, and nothing
   else: it edits the contracts the designers read, so every other row waits one batch.
   Otherwise spawn **every ready row's step in one message**, whatever mix of steps the rows
   are at:
   - PROBE → the researchers, one per source that lacks the section's entry (two sections
     waiting on one source take turns).
   - DESIGN → a designer per section; also a section at TEST whose last tester run this run
     returned `design-gap`.
   - TEST → a tester per section.
   - IMPLEMENT or FIX n → an implementer per section. A cap row granted *one more round* gets
     its implementer here, then its `full` reviewer as a REVIEW next batch. A gate-BLOCKED row
     granted *run the implementer again* gets its implementer here. A section named at the
     paths cap and granted *one more round* gets its implementer here; its row then reads
     REVIEW and the loop runs it.
   - REVIEW → the reviewers of every such row: two per round-1 section, one otherwise; a row
     granted *defer* gets its `defer` reviewer here. A gate-BLOCKED row granted *review
     anyway* gets its reviewers here: two at round 1, one `full` otherwise.

   Every Agent call of the batch — both of a round-1 pair, every implementer — is in this one
   message; none waits for another's return. With `--serial`: take the first kind in the
   order PLAN, PROBE, DESIGN, TEST, IMPLEMENT/FIX, REVIEW that has any row, spawn every row of
   that kind in one message, and for IMPLEMENT/FIX the first such row only.
5. **Branch** on each return's first line, `Result: <value>`, and read nothing past it except
   where a case below says so. A return is the agent's **first** hand-back: the hand-back tool
   delivers one report per run, and what an implementer does after it — a gate retry, a block,
   a third red attempt — never reaches you as a message. It reaches you as a row: the stop
   gate writes every stop to the section's record and `status.py` derives the row from it, so
   a section whose implementer handed back `done` and then blocked, or was let through, shows
   BLOCKED with `gate …` evidence at step 6, and step 3 asks. What a `done` return says after
   its first line is on disk, and the next `status.py` shows it; relaying it to the user is
   re-sampling the agent's summary.
   - `done` → nothing; a spec-change verdict is on disk and the next state shows it.
   - `design-gap` (tester) → the designer for that section in the next batch, with the whole
     return as `Design-gap:`. The third `design-gap` for one section in this run is a block
     instead: **Asking**, with the return's `Gap:` lines as the question.
   - `spec-change` → nothing to relay: the entry is in
     `docs/packages/<pkg>/deviations/<section>.md` and `status.py` re-opens the step it names
     (PLAN, DESIGN or TEST), where the next block carries it. When the next `status.py` shows
     no such row for the section, that is a row that did not move: **Asking**, below.
   - `blocked` or `stopped` → **Asking**, with the return as the question, whatever the next
     `status.py` shows. A block that comes after the hand-back is not this case: it has no
     return, and arrives as a gate-BLOCKED row.
   - a first line that is not `Result:` — never a `blocked` or `stopped` one — → re-run
     `status.py <pkg>`: if the row has moved past the step's state (IMPLEMENT or FIX → REVIEW, DESIGN → TEST, TEST → IMPLEMENT, REVIEW →
     DONE or FIX), note `<role> <section>: no Result: line; state advanced` for the
     **Summary** and go on; else **Asking**, with the return as the question. The state is on
     disk; a malformed last turn after a good commit is not a question for the user.
6. **Re-derive.** `status.py <pkg>`, its whole output read as printed — never piped through
   a filter such as `head` or `tail`, and never narrowed to the sections you spawned: a filtered table
   hides a re-opened upstream section and the `shipped:` line. Print the rows whose state or
   evidence changed, by comparing them with the rows you kept, as the table prints them: no
   label before a row and no sentence about it after. The rows are your next message after
   every `status.py` run, before the next spawn: a thought, or a sentence about the rows, is
   not them. A row whose
   agent returned `done` this batch and whose state and evidence are exactly what they were
   before it ran did not move: spawning the same step again would repeat the same run. Send
   it to **Asking** instead, with the row and the agent's first two lines. Back to step 2.
7. **Paths, then close.** Every section of the package is DONE. Read the `shipped:` and
   `paths:` lines of the last `status.py <pkg>`:
   - `shipped: no (surface check FAIL)` → **Asking**; neither the paths review nor the close
     runs.
   - `paths: needed` → the paths reviewer (**Reviewer — PATHS**), then steps 5 and 6. A
     `request changes` re-opens the sections its report names: the next `status.py` shows them
     at FIX n, and steps 2 to 6 run them like any FIX row. When they are DONE again the line
     reads `paths: needed` and the next round runs.
   - `paths: round <n> (request changes: …) (cap)` → **Asking**, the paths cap.
   - `paths: round <n> (request changes: no section named)` → **Asking**, with the line.
   - `paths: approved (…)` → the architect with `Package:` and `Run:` only — the close.

   A `<section>` walk skips this step unless its section was the last one not DONE. Then
   **Summary**.

On `request changes`, nothing is spawned from the verdict itself: the next `status.py` row
says FIX n (the implementer, then a `full` review) or BLOCKED with evidence `(cap)` — round 3,
or round 2 with a prior unfixed — and a cap goes to **Asking**, never to another implementer.
A paths review's `request changes` is handled the same way: the next `status.py` shows the
named sections at FIX n, or the `paths:` line at its cap, and nothing is spawned from the
verdict itself.

### One step

After the run gate and the scaffold (**Loop** step 1), `--step <STEP>` runs that step for the
named section once, against whatever is on disk and
whatever its derived state, and then **Summary**. A BLOCKED row does not stop it: no question
is asked, which is how *one more round* is typed by hand. PROBE spawns a researcher for every
source in the row; REVIEW is round `r` = the row's round plus one — two reviewers at round 1,
one `full` reviewer otherwise, including at FIX n and at a cap. A missing document is the
agent's to report: its own preconditions return `blocked`, which ends the step with the
return's first two lines as `stopped because`.

## Asking

One `AskUserQuestion` per block, its text built from what stopped:

- a `D<n>` BLOCKED row, or an agent `stopped` for decisions: each `D<n>` named, its question
  and its `Recommendation:` from `docs/decisions.md` as the recommended option;
- an agent `blocked` (a missing credential, a failed precondition): the return's lines, with
  *fixed, retry* and *stop here* as the options;
- a review cap: the row's evidence, with *one more round* and *defer* as the options;
- a third `design-gap`: the tester's `Gap:` lines, with the designer's options where the return
  names them;
- a section whose agent returned `spec-change` and whose next row is not PLAN, DESIGN or TEST:
  the row as it prints, and that an agent returned `spec-change` — nothing from the return's
  other lines, no count, no test name — with *run it again* and *stop here* as the options;
- a row that did not move after its agent returned `done` (**Loop** step 6): the row and the
  agent's first two lines, with *run it again*, *stop here* and, when the evidence names a
  document, *I will fix it by hand* as the options;
- a gate-BLOCKED row (evidence `gate blocked: …` or `gate let through after 3 attempts, …`):
  Read the section's record `.dev-team/gate/<pkg>/<section>.txt`; the question is the row,
  the record's `result:` line and its `FAIL` and `blocked:` lines, quoted as they stand, with
  *run the implementer again*, *review anyway* and *stop here* as the options;
- every section DONE and `shipped: no (surface check FAIL)`: run `status.py --surface <pkg>`;
  the question is its `FAIL` lines as printed, with *fixed, retry* and *stop here* as the
  options;
- every section DONE and `paths: round <n> (request changes: <sections>) (cap)`: the line as
  it prints, with *one more round* and *defer* as the options;
- every section DONE and `paths: round <n> (request changes: no section named)`: the line,
  with *run the paths review again* and *stop here* as the options.

Record the answer, then re-run **Loop** step 2:

- For decisions, on each named `D<n>` stub, fill `Decision:` with the answer and set
  `Status: decided`. Touch no other line of the entry.
- For a third `design-gap`, append a new stub to `docs/decisions.md` — the next free `D<n>`,
  `Scope: <pkg>/<section>`, `Raised by: /dev-team:run-package <pkg> (driver)`, the gap as the
  question, `Decision:` the answer, `Status: decided` — and run the designer for the section
  in the next batch.
- For a cap, no ledger edit: *one more round* grants the section an implementer and a `full`
  reviewer; *defer* grants it a `defer` reviewer.
- For *fixed, retry*, nothing; the step runs again. For *stop here*, **Summary**.
- For a gate-BLOCKED row, no ledger edit: *run the implementer again* grants the section an
  implementer, with the `--inputs` block as at IMPLEMENT; *review anyway* grants it its
  reviewers. Once a review round covers the code `status.py` stops reading the record, so the
  answer holds across re-runs.
- For the surface check, nothing: *fixed, retry* re-runs **Loop** step 2, and *stop here* is
  **Summary**. The close waits until the check passes.
- For the paths cap, no ledger edit: *one more round* grants each section the line names an
  implementer, with the `--inputs` block, which carries the paths report; *defer* grants the
  package a paths reviewer with `Focus: defer`. For *run the paths review again*, the paths
  reviewer runs at the next round.
- **An answer that is none of the options** — free text typed in place of a choice — ends the
  loop where it stands: go to **Summary**, with the row or the two lines you asked about as
  `stopped because`. Do not act on the text: no diagnosis of the plugin, no file this skill
  forbids you to read, no edit. The user reads the Summary and types what they want next.

Your ledger edits stay uncommitted: `docs/decisions.md` is exempt from the run gate, the next
agent that stages it carries it, and otherwise the user commits it.

No questions when `AskUserQuestion` is not available (a headless run) or the command has
`--defer`: a review cap or the paths cap with `--defer` is answered *defer*; every other block goes to **Summary**,
with the agent's first two lines, or the row's evidence, as `stopped because`. A
gate-BLOCKED row is quoted as it prints.

## Summary

Always your last message, whether you finished or stopped, and the block is the whole message:
no line before it or after it — no recap, no note about how the run went. What the run did is
in the block and on disk; a sentence around it is a second summary nobody checks.

```
run-package <arguments as typed>: <done | stopped at <section> <STEP>>
sections: <DONE>/<total> DONE; <section> · <state>, …
agent runs: designer <n> · tester <n> · implementer <n> · reviewer <n> · researcher <n> · architect <n>
commits: <start sha>..<end sha> (<count>)
stopped because: <the agent's first two lines, the row as it prints, the shipped: line, the paths: line, or the run gate's FAIL lines>
no Result: line: <role> <section>: no Result: line; state advanced, …
uncommitted: docs/decisions.md
next: <status.py's next line>
```

The first line echoes the command's arguments, so it says which walk this was: `run-package
data: done`, `run-package data ingest: done`, `run-package data ingest --step REVIEW: done`,
`run-package data --serial: done`.
`done` means the walk you were asked for finished — the package closed, the section DONE, or
the one step run. The first line reads `stopped at <section> BLOCKED` for a stop at a BLOCKED
row, `stopped at the surface check` for a stop at the surface question, and `stopped at the
paths review` for a stop at a paths question. `stopped because`
appears only when stopped, `no Result: line` only when a return's first line was not
`Result:` and its row had advanced (**Loop** step 5), and `uncommitted` only when `git status
--porcelain -- docs/decisions.md` prints a line: an agent's commit may have carried your edit,
and then nothing is uncommitted. `sections` and `next` come from a final `status.py <pkg>`, the
`next:` line copied as it prints; `commits` from `git rev-parse --short HEAD` and
`git rev-list --count <start>..HEAD`. Every agent run counts once under its role, the
architect's PLAN and close runs included.
