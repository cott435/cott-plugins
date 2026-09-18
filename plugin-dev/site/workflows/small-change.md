# A small change

One agent or one skill, one chat, one commit. This is the default; the phased workflow is
for when this one would not fit.

## The sequence

1. **Edit** the agent or skill. If the plugin's `CLAUDE.md` has a rule about added or
   removed files — `dev-team`'s three-file rule, say — it applies in the same commit.
2. **`check-contracts`**, if the plugin has a `contracts.yml`. A `FAIL` names the
   `file:line`; fix the file, not the claim — unless the claim is what changed, in which
   case `contracts.yml` is edited in the same commit and the eval below says so.
3. **`build-site`.** The nav is generated from the bundle, so a renamed or added file
   appears without config; a broken page is a broken prompt.
4. **An eval, if the edit changes what an agent does.** A reworded instruction, a new
   trigger, a changed return shape: `log-eval` writes the dated file under `evals/` and the
   index row *before* the result is reported in chat, with the commit field reading
   *uncommitted — see working-tree diff*. A pure typo fix needs none; a changed rule always
   does, and a clean pass is logged like a failure.
5. **Commit**, staging by explicit path.
6. **Bump?** `bump-version` decides the level from what changed and says so in chat. It
   edits, tags and pushes only on a yes; a "looks fine" is not a yes.

## When it is not small

Any of these means `plan-phases` instead: more than one agent changes; a heading another
file parses moves; a new agent or a new workflow skill; `status`-style tooling changes
alongside the prompts that read it; or the evals you would need do not fit in the chat
that makes the edit. The cost of planning is one chat; the cost of not planning is a
second half done by a model that has forgotten the first.

## Where things go

| Thing | Path |
|---|---|
| The eval record | `evals/<date>-<subject>.md` + a row in `evals/README.md` |
| A design note worth keeping | `site/notes/<name>.md` — rendered under Notes |
| A decision about this plugin's versioning or models | `VERSIONING.md` |
| The release line | `CHANGELOG.md`, written by `bump-version` |
