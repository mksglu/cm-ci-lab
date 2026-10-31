# Paired stats for the opus triage bench, N rounds. Usage: python3 analyze2.py <artdir> <tag-prefix>
# <artdir>/runs.json = gh run list json; <artdir>/<runid>/*/{lab-metrics,per-message-usage}.json = artifacts.
import json, glob, math, random, sys
from math import comb
art, prefix = sys.argv[1], sys.argv[2]
runs = {x['databaseId']: x['displayTitle'] for x in json.load(open(f"{art}/runs.json")) if prefix in x['displayTitle']}
rows = {}
for rid, title in runs.items():
    f = glob.glob(f"{art}/{rid}/*/lab-metrics.json")
    if not f: print("MISSING", rid, title); continue
    m = json.load(open(f[0])); pm = glob.glob(f"{art}/{rid}/*/per-message-usage.json")
    m['run'] = rid; m['pm'] = json.load(open(pm[0])) if pm else None
    rows[(m['task'], m['tag'], m['arm'])] = m
pairs = sorted({(t, g) for t, g, _ in rows})
pairs = [p for p in pairs if (p[0], p[1], 'direct-ts') in rows and (p[0], p[1], 'gateway') in rows]
tasks = sorted({t for t, _ in pairs})
def bad(m): return m.get('is_error') or not m.get('total_cost_usd')
errs = [(k, str(m.get('result_head'))[:80]) for k, m in rows.items() if bad(m) or 'Credit balance' in json.dumps(m.get('result_head'))]
print("errors:", errs)
C = lambda t, g, a: rows[(t, g, a)]
lr = {p: math.log(C(*p, 'gateway')['total_cost_usd'] / C(*p, 'direct-ts')['total_cost_usd']) for p in pairs}
mean = sum(lr.values()) / len(lr)
by_task = {t: [lr[p] for p in pairs if p[0] == t] for t in tasks}
random.seed(1); bs = []
for _ in range(10000):
    s = [random.choice(tasks) for _ in tasks]; v = [x for t in s for x in by_task[t]]; bs.append(sum(v) / len(v))
bs.sort(); lo, hi = bs[249], bs[9749]
pc = lambda v: (math.exp(v) - 1) * 100
print(f"pairs {len(pairs)} tasks {len(tasks)} cost {pc(mean):.1f}% CI {pc(lo):.1f}..{pc(hi):.1f} cheaper {sum(v<0 for v in lr.values())}/{len(pairs)}")
for g in sorted({g for _, g in pairs}):
    ps = [p for p in pairs if p[1] == g]; print(" round", g, f"{pc(sum(lr[p] for p in ps)/len(ps)):.1f}%", len(ps))
for a in ('direct-ts', 'gateway'):
    ms = [C(*p, a) for p in pairs]; n = len(ms)
    av = lambda k: sum((m.get(k) or 0) for m in ms) / n
    print(a, f"pass {sum(bool(m['passed']) for m in ms)}/{n} turns {av('num_turns'):.2f} cost {av('total_cost_usd'):.4f} uncached {av('input_tokens'):.0f} cw {av('cache_creation_input_tokens'):.0f} cr {av('cache_read_input_tokens'):.0f} out {av('output_tokens'):.0f}")
md = sum(C(*p, 'direct-ts')['total_cost_usd'] for p in pairs) / len(pairs); mg = sum(C(*p, 'gateway')['total_cost_usd'] for p in pairs) / len(pairs)
tg = sum(C(*p, 'gateway')['num_turns'] for p in pairs) / len(pairs)
print(f"net per run {md-mg-0.0009*tg:.4f} total spend {sum(m['total_cost_usd'] for m in rows.values() if m.get('total_cost_usd')):.3f}")
b = sum(1 for p in pairs if C(*p, 'direct-ts')['passed'] and not C(*p, 'gateway')['passed'])
c = sum(1 for p in pairs if C(*p, 'gateway')['passed'] and not C(*p, 'direct-ts')['passed'])
n = b + c; pv = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)
print(f"McNemar exact: direct-only {b} gateway-only {c} p={pv:.3f}")
# request 1 size (input + cache_write + cache_read of the first assistant message)
for a in ('direct-ts', 'gateway'):
    v = [sum((C(*p, a)['pm'][0].get(k) or 0) for k in ('uncached', 'cache_write', 'cache_read')) for p in pairs if C(*p, a).get('pm')]
    print(a, "request-1 size mean", f"{sum(v)/len(v):.0f}", "n", len(v))
for p in pairs:
    d, g = C(*p, 'direct-ts'), C(*p, 'gateway')
    print(f"{p[0]:9s} {p[1][-2:]} d ${d['total_cost_usd']:.4f}/{d['num_turns']}/{d['passed']} {d['run']}  g ${g['total_cost_usd']:.4f}/{g['num_turns']}/{g['passed']} {g['run']}  ratio {math.exp(lr[p]):.2f}")
json.dump({f"{t}|{g}|{a}": m for (t, g, a), m in rows.items()}, open(f"{art}/all.json", "w"))
