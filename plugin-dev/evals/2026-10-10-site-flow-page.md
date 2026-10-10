# The flow page drawn by the builder: agents × skills, who writes and reads what, how the drivers run

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-planning-routes` over `1069a0f` (`scripts/build_site.py`, `site/site.yml`, `site/flow.md`, `README.md`, `contracts.yml`, `skills/build-site/SKILL.md`, `templates/site/`, `templates/README.md`; in `dev-team`: `site/site.yml`, `site/flow.md`, `contracts.yml`) · model: none, every case is mechanical or read in a browser · 2026-10-10
**Set:** none; the builder has no eval set · **Baseline:** `build_site.py` at `1069a0f`, run on the same two bundles · **Pass rate:** 9/9 cases

## What was tested

`build_site.py` now fills five markers in `site/flow.md` from each agent's `skills:`
frontmatter and a `flow:` block in `site/site.yml`. The claims:

1. Nothing else on either site changed.
2. The generated parts render, in both plugins, in the layout asked for: roles in one row,
   the documents one role writes above it, the documents several write below it with an
   arrow from each writer; the same for reading; one loop per driver with its ledger.
3. A plugin with no `flow:` block, no `site/flow.md`, or neither still builds, and a block
   the page does not show, or a name that is no role, is reported.
4. Both bundles' contracts still pass.

## Method

1. The old builder (`git show 1069a0f:plugin-dev/scripts/build_site.py`, beside a copy of
   `scripts/defaults/`) and the new one each wrote `site/docs/` for `plugin-dev` and
   `dev-team` from the same working tree; `diff -rq` on the two trees.
2. `build_site.py --build` on both; `python3 -m sphinx -b html -q -E` output filtered for
   `flow` and `readme`; the two flow pages opened in the browser pane at 552, 1300, 1500 and
   1700 px wide in the dark theme, and `plugin-dev`'s in the light one.
3. A toy plugin in a scratch directory (one agent that preloads one skill, one typed
   skill), built five ways: no `site/`; no agents and no `site/`; a `flow:` block with a
   `flow.md` that lacks two markers and has one unknown marker; a misspelled role in a
   document's `reads`; every marker present, built to HTML.
4. `contract_sweep.py` on both bundles; `evals/fixtures/{phases,issues,run-evals-runner}/check.py`.

## Results

| # | Case | Result |
|---|---|---|
| 1 | old against new builder, `plugin-dev` (70 pages) | only `flow.md` differs |
| 2 | old against new builder, `dev-team` (124 pages) | only `flow.md` differs |
| 3 | both sites build; no Sphinx warning names `flow` or `readme` | pass (the warnings left are in `site/notes/` and were there before) |
| 4 | charts in the browser | both document charts and the driver rows render in both plugins; `dev-team`'s ten roles fit a 1500 px window, `plugin-dev`'s fourteen scroll sideways at 85% scale |
| 5 | toy, agents and no `site/` | a flow page is written; its table has the preloaded skill as ●; the three parts with no data say so |
| 6 | toy, no agents and no `site/` | no flow page, as before |
| 7 | toy, `flow.md` missing `documents` and `drivers`, holding `<!-- flow:ledger -->` | three `!` lines name the two missing markers and the unknown one |
| 8 | toy, `reads: [worker, wroker]` | the build prints `wroker` as "in the documents table only" |
| 9 | contracts and fixtures | `plugin-dev` 14/14 (one claim removed: the README no longer lists the skills), `dev-team` 54/54 with `site/site.yml` added to the seven swept file lists; phases 56/56, issues all passed, runner 27/27 |

Found and fixed while reading the pages: mermaid lays unconnected subgraphs side by side
whatever the direction, so the driver loops are drawn as SVG rows like the document charts;
Furo's right-hand contents column sits at `z-index: 50` and covered a widened chart; shared
documents placed strictly left to right ran to seven rows on `dev-team`'s reading chart and
take four when the most shared are placed first; a document's path set to wrap anywhere
shrank its table column to a few characters until it was given a minimum width.

## Verdict

Pass. The builder's change is confined to the flow page, and both plugins' pages render as
designed. Not tested: a real phone, Safari and Firefox (the charts use `orient="auto"`
markers and CSS variables with fallbacks, nothing newer), and a plugin with more than about
fourteen roles, where the chart scrolls. The `flow:` blocks were written by hand from the
skill and agent files; no check compares them to those files, so a role that starts using a
skill without an edit to the block goes unnoticed until someone reads the page.
