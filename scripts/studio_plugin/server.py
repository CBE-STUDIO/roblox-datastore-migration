#!/usr/bin/env python3
"""
server.py -- standalone localhost bridge for the RobloxStudioMCP.lua plugin.

Stdlib only (no pip installs). Lets you run Lua inside a running Roblox Studio
from the command line -- useful for the *no-Open-Cloud-scope* migration path and
for ordered/leaderboard stores (see docs/07-LEADERBOARDS.md).

Start the bridge:
    python scripts/studio_plugin/server.py

Then, in another terminal, run Lua:
    python scripts/studio_plugin/server.py --lua "return game.PlaceId"
    python scripts/studio_plugin/server.py --lua-file my_code.lua

Protocol (the plugin polls it):
    GET  /poll           -> {cmd:{id,op,args}} | {}
    POST /reply          {id, ok, data|error}
    POST /hello          {plugin, place, placeId, ...}
    GET  /status
    GET  /drop?id=N
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8791
CONNECT_WINDOW = 15.0

_lock = threading.Lock()
_queue: deque = deque()
_waiting: dict = {}
_seq = 0
_plugin_info: dict = {}
_last_seen = 0.0


def _next_id() -> int:
    global _seq
    with _lock:
        _seq += 1
        return _seq


def connected() -> bool:
    return (time.time() - _last_seen) < CONNECT_WINDOW


def call(op: str, args: dict | None = None, timeout: float = 45.0) -> dict:
    if not connected():
        return {"ok": False, "error": "Roblox Studio plugin is not connected "
                "(check plugin installed + Studio restarted + Allow HTTP Requests ON)."}
    cid = _next_id()
    ev = threading.Event()
    entry = {"event": ev, "result": None}
    with _lock:
        _waiting[cid] = entry
        _queue.append(cid)
    if not ev.wait(timeout):
        with _lock:
            _waiting.pop(cid, None)
            try:
                _queue.remove(cid)
            except ValueError:
                pass
        return {"ok": False, "error": f"timeout after {timeout}s (op={op})"}
    with _lock:
        _waiting.pop(cid, None)
    r = entry.get("result")
    return r if isinstance(r, dict) else {"ok": False, "error": "no result"}


def _deliver(cid: int, payload: dict) -> None:
    with _lock:
        entry = _waiting.get(cid)
        try:
            _queue.remove(cid)
        except ValueError:
            pass
    if entry:
        entry["result"] = payload
        entry["event"].set()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        global _last_seen
        u = urlparse(self.path)
        if u.path == "/poll":
            with _lock:
                if not _queue:
                    _last_seen = time.time()
                    return self._send(200, {})
                cid = _queue[0]
                entry = _waiting.get(cid) or {}
                op, args = entry.get("op"), entry.get("args")
            _last_seen = time.time()
            return self._send(200, {"cmd": {"id": cid, "op": op, "args": args}})
        if u.path == "/status":
            return self._send(200, {"connected": connected(), "plugin": _plugin_info,
                                    "queued": len(_queue), "port": PORT})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        global _last_seen, _plugin_info
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except Exception:
            body = {}
        _last_seen = time.time()
        if u.path == "/hello":
            _plugin_info = body
            sys.stderr.write(f"[bridge] studio connected: {body.get('place')} "
                             f"(placeId={body.get('placeId')})\n")
            return self._send(200, {"ok": True})
        if u.path == "/reply":
            cid = int(body.get("id", -1))
            payload = ({"ok": True, **(body.get("data") or {})} if body.get("ok")
                       else {"ok": False, "error": body.get("error", "unknown")})
            _deliver(cid, payload)
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass


def run_bridge():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stderr.write(f"[bridge] listening on http://{HOST}:{PORT}  (Ctrl+C to stop)\n")
    srv.serve_forever()


def main():
    global PORT
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--lua", help="run this Lua code in Studio and print the result")
    ap.add_argument("--lua-file", help="run the Lua in this file and print the result")
    a = ap.parse_args()
    PORT = a.port

    if a.lua or a.lua_file:
        code = a.lua if a.lua else open(a.lua_file, encoding="utf-8").read()
        print(json.dumps(call("lua", {"code": code}), indent=2))
        return
    run_bridge()


if __name__ == "__main__":
    main()
