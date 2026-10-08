---
name: data-quality
description: How a data-heavy section is designed and built from its data profile - one handler and one test per kind of failing row, a treatment only where the user decided it, every rejected or altered row kept with its kind as the reason, and unclassified rows quarantined. Invoke when a section's contract row lists dev-team:data-quality under builds with, before designing or building that section. Not for a section that only passes data through.
user-invocable: false
---

# Building a section from its data profile

The profile is the `docs/sources/<token>.md` among your **Source probes** whose title line says
`stage`. It was written from all the real data this section receives, not a sample of it. This
skill is how its kinds become code: one handler, one treatment and one test per kind.

## Reading a profile

- **Plan** — the stage's question and its numbered guarantees, each with the checks that
  test it. The design's **Purpose and scope** states them as what the section promises, and
  the kinds table below is ordered by the guarantee a kind's checks serve.
- **Observed schema** — the shape to parse: columns, dtypes, nulls, ranges.
- **Checks** — each rule `C<n>` and what it judges against. The built section runs all of them.
- **Quirks** — the kinds: id, the checks that isolate it, its count, the proposed treatment,
  its `D<n>`, and `verified` or `unverified`. A kind marked `unverified` is not designed for:
  its rows are unclassified (below), because no second look confirmed its check.
- **Unexplained** — how many failing rows are still in no kind; they too are unclassified.
- `<token>.sample.json` — up to five rows per kind id, and `accepted`, five rows that pass
  every check. These are the test fixtures.

## The design's kinds table

Under the design's **Workflow / pipeline**, after the steps, one row per verified kind:

`| kind | rule | handler | treatment | decided by |`

`kind` is `K<n>` and its name; `rule` the check in the design's own words; `handler` the
function that isolates and treats it; `treatment` one of `repair`, `drop`, `quarantine`, `flag`;
`decided by` the `D<n>`, `D<n> (open)` for a kind quarantined while its decision waits, or `—`
for a kind that needs none. Rows are grouped by **Plan** guarantee, in its order, and the
handlers run in the table's order.

## Treatments

A treatment is `repair` or `drop` only where its `D<n>` in `docs/decisions.md` reads
`Status: decided`, and it is what the decision says, which may differ from the profile's
proposal: the user's answer is the rule, the proposal was a question. A kind whose `D<n>` is
open is quarantined, and listed under the design's **Open questions** as waiting on that
decision, so nothing is changed or removed before the user says yes.

- `quarantine` — the row is kept out of the output and kept in the reject record.
- `flag` — the row passes into the output, marked with its kind id; how it is marked is the
  design's to say.

## The reject record

Every rejected or altered row is kept: its key columns, the kind id as the reason, the
treatment applied, and for a `repair` the value before. Nothing is rewritten or removed
silently, because a rule that is wrong is found only by reading what it touched. A repaired
row is in the output and in the record; a flagged row is in the output, marked, and in the
record with the treatment `flag`. Where the record is stored is the package contract's to say.

## Unclassified rows

A row that fails a check and matches no kind in the table is quarantined with the reason
`unclassified`. So a built section sorts every input row into exactly one of: accepted, a
decided kind, or `unclassified`, and never raises on or passes an unexpected row. The section
runs every check in the profile's **Checks** table, not only the checks of verified kinds, so a
row of an `unverified` kind is caught and lands here, where the next profile round finds it.

## Tests

The design's **Tests** names:

- one case per kind, run on that kind's rows in `<token>.sample.json`, asserting the
  treatment and the reject record's reason;
- one case that the `accepted` rows stay accepted and unchanged;
- one case that a failing row of no kind is quarantined as `unclassified`.

A kind whose check compares rows (a duplicate, an out-of-order timestamp) is tested together
with the rows it is compared against, taken from `accepted`.

## What the README says

The section README's **Pipeline / workflow** lists the handlers in order with their kind ids,
and its **Implementation notes** names the profile and the round it was built from. The
design's **Skills used** lists `data-quality`, so the implementer invokes it too.
