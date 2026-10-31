# Paired stats for the opus triage bench. Usage: python3 analyze.py <artdir>
import json, glob, math, random, os, sys
art = sys.argv[1]
runs = {x['databaseId']: x['displayTitle'] for x in json.load(open(f"{art}/runs.json"))}
rows = {}
for rid, title in runs.items():
    f = glob.glob(f"{art}/{rid}/*/lab-metrics.json")
    if not f: print("MISSING", rid, title); continue
    m = json.load(open(f[0])); pm = glob.glob(f"{art}/{rid}/*/per-message-usage.json")
    m['run'] = rid; m['pm'] = json.load(open(pm[0])) if pm else None
    rows[(m['task'], m['arm'])] = m
tasks = sorted({t for t, _ in rows})
def bad(m): return m.get('is_error') or not m.get('total_cost_usd')
errs = [(k, m.get('result_head')) for k, m in rows.items() if bad(m) or 'Credit balance' in json.dumps(m.get('result_head'))]
print("errors:", errs)
lr = {t: math.log(rows[(t,'gateway')]['total_cost_usd'] / rows[(t,'direct-ts')]['total_cost_usd']) for t in tasks}
mean = sum(lr.values()) / len(lr)
random.seed(1); bs = []
for _ in range(10000):
    s = [random.choice(tasks) for _ in tasks]; bs.append(sum(lr[t] for t in s) / len(s))
bs.sort(); lo, hi = bs[249], bs[9749]
pc = lambda v: (math.exp(v) - 1) * 100
print(f"pairs {len(tasks)} cost {pc(mean):.1f}% CI {pc(lo):.1f}..{pc(hi):.1f} cheaper {sum(v<0 for v in lr.values())}/{len(tasks)}")
for a in ('direct-ts', 'gateway'):
    ms = [rows[(t,a)] for t in tasks]; n = len(ms)
    av = lambda k: sum((m.get(k) or 0) for m in ms) / n
    print(a, f"pass {sum(m['passed'] for m in ms)}/{n} turns {av('num_turns'):.2f} cost {av('total_cost_usd'):.4f} uncached {av('input_tokens'):.0f} cw {av('cache_creation_input_tokens'):.0f} cr {av('cache_read_input_tokens'):.0f} out {av('output_tokens'):.0f}")
md = sum(rows[(t,'direct-ts')]['total_cost_usd'] for t in tasks)/len(tasks); mg = sum(rows[(t,'gateway')]['total_cost_usd'] for t in tasks)/len(tasks)
tg = sum(rows[(t,'gateway')]['num_turns'] for t in tasks)/len(tasks)
print(f"net per run {md-mg-0.0009*tg:.4f} total spend {sum(m['total_cost_usd'] for m in rows.values()):.3f}")
b = sum(1 for t in tasks if rows[(t,'direct-ts')]['passed'] and not rows[(t,'gateway')]['passed']); c = sum(1 for t in tasks if rows[(t,'gateway')]['passed'] and not rows[(t,'direct-ts')]['passed'])
print("direct-only pass", b, "gateway-only pass", c)
for t in tasks:
    d, g = rows[(t,'direct-ts')], rows[(t,'gateway')]
    print(f"{t:9s} d ${d['total_cost_usd']:.4f}/{d['num_turns']}/{d['passed']} {d['run']}  g ${g['total_cost_usd']:.4f}/{g['num_turns']}/{g['passed']} {g['run']}  ratio {math.exp(lr[t]):.2f}")
json.dump({f"{t}|{a}": {k: v for k, v in m.items()} for (t, a), m in rows.items()}, open(f"{art}/all.json", "w"))
