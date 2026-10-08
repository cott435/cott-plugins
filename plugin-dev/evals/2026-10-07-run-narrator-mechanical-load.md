# run-narrator phase 8 — the narration check in `flow.py` (M8.1), the agent's frontmatter in the contract sweep (M8.2), and the agent registers (L8.1)

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `dd6af0f`): `skills/run-flow/scripts/flow.py`, `agents/run-narrator.md` · model: none for M8.1 and M8.2 (scripts, checked by script); L8.1 `claude -p` on the CLI's default model, Claude Code 2.1.283 · 2026-10-07
**Set:** none — M8.1, M8.2 and L8.1 are rows of `site/notes/0.16-audit-ledger-08-run-narrator.md` **Evals** with no set · **Iteration:** none, run in the phase chat (harness `evals/workspace/run-narrator/m8.sh`, output `m8.out`, sweep output `m82.out`, gitignored) · **Baseline:** none · **Pass rate:** M8.1 13/13 · M8.2 11/11 · L8.1 1/1

## What was tested

That a unit page shows `explain/U<nn>.md` above **Prompt** under **What it did**, links each
line's step range to the step anchors, drops a line that cites a step the unit does not have or
starts with no range (and says how many), marks the account out of date when its header's step
count is not the unit's, and that the units table's **Narrated** column says `stale`, `yes` or
`—`; that `agents/run-narrator.md`'s frontmatter uses only documented agent keys; and that the
agent registers when the plugin is loaded from its working copy.

## Method

- **M8.1**: one bash harness, every check a string comparison. The planted fixture
  (`evals/fixtures/audit-run/make_session.py` into a `mktemp -d`, session `0a0d17f0`, one
  `toy:writer` unit U01 of 8 steps) is built with `trace.py build`. A hand-written
  `explain/U01.md` with header `steps 1–99` and lines `S1–S2 · a`, `S3 · b`, `S40 · c`,
  `no range here` is rendered with `trace.py flow $WS`; then the header is corrected to
  `steps 1–8` with the same lines; then the file is removed.
- **M8.2**: `python3 scripts/contract_sweep.py` on the working tree.
- **L8.1**: `claude --plugin-dir ./plugin-dev -p "List the agents you have from plugin-dev"`
  from the repo root.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M8.1a | `units/U01.html` says `Narration out of date: written for 99 steps` | `Narration out of date: written for 99 steps, the unit now has 8.` | ✓ |
| M8.1b | … and `2 line(s) dropped` | `2 line(s) dropped: they cite steps this unit does not have.` | ✓ |
| M8.1c | line `a` with links to `#S1` and `#S2` | `<a href="#S1">S1</a>–<a href="#S2">S2</a> · a` | ✓ |
| M8.1d | line `b` with a link to `#S3` | `<a href="#S3">S3</a> · b` | ✓ |
| M8.1e | the `S40` line and the line with no range are not shown | neither on the page | ✓ |
| M8.1f | the block is headed **What it did** and sits above **Prompt** | yes | ✓ |
| M8.1g | the units table's **Narrated** for U01 says `stale` | `stale` | ✓ |
| M8.1h | the anchors the links point at exist | `id="S1"` … `id="S8"` | ✓ |
| M8.1i | header corrected to `steps 1–8`: no out-of-date mark | none | ✓ |
| M8.1j | … **Narrated** says `yes` | `yes` | ✓ |
| M8.1k | … the two bad lines are still dropped | `2 line(s) dropped` | ✓ |
| M8.1l | no explain file: no **What it did** block | none | ✓ |
| M8.1m | … **Narrated** says `—` | `—` | ✓ |
| M8.2 | `check-contracts` all PASS, the agent frontmatter claim over both agents | 11/11 PASS; `every agent's frontmatter uses only documented agent fields, none plugins ignore — 2 files, every key documented` | ✓ |
| L8.1 | the reply names `run-narrator` | a table of two agents, `plugin-dev:run-auditor` and `plugin-dev:run-narrator` ("Writes a short plain-English account of what one spawned agent did in a traced run … Tools: Read, Write") | ✓ |

## Verdict

Held: M8.1 13/13, M8.2 11/11, L8.1 names `run-narrator`. `model: claude-sonnet-5-5` is a full
id, not a dated pin; L8.1 does not show which model a spawned narrator ran on, which the
behavioral log records from its transcripts' proxy runs instead.
