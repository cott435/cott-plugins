# Changelog

Format: one entry per tagged release. The versioning policy — what triggers patch/minor/major,
and how model and eval versioning relate to it — is in the `plugin-dev` plugin's
`bump-version` skill. This repo's own decisions are in `VERSIONING.md`.

**Versions are the `0.x` line below, and nothing else.** This plugin had generations before
`0.1.0` — it was `project-workers` until `259785a`, and prose once referred to a "v3" and a
"v4" — but none of that is recorded here and none of it is a version this repo can resolve. So
those labels are not used to date anything: where an older artifact still has to be read, it is
described by what it looks like, not by the generation that produced it. The one surviving use
of the name is the **dev_team v4 Flow** artifact in the gallery, which is a title.



## [0.4.0] - 2026-09-18

Probing generalizes from "one external data API" to "one external source, of a kind".

### Breaking
- **Probe docs moved to `docs/sources/<source>.md`** from
  `docs/packages/<pkg>/sources/<source>.md`, and that document's **Credentials** heading is now
  **Access**. A repo planned under 0.3.2 has its probe docs at the old path under the old
  heading, so after upgrading `/dev-team:plan-package` finds none and re-probes every source —
  real requests against real quota — and the architect's stop check looks for a heading that is
  not there. No fallback read was added: a second path every reader has to know about is the
  duplication this change exists to remove. The fix in an existing repo is two commands' worth
  of work, once:

  ```
  git mv docs/packages/*/sources/* docs/sources/     # then remove the empty sources/ dirs
  sed -i '' 's/^## Credentials$/## Access/' docs/sources/*.md
  ```

  A `source` column written before this release still reads correctly: a bare token means
  `api`, which is what every such column held.

### Added
- **`dataset` is a probe kind.** `researcher`'s **Probe mode** now branches on a `Kind:` field:
  `api` keeps the existing procedure, widened; `dataset` is new — resolve and open the data,
  record its provenance claims, profile it with a re-runnable `<source>.profile.py`, and write
  columns, dtypes as loaded against dtypes declared, null rates, cardinalities, duplicates and
  candidate keys. When the purpose names a modeling task it also runs **task fit**: the target
  and the baseline any model must beat, the leaking columns, the usable features, and whether
  the rows admit a random split at all — then what the data can and cannot actually support.
  Ordered so each finding can invalidate the next, with leakage before features, because a
  leaking column is not a weak feature but a fake result.
- **Repo-scope dataset probing.** `/dev-team:plan-repo` gains step 2b: probe the datasets the
  brief names *before* the contract, because a target that cannot carry the task, or data that
  forbids a random split, decides which packages exist. Contradictions with the brief become
  interview questions in step 3 rather than assumptions. Only datasets — an api has no call
  worth making until a section's purpose exists.
- **Write-side API facts.** The `api` template gains **Write semantics** and **Webhooks**, and
  **Access** now records the auth *mechanism* — a static key or an OAuth2 grant with its token
  endpoint, lifetime and scopes — because a client that refreshes a token is a different client
  from one that sets a header.
- **A `contracts.yml` headings claim for the probe doc**, owned by `researcher.md` and cited by
  all four of its readers. The probe doc was the one document parsed by heading with no such
  claim behind it.

### Changed
- **Probe docs are repo-wide: `docs/sources/<source>.md`, not
  `docs/packages/<pkg>/sources/<source>.md`.** An external source belongs to no package, so two
  packages consuming one were probing it twice and could disagree about what it returned; and a
  dataset probed before any package exists had nowhere to live. Every reader moved with it —
  architect, designer, reviewer, implementer, `plan-package`, `plan-change`,
  `implement-section`, `review-section`, the package-contract template, `workspace-scaffold`'s
  mkdocs excludes, `README.md` and `flow.md`.
- **The Sections table's `source` column is `<kind>:<token>`**, comma-separated for a section
  consuming more than one. A bare token still means `api`, so contracts written before this
  read unchanged. A section could previously name only one source.
