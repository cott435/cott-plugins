# Seed
/plugin-dev:plan-phases --new trading-agents a plugin for stock research agents

# User's answers (use these whenever the skill would ask; for anything not covered, pick the option you marked Recommended)
- Who/purpose: personal use only, just me. Today I read filings and news by hand and keep notes in a doc.
- Jobs I want: (1) a deep dive on a single ticker that reads it like a professional analyst reads filings, ending in an investment thesis; (2) screen my watchlist to shortlist candidates worth a deep dive; (3) review my current portfolio and flag positions that need attention.
- Source material: SEC filings (10-K, 10-Q, 8-K), earnings call transcripts, current news. A professional reads every recent filing, not just the latest.
- Data access: WebSearch/WebFetch and SEC EDGAR (free, no key). No paid data API.
- Watchlist and positions: YAML files I edit by hand (data/watchlist.yml, data/positions.yml). Watchlist ~30 tickers, portfolio ~15 positions.
- Outputs: durable markdown files in the repo, one per run.
- Boundaries: research and recommend only. Never place orders, no brokerage access. Equities only.
