#!/usr/bin/env bash
# One dedupe run: mirrors anthropics/claude-code claude-dedupe-issues.yml (prompt "/dedupe <repo>/issues/<n>", the same
# dedupe.md command, scripts/gh.sh and comment-on-duplicates.sh, same disallowed tools) with headless `claude -p`.
# The gh wrapper only shows issues created before the target and hides the target's comments. Usage: run.sh <task-id> <model>
set -euo pipefail
id="$1"; model="$2"; lab="$GITHUB_WORKSPACE"
t=$(jq -c --arg id "$id" '.[]|select(.id==$id)' "$lab/lab/dedupe/tasks.json")
repo=$(jq -r .repo <<<"$t"); num=$(jq -r .number <<<"$t"); created=$(jq -r .created <<<"$t")
w="$RUNNER_TEMP/work"; rm -rf "$w"; mkdir -p "$w/.claude/commands" "$w/scripts" "$lab/out"
cp "$lab/lab/dedupe/commands/dedupe.md" "$w/.claude/commands/dedupe.md"
cp "$lab/lab/dedupe/scripts/"* "$w/scripts/"
cd "$w"; git init -q
{ echo "GITHUB_REPOSITORY=$repo"; echo "DEDUPE_BEFORE=$created"; echo "DEDUPE_TARGET=$num"; echo "DEDUPE_OUT=$lab/out"; } >> "$GITHUB_ENV"
export GITHUB_REPOSITORY="$repo" DEDUPE_BEFORE="$created" DEDUPE_TARGET="$num" DEDUPE_OUT="$lab/out"
set +e
claude -p "/dedupe $repo/issues/$num" --model "$model" --output-format stream-json --verbose --max-turns 60 --max-budget-usd 2 \
  --allowedTools "Bash(./scripts/gh.sh:*) Bash(./scripts/comment-on-duplicates.sh:*) Task Agent TodoWrite" \
  --disallowedTools "WebFetch,WebSearch,Write,Edit,MultiEdit,NotebookEdit" > "$lab/out/claude-stream.jsonl" 2> "$lab/out/claude-stderr.txt"
echo "claude rc=$?"
set -e
[ -f "$lab/out/comment.txt" ] || echo "" > "$lab/out/comment.txt"
