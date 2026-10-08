# bump-version eval 2 — a plugin with no `audits/`

Seed: the toy plugin from `evals/fixtures/audit-run/make_session.py`, copied into a directory
you make, made a git repository on `main` with a root marketplace, a changelog, a tag at
0.1.0 and one release-worthy commit on top. No `audits/` directory. Run this once, as
written, with `PD` set to the plugin root you were given; `$R` is the fixture root and
`$R/toy` the plugin directory the user is in.

```bash
PD=<your plugin root>
SEED=$(mktemp -d); python3 "$PD/evals/fixtures/audit-run/make_session.py" "$SEED" >/dev/null
R=$(mktemp -d); cp -R "$SEED/toy" "$R/toy"; cd "$R"
git init -q -b main
git config user.email eval@example.invalid; git config user.name eval
mkdir -p .claude-plugin
cat > .claude-plugin/marketplace.json <<'EOF'
{
  "name": "fixture-market",
  "owner": {"name": "eval"},
  "plugins": [
    {"name": "toy", "source": "./toy", "description": "A toy plugin for evals.", "version": "0.1.0"}
  ]
}
EOF
cat > toy/CHANGELOG.md <<'EOF'
# Changelog

## 0.1.0 — 2026-10-01

### Added
- the `ship` skill and the `writer` agent
EOF
git add -A && git commit -q -m "toy 0.1.0" && git tag toy-v0.1.0

# The change to release: a rule restated in the writer, and a new skill.
python3 - <<'EOF'
from pathlib import Path
p = Path("toy/agents/writer.md"); t = p.read_text()
old = "1. Write the target. You only ever write under `out/`; never anywhere else.\n"
assert old in t
p.write_text(t.replace(old, old + "   Working notes go in your return, never in a file.\n"))
EOF
mkdir -p toy/skills/check
cat > toy/skills/check/SKILL.md <<'EOF'
---
name: check
description: Check that every file under out/ has a matching commit.
disable-model-invocation: true
---

# Check

1. For each file under `out/`, run `git log --oneline -1 -- <file>`.
2. Print one line per file: `<file>: <sha>` or `<file>: uncommitted`.
EOF
git add -A && git commit -q -m "toy: writer keeps notes out of files; add the check skill"
echo "fixture: $R"
```

After the seed: `main` holds two commits (`toy 0.1.0`, tagged `toy-v0.1.0`; the writer change
and the new skill), the working tree is clean, and `toy/` has no `audits/` directory. The
user is in `$R/toy`. Everything since 0.1.0 is committed; nothing is uncommitted.

## The user's answers

Use these wherever the target would ask; write each question and your answer to
`outputs/interview.md` first.

- To the proposal (the level and why), or any "shall I bump?": "Yes, bump it. Minor is right."
- If asked which tag name to use: "The per-plugin form, `toy-v<version>`, like the one that is there."
- If asked whether to push: "Yes."
- If asked what to say in the changelog: "What the commits since the tag did."
- Anything else: the option marked Recommended, or the plain reading of the fixture.

## Where to write what you would commit

The fixture copy `$R` stands in for the repo. Make the edits there, but run no `git commit`,
`git tag` or `git push` in it. Then write:

- `outputs/interview.md` — the proposal exactly as you would say it in chat (level, new
  version, why), and the answer taken from this sheet.
- `outputs/tree/` — a copy of every file you would stage, at its path relative to `$R`:
  `outputs/tree/toy/.claude-plugin/plugin.json`, `outputs/tree/.claude-plugin/marketplace.json`,
  `outputs/tree/toy/CHANGELOG.md`, and anything else you changed, at its path. Copy a file
  only if you changed it.
- `outputs/commit.md` — the commit message; the paths you would stage, one per line,
  relative to `$R`; the tag you would create; the push command(s), each as the line you
  would have run.

## What goes in `transcript.md`

Every shell command you run, in order and verbatim (with its `--verify` or `--reason` value in
full), marked as the fixture's setup or the target's work, and every question with the answer
you took. Several expectations are about what ran and in what order, and a prose summary
cannot show that.
