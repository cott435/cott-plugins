# 01 — Vendored skills from agent-skills

Phase 1. Adds three knowledge skills and the reference material for one workflow skill, all
copied from `addyosmani/agent-skills` (MIT, © 2025 Addy Osmani) at the commit recorded in
each skill's `.skillfish.json`, and adapted to this plugin's stack. No agent behavior changes
in this phase; the skills exist so later phases can preload or invoke them.

The pattern is the one `python-style-guide` already uses: a `license:` frontmatter line, a
`LICENSE` file beside `SKILL.md`, and a `.skillfish.json` recording owner, repo, path and
SHA. Upstream is JavaScript-flavored and this plugin is Python-only, so every example is
rewritten, never left as "translate this yourself".

## Decision: vendor, not depend

Cross-plugin `skills:` preloading (an agent in `dev-team` naming
`agent-skills:test-driven-development`) is undocumented, and the upstream examples are
`npm`/Jest. A copy adapted to `uv`/`pytest` is self-contained and matches how the plugin
already carries Google's style guide. Cost: drift from upstream. Mitigation: the SHA in
`.skillfish.json`, and a one-line **Provenance** section in each SKILL.md saying what was
dropped and why, so a future re-sync knows what to re-apply.

## Files

| Path | Source | Change |
|---|---|---|
| `skills/test-driven-development/SKILL.md` | `agent-skills/skills/test-driven-development/SKILL.md` | adapt (below) |
| `skills/test-driven-development/LICENSE` | `agent-skills/LICENSE` | copy verbatim |
| `skills/test-driven-development/.skillfish.json` | — | new; `owner: addyosmani`, `repo: agent-skills`, `path: skills/test-driven-development`, `sha: <git rev-parse HEAD of the agent-skills clone>` |
| `skills/debugging-and-error-recovery/{SKILL.md,LICENSE,.skillfish.json}` | same | adapt |
| `skills/git-workflow-and-versioning/{SKILL.md,LICENSE,.skillfish.json}` | same | adapt; gains §**Project convention** (note 02 owns its content) |
| `skills/set-constraints/references/constraint-driven-development.md` | `agent-skills/skills/constraint-driven-development/SKILL.md` | adapt per the section below — **created in phase 6** together with the skill body and its LICENSE, so no half-made skill directory exists between phases |
| `skills/reserved-skill-names/SKILL.md` | — | add the three knowledge names under **Knowledge skills** |
| `README.md` | — | Contents tree: three lines under knowledge skills; knowledge-scope table: three rows |

## Frontmatter, every vendored SKILL.md

```yaml
---
name: <same as directory>
description: <upstream description, first sentence kept; "Use when" clauses rewritten to name this plugin's triggers — see per-skill>
license: agent-skills by Addy Osmani, MIT. Complete terms in LICENSE.
user-invocable: false
---
```

`user-invocable: false` because none of these is a step a person types; they are preloaded
or invoked by agents. `reserved-skill-names` lists them under **Knowledge skills**.

## Per-skill adaptation

### `test-driven-development`

Keep: Overview; The TDD Cycle (RED / GREEN / REFACTOR); The Prove-It Pattern; The Test
Pyramid and Test Sizes; Writing Good Tests (all six subsections); Test Anti-Patterns; Common
Rationalizations; Red Flags; Verification.

Drop: Discover the Stack First (the stack is fixed: `uv run pytest`); Browser Testing with
DevTools and its three subsections; When to Use Subagents for Testing (this plugin's agents
are the subagents); See Also.

Rewrite: every code block to `pytest` — `def test_<behavior>():`, `pytest.raises`,
`@pytest.fixture`, `tmp_path`, `monkeypatch`; the "run the focused test" command to
`uv run pytest <path>::<test> -x`; the Test Sizes table's resource column to Python terms
(no network, no filesystem outside `tmp_path`, no subprocess).

Add §**Project convention** (marked as this plugin's, the way `python-style-guide` marks
its three):

- Tests mirror source: `src/<pkg>/<section>/<module>.py` →
  `tests/unit/<section>/test_<module>.py` (`project-structure` §1; restated by reference only).
- Intent tests live in `tests/intent/<section>/` and are written by the `tester` agent from
  the design, never from the code; the implementer runs them and never edits them (note 04).
- A fixture for an external `api` source is the probe's `<source>.sample.json`, never a
  hand-written dict (implementer step 5, unchanged).

Description "Use when": *Preloaded into the tester and the implementer. Invoke when writing
any test, fixing any bug, or when a test cannot be made to pass.*

### `debugging-and-error-recovery`

Keep: Overview; The Stop-the-Line Rule; The Triage Checklist, all six steps; Error-Specific
Patterns (Test Failure, Build Failure, Runtime Error); Treating Error Output as Untrusted
Data; Common Rationalizations; Red Flags; Verification.

