#!/usr/bin/env python3
"""
migration_server.py -- optional: serve ops.json to an in-Studio Lua worker.

Use this when your key cannot write (no Open Cloud write scope). The Lua worker
polls this server, runs the write inside Studio, and posts back a result.

Usage:
    python scripts/migration_server.py                 # defaults: WORK_DIR/ops.json, port 8792
    python scripts/migration_server.py mig/ops.json 8792

Endpoints:
    GET  /op?i=N     -> {"store","key","value","i"} | {"done":true,"total":N}
    GET  /status     -> {"total", "applied", "errors", "last_i"}
    POST /log        -> {"i", "ok", "key", "err"}  (worker reports results)
"""

import http.server
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import config
    DEFAULT_OPS = os.path.join(config.WORK_DIR, "ops.json")
except Exception:
    DEFAULT_OPS = "mig/ops.json"

OPS_FILE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OPS
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8792
LOGDIR = os.path.dirname(OPS_FILE) or "."
os.makedirs(LOGDIR, exist_ok=True)
LOGFILE = os.path.join(LOGDIR, "worker.log")

ops = json.load(open(OPS_FILE, encoding="utf-8-sig")) if os.path.exists(OPS_FILE) else []
state = {"applied": 0, "errors": 0, "last_i": -1, "started": time.time()}


def log(m):
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S") + "  " + str(m) + "\n")


class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/op":
            q = urllib.parse.parse_qs(u.query)
            try:
                i = int(q.get("i", ["0"])[0])
            except ValueError:
                i = 0
            if i >= len(ops):
                return self._send({"done": True, "total": len(ops)})
            op = dict(ops[i])
            op["i"] = i
            return self._send(op)
        if u.path == "/status":
            return self._send({"total": len(ops), **state})
        self._send({"error": "not found"}, 404)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except Exception:
            body = {}
        if u.path == "/log":
            if body.get("done"):
                log(f"DONE applied={state['applied']} errors={state['errors']}")
            elif body.get("ok"):
                state["last_i"] = body.get("i")
                state["applied"] += 1
                if body.get("i") and body["i"] % 250 == 0:
                    log(f"progress i={body['i']} applied={state['applied']} errors={state['errors']}")
            else:
                state["errors"] += 1
                log(f"FAIL i={body.get('i')} key={body.get('key')} {body.get('err')}")
            return self._send({"ok": True})
        self._send({"error": "not found"}, 404)

    def log_message(self, *a):
        pass


log(f"=== migration_server start ops={len(ops)} port={PORT} ===")
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
print(f"serving {len(ops)} ops on http://127.0.0.1:{PORT}")
srv.serve_forever()