- **The credential stop is now the access stop**, and the heading it reads is **Access** in both
  templates rather than **Credentials**. One stop covers a key that is unset or rejected *and* a
  dataset that is missing or unreadable — the second of which previously had no stop at all.
- **A probe doc's authority is per heading.** A probe never sends a write, so write endpoints
  and webhooks are marked `documented` while read endpoints called are `observed` and a vendor
  sandbox is `sandbox`; the **Endpoints** table carries the marker. The designer treats a
  `documented` guarantee as an assumption to state, not a fact to build on. Without the
  distinction, widening to write-side APIs would have quietly diluted the one property that
  makes a probe doc worth reading.
- **`/dev-team:probe-source` takes `<pkg | repo> <source>`** and resolves `Kind:` from the
  argument's prefix, the contract, or `api`. Its artifacts differ by kind:
  `.sample.json`/`.probe.py` for an api, `.stats.json`/`.profile.py` for a dataset.
- **The probe doc templates moved out of `researcher.md`** into
  `skills/planning-templates/references/source-probe.md`, where the architect's five already
  live, and in the numbered-bolded form its siblings use. That form is not cosmetic:
  `check_headings` reads an owner template through `template_items()`, which matches only
  `N. **Name**`, so a template written as fenced `##` headings defines nothing a claim can be
  declared against — the claim failed on its own owner before the move, not on any reader
  (`evals/2026-09-18-probe-doc-headings-claim.md`). `researcher.md` drops from 377 to 284 lines
  and invokes `planning-templates` for the template, as the architect does; `planning-templates`
  is no longer an architect-only skill.
- **The repo contract records external sources.** `references/repo-contract.md` §5 now says to
  list each api's env var and each dataset's location — the field a probe's `Access:` is
  resolved from, which every caller already assumed was there and no template ever asked for.

### Security
- **A dataset probe writes statistics, never records.** There is no sample of real rows: example
  values are allowed only where the value is the statistic (numerics, categoricals under ~50
  distinct), free text and high-cardinality strings get shape and no contents, and any column
  that looks like a person is reduced to its null rate and cardinality and named under
  **Quirks**. The existing secret-scrubbing rule covered credentials in a response; it did not
  cover personal data in a file, and a record copied into `docs/` is in the repo's history for
  good.
- **Probes never mutate.** No POST, PUT, PATCH or DELETE against a live account, whatever the
  documentation calls reversible — the probe is holding the user's real credential. The
  implementer's own fallback probe inherits the rule.

## [0.3.2] - 2026-09-17

Passes 3 and 4 of the 2026-09-17 audit: the documents people read, and the site. No prompt an
agent loads changes. `flow.md` changes, and no agent reads it.

### Fixed
- **`README.md` annotated the architect `(opus)`.** It sets `model: inherit`; `VERSIONING.md`
  records `opus` as a candidate that is not applied.
- **"The `AskUserQuestion` widget is gone" was true of subagents only.** It is removed from every
  subagent whatever its `tools:` field says — which is why the architect writes decision stubs
  instead of asking — but it is there in the main conversation, where
  `/dev-team:shape-brief` uses it at four questions per call. The README says which is which.
- **"Three conventions … marked *Project convention*" listed four.** The style guide marks three:
  docstrings, function shape, `__init__.py`. CLI commands in `src/<pkg>/cli.py` with no
  `scripts/` is `project-structure` §1's rule and now stands in its own paragraph saying so.
- **`plugin.json`'s description was "Project planning skills and agents"** — the string `/plugin`
  shows — while the `marketplace.json` row said what the plugin does. They match now.
  `README.md`'s heading is `# dev-team`, and the site's H1 follows the plugin name.
- **`CLAUDE.md` pointed at an "untagged `1.1.0` loose end"** that `VERSIONING.md` never held. It
  now says what that file holds: the `model:` decisions, and nothing else.
