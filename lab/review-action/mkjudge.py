# Builds blind judge files (one per pair) into lab/review-action/judge/. Key (A/B order) goes to work/judgekey.json, outside the repo.
import json, glob, random, sys, os
art, tsv, diffs = sys.argv[1], sys.argv[2], sys.argv[3]
rows = {}
for l in open(tsv):
    rid, title, c = l.rstrip("\n").split("\t"); p = title.split(); arm, rp, tag = p[1], p[2], p[3]
    f = (glob.glob(f"{art}/{rid}/*/lab-metrics.json") + glob.glob(f"{art}/{rid}/lab-metrics.json"))[0]
    rows[(tag, rp, arm)] = json.load(open(f)).get("review", "")
rng = random.Random(7); key = {}; n = 0
os.makedirs("lab/review-action/judge", exist_ok=True)
for tag in sorted({k[0] for k in rows}):
    base = "direct" if "-direct-" in tag else "direct-ts"
    for rp in sorted({k[1] for k in rows if k[0] == tag}):
        d, g = rows[(tag, rp, base)], rows[(tag, rp, "gateway")]
        flip = rng.random() < 0.5
        a, b = (g, d) if flip else (d, g)
        jid = f"j{n:02d}"; n += 1
        key[jid] = dict(tag=tag, pr=rp, base=base, A="gateway" if flip else base, B=base if flip else "gateway")
        diff = open(f"{diffs}/{rp.replace('/', '_').replace('#', '_')}.diff", errors="replace").read()
        open(f"lab/review-action/judge/{jid}.md", "w").write(f"# PR diff (the real change)\n\n```diff\n{diff}\n```\n\n# REVIEW A\n\n{a}\n\n# REVIEW B\n\n{b}\n")
json.dump(key, open("work/judgekey.json", "w"), indent=1)
print(n, "judge files")
