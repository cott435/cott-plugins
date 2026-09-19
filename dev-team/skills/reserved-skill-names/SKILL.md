---
name: reserved-skill-names
description: The names this plugin's own skills occupy — the one list of them. The architect ignores these when enumerating a project's skills; extract-legacy refuses to write one over a plugin skill. Read it instead of carrying a copy of the list.
user-invocable: false
---

# Reserved skill names

Every skill `dev-team` ships. A project skill in `.claude/skills/` may not take one of these
names, and nothing in a project's own conventions is expressed by one: they are this plugin's
machinery.

This file is the only copy of the list. Two readers need it and reach it differently — the
architect invokes this skill with the `Skill` tool; the curator has no `Skill` tool, so
`/dev-team:extract-legacy` passes it the path and it reads this file. Anything else that needs
the list does the same. Do not paste the names into another file.

## Workflow skills — the ones a person types

`shape-brief` · `set-constraints` · `plan-repo` · `plan-package` · `review-plan` · `plan-change` · `map-project` ·
`test-section` · `implement-section` · `review-section` · `finalize-package` · `review-package` · `sync-plan` ·
`sync-design` · `run-package` · `finalize-project` · `extract-legacy` · `probe-source` · `status`

## Knowledge skills — preloaded, or invoked on their own triggers

`project-structure` · `python-implementation` · `python-style-guide` · `security-review` ·
`workspace-scaffold` · `planning-templates` · `reserved-skill-names` ·
`test-driven-development` · `debugging-and-error-recovery` · `git-workflow-and-versioning`

## What each reader does with it

- **The architect**, enumerating `.claude/skills/` to assign project skills to packages and
  sections: every name above is skipped. None of them needs a section assignment — they are
  preloaded into agents, invoked on their own triggers, or are the workflow skills that invoke
  the architect in the first place. What is left is the project's own skills.
- **`/dev-team:extract-legacy`**, before extracting: an inventory row whose `skill` is one of
  these names is `failed: name reserved` and is never extracted. Writing
  `.claude/skills/plan-repo/` would shadow nothing — plugin skills are namespaced
  `/dev-team:plan-repo` — but it would collide with the project's own unprefixed `plan-repo`
  command and confuse every later enumeration.

## Keeping it current

**A skill added to this plugin is added here, in the same change.** This list is not derived
at run time: the architect cannot tell a plugin skill from a project skill by looking, because
by the time it enumerates `.claude/skills/` both are just directories. A missing name means
the architect tries to assign this plugin's own machinery to a section, and `extract-legacy`
lets a researcher overwrite it.

Three other places name the skills and go stale the same way, so the full set for adding a
skill is:

1. this file;
2. `README.md`'s **Contents** tree — one line, in the right group;
3. `site/site.yml`'s `workflow_skills_order`, for a workflow skill — an unlisted one falls to
   the alphabetical tail of the reading site's nav rather than sitting in run order.

`plugin-dev`'s `check-contracts` enforces item 1: it fails when a directory under `skills/`
has no name in this file. It cannot check the other two, so they are on you.
