#!/usr/bin/env python3
"""
board_fetch.py -- special-case migration for an aggregate "board" store.

Some stores keep ALL players inside ONE key, e.g.:

    store "Donation Board v4"
      key  "donationboard@donations"        -> { "<uid>": {"Raised":..,"Donated":.., "History":[...]}, ... }
      key  "donationboard@settings"         -> {...}
      key  "donationboard@transferreddata"  -> [...]

That needs bespoke merging (per-user max + history union), so it lives here.

This script fetches both boards, merges them, writes the OLD board to the backup,
and APPENDS the resulting ops to ops.json.

Usage:
    python scripts/board_fetch.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import config
except ImportError:
    sys.exit("ERROR: copy scripts/config.example.py to scripts/config.py and edit it first.")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KEY  = config.load_key()
OLD  = config.OLD_UNIVERSE
NEW  = config.NEW_UNIVERSE
BK   = config.BACKUP_DIR
OUT  = config.WORK_DIR

# ---- EDIT THESE for your board store ----------------------------------------
BOARD = "Donation Board v4"
BKEYS = ["donationboard@donations",
         "donationboard@settings",
         "donationboard@transferreddata"]
# -----------------------------------------------------------------------------


def raw(url):
    req = urllib.request.Request(url, headers={"x-api-key": KEY})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(0.5 * 2 ** i)
                continue
            try:
                return e.code, e.read().decode()
            except Exception:
                return e.code, ""
        except Exception:
            time.sleep(0.5 * 2 ** i)
    return -2, "giveup"


def v1_get(universe, key):
    u = (f"https://apis.roblox.com/datastores/v1/universes/{universe}/standard-datastores/"
         f"datastore/entries/entry?datastoreName={urllib.parse.quote(BOARD)}&scope=global"
         f"&entryKey={urllib.parse.quote(key)}")
    st, b = raw(u)
    if st == 200:
        return json.loads(b)
    return {"__error__": st, "body": b[:200]}


def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def merge_rec(a, b):
    """a = NEW (priority), b = OLD (merged in)."""
    out = dict(a)
    for k, v in b.items():
        if k in a and a[k] is not None:
            av = a[k]
            if isnum(av) and isnum(v):
                out[k] = max(av, v)
            elif isinstance(av, list) and isinstance(v, list):
                out[k] = av + [x for x in v if x not in av]
            elif isinstance(av, dict) and isinstance(v, dict):
                out[k] = merge_rec(av, v)
            else:
                out[k] = av
        else:
            out[k] = v
    return out


def main():
    os.makedirs(BK, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    old = {k: v1_get(OLD, k) for k in BKEYS}
    new = {k: v1_get(NEW, k) for k in BKEYS}

    # save the OLD board to the backup
    with open(os.path.join(BK, config.safe_filename(BOARD) + ".jsonl"), "w", encoding="utf-8") as f:
        for k in BKEYS:
            f.write(json.dumps({"id": k, "value": old[k], "_store": BOARD}, ensure_ascii=False) + "\n")

    ops, conf = [], []

    od, nd = old["donationboard@donations"], new["donationboard@donations"]
    if isinstance(od, dict) and "__error__" not in od:
        ndd = nd if isinstance(nd, dict) and "__error__" not in nd else {}
        merged = {}
        for uid in set(od) | set(ndd):
            if uid in od and uid in ndd:
                merged[uid] = merge_rec(ndd[uid], od[uid])
                conf.append(("merge-max", BOARD, uid))
            else:
                merged[uid] = od.get(uid, ndd.get(uid))
        ops.append({"store": BOARD, "key": "donationboard@donations", "mode": "set", "value": merged})
        print(f"donations: old={len(od)} new={len(ndd)} merged={len(merged)}")
    else:
        print("donations ERROR", od)

    for k in ["donationboard@settings", "donationboard@transferreddata"]:
        ov, nv = old[k], new[k]
        have_new = not (isinstance(nv, dict) and "__error__" in nv)
        if have_new and nv is not None:
            conf.append(("keep-new", BOARD, k))
            print(f"{k}: NEW present -> keep NEW")
        else:
            ops.append({"store": BOARD, "key": k, "mode": "set", "value": ov})
            print(f"{k}: set from OLD")

    of = os.path.join(OUT, "ops.json")
    allops = json.load(open(of, encoding="utf-8")) if os.path.exists(of) else []
    before = len(allops)
    allops.extend(ops)
    json.dump(allops, open(of, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"ops.json: {before} + {len(ops)} board = {len(allops)}")
    with open(os.path.join(OUT, "build_report.txt"), "a", encoding="utf-8") as f:
        f.write(f"{BOARD} -> appended {len(ops)} ops (after {before})\n")
    print("BOARD DONE")


if __name__ == "__main__":
    main()
