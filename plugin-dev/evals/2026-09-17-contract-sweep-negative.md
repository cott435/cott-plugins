# `contract_sweep.py` — does each check actually fail when the claim is false?

**Tested against:** uncommitted — the script and skill are new in this change, see the
working-tree diff · model: none, the subject is a deterministic script · 2026-09-17

## What was tested

`check-contracts` is only worth running if each of its three check kinds fails on a real
violation. A validator that passes everything is worse than no validator: it launders the
bundle it was supposed to check. So each kind was run against a bundle with a deliberate defect
of exactly the shape it exists to catch, and against the real bundle, which must still pass.

## Method

`dev-team` at this change's working tree is the reference bundle — it declares five claims in
`contracts.yml` (two `forbid`, two `headings`, one `names_listed`). Copied it to scratch,
introduced four defects, ran the script over both. No model runs, no API cost.

Defects, one per check kind plus one for the second `forbid`:

1. a sentence in `skills/finalize-package/SKILL.md` telling a repo to put pipeline drivers in
   `scripts/` at the repo root;
2. a `site/flow.md` table row crediting `docs/api/<pkg>.md` to `finalize-project` alone;
3. `agents/documenter.md`'s enumeration of `interface.md` headings extended with `Scripts`,
   which the implementer's template does not define — the 0.2.1 bug, reintroduced;
4. a new `skills/brand-new-skill/` directory with no name added to `reserved-skill-names`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| real bundle, all five claims | 5/5 PASS, exit 0 | 5/5 PASS, exit 0 | ✅ |
| defect 1 — `scripts/` promised to a repo | FAIL naming the line | FAIL `skills/finalize-package/SKILL.md:91` | ✅ |
| defect 2 — wrong `docs/api` writer | FAIL naming the line | FAIL `site/flow.md:128` | ✅ |
| defect 3 — heading no owner defines | FAIL naming reader + heading | FAIL `agents/documenter.md names 'Scripts'` | ✅ |
| defect 4 — skill missing from the list | FAIL naming the skill | FAIL `not listed …: brand-new-skill` | ✅ |
| defective bundle overall | exit 1 | 1/5 pass, exit 1 | ✅ |

## Verdict

**All four defects caught, and the real bundle still passes.** Two findings from building it,
both about writing claims rather than about the checker:

- **The first attempt missed defect 1**, because the defect sentence happened to contain a
  phrase listed under `unless` (`` `scripts/` directory beside ``). A too-broad exemption is
  the failure mode for `forbid`: it silently widens into an escape hatch. The exemption was
  narrowed to the specific sentence in `project-structure` §1 that states the prohibition.
- **Narrowing it too far then failed the legitimate line**, because the checks are line-based
  and that sentence wraps mid-phrase. The exemption now quotes the fragment that ends before
  the line break. Both lessons are written into the skill.

**Not a substitute for a behavioral eval.** This settles that the tool reports what the files
say, nothing about whether an agent obeys a rule it reads. That still needs a real run, and
`claude -p --agent …` remains unavailable in this environment (the CLI is stubbed).

**Re-run both halves** whenever `contract_sweep.py` changes — `plugin-dev/CLAUDE.md` now says
so, next to the same rule for `build_site.py`. The defective copy is cheap to rebuild from the
four defects above.
