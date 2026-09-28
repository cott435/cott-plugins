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

Every run from here on starts with the run gate and ends in one commit of the files it wrote:
the new repo is a git repository on a feature branch, with the brief committed.

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
`notes` ("the pagination has an off-by-one — do not port it"). One row becomes one skill, so
granularity is your call, made here.

```
/dev-team:extract-legacy
```

The curator spawns one **researcher** per kept row, in parallel. Each cuts the resource out of
the old code into `.claude/skills/<name>/references/`, rewrites its imports to stdlib and
third-party only, checks it imports cleanly in a scratch venv, copies the old fixtures
(scrubbed, 200 KB cap), and writes a `SKILL.md` whose first paragraph says the contracts
govern where the code lives and what it is called. The curator marks each row `extracted` or
`failed: <reason>`. Re-running is idempotent; reset a row to `pending` to redo it. A row named
like one of this plugin's own skills is extracted and reported: the name is yours to change.

The old repo can live anywhere and is not needed after this step.

## 2. Plan the new repo

```
/dev-team:plan-repo
```

The architect lists `.claude/skills/`, minus this plugin's own skill names (`ls
${CLAUDE_PLUGIN_ROOT}/skills`), finds the extracted skills beside any you wrote by hand, and
reports a project skill whose name collides with a plugin skill. It profiles the brief's
datasets first. It never opens the old repo.

## 3. Each package

```
/dev-team:plan-package data
/dev-team:run-package data
```

The architect assigns each project skill to the sections that need it, as the Sections table's
`builds with`; the designer and the implementer invoke it. From here it is the
[new-repo](new-repo.md) loop, with the sources probed inside it: when a section that names an
`api:` source becomes ready, the driver spawns a **researcher** for it before its designer. The
researcher checks the credential (env or a root `.env`), reads the vendor's reference, calls
the read endpoints the section needs plus one deliberately bad request, and appends a
`## data/<section>` entry to `docs/sources/<source>.md` with the **observed** schema,
pagination, limits, auth flow and error shapes, a scrubbed sample and a re-runnable probe.
When an extracted skill exists for that source, the probe also diffs its old fixtures against
today's responses. A missing credential stops the section, and the driver asks you for it.

## Later

```
/dev-team:probe-source data/ingest polygon
```

Re-probes one source for one section after the world changed — an API changed, a dataset was
refreshed. The doc's section entry is rewritten, and a design older than the probe doc re-opens
at DESIGN on the next `run-package`.
