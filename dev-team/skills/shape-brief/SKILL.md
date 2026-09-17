---
name: shape-brief
description: Turn a rough project idea into docs/brief.md through an open discussion - restates the idea, maps the domain including areas you have not named, narrows it with you to now / later / out, and records constraints and success criteria. Runs in the main conversation so it can ask. Use before /dev-team:plan-repo, to add to a planned repo, or to correct a brief whose contract came out wrong.
argument-hint: "[idea, or path to notes]"
disable-model-invocation: true
---

Shape the project brief with the user. Seed:

$ARGUMENTS

This is the one planning skill that runs **in the main conversation**, because its whole job is
the discussion the forked agents cannot have. The architect turns a settled brief into a
contract. This skill settles the brief: what the project covers and why, before anyone decides
how it is built. A brief that has been through this should leave the architect little to ask.


## Boundaries

- **What and why, never how.** No packages, sections, boundaries, schemas or libraries. Those
  are `/dev-team:plan-repo`'s. A technology belongs in the brief only as a constraint the user
  holds ("must run on our Postgres"), in their words.
- **Suggest; the user decides.** Every capability you add is marked *suggested* until the user
  places it. Nothing enters **Scope — now** without their say.
- **Write only** `docs/brief.md` and, when archiving, `docs/history/<date>-brief.md`. Read
  anything under `docs/`; change nothing else.
- **General, not domain-bound.** What you know about the domain comes from the seed, your own
  knowledge, and web search, never from wording in this skill.

## Start — what exists decides the entry

Read what exists before asking anything:

| Found | Entry |
|---|---|
| No `docs/brief.md` | **New.** The seed is the argument (text, or a file to read). If empty, ask for the idea in the user's own words. |
| `docs/brief.md` with `Status: draft` | **Resume.** Pick up at the first phase whose section is empty or marked pending. |
| `docs/brief.md`, no `docs/architecture.md` | **Rework.** The brief was never planned; edit it with the user. |
| `docs/brief.md` and `docs/architecture.md` | **Correct or add.** Read the contract as the picture the brief produced, and ask which applies: something in it is wrong (correct), or the project is growing (add). |
| `docs/architecture.md` from `/dev-team:map-project`, no brief | **Existing code.** Seed the map with what the contract says already exists, marked *exists*. |

Also read, when present: `docs/decisions.md` entries tagged `Raised by: /dev-team:plan-repo`
(the questions the brief left open last time — settle them here), `docs/assessment.md`, and
the `resource` column of `docs/legacy/inventory.md` (building blocks that already exist).

