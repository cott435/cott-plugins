# Harness — designer eval 10: window, mode new, one entry point that runs three phases

Seed: you maintain `marketlab`, a two-package uv workspace. `data`'s `ingest`, `clean` and
`storage` sections have shipped. On 2026-09-29 the `data` contract gained a section,
`window`, so that `analysis` can get the bars of several symbols over one date window in a
single call; `data/window` is ready to design, and `surface` waits for it. You are not at the
keyboard during the design step, so any question the designer would ask goes to
`outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The fixture tree holds documents only. The shipped sections' code is not in it and is not
  needed: each README is that section's shipped document and describes its code as it is.
  There is nothing at `packages/data/src/data/window` yet.
- `analysis` will call `load_window` once per signal run, with ten to fifty symbols.
- `kind="csv"` is for a dry run over a fresh broker export, before anything is ingested.
  `kind="store"` is the everyday call.
- A bar comes from the store or from the CSV files. Those two kinds are all there are, and no
  third source is planned.
- `window` writes nothing: no bar to the store, no row to the `runs` ledger. It is not a
  pipeline and has no command.
- `Bar`, `load_bars` and `query_bars` are the shipped ones; nothing about them changes for
  this section.
- Nothing about `data` is undecided. D1 is decided, and no change file is open.
- No answer here names a mode, an exit value, a file or a document heading; those are the
  designer's to decide from its instructions.

## The document substituted for this run

The repo for this run is `evals/sets/files/designer/repo-shipped`, with one of its documents
replaced. The replacement is under the dev-team plugin directory the eval was initialized
from (the directory holding `evals/sets/designer.json`):

- `docs/packages/data/contract.md` is `evals/sets/files/designer/eval-10-contract.md`.

Read the replacement wherever the designer would read the document, and treat it as being at
the document's path in the repo. The tree's own copy is not part of this run and is not read.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/window.md` for the design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## What the transcript records

Besides the harness rules' steps: every file read, by its path, in the order read — a
document of the repo by its repo-relative path, a file of the plugin by its path under the
plugin root; each step of the designer's procedure as it is carried out, in order, by the
name its instructions give the step, with what was read, checked or changed in it; and the
designer's final message, verbatim.
