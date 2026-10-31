# Usage: extract.py claude-output.json tasks.json task_id answer.json
# Reads the final answer {"labels":[...]} (last JSON object with a "labels" key in the result text), writes the
# answer, then the F1 against the maintainers' labels. Status and bot labels are dropped from BOTH sides.
import json, sys
src, tasks, tid, dst = sys.argv[1:5]
DROP = ("stale", "triage", "needs", "wontfix", "duplicate", "invalid", "autoclose", "bot", "ai-", "status", "waiting", "close", "resolved",
        "fixed", "released", "regression-", "spam", "archived", "verif", "team", "contrib", "priority", "severity", "reach", "relnotes", "milestone")
def keep(l): return not any(x in l.lower() for x in DROP)
text = ""
for l in open(src):
    l = l.strip()
    if l.startswith("{"):
        try: e = json.loads(l)
        except Exception: continue
        if e.get("type") == "result": text = e.get("result") or ""
labels, dec = None, json.JSONDecoder()
for i in range(len(text) - 1, -1, -1):
    if text[i] == "{":
        try: o, _ = dec.raw_decode(text[i:])
        except Exception: continue
        if isinstance(o, dict) and isinstance(o.get("labels"), list): labels = [str(x) for x in o["labels"]]; break
truth = next(t["truth"] for t in json.load(open(tasks)) if t["id"] == tid)
pred = sorted({l for l in (labels or []) if keep(l)}); tr = sorted(set(truth))
tp = len(set(pred) & set(tr))
p = tp / len(pred) if pred else 0.0; r = tp / len(tr) if tr else 0.0
f1 = 2 * p * r / (p + r) if p + r else 0.0
json.dump({"task": tid, "parsed": labels is not None, "labels_raw": labels, "pred": pred, "truth": tr, "tp": tp, "precision": p, "recall": r, "f1": f1}, open(dst, "w"), indent=1)
print(json.dumps({"task": tid, "pred": pred, "truth": tr, "f1": round(f1, 3)}))
