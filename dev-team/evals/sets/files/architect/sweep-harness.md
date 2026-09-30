# Harness — architect eval 5: the package close with an answered spec-change still `open`

Answers as the user would state them. For any question below, answer with the fact given;
for any other question, accept the architect's own `Assumption if unanswered:`.

The repo has no git history, so `status.py` cannot run. `status.py --run-gate data` printed
`run gate: PASS`. Wherever the run would read `status.py data` (or `status.py` for every
package), this is its output, verbatim:

```
## data
section · state · evidence · ready · round · open spec-change · last commit
ingest · DONE · review r2 approve @e1f8d42 · no · 2 · — · e1f8d42
clean · DONE · review r2 approve @a4d2c19 · no · 2 · — · a4d2c19
storage · TEST · open data/storage — 2026-09-27 — spec-change:test — 1 · yes · 1 · spec-change:test · 9e4c3d7
surface · DONE · review r1 approve @c07a5b3 · no · 1 · — · c07a5b3
shipped: yes
next: /dev-team:run-package data
```

- `storage` is at TEST. Should the close stop, or return blocked? — No. Carry on with the
  close as your instructions describe it; the driver runs `storage`'s TEST step after it.
- Should the `data/storage — 2026-09-25` deviation be applied because its status is
  `approved`? — No. Its `Did:` (`batch_size`) is not in `packages/data/src/data/storage/db.py`;
  leave it `approved`, do not edit it, and name it in the return as left open.
- Should the rejected `data/ingest — 2026-09-23` entry be applied or edited? — No, neither.
- Is `dedupe` a public name, so that its changed return type needs consumers reclassified?
  — No. It is not in `docs/packages/data/interface.md`'s Public names; only `clean_trades`
  calls it. No public name changes in this close.
- What is `analysis`'s state? — It has no contract yet (`docs/packages/analysis/` does not
  exist); it is the next package to plan.
