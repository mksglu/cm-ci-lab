# Per-message usage anatomy for the clean 1031 area runs. Run from the repo root: python3 -I lab/ci-areas/anatomy.py
# Units are INPUT-side cost units: uncached 1.0, cache write 1.25, cache read 0.1. Output tokens are left out on purpose,
# because the gateway arm streams output_tokens 0 on every message (the stream carries the start-of-message value only).
import glob, json, statistics as st
def load(f):
    d = json.load(open(f)); return list(d.values()) if isinstance(d, dict) else d
AREAS = {"pr-review": load("lab/pr-review/results/runs.json"), "review-action": load("lab/review-action/results/runs.json"),
         "dedupe": [json.load(open(f)) for f in glob.glob("lab/dedupe/results/*.json")], "ci-fix-opus": load("lab/opus/results.json")}
def pm(r): return [p for p in (r.get("per_message_usage") or r.get("pm") or []) if not p.get("sub")]
g = lambda p, a, b: p.get(a, p.get(b, 0)) or 0
W = lambda p: g(p, "in", "uncached") + 1.25 * g(p, "cw", "cache_write") + 0.1 * g(p, "cr", "cache_read")
for area, rs in AREAS.items():
    for model in sorted(set(r["model_input"] for r in rs)):
        out = {}
        for arm in ("direct-ts", "gateway"):
            G = [x for x in (pm(r) for r in rs if r["model_input"] == model and r["arm"] == arm and not r.get("is_error")) if x]
            out[arm] = dict(n=len(G), req=st.mean(len(x) for x in G),
                req1=st.mean(g(x[0], "in", "uncached") + g(x[0], "cw", "cache_write") + g(x[0], "cr", "cache_read") for x in G),
                r1w=st.mean(1.25 * g(x[0], "cw", "cache_write") + g(x[0], "in", "uncached") for x in G),
                later=st.mean(sum(1.25 * g(p, "cw", "cache_write") + g(p, "in", "uncached") for p in x[1:]) for x in G),
                read=st.mean(sum(0.1 * g(p, "cr", "cache_read") for p in x) for x in G),
                big=st.mean(sum(1.25 * g(p, "cw", "cache_write") for p in x[1:] if g(p, "cw", "cache_write") > 3000) for x in G),
                tot=st.mean(sum(W(p) for p in x) for x in G))
        d, w = out["direct-ts"], out["gateway"]; saved = d["tot"] - w["tot"]
        print(f"{area}|{model}|req1 {d['req1']:.0f}->{w['req1']:.0f}|req {d['req']:.1f}->{w['req']:.1f}|saved {saved:.0f} units: "
              f"req1 write {d['r1w']-w['r1w']:.0f}, later writes {d['later']-w['later']:.0f}, reads {d['read']-w['read']:.0f}|"
              f"gateway units {w['tot']:.0f}: later-write share {100*w['later']/w['tot']:.0f}%, writes>3k share {100*w['big']/w['tot']:.0f}%, "
              f"1k prefix tokens = {100*1000*(1.25+0.1*(w['req']-1))/w['tot']:.1f}%")
