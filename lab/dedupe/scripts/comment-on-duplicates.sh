#!/usr/bin/env bash
# Stub of anthropics/claude-code scripts/comment-on-duplicates.sh: the lab never writes to another repo.
# It prints the action and records the duplicate numbers, in the order the agent gave them, in $DEDUPE_OUT/comment.txt.
set -euo pipefail
[ "${1:-}" = "--potential-duplicates" ] || { echo "Usage: --potential-duplicates <n1> [n2] [n3]" >&2; exit 1; }
shift; [ "$#" -le 3 ] || { echo "at most 3" >&2; exit 1; }
for n in "$@"; do case "$n" in ''|*[!0-9]*) echo "bad number" >&2; exit 1;; esac; done
echo "$*" > "${DEDUPE_OUT:-.}/comment.txt"
echo "DRY RUN: would post on #${DEDUPE_TARGET}: Found $# possible duplicate issues: $*"
