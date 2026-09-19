# `plan-phases` — does it compose jobs into shared layers and publish a proposal that renders anywhere

**Tested against:** uncommitted — see working-tree diff of `skills/plan-phases/SKILL.md` (base `25a018f`, plugin-dev 0.7.0) · model: `claude-opus-5` (general-purpose subagents following the skill; baseline = 0.7.0 snapshot) · 2026-09-19

## What was tested

After a real run on `trading-agents` produced one agent per job with no shared research and
printed the mermaid chart as code, the skill gained a **Compose the workflows** step (unit
of work → extract / synthesize / compare / act layers, agents as methods, freshness, cost,
output rules), a proposal published as a self-contained page, and rules that suggestions
attach but never carry and that comparison is core. The claim: on three multi-job briefs in
different domains, the new skill designs shared layers with parallel fan-out and a core
comparison, states cost and output rules, keeps the core independent of suggestions, and
delivers a page whose chart renders legibly outside the Artifact viewer.

## Method

Three briefs, each a seed command plus a fixed sheet of user answers (trading research:
deep dive / screen / portfolio review; ML papers: deep read / literature review / weekly
digest; support tickets: triage / weekly trends / account review). Subagents followed the
skill to the approval question, answering rounds from the sheet, writing
`interview.md`, `proposal.html` (instead of publishing) and `chat.md`; nothing written to
the repo. One run per case per configuration, three iterations of the skill:

- **iteration 1** — compose step + page. 8 assertions.
- **iteration 2** — suggestions attach not carry, compare core, cost, output rules,
  cdnjs mermaid. Not graded: its pages showed mojibake (no charset) and a 31-node,
  55-edge chart that rendered 3829 px wide, so the skill was fixed before grading.
- **iteration 3** — charset, theme-aware full-size mermaid init, chart budget (~20 nodes,
  ~30 edges; skills and scripts in the table). 16 assertions.

Baseline runs (0.7.0) were run once and regraded against each iteration's assertions.
Charts were rendered in the browser pane and measured (nodes, edges, px). An independent
grader subagent graded every assertion with quoted evidence. Workspace (not in the repo):
the session scratchpad `plan-phases-workspace/`.

## Results

| Iteration | Assertions | With skill | Baseline 0.7.0 |
|---|---|---|---|
| 1 | 8 | 24/24 | 8/24 |
| 3 | 16 | 47/48 (98%) | 12/48 (25%) |

Iteration 3, per case (with / baseline): trading 16/16 vs 5/16, papers 15/16 vs 3/16,
support 16/16 vs 4/16. The one miss: papers' per-paper field file had no "must cite" rule.
Measured charts (nodes/edges): trading 19/28, papers 17/28, support 14/25 — all render,
UTF-8, dark-theme legible; widths 1.7–3.1k px at full size, scrolling horizontally.

Design shape on the trading brief: `filing-reader ×N` (one per 10-K/10-Q/8-K/transcript) →
`company-analyst` writes `research/<T>/status.md` → `peer-comparer` against named
competitors and SIC peers → thin deep-dive / screen / review commands reading the shared
files. Baseline: one or two agents shared by name, each job re-researching from scratch,
no status file, no comparison, chart as code in chat.

Cost: +138 s and +24k tokens per run over the baseline (328 s, 117k).

## Verdict

Held. The composing step turned every brief from job-shaped into layer-shaped designs with
a shared status file read by two or more jobs, and the page now renders as a downloaded
file. Grader observations folded into the skill after iteration 3, not re-run: spend depth
where the judgment is made (compare the shortlist, not the whole watchlist; counting is a
script) and read the proposal against itself (depth and fan-out arithmetic agree across
sections). Open: `direction LR` inside subgraphs had no effect (mermaid ignores it when
edges leave the subgraph) and was dropped; wide charts still scroll.
