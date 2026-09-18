# Evals

Ad hoc tests run against this plugin's own skills and agents — targeted checks of one
specific behavioral claim: does an agent actually invoke a skill when it should, does a
patched instruction change behavior, does a description trigger correctly.

The convention — file naming, the required "Tested against" commit and model fields, what
each section must contain, and the rule that a clean pass is recorded exactly like a failure
— is the `log-eval` skill in the `plugin-dev` plugin. Read it before adding an entry.

## Index

| Date | Subject | File | Commit | Verdict |
|---|---|---|---|---|
| 2026-09-18 | `plan-phases` / `run-phase` — plugin-dev's first `contracts.yml` (bare commands, README skills table, site.yml order): passes on the bundle, and every claim fails on a planted defect | [2026-09-18-phases-skills-contracts.md](2026-09-18-phases-skills-contracts.md) | uncommitted at test time | Held 6/6 — mechanical only; the skills' behavior is logged by the first real `run-phase` chat |
| 2026-09-17 | `forbid` exemptions — does a line pardoned by `unless` still catch a violation written on it | [2026-09-17-forbid-exemption-scope.md](2026-09-17-forbid-exemption-scope.md) | uncommitted at test time | **11 of 11 leaked before.** `near` scopes exemptions to the match; all 11 caught after, legitimate lines still silent. 3 of 8 exemptions deleted as redundant or dead (one pardoned nothing). One residual documented: a violation inside the window |
| 2026-09-17 | `build_site.py` — does a skill's reference file follow the skill that owns it, and does the `site_title` default stop underscoring a plugin's name | [2026-09-17-build-site-reference-placement.md](2026-09-17-build-site-reference-placement.md) | uncommitted at test time | Both fixed; full nav diff across both bundles is 3 lines in `dev-team` and 1 in `plugin-dev`, each accounted for |
| 2026-09-17 | `names_listed` gains `where` and `form` — does the three-file rule in `dev-team/CLAUDE.md` now enforce itself, and do the new filters stay quiet where they should | [2026-09-17-contract-sweep-names-listed-where-form.md](2026-09-17-contract-sweep-names-listed-where-form.md) | uncommitted at test time | 15 cases over two rounds; found D2/D3/D5 in `dev-team` on the first run. Round 2 found the command claim leaking through a line-level `unless` and both exemptions were removed; two checker fixes (empty `where` now FAILs, `list` form allows a trailing comment) |
| 2026-09-17 | `contract_sweep.py` — does each check kind actually fail when the claim is false | [2026-09-17-contract-sweep-negative.md](2026-09-17-contract-sweep-negative.md) | uncommitted at test time | All 4 planted defects caught, real bundle still 5/5; two lessons about exemption breadth written into the skill |
| 2026-09-17 | `build_site.py` — does a skill only a person can start (`disable-model-invocation: true`) land under Workflow skills, with nothing else in the site changing | [2026-09-17-build-site-workflow-classification.md](2026-09-17-build-site-workflow-classification.md) | uncommitted at test time | Held on every case; nav diff is the two skills moving and nothing else (strict mkdocs build not run — theme missing in the sandbox) |
| 2026-09-16 | `build_site.py` extraction — does the generic builder produce the same site as the dev-team original, and does a zero-config bundle still build | [2026-09-16-build-site-extraction.md](2026-09-16-build-site-extraction.md) | v0.1.0 | Held — `docs/` and nav byte-identical; one sandbox-delete bug found and fixed |
