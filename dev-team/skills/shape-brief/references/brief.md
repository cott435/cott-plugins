# `docs/brief.md` — the project brief

Written by `/dev-team:shape-brief` with the user (or by hand); read by `/dev-team:plan-repo`,
`/dev-team:map-project`, and the curator. It states **what** the project covers and **why** —
never how. Budget 150 lines; a table beats prose.

The headings are a contract: `/dev-team:plan-repo` reads the scope sections by name.

```markdown
# <Project name> — brief
Status: draft | ready
Updated: <date>

## Purpose
One paragraph: the problem, who has it, and what changes once this exists.

## Users and use
Who runs it, how (CLI, scheduled job, service, notebook, UI), and how often.

## Scope — now
| Area | Capability | Notes |
|---|---|---|
| <area> | <capability, one line> | <the user's words, a limit, an approach chosen> |

## Scope — later
Not planned now; the design must not rule these out.
| Area | Capability | Notes |
|---|---|---|

## Out of scope
- <capability> — <one-line reason>

## Constraints
- <constraint, in the user's words>
- <topic>: no preference

## Known inputs
| Input | Kind | State |
|---|---|---|
| <data source, existing code, project skill, credential> | <data / code / skill / access> | chosen / candidate / exists |

## Success criteria
- <a checkable statement of what makes the first version done>

## Open questions
- <question> — leaning: <the user's leaning, or "none">
```

Rules:

- **Status** is `draft` while the discussion is open. `/dev-team:plan-repo` refuses a draft.
- A capability sits in exactly one of *now*, *later*, *out*.
- Capability names are unique across the brief, `Addition` sections included. The repo
  contract's `covers` column refers to them by name, and a renamed capability reads as one
  removed and one added.
- **Notes** is the only part of the brief a package plan reads: `/dev-team:plan-package` takes
  the rows its package covers and quotes their Notes into the package contract. Put every
  capability-specific detail there.
- **Constraints** holds only what the user stated. *No preference* is written out, because it
  tells the architect the choice is its own.
- **Open questions** holds what the user could not settle. The architect turns each one that
  changes the decomposition into an interview question.

## Later sections

Appended below the brief, never mixed into it:

- `## Addition — <date>` — new scope. Uses the headings above one level down (`### Scope —
  now`, …), only those with content. `/dev-team:plan-repo` extends the contract.
- `## Revision — <date>` — a correction stated separately. First line: *Where this section
  conflicts with anything above it, this section wins.* `/dev-team:plan-repo` rewrites the
  contract.
