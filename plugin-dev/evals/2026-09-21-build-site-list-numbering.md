# `build_site.py` — ordered lists count the way their author wrote them

**Tested against:** uncommitted — see working-tree diff (`scripts/build_site.py`,
`scripts/defaults/mkdocs-base.yml`) · model: `claude-opus-5` · 2026-09-21

## What was tested

That every list on every built page shows a reader the same markers, at the same nesting
depth, as a GitHub reader sees in the source. Found while checking `dev-team` after
`2026-09-21-build-site-list-normalization.md`: the numbering itself was wrong on 6 pages,
and had been before that change too — the normalization fixed structure, not counting.

Two failures, one cause. `mdx_truly_sane_lists` drops an ordered list's starting number:

- a list the author resumed after an aside they wrote as a plain paragraph (`plan-repo`
  step `2b.`, which markdown cannot express as a marker) restarted at **1**, so Steps read
  1, 2, 1, 2, 3, 4 — `plan-package` read 1, 2, 3, 1, 1, 2, 3, 4, 5, with a repeated 1;
- a list written from `0.` (the `implementer`'s Procedure, whose own prose says "step 0
  below") renumbered to 1, putting all fourteen steps one off from every reference to them.

## Method

No model runs — mechanical, plus eyes on the page. For each built page that records a
`*Source:*` line, the sequence of `(nesting depth, visible marker)` pairs a reader sees is
extracted from the HTML — resolving `<ol start=…>` the way a browser does — and compared
between `markdown_it` in `commonmark` mode on the **source** (what GitHub shows) and the
site's own extension set on the **built page**. 64 pages across both bundles qualify. Each
candidate fix was measured the same way before it was adopted, and the stranded-marker scan
from the previous eval was re-run unchanged.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Baseline: pages matching GitHub, before either fix | — | 58 / 64 | — |
| Baseline: same pages, after normalization alone | unchanged — it fixes structure, not counting | 58 / 64, the same 6 failing | ✅ |
| `sane_lists` honors a start number | `<ol start="0">`, `<ol start="3">` | both emitted | ✅ |
| `mdx_truly_sane_lists` honors a start number | — | plain `<ol>` in both cases | ✅ |
| After the swap: pages matching GitHub | 64 / 64 | 64 / 64 | ✅ |
| Stranded markers (previous eval's scan) | 0 | 0 | ✅ |
| `plan-repo` Steps in the browser | 1, 2, [2b aside], 3, 4, 5, 6 | exactly that | ✅ |
| `implementer` Procedure in the browser | starts at 0, runs to 13 | starts at 0 | ✅ |
| `mkdocs build` on `dev-team` | clean | clean, 0.69s | ✅ |

## Verdict

Held. `mdx_truly_sane_lists` was only ever there to read the 2-space nesting these files
use; now that `build_site.py` re-indents every page to Python-Markdown's own 4 spaces, stock
`sane_lists` does the job and also honors start numbers. The extension is dropped — one
fewer third-party dependency to install — and all 64 pages match GitHub exactly, up from 58.
Worth noting for the next person: the earlier comparison in
`2026-09-21-build-site-list-normalization.md` measured CommonMark against the *built* page,
which flagged 23 false differences, because strict CommonMark does not nest at the width the
site is configured for. The source is the only fair left-hand side.
