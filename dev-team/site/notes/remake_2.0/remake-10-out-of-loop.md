# 10 — the commands outside the loop

Phase 10. Rewrites `probe-source` (a re-probe after the world changed; appends the consuming
section's heading; a newer probe doc re-opens the designs that cite it through `status.py`),
`set-constraints` (same shape; drops "after shape-brief"; says its file is the stop gate's
spec) and `extract-legacy` (drops the reserved-names check: a project skill named like a plugin
skill is reported by the architect, never refused). Deletes `reserved-skill-names` and turns
the plugin's `CLAUDE.md` three-file rule into a two-file rule (`README.md`'s Contents tree and
`site/site.yml`), with `contracts.yml`'s `names_listed` claims trimmed to those two. The gap it
closes: a list guarded against a case that cannot happen (a plugin skill under
`.claude/skills/`) and had to be edited by hand for every skill.

## Decisions

- **`probe-source` needs a section**: `/dev-team:probe-source <pkg>/<section> <source>
  [purpose]`, or `repo <source>` for a dataset with no package. Reason: the per-section heading
  is the unit the probe appends.
- **`set-constraints`** keeps its four questions and template; its Boundaries say the stop gate,
  `status.py` and CI run the file's rows, and the reviewer reads **Measured** and **Exceptions**
  only.
- **`extract-legacy`**'s "Before extracting" keeps `failed: skill exists`, drops `failed: name
  reserved`; the return notes that a name colliding with a plugin skill is reported by the
  architect on its next run.
- **The two-file rule** text in `CLAUDE.md` names what enforces it: the two `names_listed`
  claims.

## Files

| Path | Change |
|---|---|
| `skills/probe-source/SKILL.md` | rewritten: argument-hint `"<pkg>/<section> | repo <source, optionally kind-prefixed> [purpose]"`, `arguments: [target, source]`; resolve the seven probe fields (adds `Section:`); run gate; the researcher commits (no `Commit: yes` line); a re-probe's return names the designs that cite the doc |
| `skills/set-constraints/SKILL.md` | description: "…Runs in your conversation. Use any time before the first build, or whenever a threshold should change."; Boundaries as **Decisions**; §5 commit unchanged |
| `skills/extract-legacy/SKILL.md` | the `reserved-skill-names` paragraph removed; the collision note in Constraints |
| `skills/reserved-skill-names/` | deleted |
| `CLAUDE.md` | "Adding a skill means updating three files" → "Adding a skill means updating two files" — specification below |
| `README.md` | the Contents tree line for `reserved-skill-names/` removed; the knowledge-scope table row removed (the rest is phase 11) |
| `contracts.yml` | the `reserved-skill-names` `names_listed` claim deleted; §Project convention: no change (the curator's span stays) |

## Specification

### `CLAUDE.md` section

```
## Adding a skill means updating two files

A new skill here — workflow or knowledge — is added, in the same change, to:

1. `README.md`'s **Contents** tree, and its knowledge-scope table if it is a knowledge skill;
2. `site/site.yml`'s `workflow_skills_order`, if it is a workflow skill.

A skill *removed* comes out of both. `plugin-dev`'s `check-contracts` fails on both, in both
directions — a skill missing from a list, and a name in a list with no such skill — so run it
after any change under `skills/`. It is the rule's enforcement, not a reminder of it: the two
claims are `contracts.yml`'s two `names_listed` entries. Item 2 covers the workflow skills
only, selected by `disable-model-invocation: true` rather than by a second list. The plugin's
own skill names are never listed anywhere else: at run time the architect derives them with
`ls ${CLAUDE_PLUGIN_ROOT}/skills`.
```

The rest of `CLAUDE.md` (Repo-specific, the shared-protocol section, the build command) stays.

## Steps

1. `probe-source`, `set-constraints`, `extract-legacy`.
2. Delete `skills/reserved-skill-names/`; `README.md` tree line and table row; `CLAUDE.md`;
   `contracts.yml`.
3. `check-contracts`; `build-site`.
4. Evals, through `run-evals`, logged with `log-eval`.
5. Commit: `dev-team remake (phase 10): probe-source per section, set-constraints wording, extract-legacy without reserved names; two-file rule`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 10.1 | mechanical | `contracts.yml` | — | `check-contracts`; then plant a `skills/zz-probe/SKILL.md` and run again | all PASS; the plant FAILs both `names_listed` claims |
| 10.2 | mechanical | `skills/extract-legacy/SKILL.md`, `agents/architect.md` | — | `grep -rn 'reserved-skill-names' agents skills README.md CLAUDE.md` | 0 hits |
| 10.3 | load | `probe-source`, `set-constraints` | — | `claude --plugin-dir ./dev-team -p "/dev-team:probe-source data/ingest dataset:trades"` in a `state-cases` `design-missing` build | `docs/sources/trades.md` gains a `## data/ingest` item and a commit with the `probe-source` trailer |

## Done when

- `ls skills/ | grep -c reserved` is 0; `grep -c 'three files' CLAUDE.md` is 0.
- `check-contracts` all PASS with two `names_listed` claims counted; `build-site` exits 0.
- Logs for 10.1–10.3 in `evals/README.md`.
- The ledger row for phase 10 reads `done`.

## Deviations

- **`extract-legacy` gained a run gate.** The note's Files row for `extract-legacy` names only
  the removed paragraph and the collision note. The ledger's phase-4 note for this phase adds
  that `extract-legacy` must run the run gate first (§Project convention rule 1, a typed skill
  that forks an agent). What was done: a `## Run gate` section, the same form
  `finalize-project` and `sync-plan` use.
- **`set-constraints`'s Boundaries needed one correction.** The note's decision says the stop
  gate, `status.py` and CI "run the file's rows". `status.py --run-gate` checks the branch and
  the clean tree and runs no row. `status.py` parses the rows, and `gate_on_stop.py` imports
  that parser. The Boundaries say the gate and CI run the **Floor** and **Enforced** rows,
  parsed by `status.py`. Its old **Branch rule** bullet, which named the retired **Branch**
  and **Baseline** rules, is now **Run gate first**, citing `status.py --run-gate`.
- **`probe-source`'s re-probe return names sections, not designs by grep.** The note says a
  re-probe's return "names the designs that cite the doc". `status.py` re-opens a design when
  its Sections row's `source` column names the doc and the doc's shared headings changed after
  it, not when a design's text cites the path. So the return lists those sections, and says
  that a change to this section's own entry re-opens nothing else.
- **The probe-source description was rewritten** beyond the argument-hint. The old one said
  `/dev-team:plan-package` probes every source, which phase 6 removed, and offered this skill
  to add a source after planning, which the design makes a `plan-package` edit.
- **`README.md`'s tree** needed its closing glyph moved. `reserved-skill-names/` was the last
  branch, so `git-workflow-and-versioning/` now takes `└──`.
- **`contracts.yml`'s two remaining `names_listed` comments** were renumbered from the
  three-file rule's items 2 and 3 to the two-file rule's items 1 and 2.
- **10.3's `set-constraints` half was not run.** The row names `set-constraints` as a target
  but gives only the `probe-source` command, and `set-constraints` asks four questions in the
  main thread, which a headless run cannot answer. It is covered by 10.1's claims only.
- **Paired with phase 9 in one chat, on the user's word.** The overview allows 9 and 10 to
  pair. Phase 9 committed first (`1eff8a1`) and this phase started from a clean tree.
