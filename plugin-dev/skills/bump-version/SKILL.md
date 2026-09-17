---
name: bump-version
description: Version a Claude Code plugin — decide patch/minor/major from what actually changed, bump plugin.json (and its marketplace.json entry), write the CHANGELOG line, tag the commit, and push. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json). Ask before running it — never bump, tag, commit, or push on your own initiative; propose it in chat and wait for a yes.
---

# Versioning a plugin

Three related but separate things every plugin tracks about itself: its release number,
which model each agent runs on, and which exact commit an eval result was checked against.
This skill owns the first two. The third is `log-eval`.

## Ask first — this is the one exception to "run automatically"

Every other skill in this kit (`log-eval`, `build-site`, `new-plugin`) is meant to fire on its
own when the moment matches. This one is not, because it commits, tags, and pushes — three
things worth a person's yes before they happen.

When a change looks bump-worthy, say so in chat and stop there: name the level you'd pick and
why, in one or two sentences. Do not touch `plugin.json`, `marketplace.json`, `CHANGELOG.md`,
or run any `git` command for this until the person replies with something like "yes," "go
ahead," or "do it." Only then run the procedure below, ending with the push.

## Release versioning

The version lives in the plugin's own `.claude-plugin/plugin.json`. Its row in the root
`.claude-plugin/marketplace.json` carries a matching `version` — bump both, in the same
commit as the change that triggered it.

Tag that commit. In this bundled repo a tag names one moment across every plugin, so scope it
in the tag message or use a per-plugin tag name (`dev-team-v1.2.0`) if two plugins are
likely to release independently often enough that a plain `vX.Y.Z` would be ambiguous about
which one changed.

- **PATCH** (`1.1.0` → `1.1.1`) — wording, examples, or narration changes to an agent, skill,
  or rule that don't change what it reads, writes, invokes, or promises to its callers.
  e.g. "plan-package: drop narration from step 1."
- **MINOR** (`1.1.0` → `1.2.0`) — a new agent, skill, command, or a non-breaking capability
  addition that existing callers can ignore. e.g. "added skill extraction and external source
  probing."
- **MAJOR** (`1.x` → `2.0.0`) — a breaking change to a contract: a file path, format, or
  frontmatter shape another agent, skill, or command already depends on. e.g. changing the
  shape of a document other agents read, renaming an invoked command, changing an agent's
  required inputs.

The test for major is not "how big was the edit" but "does something that already worked
against this plugin now break." A one-word rename of a file path is major. A rewritten
500-line agent prompt that still reads and writes the same files is minor.

## The procedure (only after a yes)

1. `git status` and `git diff` — decide the level from what actually changed, not from the
   commit message someone intended to write.
2. Edit `version` in `.claude-plugin/plugin.json`.
3. Add one entry to `CHANGELOG.md` under the new version heading, grouped
   Added / Changed / Fixed. One line per change, with the short SHA where there is one.
4. Update this plugin's row in the root `.claude-plugin/marketplace.json` — `version` to
   match. (A bundled, relative-path entry has no `ref` to move; that only applies to a
   plugin sourced from a separate repo.)
5. Commit the plugin.json bump, the marketplace.json bump, and the changelog line together.
6. Tag the commit.
7. Push: `git push` then `git push --tags` (or `git push --follow-tags` if the tag is
   annotated). Report the pushed commit and tag back in chat.

Never bump without a changelog line, and never write a changelog line without a tag. The
three exist to answer one question — *what is in the copy I have installed* — and any one of
them missing makes the other two unable to answer it.

(If this plugin is ever split out into its own repo, its marketplace entry gains a `ref` and
the same procedure applies with the push now going to that plugin's own repo.)

## Model versioning

The `model:` field in agent frontmatter. `model: inherit` is the default and should stay the
default: each agent runs on whatever model the calling session is using, which keeps the
plugin's behavior consistent with a person's own model choice instead of fragmenting cost and
quality decisions across every agent behind their back.

Override `inherit` with an alias (`sonnet` / `opus` / `haiku`) or a dated model ID only when
one agent's stakes or workload genuinely differ from "whatever the session runs on," and
record the reasoning in that repo's `VERSIONING.md` when it happens. The agents worth
considering are the ones whose output nobody checks afterward — a planner whose plan becomes
every later agent's ground truth, a reviewer that is the last gate before something ships.

Pin to a **dated** model ID rather than a rolling alias for any agent under active eval, so a
silent model upgrade later doesn't get mistaken for a prompt regression, or vice versa.

## Where the repo-specific part lives

Each plugin repo keeps a short `VERSIONING.md` that points here and holds only what is true
of that plugin: its per-agent model decisions and any exceptions. The policy itself is not
copied into repos — it is this file, so there is one place to change it.
