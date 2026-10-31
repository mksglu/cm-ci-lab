# Per-message usage from `claude -p --output-format stream-json --verbose`.
# One assistant message can be streamed as several events with the same message.id; keep the last one per id.
import json, sys
src, dst = sys.argv[1], sys.argv[2]
by_id, order = {}, []
for l in open(src):
    l = l.strip()
    if not l.startswith("{"): continue
    try: e = json.loads(l)
    except Exception: continue
    if e.get("type") != "assistant": continue
    m = e.get("message") or {}
    mid = m.get("id") or f"noid-{len(order)}"
    if mid not in by_id: order.append(mid)
    u = m.get("usage") or {}
    by_id[mid] = {"id": mid, "model": m.get("model"), "uncached": u.get("input_tokens"), "cache_write": u.get("cache_creation_input_tokens"),
                  "cache_read": u.get("cache_read_input_tokens"), "output": u.get("output_tokens"),
                  "tools": [c.get("name") for c in (m.get("content") or []) if c.get("type") == "tool_use"]}
json.dump([by_id[i] for i in order], open(dst, "w"), indent=1)
print("messages", len(order))
