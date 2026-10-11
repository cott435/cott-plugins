# The unify agent

`plan-phases` spawns one general-purpose subagent once every phase's note is written, with the
prompt below and every `<…>` filled. The planners each saw one phase; this agent sees every
note, and makes them agree where they meet. It builds nothing and decides nothing that is the
user's: what it cannot settle it returns.

## The prompt

> You are the unify agent of the `<plugin>` plan `<slug>`, in `<plugin dir>` on branch
> `<branch>`. Every phase's note has been written, each by a planner that saw only its own
> phase. You make them agree where they meet. You edit notes and one table of the overview,
> and no other file.
>
> Read, in this order:
> 1. `<plugin dir>/site/notes/<slug>/<slug>-00-overview.md`: its **Phases** table and its
>    **Files other files parse** table.
> 2. Every note `<plugin dir>/site/notes/<slug>/<slug>-NN-<name>.md`, N from 1 up: its
>    **Decisions**, **Files** and **Specification** whole; its Steps, Evals and Done when
>    only where a check below needs them.
> 3. `python3 <plugin-dev>/scripts/phases.py notes-check <slug>`, run from `<plugin dir>`. It
>    prints `ok` before you start, and must again when you finish.
>
> Check, across the notes:
> - **Names.** A module, function, constant, heading, field, column, fixture case or
>   `contracts.yml` claim one note creates and another uses is spelled the same in both. The
>   creating note's spelling wins, unless the overview's **Files other files parse** gives
>   another; then the overview's.
> - **Shared files.** Two notes adding to one shared file (a README table, `hooks.json`,
>   `contracts.yml`, a fixture README) add rows that do not collide: not one row twice, not
>   two rows saying different things about one name; a table both extend keeps one column
>   order.
> - **Doubles.** A helper, a check or a rule two notes each invent for one job: the earlier
>   phase keeps it, the later note imports or cites it instead, and says so under Decisions.
> - **Anchors.** A later note anchoring on text an earlier note of the same file replaces or
>   removes: re-anchor the later note on the text as the earlier note leaves it.
> - **Asked.** Every *asked:* decision across the notes, collected; two notes asking one
>   question become one question.
>
> Edit the notes to agree — the smallest edit that does, named under the edited note's
> **Decisions** as *unify: <what, why>* — and add to the overview's **Files other files
> parse** every name two notes now share that the table lacks, with the phases that write and
> read it. Change no eval row, no pass bar, no **Items** cell, no **Files** cell, and nothing
> in the spec. Then `notes-check` again, until it prints `ok`.
>
> Return, and nothing after it:
> ```
> Changed: <one line per edit — the note, what, why> | none
> Asked: <every question, deduplicated, each with its options and the recommended one, and the phases that asked it> | none
> Unresolved: <a disagreement between two notes you could not settle without a decision that is the user's> | none
> ```

`plan-phases` asks every **Asked** and **Unresolved** line in one round, per its **The
notes** section, and writes each answer into the spec's **Decisions taken** and into the Decisions of the notes
that asked.
