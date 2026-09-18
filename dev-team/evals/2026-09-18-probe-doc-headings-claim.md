# Probe doc headings — a new `contracts.yml` claim, and the sweep over the generalized probe

**Tested against:** `d23232c` for every file under test *as committed*, with this change's
edits uncommitted — see the working-tree diff (`agents/researcher.md`, `agents/architect.md`,
`agents/designer.md`, `agents/reviewer.md`, `agents/implementer.md`, `contracts.yml`, and the
new `skills/planning-templates/references/source-probe.md`) · model: none, `contract_sweep.py`
is a deterministic script · 2026-09-18

## What was tested

The probe doc was, until this change, the one document in the bundle parsed by heading with no
`contracts.yml` claim behind it — the class of failure
`2026-09-17-documenter-interface-heading-contract.md` found on `interface.md`. Generalizing
`probe-source` into two kinds multiplied the exposure: the api template gained **Write
semantics** and **Webhooks**, the dataset template added fourteen headings of its own, and four
agents now cite headings across both. The claim under test:

> every probe-doc heading the architect, designer, reviewer or implementer names in prose is one
> `references/source-probe.md` actually defines.

Plus a regression check that the eight pre-existing claims still pass after a change that
touched five agents, eleven skills, the README and `flow.md`.

## Method

`python3 plugin-dev/scripts/contract_sweep.py dev-team`, from the marketplace root. The new
claim declares `owner: skills/planning-templates/references/source-probe.md` with
`owner_span: ['## Kind `api`', null]` — both kinds in one span, because a reader cites a heading
without knowing which kind the section it is designing will get — and four readers citing 25
heading names between them.

Two runs. The first was against a **draft where the templates were fenced `##` blocks inside
`agents/researcher.md`**, which is how the researcher had always carried them.

Deterministic, no model runs, no API cost.

## Results

| Case | Expected | Run 1 (templates fenced in the agent) | Run 2 (templates as a reference file) | Pass |
|---|---|---|---|---|
| probe doc headings owned | 25 names, all owned | **FAIL** — `no numbered template items found in the owner span` | PASS — 25 names across 4 readers, all owned | ✅ |
| 3 × `forbid` | 0 matches each | PASS | PASS | ✅ |
| `interface.md` headings | all owned | PASS | PASS | ✅ |
| section README headings | all owned | PASS | PASS | ✅ |
| 3 × `names_listed` | all listed | PASS | PASS | ✅ |

## Verdict

**The claim holds, and run 1 is the result worth keeping.** `check_headings` reads an owner
template through `template_items()`, which matches `^\d+\. \*\*(.+?)\*\*` — a *numbered,
bolded* list. A template written as `##` headings inside a fenced block defines, as far as the
checker is concerned, nothing at all, and the claim fails on its own owner rather than on any
reader. That is the checker being right for a reason worth writing down: every other owned
template in the bundle — the architect's five reference files, the implementer's `interface.md`
and section README — is a numbered bolded list, and a template in a second form is a template no
claim can be declared against.

So the fix was to the template, not to the claim or the tool: the two probe templates moved out
of `agents/researcher.md` into `skills/planning-templates/references/source-probe.md` in the
numbered-bolded form its five siblings use. `researcher.md` dropped from 377 to ~200 lines and
now invokes `planning-templates` for the template the way the architect does.

**What this does not do:** run an agent. A behavioral harness was not attempted — every claim
here is about file contents, which is what a mechanical check settles. In particular, nothing
here shows that a researcher *given* the new reference actually writes the headings it names,
or that a designer reads **Leakage** and excludes those columns. Those are prompt-behavior
claims and need a model run; they are the obvious next eval, and the cheapest of them is the
one with a wrong answer that a `grep` can catch — a dataset probe that writes a `.sample.json`
of real rows in violation of the statistics-only rule.

**Worth re-running** whenever a probe-doc heading is renamed, a sixth reader starts parsing the
document, or a template is added to `planning-templates` in any form other than a numbered
bolded list.