**Correct** means the user says what was wrong ("it assumed live trading; this is research
only"). Take that first, find the brief text that caused the misreading, and fix the brief
there — the aim is a brief that could not be misread the same way again, not a patch. Then
run the phases below only as far as the correction reaches.

**Add** means new scope. The result is a new section appended to the brief, not an edit of
what is there (see **Writing**) — unless the addition changes existing scope, in which case it
is a correction.

A change to behaviour that has already **shipped** is neither: it is
`/dev-team:plan-change`. Say so, and offer to draft its argument instead.

## Phases

Each phase ends with a checkpoint: a short summary in chat and a question. After phase 3,
write the draft to `docs/brief.md` with `Status: draft` and keep it current, so the discussion
can stop and resume in another session.

### 1. Frame

Restate the idea in two or three sentences. Ask only what the seed does not settle:

- the purpose — the problem, and what changes for whoever uses the result;
- who uses it and how (just the user, a team, external users; CLI, scheduled job, service,
  notebook, UI);
- what a first usable version looks like.

### 2. Map the domain

Build the **capability map**: every area a project like this usually covers, each broken into
capabilities with one line apiece. Go wider than the seed — the point is the areas the user
has not thought of yet:

- the core the idea names, and the variants of it (for a trading idea: rule-based and ML
  strategies, forecasting, execution, not only the one named);
- what the core depends on (data acquisition, quality, storage, reference data);
- what makes it trustworthy (evaluation, backtesting, testing against reality, monitoring);
- what running it takes (scheduling, configuration, secrets, observability, cost);
- what people forget (experiment tracking, reproducibility, access control, reporting,
  compliance, backfills and history).

When the domain is specialised or moves fast, search the web for how real systems in the
space are put together, and use it to check the map, not to pad it. Mark each capability
*you named*, *suggested*, or *exists*.

Show the map as a table grouped by area, and ask whether anything is missing or misnamed
before narrowing. Expect the user to add things once they see the map; that is the phase
working.

### 3. Narrow

Place every capability: **now**, **later**, or **out**. With `AskUserQuestion` (at most four
questions per call, two to four options each):

- one multi-select question per area — "Which of these are in the first version?" — with the
  area's capabilities as options; split an area with more than four;
- up to four areas per call, in as many rounds as the map needs;
- an unselected capability defaults to **later**, which is cheap to change; ask about **out**
  only where the user has hinted at it, or where excluding it simplifies a lot.

Where one capability has approaches that lead to very different projects (research-only
versus live, one asset class versus many), ask which, since the answer changes the scope.
That is still *what*, not *how*.

Detail the user gives about one capability — an approach, a limit, a must-have — goes in that
row's **Notes**, in their words. The row reaches the package that builds it verbatim; the rest
of the brief does not, so a detail that lives only in the Purpose paragraph is lost by the time
sections are designed.

Then write the draft.

### 4. Constraints

Ask only about the ones the conversation has not settled and that would change the shape of
the system:

- users and access;
- how it runs: batch, scheduled, on demand, live or streaming; latency where it matters;
- known inputs: data sources, whether paid sources are acceptable, credentials already held;
- where it runs: local, a server, a cloud account;
- a required language, stack or service; existing code or skills to build on;
- rough scale: volumes, history depth, number of users;
- anything regulatory or security-sensitive.

*No preference* is a valid answer and is written down as such — it tells the architect the
choice is its own.

### 5. Success and unknowns

- What makes the first version done, stated so it can be checked ("backtests a strategy over
  ten years of daily bars in under a minute" beats "fast backtesting").
- What might not be feasible (a data source that may not exist at an acceptable price, an
  approach that may not work). Offer to check the quick ones with a web search now; record
  the rest under **Open questions**, with the user's leaning if they have one.

### 6. Confirm

Write the brief per `references/brief.md` and show a short summary: purpose, the **now**
table, the constraints, the open questions. Ask the user to approve or adjust. Loop until they
approve, then set `Status: ready`.

## Writing

- Read `references/brief.md` before writing, and keep its headings — the architect reads the
  brief by them.
- Before replacing a brief that was ever `ready`, copy it to `docs/history/<today>-brief.md`
  (suffix `-2`, `-3` if taken). `/dev-team:plan-repo` compares the brief against the version it
  planned from; the archive is what lets the user compare too.
- Keep the user's words wherever they gave them.
- **Add** appends one section, `## Addition — <today>`, using the template's headings one level
  down and only the ones that have content. Do not touch the text above it — that is how
  `/dev-team:plan-repo` knows to extend rather than rewrite.
- **Correct** edits the text in place. Where a correction is easier to state than to fold in,
  append `## Revision — <today>` instead, opening with *Where this section conflicts with
  anything above it, this section wins.*

## Return

Three lines at most, then the next command:

- the file written, and whether it was new, corrected, or added to;
- counts: capabilities now / later / out, open questions;
- the next command:
  - `/dev-team:extract-legacy <old repo>` when the user is rebuilding from an old codebase and
    has not surveyed it yet — the survey uses this brief to suggest what to keep;
  - otherwise `/dev-team:plan-repo`, with no argument. When a contract already exists, say what
    that run will do: extend it for an addition; for a correction, rewrite it, keep what shipped
    packages are bound by, and list the package plans that went stale.
