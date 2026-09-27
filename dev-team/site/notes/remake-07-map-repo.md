# 07 — map-repo

Phase 07. Adds `/dev-team:map-repo [scope]`, the one command that adopts an existing repo:
phase 1 the architect lists the packages with `Explore` (on a monolith it proposes the split as
one `D<n>` per boundary and stops); phase 2 one `dev-team:architect` per package, all in one
message, each writing that package's contract from its code, treating every existing contract
line as a claim to check; phase 3 the same forked architect writes `docs/architecture.md` from
the N contracts and the import graph. Defects seen while mapping go to `docs/followups.md` (the
backlog). `map-project` is deleted. The gap it closes: adoption was one repo-level run plus N
typed document-mode `plan-package` runs, and a monolith's split was invented silently.

## Decisions

- **Phase 1's package list travels in the phase-2 prompts**, not in a file; a re-run
  recomputes it. Reason: the design's `assessment.md` decision.
- **The phase-2 spawn block** the architect sends to each package architect:

  ```
  Scope: package (map-repo phase 2)
  Package: <name>
  Path: <directory>
  Existing contract: docs/packages/<pkg>/contract.md | none
  Sibling packages: <name: path, …>
  Import graph: <the lint-imports output, or the grep lines for this package>
  Write to: docs/packages/<pkg>/contract.md
  Run: map-repo <scope>
  ```

  Each package architect writes its contract from `package-contract.md` in as-is wording,
  files defects to `docs/followups.md` as `- [ ] <pkg>/<section>: <what> — architect <date>`,
  reports each correction to an existing line as *stale doc corrected* or *code looks wrong,
  filed*, commits its contract only (scope `plan <pkg>`), and returns ten lines.
- **The monolith test:** phase 1 finds packages when `packages/*/pyproject.toml` exist, or the
  Packages table of an existing `docs/architecture.md` names them, or a `D<n>` tagged
  `/dev-team:map-repo (interview)` is `decided` for the split. Otherwise it stubs one `D<n>` per
  proposed boundary with the directories each would own and stops with the interview message.
  A re-run with the stubs still `open` proceeds on their assumptions.
- **The import graph** is `uv run lint-imports` output when `[tool.importlinter]` is
  configured, else `grep -rn "^from \|^import " <path>` filtered to the other packages' names,
  read-only.
- **Batching:** more than 20 packages are mapped in batches of 20, and the return says so
  (the design's unconfirmed concurrency fact).
- **Commits:** each phase-2 package architect commits its own contract and backlog lines
  (scope `plan <pkg>`, trailer `Dev-Team-Run: map-repo <scope>`); the forked architect commits
  `docs/architecture.md` and `docs/decisions.md` last (scope `plan repo`). Two or more commits
  per typed command, one per agent run, as everywhere else in the remake.
- **Top-level modules** (`cli.py`, `settings.py`, `__init__.py` directly under the package)
  belong to the `surface` row; every other section path is a directory.
- **The first run stops** at the monolith split; the re-run proceeds on the stubs' assumptions
  when they are still `open`. The return echoes phase 1's package list as `packages: <name>
  (<path>), …` before the contract paths.
- **The interview stop message** is the architect's, verbatim from today's `agents/architect.md`
  (`Stopped for decisions: D<n>, …` / one line per stub / `Answer in docs/decisions.md, or
  re-run …`), with the continue command `/dev-team:map-repo` and the tag `Raised by:
  /dev-team:map-repo (interview)`; every stub carries the ledger's full field list (`Scope:`,
  `Raised by:`, `Recommendation:`, `Assumption if unanswered:`, `Decision:`, `Status:`,
  `Applied:`).
- **`map-project` is deleted here**, under the three-file rule as it stands: its line leaves
  `reserved-skill-names`, the README tree and `site.yml`; `map-repo` enters all three.

## Files

| Path | Change |
|---|---|
| `skills/map-repo/SKILL.md` | new — specification below |
| `skills/map-project/` | deleted |
| `agents/architect.md` | `## map-repo` filled: the three phases, the spawn block, the monolith test, the as-is wording rule, the backlog line |
| `skills/reserved-skill-names/SKILL.md` | `map-project` → `map-repo` |
| `README.md` | the Contents tree line only (`map-project/` → `map-repo/`); the rest is phase 11 |
| `site/site.yml` | `workflow_skills_order`: `map-project` → `map-repo` |
| `contracts.yml` | the `no unprefixed plugin command` claim needs nothing; `names_listed` claims pass by the three edits above |

## Specification

### `skills/map-repo/SKILL.md`

```yaml
---
name: map-repo
description: Adopt an existing repository into the planning system in one run - list its packages (on a monolith, propose the split and stop for your answer), write one package contract per package from the code in parallel, then the repo contract from those contracts and the import graph. Every existing contract line is a claim checked against the code; defects go to the backlog. Run once on a repo with code and no docs/, and again when the contracts have drifted.
argument-hint: "[scope - a directory or a note on what to focus on; optional]"
context: fork
agent: dev-team:architect
background: false
disable-model-invocation: true
---
```

Body, in order: the Guard block (as the other forked skills); step 1 run gate; step 2 phase 1
(`Explore` over the repo for packages, entry points, top-level exports, imports between
packages, toolchain; the monolith test; the interview stop); step 3 phase 2 (the fan-out per
the architect's **map-repo** section, one message, `run_in_background: false`); step 4 phase 3
(`repo-contract.md`; the Dependency graph from the import graph, a cycle recorded as one line
"does not yet hold"; `covers` `—` without a brief; every existing line a claim); step 5
decisions; step 6 commit (`plan repo`, trailer `Dev-Team-Run: map-repo <scope>`) and return:
packages mapped with their contract paths, corrections by kind, defects filed, `D<n>` stubs,
next command `/dev-team:run-package <pkg>` for the lowest package in the Dependency graph.

## Steps

1. `agents/architect.md` **map-repo** section.
2. `skills/map-repo/SKILL.md`.
3. Delete `skills/map-project/`; the three-file rule edits.
4. `check-contracts`; `build-site`.
5. Evals, through `run-evals`, logged with `log-eval`.
6. Commit: `dev-team remake (phase 07): map-repo replaces map-project — package fan-out, monolith stop`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 7.1 | mechanical | `contracts.yml` | — | `check-contracts` before and after the three-file edits | FAIL on all three `names_listed` claims with `map-repo` unlisted; all PASS after |
| 7.2 | behavioral | `map-repo` | none | `evals/sets/map-repo.json` 1, 2 | every expectation passes for `with_skill`: two package contracts and a repo contract from a two-package fixture tree, each Sections table ending with `surface`; a monolith stops with one `D<n>` per proposed boundary and writes no contract |
| 7.3 | load | `map-repo` | — | `claude --plugin-dir ./dev-team -p "/dev-team:map-repo"` in a scratch repo with two `packages/*/pyproject.toml` | the run returns `Result:` and `docs/architecture.md` exists |

## Done when

- `ls skills/ | grep -c 'map-'` is 1 and it is `map-repo`.
- `check-contracts` all PASS; `build-site` exits 0 and `site/docs/` has a `map-repo` page.
- Logs for 7.1–7.3 in `evals/README.md`.
- The ledger row for phase 7 reads `done`.
