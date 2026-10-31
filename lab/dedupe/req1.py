import json,glob,sys,collections
root=sys.argv[1]
d=collections.defaultdict(list)
for f in glob.glob(root+"/*/*/lab-metrics.json"):
    m=json.load(open(f))
    if "per_message_usage" not in m: print("missing",f); continue
    p=[x for x in m["per_message_usage"] if not x["sub"]]
    first=p[0]; d[m["arm"]].append(first["in"]+first["cw"]+first["cr"])
for a,v in d.items(): print(a,len(v),sum(v)/len(v),min(v),max(v))