- **The 2026-09-16 eval credited the eval convention to `VERSIONING.md`** in two places; it is
  `plugin-dev`'s `log-eval`.
- **The Workflows section promised one page per pipeline and listed four of five.**
  `add-package.md` was missing, though it was already in `site.yml` and the nav.
- **The Contents tree omitted `CHANGELOG.md` and `skills/status/scripts/status.py`**, the only
  executable here.
- **`flow.md` credited `docs/packages/<pkg>/assessment.md` to "plan-package, map-project".**
  `map-project` writes the four repo-level documents and is explicitly told not to write package
  documents; `docs/assessment.md` is its row, one line up.
- **`flow.md`'s `docs/` map omitted three things** — `docs/legacy/inventory.md`, the probe docs
  (`docs/packages/<pkg>/sources/<source>.md` with their sample and probe script), and the
  package-level review file. The probe docs are the omission that mattered: a designer reading
  the map would not have known the one document describing an external system as it actually
  answered. The two review rows now also name `finalize-package`, which gates on their dates.
- **`skills/python-style-guide/LICENSE` was not on the reading site.** That skill's frontmatter
  says "Complete terms in LICENSE" for CC BY 3.0 attribution to Google's guide, and a pointer to
  a file the reader cannot open is not attribution. Added to `config_files`.

### Changed
- Both `forbid` claims in `contracts.yml` set `near: 40`, scoping their exemptions to the match
  rather than the line, and the `scripts/` claim drops three of its eight exemptions: two
  redundant with the prohibition sentence they sat beside, and one (`.probe.py`) that pardoned
  nothing at all. Line-scoped, those eight had left ten lines unprotected — every line in the
  bundle where `scripts/` is discussed. Needs `plugin-dev` 0.5.0.
- The `v3` / `v4` labels are no longer used to date anything, because this repo cannot resolve
  them: `0.1.0` is the initial release under `cott-plugins`, the plugin was `project-workers`
  until `259785a`, and nothing earlier is recorded. `CHANGELOG.md` says exactly that, once. The
  two places that needed the labels describe the artifact instead — an older `decisions.md`
  "predating `0.1.0`", and **dev_team v4 Flow** as the title of a gallery artifact.
- `site/README.md` says what `--evals` actually renders (a JSON of eval *definitions*) and that
  the `evals/` directory is deliberately not on the site: dated records, read in the repo beside
  the commit they name, turning over faster than the prompts the site mirrors.

## [0.3.1] - 2026-09-17

Passes 1 and 2 of the 2026-09-17 audit. Every prompt change here removes a second statement of
something already stated elsewhere, or corrects a rule that contradicted another file. No
document path, format, frontmatter shape or invoked command changed.

### Fixed
- **Two probe-skip rules for the same agent.** `architect.md`'s **Probing** said skip a probe
  doc dated today *and* valid; `plan-change` told the same architect a valid doc is never
  re-probed however old. Probing now states the change-scope relaxation as its own paragraph,
  with the reason it is deliberate, and `plan-change` step 6b states neither rule — it points at
  Probing and at its own wave B, which handles a valid doc older than the code.
- **The curator's read boundary forbade three checks `extract-legacy` requires.** "Read only
  `docs/brief.md`" ruled out testing whether `docs/architecture.md` exists, and "never read
  `.claude/skills/`" read as ruling out testing whether a skill directory does. The hard rule
  now says existence checks are fine and content is not, naming both paths.
- **The finalize-package preconditions, four copies down to two.** `implementer.md` Surface mode
  defines them and `status.py --gate` computes them; `finalize-package` runs the gate and
  restates nothing, and the README gotcha states the no-partial-mode rule rather than the list.
- **The probe prompt claimed to be defined in a file that defines none of it.** `researcher.md`'s
  **Probe mode** is now named as the definition of the five fields; `architect.md` and
  `probe-source` each keep only their own resolution rules, which differ and are not duplicates.
