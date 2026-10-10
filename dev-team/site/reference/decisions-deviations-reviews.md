# Questions, decisions, deviations and reviews

The records a run leaves and reads besides the designs and the code: how an agent asks you something, the decisions ledger, a section's deviations ledger, and the review reports. `planning-templates` holds the exact headings of each.

## Questions

Subagents cannot ask you anything — Claude Code removes `AskUserQuestion` from every subagent.
So an agent with a question that changes a boundary writes a stub to `docs/decisions.md` (a
designer under the driver writes it to its section's inbox, **Decisions** below), tagged
`Raised by: /dev-team:plan-package data (interview)`, writes nothing else, and **stops**:

```
Stopped for decisions: D12, D13
- D12 — Bars: store timestamps as UTC or exchange-local? (assumption: UTC)
- D13 — Is audit its own section or part of clean? (assumption: its own)
Answer in docs/decisions.md, or re-run `/dev-team:plan-package data` as-is to accept the assumptions.
```

Fill in `Decision:` and set `Status: decided`, or do nothing — either way, re-run the same
command. The tag is how it knows not to ask twice. Under `/dev-team:run-package` the driver does
this for you: it shows the question with the stub's `Recommendation:`, records your answer and
continues.

## Decisions

Subagents start with a fresh context and never see your conversation, so anything you decide
has to be in a file. `docs/decisions.md` is that file, and it outranks every document a section
is built from. One ledger for the whole repo, one `D<n>` sequence.

```markdown

## Deviations and spec-changes

`docs/packages/<pkg>/deviations/<section>.md` is a section's ledger for "the document and the
code disagree", one file per section so agents running in parallel on different sections never
write the same file, one entry per item, `## <pkg>/<section> — <date> — <kind> — <k>` (`<k>` the
entry's sequence in the file, so two entries of one day never share a heading), with
**Clause**, **Said**, **Did** or **Found**, **Why**, **Status**, **Raised by** and **Resolved
by**. Append-only; the status line is the only edit. The older locations — the 2.0
`docs/deviations/<pkg>/<section>.md` and the pre-2.0 `docs/deviations.md` — are still read, and
an entry is edited where it is; a heading without `— <k>` still parses. An intent test tags a
tolerated clause `(deviation <date>-<k>)`.

- **`deviation`** — the implementer built something other than the design said, inside its
  section, for a reason. It writes the entry `proposed`; the reviewer sets `approved` or
  `rejected`; the tester regenerates the intent tests that cite an approved clause; `sync-plan`
  applies it to the contracts and sets `synced`. A departure with no entry, or with an empty
  **Why**, is a CRITICAL finding.
- **`spec-change:<level>`** — a document is wrong: a boundary shape, a public name, a test
  that asserts what no document says. The designer, tester, implementer or reviewer writes it
  `open` with its evidence, and `status.py` re-opens the step for its level: `test` → TEST,
  `design` → DESIGN, `contract` → PLAN, where the architect edits the contract and sets it
  `resolved`. A tester that finds two design items contradicting each other appends a
  `spec-change:design` citing both under **Found** and returns `Result: spec-change`. An entry
  written since 2.2 (its heading ends `— <k>`) is open until the agent that answers it sets
  its `Status:` to `resolved` — the tester for `test`, the designer for `design`, the
  architect for `contract` — whatever was committed since, and every open entry of a level
  reaches that agent in one spawn: `status.py`'s evidence lists them all (`open <h1>; <h2>`),
  and the driver sends each on its own line. An agent handed several sets `resolved` only on
  those its commit answers. An older entry without `— <k>`, and a review report's
  `spec-change` verdict, keep the earlier rule: answered by the next commit of the level's
  document, and `sync-plan` sweeps any such entry still `open` at the close. A spec-change is
  a normal exit, not a failure.
- **Two cases agents used to guess at.** An intent test that fails before it reaches the
  section's code — its own helper, fixture or import is broken — is a `spec-change:test`,
  with the test's docstring citation as **Clause** and the traceback line as **Found**. A
  signature the contract's **Section interfaces** states for a name that is not public is a
  seam: changing how a caller calls it is a `spec-change:contract`, while an additive,
  compatible change, such as a new optional parameter, is a `deviation`.

## Reviews

Round 1 is two reviewers in parallel, each writing its own report: **A** (`Focus:
conformance`) owns a coverage table with one row per contract clause and design item — pass,
fail or can't-tell, with `file:line` — plus the seams and the deviations ledger; **B**
(`Focus: correctness`) owns correctness and security. From round 2 one reviewer (`Focus:
full`) reads only the diff since the last round and the previous reports, classifies each
prior finding fixed or unfixed, and may raise a new CRITICAL only on lines the fix touched, so
the finding count can only fall.

Reports are `docs/packages/<pkg>/reviews/<section>/<date>-r<n>-<a|b|s>.md`, one directory per
section (a 2.0 `docs/reviews/<date>-<pkg>-<section>-r<n>-<letter>.md` is still read as that
round), and the report is the queue: the fix-round implementer reads its **CRITICAL** and
**WARNING** lines. A report's `Commit:` is the section's last commit as `status.py --rounds`
prints it, never `HEAD`, which in a batch may be a sibling's. The verdict is `approve`,
`request changes` or `spec-change`.

Once every section is DONE, one more reviewer (`Focus: paths`) follows each command of the
package from `cli.py` to its external effects, on the call tree `status.py --paths <pkg>
--against-contract` prints: each command's built frames beside its **Call paths** entry, each
frame `match`, `extra` (in the code, not in the contract) or `missing`; an open change file's
entry for a command stands in for the contract's until `sync-plan` applies it. It writes
`docs/packages/<pkg>/reviews/paths/<date>-r<n>-p.md`, with one row per command under **Paths**
and a `contract` column. An `extra` or `missing` frame is a break, CRITICAL under the section
that holds it; beyond that it may block on four things only: a command deeper than its
**Call paths** budget, or than 8 frames from its first external effect when the contract has
no entry for it (P1), a lambda, closure or mapping dispatch on a main path (P2), a
pipeline or orchestrator that fails the reader's test in `python-style-guide`'s
`references/pipelines.md` (P3), and a trivial single-use helper or options bag on a main path
(P4). Each finding names a section, and `status.py` re-opens that section as FIX n with the
paths report as its previous round. A package is not shipped until this review approves; at
round 3 the driver asks *one more round* or *defer*. A package with no `[project.scripts]`
commands needs no paths review.

A designer's `proposed` entry against a contract row — its §10 items — is judged by one test,
the one the designer applied: additive and compatible (a new optional parameter, a helper the
row does not name) is `approved` and folded in at the close; anything a consumer must change
for (a signature, a public name, a shape) is `rejected`, a `spec-change:contract` is appended,
and the verdict is `spec-change`.

CRITICAL is a closed list: a **break** (a contract, a decided `D<n>`, or a name a consumer takes
from a shipped document), a **wrong result** on the main path, a **security** finding, a
**silent or unreasoned deviation**. Everything else is a WARNING or a SUGGESTION. A mechanical
failure is never the reviewer's: the stop gate already ran it, and the reviewer runs no command.
An out-of-diff finding on round 2+, and each `ELSEWHERE` line, is appended to `docs/followups.md`, the backlog —
work no loop step will pick up, never counted and never a gate. At the cap,
[Running a package](running-a-package.md) says what happens.
