# What reaches an agent's caller — the first `SubagentHandback`, and nothing after it

**Tested against:** `fa3e6a7` (`skills/plugin-anatomy/references/agents.md`, **What reaches its caller**, unchanged since `eda16c0` added it) · two recorded sessions, both Claude Code 2.1.284 in the desktop app (`entrypoint: claude-desktop`), models `claude-fable-5-1` and `claude-opus-5-5` · read by `claude-fable-5-1`, no model in the check itself · 2026-10-01
**Set:** none — a platform-fact check on existing transcripts, no new run · **Baseline:** — · **Pass rate:** the fact as written 0/2; the corrected fact 4/4

## What was tested

`agents.md` said that with a `SubagentHandback` tool the caller receives the agent's
**last** hand-back, and that an agent sent back to work by a stop hook "must hand back
again". Two later dev-team audits disagree with the second half:
`dev-team/evals/2026-09-30-audit-run-package-befb4798.md` (E11) and
`dev-team/evals/2026-10-01-audit-run-package-b05b2879.md` (E1). The question: which report
reaches the caller when an agent hands back and then goes on, and can it send a second one.

Assumed before reading, from the two audit logs: the first hand-back is the only one
delivered.

## Method

No new session. The two audited sessions' main transcripts and subagent transcripts
(`~/.claude/projects/-Users-connorott-PycharmProjects-wild-ones/<session>.jsonl` and
`<session>/subagents/agent-*.jsonl`) were read with a script, for:

- the Claude Code version and entrypoint on every record;
- how many Agent tool results say the report "is not repeated here";
- which record carries a hand-back's text to the driver;
- how many times `Result: blocked` and `let through after 3` occur anywhere in the main
  transcript (the outcomes the audits say the implementers ended on after their hand-back);
- per subagent, the number of `SubagentHandback` calls and any refusal text.

The audit reports themselves (`dev-team/evals/workspace/audit/<id>/report.md`, gitignored)
were read for the unit and step each finding cites.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| The Agent tool's result carries no report | every result defers to the hand-back message | befb4798: 28 of 28 results, b05b2879: 73 of 73, read "This agent's report was delivered to you as a message from "<agent id>" (its SubagentHandback call). Read it there; it is not repeated here." | ✅ |
| How the report arrives | as a message, not a tool result | a `queue-operation` record and a `queued_command` attachment per hand-back, framed as the subagent's words with no user authority, every line of the report indented | ✅ |
| A second `SubagentHandback` call in one run | refused | befb4798: one agent called it twice (the audit's U24, `Result: done` then `Result: blocked`); the second returned "Nothing was sent: your report was already delivered (SubagentHandback delivers one report)". b05b2879: no agent called it twice | ✅ |
| Text after the hand-back reaches the driver | it does not | `Result: blocked` and `let through after 3`: 0 occurrences in either main transcript, though three b05b2879 implementers (U43, U71, U40) and befb4798's U24 ended on one of them | ✅ |
| *The fact as written:* "the caller receives the last hand-back" | — | false where there were two: U24's second was refused, and the driver had the first (`Result: done`, `Gate: PASS`) | ✗ |
| *The fact as written:* such an agent "must hand back again" | — | it cannot: the tool delivers one report per run | ✗ |

Two things in the earlier logs do not survive the raw transcripts:

- The befb4798 report says the driver "learned of the block only because the agent repeated
  it as final text". The main transcript holds no `Result: blocked`. The driver's trace line
  `D104 ← U24 handed back: Result: blocked` was written by `audit-run`'s `trace.py`, whose
  `unit_return` takes a unit's **last** `SubagentHandback` call, here the refused one. The
  driver went on to spawn the reviewers without a question, which fits it never having seen
  the block.
- The 1493ed56 audit (2.1.281), which the old fact cited, saw nine implementers hand back
  before the gate's final stop and records no second hand-back. With one call per agent,
  "last" and "first" are the same call, so that run could not tell them apart.

## Verdict

The old fact is wrong in its second half and is corrected in `agents.md`, in the same
change as this log: with the tool, the caller receives the agent's **first** hand-back and
nothing after it; a second call is refused; later text, final text included, reaches nobody.
An outcome that can change after the hand-back has to be carried on disk, or the agent has
to hand back only when nothing after it can change the answer. `edge-cases.md` gains the
row.

Still unconfirmed, and marked so in `agents.md`: which sessions give subagents the tool
(seen in the desktop app on 2.1.281 and 2.1.284; a `claude -p` session on 2.1.270 returned
the last turn's text in the Agent tool's result, `dev-team/evals/2026-09-27-remake-platform-facts.md`
PF-1; later CLI versions and cloud sessions are untested); whether a subagent can reach its
caller after the hand-back by another route such as `SendMessage`; whether a caller that
continues an agent with `SendMessage` gets a second report. None of the three was run here.

Left for a separate change: `trace.py`'s `unit_return` should take the first
`SubagentHandback` call, since that is the one the driver received.
