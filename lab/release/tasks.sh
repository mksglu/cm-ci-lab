# Release-notes tasks: 12 real releases, 2 from each of 6 popular repos.
# release_task <name> sets REL_REPO, REL_TAG (the new tag), REL_PREV (the previous tag), REL_NAME.
release_task() {
  case "$1" in
    gemini-66) REL_REPO=google-gemini/gemini-cli;       REL_TAG=v0.66.0; REL_PREV=v0.65.0; REL_NAME="Gemini CLI" ;;
    gemini-65) REL_REPO=google-gemini/gemini-cli;       REL_TAG=v0.65.0; REL_PREV=v0.64.0; REL_NAME="Gemini CLI" ;;
    uv-135)    REL_REPO=astral-sh/uv;                   REL_TAG=0.13.5;  REL_PREV=0.13.4;  REL_NAME="uv" ;;
    uv-1222)   REL_REPO=astral-sh/uv;                   REL_TAG=0.12.22; REL_PREV=0.12.21; REL_NAME="uv" ;;
    mcp-21)    REL_REPO=modelcontextprotocol/servers;   REL_TAG=v2.1.0;  REL_PREV=v2.0.0;  REL_NAME="MCP servers" ;;
    mcp-22)    REL_REPO=modelcontextprotocol/servers;   REL_TAG=v2.2.0;  REL_PREV=v2.1.0;  REL_NAME="MCP servers" ;;
    rg-152)    REL_REPO=BurntSushi/ripgrep;             REL_TAG=15.2.0;  REL_PREV=15.1.0;  REL_NAME="ripgrep" ;;
    rg-141)    REL_REPO=BurntSushi/ripgrep;             REL_TAG=14.1.1;  REL_PREV=14.1.0;  REL_NAME="ripgrep" ;;
    zod-466)   REL_REPO=colinhacks/zod;                 REL_TAG=v4.6.6;  REL_PREV=v4.6.5;  REL_NAME="Zod" ;;
    zod-465)   REL_REPO=colinhacks/zod;                 REL_TAG=v4.6.5;  REL_PREV=v4.6.4;  REL_NAME="Zod" ;;
    ruff-173)  REL_REPO=astral-sh/ruff;                 REL_TAG=0.17.3;  REL_PREV=0.17.2;  REL_NAME="Ruff" ;;
    ruff-171)  REL_REPO=astral-sh/ruff;                 REL_TAG=0.17.1;  REL_PREV=0.17.0;  REL_NAME="Ruff" ;;
    *) echo "unknown task $1" >&2; return 2 ;;
  esac
}
