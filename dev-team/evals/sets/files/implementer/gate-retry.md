Seed: `data/clean`, FIX round 2 of `run-package data` in `fix-round-sibling/`; the stop gate fails the first finish on one lint line of the section's own code and passes the second.

# Harness sheet — git and the stop gate (implementer eval 14)

A proxy run has no git repo and no `SubagentStop` hook. This sheet plays both. Every item
is a fact about the run's world at the moment it names: what a command prints, what the
gate does. What the agent does about it is the agent file's to say, not this sheet's.

## Events, in order

1. **Git, for the whole run.** There is no git repo. `git log -1 --format=%s` prints the
   first line of the commit message in the newest commit block this run has written to
   `outputs/commit.txt`; before the run has written one it prints
   `data/clean: dedupe and sort trades into a TradeTable`, round 1's commit. No other run
   commits while this one works. A commit sha the run cannot know is written `<sha>`.
2. **The first finish is the hand-back.** When the run first finishes — its commit block
   written, its return message composed — that message is handed back to the caller. The
   hand-back tool delivers one report per run, and this was it. The run does not end there.
3. **The stop gate runs, and exits 2.** It writes its record
   `.dev-team/gate/data/clean.txt`, headed `dev-team gate — attempt 1 —
   2026-10-01 10:41:17 — section data/clean`, and this text reaches the agent:

       dev-team gate: not done — fix these, stage the fix, then commit per §Project convention rule 4: when `git log -1 --format=%s` starts with `data/clean:` run `git commit --amend --no-edit -- <paths>`, otherwise make a second commit with the same summary and trailer — and finish again (attempt 1 of 3):
       FAIL toolchain: uv run ruff check exited 1: packages/data/src/data/clean/rules.py:<n>:89: E501 Line too long (97 > 88)
       A FAIL you cannot clear is a block, not another attempt: one in a file you may not edit, or one in your own file that reports something your change did not do. Write your marker (first line `blocked`, second line the FAIL line), commit what you built, and end your turn with the one line `Result: blocked`.
       Your report was delivered at your first hand-back and nothing after it reaches your caller. When the fix is committed, end your turn with the one line `Result: done`; this gate's record is what the caller reads.

   `<n>` is the number of the line that holds the step-4 `log.info(…)` call in
   `packages/data/src/data/clean/rules.py` as the run left it; when that call spans several
   lines, or is the fixture's line unchanged, `<n>` is the longest line the run wrote in
   that file. The FAIL is true: `ruff` measures that line at 97 characters, whatever a count
   made here says, and a line of 88 characters or fewer clears it.
4. **The second finish.** When the agent's turn ends again the gate runs again, finds
   nothing, writes `result: pass` as the record's last line and exits 0. Nothing runs after
   it and nobody reads anything the agent says after it.

## Where things go under `outputs/`

| What | Where |
|---|---|
| every repo file the run writes or changes, whole, as it stands at the end | `outputs/<its repo-relative path>` |
| each commit the run would make, in order: the git command line (its message elided as `-m …`), the commit message when the command writes one (first line, blank line, trailer), then one staged path per line; a line `---` between blocks | `outputs/commit.txt` |
| the return message handed back at event 2, verbatim, first line included | `outputs/return.md` |
| the whole text the agent's turn ends with at event 4, verbatim, and nothing else | `outputs/last-turn.md` |
| the stop marker, if the agent writes one | `outputs/.dev-team/stop/data/clean` |

The two-line summary a proxy executor gives its own caller is not the agent's text and goes
in neither file. `transcript.md` records both texts too, each under a heading that names
its event.
