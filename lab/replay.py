"""Replay requests captured by lab/capture.py against api.anthropic.com with the real key, one variant per
difference, to find which request field makes Anthropic answer billing_error. Prints status + error type +
usage only. Never prints a key. max_tokens is capped at 64 to keep spend tiny."""
import json, os, sys, glob, urllib.request, ssl
key = os.environ["LAB_API_KEY"]
src = sys.argv[1]; out = sys.argv[2]
def send(path, headers, body):
    h = {k: v for k, v in headers.items() if k.lower() not in ("host", "content-length", "_auth", "accept-encoding", "connection")}
    h["x-api-key"] = key
    body = dict(body); body["max_tokens"] = 64
    if isinstance(body.get("thinking"), dict) and body["thinking"].get("type") == "enabled": body.pop("thinking")
    req = urllib.request.Request("https://api.anthropic.com" + path, data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=120); raw = r.read().decode(errors="replace"); st = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace"); st = e.code
    err = None; usage = None
    for line in raw.splitlines():
        if line.startswith("data: "):
            try: ev = json.loads(line[6:])
            except Exception: continue
            if ev.get("type") == "error": err = ev.get("error")
            if ev.get("type") == "message_start": usage = ev["message"].get("usage")
    if st >= 400:
        try: err = json.loads(raw).get("error")
        except Exception: err = {"raw_bytes": len(raw)}
    return {"status": st, "error": err, "usage": usage}
def swap_entry(body, new):
    b = json.loads(json.dumps(body)); s = b.get("system")
    if isinstance(s, list) and s and "cc_entrypoint=" in s[0].get("text", ""):
        t = s[0]["text"]; a = t.index("cc_entrypoint=") + len("cc_entrypoint="); z = t.index(";", a)
        s[0]["text"] = t[:a] + new + t[z:]
    return b
def drop_billing_block(body):
    b = json.loads(json.dumps(body)); s = b.get("system")
    if isinstance(s, list) and s and s[0].get("text", "").startswith("x-anthropic-billing-header"): b["system"] = s[1:]
    return b
def ua(h, v):
    h = dict(h)
    for k in list(h):
        if k.lower() == "user-agent": h[k] = v
    return h
CLI_UA = "claude-cli/2.1.312 (external, sdk-cli)"
res = []
files = sorted(glob.glob(src + "/*.json"))[:1] + sorted(glob.glob(src + "/*.json"))[2:3]
for f in files:
    d = json.load(open(f)); p, h, b = d["path"], d["headers"], d["body"]
    variants = [("orig", h, b), ("ua=sdk-cli", ua(h, CLI_UA), b), ("entry=sdk-cli", h, swap_entry(b, "sdk-cli")),
                ("ua+entry=sdk-cli", ua(h, CLI_UA), swap_entry(b, "sdk-cli")), ("no-billing-block", h, drop_billing_block(b))]
    for name, hh, bb in variants:
        r = send(p, hh, bb); r.update(file=os.path.basename(f), variant=name); res.append(r)
        print(json.dumps(r))
json.dump(res, open(out, "w"), indent=1)
