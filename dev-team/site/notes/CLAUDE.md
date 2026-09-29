# CLAUDE.md — site/notes

Rules for any chat working from the plan notes in this directory (a `run-phase` chat reads
them first, so this file loads before any phase does its work).


Spawn `run-evals` **executors** (`with_skill`, `old_skill`, `without_skill`), **blind comparators**, and **graders** with
`model: "opus"` (Claude Opus 5.5) on the Agent tool. Keep both configurations of one
iteration on the same model so their pass rates compare, and name the model in the
`log-eval` entry's **Tested against** line.
