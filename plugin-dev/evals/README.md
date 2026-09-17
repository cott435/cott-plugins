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
| 2026-09-16 | `build_site.py` extraction — does the generic builder produce the same site as the dev-team original, and does a zero-config bundle still build | [2026-09-16-build-site-extraction.md](2026-09-16-build-site-extraction.md) | v0.1.0 | Held — `docs/` and nav byte-identical; one sandbox-delete bug found and fixed |
