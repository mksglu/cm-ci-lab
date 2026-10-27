# cm-ci-lab

Private lab for one question: what happens when a CI agent (anthropics/claude-code-action, `claude -p`)
sends its traffic through the context-mode gateway, compared with a direct run.

The code is python-slugify (MIT, Val Neekman, upstream commit 35aca63f, see LICENSE). One function is broken on
purpose: `slugify/slugify.py` decodes hex entities (`&#x41;`) with base 10. Seven tests fail.

Workflows (all `workflow_dispatch` only, never on pull requests, so fork code never sees a secret):

- `tests.yml` — plain `pytest -vv`, the long CI log.
- `lab-action.yml` — claude-code-action@v1. Input `arm`: `direct`, `gateway`, `gateway-dry`, `litellm`, `litellm-dry`.
- `lab-cli.yml` — `claude -p` (native install). Same arms.

`*-dry` arms send `x-cm-dry-run: 1`: the gateway answers with the body it WOULD forward and calls no model.
They need no model key. Live arms need the secret `CLAUDE_CODE_OAUTH_TOKEN` (or `ANTHROPIC_API_KEY`).
The gateway arms act as the disposable tenant `t_ci_lab_1` (admin key + `x-cm-tenant`), never an owner tenant.
