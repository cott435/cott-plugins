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
| 2026-09-17 | `build_site.py` — does a skill only a person can start (`disable-model-invocation: true`) land under Workflow skills, with nothing else in the site changing | [2026-09-17-build-site-workflow-classification.md](2026-09-17-build-site-workflow-classification.md) | uncommitted at test time | Held on every case; nav diff is the two skills moving and nothing else (strict mkdocs build not run — theme missing in the sandbox) |
| 2026-09-16 | `build_site.py` extraction — does the generic builder produce the same site as the dev-team original, and does a zero-config bundle still build | [2026-09-16-build-site-extraction.md](2026-09-16-build-site-extraction.md) | v0.1.0 | Held — `docs/` and nav byte-identical; one sandbox-delete bug found and fixed |
