# Rebuilding from a legacy repo

For a rebuild: you have an old, messy repo with working pieces in it — API clients, schemas,
parsers, validators, algorithms — and you want a fresh repo whose contracts come from a brief,
not from the old shape. The old code reaches the new build as **project skills**, never as a
map the architect reads. The architect only ever sees skill names and descriptions.

## 0. Shape the brief

```
/dev-team:shape-brief "<what the rebuild is for>"
```

The curator uses `docs/brief.md` to suggest which old resources are worth keeping, so settle
the scope first. Describe what the old repo does; `shape-brief` maps it with you into *now*,
*later*, and *out* — a rebuild is the moment to drop things — and it never reads the old code.
Its return names `/dev-team:extract-legacy` as the next step.

Every forked run from here on ends in one commit of the files it wrote, and refuses to start on
`main`/`master` or with other uncommitted changes (your hand edits to `docs/decisions.md`,
`docs/brief.md` and `docs/constraints.md` excepted). So the repo is a git repository on a
feature branch before the first one — `git init`, `git switch -c build`, and commit the brief.

## 1. Mine the old repo

```
/dev-team:extract-legacy ../old-repo
```

Forks into the **curator**. It spawns `Explore` over the old repo, verifies what it cites,
and drafts `docs/legacy/inventory.md`: one row per resource worth carrying — named as a
capability (`polygon-aggregates`, `bars-schema`), never as a file — with `suggested: yes/no`
from the brief and `keep: ?` on every row. Then it **stops**.

You edit the inventory: set `keep` to `yes` or `no`, merge rows that belong in one skill by
listing their paths under one id, name the skills, and put instructions for the extractor in
`notes` ("the pagination has an off-by-one — do not port it"). The row is the unit: one row
becomes one skill, so granularity is your call, made here.

```
/dev-team:extract-legacy
```

The curator spawns one **researcher** per kept row, in parallel. Each cuts the resource out of
the old code into `.claude/skills/<name>/references/`, rewrites its imports to stdlib and
third-party only, checks it imports cleanly in a scratch venv, copies the old fixtures
(scrubbed, 200 KB cap), and writes a `SKILL.md` whose first paragraph says the contracts
govern where the code lives and what it is called. The curator marks each row `extracted` or
`failed: <reason>`. Re-running is idempotent; reset a row to `pending` to redo it.

The old repo can live anywhere — a sibling directory, another disk — and is not needed
after this step.

## 2. Plan the new repo

```
/dev-team:plan-repo
```

The architect enumerates `.claude/skills/`, finds the extracted skills beside any you wrote by
hand, and lists them as candidate skills per package, beside the brief capabilities each
package covers. It never opens the old repo. If the contract comes out wrong, correct the
brief and re-run — see [New repo](new-repo.md).

## 3. Plan each package, probing its sources

```
/dev-team:plan-package data
```

Same as the new-repo workflow, with one step you will notice: after the package contract is
written — its Sections table names the external `source` each section consumes — the
architect spawns one **researcher** per source, in parallel, before any designer, each
writing to the repo-wide `docs/sources/<source>.md`. For an `api`, the researcher checks the
credential (env or a root `.env`), reads the vendor's reference, calls the real read endpoints
plus one deliberately bad request each, and records the **observed** schema, pagination,
limits, auth flow and error shapes with a scrubbed sample and a re-runnable probe. For a
`dataset` it opens the data and records columns, dtypes, null rates and duplicates, plus the
target, leakage and split when a modeling task is named — statistics only, never rows. When an
extracted skill exists for that source, the probe also diffs the old fixtures against today's
responses.

A source that cannot be reached **stops** the run there:

```
Stopped for access: POLYGON_API_KEY unset
Resolve them and re-run `/dev-team:plan-package data`.
```

Nothing is designed until every source has answered. Designers then get `Source probes:` and
design the parser against the observed schema; implementers test against the recorded sample
(and re-probe themselves if the doc is missing or older than the design); the reviewer flags
a parser whose fixture is a hand-written dict shaped like the design.

From here it is the new-repo loop: `/dev-team:implement-section`, `/dev-team:review-section`,
`/dev-team:finalize-package`, `/dev-team:review-package`, package by package.

## Later

```
/dev-team:probe-source data polygon
```

Re-probes one source on its own — after an API changes, after a dataset is refreshed, or when
a follow-up from an implementer says the design assumed one shape and the wire returned
another. The doc is rewritten with a new date and a **Changes since last probe** section.
