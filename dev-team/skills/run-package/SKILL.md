---
name: run-package
description: Drive one package to shipped - derive every section's state from disk, run the ready set (probes, designs and tests in parallel, implementers one at a time, two reviewers in round 1), route design-gap and spec-change, ask you on a block and record the answer, close the package with sync-plan, and end with a summary and the exact next command. Optional section and --step run one section or one step by hand; --defer moves a stuck review's findings to the backlog instead of asking.
argument-hint: "<pkg> [<section>] [--step PROBE|DESIGN|TEST|IMPLEMENT|REVIEW] [--defer]"
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
  start and at the end, and `git rev-list --count <start>..HEAD` for the summary.
- Read a return past its first line, except a tester's `design-gap` return, which you relay in
  full to the designer, and a `blocked` or `stopped` return, which is the question you ask. A
  `spec-change` return is not relayed: its entry is on disk, and `status.py` names it.
- Open the files the agents wrote to check their work. You read only what resolves a spawn
  field: the Sections table of `docs/packages/<pkg>/contract.md`, the `<pkg>` row of
  `docs/architecture.md`'s Packages table, the first line of a design (`Mode:`), the `Commit:`
  line of a review report, and file names under `docs/reviews/`, `docs/sources/` and
  `docs/changes/`. Judging the work is the reviewer's.
- Spawn anything in the background. Every Agent call is `run_in_background: false`; the next
  batch needs the last one's commits.
- Spawn with a bare agent name. `architect` does not resolve to the plugin agent; it silently
  runs a general-purpose agent that never loads the role's prompt.

## Arguments

The first word is `<pkg>`. After it, in any order:

- `<section>` — a word not starting with `--`: walk that section alone.
- `--step <STEP>` — one of `PROBE`, `DESIGN`, `TEST`, `IMPLEMENT`, `REVIEW`: run that one step
  for the named section and stop.
- `--defer` — at a review cap, defer instead of asking.

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
file exists, else `provisional: docs/packages/<dep>/contract.md`. Sources are the row's `source`
cell, `<kind>:<token>` each. An open change file naming the section is one under `docs/changes/`
that `grep -l` finds with both `Status: open` and `<pkg>/<section>` in it. Rounds are the row's
`round` column (`—` is 0); a round's reports are `docs/reviews/*-<pkg>-<section>-r<n>-*.md`,
and a report with no `-r<n>-` in its name is round 1.

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
| **Access** | the env var or location the repo contract's Shared conventions names for the token, else `discover` |
| **Extracted skill** | the `.claude/skills/<name>/` a `docs/legacy/inventory.md` row names for the token, else `none` |
| **Section** | `<pkg>/<section>` |
| **Write to** | `docs/sources/<token>.md` |
| **Run** | `run-package <pkg>` |

### Designer — DESIGN

`subagent_type: "dev-team:designer"`, one per section.

| Field | Value |
|---|---|
| **Section** | `<pkg>/<section>` |
| **Mode** | `delta` when an open change file names the section; `document` when `<path>` holds code and there is no design; else `new` |
| **Contract** | `docs/packages/<pkg>/contract.md` |
| **Repo contract** | `docs/architecture.md` |
| **Dependency READMEs** | `<dep path>/README.md` per dependency, comma-separated; in `delta` and `document` modes `own: <path>/README.md` first when it exists |
| **Upstream interfaces** | per upstream package, as resolved above |
| **Source probes** | `docs/sources/<token>.md` per source |
| **Change file** | the open change file (`delta` only) |
| **Design-gap** | the tester's `design-gap` return, verbatim, when this run's tester returned one for the section |
| **Skills to invoke** | the row's `builds with` |
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
| **Upstream interfaces** | per upstream package, as resolved above |
| **Source probes** | `docs/sources/<token>.md` per source |
| **Regenerate** | the entry heading from the row's evidence when it reads `regenerate: <heading>` or `open <heading>` (a `spec-change:test`); else `none` |
| **Adopted code** | `yes` when the design's first line is `Mode: document`, else `no` |
| **Write to** | `tests/intent/<section>/ under <package root>` |
| **Run** | `run-package <pkg>` |

### Implementer — IMPLEMENT and FIX n

`subagent_type: "dev-team:implementer"`, one at a time: implementers never run in parallel,
since they share `pyproject.toml`, the workspace and `docs/deviations.md`.

The prompt is the output of `status.py --inputs <pkg>/<section>`, verbatim: the script
resolves every field of the implementer's **Inputs** — the review reports at FIX `n` and at a
cap granted *one more round*, the round, the open change file — and its docstring is the one
list of them. `/dev-team:pair` reads the files the same block names, so a section built here
and a section paired on by hand start from the same documents. Do not add, drop or rewrite a
line of it.

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
| **Upstream interfaces** | per upstream package, as resolved above |
| **Source probes** | `docs/sources/<token>.md` per source |
| **Intent tests** | `tests/intent/<section>/` |
| **Previous round** | from round 2: round `r-1`'s report paths, comma-separated; else `none` |
| **Diff** | from round 2: `<sha>..HEAD`, `<sha>` the `Commit:` line of round `r-1`'s `-s` report, or its `-a` report when `r-1` is 1 (the one report when it has no letter); else `none` |
| **Gate** | `.dev-team/gate.txt` |
| **Run** | `run-package <pkg>` |

