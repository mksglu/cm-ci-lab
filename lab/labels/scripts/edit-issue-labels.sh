#!/usr/bin/env bash
# Lab replacement for the label write: prints the action and records it, writes nothing to any repo.
set -euo pipefail
adds=(); rems=()
while [ $# -gt 0 ]; do case "$1" in --add-label) adds+=("$2"); shift 2 ;; --remove-label) rems+=("$2"); shift 2 ;; *) shift ;; esac; done
echo "DRY-RUN edit labels: add=[$(IFS=,; echo "${adds[*]:-}")] remove=[$(IFS=,; echo "${rems[*]:-}")]"
printf '%s\n' "${adds[@]:-}" >> "${LABEL_ACTIONS:-/dev/null}"
