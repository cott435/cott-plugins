# Seed
/plugin-dev:plan-phases 0.1

# Setup
Copy `evals/fixtures/trading-agents/` to `outputs/trading-agents/` before starting, then make
two edits in the copy's `site/notes/0.1-design.md`, and nothing else:
1. In the **Cost** table, delete the Horizon column (its header, its separator cell, and its
   cell in every row).
2. In the Deep dive's Input table, change the "Which filings" row's supplier to:
   script: `fetch_filings.py` lists every 10-K, 10-Q and 8-K from EDGAR that has no note yet
Treat `outputs/trading-agents/` as the plugin directory. It has no `.claude-plugin/plugin.json`,
no `CLAUDE.md` and no `contracts.yml`; treat the first check in **Find the design** as passed,
and the plugin as having no `CLAUDE.md` rules and no `contracts.yml` yet. Skip the branch and
clean-tree checks.

# User's answers
- If asked how far back the filings go: the last 8 quarterly filings and the latest 10-K.
- For anything else the skill asks about a gap: pick the option marked Recommended.
- At the split approval: approve as shown.

# Harness override for this eval only
Write everything the skill would write into outputs/trading-agents/, keeping plugin-relative
paths under it. Skip the eval writers: write no evals/sets/ files. Do not commit. Write the
skill's final chat message to outputs/chat.md.
