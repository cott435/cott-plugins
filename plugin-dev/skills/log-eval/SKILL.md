---
name: log-eval
description: Record a test run against a plugin's own skills or agents as a dated file under evals/ with the commit and model it was tested against, and add its row to the index. Use only in a plugin repo (one containing .claude-plugin/plugin.json), every time a triggering check, before/after comparison, or behavioral probe is run against that plugin — including when it passes cleanly.
---

# Recording an eval

An eval entry is a claim about one specific prompt's behavior. The prompt keeps changing, so
every entry has to record exactly which version of it was tested — otherwise a later edit to
the same agent silently invalidates a "confirmed" result with nothing to flag it.

This covers ad hoc tests against a plugin's own skills and agents: does an agent actually
invoke a skill when it should, does a patched instruction change behavior, does a description
trigger correctly. It is not the automated skill-creator benchmark loop, which produces its
own workspace under a skill's `<skill-name>-workspace/`.

## When

Every time, not only when the result is surprising or someone asks for a writeup. A clean
pass is exactly as worth recording as a failure: the record is what lets a later question
about the same claim be answered by reading a file instead of rerunning the whole test. This
applies regardless of how the test was run — the skill-creator eval loop, a hand-built
subagent harness, or a live command against a real repo.

Write the entry **before** reporting results back, not after. A test that exists only in a
conversation transcript is a test nobody can check later, and the next person to doubt the
same claim has to redo the whole thing from scratch.

## Where

One file per test run: `evals/<date>-<subject>.md`, most specific subject first — e.g.
`evals/2026-09-16-implementer-security-review-trigger.md`. Then add a row to the index table
at the bottom of `evals/README.md`. Both, in the same commit.

## What every entry records

- **Tested against** — the short commit SHA of the file(s) under test, *as of when the test
  ran* (`git log -1 --format=%h -- <path>`), plus the model that actually ran it. Not what
  the frontmatter says: `inherit` resolves to something specific at run time, and that
  specific thing is what the result is about. If the change under test isn't committed yet,
  write "uncommitted — see working-tree diff" rather than leaving it implied.
- **What was tested** — the specific behavioral claim, in one or two sentences.
- **Method** — how the test was actually run: real runs vs. a proxy, sample size, what was
  held constant, what varied, real API cost incurred if any.
- **Results** — a table when there are multiple cases; pass/fail per case, not just an
  overall impression.
- **Verdict** — did the claim hold. If not, what was changed in response, and whether a
  re-run on the same cases confirmed the fix.

## Template

```markdown
# <subject>

**Tested against:** `<sha>` (`<path>`) · model: `<model that ran it>` · <date>

## What was tested

<the claim, in one or two sentences>

## Method

<real runs or proxy, sample size, what was held constant, what varied, cost>

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|

## Verdict

<did the claim hold; what changed if not; whether a re-run confirmed the fix>
```

## Relationship to versioning

The commit field is the link between an eval and `bump-version`. If an agent under active
eval has its `model:` pinned to a dated ID, say so in the entry — that pin exists so a model
upgrade can't be mistaken for a prompt regression.
