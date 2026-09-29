---
name: pair
description: Work on one built section together in this conversation, for changes you have to see to judge, such as a UI. Loads the documents the section's implementer reads, edits the code turn by turn with no gate in the loop, then at wrap-up sorts the diff by clause into within-design, a deviation or a spec-change, updates the section README, writes the ledger entries, runs the stop gate's checks by hand, commits once, and prints the command that brings the documents back in line.
argument-hint: "<pkg>/<section>"
arguments: [target]
disable-model-invocation: true
---

Pair on **$target**. The whole command line was: **`$ARGUMENTS`**.

If the target above reached you unsubstituted, as a literal dollar-sign placeholder, take the
first word of the command line as the target.

This skill runs in your conversation, not in a fork, and spawns no agent. The user is the
designer and the reviewer: they say what to change, try it, and say what is still missing. You
are the implementer's hands for this one section, turn by turn. Nothing checks the edits while
you work, because the plugin's hooks gate its own agents only. The bar comes back at
**Wrap-up**, and the section goes back through a review under `/dev-team:run-package`
afterwards.

Every `status.py` below is `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py`, and
every `gate` is `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/gate_on_stop.py`, both run from the repo
root. `status.py` exits 1 on a failing gate; that is the answer, not an error.

## What you never do

- Write under `tests/intent/`. It is the tester's alone. An intent test the new behavior
  breaks becomes a ledger entry at **Wrap-up**, never an edit.
- Edit a contract, a design, a change file, a review report, `docs/constraints.md` or
  anything under `docs/sources/`. Those documents move through their owners at the next
  `/dev-team:run-package`, and the ledger entries you write are what moves them.
- Edit code outside the section, with the implementer's exceptions: shared test fixtures and
  the root `.gitignore`. When the change the user wants needs another section, say which
  section and what it lacks; pairing on it is a second `/dev-team:pair`.
- Lower a bar: add a `# noqa`, a `# type: ignore`, a `# pragma: no cover`, a skip or an xfail,
  remove an assert, or lower a threshold. Those are the **Guarded** items the gate fails on.
- Commit before **Wrap-up**, or stage anything but explicit paths. If the user commits on
  their own in between, that is fine: wrap-up diffs from the start commit.

## Start

1. **Target.** `<pkg>/<section>`. With no `/` in it, print `pair needs <pkg>/<section>` and
   stop.
2. **Run gate.** `status.py --run-gate <pkg>`. On FAIL, print its lines and stop.
3. **Start commit.** Record `git rev-parse --short HEAD`. You will print it in the brief, so
   it survives in the transcript.
4. **State.** `status.py <pkg>`, the section's row. Pairing refines code that exists, so it
   starts only from **REVIEW**, **FIX n**, **DONE**, or **BLOCKED** with `(cap)` in its
   evidence. Any other state means the documents are ahead of the code, or a decision is
   unanswered: print the row and the `next:` line, say pairing would put two changes in one
   review, and stop.
5. **Read.** `status.py --inputs <pkg>/<section>` prints the implementer's block. Read every
   file it names except the `Section`, `Round` and `Run` lines. For `Intent tests`, read
   only the test names and docstrings (`grep -rn '"""' <dir>`): each docstring cites the
   clause it tests, as `Design §<n> <item>`. Then read:
   - the section's own README, `<path>/README.md` (for `surface`,
     `docs/packages/<pkg>/interface.md`);
   - the `docs/decisions.md` entries whose `Scope:` covers `repo`, the package or the
     section;
   - the section's entries in `docs/deviations.md`, and its `docs/followups.md` lines.

   Read the section's code as you need it, not all at once.
6. **Brief.** Eight lines at most:
   - the start commit;
   - what the section does, from its README's **Purpose**;
   - its public names, from the README's **Entry points and interfaces** rows marked
     `Public: yes`, and who consumes them;
   - the decided `D<n>` entries that bind it;
   - at **FIX n** or a cap, the review's CRITICAL and WARNING lines;
   - the boundary: a change to a public name, a consumed signature or a decided `D<n>` is a
     spec-change; anything else inside the section is at most a deviation.

   Then ask what to change first.

## While pairing

- Make the change the user asks for, as the smallest diff that does it, in the section's own
  style. Before the first new module or public function, invoke `project-structure` and
  `python-style-guide` with the Skill tool; they are the conventions the reviewer checks.
- Tell the user how to see the change: the command that runs or restarts the thing they are
  judging. They judge it, not you. Never say it looks right when you have not seen it.
- After every `.py` edit, run `ruff format <file>`, `ruff check --fix <file>` and `ruff format
  <file>` again. The plugin's format hook does this for its agents, but not in your
  conversation, and an unformatted file is a FAIL line at wrap-up.
