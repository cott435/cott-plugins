# Notes live in `site/notes/<slug>/` — the contract sweep and `build_site.py`

**Tested against:** uncommitted — see working-tree diff (on `ba2e8fc`; `scripts/build_site.py`, `skills/plan-phases/SKILL.md`, `skills/design-plugin/SKILL.md`, `skills/run-phase/SKILL.md`, `skills/run-phases/SKILL.md`) · model: none, mechanical (session on `claude-sonnet-5-5`) · 2026-10-09
**Set:** none — mechanical checks, no set file · **Iteration:** none · **Baseline:** `main` at `d9d38c3` for the builder · **Pass rate:** sweep 11/11 after one fix; builder 3/3

## What was tested

That moving a plan's notes from `site/notes/<slug>-*.md` to a folder per plan, `site/notes/<slug>/`,
leaves the bundle's contracts holding, and that `build_site.py` shows only a plan folder's
`<slug>-00-overview.md` under Notes while loose notes render as before.

## Method

No model runs. `python3 scripts/contract_sweep.py` over `plugin-dev` before and after fixing the
skill edit, then three builds in a scratch copy of `dev-team` (which has the committed folders
`site/notes/remake_2.0/` and `site/notes/determinism/`): the `main` builder, the working-tree
builder, and the working-tree builder on a copy with `2.2-*.md` moved into `site/notes/2.2/`.
`plugin-dev`'s own site was rebuilt in place.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Sweep on the edited skills, first run | 11/11 | **FAIL** `no skill or agent description contains an XML-style tag` at `skills/plan-phases/SKILL.md:3`: `plan-phases`' description named `site/notes/<slug>/…`, and claude.ai rejects any `<word>` in a description | ❌ |
| Sweep after the description used `{slug}` | 11/11 | 11/11 | ✅ |
| Old and new builder on `dev-team` as committed | the same site, plus the overview of the one plan already in a folder | `diff -r` of `site/`: one new page, `note-remake_2.0-remake-00-overview.md`, and one nav line `remake_2.0 overview`; every other page byte-identical (63 → 64 notes) | ✅ |
| New builder with `2.2-*.md` moved into `site/notes/2.2/` | Notes shows `2.2 overview` and none of the 14 other `2.2-*` notes | exactly that: `note-2.2-2.2-00-overview.md` only (63 → 50 notes) | ✅ |
| A folder with no overview (`site/notes/determinism/`: `00-plan.md`, `findings/`) | nothing rendered, no error | nothing rendered, build exits 0 | ✅ |

## Verdict

The sweep caught a real break in the edit before it shipped, and passes after the fix. The builder
change is additive: loose notes render as before, a plan folder contributes its overview and
nothing else. Not tested: the behavioral evals for `design-plugin`, `plan-phases`, `run-phase` and
`run-phases` — their fixtures under `evals/fixtures/` and the paths in `evals/sets/*.json` still
use the flat layout, so those sets need the fixtures moved into folders before they are rerun.
`contract_sweep.py`'s default scope is still `site/notes/*.md`, so notes inside a plan folder are
not swept.