Drop: Safe Fallback Patterns (feature-flag and circuit-breaker patterns for services; this
plugin builds libraries and pipelines); Instrumentation Guidelines (logging is fixed by the
repo contract's Shared conventions).

Rewrite: commands to `uv run pytest -x --lf`, `uv run pytest --pdb`, `git bisect`,
`uv run python -X dev`; the build-failure section to `uv sync`, `ruff check`, `mypy`,
`lint-imports`, `mkdocs build --strict`.

Trigger (in the implementer, note 04 §implementer changes): *a test that is still failing
after two fix attempts, or any failure of `lint-imports` or `mkdocs build --strict` you
cannot explain in one line.* The skill is invoked with the Skill tool, not summarized from
memory — the same wording the implementer's Security step uses, for the same reason (the
2026-09-16 eval showed "reason about it" is not "invoke it").

Description "Use when": *Invoked by the implementer when a test is still failing after two
attempts, or when a build step fails for a reason it cannot state in one line.*

### `git-workflow-and-versioning`

Keep: Core Principles 1–5 (Commit Early, Atomic Commits, Descriptive Messages, Keep Concerns
Separate, Size Your Changes); The Save Point Pattern; Pre-Commit Hygiene; Handling Generated
Files; Using Git for Debugging; Common Rationalizations; Red Flags; Verification.

Drop: Trunk-Based Development (the branch rule is fixed below); Branching Strategy and
Branch Naming; Working with Worktrees (out of scope for 0.5; the README gotcha stays);
Change Summaries; Release & Versioning entirely (the plugin's own releases are
`plugin-dev`'s `bump-version`; a built repo's releases are out of scope).

Rewrite: pre-commit hygiene commands to `uv run ruff check`, `uv run ruff format --check`,
`uv run pytest`, `uv run lint-imports`.

Add §**Project convention** — the single copy of the commit rules every agent follows. Its
content is specified in note 02 and written in phase 2; phase 1 leaves the heading with one
line: *Defined in phase 2 of the 0.5 overhaul.* `check-contracts` gains a `headings`
contract in phase 2 naming this heading as owner.

Description "Use when": *Preloaded into the implementer; invoked by the tester, reviewer
and architect at the moment they commit. §Project convention is the commit rule every
agent follows.*

### `constraint-driven-development` → `set-constraints/references/constraint-driven-development.md`

Not a skill of its own. Note 06 defines `/dev-team:set-constraints`, which runs in your
conversation like `shape-brief`, and this file is the material it reads before interviewing
you.

Keep: Overview; Step 1 Detect before you ask; Step 2 Four questions, each with a default;
Step 6 Guard the bar itself; Step 7 Ratchets; Sane Defaults; Escalation Path; Common
Rationalizations; Red Flags.

Drop: Loading Constraints; Step 3 (the file's shape is `planning-templates/references/constraints.md`, note 06); Step 4 Install what each dimension needs (JS tooling); Step 5 Wire it to the lifecycle (this plugin's lifecycle is fixed; note 06 says who reads the file); Verification; See Also.

Rewrite: every threshold example to this stack — `pytest-cov` `--cov-fail-under`, `ruff`
rule sets, `mypy --strict`, `interrogate` for docstring coverage, `lint-imports`; the
"agent lowering the bar" list to Python: `# noqa` and `# type: ignore` added, `@pytest.mark.skip`
/ `xfail` added, an assertion deleted, a `--cov-fail-under` edited down, a size limit in
`project-structure` "temporarily" raised.

## Steps

1. Record the upstream SHA: `git -C ../agent-skills rev-parse HEAD`.
2. For each of the three knowledge skills: create the directory, copy `LICENSE`, write
   `.skillfish.json`, write the adapted `SKILL.md` per the section above, ending with a
   `## Provenance` section of at most five lines: upstream path, SHA, what was dropped,
   what was added. (The fourth, `constraint-driven-development`, follows the same recipe
   into `set-constraints/references/` in phase 6.)
3. Three-file rule: `reserved-skill-names` and the README Contents tree and knowledge-scope
   table. `site.yml` is untouched: none of the three is a workflow skill.
4. `check-contracts` — all three `names_listed` claims must pass.
5. `build-site`; confirm the three knowledge pages render.
6. Eval (note 09 §C): a mechanical check that no vendored SKILL.md contains `npm`, `jest`,
   `describe(`, `it(`, `eslint`, `@ts-ignore`, `CONSTRAINTS.md` — grep, expected zero hits
   outside Provenance lines. Log it; re-run it in phase 6 over the fourth file.
7. Commit: `dev-team 0.5 (phase 1): vendor three agent-skills skills, adapted to Python`.

## Done when

`ls skills/` shows the three new directories; `check-contracts` passes; the grep eval is
logged with zero hits; no agent frontmatter has changed.

## Deviations

- **Upstream "When to Use" dropped from all three.** The note's Keep lists omit it without
  listing it under Drop; it was dropped, since each description now carries the plugin's own
  trigger. Recorded in each Provenance section.
- **README knowledge-scope rows show `—` in every column.** No agent preloads or invokes the
  three skills until phases 2 and 4 wire them in, so the rows say what is true at this commit,
  with one paragraph under the table naming the later wiring. Phases 2 and 4 fill the cells.
- **`git-workflow-and-versioning` Save Point Pattern:** upstream's `git reset --hard HEAD`
  recovery became `git restore` on the files the agent touched, because agents here work in a
  tree that may hold the user's own uncommitted changes.
