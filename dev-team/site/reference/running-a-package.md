# Running a package

What `/dev-team:run-package <pkg>` does, step by step: the run gate, the ready set, what each return does, the checks before a package closes, when it asks you, and the states a section moves through. [The flow](../flow.md) has the chart; each route that ends here has a page under **Workflows**.

## The loop

`/dev-team:run-package <pkg>` walks every section of one package to DONE — the `surface`
section designed and tested right after PLAN, from the contract, and built last, from the
shipped READMEs — then closes the package. It runs in your conversation and spawns every agent
itself as `dev-team:<agent>`, one layer deep; no state is kept anywhere but on disk.

**Call paths** (item 5 of the contract) fixes, per command, the frames from `cli.py` to each
external effect and a depth budget (8 unless a decided `D<n>` says more), before any section
is designed. The surface's design and intent tests are written right after PLAN from the
contract; every section's design carries a skeleton for each entry point a path names, with
`frames to effect`; the paths review runs `status.py --paths <pkg> --against-contract` and
fails a frame the contract does not list, or lists and the code lacks, as a break. A contract
written before 2.6 has no heading: the `surface` row keeps waiting for every section, the
review runs as in 2.5, and the next close writes the heading as built, with a change file for
each command deeper than 8.

1. **Run gate.** `status.py --run-gate <pkg>`: the branch, the clean tree, the contract exists.
   Then **scaffold**: when `status.py --scaffold <pkg>` says the workspace is missing (no root
   `pyproject.toml`, or no package `pyproject.toml` in a uv workspace), one implementer builds
   it first — the root with the plugin's lint rules, the package skeleton, `uv sync`, one
   commit with `uv.lock`. Every tester then writes and runs its intent tests inside the
   workspace, under the repo's own lint rules.
2. **State.** `status.py <pkg>` derives one state per section from the documents, the code and
   git (**The states**, below). A re-run a week later, after hand edits or a crash, picks up
   exactly where the files say.
3. **The ready set.** A section is ready when it is neither DONE nor BLOCKED and every
   section it depends on in the package is DONE — except `surface` at PLAN, DESIGN and TEST
   once the contract has **Call paths**: only its IMPLEMENT waits for every section. Each
   role's **Dependency READMEs** line is copied from `status.py --fields`, which lists only the
   READMEs that exist, so the early surface designer and tester are sent only those (often
   `none`) and build to the contract's **Section interfaces** for the rest. The driver spawns every ready row's step in
   one message — probes, designs, tests, implementers, reviewer pairs together, whatever step
   each row is at — with one exception: a PLAN row runs the architect alone, since it edits
   what designers read. Implementers run in parallel: the write guard confines each to its
   section, the stop gate judges each on its own paths, the marker and the decisions inbox are
   per section, and `locked.py` serializes the three shared edits (`uv add`, an entry-point
   line through `entry_point.py`, the `.gitignore` block).
   `--serial` restores the 2.1 loop, one implementer at a time: the first kind of step
   in the order PLAN, PROBE, DESIGN, TEST, IMPLEMENT/FIX, REVIEW.
