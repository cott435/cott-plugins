#!/usr/bin/env bash
# One headless run of a run-package driver eval (evals/sets/run-package.json 1, 2, 3, 5, 6).
#
# Usage: run.sh <eval id> <with_skill|old_skill> <plugin dir> <run dir>
#
#   <plugin dir>  the plugin the session loads with --plugin-dir: the working tree for
#                 with_skill, the iteration's baseline-snapshot/ for old_skill.
#   <run dir>     the run's directory, as eval_workspace.py init made it; outputs/ under it.
#
# Builds a fresh reset.sh copy of evals/fixtures/two-package/ seeded as the eval's harness
# sheet says (Before starting), disables an installed dev-team in the copy so only <plugin
# dir> is loaded, runs `claude -p "<the eval's command>"` from the copy with a stream-json
# record, keeps every gate-record version while it runs, then calls post.py. The session
# loads a copy of <plugin dir> without evals/, made beside the fixture copy. Seeds and
# harness sheets are always read from the working tree that holds this script: a baseline
# snapshot has no evals/.
#
# The session has no AskUserQuestion. The appended system prompt replaces it with an append
# to outputs/interview.md answered from the harness's **Answers**, and carries the harness's
# **Where the walk ends** when the sheet has one (evals 5 and 6). Nothing it appends holds an
# expectation.
#
# Environment: RUN_PACKAGE_MODEL (default claude-sonnet-5-5, the full ID; `sonnet` in a
# headless session is a different model), RUN_PACKAGE_TMP (where the copy is made; default
# $TMPDIR).
set -euo pipefail

if [ $# -ne 4 ]; then
  echo "usage: run.sh <eval id> <with_skill|old_skill> <plugin dir> <run dir>" >&2
  exit 2
fi
eval_id="$1"; config="$2"; plugin_dir="$(cd "$3" && pwd)"; run_dir="$4"
case "$config" in with_skill|old_skill) ;; *) echo "config must be with_skill or old_skill" >&2; exit 2 ;; esac

here="$(cd "$(dirname "$0")" && pwd)"
tree="$(cd "$here/../../.." && pwd)"          # the working tree's plugin directory
files="$tree/evals/sets/files/run-package"
model="${RUN_PACKAGE_MODEL:-claude-sonnet-5-5}"

case "$eval_id" in
  1) harness="$files/harness-1-walk-one-section.md"; command="/dev-team:run-package data ingest" ;;
  2) harness="$files/harness-2-spec-change-contract.md"; command="/dev-team:run-package data ingest" ;;
  3) harness="$files/harness-3-ask-on-blocked-decision.md"; command="/dev-team:run-package data ingest" ;;
  5) harness="$files/harness-5-two-sections.md"; command="/dev-team:run-package data" ;;
  6) harness="$files/harness-5-two-sections.md"; command="/dev-team:run-package data --serial" ;;
  *) echo "run.sh runs evals 1, 2, 3, 5 and 6; eval $eval_id is not headless" >&2; exit 2 ;;
esac

mkdir -p "$run_dir/outputs"
run_dir="$(cd "$run_dir" && pwd)"
outputs="$run_dir/outputs"

# --- the copy, seeded and committed (harness: Before starting) ---
base="$(mktemp -d "${RUN_PACKAGE_TMP:-${TMPDIR:-/tmp}}/run-package-eval-$eval_id-$config.XXXXXX")"
copy="$(bash "$tree/evals/fixtures/two-package/reset.sh" "$base/repo" | tail -1)"
cp -R "$files/seed/common/." "$copy/"
case "$eval_id" in
  2) cp "$files/seed/eval-2/docs/packages/data/contract.md" "$copy/docs/packages/data/contract.md" ;;
  3) cp "$files/seed/eval-3/docs/decisions.md" "$copy/docs/decisions.md" ;;
  5|6) cp -R "$files/seed/eval-5/." "$copy/" ;;
esac
git -C "$copy" add docs
git -C "$copy" -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: seeded planning documents"
seed_sha="$(git -C "$copy" rev-parse --short HEAD)"

