# The flow page drawn by the builder: agents × skills, who writes and reads what, how the drivers run

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-planning-routes` over `1069a0f` (`scripts/build_site.py`, `site/site.yml`, `site/flow.md`, `README.md`, `contracts.yml`, `skills/build-site/SKILL.md`, `templates/site/`, `templates/README.md`; in `dev-team`: `site/site.yml`, `site/flow.md`, `contracts.yml`) · model: none, every case is mechanical or read in a browser · 2026-10-10
**Set:** `evals/fixtures/flow/check.py` (16 cases) for the `flow` claim; none for the builder's layout · **Baseline:** `build_site.py` at `1069a0f`, run on the same two bundles · **Pass rate:** 17/17 cases

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

## The block held to the files (added the same day, over `2949ca8`)

The first version of this log ended by saying nothing compared the hand-written `flow:`
block to the agent and skill files. `contract_sweep.py` now has a `flow` claim that does,
declared in both plugins' `contracts.yml`.

**Method.** `python3 evals/fixtures/flow/check.py`, no model: a throwaway plugin whose block
agrees with its files must pass the sweep and build its flow page with every marker filled;
then fourteen copies, each with one planted disagreement, must each exit 1 and name it. Then
the claim on the two real bundles as their blocks stood at `2949ca8`.

| # | Case | Result |
|---|---|---|
| 10 | fixture: the agreeing block passes and builds | pass |
| 11 | fixture: fourteen planted disagreements (a skill newly named, a use and a `names` entry no longer backed, a skill that does not exist, a document a new role names, a listed role that never names it, an agent that is no role, a hook wired and unnamed, named and unwired, named on the wrong event, a script that does not exist, a script the driver never names, a driver that is no skill, no block) | 14/14 fail as they should, each naming the file and line or the entry |
| 12 | `plugin-dev`'s block as first written | 75 disagreements; 0 after the block was corrected |
| 13 | `dev-team`'s block as first written | 42 disagreements; 0 after |

Most of the 117 were mentions to classify (a file names a skill or a document without
using it, now a `names` entry) and documents the files name by something other than their
path (now a `match`). The rest were facts the hand-written block had wrong, several of them
carried over from `dev-team`'s old `docs/` map:

- the profiler writes to the decisions inbox, a section's deviations and `docs/followups.md`,
  and reads the package contract and the source probes; none of that was listed;
- the tester reads source probes, and the implementer reads `docs/constraints.md`;
- the designer, tester, implementer and reviewer each read a `planning-templates` reference,
  the designer reads `python-style-guide`'s `pipelines.md`, and the architect lists the
  project skills by name;
- the researcher never reads `docs/legacy/inventory.md`: the curator sends it one row;
- in `plugin-dev`, the unit agents read the issues their row names, `run-phase` and
  `plan-phases` can write an eval set, and `run-phase` does not write issue files itself (a
  plan's last phase does, from its note).

## A Reference section, and `dev-team`'s README (added the same day, over `172e41d`)

`build_site.py` renders `site/reference/*.md` under a **Reference** heading after Workflows,
ordered by `reference_order`. `dev-team`'s README went from 801 lines to 111 (what it is
for, how it runs and why, where you are asked, install, the site); its reference sections
moved, text unchanged but for cross-references, to six pages under `site/reference/`.

| # | Case | Result |
|---|---|---|
| 14 | `dev-team` builds: 130 pages, 6 reference, no Sphinx warning on `reference/`, `readme` or `flow` | pass |
| 15 | `plugin-dev`, which has no `site/reference/`, builds as before: 70 pages, no Reference heading | pass |
| 16 | `dev-team` contracts, with every claim that swept the README now sweeping `site/reference/*.md` too, the states claim reading the moved table, and the README's Contents-tree claim removed | 54/54 |
| 17 | every README section is in a reference page, the new README, a workflow page that already held it, or the flow page's generated parts | pass: Contents and the role-by-skill table are the site's own pages and the flow table; Which skill to run is the flow page's **Which route**; Pairing is its workflow page |

## Verdict

Pass, 17/17. The builder's change is confined to the flow page, both plugins' pages render
as designed, and the block they are drawn from now fails `check-contracts` when it and the
files disagree. Not tested: a real phone, Safari and Firefox (the charts use `orient="auto"`
markers and CSS variables with fallbacks, nothing newer), and a plugin with more than about
fourteen roles, where the chart scrolls. What the `flow` claim cannot see: a role that
already names a skill or a document and changes what it does with it (from naming to
running, from reading to writing), the free text of `spawns`, `returns` and each condition,
and the two `plugin-dev` documents marked `match: false` (the plugin's own files, the
release), which are too general to look for.
