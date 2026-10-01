# 05 — reviewer

Phase 05. Rewrites the reviewer around a `Focus:`: in round 1 two reviewers run in parallel,
`conformance` (A: the coverage table, the seams, the deviations ledger) and `correctness` (B:
correctness and security); from round 2 one `full` reviewer scoped to the diff since the
previous round; a `defer` run moves the standing CRITICALs to the backlog and approves. It
writes the report shape phase 1 defined, names its file from `status.py --rounds`, approves or
rejects `proposed` deviations, returns `spec-change` as a verdict, and runs no command: every
mechanical result comes from `.dev-team/gate.txt`. CRITICAL is the closed list. Axis 0 and the
followups queue are gone. The gap it closes: the 0.6 loop did not converge because every
fresh reviewer re-sampled the whole section, ran every check again, and graded a wrong contract
as the implementer's failure.

## Decisions

- **Round 1 writers:** A alone edits `docs/deviations.md` statuses (`approved` / `rejected`)
  and appends `spec-change` entries; B writes only its report. Neither writes
  `docs/followups.md` in round 1 (the whole section is in scope, so nothing is out of diff).
  Reason: two parallel agents editing one file lose writes.
- **Round 2+ `full`** edits deviations statuses, appends out-of-diff WARNINGs to
  `docs/followups.md` as `- [ ] <pkg>/<section>: <finding> — noted <date>, see <report>`, and
  reads the previous round's reports for **Carried**.
- **`defer`** reads the newest round's reports only, writes `-r<n+1>-s.md` with `Verdict:
  approve`, `Focus: defer` and **Deferred**, appends `- [ ] <pkg>/<section>: <finding> —
  deferred <date>, see <report>` per standing CRITICAL, and never defers a CRITICAL that is a
  break or a security finding: those return `Result: blocked` naming the finding, as today's
  `--defer` did for kinds 1 and 2. Reason: the design's `--defer` decision.
- **`spec-change` as a verdict:** the report's **Spec-change** heading carries level and
  evidence, the reviewer appends the `spec-change:<level>` entry to `docs/deviations.md`, and
  the return's second line is `Verdict: spec-change`. A round whose verdict is `spec-change`
  is re-opened by `status.py` at the level's step.
- **The report file name** is `docs/reviews/<date>-<pkg>-<section>-r<n>-<letter>.md`, `n` from
  `status.py --rounds <pkg>/<section>`'s `next round:` line, the letter from the spawn prompt.
  No collision suffix: the round is literal.
- **Verdict precedence:** `spec-change` wins over `request changes` when both hold — a wrong
  document is fixed before code is judged against it; the CRITICALs still go in the report.
- **Round-2 coverage** lists only the clauses and design items the diff touches; untouched
  ones do not appear. A `defer` report's commit summary counts `(0 critical)`; each
  **Deferred** line says which closed-list kind the finding was, so the not-a-break check is
  visible. The reviewer does not fill `Resolved by:` when it sets `approved` or `rejected`
  (`sync-plan` does, at `synced`); it sets it on a `rejected` entry to its report path.
- **Security routing:** B in round 1 invokes `security-review`; the `full` reviewer invokes it
  when the diff touches a **When to Activate** trigger; A never.

## Files

| Path | Change |
|---|---|
| `agents/reviewer.md` | rewritten in full — specification below |
| `contracts.yml` | review-report `headings` claim added (owner the template, readers reviewer and implementer); deviations-entry claim gains the reviewer; order-of-authority reader span updated; probe-doc, section-README, interface.md and design-headings claims keep the reviewer's cites, `As shipped` and the integration/surface claims lose it; `docs/constraints.md` claim: reviewer cites `Measured`, `Exceptions` (not `Floor`, `Enforced`, `Guarded`); the plan-loop-exit claim's `agents/reviewer.md` file entry stays until phase 8 rewrites the claim |

## Specification

### `agents/reviewer.md`

```yaml
---
name: reviewer
description: Judges one section against its design, the contracts and the shipped documents it consumes, with a Focus — conformance or correctness in round 1, full and diff-scoped from round 2, defer to move standing findings to the backlog. Writes one report per run to docs/reviews/, approves or rejects proposed deviations, and runs no command — the stop gate's output is its evidence. Spawned by /dev-team:run-package at the REVIEW step.
tools: Read, Grep, Glob, Bash, Skill, Write, Edit
model: inherit
memory: project
skills:
  - project-structure
  - python-style-guide
  - git-workflow-and-versioning
