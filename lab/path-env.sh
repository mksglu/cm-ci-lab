#!/usr/bin/env bash
# Env for one paths.yml arm into $GITHUB_ENV, exactly the lines `npx @context-mode/cli ci init` writes:
# the CI key (CONTEXT_MODE_KEY secret) as x-cm-device-key, banner off, x-cm-ci-* run headers. Never prints a secret.
# No entrypoint change of any kind: each client reports itself as it is.
set -euo pipefail
arm="$1"; gw="https://gateway.context-mode.com"
put() { local d="EOF_$RANDOM$RANDOM"; { echo "$1<<$d"; echo "$2"; echo "$d"; } >> "$GITHUB_ENV"; }
hdr="x-cm-device-key: ${CONTEXT_MODE_KEY}
x-context-mode-banner: off
x-cm-ci-repo: ${GITHUB_REPOSITORY}
x-cm-ci-ref: ${GITHUB_REF_NAME}
x-cm-ci-run: ${GITHUB_RUN_ID}"
case "$arm" in
  direct) ;;
  direct-ts) put ENABLE_TOOL_SEARCH true ;;
  gateway) put ANTHROPIC_BASE_URL "$gw"; put ANTHROPIC_CUSTOM_HEADERS "$hdr"; put ENABLE_TOOL_SEARCH true ;;
  gateway-dry)
    put ANTHROPIC_BASE_URL "$gw"; put ANTHROPIC_CUSTOM_HEADERS "$hdr
x-cm-dry-run: 1"; put ENABLE_TOOL_SEARCH true ;;
  *) echo "unknown arm $arm"; exit 2 ;;
esac
echo "arm=$arm"
