---
name: check-contracts
description: Check a Claude Code plugin's own contracts — the cross-file claims its agents and skills make about each other (a heading one file parses and another owns, a rule one file states and another contradicts, a list of skill or agent names that goes stale when a directory changes) — and report PASS/FAIL with exact file:line. Use when someone asks to check, verify, or sweep a plugin's contracts ("check the contracts", "run the contract sweep", "does the bundle still hold after my edit?", "which file:line fails?"), after editing any agent or skill, and before proposing a version bump. Use only in a plugin repo that has a contracts.yml. Not for API/service contract testing (Pact, OpenAPI, tests/contract/), type checking, or markdown/link linting.
argument-hint: "[bundle path]"
---

# Check a bundle's own contracts

A plugin is a set of prompts that reference each other by name. One agent owns a document
template and others parse it by heading; one skill states a rule another still describes the
old way; a list of names sits in a prompt because nothing can derive it at run time. None of
that fails when it drifts — the agent reads for a heading that is never written and reports a
gap, or assigns the plugin's own machinery to a section, and the run looks normal.

Those claims are about file contents, so they are decidable without running a model. This
skill runs them.

## Run it

From the plugin repo root:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/contract_sweep.py"
```

When this plugin is not installed — a sandbox, a session that has the repo but not the
plugin — use the path inside the repo:

```
python3 ../plugin-dev/scripts/contract_sweep.py
```

The bundle defaults to the current directory. Exit 0 means every declared claim holds, 1 means
at least one failed, 2 means the bundle declares none. `--quiet` prints failures only, which
is the form to use in CI. Each line is `PASS`/`FAIL`, the claim's name, and either the count
checked or the exact `file:line` of every violation.

A `FAIL` is a real finding about the bundle, not a broken tool: fix the file, do not relax the
claim. A claim that reports `PASS` is worth exactly as much as the last time someone planted a
violation in it and watched it fail — a claim nobody has seen fail is not enforcement. When you
add one, or change its pattern or exemptions, plant the defect it exists to catch and record the
run with `log-eval` — unless the claim itself is what changed, in which case edit `contracts.yml` in the same
change and say so.

## When

After editing any agent or skill, beside `build-site`; those are the edits that break a
contract. Always before `bump-version` — a bundle that ships a heading nobody writes has a bug
in it whatever the changelog says. Cheap enough to run on every pass; it reads files and
nothing else.

Report the result, and when a check fails or a new claim is added, record the run with
`log-eval` — a checker nobody can see the output of is a checker nobody trusts.

## Declaring claims — `contracts.yml` at the bundle root

Absent, nothing is checked and the script says so. Four kinds:

```yaml
forbid:                 # a pattern that must not appear in an authored file
  - name: no file promises a repo a `scripts/` directory
    pattern: '\bscripts/'          # regex; a match fails the check
    near: 40                       # optional but usually right — see below
    all_of: ['finalize-project']   # optional: …with every one of these in scope
    unless:                        # optional: skip the match if any of these is in scope too
      - '\[project\.scripts\]'
    files: ['agents/*.md']         # optional: defaults to the authored set, below

headings:               # every heading a reader parses is one the owner's template defines
  - name: interface.md headings its readers parse are ones the implementer writes
    owner: agents/implementer.md
    owner_span: ['**Write `docs/packages/<pkg>/interface.md`**', null]   # [start, end]; null = to EOF
    readers:
      - file: agents/documenter.md
        span: ['The ones you read are', 'spelled exactly like that']     # parse names from this slice
      - file: agents/reviewer.md
        cites: ['Public names', 'Shapes provided']                       # or assert them literally

names_listed:           # every directory under `dirs` has its name in `file`
  - name: every skill this plugin ships is named in reserved-skill-names
    dirs: 'skills/*'
    file: skills/reserved-skill-names/SKILL.md
    span: ['## Workflow skills', '## What each reader does with it']
    where: {disable-model-invocation: true}   # optional: only dirs whose SKILL.md frontmatter matches
    form: code                                # optional: how the list cites a name — below

frontmatter:            # every frontmatter key is one the platform documents, and honors here
  - name: every agent uses only fields plugin agents honor
    kind: agent                    # agent or skill
    files: 'agents/*.md'           # a glob or a list; a glob matching nothing is a FAIL
```

`form` is how the target list writes a name, because a list is checked where it lives rather
than reformatted to suit the checker:

| `form` | A name appears as | Use it for |
|---|---|---|
| `code` (default) | `` `plan-repo` `` anywhere in the span | prose and tables |
| `tree` | an indented `── plan-repo/` branch | a directory tree in a fenced block, where backticks would render literally |
| `list` | `- plan-repo` on its own line, trailing comment allowed | a YAML sequence or a Markdown bullet list |

`where` narrows which directories the list is answerable for, from the frontmatter that already
distinguishes them. A list covering one class of skill — the ones a user types, say — is checked
against that class, so a knowledge skill is not reported missing from it and a second list of
which skills count never has to exist. A key that matches nothing is a `FAIL`, not a silent
pass: a typo in `where` would otherwise turn the claim off.

The owner template is **parsed, not restated**: `owner_span` slices the owner file and every
`N. **Name** —` line in that slice is a defined heading. When the owner is a document template
whose own `##` headings are the sections, set `owner_form: markdown` and those headings are the
defined names instead (fenced code blocks are skipped). Rename one and the check follows it,
which is the point — a checker carrying its own copy of the list is one more thing to go stale.

`frontmatter` reads its key lists from `plugin-anatomy`'s references — the
`frontmatter-keys` blocks in `references/skills.md` and `references/agents.md` — rather than
carrying its own copy. A misspelled key (`allowed_tools`) fails as undocumented, and a key
plugin agents ignore (`hooks`, `mcpServers`, `permissionMode`, `initialPrompt`) fails as
ignored: both look fine and do nothing at run time. When the platform adds a field, the fix is
in the reference, with its source, and the check follows.

Three things to know about writing claims:

- **Scope an exemption with `near`, or it pardons the whole line.** `all_of` and `unless`
  default to line scope; `near: <n>` narrows them to the matched text plus n characters either
  side. Almost every exemption means "this occurrence is fine", not "this line is exempt" — and
  an exemption lives exactly where the thing it pardons is discussed, which is where a real
  violation would be written. `dev-team`'s `scripts/` claim had eight line-scoped exemptions
  pardoning ten lines outright; `near: 40` caught all ten planted violations with the
  legitimate lines still silent. The residual: a violation inside the same clause as the
  exemption, within the window, is still pardoned. Lower `n` to tighten, or put the exemption
  in the pattern as a negative lookahead when it can be expressed structurally — that exempts
  a token and has no window at all.
- **The checks are line-based.** A `pattern`, `unless` or `all_of` phrase must fit on one line
  as the file wraps it. Quote the shortest fragment that ends before the line break.
- **`names_listed` reports both directions** — a directory with no name in the file, and a name
  in the span with no directory. The second catches a skill that was renamed or removed without
  the list following.

Authored files only, by default: `agents/*.md`, `skills/**/*.md`, `rules/*.md`, `README.md`,
`CLAUDE.md`, `site/*.md`, `site/workflows/*.md`, `site/notes/*.md`, `skills/**/*.py`. A script a
plugin ships is authored too, and it is the one file that prints to the user rather than to a
model. `site/docs/` is always excluded — it is a generated mirror, so a finding there is a
duplicate of one in its source.

## What this cannot check

Anything that needs a model: whether a prompt is clear, whether an agent *acts* on the rule it
reads, whether a description triggers. Those are `log-eval`'s territory and need a real run.
This skill only settles whether two files still say the same thing.
