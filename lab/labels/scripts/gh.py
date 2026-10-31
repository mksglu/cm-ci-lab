#!/usr/bin/env python3
# Read-only gh wrapper for the label-triage lab (mirrors ./scripts/gh.sh of anthropics/claude-code).
# Only: label list, issue view N [--comments], issue list, search issues. Time-boxed to the target issue:
# the target shows title, body and author only (no labels, no comments, state open); other issues are visible
# only if created before the target, and their comments only if written before it. Writes nothing anywhere.
import json, os, subprocess, sys, time

REPO, NUM, CREATED = os.environ["TASK_REPO"], int(os.environ["TASK_NUMBER"]), os.environ["TASK_CREATED"]


def gh(args):
    for i in range(5):
        r = subprocess.run(["gh"] + args, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
        e = r.stderr.lower()
        if "rate limit" in e or "secondary" in e or "502" in e or "503" in e or "timeout" in e:
            time.sleep(10 * (i + 1)); continue
        break
    sys.stderr.write(r.stderr[:300] + "\n"); sys.exit(1)


def api(path):
    return json.loads(gh(["api", path]))


def lim(rest, default):
    if "--limit" in rest:
        i = rest.index("--limit")
        return int(rest[i + 1]), rest[:i] + rest[i + 2:]
    return default, rest


def show(i, comments_wanted, is_target):
    labels = "" if is_target else ", ".join(l["name"] for l in i["labels"])
    print(f"number: {i['number']}\ntitle: {i['title']}\nstate: {'open' if is_target else i['state']}\nauthor: {i['user']['login']}\nlabels: {labels}\n--\n{i['body'] or ''}")
    if comments_wanted:
        print("\n-- comments --")
        n = 0
        if not is_target:
            for c in api(f"repos/{REPO}/issues/{i['number']}/comments?per_page=100"):
                if c["created_at"] < CREATED:
                    n += 1; print(f"\n{c['user']['login']} ({c['created_at']}):\n{c['body']}")
        if n == 0:
            print("(no comments)")


def main(a):
    if a[:2] == ["label", "list"]:
        n, _ = lim(a[2:], 30)
        print(gh(["label", "list", "-R", REPO, "--limit", str(n), "--json", "name,description", "-q", '.[]|.name+" - "+.description']), end="")
    elif a[:2] == ["issue", "view"] and len(a) >= 3 and a[2].isdigit():
        n = int(a[2])
        if n == NUM:
            show(api(f"repos/{REPO}/issues/{n}"), "--comments" in a, True)
        else:
            i = api(f"repos/{REPO}/issues/{n}")
            if "pull_request" in i or i["created_at"] >= CREATED:
                print("issue not found"); sys.exit(1)
            show(i, "--comments" in a, False)
    elif a[:2] == ["issue", "list"]:
        n, rest = lim(a[2:], 30)
        state = rest[rest.index("--state") + 1] if "--state" in rest else "open"
        out = gh(["issue", "list", "-R", REPO, "--state", state, "--limit", str(n), "--search", f"created:<{CREATED}",
                  "--json", "number,title,state,labels", "-q", '.[]|"#\\(.number) [\\(.state)] \\(.title) (\\([.labels[].name]|join(", ")))"'])
        print(out, end="")
    elif a[:2] == ["search", "issues"] and len(a) >= 3:
        n, rest = lim(a[2:], 30)
        out = gh(["search", "issues", " ".join(rest), "--repo", REPO, "--created", f"<{CREATED}", "--limit", str(n),
                  "--json", "number,title,state,labels", "-q", '.[]|"#\\(.number) [\\(.state)] \\(.title) (\\([.labels[].name]|join(", ")))"'])
        print(out, end="")
    else:
        print("unsupported: use label list | issue view N [--comments] | issue list [--state S] [--limit N] | search issues QUERY [--limit N]"); sys.exit(2)


main(sys.argv[1:])
