# Reads `claude -p --output-format stream-json --verbose` output (JSON lines).
# Writes per-message usage (one row per API request, deduped by message id) next to lab/metrics.py totals.
# Usage: python3 stream-metrics.py <stream.jsonl> <out-usage.json>
import json, sys
rows, seen, res = [], {}, {}
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("{"): continue
    try: m = json.loads(line)
    except Exception: continue
    if m.get("type") == "assistant":
        msg = m.get("message") or {}; u = msg.get("usage") or {}
        mid = msg.get("id") or str(len(rows))
        row = {"id": mid, "model": msg.get("model"), "stop_reason": msg.get("stop_reason"),
               "input_tokens": u.get("input_tokens", 0), "cache_creation_input_tokens": u.get("cache_creation_input_tokens", 0),
               "cache_read_input_tokens": u.get("cache_read_input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
               "tools": [b.get("name") for b in (msg.get("content") or []) if b.get("type") == "tool_use"]}
        if mid in seen:
            rows[seen[mid]]["tools"] += [t for t in row["tools"] if t not in rows[seen[mid]]["tools"]]
            for k in ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens","stop_reason"):
                rows[seen[mid]][k] = row[k]
        else:
            seen[mid] = len(rows); rows.append(row)
    elif m.get("type") == "result": res = m
tot = {k: sum(r[k] for r in rows) for k in ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens")}
json.dump({"requests": len(rows), "per_message_totals": tot, "result_usage": res.get("usage"), "messages": rows}, open(sys.argv[2], "w"), indent=1)
print(json.dumps({"requests": len(rows), **tot}))
