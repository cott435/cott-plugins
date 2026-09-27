# `docs/reviews/<date>-<pkg>-<section>-r<n>-<a, b or s>.md` — a review report

Written by the reviewer, one file per reviewer per round: `a` (conformance) and `b`
(correctness) in round 1, `s` from round 2 (`full`) and for a `defer` run. Read by
`status.py` (round, verdict, `Commit:`, `Convergence:`), the fix-round implementer (the queue),
the next reviewer (fixed / unfixed), never the documenter. `n` comes from `status.py --rounds`.
Never overwrite a report; the filename is the round.

Header, the first lines of the file, each `Key: value`:

```
# Review — <pkg>/<section> — round <n> — <focus>
Scope: <what was read>
Commit: <sha reviewed>
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
6. **Spec-change** — when that is the verdict: the level (`test | design | contract`) and the
   evidence; the same content as the `docs/deviations.md` entry the reviewer appends.
7. **Deferred** — `defer` runs only: each standing CRITICAL and the `docs/followups.md` line it
   became.

A round's verdict is the worst over its reports. Never a mechanical failure (the gate owns
those), never a fix, never a CRITICAL outside the closed list, and on round 2 or later never a
CRITICAL on code the fix did not touch that the previous round did not raise.
