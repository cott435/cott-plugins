# Changelog

Format: one entry per tagged release. The versioning policy — what triggers patch/minor/major,
and how model and eval versioning relate to it — is in the `plugin-dev` plugin's
`bump-version` skill. This repo's own decisions are in `VERSIONING.md`.

## [0.2.1] - 2026-09-17

### Fixed
- `documenter` read `interface.md` by two headings the implementer never writes: `Scripts`
  (heading 3 is **CLI commands**) and `Consumers` (it is **Consumers (computed)**). The
  paragraph no longer restates that template — it names the six headings the documenter
  consumes, spelled as the owner writes them, and makes a heading it cannot find a
  **Known gaps** entry rather than something to substitute a similar heading for. Checked
  mechanically in `evals/2026-09-17-documenter-interface-heading-contract.md`; the behavioral
  impact on a real run is recorded there as unverified.
- `/dev-team:finalize-package` ran `status.py <pkg>` without `--gate`, so it got the section
  table rather than its own preconditions as `PASS`/`FAIL`. It now runs the gate, and the
  skill says the non-zero exit is the gate reporting — the `FAIL` lines are the blocker to
  return.

### Removed
- `rules/python-standards.md`. A plugin has no `rules/` component — Claude Code loads
  path-scoped rules only from `.claude/rules/` or `~/.claude/rules/` — so this one never
  loaded on an installed plugin. The conventions it pointed at already reach the agents
  through their `skills:` frontmatter; `README.md` now says how to write one in the repo you
  are building if you want it for interactive work.

## [0.2.0] - 2026-09-17

### Added
- `/dev-team:shape-brief` — new skill, runs in the main conversation so it can ask: turns a
  rough idea into `docs/brief.md` by mapping the domain, narrowing it with the user to
  now / later / out, and recording constraints, success criteria and open questions. Also
  corrects an existing brief, or appends scope to one.
- `/dev-team:plan-repo` **Revise** mode — a corrected brief, or `--revise "<notes>"`: archives
  and rewrites the repo contract, retires open decisions whose premise is gone, turns a decided
  one that now conflicts into a question, and lists stale package plans. Mode is decided by how
  the brief changed against the new `docs/history/brief-contracted.md` snapshot, not only by
  whether the contract exists.
- Repo contract Packages table gains a `covers` column mapping brief capabilities to packages.
  `/dev-team:plan-package` reads only its covered brief rows and quotes their Notes into the
  package contract's **Purpose**, so the user's own wording reaches designers.

### Changed
- Built-but-unshipped packages are treated as bound (frozen) at repo scope, like shipped ones.
- `docs/assessment.md` is written by `plan-repo` only when there is something to survey.
- A `superseded` decision no longer counts as already asked, so a retired question can be
  raised again.
- Site workflow pages cover the new flow: new-repo (shape the brief, and correcting a wrong
  contract), add-package, rebuild-from-legacy (shape the brief before mining),
  adopt-existing-repo (new scope on a mapped repo), change-shipped-code (recording scope
  changes in the brief). `docs/packages/<pkg>/brief.md` is gone from the flow page — there is
  no per-package brief.
- `dev-team/CLAUDE.md` records that the shared protocol lives in the parent repo, that git runs
  from there, and how to rebuild the site without `plugin-dev` installed.

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
