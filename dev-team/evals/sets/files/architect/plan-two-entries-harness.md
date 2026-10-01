# Harness — architect eval 6: the driver's PLAN step with two open `spec-change:contract` entries

Answers as the user would state them. For any question below, answer with the fact given;
for any other question, accept the architect's own `Assumption if unanswered:`.

## Seed

The run works in its own copy of the fixture, and the copy is a git repository. Before
reading the target's documents, in a directory made with `mktemp -d` (`<plugin dir>` is the
plugin directory holding this eval set, `$COPY` the new directory):

```
cp -R <plugin dir>/evals/sets/files/architect/edit/. "$COPY"/
cp <plugin dir>/evals/fixtures/two-package/docs/brief.md "$COPY"/docs/brief.md
mkdir -p "$COPY"/docs/packages/analysis/deviations
cp <plugin dir>/evals/sets/files/architect/plan-two-entries-ledger.md "$COPY"/docs/packages/analysis/deviations/features.md
git -C "$COPY" init -q
git -C "$COPY" add -A
git -C "$COPY" -c user.name=harness -c user.email=harness@example.invalid -c commit.gpgsign=false commit -q -m "seed: the repo as the run finds it"
```

That seed commit is the harness's, not the run's: it stands for the repo's history, it is
the only commit the copy ever gets, and after it the copy's tree is clean. `$COPY` is the
repo root for the whole run. Files are read, written and edited there, in place, and git
commands run there with `git -C "$COPY"`.

## What `status.py` printed

The seed puts every file in one commit, so the commit order `status.py` reads is not this
repo's. Do not run it against the copy. `status.py --run-gate` printed `run gate: PASS`
before the driver spawned the architect. Wherever the run would read `status.py <pkg>`, this
is its output, verbatim:

```
## data
section · state · evidence · ready · round · open spec-change · last commit
ingest · DONE · review r1 approve @4c1d9e2 · no · 1 · — · 4c1d9e2
clean · DESIGN · no docs/packages/data/design/clean.md · yes · — · — · —
storage · DESIGN · no docs/packages/data/design/storage.md · no · — · — · —
surface · DESIGN · no docs/packages/data/design/surface.md · no · — · — · —
shipped: no (surface DESIGN)
next: /dev-team:run-package data

## analysis
section · state · evidence · ready · round · open spec-change · last commit
features · PLAN · open analysis/features — 2026-09-30 — spec-change:contract — 1; analysis/features — 2026-09-30 — spec-change:contract — 2 · yes · — · spec-change:contract · —
report · DESIGN · no docs/packages/analysis/design/report.md · no · — · — · —
surface · DESIGN · no docs/packages/analysis/design/surface.md · no · — · — · —
shipped: no (surface DESIGN)
next: /dev-team:run-package analysis
```

## Facts

- Is any section of `analysis` built? — No. `packages/analysis/` does not exist; the package
  has a contract and nothing else but the `features` ledger.
- Does any package consume `analysis`? — No. It is the top of the dependency graph, and its
  one public name is the `analysis-summary` command.
- Does a symbol with fewer than `window` trades get a VWAP? — Yes. Every trade yields a
  point, computed over that symbol's trades so far until there are `window` of them.
- What does `window < 1` raise? — `InvalidWindowError(window: int)`, an `AnalysisError`.
  `analysis-summary` prints its message and exits 1.
- Has the repo contract or the brief changed since `analysis` was planned? — No. There is no
  `docs/history/` yet; `docs/architecture.md` and `docs/brief.md` are as the contract was
  planned from.
- Should `data` be re-planned, or its contract edited, in this run? — No.
- Are there project skills? — None. The repo has no `.claude/skills/` directory.
- Is there agent memory to read or write? — No. This harness has none: read none, write
  none.
- What goes on the return's `Commit:` line when no commit is made? — `Commit: none
  (harness)`.

## Recording

Staging is real and the run's commit is not: `git add` runs in the copy, `git commit` does
not. At the point where the run would run `git commit`, it records instead:

- **The files.** Every file the run wrote or edited in the copy, copied whole to `outputs/`
  at its repo-relative path (`outputs/docs/packages/analysis/contract.md`, …).
- **`outputs/commit.txt`.** The commit message the run would use — subject line, body,
  trailer — then a line `staged:` and, under it, the output of `git -C "$COPY" status
  --short` taken at that point, verbatim. A path it prints with a letter in the first column
  is staged; one with a space or a `?` there is not.
- **`outputs/return.md`.** The run's return message, verbatim, and nothing else.
