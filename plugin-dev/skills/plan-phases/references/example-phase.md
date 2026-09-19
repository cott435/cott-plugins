# A worked phase note

What `### The phase note` in `SKILL.md` describes, shown on a note that was actually run.
Read the note itself alongside this; nothing here copies it, so nothing here can drift from
it.

## Where it is

`${CLAUDE_PLUGIN_ROOT}/site/notes/0.9-evals-01-run-evals.md` — phase 1 of the plan that
added `run-evals` to plugin-dev. It is installed with the plugin, so it is readable from any
session. It was written before the phase-note structure had a name, so its Evals table sits
under `### Evals` inside **Steps**; a new note puts it at `## Evals`, between **Steps** and
**Done when**. Its `## Deviations` is the part `run-phase` appended when the note met the
real files.

## Section by section

- **Title and purpose paragraph.** `# 01 — run-evals`, then one paragraph that says what the
  phase adds and ends on the gap it closes — "every phase says 'run its evals' and none says
  how". It also says what is deliberately stubbed (the trigger kind), so the chat that reads
  it does not build ahead.
- **Decisions.** Only what would otherwise be guessed: the config directory names
  (`with_skill`, `old_skill`, `without_skill`), where the workspace lives, which script owns
  which layout. Each carries its reason — a name chosen because skill-creator's benchmark
  labels configurations by it is not a name the next chat will "improve".
- **Files.** A Path · Change table, one row per file, naming the section each edit lands
  in. It is the list of every file the chat opens; a file not in it is not this phase's.
- **Specification.** Frontmatter blocks, heading names, the set's JSON shape and the
  executor and grader prompts verbatim — anything another file parses or another model is
  given. The `contracts.yml` entry is written out in full, so the claim that enforces the
  headings ships in the same commit as the headings.
- **Steps.** Ordered so the bundle is consistent after each: the script before the files
  that cite its commands, the contracts check (with a planted defect that must fail) before
  `build-site`, and both before the evals.
- **Evals.** Platform facts first (E0.1–E0.5), each with its *assumed* answer written down
  before the test and what a later phase does if it comes out otherwise; then mechanical
  rows; the behavioral row last, naming its set file, its eval IDs, its baseline ref, and a
  pass bar with numbers (`with_skill` ≥ 90%, `old_skill` ≤ 40%).
- **Done when.** A checklist of commands and files — `check-contracts` prints all PASS, the
  planted defect failed, a path is ignored, named logs exist, the ledger row says `done`.
  Nothing on it needs judgment.
- **Deviations.** Absent when `plan-phases` writes the note. This one shows what `run-phase`
  appends when a step cannot be followed as written — what the note said, what was done,
  why — including a limit a later phase inherits.
