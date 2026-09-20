#!/usr/bin/env bash
# Copy this fixture to a fresh git repository on branch `build` and print its path.
#
# Usage: reset.sh [--no-constraints] [dest]
#   --no-constraints  drop docs/constraints.md (phases before 6 of the 0.5 overhaul)
#   dest              directory to create; must not exist. Default: a new mktemp dir.
set -e

here="$(cd "$(dirname "$0")" && pwd)"
constraints=1
dest=""
for arg in "$@"; do
  case "$arg" in
    --no-constraints) constraints=0 ;;
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) dest="$arg" ;;
  esac
done

if [ -z "$dest" ]; then
  dest="$(mktemp -d "${TMPDIR:-/tmp}/two-package.XXXXXX")"
else
  if [ -e "$dest" ]; then echo "$dest already exists" >&2; exit 2; fi
  mkdir -p "$dest"
fi

mkdir -p "$dest/docs" "$dest/data"
cp "$here/docs/brief.md" "$dest/docs/"
cp "$here/data/trades.csv" "$dest/data/"
if [ "$constraints" = 1 ]; then cp "$here/docs/constraints.md" "$dest/docs/"; fi

cd "$dest"
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q --allow-empty -m "root"
git checkout -q -b build
git add docs data
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: brief and trades dataset"

pwd
