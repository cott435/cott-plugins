# Changelog

Format: one entry per tagged release. The versioning policy — what triggers patch/minor/major,
and how model and eval versioning relate to it — is in the `plugin-dev` plugin's
`bump-version` skill. This repo's own decisions are in `VERSIONING.md`.

## [0.1.0] - 2026-09-16

Initial release under `cott-plugins`.

- Seven agents (architect, designer, implementer, reviewer, documenter, curator, researcher)
  and their skills, planning a repo of packages section by section through file-based
  contracts.
- `implementer`'s Security step invokes `security-review` on matching sections rather than
  writing a security paragraph from memory — see
  `evals/2026-09-16-implementer-security-review-trigger.md`.
- Skill extraction and external source probing (`researcher` extract/probe modes,
  `/dev-team:probe-source`).
