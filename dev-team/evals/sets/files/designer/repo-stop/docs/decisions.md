# Decisions

## D1 — Which lookbacks does the momentum signal compute?

Scope: analysis/signals
Raised by: /dev-team:plan-repo (interview)
Recommendation: 20, 60 and 120 trading days.
Assumption if unanswered: 20, 60 and 120 trading days.
Decision: 20, 60 and 120 trading days; nothing shorter.
Status: decided

## D2 — Do the CLI commands log JSON or console lines?

Scope: repo
Raised by: /dev-team:plan-repo (interview)
Recommendation: JSON lines through `structlog`'s JSON renderer.
Assumption if unanswered: JSON lines.
Decision: JSON lines, one event per line, on stderr.
Status: decided
