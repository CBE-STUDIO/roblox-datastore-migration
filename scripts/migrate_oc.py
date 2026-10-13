#!/usr/bin/env python3
"""
migrate_oc.py -- apply ops.json into the NEW game using the Open Cloud API.

Features:
  * writes via the DataStore v1 "upsert" endpoint
  * 10 worker threads
  * exponential back-off on 429 / 5xx
  * RESUMABLE: every applied key is appended to WORK_DIR/applied_keys.jsonl,
    so running it again only does the remaining work.

Usage:
    python scripts/migrate_oc.py
    python scripts/migrate_oc.py --workers 6     # if you get throttled
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    import config
except ImportError:
    sys.exit("ERROR: copy scripts/config.example.py to scripts/config.py and edit it first.")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KEY = config.load_key()
NEW = config.NEW_UNIVERSE
MIG = config.WORK_DIR
OPS = json.load(open(os.path.join(MIG, "ops.json"), encoding="utf-8"))
LEDGER = os.path.join(MIG, "applied_keys.jsonl")
FAILLOG = os.path.join(MIG, "migrate_fails.txt")

applied = set()
if os.path.exists(LEDGER):
    for ln in open(LEDGER, encoding="utf-8"):
        try:
            applied.add(json.loads(ln)["id"])
        except Exception:
            pass
print(f"ops={len(OPS)} already-applied={len(applied)}")


def v1post(store, key, val):
    """Upsert one entry. Returns (status_code, message)."""
    u = (f"https://apis.roblox.com/datastores/v1/universes/{NEW}/standard-datastores/"
         f"datastore/entries/entry?datastoreName={urllib.parse.quote(store)}&scope=global"
         f"&entryKey={urllib.parse.quote(key)}")
    data = json.dumps(val, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        u, headers={"x-api-key": KEY, "Content-Type": "application/json"},
        data=data, method="POST")
    for i in range(15):
        try:
            with urllib.request.urlopen(req, timeout=45) as x:
                return x.status, ""
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(min(30, 0.5 * (2 ** i)))
                continue
            try:
                return e.code, e.read().decode()[:150]
            except Exception:
                return e.code, ""
        except Exception:
            time.sleep(min(20, 0.5 * (2 ** i)))
    return -1, "giveup"


lock = threading.Lock()
lf = open(LEDGER, "a", encoding="utf-8")
stats = {"ok": 0, "fail": 0, "skip": 0}
fails = []


def do(o):
    sid = o["store"] + "\x1f" + o["key"]
    if sid in applied:
        with lock:
            stats["skip"] += 1
        return
    st, msg = v1post(o["store"], o["key"], o["value"])
    with lock:
        if st == 200:
            stats["ok"] += 1
            lf.write(json.dumps({"id": sid}) + "\n")
            if stats["ok"] % 500 == 0:
                lf.flush()
                print(f"  applied={stats['ok']} fail={stats['fail']} skip={stats['skip']}", flush=True)
        else:
            stats["fail"] += 1
            fails.append((sid, st, msg))
            print(f"  FAIL {st} {sid} :: {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(do, OPS))
    lf.flush()
    lf.close()
    dt = time.time() - t0
    print(f"DONE ok={stats['ok']} fail={stats['fail']} skip={stats['skip']} "
          f"in {dt:.0f}s ({stats['ok']/max(dt,1):.1f}/s)")
    if fails:
        with open(FAILLOG, "w", encoding="utf-8") as f:
            for sid, st, msg in fails:
                f.write(f"{st} | {sid} | {msg}\n")
        print(f"fails written to {FAILLOG}")
    print("MIGRATE DONE")


if __name__ == "__main__":
    main()
