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
| 2026-09-17 | `documenter` — does every `interface.md` heading it is told to expect exist in the template the implementer owns | [2026-09-17-documenter-interface-heading-contract.md](2026-09-17-documenter-interface-heading-contract.md) | `259785a` (fix uncommitted) | Claim fails on 2 of 7 headings (`Scripts`, `Consumers`) — never written anywhere in the plugin; fixed in `documenter.md`. Mechanical check only: no agent run was possible (`claude` CLI disabled in the session), so the behavioral impact stays unverified |
| 2026-09-17 | cross-file contract sweep — headings a reader parses, the `scripts/` prohibition, the `docs/api/<pkg>.md` writer | [2026-09-17-cross-file-contract-sweep.md](2026-09-17-cross-file-contract-sweep.md) | `e4bedca` / `259785a` / `0604620` (fixes uncommitted) | 2 of 3 claims false before (4 stale `scripts` mentions, 2 wrong `docs/api` attributions), all 3 pass after. Heading check passed before, confirming the 0.2.1 documenter fix holds. Mechanical: no agent run was possible |
| 2026-09-18 | probe doc headings — is every heading the four readers of a probe doc name one the template actually defines, after `probe-source` split into `api` and `dataset` kinds | [2026-09-18-probe-doc-headings-claim.md](2026-09-18-probe-doc-headings-claim.md) | `d23232c` (change uncommitted) | Claim fails on its own owner while the template is a fenced `##` block — `check_headings` only reads numbered bolded items — and passes once the two templates move to `planning-templates/references/source-probe.md` in that form. 9/9 claims pass. Mechanical: no agent run |
| 2026-09-18 | platform facts for 0.5 (evals A, B) — which `subagent_type` form a plugin skill's Agent call resolves, and whether `${CLAUDE_PLUGIN_ROOT}` is substituted in a skill body and an agent body | [2026-09-18-platform-facts.md](2026-09-18-platform-facts.md) | `3127526` | Both hold: `dev-team:<agent>` resolves, bare `reviewer` errors ("Agent type 'reviewer' not found"); the variable is substituted to an absolute path in both bodies. Real headless runs, `claude-sonnet-5`, Claude Code 2.1.270 |
| 2026-09-18 | vendored skills (0.5 eval C) — no `agent-skills` skill adapted in phase 1 still carries JS-stack text or `CONSTRAINTS.md` | [2026-09-18-c-vendored-skills-js-stack-grep.md](2026-09-18-c-vendored-skills-js-stack-grep.md) | uncommitted at test time (phase 1 commit) | Holds: 0 hits in all three adapted files; positive control hits 3–25 lines per upstream original. Mechanical; re-run over the fourth file in phase 6 |
| 2026-09-18 | commit per run (0.5 eval D) — `status.py` review freshness is commit-based; each run commits exactly what it wrote, with the `Dev-Team-Run:` trailer | [2026-09-18-d-commit-per-run.md](2026-09-18-d-commit-per-run.md) | uncommitted at test time (phase 2 commit) | Mechanical holds (7 states). Behavioral failed first: the architect never committed and a spawned researcher did. Fixed by adding commit-then-return to each forked skill's last step and a `Commit: yes` marker for direct probes; the re-run holds for `plan-repo` and `implement-section`. `plan-package` did not complete headless: designers were backgrounded, a pre-existing bug filed separately. Its commit was made by hand |
| 2026-09-18 | foreground fan-out (0.5 eval D follow-up) — does a forked architect get its designers back in the same turn and finish `plan-package` headless | [2026-09-18-d2-foreground-fanout.md](2026-09-18-d2-foreground-fanout.md) | `9fc74a3` (fix uncommitted, phase 2) | Failed first even with the `run_in_background: false` Hard rule: bare `agent: architect` silently forks as general-purpose, so the architect prompt never loads. With `agent: dev-team:<name>` on all 12 skills plus the flag, it holds: 3 designers in one message run in parallel, and the fork writes integration + surface and commits (`f5c7393`). Main-thread tool calls 0. Real headless runs, `claude-sonnet-5` |
