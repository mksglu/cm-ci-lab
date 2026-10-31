# Dry-run probe: what does the gateway forward for a CI turn whose tool_result is the real big test log?
# Sends two synthetic bodies to /v1/messages with x-cm-dry-run: 1 (no model call, nothing billed):
#   A: the log is the LAST message (the turn right after the test command ran)
#   B: the log is followed by 8 more small tool exchanges (a later turn, the log is no longer in the tail)
# Env: ANTHROPIC_BASE_URL, ANTHROPIC_CUSTOM_HEADERS (from path-env.sh gateway-dry). Prints no secret.
import base64, json, os, sys, urllib.request
log = open(sys.argv[1], errors="replace").read()
cmd = os.environ.get("TASK_TEST", "pytest")
hdrs = {"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": "sk-ant-lab-dry-not-a-key"}
for line in os.environ["ANTHROPIC_CUSTOM_HEADERS"].splitlines():
    k, _, v = line.partition(":"); hdrs[k.strip()] = v.strip()
def tu(i, name, inp): return {"role": "assistant", "content": [{"type": "tool_use", "id": f"toolu_{i:02d}", "name": name, "input": inp}]}
def tr(i, text): return {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"toolu_{i:02d}", "content": text}]}
first = {"role": "user", "content": "CI failed. Run `%s`, find the root cause, fix it with the smallest change." % cmd}
base = [first, tu(1, "Bash", {"command": cmd}), tr(1, log)]
more = []
for i in range(2, 10): more += [tu(i, "Read", {"file_path": f"/repo/f{i}.txt"}), tr(i, "line %d\n" % i * 20)]
def send(msgs):
    body = {"model": "claude-sonnet-5-5", "max_tokens": 1024, "stream": True, "messages": msgs,
            "tools": [{"name": n, "description": n, "input_schema": {"type": "object", "properties": {}}} for n in ("Bash", "Read")]}
    req = urllib.request.Request(os.environ["ANTHROPIC_BASE_URL"] + "/v1/messages", json.dumps(body).encode(), hdrs)
    raw = urllib.request.urlopen(req, timeout=120).read().decode()
    i = raw.find("cm-dry-run:"); assert i >= 0, raw[:300]
    b64 = raw[i + 11:].split('"')[0].split("\\")[0]
    return json.loads(base64.b64decode(b64))
os.makedirs("out", exist_ok=True)
for name, msgs in (("A_last_message", base), ("B_older_turn", base + more)):
    p = send(msgs); fb = p["body"]["messages"]
    def result_of(m):
        c = m["content"]; c = c if isinstance(c, list) else []
        for b in c:
            if b.get("type") == "tool_result":
                t = b["content"]; t = t if isinstance(t, str) else "".join(x.get("text", "") for x in t)
                if t and (len(t) > 2000 or "context-mode" in t): return t
    kept = [(i, result_of(m)) for i, m in enumerate(fb) if result_of(m)]
    print(f"== {name}: sent_log_bytes={len(log)} sent_msgs={len(msgs)} forwarded_msgs={len(fb)} forwarded_body_bytes={len(json.dumps(p['body']))} tenant={p.get('tenant')}")
    for i, t in kept:
        print(f"   msg[{i}] tool_result bytes={len(t)} whole={t == log} head={t[:160]!r}")
        print(f"   tail={t[-300:]!r}")
    if not kept: print("   no oversized tool_result left; first msgs:", json.dumps(fb[:4])[:400])
    json.dump(p["body"]["messages"], open(f"out/dry-forwarded-{name}.json", "w"))
