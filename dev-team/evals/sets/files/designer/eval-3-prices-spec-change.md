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
commit under `outputs/` at its repo-relative path, the path its own instructions give (for
example `outputs/docs/packages/data/design/prices.md` for a design), and put the commit
message — scope, summary and trailer exactly as it would be committed — in
`outputs/commit.txt`, then a line `---`, then each path the commit would stage, one per line,
exactly as its `git commit … -- <paths>` pathspec would name them.

## The fixture's ledger at an older location

The repo holds `docs/deviations/data/prices.md`, the section's ledger at its 2.0–2.1 location:
a title line and a note, no entries. The designer reads it as it reads any ledger. A file it
does not write is not copied into `outputs/`.

For the grader: under 2.2 an entry is edited in the file that holds it, and every new entry
goes to `docs/packages/<pkg>/deviations/<section>.md`. This run appends a new entry, so it
lands in a new file, `docs/packages/data/deviations/prices.md`, whose first line is
`# Deviations — data/prices` and whose one entry is numbered `— 1`; the older file is read and
never written. A 2.1 designer appends to the older file with a heading that has no `— <k>`.