- After a logic change, run the section's unit tests (`<package root>/tests/unit/<section>/`
  with the Toolchain's test command). The full gate waits for **Wrap-up**.
- Before an edit that crosses the boundary in the brief, say so in one line: what it crosses,
  and what it costs at wrap-up. A spec-change re-opens PLAN, DESIGN or TEST, which means more
  agent runs. Make the edit if the user still wants it.
- Keep a running list of each departure from the design: the clause as the design numbers it
  (`design §<n> <item>`, or `contract §2 row <section>`) and the user's reason, in their words.
  **Wrap-up** needs the reason, and it is cheapest to write it down when the user says it.
- When the user answers an open `D<n>` along the way, record it as `/dev-team:run-package`'s
  **Asking** does: fill `Decision:` and set `Status: decided`, touching no other line.

## Wrap-up

When the user says they are done, or asks to wrap up:

1. **Diff.** `git diff --stat <start>` plus untracked files. Name any changed file that is
   not in this section, and which section it belongs to: the gate checks that section too.
2. **Classify.** One line per change, by the clause it touches. A change the design leaves
   open (layout, styling, copy, an internal helper) needs no entry. Every other change takes
   its kind from the implementer's **Which one, by the clause** table, under **Deviations and
   spec-changes** in `${CLAUDE_PLUGIN_ROOT}/agents/implementer.md`. Read it there: it is the
   one copy, and it sorts `deviation` from `spec-change:contract`, `spec-change:design` and
   `spec-change:test`. Show the list to the user and let them correct it before you write
   anything.
3. **Ledger.** Read `${CLAUDE_PLUGIN_ROOT}/skills/planning-templates/references/deviations-entry.md`,
   then append one entry per `deviation` or `spec-change` line to `docs/deviations.md` (create
   it with a `# Deviations` title when it does not exist). Heading `## <pkg>/<section> —
   <ISO date> — <kind>`. The fields:
   - **Clause**: the design item exactly as the intent tests cite it, `design §<n> <item>`.
     The gate tolerates a failing intent test only when its docstring matches this.
   - **Said**: the document's words, quoted.
   - **Did** for a deviation, or **Found** for a spec-change: what the code now does, with its
     `file:line`.
   - **Why**: the user's reason. A deviation with none is a CRITICAL review finding.
   - **Status**: `proposed` for a deviation, `open` for a spec-change.
   - **Raised by**: `pair — pair <pkg>/<section>`.
   - **Resolved by**: `—`.
4. **README.** Bring the section's README in line with the code as it now is, under the
   implementer's headings (its **Section README template**, in
   `${CLAUDE_PLUGIN_ROOT}/agents/implementer.md`). **Implementation notes** cites each new
   entry by its heading and never restates it. For `surface` the README is
   `docs/packages/<pkg>/interface.md`; when its **Public names** change, the entry is a
   spec-change, and `docs/api/<pkg>.md` follows it.
5. **Gate.** `gate --report --base <start>`. It runs the stop gate's checks over everything
   since the start commit and writes the section's record, `.dev-team/gate/<pkg>/<section>.txt`,
   which the next reviewer reads as its evidence. Go through each FAIL line with the user
   (an `ELSEWHERE` line is another section's intent tests, not this one's to fix):
   - lint, format, type, coverage or a unit test: fix it, then run the gate again;
   - an intent test whose clause a `spec-change` entry names: expected. The tests are
     regenerated before the section is reviewed, so leave it;
   - any other intent test: either the change departs from a clause with no entry (back to
     step 2), or it is a bug.

   Stop when it passes, or when the user says to leave the rest. The `result:` line then
   records it, and the reviewer quotes it.
6. **Commit.** One commit of every path changed since the start commit and not yet committed:
   the code, the unit tests, the README, `docs/deviations.md`, and `docs/decisions.md` if you
   edited it. Follow `git-workflow-and-versioning` §Project convention: stage by explicit
   path, commit with the same pathspec, and write the message
   `<pkg>/<section>: pair — <what changed>` with the trailer `Dev-Team-Run: pair
   <pkg>/<section>`.
7. **Summary.** Run `status.py <pkg>` and end with this block and nothing after it:

   ```
   pair <pkg>/<section>: wrapped up
   commits: <start sha>..<end sha> (<count>)
   entries: <heading> · <kind>, … | none
   gate: <the result: line>
   state: <the section's row: state · evidence>
   next: <status.py's next line>
   ```

   Then two lines on what that command will do next, going by the entries. None means one
   review round. A `deviation` means the reviewer approves or rejects it; the tester then
   regenerates the tests an approved one cites, and `sync-plan` writes it into the contracts
   when the package closes. A `spec-change` re-opens its level first: `test` → TEST, `design`
   → DESIGN, `contract` → PLAN, where the architect edits the contract.
