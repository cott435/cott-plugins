# `plan-phases` / `run-phase` — the bundle's first `contracts.yml` passes, and each claim can fail

**Tested against:** uncommitted — see working-tree diff (`plugin-dev/contracts.yml`, `README.md`, `site/site.yml`, `skills/plan-phases/`, `skills/run-phase/`); `contract_sweep.py` at `d23232c` · model: Claude Fable 5.1 (Cowork session; mechanical run, no agent behavior involved) · 2026-09-18

## What was tested

Adding the two phase skills gave `plugin-dev` its first `contracts.yml` with three claims: no bare
`/<name>` command anywhere in the bundle; the README's **The skills** table names every directory
under `skills/`; every `disable-model-invocation: true` skill is in `site.yml`'s run order. The
claim: all three pass on the real bundle, and each fails on a planted defect — per this plugin's
own `CLAUDE.md` rule that a checker that cannot fail is worse than none.

## Method

Two runs of `scripts/contract_sweep.py` from `plugin-dev/`. Positive: the working tree as is.
Negative: a copy with three defects planted at once — `Run /run-phase now.` appended to
`README.md`, the `run-phase` row deleted from the skills table, `- run-phase` deleted from
`site/site.yml`. No agent runs; the skills' behavior (does `run-phase` actually stop after one
phase, does `plan-phases` produce notes that a cold chat can follow) is untested here and is the
first thing the next `run-phase` chat of `dev-team`'s 0.5 overhaul should log.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| real bundle, forbid | PASS, 0 matches | PASS, 0 matches | ✓ |
| real bundle, README table | PASS, 7 names | PASS, 7 names, all listed | ✓ |
| real bundle, site.yml order | PASS, 2 names | PASS, 2 names matching `where` | ✓ |
| planted bare `/run-phase` | FAIL naming the line | FAIL `README.md:161` | ✓ |
| README row removed | FAIL naming `run-phase` | FAIL `not listed in README.md: run-phase` | ✓ |
| site.yml entry removed | FAIL naming `run-phase` | FAIL `not listed in site/site.yml: run-phase` | ✓ |

The site also rebuilt with the three workflow pages in `site.yml` order and both skills under
Workflow skills; `site/docs/` could not be cleared in the sandbox (no delete permission), so the
rebuild was in place.

## Verdict

Held, 6/6. Nothing changed in response. Open: the two skills' behavioral claims — logged by the
first real `run-phase` chat, against `dev-team` `0.5-overhaul` phase 2 or later.
