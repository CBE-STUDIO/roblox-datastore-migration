# 08 — Verify the migration

Never trust "it said done". Prove it.

## 1. The migration's own numbers

```bash
# ops in the plan
python -c "import json;print(len(json.load(open('mig/ops.json'))))"

# ops actually applied (lines in the ledger)
python -c "print(sum(1 for _ in open('mig/applied_keys.jsonl')))"
```

These should match (minus any keys you deliberately skipped).

Check for failures:

```bash
# should be empty or you should have fixed them
type mig\migrate_fails.txt
```

## 2. Compare a few keys by hand

Pick **3–5 players** you know. Read the key from the new game and compare with the
backup.

**Read from the new game (v1 API):**

```
GET https://apis.roblox.com/datastores/v1/universes/<NEW>/standard-datastores/
    datastore/entries/entry
    ?datastoreName=<store>&scope=global&entryKey=<key>
Header: x-api-key: <your key>
```

**Read from the backup:**

```bash
python -c "import json;[print(json.loads(l)['value']) for l in open('old_backup/TimeStats.jsonl') if json.loads(l)['id']=='123456789']"
```

The values should match (or be **larger** in the new game if a merge took the max).

## 3. Automated count check

Count keys in each store and compare old backup vs new game:

```python
# save as check.py and run: python check.py
import json, urllib.request, urllib.parse, config

KEY, NEW = config.load_key(), config.NEW_UNIVERSE

def count(store):
    leaf, tok, n = store, None, 0
    while True:
        u = f"https://apis.roblox.com/cloud/v2/universes/{NEW}/data-stores/{urllib.parse.quote(leaf)}/entries?maxPageSize=100"
        if tok: u += "&pageToken=" + urllib.parse.quote(tok)
        r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"x-api-key": KEY})))
        n += len(r.get("dataStoreEntries", [])); tok = r.get("nextPageToken")
        if not tok: return n

for old, new in config.STORE_MAP:
    try:
        print(f"{old:45s} -> {new:45s} new={count(new)}")
    except Exception as e:
        print(f"{new:45s} ERROR {e}")
```

## 4. In-game check

The real test: open the **new** game and look.

- Play as a known player → coins/items should match the old game.
- Check the leaderboard top 10 shows the same names.
- Check the donation board total.

## 5. What "good" looks like

| Check | Expected |
|-------|----------|
| applied == planned | ✅ (allow a few deliberate skips) |
| `migrate_fails.txt` | empty |
| random 5 players | match or higher |
| in-game | looks right |

## 6. If something is wrong

- **A whole store is missing** → the store name in `config.py` was wrong, or the
  suffix (old/new place id) was wrong. Fix, re-run `build_ops.py` + `migrate_oc.py`.
- **A player's value is too small** → the merge kept the new (smaller) number,
  which means the new game already had data for them. Check `conflicts.txt`.
- **Nothing was written** → your key has no `write` scope, or the wrong universe.
  Look at the HTTP codes printed by `migrate_oc.py`.

Next → `docs/09-TROUBLESHOOTING.md`
