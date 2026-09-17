---
name: check-contracts
description: Check the cross-file claims a plugin's own agents and skills act on — a heading one file parses and another owns, a rule one file states and another contradicts, a list of names that goes stale when a directory changes. Use only in a plugin repo that has a contracts.yml, after editing any agent or skill, and before proposing a version bump.
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
claim — unless the claim itself is what changed, in which case edit `contracts.yml` in the same
change and say so.

## When

After editing any agent or skill, beside `build-site`; those are the edits that break a
contract. Always before `bump-version` — a bundle that ships a heading nobody writes has a bug
in it whatever the changelog says. Cheap enough to run on every pass; it reads files and
nothing else.

Report the result, and when a check fails or a new claim is added, record the run with
`log-eval` — a checker nobody can see the output of is a checker nobody trusts.

## Declaring claims — `contracts.yml` at the bundle root

Absent, nothing is checked and the script says so. Three kinds:

```yaml
forbid:                 # a pattern that must not appear in an authored file
  - name: no file promises a repo a `scripts/` directory
    pattern: '\bscripts/'          # regex; a line matching it fails the check
    all_of: ['finalize-project']   # optional: …and containing every one of these
    unless:                        # optional: skip the line if any of these matches
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
```

The owner template is **parsed, not restated**: `owner_span` slices the owner file and every
`N. **Name** —` line in that slice is a defined heading. Rename one and the check follows it,
which is the point — a checker carrying its own copy of the list is one more thing to go stale.

Two things to know about writing claims:

- **The checks are line-based.** An `unless` phrase must fit on one line as the file wraps it,
  or it will not match and the legitimate line will fail. Quote the shortest fragment that ends
  before the line break.
- **`names_listed` reports both directions** — a directory with no name in the file, and a
  backticked name in the span with no directory. The second catches a skill that was renamed
  or removed without the list following.

Authored files only, by default: `agents/*.md`, `skills/**/*.md`, `rules/*.md`, `README.md`,
`CLAUDE.md`, `site/*.md`, `site/workflows/*.md`, `site/notes/*.md`. `site/docs/` is always
excluded — it is a generated mirror, so a finding there is a duplicate of one in its source.

## What this cannot check

Anything that needs a model: whether a prompt is clear, whether an agent *acts* on the rule it
reads, whether a description triggers. Those are `log-eval`'s territory and need a real run.
This skill only settles whether two files still say the same thing.
