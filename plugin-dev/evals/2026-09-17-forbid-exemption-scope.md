# `forbid` exemptions — does a pardoned line still catch a violation written on it?

**Tested against:** uncommitted — `near` is new in this change, see the working-tree diff ·
model: none, the subject is a deterministic script · 2026-09-17

## What was tested

The 0.4.0 eval found that `forbid`'s `unless` matches the whole **line**, so one exempt phrase
pardons everything else on it. That was fixed for the claim it was found in — the unprefixed
command claim, whose exemptions moved into the pattern — and recorded as a lesson about the
bundle's oldest claim: *`no file promises a repo a `scripts/` directory` still has eight
line-scoped exemptions and has not been probed this way.* This is that probe.

A claim reporting `PASS` is worth what its last planted defect was worth. So: for every line the
eight exemptions actually pardon, plant a genuine violation of the shape the claim exists to
catch, and see whether the claim still reports it.

## Method

Enumerated the lines each exemption pardons by running the claim's own pattern and each `unless`
regex over the authored set — 10 distinct lines across 8 files. Onto each, appended a real
violation: *"Put the pipeline driver in scripts/run.py at the repo root."* — the exact promise
`project-structure` §1 forbids. Ran the sweep after each, restoring the file between runs. Same
for the bundle's second `forbid` claim, whose `unless: ['finalize-package']` is line-scoped in the
same way. One control: the same violation on a line with no exemption. No model runs, no API cost.

## Results — before

| Planted on | Expected | Observed |
|---|---|---|
| all 10 pardoned lines (`README.md` ×2, `implementer.md`, `project-structure` ×2, `finalize-package`, `status`, `surface.md`, `CLAUDE.md`, `site/README.md`) | FAIL | **passed — 10/10 missed** |
| `docs/api` credited to `finalize-project` on a line also containing the word `finalize-package` | FAIL | **passed — missed** |
| control: the violation on an unexempted line | FAIL | FAIL ✅ |

**Eleven of eleven leaked.** The claim worked only where no exemption was present — which is to
say, nowhere that `scripts/` is discussed. Every file that explains the prohibition was a place
the prohibition could be contradicted for free.

## The fix

`near: <n>` on a `forbid` claim scopes `all_of` and `unless` to the matched text plus n
characters either side instead of the whole line. An exemption then pardons the occurrence it
describes. Both claims set `near: 40`, and three of the eight exemptions were dropped in the same
change as dead weight the enumeration exposed:

- `'There is no `scripts/`'` — every line it pardoned was already pardoned by `'no `scripts/`'`.
- `'\[project\.scripts\]'` — same, redundant with the prohibition sentence it co-occurs with.
- `'\.probe\.py'` — pardoned **nothing**. The line it was written for no longer matches the
  pattern, and nobody noticed, because a dead exemption and a working one look identical from a
  `PASS`.

## Results — after

| Case | Expected | Observed |
|---|---|---|
| all 10 previously-pardoned lines | FAIL | FAIL, 10/10 ✅ |
| `docs/api` credited to `finalize-project` alone | FAIL | FAIL ✅ |
| the 5 remaining exemptions, clean bundle | silent | silent, 8/8 pass ✅ |
| violation ~45 and ~80 chars from the exempt phrase | FAIL | FAIL ✅ |
| violation **inside the same clause** as the exempt phrase | FAIL | **pardoned — residual** |
| `headings`: an `owner_span` end marker that no longer exists | FAIL loudly | FAIL `could not run: end marker not found` ✅ |

## Verdict

**Fixed, with one residual stated rather than papered over.** A violation written within 40
characters of the phrase that pardons it is still pardoned — "there is no `scripts/` directory,
so use `scripts/run.py`" passes. That is a self-contradicting clause a reader would catch, and it
is not the failure mode the audit found; the ten real leaks were all far outside the window.
Lower `n` to tighten it, or express the exemption structurally in the pattern, which has no
window at all. Both options are now in the skill.

Three things worth keeping:

- **Enumerate what an exemption pardons before trusting it.** The list of pardoned lines took one
  short script and immediately produced three deletions and ten leaks. No amount of reading the
  `unless` list would have shown that `'\.probe\.py'` matched nothing.
- **A dead exemption is indistinguishable from a live one at a glance**, and it is worse than
  noise: it pardons whatever drifts into its phrasing later. Re-enumerate when a pattern changes.
- **The first fix for this bug was applied to one claim and recorded as a lesson for the other.**
  The lesson sat in an eval for one release while the older claim kept reporting `PASS` over ten
  unprotected lines. A known hole in a checker should be probed everywhere it can exist in the
  same change, not filed as a lead.

**Not a behavioral eval.** This settles what the checker reports about file contents, nothing
about whether an agent obeys a rule it reads.

**Re-run on any change to a `forbid` pattern or its exemptions** — re-enumerate the pardoned
lines first, then plant on each one.
