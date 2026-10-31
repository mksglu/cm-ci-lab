# Paired analysis for the dedupe lane. Usage: analyze.py <runs-dir-glob-root> ; reads */*/lab-metrics.json
# Pair by (task, round tag). Cost: mean paired log-ratio gateway/direct-ts -> exp(mean)-1. 95% CI: bootstrap over TASKS
# (all rounds of a task stay together), 10,000 resamples, seed 1.
import glob, json, math, random, sys, collections
root = sys.argv[1]; FEE = 0.0009
rows = []
for f in glob.glob(root + "/*/*/lab-metrics.json"):
    m = json.load(open(f))
    if m.get("tag", "").endswith("smoke") or "task" not in m: continue
    rows.append(m)
by = collections.defaultdict(dict)
for m in rows: by[(m["task"], m["tag"])][m["arm"]] = m
pairs = {k: v for k, v in by.items() if "direct-ts" in v and "gateway" in v}
errs = [m for m in rows if m.get("is_error") or not m.get("total_cost_usd") or m.get("credit_low")]
print("runs", len(rows), "pairs", len(pairs), "errors", len(errs))
lr = collections.defaultdict(list)
for (t, tag), v in pairs.items():
    lr[t].append(math.log(v["gateway"]["total_cost_usd"] / v["direct-ts"]["total_cost_usd"]))
allv = [x for l in lr.values() for x in l]
mean = sum(allv) / len(allv)
random.seed(1); tasks = list(lr); bs = []
for _ in range(10000):
    s = [x for t in random.choices(tasks, k=len(tasks)) for x in lr[t]]
    bs.append(sum(s) / len(s))
bs.sort(); lo, hi = bs[249], bs[9749]
pc = lambda x: 100 * (math.exp(x) - 1)
print(f"cost change {pc(mean):+.1f}%  task-resampled 95% CI {pc(lo):+.1f}..{pc(hi):+.1f}  cheaper {sum(x < 0 for x in allv)}/{len(allv)}")
def arm_stats(arm):
    ms = [v[arm] for v in pairs.values()]; n = len(ms)
    MU = dict(**{"in": "inputTokens", "cw": "cacheCreationInputTokens", "cr": "cacheReadInputTokens", "out": "outputTokens"})
    # tokens from model_usage (the same source as total_cost_usd). The streamed per-message usage shows output 0 on the gateway arm.
    tok = lambda k: sum(sum(v.get(MU[k], 0) for v in m["model_usage"].values()) for m in ms) / n
    return dict(cost=sum(m["total_cost_usd"] for m in ms) / n, api_calls=sum(m["api_calls"] for m in ms) / n,
                turns=sum(m["num_turns"] for m in ms) / n, uncached=tok("in"), cache_write=tok("cw"), cache_read=tok("cr"), output=tok("out"),
                hit=sum(bool(m["hit_top3"]) for m in ms), n=n)
d, g = arm_stats("direct-ts"), arm_stats("gateway")
for n, s in (("direct-ts", d), ("gateway", g)): print(n, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()})
print(f"net per run = {d['cost']:.4f} - {g['cost']:.4f} - {FEE} x {g['api_calls']:.1f} api calls = {d['cost'] - g['cost'] - FEE * g['api_calls']:+.4f}  (turns-based: {d['cost'] - g['cost'] - FEE * g['turns']:+.4f})")
b = c = 0
for v in pairs.values():
    x, y = bool(v["direct-ts"]["hit_top3"]), bool(v["gateway"]["hit_top3"])
    b += x and not y; c += y and not x
p = 1.0 if b + c == 0 else min(1.0, 2 * sum(math.comb(b + c, i) for i in range(0, min(b, c) + 1)) / 2 ** (b + c))
print(f"quality top3 direct-ts {d['hit']}/{d['n']} gateway {g['hit']}/{g['n']}  direct-only {b} gateway-only {c} McNemar exact p={p:.3f}")
print("PER PAIR task tag | direct cost/calls/hit | gateway cost/calls/hit")
for (t, tag), v in sorted(pairs.items()):
    a, z = v["direct-ts"], v["gateway"]
    print(f"{t} {tag[-2:]} | ${a['total_cost_usd']:.4f}/{a['api_calls']}/{a['hit_top3']} {a['run_id']} | ${z['total_cost_usd']:.4f}/{z['api_calls']}/{z['hit_top3']} {z['run_id']}")
