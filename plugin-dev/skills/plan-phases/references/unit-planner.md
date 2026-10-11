# The unit planner

`plan-phases` spawns one general-purpose subagent per phase, a level of the Phases table at a
time: every planner of one level in one message, the next level's only once the earlier
level's have returned. Each is given the prompt below with every `<…>` filled. Two phases of
one level cite no region of a file that is not shared, so planners of a level never describe
the same text; a planner of a later level reads the notes of the earlier phases on its files,
so it anchors on the text as those phases leave it.

The planner sees the spec, the overview, its own items and its own files, never the
discussion or the review. That is intended: what it cannot decide from the written spec is a
question for the user, returned, not a guess written into the note.

## The prompt

> You are writing the note for phase `<N>` (`<NN-name>`) of the `<plugin>` plan `<slug>`, in
> `<plugin dir>` on branch `<branch>`. The note is the plan one agent builds the phase from,
> later, in a fresh chat that reads nothing of this conversation. You edit no plugin file: you
> write one note.
>
> Read, in this order, and nothing else:
> 1. `python3 <plugin-dev>/scripts/phases.py brief <slug> --phase <N>`, run from
>    `<plugin dir>`: your phase's row, its eval rows and checks, the spec's **Goal**,
>    **Decisions taken** and **What must not break** (from `<slug>-edits.md`, which you never
>    open whole), your items whole with every line they cite as it stands now, and the other
>    phases on your files.
> 2. `<plugin dir>/site/notes/<slug>/<slug>-design.md`, when there is one, for the why.
> 3. The notes of the phases the brief lists under **Before this one**, each at
>    `<plugin dir>/site/notes/<slug>/<slug>-NN-<name>.md`. Their **Files** and
>    **Specification** say how your files will read when your phase runs; where one changes
>    text your item cites, anchor on the text as that note leaves it.
> 4. `<plugin-dev>/templates/phases/phase.md`, the shape of your note, and
>    `<plugin-dev>/skills/run-phase/references/example-phase.md`, a real one.
> 5. For each component kind your items add or change, its file in
>    `<plugin-dev>/skills/plugin-anatomy/references/` (`skills.md`, `agents.md`, `hooks.md`,
>    `mcp.md`, `manifest.md`, `other.md`): what the frontmatter may hold, how it is tested.
> 6. The files your phase owns (your row's **Files** cell), whole, as they are now; a shared
>    file only where your items add to it. No other phase's files, no other phase's items, no
>    findings file, no earlier conversation.
>
> Write `<plugin dir>/site/notes/<slug>/<slug>-<NN-name>.md` from the template, every
> section, in its order:
> - **Decisions**: everything the spec left to the phase and you settled — a module's name
>   and place, a rule's exact wording, the order of two edits, how an edge the item does not
>   mention is handled — each with its reason. A decision that is the user's (a default that
>   changes behavior, a choice between two designs the spec did not take, a rule that would
>   refuse what the plugin's own fixtures show a good run doing) is not settled here: write it
>   under Decisions as *asked: <the question>* with the options, the recommended one first,
>   and return it.
> - **Files**: one row per file; each is in your **Files** cell, a shared file, or a file this
>   phase creates. The Change cell names the section by its heading or by text quoted from
>   it, never by a line number.
> - **Specification**: the exact content. Every edit anchored on text quoted from the file as
>   it will stand when your phase runs (the file as it is now, as the earlier notes leave it),
>   long enough to be found once with `grep -nF`. Frontmatter verbatim; headings verbatim;
>   `contracts.yml` entries verbatim. For a hook or a script: the rules it enforces as a
>   table (input → exit code and message), and the fixture cases, each named as the item's
>   `fixture:` line names it, with its input and its expected result; add the cases the rules
>   need beyond those and mark them yours.
> - **Steps**: in the order that keeps the bundle consistent after each one.
> - **Evals**: the brief's rows, copied, every cell as printed. Loosen nothing.
> - **Done when**: conditions checkable without judgment.
>
> Then `python3 <plugin-dev>/scripts/phases.py notes-check <slug>`, from `<plugin dir>`, and
> fix every line that names your note; lines naming other notes are not yours. Write nothing
> but the note.
>
> Return four lines and nothing after them:
> ```
> Note: <path>
> Decisions: <n> settled · <n> asked
> Asked: <each question on one line — the question, its options, your recommendation> | none
> Gaps: <anything the spec or the overview did not say that you needed> | none
> ```

`plan-phases` runs `notes-check` over every note when a level has returned, then the unify
agent (`references/unify.md`) when every level has, then asks every *asked* question in one
round. A planner's **Gaps** line is a gap in the spec: asked about or reported per **Ask about
the gaps**, not guessed at.
