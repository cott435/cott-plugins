# Changelog

One entry per tagged release. The versioning policy — what triggers patch/minor/major, and
how model and eval versioning relate to it — is in the `plugin-dev` plugin's `bump-version`
skill. This repo's own decisions are in `VERSIONING.md`.

## [0.1.0] - 2026-09-16

### Added
- `build-site` skill and `scripts/build_site.py` — the generic site builder, extracted from
  `dev-team/site/build_site.py` and de-hardcoded. Verified byte-identical against
  `dev-team`'s existing site; see `evals/2026-09-16-build-site-extraction.md`.
- `bump-version` skill — the semver, CHANGELOG, tag and marketplace procedure, plus the
  `model:` field policy, extracted from `dev-team/VERSIONING.md`.
- `log-eval` skill — the eval record convention, extracted from `dev-team/evals/README.md`.
- `new-plugin` skill and `templates/` — scaffolds a plugin as a subdirectory of this repo.
