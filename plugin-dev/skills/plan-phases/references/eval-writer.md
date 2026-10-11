# The eval writer

`plan-phases` spawns one general-purpose subagent per target that has a behavioral row in the
overview's **Evals by phase** table, all in one message. Each writer is given the prompt below with every `<…>` filled
in. One writer owns one set file, so parallel writers never touch the same file.

The writer sees the spec and the overview, never the discussion or the review. That is
intended: an expectation a writer cannot derive from the written spec tests something the
spec never said, and the writer reports it instead of inventing it.

## The prompt

> You are writing the committed eval set for one target of a plugin plan. Target: `<target>`,
> at `<target_path>` (it may not exist yet; the phase that creates it runs these evals).
> Plugin directory: `<plugin dir>`. Mode for this target: `<new target | changed target>`.
>
> Read, in this order and nothing else:
> 1. The approved spec: `<plugin dir>/site/notes/<slug>/<slug>-design.md` in full, and/or,
>    for an edit list, the items that name this target, printed by
>    `python3 <plugin-dev>/scripts/edits.py show <plugin dir>/site/notes/<slug>/<slug>-edits.md <ids>`
>    (`<the ids of the items whose evals: line names this target>`).
> 2. `<plugin dir>/site/notes/<slug>/<slug>-00-overview.md`: the Phases rows of the phases
>    below, and the **Evals by phase** rows for this target, which name these eval IDs:
>    `<IDs, with each row's phase, baseline and pass bar>`.
> 3. `<plugin-dev>/skills/run-evals/references/eval-kinds.md`, for what a behavioral eval is.
> 4. `<plugin-dev>/skills/run-evals/SKILL.md`, section **The set**, for the set's JSON
>    shape, and `<plugin-dev>/skills/run-evals/references/prompts.md`, **Executor**, for the
>    prompt your evals will be run with.
> 5. `<plugin-dev>/skills/plugin-anatomy/references/<the target's component file>`, its
>    **How to test it** section: what can be observed about this kind of component, and
>    what a general-purpose executor cannot reproduce (an agent's `tools:` and `skills:`).
> 6. `<existing set path, or "none">`: for a changed target, keep every eval in it, and
>    append yours after the highest existing ID.
>
> Write `<plugin dir>/evals/sets/<target>.json` containing exactly the eval IDs above. For
> each eval:
> - `prompt` is what a user would type to start the target, with realistic names and
>   arguments.
> - `harness` is required when the target asks the user anything. Write it under
>   `<plugin dir>/evals/sets/files/<target>/`: a seed line, then the user's answers as a
>   list. The answers are facts a user would state, not the design the target should arrive
>   at. An answer that names the loop or agent the eval checks for makes the eval pass for
>   the wrong reason. When the eval must run past an approval point, add a section saying
>   what to approve and where to write the files the target would commit, under `outputs/`.
> - `expected_output` is one sentence a reviewer can hold the output against.
> - `expectations` are statements a grader can check in `outputs/` or `transcript.md`: a file
>   exists, a heading is present, a count is under a limit, a component reads a named file,
>   the chat message does or does not do something. Derive each from what the spec and the
>   overview say the target must do. At least one per eval must be something the row's baseline
>   would fail; name which in your reply.
> - `added_in` is `"<slug> phase 0, run from phase N"`.
>
> Then run `python3 <plugin-dev>/skills/run-evals/scripts/eval_workspace.py validate
> <plugin dir>/evals/sets/<target>.json` and fix the set until it exits 0.
>
> Write nothing but that set file and its harness sheets. Reply with: the eval IDs written;
> for each, the expectation the baseline should fail; and anything the spec or the overview
> did not say clearly enough to write an expectation for, as a list.

`plan-phases` checks each set against **The eval sets** in its `SKILL.md` before committing.
A writer's list of what the spec did not say is a gap: it is asked about or reported per
**Ask about the gaps**, not guessed at.