color: yellow
---
```

Headings, in order: `## Inputs`, `## Order of authority`, `## Bash usage`, `## The evidence`,
`## Severity — what may be CRITICAL`, `## Focus: conformance`, `## Focus: correctness`,
`## Focus: full`, `## Focus: defer`, `## Deviations`, `## Verdict`, `## Report`, `## Commit`,
`## Return message`, `## Memory`.

**Inputs**: `Section:`, `Focus: conformance | correctness | full | defer`, `Round: <n>`,
`Letter: a | b | s`, `Design:`, `Contract:`, `Repo contract:`, `Dependency READMEs:`,
`Upstream interfaces:`, `Source probes:`, `Intent tests:`, `Previous round: <reports> | none`,
`Diff: <sha>..HEAD | none`, `Gate: .dev-team/gate.txt`, `Run:`.

**Order of authority**: the implementer's five documents, same wording, then the consumed-side
rule; span markers as the existing claim expects (`design line that a higher document
overrides` … `read together with`).

**Bash usage**: `git diff`, `git log`, `git blame`, `status.py --rounds`, `git add`/`commit`
for the report and the two ledgers, and nothing that runs the code: no tests, no linters, no
constraint command. The gate ran them; `.dev-team/gate.txt` is the record.

**The evidence**: `.dev-team/gate.txt` — its `FAIL` lines are the implementer's, already
reported; a `TOLERATED intent` line is a `proposed` deviation to judge; `MEASURED` lines go
under **SUGGESTION** verbatim. A report with no gate file (the run was let through after 3
attempts and the file is stale) says so under **WARNING**.

**Severity** — the closed list, verbatim from the design: a break (contract, decided `D<n>`,
consumed shipped signature); a wrong result on the main path; a security finding; a silent or
unreasoned deviation. On round 2 and later a finding outside `Diff:` that the previous round
did not raise is a WARNING filed to the backlog with `— noted`, never a CRITICAL.

**Focus: conformance** (round 1, A): the **Coverage** table, one row per contract clause
(Sections row, Section interfaces, Pipelines, Public surface (intent), Consumes) and per design
item (**Interfaces** rows, **Workflow / pipeline** steps, **Error handling and logging** cases,
**Tests**), `pass / fail / can't-tell` with `file:line`; the seams (consumed names against the
provider's shipped document; `api` parsers against **Observed schema**; a `dataset`'s target,
**Leakage** and **Splitting**); the README's seven headings against the code; **Deviations**
below.

**Focus: correctness** (round 1, B): edge cases, error paths, races; `security-review`
invoked when a **When to Activate** condition matches; tests testing behavior; function shape
and docstrings as WARNINGs.

**Focus: full** (round 2+): `git diff <Diff:> -- <section path> <tests/unit/<section>>
<tests/intent/<section>>` is the object; **Carried** classifies every prior CRITICAL `fixed` or
`unfixed` (one unfixed line per fact, `incomplete propagation of <prior finding>` when the same
fact stands elsewhere); `Convergence: <k> prior unfixed, <m> new`; the coverage table over the
diff's rows only; security when the diff hits a trigger.

**Focus: defer**: as **Decisions**.

**Deviations** (A and `full`): read
`${CLAUDE_PLUGIN_ROOT}/skills/planning-templates/references/deviations-entry.md`; for every
`proposed` entry of this section: `approved` when its `Why:` holds and its `Clause:` is internal,
`rejected` with a CRITICAL naming it otherwise; a `proposed` entry with an empty `Why:` is
CRITICAL *deviation recorded without a reason*; an unrecorded departure from the design is
CRITICAL. A `spec-change` the reviewer finds itself → the **Spec-change** heading, the entry,
the verdict.

