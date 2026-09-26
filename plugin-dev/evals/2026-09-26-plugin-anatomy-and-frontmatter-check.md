# `plugin-anatomy` added, and `contract_sweep.py` gains a `frontmatter` check that reads its key lists

**Tested against:** uncommitted — see working-tree diff on branch `design-plugin` (from `bdd8340`) · Claude Code 2.1.270 · model: `claude-opus-5-5` (session and `claude -p`) · 2026-09-26
**Set:** `evals/sets/plugin-anatomy.json` (behavioral 1–4, platform-fact 5–10) and `evals/sets/plugin-anatomy.trigger.json` — validated only, not run · **Iteration:** none · **Baseline:** n/a · **Pass rate:** n/a (mechanical and load)

## What was tested

That the new `frontmatter` check kind in the shared `scripts/contract_sweep.py` passes on
both bundles in the repo and fails on each defect it exists to catch, with its allowed keys
read from `plugin-anatomy`'s references rather than from the script; that the existing check
kinds still fail on a planted defect; that the new skill registers when the plugin loads; and
that the site and the new sets are well-formed.

## Method

- Facts in the references: a claude-code-guide subagent summarized the docs, then the skills,
  sub-agents, hooks, plugins-reference, plugins/components and plugin-evals pages were fetched
  directly. Where the two disagreed, the direct fetch won (the summary missed seven skill
  fields, including `hooks` and `argument-hint`; it had MCP tool names with `_` where the docs
  keep `-`; it omitted `initialPrompt` from the fields plugin agents ignore). Facts only in the
  summary are marked `[unconfirmed: from a docs summary, not re-read]`.
- Positive: `contract_sweep.py` on plugin-dev (7 claims, one new: skills' frontmatter), and on
  a temp copy of dev-team with an added `contracts.yml` declaring `frontmatter` for
  `agents/*.md` and `skills/*/SKILL.md`.
- Negative, each on a temp copy: (1) `allowed_tools:` added to a skill; (2) `hooks:` and
  `permissionMode:` added to dev-team's `designer` agent; (3) the `frontmatter-keys: skill`
  marker renamed in the reference; (4) a `files` glob matching nothing; (5) a bare
  `/plan-phases` appended to a skill, for the existing `forbid` kind.
- Load: `claude --plugin-dir <worktree>/plugin-dev -p "List every skill you have from the
  plugin-dev plugin…"` from a scratch project with the installed plugin-dev disabled.
- `eval_workspace.py validate` on both new sets; `build_site.py .`; `mkdocs build --strict`
  to a temp dir.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| plugin-dev sweep | 7/7 | 7/7 (first run 6/7: README did not list `plugin-anatomy`, then listed `frontmatter` as a phantom skill name; both fixed in the README) | ✅ |
| dev-team, agents and skills | PASS | 8 agents, 29 skills, every key documented | ✅ |
| (1) misspelled skill key | FAIL at file:line | `skills/plan-phases/SKILL.md:4 \`allowed_tools\` is not a documented skill field` | ✅ |
| (2) ignored agent keys | FAIL, both named | `agents/designer.md:10 \`hooks\` is ignored…; :11 \`permissionMode\` is ignored…` | ✅ |
| (3) reference block missing | FAIL, not a silent pass | `could not run: …/skills.md: no \`frontmatter-keys: skill\` block` | ✅ |
| (4) glob matches nothing | FAIL | `` `files: agents/*.md` matched no file `` | ✅ |
| (5) existing `forbid` kind | FAIL | `skills/plugin-anatomy/SKILL.md:91` | ✅ |
| Load | `plugin-anatomy` listed | listed with the other five model-invoked skills; the three typed skills absent, as `references/skills.md` predicts (their descriptions are not in context) | ✅ |
| `validate` on both sets | exit 0 | exit 0, exit 0 | ✅ |
| Site | builds, references under Knowledge skills | 17 knowledge pages incl. 8 `plugin-anatomy` references; strict build exit 0 | ✅ |

## Verdict

Held. The check is only as current as the references it reads: it now enforces the skill and
agent field lists as the docs stated them on 2026-09-26. Not yet run: the behavioral evals
(does the skill give the right routing answer when asked), the trigger set, and the six
platform facts (5–10) the references mark `[unconfirmed]`.
