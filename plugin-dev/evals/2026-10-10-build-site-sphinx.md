# build-site: Sphinx builder replaces MkDocs

**Tested against:** `0f06f12` (`scripts/build_site.py`, `skills/build-site/SKILL.md`) · model: none — the builder is a script, no model ran · 2026-10-10
**Set:** none — a smoke check, not a `run-evals` set · **Baseline:** the MkDocs builder at `fa2bdc7`, not run

## What was tested

That the Sphinx builder discovers everything the MkDocs one did, nests a skill's `references/`
under it, gives every script a page that links back to its callers, and builds without a
warning on both plugins that use the shared builder.

## Method

`build_site.py --build` run from `plugin-dev/` and from `dev-team/` in a worktree at
`0f06f12`, with sphinx 9.1.0, myst-parser, furo 2025.12.19 and sphinxcontrib-mermaid 2.1.1.
Output read by DOM in the browser pane (sidebar nesting, "Referenced by", body links). The
generated page counts were compared with what the MkDocs builder reports for the same bundle
in `evals/2026-09-17-*`. No model calls.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| plugin-dev builds | 0 warnings | 71 pages, 0 warnings | yes |
| dev-team builds | 0 warnings | 124 pages; 2 errors from one note with an unescaped backtick inside a code span (`2.6-spine-05-against-contract-review.md:88`), 0 after escaping it | yes, after fixing the note |
| a skill's references nest under it | `run-evals` shows `eval-kinds`, `prompts`, `skill-creator` as children | all three, in the sidebar | yes |
| a script mentioned in a skill links to its page | `phases.py` linked from `run-phase`, `run-phases`, `plan-phases` | 6 pages in "Referenced by", including `${CLAUDE_PLUGIN_ROOT}/scripts/phases.py` spans | yes |
| `--help` captured for subcommands | every `phases.py` subcommand has its own section | 8 `###` sections | yes |
| a script whose `main()` works before parsing (`contract_sweep.py`) | does not run its sweep during the build | ran the sweep on import in the first attempt; contained in a child process in an empty directory afterward, falls back to `--help` | yes, after fixing |
| `check-contracts` | still passes | plugin-dev 15/15, dev-team 54/54 | yes |

## Verdict

Held. Two defects found and fixed in the same session: the in-process `main()` capture (above),
and a skipped heading level from the MkDocs-era `demote`. Not covered: the mermaid diagrams were
not inspected visually, and the other plugin repos' `site/` layouts were not built. The old and new
nav were compared by section counts, not diffed page by page.