**Verdict**: `request changes` when a CRITICAL stands; `spec-change` when the section's
document is what is wrong; `approve` otherwise. No `approve with fixes`: a WARNING does not
block and the fix round reads it from the report.

**Report**: read `${CLAUDE_PLUGIN_ROOT}/skills/planning-templates/references/review-report.md`
with the Read tool before writing; the file name per **Decisions**; the header lines and seven
headings as the template has them.

**Commit**: §Project convention (preloaded): the report, `docs/deviations.md` when edited,
`docs/followups.md` when appended; scope `review <pkg>/<section>`; summary `r<n>-<letter>:
<verdict> (<k> critical)`; trailer from `Run:`.

**Return message**, the first two lines fixed:

```
Result: done | blocked
Verdict: approve | request changes | spec-change
```

then, under 30 lines: `Report: <path>`; counts by severity; `Round:` and `Convergence:` (round
2+); deviations approved / rejected by heading; `Commit: <sha>`; the CRITICALs one line each.

### `contracts.yml`

```yaml
  - name: review report headings its readers parse are ones planning-templates defines
    # status.py reads the header lines, the fix-round implementer reads CRITICAL and WARNING,
    # the next reviewer reads Carried; a renamed heading leaves each reading nothing.
    owner: skills/planning-templates/references/review-report.md
    owner_span: ['1. **CRITICAL**', null]
    readers:
      - file: agents/reviewer.md
        cites: ['CRITICAL', 'WARNING', 'SUGGESTION', 'Coverage', 'Carried', 'Spec-change', 'Deferred']
      - file: agents/implementer.md
        cites: ['CRITICAL', 'WARNING']
```

