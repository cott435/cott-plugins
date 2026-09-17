# Cross-file contract sweep — headings, runnable location, `docs/api` writer

**Tested against:** `e4bedca` (`agents/documenter.md`, `skills/finalize-package/SKILL.md`,
`README.md`), `259785a` (`agents/implementer.md`,
`skills/planning-templates/references/surface.md`), `0604620` (`site/flow.md`) — fixes to the
last three uncommitted at test time, see the working-tree diff · model: none, this is a
deterministic script · 2026-09-17

## What was tested

Three claims that an agent acts on and that nothing else in the plugin checks:

1. **HEADING** — every heading a reader is told to parse in `interface.md` or a section README
   is one the owner template (the implementer, surface mode and README template) actually
   defines. This is the class of failure
   `2026-09-17-documenter-interface-heading-contract.md` found; the check exists so it cannot
   come back silently.
2. **RUNNABLE** — nothing in the bundle tells a repo it gets a `scripts/` directory, which
   `project-structure` §1 forbids outright.
3. **WRITER** — no line credits `docs/api/<pkg>.md` to `/dev-team:finalize-project` alone; the
   implementer writes it in surface mode and `finalize-project` fills gaps.

## Method

A ~70-line script over the authored bundle — `agents/*.md`, `skills/**/*.md`, `README.md`,
`site/*.md`, `site/workflows/*.md`. `site/docs/` is excluded: it is a generated mirror, so a
finding there is a duplicate of its source. Owner templates are **parsed out of
`agents/implementer.md`** rather than hard-coded, so the check follows the template if it is
edited. The documenter's own heading list is parsed from its enumeration sentence; six further
heading citations (reviewer ×2, `sync-plan`, `finalize-project`, `finalize-package`,
documenter on the section README) are asserted explicitly.

Run before and after the fixes in this change. Deterministic, no model runs, no API cost:

```
python3 sweep.py dev-team      # exits 1 on any FAIL
```

The script is **not checked in** — it ran from session scratch and is gone with the session.
The three rules above are the specification; rewriting it is an hour at most. If this sweep is
worth having in CI, it belongs beside the bundle as its own file, and this entry is the
argument for that rather than a substitute for it.

**What this does not do:** run an agent. A behavioral harness
(`claude -p --agent <name> --plugin-dir …`) was unavailable — the `claude` CLI is stubbed in
this environment (`claude is not enabled in this environment`), the same blocker recorded in
the documenter entry. All three cases here are claims about file contents, which is exactly
what a mechanical check settles; none of them needed a model.

## Results

| Case | Expected | Before | After | Pass |
|---|---|---|---|---|
| HEADING — reader-parsed headings owned | all owned | PASS — 6 listed by documenter + 6 cited elsewhere | PASS | ✅ |
| RUNNABLE — no `scripts/` promised to a repo | 0 mentions | FAIL — `finalize-package/SKILL.md:3`, `:26`; `site/flow.md:25`, `:54` | PASS — 0 | ✅ |
| WRITER — `docs/api/<pkg>.md` not credited to finalize-project alone | no such line | FAIL — `README.md:289`, `site/flow.md:116` | PASS | ✅ |

HEADING passing *before* is the useful result: it confirms the 0.2.1 documenter fix holds under
a check that does not share its assumptions, and that no other reader of `interface.md` cites a
heading the implementer does not write.

## Verdict

**Two of three claims were false and are now true.** The `scripts` wording was v3 residue in a
skill description, a skill body, and two `flow.md` diagram nodes; `docs/api/<pkg>.md` was
credited to the wrong skill in the README's `docs/` layout and in `flow.md`'s map. Both are
fixed and the sweep exits 0.

**Scope of the behavioral risk, recorded honestly.** Of the four findings flagged as
"worth an eval", only the documenter one (0.2.1) edited a prompt whose wrongness could change
what an agent wrote: `README.md` and `site/flow.md` are read by people, not by any agent, so
the `docs/api` and `flow.md` corrections cannot change agent behavior at all. The
`finalize-package` description and body *are* loaded when the skill forks the implementer, but
the implementer's own surface-mode step 3 already said `cli.py` and "there is no `scripts/`
directory" — so the stale wording contradicted an instruction that was already correct rather
than replacing it. Whether an implementer ever acted on the weaker one is unknown and now
unfalsifiable; the contradiction is gone either way.

**Worth re-running** whenever a template heading is renamed or a new reader of `interface.md`
is added — those are the two edits that can reintroduce the A2 class of failure, and neither
shows up in a diff as anything more alarming than a word change.
