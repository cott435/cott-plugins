# Deviations — analysis/features

## analysis/features — 2026-09-30 — spec-change:contract — 1

Clause: contract §3 Section interfaces, `features`
Said: "`rolling_vwap(trades: list[Trade], window: int) -> list[VwapPoint]`, window in trades per symbol"
Found: the line does not say what a symbol's first `window - 1` trades yield. Contract §2 gives `report` "one markdown row per symbol: count, total size, last price, last VWAP", so every symbol on the tape needs a last VWAP, and a symbol with fewer than `window` trades has one only if a point is emitted before the window fills. The line should say `rolling_vwap` returns one `VwapPoint` per input trade, in input order, each computed over that symbol's most recent `min(window, trades so far)` trades
Why: how many points `rolling_vwap` returns is what `report` consumes; the `features` design cannot settle it for a sibling section
Status: open
Raised by: designer — run-package analysis
Resolved by: —

## analysis/features — 2026-09-30 — spec-change:contract — 2

Clause: contract §3 Section interfaces, `features`
Said: "`rolling_vwap(trades: list[Trade], window: int) -> list[VwapPoint]`, window in trades per symbol"
Found: `window` has no stated lower bound and the line names no exception. `analysis-summary --window 0` reaches `rolling_vwap` (contract §4 Pipelines, **summary**), and the repo contract's Shared conventions give the package one exception base, `AnalysisError`. The line should say `rolling_vwap` raises `InvalidWindowError(window: int)` (an `AnalysisError`) when `window < 1`
Why: the exception a `window` below 1 raises is caught by `surface`'s command, so its type is the contract's to name; a design's §6 cannot name a type another section catches
Status: open
Raised by: designer — run-package analysis
Resolved by: —
