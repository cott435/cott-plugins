# Decisions

In the repo this is `docs/decisions.md`.

## D5 — pull cap for `stage:rawtrades`: 5 session days?

**Scope:** data
**Raised by:** the package contract, **Package conventions**
**Recommendation:** 5 session days; the vendor bills per day pulled.
**Assumption if unanswered:** 1 session day.
**Status:** decided
**Decision:** 5 session days.

## D7 — negative-size: repair 212 rows?

**Scope:** data/clean
**Raised by:** K1 of docs/sources/rawtrades.md
**Recommendation:** repair (take the absolute value of `size`)
**Assumption if unanswered:**
**Status:** decided
**Decision:** Repair, and not by the absolute value alone. The vendor confirmed a negative size is
how it writes a sell, so take the absolute value of `size` and also set `side` to `S`.

## D8 — duplicate-trade-id: drop 96 rows?

**Scope:** data/clean
**Raised by:** K2 of docs/sources/rawtrades.md
**Recommendation:** drop
**Assumption if unanswered:**
**Status:** open
