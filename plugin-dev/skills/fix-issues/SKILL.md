---
name: fix-issues
description: Fix a few of the issues an audit filed in a plugin's committed ledger (runs/audits/issues/) from any chat - select them by id, by run, or as open or recurred; stop and name revise-plugin when a script says the selection is too many issues or too many roles for one chat; plan one edit per issue and get a yes; make the edits on a worktree branch; run check-contracts, build-site and run-evals against the plugin's last tag; record a Fix attempt with a Verify line in each issue; then propose the merge to main and the bump. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) that has an runs/audits/ directory. It never marks an issue verified - only an audit of a rerun can.
argument-hint: "[<ID> ... | run:<id8> | open | recurred] [--here]"
disable-model-invocation: true
---

# Fixing audited issues

`/plugin-dev:audit-run` writes what went wrong in a run as issues under the plugin's
`runs/audits/issues/`, each with an id that stays the same from one audit to the next. This skill
is how those issues get fixed, from any chat: it plans one edit per issue, gets one yes,
makes the edits on a worktree branch, proves them with the plugin's own checks and evals,
and records in each issue what changed and how a rerun will show whether it held. That
record is what the next audit of a rerun checks, so it is written for that audit to read.

It is the small end of one route. A change that starts from facts about a plugin (issues,
eval logs, contradictions) is planned here when it is a handful of edits one chat can read
and make, and by `/plugin-dev:revise-plugin` when it is not: that skill reads each role
whole in its own agent and writes an edit list `plan-phases` splits into phases, and the
last phase records the same Fix attempts this skill does. Which of the two a selection
belongs to is `issues.py route`'s answer (§1), not this chat's.