Deviations-entry claim gains `- file: agents/reviewer.md` with `cites: ['Clause', 'Why',
'Status', 'Found']`. The `docs/constraints.md` claim's reviewer reader becomes `cites:
['Measured', 'Exceptions']`. The order-of-authority reader span stays as written if the two
marker phrases survive; otherwise both markers are set to the new file's phrases in the same
edit as the implementer's owner span (phase 4 chose them; keep them).

## Steps

1. `agents/reviewer.md`.
2. `contracts.yml`; plant `cites: ['Carried on']` and watch it fail.
3. The plugin's own rules (no skill added or removed).
4. `check-contracts`; `build-site`.
5. Evals, through `run-evals`, logged with `log-eval`.
6. Commit: `dev-team remake (phase 05): reviewer with Focus, coverage table, diff-scoped rounds, spec-change verdict, defer`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 5.1 | mechanical | `contracts.yml` | — | `check-contracts` + the planted cite | all PASS; the plant FAILs |
| 5.2 | behavioral | `reviewer` | previous | `evals/sets/reviewer.json` 1, 2, 3, 4 | every expectation passes for `with_skill`; `old_skill` fails the report file name, the `Focus:` line and the no-command rule |
| 5.3 | load | `reviewer` | — | the agents listing | the name appears |

## Done when

- `grep -c 'Axis 0\|followups queue\|approve with fixes' agents/reviewer.md` is 0.
- `grep -c 'Focus: ' agents/reviewer.md` ≥ 4.
- `check-contracts` all PASS with the review-report claim counted; `build-site` exits 0.
- Logs for 5.1–5.3 in `evals/README.md`.
- The ledger row for phase 5 reads `done`.

## Deviations

- **Order of authority: six items, not five.** The note says "the implementer's five
  documents"; the implementer has six since phase 4 (constraints, decisions, an open change
  file, package contract, repo contract, design), and the ledger's phase-4 note says the
  reviewer's list is those six. The reviewer lists six, same wording. Item 1 names Floor and
  Enforced unbolded: bolded, they fall inside the claim's reader span and are not implementer
  item names (a planted `**Floor**` fails the claim). Both span markers survive, so the span is
  unchanged: item 6 reads *read together with every `approved` entry … in
  `docs/deviations.md`*.
- **Design-headings claim.** The note says the reviewer's cites are kept. They named the plan
  review's headings (`Skills used`, `Contract deviations`), which the new file never reads. They
  now name what the Coverage table reads: `Interfaces`, `Workflow / pipeline`, `Error handling
  and logging`, `Tests`, `Open questions`.
- **Surface claim.** Followed as written: the reviewer was its only reader, so it now has
  `readers: []` and a comment that phase 6 deletes it with `surface.md`.
- **Deviations-entry claim.** The reviewer cites `Said`, `Raised by` and `Resolved by` as well
  as the note's four, since it appends spec-change entries and sets `Resolved by:` on a
  rejected entry.
- **Decided where the note is silent.** A round-1 `correctness` (B) reviewer that finds a wrong
  document writes it under its report's **Spec-change** with verdict `spec-change`, and writes
  no ledger entry (the note gives the ledger to A alone). A `blocked` return's second line is
  `Blocked: <reason>`, not a verdict. The gate always writes `.dev-team/gate.txt` (phase 2), so
  the note's "no gate file" case became: a `result:` line other than a pass is quoted under
  **WARNING**. A missing file, or one naming another section, is a WARNING too.
- **Commit summary.** The reviewer writes `review data/clean: r1-a: request changes (2
  critical)`, as the note and the eval set have it. `git-workflow-and-versioning`'s message
  table example has no colon after the section. That file is not in this phase's Files; see the
  ledger's *noticed:* line.
- **Pass bar 5.2: "`old_skill` fails … the no-command rule."** It cannot be observed: the eval
  harness forbids every command for both configurations, and the baseline ran none.
- **Eval set corrected.** `status.py` was added to the forbidden-command list of all four
  no-command expectations (user's yes). Iteration 1's eval-2 `with_skill` run had executed
  `status.py --rounds` against the plugin checkout and passed only because the list did not name
  it.
- **Pass bar 5.2 missed after one fix.** Bar: every expectation passes for `with_skill`.
  Iteration 1: 35/37, with two misses. Eval 1 added an eighth `## Deviations` report heading.
  Eval 2 re-filed round-1 WARNINGs to the backlog beside the new calendar.py line. There was
  also the `status.py` run above. The one fix, in `agents/reviewer.md`: no heading beyond the
  seven; the backlog takes only WARNINGs that **Severity** demoted; `Round:` is taken as given,
  with `status.py --rounds` only when the prompt has none. Iteration 2 reran evals 1 and 2,
  `with_skill` only. Evals 3 and 4 passed and never ran `status.py`, so the stricter
  expectation changes no verdict there. Eval 1 is 11/11. Eval 2 is 8/11. It found no
  calendar.py weekend fill, so there is no WARNING and no backlog line for it; its one backlog
  line is a different demoted finding. It classified `fill_gaps` `unfixed` under **Carried** but
  wrote **CRITICAL** `- none` and `(0 critical)`. The grader passed that; the phase chat
  regraded it FAIL. The second miss is a real defect: a `defer` run reads the standing CRITICALs
  from the **CRITICAL** heading, so it would find none to defer. On the user's call, a second
  fix went in: one sentence in **Focus: full** step 2 saying an `unfixed` prior finding also
  stands as a line under **CRITICAL**. Iteration 3 reran eval 2, `with_skill` only: 8/11.
  `fill_gaps` is now under **CRITICAL** and the commit reads `(1 critical)`. The three misses
  are all the calendar.py weekend fill: not found, so there is no WARNING, no backlog line, and
  no `docs/followups.md` to stage. Over three round-2 runs it was found once (iteration 1). The
  new **Focus: full** judges the diff and treats the rest of the section as context, which is
  the design's convergence rule. Finding an untouched out-of-diff defect is therefore sampling,
  not a rule the agent skips. Committed on the user's yes with the bar missed.
