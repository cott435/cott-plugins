# D — review freshness by commit; every run commits exactly what it wrote

**Tested against:** uncommitted — see working-tree diff (phase 2 of the 0.5 overhaul, on top of
`1b5b5f9`): `skills/status/scripts/status.py`, `skills/git-workflow-and-versioning/SKILL.md`,
`agents/{implementer,reviewer,architect,researcher,curator,documenter,designer}.md`, the twelve
forked skills' last step, `contracts.yml` · model: `claude-sonnet-5` (the CLI default in the
headless runs; every agent on `inherit`) for the behavioral part; `claude-opus-5` ran the
mechanical script · Claude Code `2.1.270` · 2026-09-18

## What was tested

Note 09 eval D, two claims:

- **Mechanical.** `status.py`'s reviewed-since-build column comes from commits: a review counts
  only with a `Commit:` line and no commit touching the section since that sha; changes git
  does not hold read as `uncommitted` and fail the gate; nothing reads an mtime.
- **Behavioral.** After one `implement-section` run on the fixture, `git show --stat HEAD` is
  exactly the implementer's paths and `git log -1 --format=%B` carries
  `Dev-Team-Run: implement-section data/ingest`.

## Method

**Mechanical**: a scripted fixture repo (`evals/fixtures/two-package/reset.sh --no-constraints`,
then a hand-written `docs/architecture.md`, a three-section `contract.md`, and stub files),
with `status.py data --gate` run at seven states. Plus `grep -c st_mtime status.py`. No model
cost.

**Behavioral**: real headless runs, `claude -p "<command>" --plugin-dir ./dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`, in a fresh
`reset.sh --no-constraints` copy on branch `build`, one run per step. Evidence comes from git
itself and the subagent transcripts (every `Bash`/`Skill` call), not from the models' summaries.

| Run | Command | Cost |
|---|---|---|
| 1 | `/dev-team:plan-repo` (first wording, discarded with its copy) | $0.79 |
| 1b | `/dev-team:plan-repo` (after the fixes below, fresh copy) | $0.72 |
| 2 | `/dev-team:plan-package data` | $1.38 |
| 3 | `/dev-team:implement-section data/ingest` | $2.78 |

## Results

Mechanical:

| State | Expected | Observed | Pass |
|---|---|---|---|
| 1 — `ingest` built, never committed | `uncommitted`; gate `data/ingest: uncommitted changes` | exactly that | ✅ |
| 2 — committed; newest review is 0.4-style, no `Commit:` | `· <date> approve @—`; gate fails not-reviewed | exactly that | ✅ |
| 3 — `clean` committed *after* `ingest`, then `ingest` reviewed at `HEAD` (so `Commit:` ≠ `ingest`'s last commit), report committed | `✓ … @<sha>` | `✓ 2026-09-18 approve @…`; gate names only `clean`/`storage` | ✅ |
| 4 — `ingest` source changed and committed after the review | `·`; gate fails | `·`; `data/ingest: not reviewed since last build` | ✅ |
| 5 — `ingest` unit test edited, uncommitted | `uncommitted` | `uncommitted` | ✅ |
| 6 — `Commit:` names a sha not in history | `·` | `·` | ✅ |
| 7 — `.git` removed | `·`, no crash | `·` | ✅ |
| `grep -c st_mtime status.py` | 0 | 0 | ✅ |

State 3 is why the rule is "no commit since", not the note's "equals": under equality it
would read `·` forever (note 02 §Deviations).

Behavioral:

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 1 — architect commits `plan-repo` | one commit, trailer | **no commit**; the architect never called `git-workflow-and-versioning` and returned after `plan-repo`'s step 6 "Return"; its files were left untracked | ❌ |
| 1 — researcher spawned by the architect | does not commit | **committed** its probe (`Dev-Team-Run: probe-source trades`), reading "run directly by probe-source" as its own case | ❌ |
| 1 — `.claude/agent-memory/` | — | left untracked by the researcher after its commit; this would fail the next run's baseline | finding |
| 1b — after the fixes: architect | one commit, `plan repo: …`, trailer `Dev-Team-Run: plan-repo`, all six files it and the researcher wrote | exactly that (`b0fa1b5`); tree clean | ✅ |
| 1b — researcher | no commit | no commit | ✅ |
| 2 — `plan-package data` completes and commits | one commit | **incomplete**: the forked architect spawned its three designers in the background and ended its turn (`echo waiting`); the designers' completion notices went to the *main* thread, which improvised a reconciliation — no `integration.md`, no `surface.md`, no commit. Predates phase 2; not fixed here (see Verdict). **Manual intervention:** the contract, three designs and `decisions.md` were committed by hand (`9a9c16b`) so step 3 could run | ⚠ out of scope |
| 3 — implementer checks branch and baseline first | `git branch --show-current`, `git status --porcelain` before writing | both, first Bash call after reading; `.claude/` untracked was accepted as exempt | ✅ |
| 3 — staging by explicit path | no `-A`, `.`, `-a` | `git add pyproject.toml mkdocs.yml docs/index.md .gitignore uv.lock packages/ docs/decisions.md docs/followups.md` (the one directory, `packages/`, held only files this first-section run wrote) | ✅ |
| 3 — `git show --stat HEAD` = the paths the return lists | equal | 28 files: scaffold (root `pyproject.toml`, `uv.lock`, `mkdocs.yml`, `docs/index.md`, `.gitignore`, `packages/data/pyproject.toml`, `__init__.py`, `configs.py`), section source and README, `conftest.py`, 12 fixtures, the unit test, `decisions.md`, `followups.md`; the return lists the same set, and `git status` afterwards shows only `.claude/` | ✅ |
| 3 — message | `data/ingest: …` ≤ 72 chars; trailer | `data/ingest: read and validate the trades CSV` / `Dev-Team-Run: implement-section data/ingest`; return ends `Commit: c83e8b3…` | ✅ |
| 3 — `status.py` on the real repo | `ingest` built, `·` unreviewed | `ingest ✓ ✓ · — @—`, one `TODO(decision` marker; gate names `ingest` not reviewed | ✅ |

## Verdict

**Mechanical: holds.** **Behavioral: failed on first run, fixed, holds on re-run** for the
implementer and the architect's `plan-repo`. The fixes, all recorded in note 02 §Deviations:
each forked skill's last step now reads "commit per your **Commit** section — trailer
`Dev-Team-Run: <skill> $ARGUMENTS` — then return"; the architect's Hard rules name the
start check and the final commit; the researcher commits only on an explicit `Commit: yes`,
which only `probe-source` sets; §Project convention's baseline exempts `.claude/agent-memory/`.
Run 1b confirmed the architect and researcher fixes on a fresh copy; run 3 confirmed the
implementer end to end.

Not covered: the reviewer's commit and `Commit:` line in a real run (the mechanical states
use hand-written reports), and the architect's commit at package scope, which run 2 could not
reach. Both are exercised again in later phases' evals on this fixture. The background-designer
failure in run 2 is a pre-existing headless-mode defect in the architect's delegation, filed
as a separate task rather than fixed in this phase.

**Follow-up:** [2026-09-18-d2-foreground-fanout.md](2026-09-18-d2-foreground-fanout.md) found
the root cause behind run 1 as well. Each skill's bare `agent: architect` forked as
general-purpose, so the architect's own prompt, including its **Commit** section, was never
loaded. The skills now say `agent: dev-team:<name>`. The "commit, then return" skill steps
added above may be redundant with that fix; note 02 §Deviations says so.
