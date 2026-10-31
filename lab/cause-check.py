# Cause check, no model call. Input: the real failing test log (out/baseline.log) and a dir of requests captured from
# the real headless `claude -p` (lab/capture.py, local, no key). We take the captured first request (real tools +
# system + first user turn), append the Bash tool_use and a tool_result holding the real log, and replay it to the
# gateway with x-cm-dry-run: 1 (nothing is sent to a model). Report bytes per block, client vs forwarded.
# Variants: log last message / log followed by 8 small exchanges (older turn), each with is_error true and false.
# Real Claude Code marks a Bash call that exits non-zero as is_error=true, so the failing-test case is is_error=true.
import base64, glob, json, os, sys, urllib.request
log = open(sys.argv[1], errors="replace").read(); capdir = sys.argv[2]
caps = [json.load(open(f)) for f in sorted(glob.glob(capdir + "/*.json"))]
caps = [c for c in caps if c["path"].startswith("/v1/messages") and (c["body"].get("tools") or [])]
assert caps, "no captured request with tools"
cap = max(caps, key=lambda c: len(json.dumps(c["body"].get("tools"))))
body0 = cap["body"]
print("captured:", len(caps), "requests; used model=%s tools=%d msgs=%d" % (body0.get("model"), len(body0.get("tools") or []), len(body0["messages"])))
H = {k: v for k, v in cap["headers"].items() if k.lower() not in ("host", "content-length", "_auth", "accept-encoding", "connection", "x-api-key", "authorization")}
H["x-api-key"] = "sk-ant-lab-dry-not-a-key"; H["content-type"] = "application/json"
for line in os.environ["ANTHROPIC_CUSTOM_HEADERS"].splitlines():
    k, _, v = line.partition(":"); H[k.strip()] = v.strip()
D = lambda x: len(json.dumps(x, separators=(",", ":"), ensure_ascii=False))
def text_of(b):
    c = b.get("content"); return c if isinstance(c, str) else "".join(x.get("text", "") for x in (c or []) if isinstance(x, dict))
def blocks(body):
    tr = 0; other = 0; n_tr = 0
    for m in body.get("messages", []):
        c = m["content"]
        if isinstance(c, str): other += len(c); continue
        for b in c:
            if b.get("type") == "tool_result": tr += len(text_of(b)); n_tr += 1
            else: other += D(b)
    return {"tools": D(body.get("tools") or []), "system": D(body.get("system") or []), "messages_non_result": other, "tool_results": tr, "n_tool_results": n_tr, "total": D(body)}
def mk(msgs, is_err):
    tu = lambda i, n, inp: {"role": "assistant", "content": [{"type": "tool_use", "id": f"toolu_{i:02d}", "name": n, "input": inp}]}
    tr = lambda i, t, e=False: {"role": "user", "content": [dict({"type": "tool_result", "tool_use_id": f"toolu_{i:02d}", "content": t}, **({"is_error": True} if e else {}))]}
    cmd = os.environ.get("TASK_TEST", "pytest")
    m = list(body0["messages"]) + [tu(1, "Bash", {"command": cmd}), tr(1, log, is_err)]
    if msgs == "older":
        for i in range(2, 10): m += [tu(i, "Read", {"file_path": f"/repo/f{i}.txt"}), tr(i, "line %d\n" % i * 20)]
    b = dict(body0); b["messages"] = m; return b
def send(b):
    req = urllib.request.Request(os.environ["ANTHROPIC_BASE_URL"] + "/v1/messages", json.dumps(b).encode(), H)
    raw = urllib.request.urlopen(req, timeout=120).read().decode(); txt = ""
    for ln in raw.splitlines():
        if ln.startswith("data:"):
            try: e = json.loads(ln[5:])
            except Exception: continue
            if e.get("type") == "content_block_delta": txt += e["delta"].get("text", "")
    assert txt.startswith("cm-dry-run:"), raw[:300]
    return json.loads(base64.b64decode(txt[11:]))
os.makedirs("out", exist_ok=True); res = {}
print("log bytes:", len(log))
for where in ("last", "older"):
    for is_err in (True, False):
        b = mk(where, is_err); p = send(b); fb = p["body"]
        c, f = blocks(b), blocks(fb)
        # the big result in the forwarded body: first tool_result whose text is not tiny
        big = None
        for m in fb["messages"]:
            if isinstance(m["content"], list):
                for x in m["content"]:
                    if x.get("type") == "tool_result" and (len(text_of(x)) > 2000 or "context-mode" in text_of(x)): big = x; break
            if big: break
        t = text_of(big) if big else ""
        key = f"{where}_is_error={str(is_err).lower()}"
        res[key] = {"client": c, "forwarded": f, "log_whole": t == log, "forwarded_log_bytes": len(t), "log_is_error_flag_kept": bool(big and big.get("is_error")), "head": t[:120]}
        print("== %s" % key)
        for k in ("tools", "system", "messages_non_result", "tool_results", "total"): print("   %-20s client %8d  forwarded %8d  delta %+d" % (k, c[k], f[k], f[k] - c[k]))
        print("   log whole: %s  forwarded_log_bytes=%d  is_error kept=%s" % (t == log, len(t), bool(big and big.get("is_error"))))
        if t != log: print("   head=%r\n   tail=%r" % (t[:200], t[-200:]))
json.dump(res, open("out/cause-check.json", "w"), indent=1)
