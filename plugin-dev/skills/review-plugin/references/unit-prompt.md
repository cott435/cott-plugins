# The unit prompt

`review-plugin` spawns one general-purpose subagent per unit of a wave, all in one message,
each given the prompt below with every `<…>` filled from the unit's row in the review plan.
One unit owns one findings file, so units in a wave never write the same file.

The unit reads the plan's charge and its own row, and not the conversation that wrote them.
That is intended: what the unit needs to know is in the plan, or the plan has a gap that the
unit reports in its return.

## The prompt

> You are unit `<UNIT>` of a review of the `<P>` plugin, in `<plugin dir>` on branch
> `<branch>`. You read; you do not run the plugin and you edit no plugin file.
>
> Read, in this order:
> 1. `<plugin dir>/site/notes/<slug>/<slug>-review-plan.md` §1 to §6: the goal, where things
>    are written, the brief, the checks, the finding format.
> 2. `<plugin-dev>/templates/review/findings.md`: the exact shape of your file.
> 3. Your row, in §7 or §8 of the plan: `<the row, verbatim>`.
> 4. Every file your row lists under Reads whole, with the Read tool, whole; the sections
>    your row lists under Reads in part; the issues it names under `audits/issues/`.
>    <Wave 2 and later: the findings files or kinds your row names, under
>    `site/notes/<slug>/findings/`.>
>
> Do the checks in §5 in order, over what you read, with the emphasis your row gives. Quote
> every line you cite as `path:line` from the files as they are now.
>
> Write exactly `<plugin dir>/site/notes/<slug>/findings/<UNIT>.md`, in the template's shape,
> ids `F-<UNIT>-<nn>`, ERROR first. Then run
> `python3 <plugin-dev>/scripts/edits.py findings <plugin dir>/site/notes/<slug>/findings`
> and fix every `FAIL` line that names your file. Write nothing else.
>
> Return three lines and nothing after them:
> ```
> File: <path>
> Findings: <n> (<count by kind>)
> Top: <your three highest-value finding ids> | Gaps: <anything the plan did not say that you needed, or none>
> ```