4. **Branch** on each return's first line, `Result: done | blocked | stopped | spec-change |
   design-gap`. A tester's `design-gap` goes back to the designer with the tester's reasons
   (three for one section in one run is a question for you); a tester that finds two design
   items contradicting each other returns `spec-change` instead. A `spec-change` needs no
   relay: its entry is in `docs/packages/<pkg>/deviations/<section>.md`, and the next
   `status.py` re-opens the step it names.
   `blocked` and `stopped` are asked, whatever row the next `status.py` shows. A return is the
   agent's first hand-back, and the only one the driver receives: what an implementer does
   after it — a gate retry, a block, a third red attempt — reaches the driver as a row, since
   the stop gate writes every stop to the section's record and `status.py` reads it.
5. **Re-derive** and loop.
6. **The integration check.** When every section is DONE, the driver runs
   `hooks/gate_on_stop.py --integration <pkg>`: every check CI runs — each **Floor** and
   **Enforced** row of `docs/constraints.md`, the repo-wide `pytest` included, else the
   Toolchain — over the whole repo, every failure a `FAIL`, recorded in
   `.dev-team/integration/<pkg>.txt`. A failure located in a section of the package re-opens it
   at FIX n with the record in its implementer's **Review**; once the fixed sections are DONE
   again, the check runs again. The paths review waits for `integration: pass`.
7. **The close.** When the paths review approves, the architect runs as `sync-plan`: approved
   deviations and pending change files go into the contracts, each verified against the code.
8. **Summary** — always the last message: sections, agent runs per role, the commit range, why
   it stopped, and `next:`, the exact command to type.

**The caps.** A review loop gets three rounds, two when a prior finding is unfixed. At the cap
the section is BLOCKED and the driver asks: *one more round*, or *defer*. `--defer` answers
*defer* without asking: the reviewer writes a `defer` report that moves the standing findings
to `docs/followups.md`, and the section is DONE.

**The ask step.** A decision with no assumption, a missing credential, a review cap or a third
`design-gap` stops the ready set for that section. The driver asks you once per block, writes
your answer into `docs/decisions.md` (`Decision:` and `Status: decided`) and runs the step
again. That ledger edit is the only file it ever writes, and it runs no git command that
writes. With nobody to ask — a headless run — it ends in the summary instead. Two more
questions come from the stop gate's record:

- **A section whose implementer blocked, or was let through after three red attempts,**
  after its hand-back: the row is BLOCKED with `gate …` evidence, and the driver quotes the
  record's `result:`, `FAIL` and `blocked:` lines and offers *run the implementer again*,
  *review anyway* or *stop here*. Neither answer touches `docs/decisions.md`; once a review
  round covers the code, the record is no longer read, so *review anyway* holds.
- **A package whose surface check fails** (`shipped: no (surface check FAIL)`, every section
  DONE): the driver quotes the `FAIL` lines of `status.py --surface <pkg>` and offers *fixed,
  retry* or *stop here*. The close waits until the check passes; the faulty rows are usually
  in sibling READMEs, which you correct.
- **A paths review that still requests changes at round 3** (`paths: round 3 (request changes:
  …) (cap)`): the driver quotes the line and offers *one more round*, which runs an
  implementer and a review for each section it names and then the paths review again, or
  *defer*, which moves the findings to `docs/followups.md`.
- **An integration check that still fails at run 3** (`integration: run 3 fail (reopens: …)
  (cap)`): the driver quotes the record's `FAIL` lines and offers *one more round* or *stop
  here*. There is no *defer*: a package whose whole-repo checks fail does not ship.
- **An integration failure no section of the package owns** (`integration: run <n> fail
  (reopens: no section named)`) — a test of another package, a shared config — or a run that
  ran out of time (`integration: run <n> incomplete`): the driver quotes the record's `FAIL`,
  `TIMEOUT`, `unowned:` and `unplaced:` lines and offers *fixed, run it again* or *stop here*.
  No agent of the run may edit there; you fix it, or run the check by hand with
  `DEV_TEAM_INTEGRATION_BUDGET` raised.

An answer that is none of the options — free text typed in place of a choice — ends the run
where it stands with the Summary. The driver does not act on the text; you read the Summary
and type what you want next.

`<section>` walks one section; `--step` runs one step of it once, whatever its state, which is
how *one more round* is typed by hand.

## Data-heavy sections

The architect marks, at PLAN, each section whose job is to clean, validate, reconcile or audit
data its dependencies produce, in the Sections table where you can see and edit it:
`stage:<token>` in the `source` cell and `dev-team:data-quality` in `builds with`. The plan
for the data is the contract's **Data stages** table, written at the same PLAN, before any
section is designed: one row per stage in the order they are profiled and cleaned, the first
the population every later stage is judged against (what instruments exist, keyed how), then
metadata, bars, facts. Each row holds the question the stage answers, what the data is and
which sections produce it (each in the cleaning section's `depends on`), the section that
cleans it, what clean means as numbered guarantees in the brief's words, the standards it is
judged against, and the pull: whole or a sample, its window, what that scope cannot judge, and
its cost in requests and minutes from the vendor probes, approved through one `D<n>` per
stage with an assumption. A guarantee is never a treatment: the kinds of failing row come
from the profile, and you decide each treatment. The run gate fails a marked row with no plan
row, an empty cell, or a producer the section does not depend on.

Before such a section is designed, once every section it depends on is DONE, the **profiler**
reads the data already on disk (else pulls it through the shipped entry points, as the plan's
pull cell says, with `.pull.py` beside the profile), runs checks over all of it as queries,
each check serving one of the plan's guarantees, counts the rows that pass, sorts the failing
rows into kinds and proposes a treatment for each: `repair`, `drop`, `quarantine` or `flag`. A
second profiler run, `Mode: verify`, in its own context, samples each kind's check and rejects
one that catches good rows or misses bad ones; a kind rejected twice is `unverified`. You are
asked about every verified `repair` or `drop`, since it changes or removes data; `quarantine`
and `flag` go ahead. The designer and implementer then build with `data-quality`: one handler
and one test per kind, and a failing row in no kind quarantined as `unclassified`.

After the reviewers approve, the profiler runs a round over the section's own output on the
same checks. Nothing new: `clean`, and the section is DONE. New kinds reopen the design through
a `spec-change:design` entry. When round 2 or later still finds new kinds, the section is
BLOCKED and the driver asks *one more round* or *defer*, which moves them to
`docs/followups.md`; `--defer` answers *defer*.

The profile is `docs/sources/<token>.md` — its **Plan** heading quotes the stage's row and
lists each guarantee with the checks that test it, so a reader knows what every check is
for — with its programs `.profile.py` (the checks) and `.pull.py` (the pull), and up to five
example rows per kind in `.sample.json` (the write guard refuses one over 200 KB); the pulled
input and the full failing rows stay in `.dev-team/data/<token>/`, not in git. Re-profile by hand with
`/dev-team:run-package <pkg> <section> --step PROBE`. A package with no `stage:` row runs
exactly as before.

## The states

Every section is in exactly one state, the first rule that matches, derived by `status.py` on
every call and never stored:

| State | When |
|---|---|
| **BLOCKED** | an open decision with no assumption binds the section; or the review cap is hit (round 3, or round 2 with a prior unfixed); or the stop gate's record for the section's current commit says the implementer blocked, or was let through after three attempts, and no review round covers that code; or a profile round 2 or later found new kinds and its spec-change is still open |
| **PLAN** | an open `spec-change:contract` entry names the section — the architect edits the contract and sets the entry `resolved` |
| **PROBE** | an `api:` source has no `## <pkg>/<section>` entry in its probe doc, or a `dataset:` source has no probe doc; or a `stage:` source's profile has no closed round 0 for the section (no round line yet, or one waiting on its verify run or a revision); or a marked section's reviewers approved it and its built output has not been profiled since the code last changed |
| **DESIGN** | no design; or an open `spec-change:design` entry (one written since 2.2 stays open until its `Status:` is `resolved`); or an open change file naming the section is newer than the design; or a probe doc it names lost or reworded a line the design was written against |
| **TEST** | no intent tests; or the design is newer than them; or an open `spec-change:test` entry; or an `approved` deviation's clause is cited by a test not yet regenerated |
| **IMPLEMENT** | no README (for `surface`, no `interface.md`); or the intent tests are newer than it (a regeneration commit, or one marked `intent tests current with design`, does not count); or the gate's record for the current commit says `not done`, a run that died between attempts |
| **REVIEW** | no review round; or round 1 lacks its `a` or `b` report; or the code is newer than the newest round's `Commit:`; or a `spec-change` verdict has no open entry left |
| **FIX n** | round `n` says `request changes`, under the cap, and nothing changed since; or the section is DONE and the package's paths review names it; or the section is DONE and the package's current integration record fails in its files, below run 3 |
| **DONE** | the newest round approves and the code is not newer than its `Commit:` |

A package is **shipped** when its `surface` section is DONE, `status.py --surface <pkg>`
passes, the integration check passes on the package's current code (`integration: pass`),
and its paths review, against the contract's **Call paths**, approves (`paths: approved`). A
package whose check fails prints `shipped: no (surface check FAIL)`; one whose whole-repo
checks have not run since its code last changed prints `shipped: no (integration needed)`, and
one whose commands have not been reviewed prints `shipped: no (paths needed)`, until
`/dev-team:run-package <pkg>` has run them. The integration record holds while nothing under
the package root changes; another package's later work does not unship it. A round is the
set of reports sharing `-r<n>`; its verdict is the worst of them.
