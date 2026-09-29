---
name: planning-templates
description: The heading-by-heading templates for the documents the loop writes and parses — repo contract, package contract, change file, deviations entry, review report, source probe. Invoke when about to write one of them and read only the reference for that document. Kept out of the always-loaded prompts so a run pays for the templates it uses.
---

# Planning document templates

One reference file per document. Read the one you are about to write; do not read the others.
The calling agent's own prompt carries the rules that apply to all of them — for the architect,
what is canonical, who may edit what, the ledger shape, the delegation prompt; for the
researcher, how to reach a source and what counts as having observed it. These files carry only
the headings, the budget, and what goes under each heading.

| You are writing | Read |
|---|---|
| `docs/architecture.md` — the repo contract | `references/repo-contract.md` |
| `docs/packages/<pkg>/contract.md` — the package contract | `references/package-contract.md` |
| `docs/changes/<slug>.md` — a change file | `references/change.md` |
| an entry in `docs/deviations/<pkg>/<section>.md` — a deviation or a spec-change | `references/deviations-entry.md` |
| `docs/reviews/<date>-<pkg>-<section>-r<n>-<a, b or s>.md` — a review report | `references/review-report.md` |
| `docs/sources/<source>.md` — a source probe, either kind | `references/source-probe.md` |

The reviewer, implementer, documenter, and — for the source probe — every one of the four
agents that read it parse these documents by heading, so the headings are a contract too: keep
them, in order, spelled as written. Omit one only when it truly does not apply, and leave a
one-line note under it saying so. `contracts.yml` checks the ones a reader names by hand
against the template that owns them.
