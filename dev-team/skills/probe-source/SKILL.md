---
name: probe-source
description: Re-probe one external source for one consuming section after the world changed - an API changed, a dataset was refreshed - and extend docs/sources/{source}.md under that section's heading. An api - check the credential, read the official reference, call the read endpoints the section needs, and record the observed schema, pagination, limits, auth flow and error shapes with a scrubbed sample and a re-runnable probe. A dataset - record its columns, dtypes, missingness and duplicates, plus task fit when a modeling task is named, as statistics and never as records. /dev-team:run-package probes each new consuming section itself; adding a source after planning is a /dev-team:plan-package edit, not this.
argument-hint: "<pkg>/<section> | repo <source, optionally kind-prefixed> [purpose]"
arguments: [target, source]
context: fork
agent: dev-team:researcher
background: false
disable-model-invocation: true
---

Probe source **$source** for **$target** — **probe mode**.

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `researcher` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not probe in the main thread.

If `$target` reached you unsubstituted — literally the text `$target` — take the first token
of `$ARGUMENTS` as the target and the second as the source. Everything after the second token
is the purpose; it may be empty.

`$target` is the consuming section, `<pkg>/<section>`: the per-section heading this run
appends to the probe doc is the unit a probe serves. It may also be the literal `repo`: a
dataset probed before any package exists, which writes no section heading. A target with no
`/` that is not `repo` is a blocker — "name the consuming section as `<pkg>/<section>`".

## Why this runs

Nothing on disk sees an API change or a refreshed dataset, so the user types this. It is not
how a source gets probed the first time: `/dev-team:run-package` probes each consuming section
at its PROBE step, and `/dev-team:plan-repo` probes the brief's datasets. A source added after
planning is a `/dev-team:plan-package <pkg>` edit that puts it in a Sections row; the driver
probes it from there.

## Resolve the prompt

Your **Probe mode** section's **Inputs** are the fields a probe prompt carries. Nothing spawned
you, so resolve them here, from what exists, and a direct run matches a driver-spawned one.
With `$target` as `<pkg>/<section>`, `$pkg` below is its first half and `$section` its second.

- `Kind:` the prefix on `$source` if it carries one (`dataset:trades-2024` → `dataset`); else
  the prefix on this source's entry in `docs/packages/$pkg/contract.md`'s Sections table; else
  `api`.
- `Source:` `$source` with any prefix stripped, lowercase — the token the `source` column uses
  and the name the doc takes.
- `Purpose:` the argument text if given; else the `responsibility` of the `$section` row in
  `docs/packages/$pkg/contract.md`'s Sections table; else, when `$target` is `repo`, the
  brief's **Scope — now** row that names this source; else a blocker — "no purpose given and
  none on file".
- `Access:` for an api, the env var the repo contract's **Shared conventions** gives for this
  source; for a dataset, the location the repo contract or the brief gives for it; else
  `discover`.
- `Extracted skill:` `.claude/skills/<skill>/` for the `docs/legacy/inventory.md` row whose
  `skill` or `resource` names `$source`, else `none`.
- `Section:` `$target`.
- `Write to:` `docs/sources/$source.md`.

No `Run:` line: your commit trailer is `Dev-Team-Run: probe-source $ARGUMENTS`.

## Steps

1. **Run gate.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate`.
   FAIL → return `Result: blocked` with its lines, and write nothing.
2. **Probe.** Run your **Probe mode** procedure for the resolved kind, steps 1–7, extending
   the doc per **When the doc already exists** when it does. An access failure — a credential
   unset or rejected, a dataset missing or unreadable — still writes the doc, with **Access**
   filled and every later heading `not probed`, before returning the blocker.
3. **Commit** per your probe-run commit rule, trailer `Dev-Team-Run: probe-source $ARGUMENTS`.
4. **Return**, starting `Result: done` (or `Result: blocked` with the reason): access status,
   what was called or profiled, the discrepancy count, the path, `Commit: <sha>`. On a
   re-probe that changed the doc's shared headings, list every section whose Sections row
   names this source in its `source` column and has a design: `status.py` now reads each as
   DESIGN (a probe doc newer than its design), so the next `/dev-team:run-package <pkg>`
   redesigns it. A change to this section's own entry alone re-opens nothing else.

## Constraints

- Write only under `docs/sources/`: `$source.md`, plus `$source.sample.json` and
  `$source.probe.py` for an api, or `$source.stats.json` and `$source.profile.py` for a
  dataset. Never touch the contracts, the designs, or `packages/`.
- One source and one section per run.
- A re-probe never edits a contract or a design to match what it found. A changed source that
  a design can absorb is the designer's, reached through the re-opened DESIGN step; one that
  changes a boundary is a `spec-change` the loop routes, or a `/dev-team:plan-package <pkg>`
  edit. The return says which designs are affected, never how to fix them.