`I` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/issues.py`, run from the plugin's own
directory (or with `--dir <plugin directory>`). It is the only writer of issue files and of
`runs/audits/INDEX.md`; `${CLAUDE_PLUGIN_ROOT}/templates/audits/issue.md` is the shape of what it
writes.

## 1. The plugin and the selection

1. Read `.claude-plugin/plugin.json`. Its `name` is **P**. With no manifest, stop: this
   skill runs inside the plugin whose issues they are. With no `runs/audits/` directory, say the
   plugin has no ledger yet (an audit with `/plugin-dev:audit-run` makes one) and stop.
2. The selection, from the arguments:
   - issue ids (`DT-004 DT-011`): those, as given;
   - `run:<id8>`: `I list --session <id8>`, the issues that audit found or saw again;
   - `open`, the default with no argument: `I list --status open,recurred`, since an issue
     whose fix recurred is open again;
   - `recurred`: `I list --status recurred`.
3. Show the selection as a table: id, status, severity, fault, title. Nothing selected: say
   so and stop.
4. **The route.** Run `I route` with the same selection: the ids, or `--session <id8>`, or
   `--status open,recurred`, or `--status recurred`. It prints one line and exits 0 or 3.
   - Exit 0, `route: fix-issues`: go on to §2.
   - Exit 3, `route: revise-plugin`, with the reason: more than six issues, more than three
     issues across more than three roles, or an issue that recurred after two fixes. Print
     the line, and stop with:

     > This selection is `revise-plugin`'s. In a new chat, from this directory:
     > `/plugin-dev:revise-plugin <slug> issues <the selection as typed>`
     > It reads each role these issues name whole, writes one edit list, and `plan-phases`
     > lands it in phases. To fix a few of them here, name them: `/plugin-dev:fix-issues
     > <ids>`. To fix all of them here anyway: add `--here`.

     Read no issue file and plan nothing before stopping: the plan is what this route
     exists to keep out of one chat.
   - With `--here` in the arguments, print the line, say the selection is being fixed here
     on the user's `--here`, and go on to §2.

## 2. The plan, and your yes

For each selected issue, read:

- its record: `I list --format json` gives its frontmatter, its **Found in** lines and its
  attempts; open the issue file itself for the whole **Finding**, every **Fix** attempt and
  its **Checks** lines. A recurred issue's earlier attempt and the Checks line that says it
  recurred are the reason it is back: the new plan has to say why that attempt did not hold
  and what this one does differently.
- the run report each Found in line names (`runs/audits/reports/<date>-<id8>.md`), at the finding
  its finding id names, under **Errors**, **Warnings** or **Notes**: the evidence and the
  edit the report proposed. A report that does not exist here (a report from another
  checkout, or an issue seeded without one) is not a reason to stop: plan from the issue's
  **Finding**, its quote and its rule file, and say in the chat that the report was not
  found.
- the rule file in the working tree: `grep -nF "<rule_quote>" <rule_file>` says whether the
  rule is still there and where it is now. Line numbers drift between versions; the quote
  does not. A rule that spans two lines may not match whole: grep a distinctive part of it.
  A rule that is gone may already have been fixed, so say so rather than planning an edit
  for it.

The plan is one proposed edit per issue: the file, the sentence or step that changes, and
how it reads afterwards. Or `wontfix`, with the reason. By fault:

- **`definition`**: change the definition where the rule is missing, ambiguous or
  contradicted, at the step where it applies.
- **`driver`**: change the skill whose main thread did it, at the step it broke.
- **`agent`**: the agent broke a rule its definition states. Restate the rule in the step
  where it applies, since a rule stated once, far from where it applies, is the usual cause;
  or add a guard where the plugin already guards that kind of action (a hook that checks
  it). Otherwise close it as `wontfix` with the reason: one agent once breaking a rule that
  is stated plainly where it applies is not something an edit fixes.

Show the plan, then ask once with `AskUserQuestion`: `Approve the plan` (Recommended) or
`Change it`. A changed plan is shown again and asked again. Make no edit before the yes:
the yes is for the plan as shown, and an edit made first is one the user never saw.

## 3. The worktree

The edits go on their own branch in their own worktree, never in the checkout this chat
started in, which may be another chat's (the root `CLAUDE.md` on working across branches).

- The branch: `<P>-audit-fixes-<YYYYMMDD>`, today's date; when that branch exists, add
  `-2`, then `-3`, and so on.
- The path: `<repo root>/../cott-plugins-worktrees/<P>_<branch>`, where `<repo root>` is
  `git rev-parse --show-toplevel`.
- From the repo root: `git worktree add -b <branch> <path> main`.

Everything below runs in `<path>/<P>/`, the plugin's directory inside the worktree, and
every `I` call there carries `--dir <path>/<P>`.

## 4. The edits

Make the plan's edits, as approved, and nothing else. Each is a change to an agent or skill
like any other: before changing an agent, skill, hook or manifest field, read its reference
in `${CLAUDE_PLUGIN_ROOT}/skills/plugin-anatomy/references/`. Something else worth fixing
that the plan did not name is a line in the final message, not an edit. A `wontfix` issue
gets no edit.

## 5. The checks

In this order, in the worktree's plugin directory:

1. The plugin's own rules, from its `CLAUDE.md`: a list to update, a file to keep in step.
2. `check-contracts`, when the plugin has a `contracts.yml`. A FAIL names a `file:line`; fix
   the file, not the claim.
3. `build-site`, when the plugin has a `site/`.
4. `run-evals` for every set under `evals/sets/*.json` whose `target_path` is a file the
   edits touched, with the plugin's last tag as the baseline: `git describe --tags --match
   '<P>-v*' --abbrev=0`, else `git describe --tags --match 'v*' --abbrev=0`; with no tag at
   all, `previous`. No covering set, or no `evals/sets/`, means there is nothing to run:
   say so, and never invent a set to have something to run.

Each check with nothing to run in this plugin is stated as such, in this order, so the
record shows it was considered. A failure goes back to §4, inside the approved plan. The
eval logs `run-evals` writes through `log-eval` are the attempts' `evals`; with none, the
attempt's `evals` is `none`.

## 6. Record each attempt

1. Commit the edits, staging them by path: `<P> audit fixes: <ids> — <one line>`. Its short
   sha is every attempt's `commit`.
2. Per fixed issue:

   ```
   I fix <ID> --dir <path>/<P> --branch <branch> --commit <short sha> --files <paths> \
     --evals <log paths | none> \
     --verify "watch <applies_to>; held when <what a trace shows when the fix held>; recurred when <what a trace shows when it did not>"
   ```

   `held when` and `recurred when` each name something a trace shows: a return line, a
   tool call and its output, a Write to a path. The next audit of a rerun checks exactly
   this line against the trace, and "the agent follows the rule" is not something a trace
   shows.
3. Per `wontfix` issue: `I wontfix <ID> --dir <path>/<P> --reason "<why>"`.
4. `I check --dir <path>/<P>` must print `ok`. If it does not, fix what it names through
   `issues.py` and run it again.
5. Commit the attempts, from `<path>/<P>/` (the plugin's directory in the worktree, not the
   worktree's root, where `runs/audits` names nothing): `git add runs/audits && git commit -m "<P>
   audits: fix attempts for <ids>" -- runs/audits`. Two commits, in that order, because an
   attempt names the edit commit, which must exist first.

Never `I check-result`, and never a `held`: fix-issues records what was changed, not
whether it worked. Only an audit of a rerun can say an issue held.

## 7. Merge, then bump — each on its own yes

1. Ask with `AskUserQuestion` whether to merge `<branch>` into `main`.
   - **Yes**: merge in the main checkout only when it is on `main` with a clean tree
     (`git -C <repo root> branch --show-current` and `git -C <repo root> status
     --porcelain`). Then `build-site` for **P** in the main checkout (the site is gitignored
     and never arrives with a merge), and `git worktree remove <path>`. When the main
     checkout is on another branch or has uncommitted work, say so, leave the branch and the
     worktree, and stop: the user merges.
   - **No**: say the branch and the worktree are left where they are, at their names.
2. Then say a bump looks warranted and name the level: a fix that changes what an agent or
   skill reads, writes or does is minor; a change to wording alone is patch. Say it has not
   been made and waits for a yes, and stop. `bump-version` runs only on that yes, and stamps
   `fixed_in` on the issues the release carries.

## What this skill never does

- Plan a selection `I route` gave to `revise-plugin`, unless the arguments carry `--here`.
- Edit anything outside the worktree, or before the plan's yes.
- Merge, bump, tag or push without a yes for each.
- Set an issue to verified, or call `I check-result`: only an audit of a rerun can.
- Write or edit a file under `runs/audits/issues/`, or `runs/audits/INDEX.md`, by hand. `issues.py`
  writes them all.
- Rerun the workflow. The user reruns it, and the next audit reads the trace.
