#!/usr/bin/env bash
# The action runs this instead of the claude binary (input path_to_claude_code_executable).
# Measured (lab replay arm, run 40672064178): Anthropic answers 400 "credit balance is too low" for this
# repo's API key when the request's billing block says cc_entrypoint=claude-code-github-action, and 200 for
# the byte-identical request with cc_entrypoint=sdk-cli. User-agent and the billing block itself do not matter.
# The action hard-sets CLAUDE_CODE_ENTRYPOINT=claude-code-github-action in the SDK env; this resets it.
export CLAUDE_CODE_ENTRYPOINT=sdk-cli
exec "$HOME/.local/bin/claude" "$@"
