# Seed
/plugin-dev:design-plugin --new idea-lab a research scientist plugin that comes up with new research ideas by reading papers

# User's answers (use these whenever the skill would ask; for anything not covered, pick the option you marked Recommended)
- Who/purpose: me, a research scientist in machine learning. Today I read papers by hand, keep scattered notes, and my ideas come from whatever I happened to read last month.
- Jobs I want: (1) generate new research ideas on a direction I name, each grounded in what the papers actually show and where they leave gaps; (2) answer a specific question I have against the literature ("does X still hold at scale?"), with the papers that bear on it.
- Source material: my library of about 300 PDFs in library/, growing by 10–20 a week, plus arXiv when a direction needs papers I do not have.
- What a careful reading of one paper looks like: its specific claims, each with the evidence behind it (which experiment, table or figure), and how strong that evidence is, not the abstract's framing. Which claims matter depends on what I am investigating; the same paper answers different questions differently.
- Data access: local PDFs, arXiv API and WebFetch, no keys.
- Outputs: markdown files in the repo.
- Boundaries: never presents an idea as supported unless it cites the claims and evidence it rests on. Read-only; never submits or emails anything.
