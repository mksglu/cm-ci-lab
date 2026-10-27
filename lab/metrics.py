# Reads one Claude result (action execution_file or `claude -p --output-format json`) and writes lab-metrics.json.
# Checks: banner line, owner-memory markers, and for dry arms the tenant and URL the gateway would forward to.
# Prints no secret: the admin key never appears in these files (checked by the workflow before upload).
import base64, json, os, sys
src, arm, kind = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(src).read()
try: data = json.loads(raw)
except Exception: data = [json.loads(l) for l in raw.splitlines() if l.strip().startswith("{")]
msgs = data if isinstance(data, list) else [data]
res = next((m for m in reversed(msgs) if isinstance(m, dict) and m.get("type") == "result"), {})
u = res.get("usage") or {}
text = res.get("result") or ""
MARKERS = ["[[CM-", "CM-CORE", "CM-RULES", "CM-MEM", "Koseoglu", "context-mode saved", "⚡"]
out = {
  "arm": arm, "client": kind, "run_id": os.environ.get("GITHUB_RUN_ID"), "attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
  "is_error": res.get("is_error"), "subtype": res.get("subtype"), "num_turns": res.get("num_turns"),
  "duration_ms": res.get("duration_ms"), "duration_api_ms": res.get("duration_api_ms"),
  "total_cost_usd": res.get("total_cost_usd"),
  "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
  "cache_read_input_tokens": u.get("cache_read_input_tokens"),
  "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
  "model_usage": res.get("modelUsage"),
  "result_markers": [m for m in MARKERS if m in text],
  "result_head": text[:400] if not text.startswith("cm-dry-run:") else "cm-dry-run:<payload>",
}
if text.startswith("cm-dry-run:"):
  p = json.loads(base64.b64decode(text[len("cm-dry-run:"):]))
  body = json.dumps(p.get("body"))
  out["dry"] = {"tenant": p.get("tenant"), "url": p.get("url"), "header_names": sorted((p.get("headers") or {}).keys()),
                "body_bytes": len(body), "body_markers": [m for m in MARKERS if m in body],
                "model": (p.get("body") or {}).get("model"), "tools": len((p.get("body") or {}).get("tools") or [])}
json.dump(out, open("lab-metrics.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("arm", "client", "is_error", "num_turns", "total_cost_usd", "result_markers")}))
if "dry" in out: print(json.dumps(out["dry"]))
