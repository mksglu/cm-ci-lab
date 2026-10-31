# Reads claude-stream.jsonl (stream-json): keeps the result totals (via lab/metrics.py) and saves the per-message usage list.
# Messages are deduplicated by message id (one API response is streamed as several blocks with the same usage).
import json, os, subprocess, sys
src, arm, task, tag, model = sys.argv[1:6]
tasks = {t["id"]: t for t in json.load(open("lab/dedupe/tasks.json"))}
t = tasks[task]
lines = [json.loads(l) for l in open(src) if l.strip().startswith("{")]
seen, per = set(), []
for m in lines:
    if m.get("type") != "assistant": continue
    msg = m["message"]; mid = msg.get("id")
    if mid in seen: continue
    seen.add(mid)
    u = msg.get("usage") or {}
    per.append({"id": mid, "model": msg.get("model"), "sub": bool(m.get("parent_tool_use_id")),
                "in": u.get("input_tokens", 0), "cw": u.get("cache_creation_input_tokens", 0),
                "cr": u.get("cache_read_input_tokens", 0), "out": u.get("output_tokens", 0),
                "tools": [c.get("name") for c in msg.get("content", []) if c.get("type") == "tool_use"]})
subprocess.run([sys.executable, "lab/metrics.py", src, arm, "cli"], check=True, stdout=subprocess.DEVNULL)
out = json.load(open("lab-metrics.json"))
res = next((m for m in reversed(lines) if m.get("type") == "result"), {})
picked = [int(x) for x in open("out/comment.txt").read().split() if x.isdigit()]
txt = (res.get("result") or "")
out.update(task=task, tag=tag, model_input=model, repo=t["repo"], target=t["number"], original=t["original"],
           picked=picked, hit_top3=t["original"] in picked[:3], rank=(picked.index(t["original"]) + 1) if t["original"] in picked else None,
           api_calls=len(per), per_message_usage=per,
           credit_low=("Credit balance is too low" in json.dumps(lines)[:200000]),
           final_text_head=txt[:300])
json.dump(out, open("out/lab-metrics.json", "w"), indent=1)
print(json.dumps({k: out.get(k) for k in ("arm", "task", "is_error", "num_turns", "api_calls", "total_cost_usd", "picked", "hit_top3", "credit_low")}))
