#!/usr/bin/env bash
# Runs one evaluation of the explore-implement-review pipeline (or a single-agent
# control) headlessly, so every iteration is a real Claude Code session.
#
#   run.sh pipeline <label> <repo> <task.md>   # skill + local plugin, in <repo> on its current branch
#   run.sh control  <label> <repo> <task.md>   # plain single agent, same task, no plugin
#   run.sh audit    <label> <repo> <base> <head> <task.md>  # blind standards + spec audit of a commit range
#   run.sh review   <label> <repo> <base> <head> <prompt.md> # replay the plugin reviewer on <head>'s changes,
#                                                            # left uncommitted on top of <base> in a temporary worktree
#
# Output: eval/runs/<label>/{stream.jsonl,meta.env}. metrics.py reads them.
set -euo pipefail

EVAL="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$EVAL/.." && pwd)"
mode=$1 label=$2 repo=$(cd "$3" && pwd)
out="$EVAL/runs/$label"
workdir=$repo
mkdir -p "$out"
sid=$(python3 -c 'import uuid; print(uuid.uuid4())')
budget=${BUDGET_USD:-40}

case $mode in
  pipeline)
    task=$(cat "$4")
    prompt="/explore-implement-review:explore-implement-review $task"
    extra=(--plugin-dir "$PLUGIN")
    ;;
  control)
    task=$(cat "$4")
    prompt="$task

Implement this with tests, run the relevant build and tests, and commit only the files you changed to the current branch with a Conventional Commits message. Report the commit SHA."
    extra=()
    ;;
  audit)
    base=$4 head=$5 task=$(cat "$6")
    prompt="You are an independent auditor. Do not edit, write or commit anything.

Audit the change \`git diff --ignore-cr-at-eol $base $head\` (only that range; ignore the working tree).

1. Read coding_standards.md. For each added or changed line in the range, list every violation of a rule there as \`file:line | rule ID | one-line reason\`. Do not flag lines the range does not touch, or anything listed under Known debt.
2. Check the range against this spec and list each acceptance criterion as MET, PARTIAL or MISSING with evidence:

$task

3. List each new or changed test and say whether it would fail if the behaviour it covers were broken (YES/NO).

End with exactly these lines:
VIOLATIONS: <count>
CRITERIA_MET: <met>/<total>
WEAK_TESTS: <count of NO>"
    extra=()
    ;;
  review)
    base=$4 head=$5 reviewer_prompt=$(cat "$6")
    # Recreate the state the reviewer saw: the implementer's work uncommitted on top of the fixed point.
    workdir="${REVIEW_WORKTREES:-$HOME/work}/$label"
    git -C "$repo" worktree add --detach --force -q "$workdir" "$head"
    git -C "$workdir" reset -q "$base"
    trap 'git -C "$repo" worktree remove --force "$workdir"' EXIT
    prompt="Spawn the \`explore-implement-review:reviewer\` subagent with the prompt between the markers below, verbatim. Do nothing else: don't read files, run commands or review anything yourself. When it returns, reply with its report verbatim.

<<<REVIEWER PROMPT
$reviewer_prompt
REVIEWER PROMPT>>>"
    extra=(--plugin-dir "$PLUGIN")
    ;;
  *) echo "unknown mode $mode" >&2; exit 2 ;;
esac

{
  echo "MODE=$mode"
  echo "LABEL=$label"
  echo "REPO=$repo"
  echo "SESSION_ID=$sid"
  echo "WORKDIR=$workdir"
  echo "BRANCH=$(git -C "$workdir" branch --show-current)"
  echo "START_SHA=$(git -C "$workdir" rev-parse HEAD)"
  echo "STARTED=$(date -u +%FT%TZ)"
  echo "PLUGIN_VERSION=$(python3 -c "import json;print(json.load(open('$PLUGIN/.claude-plugin/plugin.json'))['version'])")"
} > "$out/meta.env"

start=$(date +%s)
(cd "$workdir" && claude -p "$prompt" "${extra[@]}" \
  --session-id "$sid" --output-format stream-json --verbose \
  --max-budget-usd "$budget" > "$out/stream.jsonl" 2> "$out/stderr.log") || echo "EXIT=$?" >> "$out/meta.env"
{
  echo "END_SHA=$(git -C "$workdir" rev-parse HEAD)"
  echo "WALL_SECONDS=$(( $(date +%s) - start ))"
} >> "$out/meta.env"
echo "done: $out"
