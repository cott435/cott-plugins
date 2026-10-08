# fix-issues phase 6 — the bundle's contracts with fix-issues added, and the typed skill loads (M6.1, L6.1)

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `1984aa1`): `skills/fix-issues/SKILL.md`, `skills/bump-version/SKILL.md`, `skills/audit-run/SKILL.md`, `README.md`, `site/site.yml`, `contracts.yml` · model: none for M6.1 (a script); `claude-sonnet-5-5` for L6.1 · 2026-10-07
**Set:** none — M6.1 and L6.1 are rows of `site/notes/0.16-audit-ledger-06-fix-issues.md` **Evals** with no set · **Iteration:** none, run in the phase chat · **Baseline:** none (new skill) · **Pass rate:** M6.1 3/3 · L6.1 1/1

## What was tested

M6.1: that the bundle's own `contracts.yml` passes with `fix-issues` added — the README's
**The skills** table and `site/site.yml`'s typed run order list it, and the two template
`headings` claims hold with fix-issues and bump-version as readers. L6.1: that the typed skill
registers and, from a plugin with no `audits/`, says so and stops.

## Method

- M6.1: `python3 scripts/contract_sweep.py` from `plugin-dev/` (the working copy), then
  `site/site.yml` and the README read for the new line and row.
- L6.1: a scratch plugin (`.claude-plugin/plugin.json` only, `name: scratchplug`) in the
  session scratchpad; from its directory, `claude --plugin-dir <worktree>/plugin-dev --model
  claude-sonnet-5-5 -p "/plugin-dev:fix-issues open"`. One run.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M6.1 `check-contracts`, first run | all PASS | 9/10: `README's skills table names every skill` FAILed, "listed but no such directory: open, recurred" — the note's verbatim README row backticks the two selection words | ❌ |
| M6.1 `check-contracts`, after the row was reworded | all PASS | 10/10; the issue-template claim 6 names across 3 readers, the report-template claim 10 names across 2 readers | ✅ |
| M6.1 `site/site.yml` | `- fix-issues` in `workflow_skills_order` | after `- audit-run` | ✅ |
| M6.1 README | a `fix-issues` row | after `audit-run`, "Fourteen skills" | ✅ |
| L6.1 load | answers the plugin has no `audits/` and stops | "The plugin is `scratchplug`, and it has no `audits/` directory, so it has no ledger yet. … There are no issues to fix, so I'm stopping here." Nothing written in the scratch plugin. (The CLI printed an unknown-model catalog warning for the full id; the run completed on it.) | ✅ |

## Verdict

Held. The first sweep caught the verbatim README row (backticked `open` and `recurred` read as
skill names); the row now writes them unquoted and the claim is unchanged — a Deviation in
note 06. `build-site` then wrote 56 pages with `fix-issues` under Workflow skills.
