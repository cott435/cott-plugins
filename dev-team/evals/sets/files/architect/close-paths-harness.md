# Harness — architect eval 9: the package close writes **Call paths** as built

Seed: the repo is `evals/sets/files/architect/close-paths/`, read in place and read-only;
every file the run would write or edit goes under `outputs/` at its repo-relative path, and
the commit is recorded in `outputs/commit.txt`, not made.

Answers as the user would state them. For any question below, answer with the fact given;
for any other question, accept the architect's own `Assumption if unanswered:`.

The repo has no git history, so `status.py` cannot run. `status.py --run-gate data` printed
`run gate: PASS`. Wherever the run would read `status.py data`, this is its output, verbatim:

```
## data
section · state · evidence · ready · round · open spec-change · last commit
ingest · DONE · review r1 approve @4e7c2d9 · no · 1 · — · 4e7c2d9
store · DONE · review r1 approve @b2d61f0 · no · 1 · — · b2d61f0
surface · DONE · review r1 approve @d80a3c5 · no · 1 · — · d80a3c5
paths: approved (docs/packages/data/reviews/paths/2026-09-28-r3-p.md)
shipped: yes
next: /dev-team:plan-package backfill
```

Wherever the run would run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py
--paths data`, this is its output, verbatim (every `file:line` it cites is in the tree):

```
command: data-load = data.cli:load
load (packages/data/src/data/cli.py:11)
  run_load (packages/data/src/data/pipelines/load.py:9)
    read_trades (packages/data/src/data/ingest/reader.py:9)
      [effect: open] (packages/data/src/data/ingest/reader.py:19)
      quarantine (packages/data/src/data/ingest/reader.py:27)
        [effect: shutil.copy] (packages/data/src/data/ingest/reader.py:30)
    write_trades (packages/data/src/data/store/writer.py:10)
      [effect: sqlite3.connect] (packages/data/src/data/store/writer.py:19)
      connection.executemany(INSERT_TRADE, trades) (packages/data/src/data/store/writer.py:20) [unresolved]
depth to first effect: 2
deepest effect: 3
indirect frames: 0

command: data-verify = data.cli:verify
verify (packages/data/src/data/cli.py:25)
  run_verify (packages/data/src/data/pipelines/verify.py:14)
    _each_source (packages/data/src/data/pipelines/verify.py:27)
      step(os.path.join(source_dir, name)) (packages/data/src/data/pipelines/verify.py:30) [unresolved]
      lambda (packages/data/src/data/pipelines/verify.py:23) [indirect]
        _verify_one (packages/data/src/data/pipelines/verify.py:35)
          _attempt (packages/data/src/data/pipelines/verify.py:40)
            check_header (packages/data/src/data/ingest/checks.py:11)
              _first_row (packages/data/src/data/ingest/checks.py:22)
                _rows (packages/data/src/data/ingest/checks.py:28)
                  _open (packages/data/src/data/ingest/checks.py:34)
                    [effect: open] (packages/data/src/data/ingest/checks.py:36)
depth to first effect: 9
deepest effect: 9
indirect frames: 1
```

- Are there approved deviations, open change files or open spec-change entries for `data`?
  — None. No section deviated from its contract; the package has no ledger and no change
  file, and the two paths rounds before round 3 are not in this tree.
- Was `data-verify`'s depth accepted when the paths finding was deferred? — No. Deferring
  shipped the package; it decided nothing about the path, and I do not want a `D<n>` raising
  that command's budget.
- Which sections may a cut of `data-verify`'s path touch? — Any of `data`'s. `backfill` has
  no code and no contract, and nothing imports `data` yet.
- Should the backlog line for `data-verify` in `docs/followups.md` be edited or removed? —
  No. The backlog is the reviewer's.
- What is `backfill`'s state? — Unplanned: no `docs/packages/backfill/` and no
  `packages/backfill/`. It is the next package to plan.
