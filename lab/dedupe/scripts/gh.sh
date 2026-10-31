#!/usr/bin/env bash
# Time-boxed gh wrapper for the dedupe bench. Mirrors anthropics/claude-code scripts/gh.sh (issue view, issue list,
# search issues, label list) but the agent only sees the world as it was before the target issue was created:
#  - search and list queries get "created:<DATE" appended; results created at/after DATE are dropped
#  - comments created at/after DATE are dropped (this hides the maintainer's duplicate verdict)
#  - the target issue shows as OPEN, with its title and body only (no comments, no labels)
# Env: GITHUB_REPOSITORY (owner/repo), DEDUPE_BEFORE (ISO time of the target), DEDUPE_TARGET (issue number).
exec python3 -I "$(dirname "$0")/gh_boxed.py" "$@"
