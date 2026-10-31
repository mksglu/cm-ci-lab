import json, os, subprocess, sys, time
REPO = os.environ["GITHUB_REPOSITORY"]; BEFORE = os.environ["DEDUPE_BEFORE"]; TARGET = int(os.environ["DEDUPE_TARGET"])
def die(m): print("Error: " + m, file=sys.stderr); sys.exit(1)
def api(args):
    for i in range(6):
        p = subprocess.run(["gh", "api"] + args, capture_output=True, text=True)
        if p.returncode == 0: return json.loads(p.stdout or "null")
        if "rate limit" in (p.stderr + p.stdout).lower() or "secondary" in p.stderr.lower(): time.sleep(8 * (i + 1)); continue
        if "404" in p.stderr or "Not Found" in p.stdout: die("not found")
        die(p.stderr.strip()[:200])
    die("rate limited")
def show(i, comments):
    if i["number"] == TARGET:
        print(f"title: {i['title']}\nstate: OPEN\nnumber: {i['number']}\nlabels:\n--\n{i.get('body') or ''}"); return
    if i["created_at"] >= BEFORE: die("not found")
    print(f"title: {i['title']}\nstate: {i['state'].upper()}\nnumber: {i['number']}\nlabels: {', '.join(l['name'] for l in i.get('labels', []))}\n--\n{i.get('body') or ''}")
    if comments:
        for c in api([f"repos/{REPO}/issues/{i['number']}/comments?per_page=100"]):
            if c["created_at"] < BEFORE: print(f"\n--- comment by {c['user']['login']} ---\n{c.get('body') or ''}")
def parse(a):
    pos, fl, k = [], {}, 0
    while k < len(a):
        x = a[k]
        if x.startswith("--"):
            n = x.split("=")[0]
            if n not in ("--comments", "--state", "--limit", "--label"): die("only --comments, --state, --limit, --label flags are allowed")
            if n == "--comments": fl[n] = True
            elif "=" in x: fl[n] = x.split("=", 1)[1]
            else: k += 1; fl[n] = a[k]
        else: pos.append(x)
        k += 1
    return pos, fl
s1, s2 = (sys.argv[1:3] + ["", ""])[:2]; pos, fl = parse(sys.argv[3:]); lim = int(fl.get("--limit", 30))
if (s1, s2) == ("issue", "view"):
    if not pos: die("issue number required")
    show(api([f"repos/{REPO}/issues/{int(pos[0].lstrip('#'))}"]), bool(fl.get("--comments")))
elif (s1, s2) == ("search", "issues"):
    q = f"repo:{REPO} is:issue created:<{BEFORE} " + " ".join(pos)
    if fl.get("--state") in ("open", "closed"): q += f" state:{fl['--state']}"
    if fl.get("--label"): q += f' label:"{fl["--label"]}"'
    r = api(["-X", "GET", "search/issues", "-f", f"q={q}", "-f", f"per_page={min(lim, 100)}"])
    for i in r["items"]:
        if i["number"] != TARGET and i["created_at"] < BEFORE: print(f"{i['number']}\t{i['state'].upper()}\t{i['title']}\t{i['created_at'][:10]}")
elif (s1, s2) == ("issue", "list"):
    st = fl.get("--state", "open"); q = f"repo:{REPO} is:issue created:<{BEFORE} sort:created-desc" + ("" if st == "all" else f" state:{st}")
    if fl.get("--label"): q += f' label:"{fl["--label"]}"'
    r = api(["-X", "GET", "search/issues", "-f", f"q={q}", "-f", f"per_page={min(lim, 100)}"])
    for i in r["items"]:
        if i["number"] != TARGET and i["created_at"] < BEFORE: print(f"{i['number']}\t{i['state'].upper()}\t{i['title']}\t{i['created_at'][:10]}")
elif (s1, s2) == ("label", "list"):
    for l in api([f"repos/{REPO}/labels?per_page={min(lim, 100)}"]): print(f"{l['name']}\t{l.get('description') or ''}")
else: die("only 'issue view', 'issue list', 'search issues', 'label list' are allowed")
