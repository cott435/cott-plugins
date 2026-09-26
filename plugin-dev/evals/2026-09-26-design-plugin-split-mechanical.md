# `design-plugin` split from `plan-phases` — mechanical checks

**Tested against:** uncommitted — see working-tree diff on branch `design-plugin` (from `eaf3194`) · model: `claude-opus-5-5` · 2026-09-26
**Set:** `evals/sets/design-plugin.json` evals 1–5, `evals/sets/plan-phases.json` evals 1–2 — validated only, not run · **Iteration:** none · **Baseline:** n/a · **Pass rate:** n/a (mechanical)

## What was tested

That the bundle still holds its own contracts after `plan-phases` was split into `design-plugin`
(discussion, charts, writeup) and a slimmed `plan-phases` (design → phases + parallel eval
writers), including a new `headings` claim that `plan-phases` names only design sections
`design-plugin` owns; that every eval set is well-formed; and that the site builds.

## Method

- `python3 scripts/contract_sweep.py .` on the working tree.
- The same on a temp copy with `9. **Build order**` renamed to `**Build plan**` in
  `skills/design-plugin/SKILL.md` (planted defect for the new claim).
- `eval_workspace.py validate` on all 8 files under `evals/sets/`.
- `scripts/build_site.py .`, then `mkdocs build --strict` in `site/`.
- Frontmatter of `design-plugin`, `plan-phases`, `run-phase` parsed with PyYAML.

No behavioral runs; no API cost beyond this session.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Contract sweep, real bundle | 6/6 PASS | 6/6 PASS (9 skills listed; 3 typed in `site.yml`; 5 design names owned) | ✅ |
| Planted `Build plan` rename | new claim FAILs naming the reader | `FAIL … skills/plan-phases/SKILL.md names 'Build order'`, 5/6 | ✅ |
| `validate` on 8 sets | exit 0 each | exit 0 each (first run of `plan-phases.json` failed on two missing harness files — the `git rm` of the old sheet removed the directory; recreated) | ✅ |
| `build_site.py` | builds, new skill and references in nav | 28 pages; `design-plugin`, its `charts`/`composing` references and `plan-phases / eval-writer` under Workflow skills | ✅ |
| `mkdocs build --strict` | exit 0 | exit 0 | ✅ |
| Frontmatter parses | `disable-model-invocation: true`, no XML tag | all three parse; forbid claim 0 matches | ✅ |

## Verdict

Held. This proves only the bundle's shape. The behavioral claims (does `design-plugin` find
the two connected loops in the research-scientist seed, eval 4; does `plan-phases` ask about a
planted gap rather than guess, eval 2) are not yet run.
