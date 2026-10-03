#!/usr/bin/env bash
# Seed a reset.sh copy of the two-package fixture for run-package eval 19: a `data` package
# planned under 2.7 whose workspace is scaffolded, whose `ingest` section is built and approved
# in round 1, and whose `clean` row is a data stage (`stage:rawtrades`) with nothing done yet.
# The export then gains the nine rows of planted-rows.csv, after the probe and after ingest.
#
# Usage: seed.sh <copy>      <copy> is the directory reset.sh printed, on its `build` branch.
#
# One commit per step, in the order the loop would have made them, because status.py reads
# the state from commit order: plan, scaffold, design, intent tests, build, review, data.
set -e

here="$(cd "$(dirname "$0")" && pwd)"
copy="$1"
if [ -z "$copy" ] || [ ! -d "$copy/.git" ]; then echo "usage: seed.sh <copy>" >&2; exit 2; fi
cd "$copy"

commit() {
  git add -A
  git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "$1"
}

cp -R "$here/../common/." .
cp -R "$here/1-plan/." .
commit "fixture: seeded planning documents"

cp -R "$here/2-scaffold/." .
mv gitignore .gitignore
uv sync --all-packages --quiet
commit "scaffold: workspace root and the data package skeleton"

cp -R "$here/3-design/." .
commit "data/ingest: design"

cp -R "$here/4-tests/." .
commit "data/ingest: intent tests"

cp -R "$here/5-build/." .
commit "data/ingest: build"
code="$(git rev-parse HEAD)"

cp -R "$here/6-review/." .
for report in docs/packages/data/reviews/ingest/2026-09-27-r1-a.md docs/packages/data/reviews/ingest/2026-09-27-r1-b.md; do
  sed "s/{CODE}/$code/" "$report" > "$report.tmp" && mv "$report.tmp" "$report"
done
commit "data/ingest: review r1"

cat "$here/planted-rows.csv" >> data/trades.csv
commit "data: the export, refreshed (nine more rows)"

git rev-parse --short HEAD
