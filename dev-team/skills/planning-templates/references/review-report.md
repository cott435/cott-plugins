# `docs/packages/<pkg>/reviews/<section>/<date>-r<n>-<a, b or s>.md` — a review report

Written by the reviewer, one file per reviewer per round: `a` (conformance) and `b`
(correctness) in round 1, `s` from round 2 (`full`) and for a `defer` run, one directory per
section. Read by `status.py` (round, verdict, `Commit:`, `Convergence:`), the fix-round
implementer (the queue), the next reviewer (fixed / unfixed), never the documenter. `n` comes
from `status.py --rounds`, and so does `Commit:`: its `commit:` line, the section's last commit
(`git log -1 --format=%h -- <the section's paths>`), never `HEAD`, which in a parallel batch is
a sibling's report commit. A 2.0 report `docs/reviews/<date>-<pkg>-<section>-r<n>-<letter>.md`
is still read as round `n`. Never overwrite a report; the filename is the round.

Header, the first lines of the file, each `Key: value`:

```
# Review — <pkg>/<section> — round <n> — <focus>
Scope: <what was read — a conformance or full report names the intent-test files>
Commit: <the commit: line of status.py --rounds>
Verdict: approve | request changes | spec-change
Round: <n>
Focus: conformance | correctness | full | defer
Convergence: <k> prior unfixed, <m> new        (round 2 and later)
Diff: <sha>..HEAD                              (round 2 and later)
```

Then these headings, in order; an empty one is written with `- none`:

1. **CRITICAL** — one line per finding: `<file:line> — <finding> — <what to change>`. Only the
   closed list: a break (contract, decided `D<n>`, consumed shipped signature), a wrong result
   on the main path, a security finding, a silent or unreasoned deviation.
2. **WARNING** — should fix; the fix round picks these up.
3. **SUGGESTION** — consider; **Measured** values from the gate's output go here.
4. **Coverage** — `conformance` and `full` only: table `clause or design item | pass / fail /
   can't-tell | file:line`, one row per contract clause and design item.
5. **Carried** — round 2 and later: each prior CRITICAL as `fixed` or `unfixed`, worded as it
   was, with `file:line` where it stands.
6. **Spec-change** — when that is the verdict: one bullet per spec-change, starting with its
   level, `- design: …` (`test | design | contract`), then the evidence. `status.py` reads the
   level from there: until a ledger entry records it, the report is the open spec-change and
   re-opens that step. For a round-1 `b` report, which never writes the ledger, it is the only
   record. An `a` or `s` reviewer also appends the matching entry to `docs/packages/<pkg>/deviations/<section>.md`.
7. **Deferred** — `defer` runs only: each standing CRITICAL and the `docs/followups.md` line it
   became.

A round's verdict is the worst over its reports. Never a mechanical failure (the gate owns
those), never a fix, never a CRITICAL outside the closed list, and on round 2 or later never a
CRITICAL on code the fix did not touch that the previous round did not raise.
