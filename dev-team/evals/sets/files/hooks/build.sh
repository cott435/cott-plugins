#!/usr/bin/env bash
# Build the two scratch directories the hooks evals run real sessions in, and print both.
#
# Usage: build.sh [--green] <in-scope-dest> <out-of-scope-dest>
#
# in-scope:     evals/fixtures/two-package/reset.sh --no-constraints, then this directory's
#               repo/ tree on top (docs/architecture.md is the scope marker; its own
#               docs/constraints.md has rows that pass in a bare checkout; docs/decisions.md
#               holds D1-D2; the data contract has sections ingest, clean and surface),
#               committed in two commits, the second carrying the `Dev-Team-Run:` trailer the
#               gate looks for and holding the ingest code, intent tests and unit tests.
# out-of-scope: the same packages/ tree in a fresh git repo with no docs/ directory.
# --green:      loader-green.py replaces the ingest loader in both, so the section's intent
#               suite passes and the stop gate lets an implementer stub finish at its first
#               stop (the guard evals, 4 and 5). Without it one intent test is red, which is
#               what the gate eval (2) needs.
# Both get .claude/settings.json disabling the marketplace's installed dev-team plugin, so
# the only dev-team the session sees is the --plugin-dir copy under test.
set -e

here="$(cd "$(dirname "$0")" && pwd)"
plugin="$(cd "$here/../../../.." && pwd)"
green=0
if [ "$1" = "--green" ]; then green=1; shift; fi
in_scope="$1"
out_scope="$2"
if [ -z "$in_scope" ] || [ -z "$out_scope" ]; then
  echo "usage: build.sh [--green] <in-scope-dest> <out-of-scope-dest>" >&2; exit 2
fi
for d in "$in_scope" "$out_scope"; do
  if [ -e "$d" ]; then echo "$d already exists" >&2; exit 2; fi
done

git_commit() { git -c user.name=fixture -c user.email=fixture@example.invalid commit -q "$@"; }

settings() {
  mkdir -p "$1/.claude"
  printf '{\n  "enabledPlugins": { "dev-team@cott-plugins": false }\n}\n' > "$1/.claude/settings.json"
}

# --- in scope ---------------------------------------------------------------
bash "$plugin/evals/fixtures/two-package/reset.sh" --no-constraints "$in_scope" > /dev/null
cp -R "$here/repo/docs/." "$in_scope/docs/"
cp "$here/repo/.gitignore" "$in_scope/.gitignore"
mkdir -p "$in_scope/packages/data/src/data"
cp "$here/repo/packages/data/pyproject.toml" "$in_scope/packages/data/"
cp "$here/repo/packages/data/src/data/__init__.py" "$in_scope/packages/data/src/data/"
settings "$in_scope"
(
  cd "$in_scope"
  git add -A
  git_commit -m "fixture: contracts, constraints, package skeleton, scratch settings"
  # The trailer commit holds ingest files only, so the gate maps the run to one section.
  cp -R "$here/repo/packages/data/src/data/ingest" packages/data/src/data/
  mkdir -p packages/data/tests
  cp -R "$here/repo/packages/data/tests/intent" packages/data/tests/
  cp -R "$here/repo/packages/data/tests/unit" packages/data/tests/
  if [ "$green" = 1 ]; then cp "$here/loader-green.py" packages/data/src/data/ingest/loader.py; fi
  git add packages
  git_commit -m "data/ingest: loader, intent tests and unit tests" -m "Dev-Team-Run: run-package data"
)

# --- out of scope ------------------------------------------------------------
mkdir -p "$out_scope"
cp -R "$here/repo/packages" "$out_scope/packages"
cp "$here/repo/.gitignore" "$out_scope/.gitignore"
if [ "$green" = 1 ]; then cp "$here/loader-green.py" "$out_scope/packages/data/src/data/ingest/loader.py"; fi
settings "$out_scope"
(
  cd "$out_scope"
  git init -q -b build
  git add -A
  git_commit -m "scratch: the same package tree, no docs/"
)

echo "in-scope:     $in_scope"
echo "out-of-scope: $out_scope"
