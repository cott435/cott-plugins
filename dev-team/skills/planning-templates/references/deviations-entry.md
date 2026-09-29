# The section ledger, `docs/deviations/<pkg>/<section>.md` — one entry per deviation or spec-change

One file per section, so agents that run in parallel on different sections never write the
same file. A new file starts with the line `# Deviations — <pkg>/<section>`. A
`docs/deviations.md` from before the split is still read: an entry there has its status line
edited where it is, and every new entry goes to the section's file.

Append-only; status lines are the only edits, each made with the Edit tool on that one line,
never by rewriting the file. Written by the implementer (`deviation`, `spec-change`), the
designer (`deviation`, one per contract deviation its design's §10 lists, and
`spec-change:contract`) and the tester (`spec-change`), and read by the reviewer (which
sets `approved` or `rejected`), the tester (regenerates the tests an `approved` entry's clause
is cited by), `status.py` (an open spec-change re-opens its step), the stop hook (tolerates a
failing intent test whose docstring cites a `proposed` or `approved` clause) and `sync-plan`
(applies `approved` entries to the contracts and sets `synced`).

Entry heading: `## <pkg>/<section> — <date> — <kind>`, `kind` one of `deviation`,
`spec-change:test`, `spec-change:design`, `spec-change:contract`. Then these lines, in order:

1. **Clause** — the contract row or design item, as the reader cites it: `contract §2 row
   ingest`, `design §5 load_trades`, `design §6 EmptyFile`.
2. **Said** — what the document says, quoted.
3. **Did** — what was built (a deviation).
4. **Found** — the evidence, `file:line` or a probe doc heading (a spec-change).
5. **Why** — the reason. A deviation with no reason is a CRITICAL review finding.
6. **Status** — `proposed | approved | rejected | synced` for a deviation; `open | resolved`
   for a spec-change.
7. **Raised by** — the role and the run: `implementer — run-package data`.
8. **Resolved by** — the commit or run that closed it; `—` while open.

Never claims a boundary shape, a public name or a nullable column as an internal deviation:
those are `spec-change` entries, routed by level.
