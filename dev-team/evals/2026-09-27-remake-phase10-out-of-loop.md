# remake phase 10 — probe-source per section, set-constraints wording, extract-legacy without reserved names; two-file rule

**Tested against:** uncommitted — see working-tree diff (on `1eff8a1`; `skills/probe-source/SKILL.md`, `skills/set-constraints/SKILL.md`, `skills/extract-legacy/SKILL.md` rewritten, `skills/reserved-skill-names/` deleted, `CLAUDE.md`, `README.md`, `contracts.yml`) · model: `claude-opus-5-5` (the phase, 10.1, 10.2), the 10.3 headless session `claude-sonnet-5` · 2026-09-27
**Set:** none — the phase note's rows are mechanical and load, run as the note gives them · **Iteration:** none (no `run-evals` behavioral run) · **Baseline:** — · **Pass rate:** —

## What was tested

- **10.1** — with `reserved-skill-names` deleted and its `names_listed` claim removed, the two remaining claims (README's Contents tree, `site.yml`'s workflow order) pass, and a planted `skills/zz-probe/SKILL.md` fails both.
- **10.2** — no agent, skill, `README.md` or `CLAUDE.md` still names `reserved-skill-names`.
- **10.3** — `/dev-team:probe-source data/ingest dataset:trades` loads from the working tree and, in a `state-cases` `design-missing` build, writes the `## data/ingest` entry and commits with the `probe-source` trailer.

## Method

- **10.1** — `contract_sweep.py` on the working tree. Then on a scratch copy with `skills/zz-probe/SKILL.md` added (`disable-model-invocation: true`, so both claims cover it).
- **10.2** — `grep -rn 'reserved-skill-names' agents skills README.md CLAUDE.md | wc -l`.
- **10.3** — `evals/fixtures/state-cases/build.py design-missing` into the scratchpad. A `.claude/settings.json` disabling the installed `dev-team@cott-plugins` was added and git-excluded. Then `claude --plugin-dir ./dev-team -p "/dev-team:probe-source data/ingest dataset:trades" --model claude-sonnet-5`, $0.38. The fixture's probe doc already carried a `## data/ingest` entry, so this is the re-probe the skill now exists for.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 10.1 bundle | all PASS, two `names_listed` claims | 36/36; `README's Contents tree …` 28 names, `every workflow skill is in site.yml's run order` 19 names | ✅ |
| 10.1 plant | both `names_listed` claims FAIL | `not listed in README.md: zz-probe`; `not listed in site/site.yml: zz-probe`; 34/36 | ✅ |
| 10.2 | 0 hits | 0 | ✅ |
| 10.3 | `docs/sources/trades.md` gains a `## data/ingest` item; a commit with the `probe-source` trailer | the doc rewritten to the template (14 numbered headings, **Changes since last probe** filled), `## data/ingest` kept last. One commit `probe trades: full dataset profile for data/ingest` with `Dev-Team-Run: probe-source data/ingest dataset:trades`, three files, all under `docs/sources/`. The return says no design exists to re-open | ✅ |

Observations:

- The 10.3 return's first line was not `Result:`. `Result: done` came on line 3, after a sentence about re-opened designs. This is the researcher return issue phases 3 and 8 noticed (`agents/researcher.md` gives its probe return no `Result:` first line); `probe-source` asks for one, and the agent put it after its lead sentence.
- The 10.3 commit body carries a `Co-Authored-By:` line after the trailer, as the 9.3 run's did.
- `site/` rebuilt at 73 pages, one knowledge page fewer: `reserved-skill-names`.
- The load row names `set-constraints` as a target but gives only the `probe-source` command. `set-constraints` runs in the main thread and asks four questions with `AskUserQuestion`, so a headless `-p` run has no one to answer. It was not run; it is checked only by 10.1's frontmatter and `names_listed` claims.

## Verdict

All three rows hold. `set-constraints` got no load run (see Observations); its edit is wording only, to the description and **Boundaries**.
