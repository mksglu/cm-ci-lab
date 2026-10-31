# Adds the per-message usage list (deduped by message id) from `claude -p --output-format stream-json --verbose`
# to lab-metrics.json. Usage: python3 lab/pr-review/usage.py out/claude-output.json out/lab-metrics.json
import json, sys
src, dst = sys.argv[1], sys.argv[2]
msgs, seen, per = [], {}, []
for l in open(src):
    l = l.strip()
    if not l.startswith("{"): continue
    try: m = json.loads(l)
    except Exception: continue
    msgs.append(m)
    if m.get("type") == "assistant":
        mm = m.get("message") or {}
        u = mm.get("usage") or {}
        mid = mm.get("id")
        if mid in seen:  # same API message repeated per content block: keep the last usage seen
            per[seen[mid]]["usage"] = u; continue
        seen[mid] = len(per)
        tools = [c.get("name") for c in (mm.get("content") or []) if c.get("type") == "tool_use"]
        per.append({"id": mid, "usage": u, "tools": tools})
rows = [{"i": i, "in": p["usage"].get("input_tokens", 0), "cw": p["usage"].get("cache_creation_input_tokens", 0),
         "cr": p["usage"].get("cache_read_input_tokens", 0), "out": p["usage"].get("output_tokens", 0), "tools": p["tools"]}
        for i, p in enumerate(per)]
res = next((m for m in reversed(msgs) if m.get("type") == "result"), {})
d = json.load(open(dst))
d["per_message_usage"] = rows
d["review"] = res.get("result", "")
d["api_requests"] = len(rows)
json.dump(d, open(dst, "w"), indent=1)
print("messages", len(rows), "sum cw", sum(r["cw"] for r in rows), "sum cr", sum(r["cr"] for r in rows))
