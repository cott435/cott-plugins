# `docs/sources/<token>.md` — the data profile

Written by the `profiler` for one `stage:<token>` source: the real data a data-heavy section
will receive, checked as a whole, its failing rows sorted into kinds. Read by the designer,
tester, implementer and reviewer as a source probe (the `Source probes:` field delivers it), by
`data-quality`, by `status.py` (the newest round line decides the next run) and by later
profiler rounds. Budget 200 lines, the **Rounds** blocks not counted.

**Every profile opens with the same three lines**, before heading 1:

```
# Source probe — <token> — stage — <date>

Purpose: <the section's row, its responsibility cell>
Profile: <token>.profile.py · Pull: <token>.pull.py · Examples: <token>.sample.json
```

**Append-only after round 0 closes.** Every line present when the round-0 closing line was
written stays byte for byte. Later rounds add lines — a new kind under **Quirks**, a
`### Round <n>` block, a round line — and never reword one, because `status.py` sends a section
back to DESIGN for a reworded line and ignores added ones.

In a profile each item below is a `## <Name>` heading, in this order, as in a source probe; the
`## <pkg>/<section>` heading follows `## Sections served`.

1. **Access** — `Location: <path>` — `on disk` | `pulled (<n> of cap <m> <unit>)` | `missing`;
   then format, size, file count.

2. **Provenance** — the dependency entry points that produced the data, each with its section's
   commit, and the vendor probe docs it rests on.

3. **Plan** — the stage's **Data stages** row from the package contract, quoted: its
   `question`, then its `clean means` guarantees as numbered lines, each ending with the
   checks that test it (`1. <guarantee> — C1, C2, C17`) or `not checkable: <why>`; then
   `Pull: planned <the pull cell> — done <what was pulled, from pull.json>`, and the reason
   when they differ. A contract with no such row quotes its **Package conventions** line, and
   the guarantees are the groups the checks fall into. This is what each check is for: a
   reader starts here, not at **Checks**.

4. **Shape** — rows × columns per table or file kind; the whole data, or a seeded sample with
   its seed and n. Under a sample every count below says `(sample)`.

5. **Observed schema** — per column: column | dtype as loaded | declared dtype | null % |
   distinct | range or top-k | notes. A column that looks personal is `<redacted>`, and its notes
   cell says `personal`; **Quirks** never names it.

6. **Duplicates and keys** — the exact-duplicate row count; each candidate key and whether it
   is unique.

7. **Checks** — table: `C<n>` | rule | judged against | rows failing | of. `judged against` is a
   document and heading (a contract shape, a vendor probe's **Observed schema**, a project
   skill's rule) or a comparison (the calendar, neighbouring rows of the same key, a second
   source); the rows are grouped by the **Plan** guarantee they serve, in its order.

8. **Quirks** — the kinds, one line each, in the order of the **Plan** guarantee their checks serve:
   `` - K<n> <name> — checks C<a>, C<b>; <count> of <denominator>; <what it is, one clause>; proposed: <repair | drop | quarantine | flag>; <D<n> | no decision needed>; <verified | unverified> ``.
   Before the verify run the last two fields read `D?` (or `no decision needed`) and
   `unverified`; the verify run rewrites those two fields of the kinds it judged, and that is
   the one edit a line under this heading ever gets, made before the round that added the kind
   closes. A duplicates kind counts the extra copies, the rows a `drop` would remove.

9. **Unexplained** — `<n> of <all failing rows>` failing rows in no kind, then the largest
   remaining groups, one line each. The rows of a kind a verify run rejected a second time
   (it stays `unverified`) count here; a kind still awaiting its verify run does not.

10. **Expected and not found** — each rule of the row's project skills that matched no row, one
   line each; a rule that could not be checked is `not checkable: <why>`.

11. **Rounds** — one `### Round <n>` block appended per round: a table check | accepted |
    rejected | previous round. Round 0's block has the one column `rows failing`.

12. **Cost and time of a full pass** — wall time, peak memory, rows scanned; for a pull, the
    requests made and the quota used.

13. **Sections served** — one `## <pkg>/<section>` heading (a `##` heading, literally): the
    purpose, then one round line per closed step, appended at the end of that block, never
    edited or removed (a `pending verify` or `revise:` line stays above the line that follows
    it): `Round <n> — <date> — commit <sha | none> — <verdict>`. Round 0's commit is `none`.
    Verdicts: `pending verify` · `revise: K<a>, K<b>` (`plan` among the names when **Plan**
    left a guarantee untested) · `kinds: <k> (<d> to decide)` · `new kinds: K<a>, …` ·
    `clean` · `deferred`.

**`<token>.pull.py`** — the pull as its own program: it calls the shipped dependency entry
points, writes `<Store>input/` to the **Plan**'s pull cell, records what it pulled, the
requests made and the wall time in `<Store>input/pull.json`, and refuses to run while the
input exists. `<token>.profile.py` holds the checks and never pulls.

**`<token>.sample.json`** — one key per kind id holding up to five failing rows as the stage
holds them, and `accepted` holding five rows that pass every check; each row carries its key
columns; never over 200 KB; written with the Write tool (a revise run may Edit its reworked
kinds' rows).
