# Claude Agent SDK (Python) run: writes the result message as one JSON object to argv[1]. Base URL and headers come
# from the environment (ANTHROPIC_BASE_URL, ANTHROPIC_CUSTOM_HEADERS), as for any Claude Code process.
import anyio, json, os, sys
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    res = None
    opts = ClaudeAgentOptions(model=os.environ.get("LAB_MODEL", "haiku"), max_turns=30,
                              allowed_tools=["Bash", "Read", "Edit", "Write", "Glob", "Grep"], permission_mode="acceptEdits")
    async for m in query(prompt=os.environ["PROMPT"], options=opts):
        if isinstance(m, ResultMessage): res = m
    d = {"type": "result"}
    if res is not None:
        for k in ("subtype", "duration_ms", "duration_api_ms", "is_error", "num_turns", "session_id", "total_cost_usd", "usage", "result"):
            d[k] = getattr(res, k, None)
        d["modelUsage"] = getattr(res, "model_usage", None)
    json.dump(d, open(sys.argv[1], "w"), default=str)
    print(json.dumps({k: d.get(k) for k in ("subtype", "is_error", "num_turns", "total_cost_usd")}))

anyio.run(main)
