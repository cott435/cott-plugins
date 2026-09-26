# Seed
/plugin-dev:design-plugin --new support-insights a plugin that helps our support lead make sense of tickets

# User's answers (use these whenever the skill would ask; for anything not covered, pick the option you marked Recommended)
- Who/purpose: our support lead, one person. Today she reads tickets in Zendesk and writes a weekly summary by hand.
- Jobs I want: (1) triage a new ticket — category, severity, likely root cause, suggested reply; (2) a weekly trends report across all tickets; (3) an account health review before a renewal call with one customer.
- Source material: ticket threads (customer and agent messages), CSAT scores, the product changelog. A good lead reads the whole thread, not just the subject.
- Data access: a nightly JSON export of tickets dropped in exports/ (no API access). ~400 tickets a week across ~120 accounts.
- Outputs: markdown files in a shared repo.
- Boundaries: never sends replies to customers — suggested replies only. No PII copied outside the repo.
