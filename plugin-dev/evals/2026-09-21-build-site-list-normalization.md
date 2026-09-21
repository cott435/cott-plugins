# `build_site.py` — list indentation normalized on the way into `site/docs/`

**Tested against:** uncommitted — see working-tree diff (`scripts/build_site.py`, previously
`d23232c`) · model: `claude-opus-5` · 2026-09-21

## What was tested

That every generated page's list structure now matches what a CommonMark renderer (GitHub)
makes of the same source — specifically that an ordered item whose content nests at 3 spaces
no longer breaks the list, dropping every item after it into a paragraph. Reported symptom:
`plan-phases` §Compose the workflows renders items 3–7 as prose after item 2's sub-bullets.

## Method

No model runs — this is mechanical. Two checks over every markdown source in both bundles
(`plugin-dev`, `dev-team`: skills, agents, `site/notes/`, `site/workflows/`), plus a visual
pass in a live `mkdocs serve`:

1. **Stranded marker scan** — render each built page with the site's exact extension set
   (`mdx_truly_sane_lists` at `nested_indent: 2`, `truly_sane: true`) and flag any `<p>`
   whose second or later line starts with a list marker. That is the reported symptom,
   stated as something a script can see.
2. **Structure comparison** — render each source three ways and compare the sequence of
   `ol`/`ul`/`li` tags: `markdown_it` in `commonmark` mode (the reference — what GitHub
   shows), the site renderer before the fix, and the site renderer after it.
3. **Content safety** — assert normalization changes whitespace only, by comparing each
   source against its normalized form with all runs of whitespace collapsed.
4. **Eyes on the page** — `mkdocs serve` for both bundles; `plan-phases` §Compose the
   workflows and §Propose then wait, the `run-evals` blockquoted executor prompt, and the
   `overhaul-0.5-03` note's fenced block inside a bullet.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Stranded markers, before | the reported symptom is visible to the scan | 8 pages flagged across both bundles | ✅ |
| Stranded markers, after | 0 | 0 | ✅ |
| List structure vs. CommonMark, after | identical tag sequence on every file | identical on all but 4 files; `li` counts match everywhere | ⚠️ |
| Content safety | whitespace-only change | 2 files differ: both are lazy continuation lines re-indented under the item CommonMark already puts them in | ✅ |
| `plan-phases` §Compose the workflows in the browser | 7 numbered items, 4 sub-bullets under 2, continuation paragraph inside 2 | exactly that | ✅ |
| `run-evals` executor prompt (list inside a blockquote) | bullets render as a list inside the quote | they do | ✅ |
| `overhaul-0.5-03` note (fenced block, then a paragraph, then the next bullet) | sibling bullets align, fence stays inside its item | they do | ✅ |

The 4 files that still differ from CommonMark differ only by a `</ul><ul>` seam: where an
item holds a second block and the next sibling marker follows with no blank line,
Python-Markdown starts a second `<ul>` rather than continuing the first. Item counts and
nesting depth are right, and the seam is invisible on the rendered page (checked on
`overhaul-0.5-03`). Python-Markdown continues an `<ol>` across the same shape; only `ul`
splits, so numbering — the thing that was actually broken — is unaffected.

## Verdict

Held. The symptom is gone in both bundles, structure now matches GitHub's on every file but
the four `ul`-seam cases, and nothing but whitespace changes in the generated pages. Two
follow-on fixes came out of the same pass and are included: a list pressed directly against
its lead-in paragraph (no blank line) was being swallowed whole — 6 of the 8 flagged pages —
and lists inside blockquotes were not normalized at all. Sources are untouched; all of it
happens on the way into `site/docs/`.
