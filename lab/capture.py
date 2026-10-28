import http.server, json, sys, os, itertools
n=itertools.count()
out=sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        l=int(self.headers.get('content-length','0')); b=self.rfile.read(l)
        i=next(n)
        hd={k:v for k,v in self.headers.items() if k.lower() not in ('x-api-key','authorization')}
        hd['_auth']=[k for k in self.headers.keys() if k.lower() in ('x-api-key','authorization')]
        open(f"{out}/{i:03d}.json","w").write(json.dumps({"path":self.path,"headers":hd,"body":json.loads(b or b'{}')}))
        e=json.dumps({"type":"error","error":{"type":"invalid_request_error","message":"capture stop"}}).encode()
        self.send_response(400); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(e))); self.end_headers(); self.wfile.write(e)
    def do_GET(self):
        self.send_response(404); self.end_headers()
    def log_message(self,*a): pass
http.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),H).serve_forever()
