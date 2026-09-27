# 09 — documenter and finalize-project

Phase 09. Rewrites the documenter and `finalize-project`: the human-facing layer from the
shipped documents — each package's `interface.md`, its section READMEs and contract, the repo
contract, the decisions ledger and the backlog — with **Known gaps** built from `status.py
--repo` plus what only a document check finds (a claimed command that does not exist, two
sections with conflicting env defaults). Gone: `docs/plans/synced.md`, the assessment inputs,
the API-page fallback (the `surface` section's implementer writes every `docs/api/` page). The
gap it closes: the documenter derived the repo's gaps its own way, a fifth reading of state.

## Decisions

- **The documenter runs `status.py --repo`** itself (Bash, read-only) and copies its output
  under **Known gaps** verbatim before its own document-only findings. Reason: one derivation.
- **Written files:** `packages/<pkg>/README.md` (or the root README's package section in a
  single-package repo), root `README.md`, `docs/index.md`; hand-written READMEs preserved to
  `docs/readme-previous.md` / `docs/packages/<pkg>/readme-previous.md` as today. Nothing under
  `docs/api/`, no `mkdocs.yml` edit; a shipped package with no API page is a **Known gaps**
  line.
- **Package status** in the root README's Packages table is copied from `--repo`'s
  `packages:` group: `planned`, `building (<n>/<total> DONE)`, `shipped`; `no contract` is
  written as `planned` with a Known gaps line.
- **The backlog appears once** under Known gaps, as the script's `backlog:` group; the
  documenter does not re-list `docs/followups.md`.
- **A conflicting env default** is shown as both values with their sections and the word
  *conflict* in the Configuration table, and again as a Known gaps line.
- **An unfinalized package** (no `interface.md`) keeps today's behavior: its README is assembled
  from the section READMEs, marked *not shipped*, and no public name is inferred from code.
- **The fixture `evals/sets/files/documenter/status-repo.txt`** is regenerated from the real
  `status.py --repo` over the `repo-gaps` overlay in this phase, before eval 9.2 runs.
- **`interface.md` headings read** stay the six the existing claim names.

## Files

| Path | Change |
|---|---|
| `agents/documenter.md` | rewritten: Hard rules (Bash gains `status.py --repo`), Finding the documents, Assembling, Known gaps (the two sources), Commit; the decisions-ledger paragraph unchanged |
| `skills/finalize-project/SKILL.md` | rewritten: preconditions drop `docs/plans/`; procedure steps 1–5 as below; run gate first |
| `contracts.yml` | the `docs/api/<pkg>.md` attribution claim rewritten: `all_of: ['finalize-project']`, `unless: ['surface section', 'the implementer']`; interface.md and section-README heading claims keep the documenter reader; §Project convention reader span updated |

## Specification

### `agents/documenter.md`

Frontmatter as today with the description: `Writes the human-facing documentation from the
shipped documents — each package's interface.md, section READMEs and contract, the repo
contract, the decisions ledger and the backlog. Package READMEs, the root README and
docs/index.md; Known gaps from status.py --repo plus what only a document check finds. Never
reads source to learn what the system does. Invoked by /dev-team:finalize-project.`

Headings: `## Hard rules`, `## Finding the documents`, `## Assembling`, `## Reading the
decisions ledger`, `## Known gaps`, `## Commit`, `## Memory`. **Known gaps** lists, in order:
the `status.py --repo` output; commands, paths or modules a document claims that do not exist
(`ls`/`grep` to confirm, never to learn); two sections declaring one env var with different
defaults; a shipped package with no `docs/api/<pkg>.md`; a README missing one of the seven
headings; unchecked `docs/followups.md` lines grouped by target (from the script's `backlog:`
group).

### `skills/finalize-project/SKILL.md`

Frontmatter as today, description: `Write the repo-level documentation from the shipped
documents - a README per package from its interface.md, section READMEs and contract, docs/
index.md, and the root README - and list everything still open from status.py --repo. Safe to
run early and often.` Body: Guard; run gate; step 1 find the documents; step 2 preserve
hand-written READMEs; step 3 package READMEs (sections as today minus **Consumers**' snapshot
label change: `interface.md`'s **Consumers (computed)** copied with its date); step 4
`docs/index.md` from the root README, `mkdocs build --strict` run and a failure listed under
Known gaps; step 5 root README (Packages table statuses from the script); commit (`docs`,
trailer `Dev-Team-Run: finalize-project`); return.

### `contracts.yml`

```yaml
  - name: the package API page is never credited to finalize-project alone
    # The surface section's implementer writes it as each package ships; finalize-project
    # lists a missing one under Known gaps and writes none.
    pattern: 'api/<pkg>\.md|api/\$pkg\.md|api/data\.md'
    near: 40
    all_of: ['finalize-project']
    unless: ['surface section', 'the implementer', 'Known gaps']
```

## Steps

1. `agents/documenter.md`.
2. `skills/finalize-project/SKILL.md`.
3. `contracts.yml`; plant a sentence crediting the package API page to `finalize-project`
   (the claim's pattern, without `Known gaps` nearby) in a scratch copy and watch it fail.
4. The plugin's own rules (no skill added or removed).
5. `check-contracts`; `build-site`.
6. Evals, through `run-evals`, logged with `log-eval`.
7. Commit: `dev-team remake (phase 09): documenter and finalize-project — Known gaps from status.py --repo`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 9.1 | mechanical | `contracts.yml` | — | `check-contracts` + the plant | all PASS; the plant FAILs |
| 9.2 | behavioral | `documenter` | previous | `evals/sets/documenter.json` 1, 2 (regression), 3 | evals 1–2 pass rate ≥ the 2026-09-20 log's; eval 3's every expectation passes for `with_skill` (the `--repo` lines appear verbatim under Known gaps; no `docs/api/` file is written; the conflicting default is reported) |
| 9.3 | load | `finalize-project` | — | `claude --plugin-dir ./dev-team -p "/dev-team:finalize-project"` in a `state-cases` `shipped` build | a root README with `Known gaps` is written and committed |

## Done when

- `grep -c 'synced.md\|assessment' agents/documenter.md skills/finalize-project/SKILL.md` is 0 on both.
- `grep -c 'status.py --repo' agents/documenter.md` ≥ 1.
- `check-contracts` all PASS; `build-site` exits 0.
- Logs for 9.1–9.3 in `evals/README.md`.
- The ledger row for phase 9 reads `done`.
