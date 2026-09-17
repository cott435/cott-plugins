# Changelog

One entry per tagged release. The versioning policy — what triggers patch/minor/major, and
how model and eval versioning relate to it — is in the `plugin-dev` plugin's `bump-version`
skill. This repo's own decisions are in `VERSIONING.md`.


## [0.4.0] - 2026-09-17

### Added
- `names_listed` gains **`form`** — how the target list cites a name, so a list is checked where
  it lives rather than reformatted to suit the checker. `code` (backticks, the default) for
  prose and tables, `tree` for an indented `── name/` branch in a fenced directory tree where
  backticks would render literally, `list` for a YAML sequence or Markdown bullet.
- `names_listed` gains **`where`** — which directories the list answers for, read from their
  `SKILL.md` frontmatter. A list covering one class of skill is checked against that class, so a
  knowledge skill is not reported missing from a list of workflow steps and a second list of
  which skills count never has to exist. A `where` that matches nothing is a `FAIL`, not
  `0 names, all listed`: a typo would otherwise switch the claim off while still printing PASS.
- `skills/**/*.py` joins the default authored set. A script a plugin ships is authored too, and
  it is the one file that prints to a person rather than to a model — which is how `dev-team`'s
  `status.py` was found printing unnamespaced commands.

### Changed
- `check-contracts` documents both keys, with a table for `form`, and states the line-level
  `unless` hazard as a design rule rather than a formatting caveat: one exempt phrase pardons
  everything else on its line, and an exemption tends to live exactly where the thing it pardons
  is discussed. Prefer a negative lookahead in the pattern, which exempts a token.

### Fixed
- `form: list` anchored a bullet to end-of-line, so a YAML entry with a trailing comment read as
  missing. The checker was fixed rather than the comment removed: a claim that dictates how the
  file it checks may be annotated will be worked around.

Tested, 15 cases over two rounds —
`evals/2026-09-17-contract-sweep-names-listed-where-form.md`. Round 1 found `dev-team`'s D2, D3
and D5; round 2 exists because round 1 tested the command claim with a bare command alone on its
own line, which is not how one gets written, and so missed the `unless` leak above.

## [0.3.0] - 2026-09-17

### Added
- `check-contracts` + `scripts/contract_sweep.py` — checks the cross-file claims a bundle's own
  prompts act on, which nothing else in a plugin verifies: a heading one file parses against
  the template another owns, a rule one file states and another contradicts, a list of names
  that goes stale when a directory changes. Config-driven like the site builder: each bundle
  declares its claims in its own `contracts.yml`, absent means nothing is checked. Owner
  templates are parsed out of the owner file rather than restated, so renaming a heading moves
  the check with it. Exit 0 all pass, 1 any fail, 2 nothing declared.
- Verified against planted defects, one per check kind —
  `evals/2026-09-17-contract-sweep-negative.md`. Two lessons about writing claims (a broad
  `unless` becomes an escape hatch; the checks are line-based, so an exemption phrase must fit
  on one line) are written into the skill.

### Changed
- `CLAUDE.md` carries the shared-script rule for `contract_sweep.py` alongside the one for
  `build_site.py`: a change to it gets both runs — the real bundle, which must still pass, and
  a defective copy, which must still fail.

## [0.2.0] - 2026-09-17

### Changed
- `scripts/build_site.py` — a skill only a person can start
  (`disable-model-invocation: true`) is now a **Workflow skill**, not a Knowledge skill.
  A step that runs inline in the conversation rather than forking into an agent was being
  filed as material an agent reads, and its `workflow_skills_order` entry had no effect.
  `dev-team` rebuild: `status` and `shape-brief` moved into Workflow skills, 48 pages.
- `build-site` — the run command now has a fallback for sessions where the plugin is not
  installed (`CLAUDE_PLUGIN_ROOT` unset): `python3 ../plugin-dev/scripts/build_site.py`.

## [0.1.0] - 2026-09-16

### Added
- `build-site` skill and `scripts/build_site.py` — the generic site builder, extracted from
  `dev-team/site/build_site.py` and de-hardcoded. Verified byte-identical against
  `dev-team`'s existing site; see `evals/2026-09-16-build-site-extraction.md`.
- `bump-version` skill — the semver, CHANGELOG, tag and marketplace procedure, plus the
  `model:` field policy, extracted from `dev-team/VERSIONING.md`.
- `log-eval` skill — the eval record convention, extracted from `dev-team/evals/README.md`.
- `new-plugin` skill and `templates/` — scaffolds a plugin as a subdirectory of this repo.
