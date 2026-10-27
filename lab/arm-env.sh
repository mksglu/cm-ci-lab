#!/usr/bin/env bash
# Sets the env for one lab arm into $GITHUB_ENV. Never prints a secret value.
set -euo pipefail
arm="$1"; tenant="${LAB_TENANT:-t_ci_lab_1}"; gw="https://gateway.context-mode.com"
dry=""; case "$arm" in *-dry) dry=1 ;; esac
hdr="x-context-mode-key: ${CM_ADMIN_KEY}
x-cm-tenant: ${tenant}"
[ -n "$dry" ] && hdr="$hdr
x-cm-dry-run: 1"
put() { local d="EOF_$RANDOM$RANDOM"; { echo "$1<<$d"; echo "$2"; echo "$d"; } >> "$GITHUB_ENV"; }
case "$arm" in
  direct) ;;
  gateway|gateway-dry)
    put ANTHROPIC_BASE_URL "$gw"; put ANTHROPIC_CUSTOM_HEADERS "$hdr"; put ENABLE_TOOL_SEARCH true ;;
  litellm|litellm-dry)
    # The user's own proxy on the runner, in front of us: claude -> LiteLLM :4000 -> gateway -> Anthropic.
    # LiteLLM refuses to start without a master key. The client authenticates to LiteLLM with it;
    # LiteLLM authenticates upstream with LAB_UPSTREAM_KEY (the real model key, or a dummy on dry arms).
    lk="sk-lab-$(openssl rand -hex 24)"; echo "::add-mask::$lk"
    LITELLM_MASTER="$lk" python3 lab/litellm-config.py "$gw" "$tenant" "$dry" > "$RUNNER_TEMP/litellm.yaml"
    chmod 600 "$RUNNER_TEMP/litellm.yaml"
    put ANTHROPIC_BASE_URL "http://127.0.0.1:4000"; put ANTHROPIC_API_KEY "$lk"; put ENABLE_TOOL_SEARCH true
    dry_client_key_set=1 ;;
  *) echo "unknown arm $arm"; exit 2 ;;
esac
# A dry arm needs no model key; give the client a dummy one so it starts.
if [ -n "$dry" ] && [ -z "${dry_client_key_set:-}" ]; then put ANTHROPIC_API_KEY "sk-ant-lab-dry-not-a-key"; fi
echo "arm=$arm tenant=$tenant dry=${dry:-0}"
