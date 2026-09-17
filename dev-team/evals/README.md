# Evals

Ad hoc tests run against this plugin's own skills and agents — not the automated
skill-creator benchmark loop (that produces its own workspace under a skill's own
`<skill-name>-workspace/`), but targeted checks of one specific behavioral claim: does an
agent actually invoke a skill when it should, does a patched instruction change behavior, does
a description trigger correctly, and so on.

## Convention

The convention is the `log-eval` skill in the `plugin-dev` plugin, shared by every plugin
repo: one file per test run named `<date>-<subject>.md`, the required **Tested against**
commit and model fields, what each section must contain, and the rule that the entry is
written before results are reported back. Read it before adding an entry.

Two things it insists on, because they are the ones that get skipped:

- A clean pass is recorded exactly like a failure. The record is about whether the claim was
  ever checked, not about whether the news was good.
- The commit SHA is the commit of the file(s) under test *as of when the test ran*
  (`git log -1 --format=%h -- <path>`), and the model is what actually ran it — `inherit`
  resolves to something specific, and that is what the result is about.

## Index

| Date | Subject | File | Commit | Verdict |
|---|---|---|---|---|
| 2026-09-16 | `implementer` — does it actually *invoke* `security-review` (not just reason about it from memory) when a section matches its When to Activate conditions | [2026-09-16-implementer-security-review-trigger.md](2026-09-16-implementer-security-review-trigger.md) | uncommitted at test time | Gap found (2/4 positive cases actually invoked the tool) and fixed by rewriting the agent's Security step; re-run confirmed 4/4 |
