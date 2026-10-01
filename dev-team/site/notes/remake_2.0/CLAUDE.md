# CLAUDE.md — site/notes

Rules for any chat working from the plan notes in this directory (a `run-phase` chat reads
them first, so this file loads before any phase does its work).


Spawn `run-evals` **executors** (`with_skill`, `old_skill`, `without_skill`) with
`model: "opus"` (Claude Opus 5.5) on the Agent tool, and every agent that reviews their
output — **graders** and **blind comparators** — with `model: "sonnet"` (Claude Sonnet 5.5),
per the user (2026-09-29). Keep both configurations of one iteration on the same models so
their pass rates compare, and name both models in the `log-eval` entry's **Tested against**
line.

A headless session (`claude -p`) names the model in full: `--model claude-sonnet-5-5` for
Claude Sonnet 5.5. `--model sonnet` in CLI 2.1.283 resolves to `claude-sonnet-5` (Sonnet 5),
not Sonnet 5.5; the Agent tool's `model: "sonnet"` is Sonnet 5.5.
