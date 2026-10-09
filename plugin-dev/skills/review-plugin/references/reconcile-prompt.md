# The reconcile prompt

`review-plugin` spawns one general-purpose subagent, REC, after the last unit wave, with the
prompt below. REC is the only agent that reads every findings file, and the only writer of
the edit list. Its list is the spec `plan-phases` plans from, so whatever a unit found and
REC does not carry is lost; `edits.py check --findings` makes that visible.

## The prompt

> You are REC, the reconcile unit of a review of the `<P>` plugin, in `<plugin dir>` on
> branch `<branch>`. You edit no plugin file.
>
> Read, in this order:
> 1. `<plugin dir>/site/notes/<slug>/<slug>-review-plan.md`, whole.
> 2. `<plugin-dev>/templates/review/edits.md`: the exact shape of your output,
>    every section and every item field.
> 3. Every file under `<plugin dir>/site/notes/<slug>/findings/`, whole. Where a synthesis
>    unit and a wave-1 unit disagree on a rule its row made it the owner of, the synthesis
>    unit's view is the starting point: <the plan's precedence, e.g. "DET on every
>    mechanism, SKL on every skill cut">.
> 4. `<plugin dir>/audits/INDEX.md` <when the plugin has one>.
> 5. A plugin file only to settle a conflict two findings quote differently, at the lines
>    they quote.
>
> Write `<plugin dir>/site/notes/<slug>/<slug>-edits.md` from the template, keeping every
> `##` heading:
> - **Edits**: one item per edit, deduplicated: two findings on one rule are one item citing
>   both ids. Number them `E-001` up, in the order the template gives, so an item's
>   `depends:` ids are lower than its own. Every field filled; `none` where nothing applies.
>   An item that must land in two steps is two items, the second depending on the first.
> - **Decisions taken**: a row per choice that is the user's (a default that changes
>   behavior, a layout a user's project will see, a mechanism with a real cost either way),
>   Chosen `open`, the recommended alternative first, and the item's `decide:` naming it.
>   A choice the findings settle is not a decision: make it, under **Conflicts**.
> - **Needs a design**: items whose fix adds a new workflow, a new agent with its own loop,
>   or a new file two workflows meet at, whole, in the item format. Not under Edits. A hook,
>   a script flag or a record file inside a loop that already exists is an edit: give it its
>   exact behavior and a fixture under Edits.
> - **Build order**: layers bottom-up as lines of E-ids, each saying what it proves, then the
>   smallest slice that works end to end.
> - **Issues**: every open, recurred and wontfix id in the audit index, with its item or
>   `not addressed — <why>`.
> - Every finding id from every findings file appears somewhere: in an item's `findings:`,
>   in **Conflicts**, or in **Non-goals** with why it was dropped.
>
> Then run
> `python3 <plugin-dev>/scripts/edits.py check <plugin dir>/site/notes/<slug>/<slug>-edits.md --findings <plugin dir>/site/notes/<slug>/findings`
> and fix the list until it prints `ok` (open decisions are expected). Write nothing else.
>
> Return four lines and nothing after them:
> ```
> File: <path>
> Items: <n> (<count by mechanism>)
> Decisions: <D-ids, each with its question in five words>
> Needs a design: <E-ids | none>
> ```
