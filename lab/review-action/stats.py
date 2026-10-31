# Paired stats for the review-action bench. Usage: python3 -I lab/review-action/stats.py work/art work/runs-all.tsv
# runs-all.tsv: run_id <tab> displayTitle <tab> conclusion. Title: "review-action ARM repo#pr TAG".
import json, glob, math, random, sys, collections
art, tsv = sys.argv[1], sys.argv[2]
FEE = 0.0009
rows = {}
for l in open(tsv):
    rid, title, concl = l.rstrip("\n").split("\t")
    p = title.split(); arm, rp, tag = p[1], p[2], p[3]
    f = glob.glob(f"{art}/{rid}/*/lab-metrics.json") + glob.glob(f"{art}/{rid}/lab-metrics.json")
    m = json.load(open(f[0])); m["rid"] = rid
    model = "opus" if "-opus-" in tag else "sonnet"
    kind = "x" if "-direct-" in tag else "main"
    rows[(model, kind, rp, tag.rsplit("-", 1)[1], arm)] = m
errs = [(k, m["rid"]) for k, m in rows.items() if m.get("is_error") or not m.get("total_cost_usd") or "Credit balance" in json.dumps(m)]
print("rows", len(rows), "errors", len(errs), errs)
def boot(pairs, B=10000):
    by = collections.defaultdict(list)
    for t, d in pairs: by[t].append(d)
    tasks = list(by); rng = random.Random(1); out = []
    for _ in range(B):
        s = [x for t in (rng.choice(tasks) for _ in tasks) for x in by[t]]
        out.append(sum(s) / len(s))
    out.sort(); return out[int(.025 * B)], out[int(.975 * B)]
res = {}
for model, kind, base in (("sonnet", "main", "direct-ts"), ("opus", "main", "direct-ts"), ("sonnet", "x", "direct")):
    keys = sorted({(k[2], k[3]) for k in rows if k[0] == model and k[1] == kind})
    pr = []
    for rp, rnd in keys:
        d, g = rows.get((model, kind, rp, rnd, base)), rows.get((model, kind, rp, rnd, "gateway"))
        if d and g: pr.append((rp, rnd, d, g))
    lr = [(rp, math.log(g["total_cost_usd"] / d["total_cost_usd"])) for rp, rnd, d, g in pr]
    mean = sum(x for _, x in lr) / len(lr); lo, hi = boot(lr)
    def avg(i, f): return sum(f(x[i]) for x in pr) / len(pr)
    r = dict(base=base, n_pairs=len(pr), tasks=len({p[0] for p in pr}), pct=math.exp(mean) - 1, ci=(math.exp(lo) - 1, math.exp(hi) - 1), cheaper=sum(1 for _, x in lr if x < 0))
    r1 = lambda m: (lambda pm: pm[0]["in"] + pm[0]["cw"] + pm[0]["cr"])(m["per_message_usage"])
    for nm, i in (("base", 2), ("gateway", 3)):
        r[nm] = dict(cost=avg(i, lambda m: m["total_cost_usd"]), turns=avg(i, lambda m: m["num_turns"]), api=avg(i, lambda m: m.get("api_requests", 0)),
                     uncached=avg(i, lambda m: m["input_tokens"]), cw=avg(i, lambda m: m["cache_creation_input_tokens"]),
                     cr=avg(i, lambda m: m["cache_read_input_tokens"]), out=avg(i, lambda m: m["output_tokens"]), req1=avg(i, r1))
    r["net"] = r["base"]["cost"] - r["gateway"]["cost"] - FEE * r["gateway"]["api"]
    res[f"{model}-{base}"] = r
    print(model, base, json.dumps(r, indent=1))
    if model == "sonnet" and kind == "main":
        for rnd in ("r1", "r2"):
            q = [(rp, x) for (rp, x), (rp2, rnd2, d, g) in zip(lr, pr) if rnd2 == rnd]
            print("  round", rnd, math.exp(sum(x for _, x in q) / len(q)) - 1)
    print("per pair:")
    for rp, rnd, d, g in pr:
        print(f"  {rp} {rnd} base ${d['total_cost_usd']:.4f}/{d['num_turns']} g ${g['total_cost_usd']:.4f}/{g['num_turns']} {d['rid']} {g['rid']}")
json.dump(res, open(sys.argv[3] if len(sys.argv) > 3 else "stats.json", "w"), indent=1)
print("total spend", sum(m["total_cost_usd"] or 0 for m in rows.values()))
