# 05 — Build the migration plan

**Goal:** turn the backup files into a single list of write operations, applying the
**merge rules** so we never clobber newer data in the new game.

## Run it

```bash
python scripts/build_ops.py
```

This does **no writing**. It only reads:

- the **backup** (`old_backup/*.jsonl`) — the old data, and
- the **current state** of the new game (a `read` over the API) — to compare.

Then it produces:

| File | What it is |
|------|------------|
| `mig/ops.json` | the **plan** — every entry to write into the new game |
| `mig/build_report.txt` | a summary per store |
| `mig/conflicts.txt` | every time a merge rule fired, and which rule |

## How store-name suffixes are handled

Some games name their stores with the **place id**:

```
AquaClub_PlayerData_v1_79229339887184     ← old place
AquaClub_PlayerData_v1_92993631642161     ← new place
```

`config.py` builds a suffix from each place id. `build_ops.py` rewrites the old
suffix → new suffix, so the data lands in the **right** store:

```
old store  AquaClub_PlayerData_v1_ + OLD_SUFFIX
new store  AquaClub_PlayerData_v1_ + NEW_SUFFIX
```

## The merge rules, in code

The heart of the file is `merge_max`:

```python
def merge_max(old, new):
    if new is None: return old          # nothing there → take old
    if old is None: return new           # nothing old   → take new
    if isinstance(old, dict) and isinstance(new, dict):
        out = dict(old)                  # merge dicts key by key
        for k, v in new.items():
            out[k] = merge_max(old.get(k), v)
        return out
    if isnum(old) and isnum(new):
        return max(old, new)             # numbers → keep the biggest
    return new                            # otherwise → keep new
```

And `process_simple` decides per-store behaviour:

- `merge=True` → merge numbers/dicts, keep the larger.
- `merge=False, skip_if_new=True` → if the key already exists in the new game,
  **keep the new value** (do not touch it).

## Reading the report

Open `mig/build_report.txt`. You will see a line per store:

```
TimeStats  ->  TimeStats : op-rows=7952 (backup-rows=9634, new-existing=0)
```

| Field | Meaning |
|-------|---------|
| `op-rows` | how many entries we will write |
| `backup-rows` | how many rows were in the old backup |
| `new-existing` | how many keys already existed in the new game |

> If `op-rows` is **0**, the new game already has everything — nothing to do.

At the end:

```
TOTAL OPS: 30148
CONFLICTS: 411 (see conflicts.txt)
ops.json bytes: 5042...
```

## Reading `conflicts.txt`

Each line is `rule | store | key`:

```
merge-max | TimeStats | 7848755666
skip-existing | DanceFavorites_v1 | 123
keep-new | Donation Board v4 | donationboard@settings
```

- `merge-max` — both had a number; we will write the bigger one.
- `skip-existing` — new game won; we will not write this key.
- `keep-new` — new game won (field present); we keep it.

You do **not** have to fix conflicts — they are logged so you can audit them.
If you disagree with a rule for a specific store, edit `build_ops.py` and re-run.

## Special cases

Some stores need custom logic. Two examples are included:

- **`AllPlayerIds`** — a single key (`AllIds`) whose value is a **list** of user ids.
  We take the **union** of old and new so nobody is forgotten.
- **`Donation Board v4`** — a dict of per-user donations. We merge each user's
  `Raised`/`Donated` with `max()` and combine their `History` lists.
  `scripts/board_fetch.py` re-fetches both boards and appends the correct ops.

## Re-running is safe

`build_ops.py` overwrites `ops.json` each time. Run it again any time the new game
changed. It always compares against the **current** new-game state.

Next → `docs/06-MIGRATE.md`
