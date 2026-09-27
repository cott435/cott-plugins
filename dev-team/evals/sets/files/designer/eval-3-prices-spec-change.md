# Harness — designer eval 3: prices, mode new, against a probe doc

Seed: you maintain `marketlab`; `data/prices` is ready to design, and its source `api:alpaca`
was probed on 2026-09-24 (`docs/sources/alpaca.md`). Any question goes to
`outputs/interview.md` and is answered from here.

Answers, as facts you would state:

- The probe is current: it ran against the live v2 endpoint with the keys in `.env`; the
  sample file is real, scrubbed.
- The contract row for `prices` was written on 2026-09-19, before the probe.
- You (the user) are not the architect and have not edited the contract since.
- `analysis` needs adjusted closes; how that is achieved is not something you have an
  opinion on.
- `Bar` is the shipped `ingest` shape; `prices` must yield it, not a new type.
- No answer here names a mode, an exit value, a ledger or a document heading; those are the
  designer's to decide from its instructions.

## Where committed files go

The designer commits its files. Under the harness rules, write every file it would write or
commit under `outputs/` at its repo-relative path (for example `outputs/docs/deviations.md`
or `outputs/docs/packages/data/design/prices.md`, whichever it writes), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`.
