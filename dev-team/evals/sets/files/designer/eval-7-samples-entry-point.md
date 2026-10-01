# Harness — designer eval 7: samples, mode new, a section that owns an entry point

Seed: you maintain `marketlab`, a two-package uv workspace; `data/ingest` shipped last week.
On 2026-09-27 the `data` contract gained a section, `samples`, so that the tests of
`analysis` can get bars without a CSV file or the network; `data/samples` is ready to design.
You are not at the keyboard during the design step, so any question the designer would ask
goes to `outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The tests in `analysis` will take `make_bars` as a test argument. They will not import
  anything from `data.samples`.
- `packages/data/pyproject.toml` came from the scaffold. It has no `[project.entry-points]`
  table of any group yet, and `pytest` is in the workspace's dev dependency group.
- Sample bars are synthetic. They never come from Alpaca and never from a CSV file.
- D2 is still open; I have not answered it. Nothing else about `data` is undecided.
- `Bar` is the shipped `ingest` shape; `samples` builds it and does not change it.
- Timestamps: `samples` builds its own, as the contract's `samples` entry says. What
  `ingest`'s loader does with CSV timestamps is the subject of a separate open change file
  about `ingest`, not this section.
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

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/samples.md` for the design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.
