# Versioning — `project-workers`

The policy — what triggers a patch/minor/major bump, the bump + `CHANGELOG.md` + tag +
marketplace procedure, and the `model:` field policy — lives in the `plugin-dev` plugin's
`bump-version` skill, shared by every plugin. This file records only what is specific to
this one.

## Model decisions

Every agent currently sets `model: inherit` — each one runs on whatever model the calling
session is using. That is the deliberate default: it keeps the plugin's behavior consistent
with a person's own model choice instead of fragmenting cost and quality decisions across
seven agents behind their back.

No overrides are applied. Candidates, recorded so the reasoning is not re-derived each time:

| Agent | Default | Override candidate | Why |
|---|---|---|---|
| architect | inherit | `opus` | Plans are read by agents with an empty context and no way to check back — a planning mistake becomes every designer's ground truth. |
| implementer | inherit | `opus` | Writes and ships the actual code; the largest and most conditional agent prompt in the plugin. |
| reviewer | inherit | `opus` | Last gate before findings are filed; a false negative here ships. |
| designer, curator, researcher | inherit | — | Narrower scope, and checked by a later step (review, or the architect reconciling designs). |
| documenter | inherit | `sonnet` / `haiku` | Assembles from documents that are already written rather than deciding anything — a plausible cost optimization, not yet applied. |
