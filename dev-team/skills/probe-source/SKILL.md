---
name: probe-source
description: Research one external source and write what it actually is to docs/sources/<source>.md. An api - check the credential, read the official reference, call the read endpoints the section needs, and record the observed schema, pagination, limits, auth flow and error shapes with a scrubbed sample and a re-runnable probe. A dataset - read it, and record its columns, dtypes, missingness and duplicates, plus its target, leakage, split and supported tasks when a modeling task is named, as statistics and never as records. /dev-team:plan-repo probes the datasets a brief names and /dev-team:plan-package probes every source in its Sections table; run this directly after an API changes, when a dataset is refreshed, or to add a source after planning.
argument-hint: "<pkg | repo> <source, optionally kind-prefixed> [purpose - what the section needs from it]"
arguments: [pkg, source]
context: fork
agent: researcher
background: false
disable-model-invocation: true
---

Probe source **$source** for **$pkg** — **probe mode**.

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `researcher` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not probe in the main thread.

If `$pkg` reached you unsubstituted — literally the text `$pkg` — take the first token of
`$ARGUMENTS` as the package and the second as the source. Everything after the second token is
the purpose; it may be empty.

`$pkg` is the package whose contract names this source, and it is what the purpose is resolved
from. It may also be the literal `repo`: a dataset probed before any package exists, which is
the sensible first move on a data-heavy or model-heavy brief.

## Resolve the prompt

Your **Probe mode** section defines the six fields a probe prompt carries. Nothing spawned
you, so resolve them here, from what exists, and a direct run matches an architect-spawned one:

- `Kind:` the prefix on `$source` if it carries one (`dataset:trades-2024` → `dataset`); else
  the prefix on this source's entry in `docs/packages/$pkg/contract.md`'s Sections table; else
  `api`. A bare token is an api, which is what every contract written before kinds existed
  contains.
- `Source:` `$source` with any prefix stripped, lowercase — the token the `source` column uses
  and the name the doc takes.
- `Purpose:` the argument text if given; else the `responsibility` of the row in
  `docs/packages/$pkg/contract.md`'s Sections table whose `source` names `$source`; else, when
  `$pkg` is `repo`, the brief's **Scope — now** row that names this source; else a blocker —
  "no purpose given and none on file". The purpose is what decides whether a dataset probe
  runs task fit, so a purpose naming a prediction, a classification or a forecast is worth
  passing explicitly.
- `Access:` for an api, the env var the repo contract's **Shared conventions** gives for this
  source; for a dataset, the location the repo contract or the brief gives for it; else
  `discover`.
- `Extracted skill:` `.claude/skills/<skill>/` for the `docs/legacy/inventory.md` row whose
  `skill` or `resource` names `$source`, else `none`.
- `Write to:` `docs/sources/$source.md`.

`docs/sources/` need not exist yet — create it. Nor need `docs/architecture.md`: probing
before planning is allowed, and on a data-heavy or model-heavy brief it is a sensible first
step. A probe doc is repo-wide, so a source two packages consume is probed once and read
twice.

## Steps

Run your **Probe mode** procedure for the resolved kind, steps 1–7. An access failure — a
credential unset or rejected, a dataset missing or unreadable — still writes the doc, with
**Access** filled and every later heading `not probed`, before returning the blocker.

## Constraints

- Write only under `docs/sources/`: `$source.md`, plus `$source.sample.json` and
  `$source.probe.py` for an api, or `$source.stats.json` and `$source.profile.py` for a
  dataset. Never touch the contracts, the designs, or `packages/`.
- One source per run. Several are several runs — or one `/dev-team:plan-package $pkg`, which
  probes every source in its Sections table in parallel.
- A re-probe rewrites the doc with today's date and a filled **Changes since last probe**. It
  never edits a contract or a design to match what it found: a changed API or a refreshed
  dataset that breaks a plan is `/dev-team:plan-change`'s to absorb, and the return says so.
