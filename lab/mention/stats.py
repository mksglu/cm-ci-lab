# Stats for the mention lane. Usage: python3 lab/mention/stats.py <artifact-root> <model-substring> [tag-substring ...]
# Pairs by (task, round). Cost = mean paired log-ratio gateway/direct-ts, % = exp(mean)-1. 95% CI: bootstrap over TASKS,
# 10,000 resamples, seed 1. Also: cheaper pairs, per-arm means, tokens, net per run at $0.0009 per request, exact McNemar.
import json, glob, math, os, random, sys
from math import comb, exp, log
root, model = sys.argv[1], sys.argv[2]
FEE = 0.0009
runs = {}
for lm in glob.glob(f"{root}/*/*/lab-metrics.json"):
    m = json.load(open(lm)); tag = m.get("tag", "")
    if model not in tag: continue
    rnd = tag.rsplit("-", 1)[-1]
    d = os.path.dirname(lm)
    pm = []
    try: pm = json.load(open(d + "/per-message-usage.json"))
    except Exception: pass
    runs[(m["task"], rnd, m["arm"])] = (m, pm)
pairs = sorted({(t, r) for (t, r, a) in runs})
def tok(m):
    return [m.get("input_tokens") or 0, m.get("cache_creation_input_tokens") or 0, m.get("cache_read_input_tokens") or 0, m.get("output_tokens") or 0]
errs = 0; rows = []
for t, r in pairs:
    a, b = runs.get((t, r, "direct-ts")), runs.get((t, r, "gateway"))
    if not a or not b: print("MISSING arm", t, r); continue
    for (m, _) in (a, b):
        c = m.get("total_cost_usd") or 0
        if m.get("is_error") or c == 0 or "Credit balance is too low" in (m.get("result_head") or ""): errs += 1
    rows.append((t, r, a[0], b[0]))
lr = {}
for t, r, a, b in rows: lr.setdefault(t, []).append(log(b["total_cost_usd"] / a["total_cost_usd"]))
allv = [v for vs in lr.values() for v in vs]; mean = sum(allv) / len(allv)
rnd = random.Random(1); tasks = list(lr); bs = []
for _ in range(10000):
    s = [v for t in (rnd.choice(tasks) for _ in tasks) for v in lr[t]]
    bs.append(sum(s) / len(s))
bs.sort(); lo, hi = bs[249], bs[9749]
n = len(rows); cheaper = sum(1 for t, r, a, b in rows if b["total_cost_usd"] < a["total_cost_usd"])
print(f"pairs {n} tasks {len(tasks)} errors {errs}")
print(f"cost change {100*(exp(mean)-1):+.1f}%  task-resampled 95% CI {100*(exp(lo)-1):+.1f}..{100*(exp(hi)-1):+.1f}  cheaper {cheaper}/{n}")
def avg(xs): return sum(xs) / len(xs)
for arm, i in (("direct-ts", 2), ("gateway", 3)):
    ms = [x[i] for x in rows]; tk = [tok(m) for m in ms]
    print(f"{arm}: pass {sum(1 for m in ms if m.get('passed'))}/{n} mean cost ${avg([m['total_cost_usd'] for m in ms]):.4f} turns {avg([m['num_turns'] for m in ms]):.2f} "
          f"uncached {avg([x[0] for x in tk]):.0f} cache_write {avg([x[1] for x in tk]):.0f} cache_read {avg([x[2] for x in tk]):.0f} output {avg([x[3] for x in tk]):.0f}")
md = avg([x[2]["total_cost_usd"] for x in rows]); mg = avg([x[3]["total_cost_usd"] for x in rows]); tg = avg([x[3]["num_turns"] for x in rows])
print(f"net per run = ({md:.4f}-{mg:.4f}) - {FEE}x{tg:.2f} = ${md-mg-FEE*tg:.4f}")
b = sum(1 for x in rows if x[2].get("passed") and not x[3].get("passed")); c = sum(1 for x in rows if x[3].get("passed") and not x[2].get("passed"))
k = b + c; p = 1.0 if k == 0 else min(1.0, 2 * sum(comb(k, i) for i in range(0, min(b, c) + 1)) / 2 ** k)
print(f"McNemar exact: direct-only {b} gateway-only {c} p={p:.3f}")
print("spend $%.3f" % sum((x[2]["total_cost_usd"] + x[3]["total_cost_usd"]) for x in rows))
json.dump({"n": n, "pct": 100*(exp(mean)-1), "ci": [100*(exp(lo)-1), 100*(exp(hi)-1)], "cheaper": cheaper, "errors": errs,
           "rows": [[t, r, a["total_cost_usd"], a["num_turns"], a.get("passed"), b["total_cost_usd"], b["num_turns"], b.get("passed")] for t, r, a, b in rows]},
          open(f"/tmp/lab-mention-scratch/stats-{model}.json", "w"))
