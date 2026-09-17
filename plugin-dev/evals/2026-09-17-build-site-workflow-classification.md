# `build_site.py` — does a `disable-model-invocation` skill land under Workflow skills?

**Tested against:** uncommitted — see working-tree diff (`plugin-dev/scripts/build_site.py`, previously `259785a`) · model: n/a, deterministic script · 2026-09-17

## What was tested

The builder classified a skill as a workflow step only on `context: fork`. The claim: adding
`disable-model-invocation: true` as a second signal moves the skills a person runs — but which
run inline rather than forking into an agent — from **Knowledge skills** to **Workflow skills**,
puts them in the `workflow_skills_order` reading order, and changes nothing else about the site.

## Method

Real run of the builder against `dev-team`, which is the reference bundle the extraction was
verified against (`2026-09-16-build-site-extraction.md`). `site/docs/` and `site/mkdocs.yml`
were copied before the change, the builder was re-run after it, and both were diffed. No API
cost. `dev-team`'s own sources were unchanged between the two runs except for `shape-brief`,
which exists in both.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `status` (`disable-model-invocation: true`, no `context`) | moves to Workflow skills, titled `/dev-team:status` | moved, titled `/dev-team:status` | yes |
| `shape-brief` (same frontmatter) | moves to Workflow skills, honours its `workflow_skills_order` position (first) | moved, listed first | yes |
| `plan-repo` and the other 11 `context: fork` skills | unchanged | unchanged, same order | yes |
| `planning-templates`, `python-style-guide`, `security-review`, `workspace-scaffold` (no such frontmatter) | stay Knowledge skills | unchanged | yes |
| `shape-brief/references/brief.md` | stays a Knowledge nav entry | stayed under Knowledge skills (path moved to `skills/workflow/`, following its skill's kind) | yes |
| Agents, workflows, rules, home page | byte-identical | no diff | yes |

Counts: 45 pages / 12 workflow skills / 17 knowledge pages before → 48 / 14 / 15 after. The page
count rises by 3 because the sandbox could not clear `site/docs/`, so the three superseded
pages (`skills/knowledge/{shape-brief,shape-brief-brief,status}.md`) linger on disk; they are
not in the nav. Removing them needs a delete the sandbox was refused.

## Verdict

Held on every case. The nav diff is exactly the two skills moving and nothing else.
`mkdocs build --strict` was **not** run — `mkdocs-material` is not installed in the sandbox
that ran this — so the strict build is unverified, and the stale pages above would be reported
by it as files not in the nav until they are deleted.
