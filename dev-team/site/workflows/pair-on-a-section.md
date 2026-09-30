# Pairing on a section

```
/dev-team:pair app/dashboard
```

For a change you have to see to judge — a UI, a report's layout, a CLI's output — where the
loop is *say what you want, try it, find what is still missing, go again*. Running the design,
test, build and review loop once per nudge is slow and expensive. Pairing runs that inner loop
in your conversation, with nothing gating the edits, and hands the result back to the ordinary
loop once, at the end.

It needs a section that is already built: its state is REVIEW, FIX n, DONE, or BLOCKED at a
review cap. A section still at PLAN, PROBE, DESIGN, TEST or IMPLEMENT goes through
`/dev-team:run-package` first; pairing on top of an unfinished step would put two changes in
one review. Like every run, it starts from the run gate: a feature branch and a clean tree.

## Start

The skill records the start commit, then reads exactly what the section's implementer would:
the files `status.py --inputs app/dashboard` names (the block `/dev-team:run-package` sends
the implementer), plus the section's own README, the `D<n>` entries that bind it, its ledger
entries and its backlog lines. It briefs you in a few lines: what the section does, its public
names and who consumes them, the decisions that bind it, any open review findings, and the
boundary. A change to a public name, a consumed signature or a decided `D<n>` is a
spec-change. Anything else inside the section is at most a deviation.

## The loop

You say what to change; it edits the section's code and tells you how to see the result; you
try it. It runs the section's unit tests after a logic change, but not the full gate. Before an
edit that would cross the boundary it says so, and what that will cost. It keeps a running
list of every departure from the design, with the reason you gave for it, because the ledger
needs that reason later. It never touches `tests/intent/`, a contract, a design or another
section's code, and it commits nothing until wrap-up.

## Wrap-up

When you say you are done:

1. **Classify.** Each change is sorted by the clause it touches. A change the design leaves
   open (layout, styling, copy) needs no entry. The rest are a `deviation` (inside the
   section) or a `spec-change:<level>` (a boundary, or a test that asserts what no document
   says), by the implementer's own table. You see the list and correct it.
2. **Ledger.** One entry per deviation or spec-change in `docs/packages/<pkg>/deviations/<section>.md`, with your
   reason as its **Why**.
3. **README.** The section README is brought in line with the code, and its **Implementation
   notes** cite the new entries.
4. **Gate.** `gate_on_stop.py --report --base <start>` runs the stop gate's checks over
   everything since the start commit and writes the section's record, `.dev-team/gate/<pkg>/<section>.txt`. The next reviewer reads
   that file as its evidence, so it describes this code, not the last implementer's. You fix
   the FAIL lines together. A failing intent test whose clause a spec-change names is expected,
   because the tests are regenerated before the review.
5. **Commit.** One commit, `app/dashboard: pair — <what changed>`, trailer `Dev-Team-Run: pair
   app/dashboard`.
6. **Summary.** The entries, the gate result, the section's new state and `next:`.

## Back to the loop

```
/dev-team:run-package app
```

What happens next depends on the entries:

| Entries | What run-package does |
|---|---|
| none | REVIEW: one round, diff-scoped from round 2 |
| `deviation` | REVIEW. The reviewer approves or rejects each entry; the tester regenerates the intent tests an approved one cites; `sync-plan` writes it into the contracts when the package closes |
| `spec-change:test` | TEST first: the tester regenerates the tests, then REVIEW |
| `spec-change:design` | DESIGN first, then TEST, IMPLEMENT (usually little left to build) and REVIEW |
| `spec-change:contract` | PLAN first: the architect classifies the edit as it always does (on built code, a change file), then down the same path |

A pairing session at a review cap leaves the section BLOCKED on the cap. `next:` then says
`--step REVIEW` (one more round), which reviews the paired code.

Every pairing session that changes code costs one review round, and the cap counts rounds.
Several short sessions on one section reach the cap sooner than one long one.
