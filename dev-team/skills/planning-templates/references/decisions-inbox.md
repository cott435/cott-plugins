# `docs/packages/<pkg>/decisions/<section>.md` — the decisions inbox

One file per section, written by that section's designer and profiler (stubs) and implementer
(`Applied:` lines) with the Write and Edit tools, never by shell, and read by
`hooks/sync_decisions.py`, which folds every entry into `docs/decisions.md` under a lock and
numbers the stubs, and by `status.py --run-gate`, which fails on an entry the central ledger
does not hold. No two agents write one inbox; nobody but the hook, the user, the driver, `pair`
and the architect writes `docs/decisions.md`. A new file starts with the line
`# Decisions — <pkg>/<section>`.

Two kinds of entry, appended, each `## `-headed:

A **stub** — `## D? — <question>`, the `?` literal; the hook rewrites it to `## D<n> —
<question>` and the writer reads the number back before citing it. Then these lines, in order:

1. **Scope** — `<pkg>/<section>`, or the list of sections the question binds.
2. **Raised by** — the design's `OQ-<pkg>-<section>-<k>`, or `K<n> of docs/sources/<token>.md`.
3. **Recommendation** — one line.
4. **Assumption if unanswered** — what the design assumes; empty only when nothing honest fits,
   or for a profiler's `repair` or `drop` kind, so the section is BLOCKED until the user answers.
5. **Status** — `open`. Nothing else.

An **applied** entry — `## D<n>`, the number of a central entry, then one or more:

6. **Applied** — `<pkg>/<section>, <date>, <path>`, one line per application.

Never in an inbox: a `Decision:` line; a `Status:` other than `open`; a number the writer chose
itself (`## D14 — …` for a new question — the hook renumbers it and says so); an edit to an
entry after the hook numbered it, other than an `Applied:` line. Only `Applied:` lines and new
stubs flow to `docs/decisions.md`; a `Decision:` or `Status:` written here never does.
