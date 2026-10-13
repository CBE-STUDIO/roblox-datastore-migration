# 04 — Back up the OLD game (read-only)

**Goal:** copy every DataStore entry from the old universe into plain files on your
PC. Nothing in the old game is changed.

## Run the backup

```bash
python scripts/old_backup.py
```

It will:

1. Run a **self-test** (proves your key + universe work).
2. For each store in `config.STORES`, **list** every key.
3. **Download** each entry (24 threads in parallel, with retries).
4. Append each result as one line of JSON to `old_backup/<store>.jsonl`.

Example output:

```
=== PY BACKUP START ===
self-test OK in 0.39s entries=100
STORE 'TimeStats' start (already done: 0)
STORE 'TimeStats' keys=9634 todo=9634
  'TimeStats' 250/9634
  'TimeStats' 500/9634
  ...
STORE 'TimeStats' DONE
...
=== PY BACKUP ALL DONE ===
```

## It is resumable

Each store's file is appended to. If you stop it (Ctrl+C) or it crashes, just run
it again — it reads the file, sees which keys are already saved, and continues from
there. You will see `already done: N` on restart.

## The backup file format

`old_backup/TimeStats.jsonl` — one JSON object per line:

```json
{"id": "123456789", "value": {"Minutes": 39536, "Cash": 0}, "_store": "TimeStats"}
```

| Field | Meaning |
|-------|---------|
| `id` | the DataStore key (often a user id) |
| `value` | exactly what the game saved |
| `error` | present instead of `value` if that entry failed |

## Listing all stores (bonus)

Not sure what stores exist? This one-liner lists every standard DataStore in the
**old** universe (uses the *v2* cloud API):

```bash
python -c "import json,urllib.request,urllib.parse; k=open(r'C:\\path\\to\\key.txt').read().strip(); u='OLD_UNIVERSE_ID'; r=urllib.request.Request('https://apis.roblox.com/cloud/v2/universes/'+u+'/data-stores', headers={'x-api-key':k}); print(json.dumps(json.load(urllib.request.urlopen(r)), indent=2))"
```

> ⚠️ The v2 endpoint may not be enabled for every key/experience. If it 404s or
> 403s, just read the store names from your game scripts.

## How long does it take?

Roughly **30–60 entries per second**. 10,000 entries ≈ 3–5 minutes. Big games can
take longer because of rate limits.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `HTTP 401` | key is wrong / expired — recreate it |
| `HTTP 403` | key has no access to that universe, or missing scopes |
| Lots of `429` | normal; the script backs off and retries. Just wait. |
| Some lines have `"error"` | run `python scripts/retry_errors.py` (next doc) |

## After the backup

Run the retry pass to fill any gaps:

```bash
python scripts/retry_errors.py
```

It scans each `old_backup/*.jsonl`, collects entries that errored, re-fetches them,
and rewrites the file. You should end with `fixed X/Y` and ideally `no errors`.

Next → `docs/05-BUILD-OPS.md`
