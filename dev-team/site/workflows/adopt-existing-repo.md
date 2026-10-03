# Adopting an existing repo

For a repo that has code but no `docs/`, or whose contracts have drifted from the code far
enough to mislead. One command writes every contract; then the ordinary loop walks each section
through a document-mode design, a green intent suite, a README and a review.

Every run starts with the run gate: not `main`/`master`, and no uncommitted change outside the
hand-edited ledgers. Commit your own work and switch to a feature branch first.

## 1. Map the repo

```
/dev-team:map-repo [scope]
```

Forks into the **architect**, in three phases:

1. **The packages.** An `Explore` pass lists the packages — each with its path and what it
   holds. On a **monolith**, one installable tree with no package boundaries, it proposes the
   split instead: one `D<n>` stub per proposed boundary, with the directories each package would
   own, and it **stops**. Package names become directory names and shell arguments, so they are
   never invented silently. Answer in `docs/decisions.md`, or re-run as-is to accept the
   proposal.
2. **One contract per package, in parallel.** It spawns one `dev-team:architect` per package in
   one message, each writing `docs/packages/<pkg>/contract.md` from that package's code with
   the same template a planned package gets — the Sections table ending with `surface`,
   Section interfaces, Pipelines, Public surface, Consumes. Nothing downstream can tell an
   adopted package from a planned one.
3. **The repo contract.** From the contracts and the import graph (`uv run lint-imports` when
   configured, else a read-only grep of imports): `docs/architecture.md`, describing the repo
   **as it is** — a cyclic import graph is recorded as cyclic, a missing convention as missing.

Defects seen while mapping go to `docs/followups.md`, the backlog. Nothing in this run
proposes a change.

On a **re-map**, every existing contract line is a claim to check against the code: wording the
code agrees with is kept, what it contradicts is rewritten, what no longer exists is removed,
and each correction is reported as *stale doc corrected* or *code looks wrong, filed*. A 0.6
repo, with its `surface.md`, `integration.md` and `docs/plans/`, migrates this way; the old files
stay on disk and nothing reads them.

## 2. Walk each package, lowest first

```
/dev-team:run-package data
```

The driver walks the sections in dependency order, as for new code, with two differences
because the code already exists:

- the designer runs in **`document`** mode: code at the path and no design, so the design
  describes what is there;
- the tester expects its intent suite **green** on adopted code. A test that fails is either a
  design that misread the code or code that is wrong — it files a `spec-change:design` with the
  evidence rather than guessing which.

The implementer adds the section README and unit tests and makes the suite pass; the reviewers
review. The `surface` section writes `interface.md` for what the package already exports, and
the package ships like any other.

The stop gate's shape check (`status.py --shape`) fails a run that adds a trivial single-use
helper or an options bag, but on an adopted section it judges only the lines added since the
section's `Mode: document` design was committed, so adopted code is measured and never failed.
The paths review is a different matter: once every section is DONE it follows each command
through the code as it stands, and the first paths review of an adopted package usually finds
P1 to P4 items — a deep call chain, a lambda or mapping on a main path — and takes several FIX
rounds before the package is shipped.

Expect **blocks** on an adopted repo: open questions with no assumption stop a section by
design. Answer them when the driver asks, or in `docs/decisions.md`, and re-run.

## 3. The docs

```
/dev-team:finalize-project
```

Package READMEs, `docs/index.md` and the root README, with **Known gaps** from
`status.py --repo` and the backlog.