- **`review-section`'s Paths table omitted `docs/followups.md`**, which the run reads — the
  reviewer skips findings already listed — and appends to in step 4. `review-package` listed it.
- **Commands nobody could type.** `site/flow.md`'s three diagrams and prose (21 occurrences) and
  `status.py`'s two user-facing messages printed bare `/plan-package`-style names; plugin skills
  are always namespaced. All prefixed, and now held by a `contracts.yml` claim.
- **`site.yml`'s `workflow_skills_order` omitted `status`**, leaving it to the alphabetical tail
  of a list whose only purpose is run order.

### Changed
- `contracts.yml` declares 8 claims, up from 5, and `CLAUDE.md`'s three-file rule now *is* three
  of them rather than a reminder to remember it. Corrects 0.3.0's note that `check-contracts`
  "cannot see the other two": with `plugin-dev` 0.4.0 it sees all three, in both directions —
  a skill missing from a list, and a name in a list with no such skill.
- The new command claim carries no exemptions. `/reload-plugins` is a negative lookahead in the
  pattern rather than an `unless`, because `unless` matches a whole line and that command
  appears in all 14 guard blocks; and the one sentence in `reserved-skill-names` that needed the
  other exemption now names "the project's own unprefixed `plan-repo` command" rather than
  writing it as a command.

## [0.3.0] - 2026-09-17

### Added
- `reserved-skill-names` — a knowledge skill holding the one copy of the names this plugin's
  own skills occupy, with what each reader does with them. The architect invokes it to know
  which `.claude/skills/` entries to skip; `/dev-team:extract-legacy` reads it (the curator has
  no `Skill` tool, so the skill passes it the path) to refuse a row that would overwrite a
  plugin skill. Both previously carried their own copy of a 20-name list.
- `contracts.yml` — the cross-file claims this bundle's prompts act on, checked by
  `plugin-dev`'s `check-contracts`: the `scripts/` prohibition, the `docs/api/<pkg>.md` writer,
  the `interface.md` and section-README heading contracts, and that every shipped skill is
  named in `reserved-skill-names`.

### Changed
- `CLAUDE.md` states what a new skill must be added to, in the same change:
  `reserved-skill-names`, `README.md`'s Contents tree and knowledge-scope table, and
  `site/site.yml`'s `workflow_skills_order` for a workflow skill. `check-contracts` enforces
  the first mechanically and cannot see the other two.

## [0.2.2] - 2026-09-17

### Changed
- A CLI command may run a **single section entry point**, not only a pipeline. `surface.md`
  §3's column is now "what it runs" and names the one-off command — schema init, a backfill, a
  cache rebuild — as the case: it has no row under **Pipelines**, and that is not a gap. The
  implementer's surface-mode step 3 and `project-structure` §1 say the same, and the package
  contract's **Public surface (intent)** takes such a command as a consumer. `interface.md`
  already had the looser column, so a command can now ship in the shape it was planned.
- `project-structure` §1 says what to do before the surface exists: there is no `cli.py` until
  `/dev-team:finalize-package` runs, so call the section's function directly and let the
  command arrive with the surface.

### Fixed
- Four v3 mentions of "scripts" where the plugin means `cli.py`: `/dev-team:finalize-package`'s
  description and its "Why this is a separate step" paragraph, and two `site/flow.md` diagram
  nodes. `project-structure` §1 forbids a `scripts/` directory outright, so these contradicted
  it.
- `docs/api/<pkg>.md` was credited to `/dev-team:finalize-project` in `README.md`'s `docs/`
  layout and in `site/flow.md`'s map. The implementer writes it in surface mode as each package
  ships; `finalize-project` regenerates `index.md` and fills gaps.
- Both fixes verified by a mechanical before/after sweep over the bundle —
  `evals/2026-09-17-cross-file-contract-sweep.md`, which also confirms the 0.2.1 documenter
  heading fix holds under a check that does not share its assumptions.

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
