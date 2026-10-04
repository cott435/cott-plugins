# Versioning — `dev-team`

The policy — what triggers a patch/minor/major bump, the bump + `CHANGELOG.md` + tag +
marketplace procedure, and the `model:` field policy — lives in the `plugin-dev` plugin's
`bump-version` skill, shared by every plugin. This file records only what is specific to
this one.

## Model decisions

Every agent currently sets `model: inherit` — each one runs on whatever model the calling
session is using. That is the deliberate default: it keeps the plugin's behavior consistent
with a person's own model choice instead of fragmenting cost and quality decisions across
nine agent files behind their back: six roles in the section loop (architect, designer,
researcher, tester, implementer, reviewer), the profiler for a data-heavy section's stage, plus
the documenter and the curator outside it.

No overrides are applied. Candidates, recorded so the reasoning is not re-derived each time:

| Agent | Default | Override candidate | Why |
|---|---|---|---|
| architect | inherit | `opus` | Contracts are read by agents with an empty context and no way to check back — a contract mistake becomes every designer's ground truth. |
| implementer | inherit | `opus` | Writes and ships the actual code; the largest and most conditional agent prompt in the plugin. |
| reviewer | inherit | `opus` | The last judgment before a section is DONE; a false negative here ships. Mechanical checks are the stop gate's, so what is left is judgment. |
| designer, tester | inherit | — | Spawned by the driver once per section, several in parallel; each is checked by the next step — the tester's `design-gap` checks the design, the implementer's run against the intent tests and the reviewer check the tests. |
| curator, researcher | inherit | — | Narrower scope, and checked by a later step (you mark the inventory; the designer reads the probe doc against the contract row). |
| profiler | inherit | — | No override: its judgment — is this row bad — is the session model's to make, and the verify run checks every kind it proposes. |
| documenter | inherit | `sonnet` / `haiku` | Assembles from documents that are already written rather than deciding anything — a plausible cost optimization, not yet applied. |
