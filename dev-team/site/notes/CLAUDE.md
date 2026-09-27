# CLAUDE.md — site/notes

Rules for any chat working from the plan notes in this directory (a `run-phase` chat reads
them first, so this file loads before any phase does its work).


Spawn `run-evals` **executors** (`with_skill`, `old_skill`, `without_skill`) and **blind comparators** with
`model: "sonnet"` on the Agent tool. Spawn **graders** (including regrades) with
`model: "haiku"` instead — grading is closer to rubric/evidence-checking against a fixed
expectations list than open-ended agentic work, so it tolerates a smaller model. Keep both configurations of one
iteration on the same model so their pass rates compare, and name the model in the
`log-eval` entry's **Tested against** line.
