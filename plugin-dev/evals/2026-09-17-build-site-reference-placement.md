# `build_site.py` — does a reference file follow its own skill, and does a plugin keep its name?

**Tested against:** uncommitted — both changes are new in this change, see the working-tree diff ·
model: none, the subject is a deterministic script · 2026-09-17

## What was tested

Two nav/title defects, both found while auditing `dev-team` rather than by using the builder:

1. **D4** — every skill's `references/*.md` was appended to the *Knowledge skills* section,
   whatever kind of skill owned it. So `shape-brief / brief` sat under Knowledge skills while
   `/dev-team:shape-brief` sat under Workflow skills, six entries away. The page was even written
   to `skills/workflow/` — only the nav entry was misfiled.
2. **The `site_title` default underscored the plugin's name** (`name.replace("-", "_")`), so
   `dev-team` rendered as `dev_team`. That is where the wrong spelling in `dev-team`'s README
   heading and site kept coming back from, which made it look like a bundle-local typo.

A nav change is only safe if it moves what it should and nothing else, so the test is a diff of
the generated `mkdocs.yml` for every bundle in the repo, before and against after.

## Method

Captured `site/mkdocs.yml` for both bundles — `dev-team` (7 agents, 21 skills, 8 reference files
across 3 skills) and `plugin-dev` (5 skills, no references) — rebuilt both, and diffed. No model
runs, no API cost. `dev-team` is the useful case: it has reference files under both a workflow
skill (`shape-brief`) and two knowledge skills (`planning-templates`, `python-style-guide`), so
one run tests the move and the non-move together.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `shape-brief / brief` | moves to Workflow skills, directly after `/dev-team:shape-brief` | moved, adjacent | ✅ |
| `planning-templates`' 5 references | stay under Knowledge skills, grouped with their skill | unchanged | ✅ |
| `python-style-guide`'s 3 references | stay under Knowledge skills, grouped with their skill | unchanged | ✅ |
| `dev-team` nav, everything else | no other line changes | only the move + the new LICENSE config page | ✅ |
| `dev-team` section counts | workflow 14 → 15, knowledge 16 → 15 | as expected | ✅ |
| `plugin-dev` nav | `site_name: plugin_dev` → `plugin-dev`, nothing else | one line | ✅ |
| `dev-team` `site_name` | stays `dev-team` with its explicit `site_title` removed | unchanged, so the default now produces it | ✅ |
| `check-contracts` on `dev-team` | 8/8, unaffected | 8/8 | ✅ |

The full `dev-team` nav diff is three lines: one insertion, one deletion, one addition from an
unrelated `config_files` entry in the same change.

## Verdict

**Both fixed, and the diff is the evidence that nothing else moved.** Two things worth keeping:

- **`dev-team` removing its explicit `site_title` is the real test of the default.** Patching the
  bundle would have hidden the builder bug from the only two bundles that could reveal it. The
  title is now produced by the corrected default, so the next plugin scaffolded gets its own name
  without knowing this was ever wrong.
- **A generated artifact needs a diff, not a rebuild.** The builder reports counts per section,
  and the counts alone would have been satisfied by a reference file moving into the *wrong*
  workflow skill. Adjacency is what was actually checked, and only the diff shows it.

**Not a behavioral eval.** The nav is read by people and by mkdocs, not by an agent. Whether the
grouping makes the site easier to read is a judgment this cannot settle.

**Re-run on any `build_site.py` change** — capture both bundles' `mkdocs.yml`, rebuild, diff, and
expect to justify every changed line. `plugin-dev/CLAUDE.md` carries the rule.
