# CLAUDE.md — site/notes

Rules for any chat working from the plan notes in this directory (a `run-phase` chat reads
them first, so this file loads before any phase does its work).

## Evals run on Sonnet

Every eval-related agent runs with `model: "sonnet"` on the Agent tool — `run-evals`
executors (`with_skill`, `old_skill`, `without_skill`), graders, blind comparators, and any
regrade or rerun. Never the inherited session model. Keep both configurations of one
iteration on the same model so their pass rates compare, and name the model in the
`log-eval` entry's **Tested against** line.

Set by the user on 2026-09-27, during phase 3 of the remake plan.
