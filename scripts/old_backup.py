#!/usr/bin/env python3 
"""
old_backup.py -- back up EVERY entry of an old Roblox experience to local files.

READ-ONLY against the old universe. Nothing there is ever changed.

Output:  <BACKUP_DIR>/<store>.jsonl   (one JSON object per line)

    {"id": "<key>", "value": <data>, "_store": "<store>"}
    {"id": "<key>", "error": "<message>", "_store": "<store>"}   # failed entry

Safe to re-run: already-downloaded keys are skipped (resumable).

Usage:
    python scripts/old_backup.py              # full backup
    python scripts/old_backup.py --selftest   # just check the key + universe
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import config
except ImportError:
    sys.exit("ERROR: copy scripts/config.example.py to scripts/config.py and edit it first.")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KEY  = config.load_key()
UNIV = config.OLD_UNIVERSE
OUT  = config.BACKUP_DIR
os.makedirs(OUT, exist_ok=True)
LOG  = os.path.join(OUT, "backup.log")
BASE = f"https://apis.roblox.com/cloud/v2/universes/{UNIV}"


def log(msg: str) -> None:
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg) + "\n")
    print(msg, flush=True)


def get(url: str, tries: int = 6):
    """GET JSON with exponential back-off on 429 / 5xx."""
    req = urllib.request.Request(url, headers={"x-api-key": KEY})
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 or e.code >= 500:
                time.sleep(min(30, 0.5 * (2 ** i)))
                continue
            raise
        except Exception as e:
            last = e
            time.sleep(min(10, 0.5 * (2 ** i)))
            continue
    raise RuntimeError(f"GET failed: {url} :: {last}")


def list_keys(store: str):
    """Page through every key in a store (v2 API)."""
    keys, token = [], None
    q = urllib.parse.quote(store, safe="")
    while True:
        url = f"{BASE}/data-stores/{q}/entries?maxPageSize=100"
        if token:
            url += "&pageToken=" + urllib.parse.quote(token)
        r = get(url)
        for e in r.get("dataStoreEntries", []):
            keys.append(e["path"].split("/entries/")[-1])
        token = r.get("nextPageToken")
        if not token:
            break
    return keys


def entry_url(store: str, key: str) -> str:
    return (f"{BASE}/data-stores/{urllib.parse.quote(store, safe='')}"
            f"/entries/{urllib.parse.quote(key, safe='')}")


def selftest() -> bool:
    try:
        t0 = time.time()
        r = get(f"{BASE}/data-stores/TimeStats/entries?maxPageSize=1")
        n = len(r.get("dataStoreEntries", []))
        log(f"self-test OK in {round(time.time()-t0, 2)}s entries={n}")
        return True
    except Exception as e:
        log(f"self-test FAIL: {e}")
        log("  -> check API_KEY_FILE, the key's universe access, and OLD_UNIVERSE")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="only test the key/universe")
    ap.add_argument("--stores", nargs="*", help="only back up these store names")
    a = ap.parse_args()

    log("=== OLD BACKUP START ===")
    if not selftest():
        return
    if a.selftest:
        return

    stores = a.stores or config.STORES
    for store in stores:
        fn = os.path.join(OUT, config.safe_filename(store) + ".jsonl")
        done = set()
        if os.path.exists(fn):
            with open(fn, encoding="utf-8") as f:
                for ln in f:
                    try:
                        i = json.loads(ln).get("id") or ""
                        if i:
                            done.add(i.split("global/")[-1])
                    except Exception:
                        pass
        log(f"STORE '{store}' start (already done: {len(done)})")
        try:
            keys = list_keys(store)
        except Exception as e:
            log(f"STORE '{store}' LIST ERROR: {e}")
            continue
        todo = [k for k in keys if k not in done]
        log(f"STORE '{store}' keys={len(keys)} todo={len(todo)}")
        n = 0
        if todo:
            with open(fn, "a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=24) as ex:
                futs = {ex.submit(get, entry_url(store, k)): k for k in todo}
                for fu in as_completed(futs):
                    k = futs[fu]
                    try:
                        rec = fu.result()
                        rec["id"] = k
                        rec["_store"] = store
                    except Exception as e:
                        rec = {"id": k, "error": str(e), "_store": store}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
                    if n % 250 == 0:
                        f.flush()
                        log(f"  '{store}' {n}/{len(todo)}")
                f.flush()
        log(f"STORE '{store}' DONE")
    log("=== OLD BACKUP ALL DONE ===")


if __name__ == "__main__":
    main()
