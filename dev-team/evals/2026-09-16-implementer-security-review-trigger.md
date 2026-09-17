# `implementer` — does it actually invoke `security-review`?

**Date:** 2026-09-16
**Subject:** `agents/implementer.md` Procedure step 3 ("Security"), and `skills/security-review/SKILL.md`
**Files touched by the fix:** `agents/implementer.md`
**Tested against:** commit not recorded at the time — added retroactively per `VERSIONING.md`.
The "before" run was against whatever `agents/implementer.md` looked like prior to this
file's own fix, which was itself never committed on its own; the "after" run was against the
patched wording below, also uncommitted as of this note. Model used for both the sandboxed
`claude -p --agent implementer` runs was also not recorded. This entry is the worked example
of the gap `VERSIONING.md` exists to close, not a clean instance of the new convention.

## What was tested

`implementer.md` instructs the agent to "invoke the `security-review` skill whenever any
condition in its own **When to Activate** section holds." The open question: when a section
plausibly matches one of those conditions, does the agent actually call the `Skill` tool and
read the checklist — or does it just write a security-sounding paragraph in its return
message from what it already knows, without ever opening the file?

Those two look identical in the final code most of the time, which is exactly the risk: a
paraphrase from memory drifts from the real checklist silently, and nothing in the output
signals that it happened.

## Method

The device's local `claude` CLI is disabled in this environment, so the test ran in an
isolated sandbox in the cloud workspace instead of on this machine. Built a throwaway
project directory with the real files — `.claude/agents/implementer.md` and
`.claude/skills/security-review/SKILL.md`, copied verbatim — and ran real, separate
`claude -p --agent implementer` sessions against it (`--dangerously-skip-permissions`,
`--effort low`, real API cost).

Eight tasks, told to skip the "no contract" blocking rule (there is intentionally no
`docs/` scaffold in a throwaway sandbox) but otherwise follow the Procedure normally,
including the Security step:

- 4 tasks that should trigger `security-review` per its own When to Activate list: a login
  endpoint (auth + DB), a third-party API ingest (secrets + outbound request), a pickle
  checkpoint loader (deserialization), a new HTTP export endpoint (API endpoint + input
  handling).
- 4 tasks that clearly should not: pure in-memory pandas transforms and type definitions,
  no I/O, no secrets, no external input of any kind.

For each run, checked the raw tool-call transcript (`--output-format stream-json`) for an
actual `Skill` tool call with `"skill":"security-review"` — not just whether the return
message *mentioned* security review.

## Results

**Before** (original wording — "invoke... and apply its checklist"):

| Case | Section | Should trigger? | Actually invoked? |
|---|---|---|---|
| 1 | `auth/login` | Yes | Yes |
| 2 | `data/ingest` (API key + outbound call) | Yes | **No** |
| 3 | `models/loader` (pickle deserialization) | Yes | Yes |
| 4 | `reporting/export_api` (new HTTP endpoint) | Yes | **No** |
| 5–8 | pure, no I/O (resample / format / types / indicators) | No | No (correct, all 4) |

2/4 positive cases actually called the tool. The other two (`data/ingest`,
`reporting/export_api`) wrote plausible, real mitigations in prose — but never opened the
skill, meaning those mitigations came from memory, not the checklist. All 4 negative cases
correctly stayed silent, confirming the frontmatter-description gate itself works fine; the
gap was specifically at the invoke-vs-paraphrase step, not at deciding whether security
applied at all.

Cost: ~$1.25 for the 8 runs.

## Fix

Rewrote `agents/implementer.md` Procedure step 3 to separate "decide if this applies" (cheap,
from the description alone) from "invoke the tool" (mandatory once it applies, named as its
own action), and to name the failure mode directly: a security paragraph in the return
message only counts if a `Skill` call for `security-review` actually happened first in that
run. Full text is in the file; see git history / the file itself for the current wording.

## Re-test

Same 8 prompts, same settings, against the patched agent.

| Case | Section | Should trigger? | Actually invoked? |
|---|---|---|---|
| 1 | `auth/login` | Yes | Yes |
| 2 | `data/ingest` | Yes | **Yes** |
| 3 | `models/loader` | Yes | Yes |
| 4 | `reporting/export_api` | Yes | **Yes** |
| 5–8 | pure, no I/O | No | No (all 4) |

Cost: ~$1.21 for the re-run.

## Verdict

**Fixed.** 8/8 correct after the patch (up from 6/8), with the two previously-missed cases
now showing a real `Skill(security-review)` tool call in the transcript, not just a sentence
claiming one happened. Caveat: n=8 on one pass each side; there's some run-to-run variance to
expect from a single sample, and this hasn't been re-checked at larger scale.