### Architect — PLAN and the close

`subagent_type: "dev-team:architect"`, one per package: at PLAN it does what
`/dev-team:plan-package <pkg>` does, and at the close what `/dev-team:sync-plan <pkg>` does.

| Field | Value |
|---|---|
| **Package** | `<pkg>` |
| **Run** | `run-package <pkg>` |
| **Spec-change** | at PLAN only, one line per PLAN row: the entry heading from its evidence, `open <heading>` without `open `. At the close the block ends after `Run:` |

## Loop

Record `git rev-parse --short HEAD` as the start commit. Keep three counts for this run, in
your own memory only: agent runs per role; `design-gap` returns per section; and the sections
granted *one more round* at a cap.

1. **Run gate.** `status.py --run-gate <pkg>`. FAIL → **Summary** with its lines.
2. **State.** `status.py <pkg>`; keep the rows. With `--step`, go to **One step**. With a
   `<section>`, only that row counts from here on; if one of its in-package dependencies is not
   DONE, print which and why, and go to **Summary**. When every row that counts is DONE → step
   7.
3. **BLOCKED rows.** For each BLOCKED row that counts, **Asking**. A row granted *one more
   round* or *defer* this run is not asked again: step 4 runs it. After the answers, re-run
   step 2.
4. **The ready set.** The rows that count with `ready` `yes`, plus the rows granted a round or
   a defer. Take the first kind in this order that has any, and spawn every one of that kind in
   **one message**:
   1. PLAN → one architect for the package, a `Spec-change:` line per PLAN row.
   2. PROBE → the researchers.
   3. DESIGN → a designer per section; also a section at TEST whose last tester run this run
      returned `design-gap`.
   4. TEST → a tester per section.
   5. IMPLEMENT or FIX n → one implementer, for the first such row only. A cap row granted
      *one more round* gets its implementer here, then its `full` reviewer as a REVIEW.
   6. REVIEW → the reviewers of every such row: two per round-1 section, one otherwise; a row
      granted *defer* gets its `defer` reviewer here. Every reviewer of the batch — both of a
      round-1 pair included — is an Agent call in this one message; none waits for another's
      return.
5. **Branch** on each return's first line, `Result: <value>`:
   - `done` → nothing; a spec-change verdict is on disk and the next state shows it.
   - `design-gap` (tester) → the designer for that section in the next batch, with the whole
     return as `Design-gap:`. The third `design-gap` for one section in this run is a block
     instead: **Asking**, with the return's `Gap:` lines as the question.
   - `spec-change` → nothing to relay: the entry is in `docs/deviations.md` and `status.py`
     re-opens the step it names (PLAN, DESIGN or TEST), where the next block carries it.
   - `blocked` or `stopped`, or a first line that is not `Result:` → **Asking**, with the
     return as the question.
6. **Re-derive.** `status.py <pkg>`; print only the rows whose state changed. Back to step 2.
7. **Close.** When every section of the package is DONE, the architect with `Package:` and
   `Run:` only — the close. A `<section>` walk skips this unless its section was the last one
   not DONE. Then **Summary**.

On `request changes`, nothing is spawned from the verdict itself: the next `status.py` row
says FIX n (the implementer, then a `full` review) or BLOCKED with evidence `(cap)` — round 3,
or round 2 with a prior unfixed — and a cap goes to **Asking**, never to another implementer.

### One step

`--step <STEP>` runs that step for the named section once, against whatever is on disk and
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
  names them.

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

Your ledger edits stay uncommitted: `docs/decisions.md` is exempt from the run gate, the next
agent that stages it carries it, and otherwise the user commits it.

No questions when `AskUserQuestion` is not available (a headless run) or the command has
`--defer`: a cap with `--defer` is answered *defer*; every other block goes to **Summary**,
with the agent's first two lines, or the row's evidence, as `stopped because`.

## Summary

Always your last message, whether you finished or stopped, as this block and nothing after it:

```
run-package <arguments as typed>: <done | stopped at <section> <STEP>>
sections: <DONE>/<total> DONE; <section> · <state>, …
agent runs: designer <n> · tester <n> · implementer <n> · reviewer <n> · researcher <n> · architect <n>
commits: <start sha>..<end sha> (<count>)
stopped because: <the agent's first two lines, or the run gate's FAIL lines>
uncommitted: docs/decisions.md
next: <status.py's next line>
```

The first line echoes the command's arguments, so it says which walk this was: `run-package
data: done`, `run-package data ingest: done`, `run-package data ingest --step REVIEW: done`.
`done` means the walk you were asked for finished — the package closed, the section DONE, or
the one step run. `stopped because` appears only when stopped, `uncommitted` only when you
edited `docs/decisions.md`. `sections` and `next` come from a final `status.py <pkg>`, the
`next:` line copied as it prints; `commits` from `git rev-parse --short HEAD` and
`git rev-list --count <start>..HEAD`. Every agent run counts once under its role, the
architect's PLAN and close runs included.
