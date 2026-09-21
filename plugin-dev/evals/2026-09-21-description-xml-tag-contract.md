# `check-contracts` — the description-tag forbid catches what claude.ai rejects, and can fail

**Tested against:** `91dcf5c` (`contracts.yml`, `../dev-team/contracts.yml`, `scripts/contract_sweep.py`) · model: `claude-opus-5` · 2026-09-21
**Set:** none — ad hoc probe of a new contract

## What was tested

The desktop app stopped listing plugin-dev because claude.ai rejected it with "SKILL.md
description cannot contain XML tags" (`skills/run-evals`), a check the CLI doesn't make. The
claim: the new forbid `no skill or agent description contains an XML-style tag`
(`^description:.*<[A-Za-z/]` over `agents/*.md` and `skills/*/SKILL.md`) passes on the fixed
bundles and fails when a tag is put back.

## Method

`contract_sweep.py` on plugin-dev and dev-team at `91dcf5c`, then one planted defect:
`<skill>` restored to line 3 of `skills/run-evals/SKILL.md`, swept, reverted. Local runs, no
API cost.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| plugin-dev, fixed | all pass | 5/5 | ✓ |
| dev-team, fixed | all pass | 25/25 | ✓ |
| `<skill>` planted in run-evals' description | FAIL at that line | `FAIL … skills/run-evals/SKILL.md:3` | ✓ |
| dev-team before the exemption | — | FAIL at `agents/researcher.md:83`: the project-skill template in the agent's body, not its frontmatter | exempted with `unless` |

## Verdict

Held. The pattern is line-based, so it also matches a `description:` line in a fenced
template in a file's body. dev-team's one such line is exempted by name. The companion claude.ai
rule, one `plugin.json` per plugin folder, is about which files exist rather than what they
contain, so `contract_sweep.py` can't express it. It was fixed by renaming the fixture's
manifest to `plugin.json.fixture`, and nothing checks it.
