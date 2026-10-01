# Harness — designer eval 8: prices, mode new, an external service behind every path

Seed: you maintain `marketlab`; `data/prices` is ready to design. Its source `api:alpaca` was
probed on 2026-09-24 (`docs/sources/alpaca.md`), and on 2026-09-27 the contract's `prices`
entry was rewritten against that probe. Any question the designer would ask goes to
`outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The probe is current: it ran against the live v2 endpoint with the keys in `.env`.
- The Alpaca keys exist in the `.env` on my laptop and nowhere else. CI has no keys and no
  outbound network, and the whole test suite has to pass there.
- The probe's sample, `docs/sources/alpaca.sample.json`, is a real response, scrubbed: two
  symbols, five trading days. It may be copied into the repo's test data.
- D2 is still open; I have not answered it. Until I do, the assumption written in
  `docs/decisions.md` is the one to build on.
- `Bar` is the shipped `ingest` shape; `prices` must yield it, not a new type.
- Timestamps: Alpaca's `t` is UTC, as the probe shows. What `ingest`'s loader does with CSV
  timestamps is the subject of a separate open change file about `ingest`, not this section.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## The two documents substituted for this run

The repo for this run is `evals/sets/files/designer/repo`, with two of its documents replaced.
Both replacements are under the dev-team plugin directory the eval was initialized from (the
directory holding `evals/sets/designer.json`):

- `docs/packages/data/contract.md` is `evals/sets/files/designer/eval-7-8-contract.md`.
- `docs/decisions.md` is `evals/sets/files/designer/eval-7-8-decisions.md`.

Read the replacement wherever the designer would read the document, and treat it as being at
the document's path in the repo. The tree's own copies of the two are not part of this run
and are not read.

The repo also holds `docs/deviations/data/prices.md`, the section's ledger at its 2.0–2.1
location: a title line and a note, no entries. The designer reads it as it reads any ledger.
A file it does not write is not copied into `outputs/`.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/prices.md` for the design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## What the transcript records

Besides the harness rules' steps: each step of the designer's procedure as it is carried out,
in order, by the name its instructions give the step, with what was read, checked or changed
in it; and the designer's final message, verbatim.
