#!/usr/bin/env python3
"""
retry_errors.py -- re-fetch backup entries that failed (429 / timeout / 5xx).

Reads every <BACKUP_DIR>/<store>.jsonl, finds lines that contain an "error",
re-fetches just those keys, and rewrites the file. De-dupes and keeps order.

Usage:
    python scripts/retry_errors.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

try:
    import config
except ImportError:
    sys.exit("ERROR: copy scripts/config.example.py to scripts/config.py and edit it first.")

KEY = config.load_key()
UNIV = config.OLD_UNIVERSE
DIR = config.BACKUP_DIR
BASE = f"https://apis.roblox.com/cloud/v2/universes/{UNIV}/data-stores/"


def get(store: str, key: str, tries: int = 8):
    url = BASE + quote(store, safe="") + "/entries/" + quote(key, safe="")
    delay = 1.0
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"x-api-key": KEY})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay = min(delay * 1.6, 8.0)
                continue
            return {"error": f"HTTP {e.code}"}
        except Exception:
            time.sleep(delay)
            delay = min(delay * 1.6, 8.0)
    return {"error": "giveup"}


def main() -> None:
    if not os.path.isdir(DIR):
        sys.exit(f"no backup dir '{DIR}' -- run old_backup.py first")

    for fn in sorted(os.listdir(DIR)):
        if not fn.endswith(".jsonl"):
            continue
        path = os.path.join(DIR, fn)
        store = None
        good, order, err = {}, [], []
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                o = json.loads(ln)
                store = store or o.get("_store")
                if "error" in o:
                    if o.get("id"):
                        err.append(o["id"])
                    continue
                i = o.get("id")
                if i not in good:
                    good[i] = o
                    order.append(i)
        err = list(dict.fromkeys(err))
        if not err:
            print(f"{fn:52s} no errors")
            continue
        # infer store name from filename if the file had none
        if not store:
            store = fn[:-6].replace("_", " ", 0)
        print(f"{fn:52s} retrying {len(err)}")

        def work(k):
            r = get(store, k)
            if "error" in r:
                return (k, None)
            r.setdefault("id", k)
            r["_store"] = store
            return (k, r)

        fixed = 0
        with ThreadPoolExecutor(max_workers=4) as ex:
            for k, r in ex.map(work, err):
                if r is None:
                    if k not in good:
                        good[k] = {"id": k, "error": "unresolved", "_store": store}
                        order.append(k)
                else:
                    good[k] = r
                    if k not in order:
                        order.append(k)
                    fixed += 1
        with open(path, "w", encoding="utf-8") as f:
            for k in order:
                f.write(json.dumps(good[k], ensure_ascii=False) + "\n")
        print(f"{fn:52s} fixed {fixed}/{len(err)}")
    print("RETRY DONE")


if __name__ == "__main__":
    main()
