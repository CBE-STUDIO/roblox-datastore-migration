#!/usr/bin/env python3
"""
build_ops.py -- turn the OLD backup into a safe migration plan (ops.json).

It compares the backup with the CURRENT state of the NEW game and decides, per key,
whether to write, merge, or skip. It does NOT write anything.

Outputs (in WORK_DIR):
    ops.json         the plan: [{"store","key","mode","value"}, ...]
    build_report.txt per-store summary
    conflicts.txt    every merge decision that was made

Usage:
    python scripts/build_ops.py
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

KEY   = config.load_key()
NEW   = config.NEW_UNIVERSE
BK    = config.BACKUP_DIR
OUT   = config.WORK_DIR
os.makedirs(OUT, exist_ok=True)
REPORT = os.path.join(OUT, "build_report.txt")


def rpt(m):
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(str(m) + "\n")
    print(m)


# --------------------------------------------------------------------------- #
# read helpers (NEW game, read-only)
# --------------------------------------------------------------------------- #
def _api(url):
    req = urllib.request.Request(url, headers={"x-api-key": KEY})
    for i in range(6):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(min(20, 0.5 * (2 ** i)))
                continue
            raise
        except Exception:
            time.sleep(min(10, 0.5 * (2 ** i)))
            continue
    raise RuntimeError("fail " + url)


def list_entries(u, store):
    keys, token = [], None
    q = urllib.parse.quote(store, safe="")
    while True:
        url = f"https://apis.roblox.com/cloud/v2/universes/{u}/data-stores/{q}/entries?maxPageSize=100"
        if token:
            url += "&pageToken=" + urllib.parse.quote(token)
        r = _api(url)
        for e in r.get("dataStoreEntries", []):
            keys.append(e["path"].split("/entries/")[-1])
        token = r.get("nextPageToken")
        if not token:
            break
    return keys


def get_entry(u, store, key):
    url = (f"https://apis.roblox.com/cloud/v2/universes/{u}/data-stores/"
           f"{urllib.parse.quote(store, safe='')}/entries/{urllib.parse.quote(key, safe='')}")
    return _api(url).get("value")


def read_store(u, store):
    """Return {key: value} for a whole store (best effort)."""
    d = {}
    try:
        ks = list_entries(u, store)
    except Exception:
        return d
    for k in ks:
        try:
            d[k] = get_entry(u, store, k)
        except Exception:
            pass
    return d


def load_bk(store):
    """Return [(key, value), ...] from the backup for one OLD store name."""
    fn = os.path.join(BK, config.safe_filename(store) + ".jsonl")
    rows = []
    if not os.path.exists(fn):
        return rows
    for ln in open(fn, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            o = json.loads(ln)
        except Exception:
            continue
        if "error" in o:
            continue
        rows.append((o["id"].split("global/")[-1], o.get("value")))
    return rows


# --------------------------------------------------------------------------- #
# merge rules
# --------------------------------------------------------------------------- #
def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def merge_max(old, new):
    """numbers -> max; dicts -> merge per key; lists -> union; else keep NEW."""
    if new is None:
        return old
    if old is None:
        return new
    if isinstance(old, dict) and isinstance(new, dict):
        out = dict(old)
        for k, v in new.items():
            out[k] = merge_max(old.get(k), v)
        return out
    if isinstance(old, list) and isinstance(new, list):
        return old + [x for x in new if x not in old]
    if isnum(old) and isnum(new):
        return max(old, new)
    return new


# --------------------------------------------------------------------------- #
# plan builder
# --------------------------------------------------------------------------- #
OPS = []
CONFLICTS = []


def add(store, key, value):
    if value is not None:
        OPS.append({"store": store, "key": key, "mode": "set", "value": value})


def process(old_store, new_store, merge=True, skip_if_new=False):
    """Build ops for one store."""
    new_cur = read_store(NEW, new_store)
    rows = load_bk(old_store)
    n = 0
    for key, val in rows:
        if val is None:
            continue
        v = val
        if key in new_cur and new_cur[key] is not None:
            if skip_if_new:
                CONFLICTS.append(("skip-existing", new_store, key))
                continue
            if merge:
                v = merge_max(new_cur[key], val)
                CONFLICTS.append(("merge-max", new_store, key))
            else:
                CONFLICTS.append(("keep-new", new_store, key))
                continue
        add(new_store, key, v)
        n += 1
    rpt(f"{old_store}  ->  {new_store} : op-rows={n} "
        f"(backup-rows={len(rows)}, new-existing={len(new_cur)})")


# --- per-store policy: "merge" (default) or "keep_new" ------------------------
# Edit this dict to change how a specific store behaves.
POLICY = {
    # "DanceFavorites_v1": "keep_new",
    # "PlayerGroupIcons":  "keep_new",
    # "PendingGifts_v1":   "keep_new",
}
DEFAULT_POLICY = "merge"


def main():
    rpt(f"build_ops start  old_universe={config.OLD_UNIVERSE} new_universe={config.NEW_UNIVERSE}")
    rpt("")

    for old_store in config.STORES:
        new_store = config.new_name(old_store)
        pol = POLICY.get(old_store, DEFAULT_POLICY)
        if pol == "keep_new":
            process(old_store, new_store, merge=False, skip_if_new=True)
        else:
            process(old_store, new_store, merge=True)

    # write ops
    opsfile = os.path.join(OUT, "ops.json")
    with open(opsfile, "w", encoding="utf-8") as f:
        json.dump(OPS, f, ensure_ascii=False)

    with open(os.path.join(OUT, "conflicts.txt"), "w", encoding="utf-8") as f:
        for c in CONFLICTS:
            f.write(" | ".join(map(str, c)) + "\n")

    rpt("")
    rpt(f"TOTAL OPS: {len(OPS)}")
    rpt(f"CONFLICTS: {len(CONFLICTS)} (see conflicts.txt)")
    rpt(f"ops.json bytes: {os.path.getsize(opsfile)}")


if __name__ == "__main__":
    main()
