# Seed
/plugin-dev:plan-phases --new trading-agents a plugin for stock research agents

# User's answers
Use every answer in trading.md (same directory) for the interview. Then, at the approval
question: approve as shown and accept every suggestion.

# Harness override for this eval only
After approval, do not create a branch, run new-plugin, or write in the repo. Write what
the skill would write into outputs/ instead, keeping repo-relative paths under it:
outputs/trading-agents/site/notes/0.1-00-overview.md, the phase-1 note, the ledger, and any
evals/sets/*.json and evals/sets/files/** the skill writes in its phase-0 commit. Stop after
those files are written; skip phases 2 onward's notes if the skill would write them —
write the overview, the phase-1 note, the ledger and the sets only.
