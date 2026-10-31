# Per request, per arm: cache write, cache read, uncached input, output. Usage: anatomy.py <runs-root> <task> <round-tag-suffix>
import glob, json, sys
root, task, rd = sys.argv[1:4]
P = dict(i=3.0, w=3.75, r=0.30, o=15.0)  # Sonnet list $/MTok, used only to split cost by token class
for arm in ("direct-ts", "gateway"):
    for f in glob.glob(root + "/*/*/lab-metrics.json"):
        m = json.load(open(f))
        if m.get("task") == task and m.get("arm") == arm and m["tag"].endswith(rd): break
    u = m["per_message_usage"]
    print(f"\n== {task} {rd} {arm} run {m['run_id']} cost ${m['total_cost_usd']:.4f} requests {len(u)} (sub {sum(x['sub'] for x in u)})")
    print("  # who    uncached  cache_write  cache_read  output  tools")
    for n, x in enumerate(u, 1):
        print(f"  {n:2d} {'sub ' if x['sub'] else 'main'} {x['in']:8d} {x['cw']:11d} {x['cr']:11d} {x['out']:7d}  {','.join(t or '' for t in x['tools'])[:40]}")
    for who in (False, True):
        s = [x for x in u if x["sub"] == who]
        if not s: continue
        t = {k: sum(x[k] for x in s) for k in ("in", "cw", "cr", "out")}
        c = dict(uncached=t["in"] * P["i"], write=t["cw"] * P["w"], read=t["cr"] * P["r"], output=t["out"] * P["o"])
        print(f"  {'sub ' if who else 'main'} totals {t}  list-price $ " + " ".join(f"{k}={v / 1e6:.4f}" for k, v in c.items()))
