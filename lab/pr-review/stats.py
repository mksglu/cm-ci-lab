# Paired stats for the pr-review bench. Usage: python3 -I lab/pr-review/stats.py work/art work/runs.tsv
import json, glob, math, random, sys, collections
art, tsv = sys.argv[1], sys.argv[2]
FEE = 0.0009
rows = {}
for l in open(tsv):
    rid, title, concl = l.rstrip("\n").split("\t")
    p = title.split()  # pr-review ARM repo#pr TAG
    if len(p) < 4 or "smoke" in p[3]: continue
    arm, rp, tag = p[1], p[2], p[3]
    f = glob.glob(f"{art}/{rid}/*/lab-metrics.json")
    if not f: print("MISSING", rid, title); continue
    m = json.load(open(f[0])); m["rid"] = rid
    model = "opus" if "-opus-" in tag else "sonnet"
    rnd = tag.rsplit("-", 1)[1]
    rows[(model, rp, rnd, arm)] = m
errs = []
for k, m in rows.items():
    rev = m.get("review", "")
    if m.get("is_error") or not m.get("total_cost_usd") or "Credit balance is too low" in rev or "Credit balance" in json.dumps(m.get("result_head", "")):
        errs.append((k, m["rid"], m.get("is_error"), m.get("total_cost_usd")))
print("rows", len(rows), "errors", len(errs), errs)
def boot(pairs, B=10000):
    by = collections.defaultdict(list)
    for (task, d) in pairs: by[task].append(d)
    tasks = list(by); rng = random.Random(1); out = []
    for _ in range(B):
        s = [x for t in (rng.choice(tasks) for _ in tasks) for x in by[t]]
        out.append(sum(s) / len(s))
    out.sort()
    return out[int(.025 * B)], out[int(.975 * B)]
res = {}
for model in ("sonnet", "opus"):
    keys = sorted({(k[1], k[2]) for k in rows if k[0] == model})
    pr = []; D = []; G = []
    for rp, rnd in keys:
        d, g = rows.get((model, rp, rnd, "direct-ts")), rows.get((model, rp, rnd, "gateway"))
        if d and g: pr.append((rp, rnd, d, g))
    if not pr: continue
    lr = [(rp, math.log(g["total_cost_usd"] / d["total_cost_usd"])) for rp, rnd, d, g in pr]
    mean = sum(x for _, x in lr) / len(lr)
    lo, hi = boot(lr)
    def avg(arm_idx, f): return sum(f(x[arm_idx]) for x in pr) / len(pr)
    cost = lambda m: m["total_cost_usd"]
    r = dict(n_pairs=len(pr), tasks=len({p[0] for p in pr}), pct=math.exp(mean) - 1, ci=(math.exp(lo) - 1, math.exp(hi) - 1),
             cheaper=sum(1 for _, x in lr if x < 0))
    for nm, i in (("direct", 2), ("gateway", 3)):
        r[nm] = dict(cost=avg(i, cost), turns=avg(i, lambda m: m["num_turns"]), api=avg(i, lambda m: m.get("api_requests", 0)),
                     uncached=avg(i, lambda m: m["input_tokens"]), cw=avg(i, lambda m: m["cache_creation_input_tokens"]),
                     cr=avg(i, lambda m: m["cache_read_input_tokens"]), out=avg(i, lambda m: m["output_tokens"]))
    r["net"] = r["direct"]["cost"] - r["gateway"]["cost"] - FEE * r["gateway"]["api"]
    r["net_turns"] = r["direct"]["cost"] - r["gateway"]["cost"] - FEE * r["gateway"]["turns"]
    res[model] = r
    print(model, json.dumps(r, indent=1))
    print("per pair:")
    for rp, rnd, d, g in pr:
        print(f"  {rp} {rnd} d ${d['total_cost_usd']:.4f}/{d['num_turns']} g ${g['total_cost_usd']:.4f}/{g['num_turns']} {d['rid']} {g['rid']}")
json.dump({k: v for k, v in res.items()}, open("work/stats.json", "w"), indent=1)
print("total spend", sum(m["total_cost_usd"] or 0 for m in rows.values()))
