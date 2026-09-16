# build_site.py extraction — does the generic builder produce the same site?

**Tested against:** `scripts/build_site.py`, as shipped in the `v0.1.0` initial commit of
this repo · source it was extracted from: `project-workers/site/build_site.py`, since
removed (superseded by this file) · model: `claude-opus-5` · 2026-09-16

## What was tested

The claim that pulling the site builder out of `project-workers` and de-hardcoding it (plugin
name, command prefix, workflow ordering, rules and config files → `site/site.yml`) is a pure
refactor: the same bundle must produce the same site, byte for byte, not merely a site that
looks right.

Second claim, weaker: a plugin with no `site/` directory at all must still build, so a new
plugin needs no site config to be readable.

## Method

Both claims tested by running the scripts, not by reading them. The repo was copied to a
scratch directory first so nothing in `~/dev` depended on the outcome.

1. Ran the original `project-workers/site/build_site.py` on a copy of `project-workers`.
   Moved its `site/docs/` and `site/mkdocs.yml` aside.
2. Wrote `site/site.yml` carrying the two ordering lists and the one config file that the
   original had as module-level constants.
3. Ran the extracted `scripts/build_site.py` on the same copy.
4. `diff -r` on the two `docs/` trees and `diff` on the two `mkdocs.yml` files.
5. For the zero-config claim: ran the extracted script against a copy of a second, unrelated
   plugin bundle (8 agents, 8 skills, no `site/` directory, no `site.yml`,
   no `mkdocs-base.yml`).

No API cost — both are local Python scripts.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 43 generated pages, `docs/` tree | identical | `diff -r` clean | ✅ |
| generated nav in `mkdocs.yml` | identical | `diff` clean | ✅ |
| section counts | 7 agents, 5 workflows, 12 workflow skills, 15 knowledge, 2 rules/config | as expected | ✅ |
| zero-config bundle | builds; nav omits empty sections; `site_name` from `plugin.json` | 17 pages, nav had Home + Agents + Knowledge skills only, `site_name: elisa_rd_agents` | ✅ |

## Verdict

Held. The extraction is behavior-preserving for the reference bundle and degrades correctly
for a bundle with no site config.

One defect found and fixed during the run, unrelated to the extraction itself: the original
`shutil.rmtree(docs)` raises `PermissionError` when the repo is mounted in a sandbox that
forbids deletes, which aborted the whole build. The extracted version catches it, warns that
pages for deleted sources may be stale, and rebuilds in place. Re-run confirmed the build
completes under that mount.

Not covered: `mkdocs serve` was not run, so this says nothing about whether the generated
nav renders — only that it is the same nav the reference site already used.
