# The section ledger, `docs/packages/<pkg>/deviations/<section>.md` — one entry per deviation or spec-change

One file per section, so agents that run in parallel on different sections never write the
same file. A new file starts with the line `# Deviations — <pkg>/<section>`. Two older
locations are still read, and an entry is edited in the file that holds it: the 2.0 section
file `docs/deviations/<pkg>/<section>.md`, and the pre-2.0 `docs/deviations.md`. Every new
entry goes to the path above.

Append-only; status lines are the only edits, each made with the Edit tool on that one line,
never by rewriting the file. Written by the implementer (`deviation`, `spec-change`), the
designer (`deviation`, one per contract deviation its design's §10 lists, and
`spec-change:contract`), the tester (`spec-change:test`, and `spec-change:design` when two
design items contradict each other) and `pair`, and read by the reviewer (which
sets `approved` or `rejected`), the tester (regenerates the tests an `approved` entry's clause
is cited by), `status.py` (an open spec-change re-opens its step), the stop hook (tolerates a
failing intent test whose docstring cites a `proposed` or `approved` clause) and `sync-plan`
(applies `approved` entries to the contracts and sets `synced`).

Entry heading: `## <pkg>/<section> — <date> — <kind> — <k>`, `kind` one of `deviation`,
`spec-change:test`, `spec-change:design`, `spec-change:contract`, `<k>` the entry's 1-based
sequence in this file (count the `## ` headings and add one). A reader accepts a heading
without `— <k>` (a 2.x ledger) and treats `k` as absent; a writer always adds it, so two
same-day entries of one kind are told apart, and a test's docstring tag names the entry as
`(deviation <date>-<k>)`. Then these lines, in order:

1. **Clause** — the contract row or design item, as the reader cites it: `contract §2 row
   ingest`, `design §5 load_trades`, `design §6 EmptyFile`.
2. **Said** — what the document says, quoted.
3. **Did** — what was built (a deviation).
4. **Found** — the evidence, `file:line` or a probe doc heading (a spec-change).
5. **Why** — the reason. A deviation with no reason is a CRITICAL review finding.
6. **Status** — `proposed | approved | rejected | synced` for a deviation; `open | resolved`
   for a spec-change. Who sets `resolved`: the designer on the `spec-change:design` entries its
   rewrite answers, the tester on the `spec-change:test` entries it regenerates, the architect
   on a `spec-change:contract` it edits for, each in the commit that answers it; `sync-plan`
   sets it on any spec-change `status.py` already counts as answered at the package close.
7. **Raised by** — the role and the run: `implementer — run-package data`.
8. **Resolved by** — `<role> — <Run:>` (`designer — run-package data`) or the report or
   change-file path that closed it; `—` while open. Never the closing commit's own sha, which
   does not exist when the line is written.

Never claims a boundary shape, a public name or a nullable column as an internal deviation:
those are `spec-change` entries, routed by level.