# The session loads a copy of <plugin dir> made without evals/: Claude Code refuses a Write
# inside a directory loaded with --plugin-dir as a sensitive file, and the working tree's
# evals/workspace/ holds this run's outputs/ (interview.md). The copy also keeps every run's
# plugin fixed while the working tree is edited.
loaded="$base/$(basename "$plugin_dir")"
rsync -a --exclude evals/ --exclude site/docs/ --exclude .git "$plugin_dir/" "$loaded/"

# Only <plugin dir> is loaded: the installed dev-team is disabled in the copy, and the
# settings file is git-excluded so the run gate sees a clean tree.
mkdir -p "$copy/.claude"
printf '{"enabledPlugins": {"dev-team@cott-plugins": false}}\n' > "$copy/.claude/settings.json"
printf '.claude/\n' >> "$copy/.git/info/exclude"

command -v uv >/dev/null || { echo "uv is not on PATH; the scaffold needs it" >&2; exit 1; }

# --- the appended system prompt ---
section() {  # print one `## <title>` section of the harness sheet, heading included
  awk -v t="## $1" '$0==t{p=1; print; next} p && /^## /{exit} p' "$harness"
}
sysprompt="$run_dir/system-prompt.md"
{
  cat <<EOF
This is a headless evaluation session of the command typed below. There is no live user, and
the AskUserQuestion tool is not available. In its place: wherever the skill would call
AskUserQuestion, append one block to $outputs/interview.md with the Write or Edit tool — the
question's text exactly as you would pass it, each option's label and description, then the
answer — answer it from the **Answers** section below (or with the option marked Recommended
when that section does not cover the question), and go on as the skill says for that answer.
That file is outside the repo and is the only file outside it you write. Treat this stand-in as
AskUserQuestion being available: the skill's rule for a session without AskUserQuestion does
not apply. Where the text below says \`transcript.md\`, there is none: this session's own
record is the transcript.

EOF
  section "Answers"
  if grep -q '^## Where the walk ends$' "$harness"; then echo; section "Where the walk ends"; fi
} > "$sysprompt"

cat > "$run_dir/runner.json" <<EOF
{"eval_id": $eval_id, "config": "$config", "command": "$command", "plugin_dir": "$loaded", "plugin_source": "$plugin_dir",
 "copy": "$copy", "seed_sha": "$seed_sha", "model_flag": "$model", "harness": "$harness",
 "started": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF

# --- the gate-record watcher (harness-4's), beside the session ---
mkdir -p "$outputs/gate-history"
(
  while :; do
    for f in "$copy"/.dev-team/gate/*/*.txt; do
      [ -f "$f" ] || continue
      m=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f")
      k="$(basename "$(dirname "$f")")-$(basename "$f" .txt)-$m.txt"
      [ -e "$outputs/gate-history/$k" ] || cp -p "$f" "$outputs/gate-history/$k"
    done
    sleep 1
  done
) &
watcher=$!
trap 'kill $watcher 2>/dev/null || true; wait $watcher 2>/dev/null || true' EXIT

# --- the session ---
start=$(date +%s)
set +e
(
  cd "$copy" && claude -p "$command" \
    --plugin-dir "$loaded" \
    --model "$model" \
    --permission-mode acceptEdits \
    --add-dir "$outputs" \
    --append-system-prompt "$(cat "$sysprompt")" \
    --disallowedTools AskUserQuestion \
    --output-format stream-json --verbose \
    --allowedTools Agent Bash Read Write Edit Glob Grep Skill TodoWrite WebSearch WebFetch \
    < /dev/null > "$run_dir/stream.jsonl" 2> "$run_dir/stream.stderr"
)
status=$?
set -e
end=$(date +%s)
sleep 2
kill $watcher 2>/dev/null || true
wait $watcher 2>/dev/null || true

python3 - "$run_dir/runner.json" "$status" "$start" "$end" <<'EOF'
import json, sys
p, status, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
d = json.load(open(p))
d.update(exit_code=status, wall_seconds=end - start)
json.dump(d, open(p, "w"), indent=1)
EOF

python3 "$here/post.py" "$run_dir" "$copy"
echo "run.sh: eval $eval_id $config exit $status in $((end - start)) s; copy $copy"
