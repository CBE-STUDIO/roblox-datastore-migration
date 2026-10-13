# 06 — Run the migration

**Goal:** write every operation in `mig/ops.json` into the new game — safely,
with retries and a resumable ledger.

## Run it

```bash
python scripts/migrate_oc.py
```

It prints:

```
ops=30148 already-applied=0
  applied=500 fail=0 skip=0
  applied=1000 fail=0 skip=0
  ...
DONE ok=30148 fail=0 skip=0 in 2987s (10.1/s)
MIGRATE DONE
```

## How it works

- Uses the **DataStore v1 write API**:

  ```
  POST https://apis.roblox.com/datastores/v1/universes/<NEW>/standard-datastores/
       datastore/entries/entry
       ?datastoreName=<store>&scope=global&entryKey=<key>
  ```

  with header `x-api-key: <your key>` and the value as the JSON body.

- Runs **10 threads** in parallel.
- On `429` (rate limit) or `5xx`, retries with **exponential back-off**
  (0.5s, 1s, 2s, … up to 30s, 15 tries).
- On success, appends `{"id": "<store>\x1f<key>"}` to `mig/applied_keys.jsonl`.

## It is resumable — this is the important part

At startup it loads `mig/applied_keys.jsonl` and **skips anything already applied**.

So if the power goes out, Studio crashes, or you press Ctrl+C:

```bash
python scripts/migrate_oc.py     # just run it again
```

It will say `already-applied=30148` and only finish whatever was left.

> Never delete `applied_keys.jsonl` unless you want to re-write everything.

## Speed

- About **10 writes/second** with 10 threads (depends on Roblox's limits).
- 30,000 entries ≈ **50 minutes**.
- You can raise `max_workers` to go faster, but Roblox will start returning `429`
  and the effective speed will not improve much. 10 is a good balance.

## Safety

- Only **upserts** (`POST ... entry`) — it never deletes.
- If a key fails permanently, it is written to `mig/migrate_fails.txt` and the run
  continues. Re-run to retry those.

## Watching progress

In another terminal:

```bash
# how many applied so far
python -c "print(sum(1 for _ in open('mig/applied_keys.jsonl')))"
```

## After it finishes

1. Confirm `fail=0` (or fix the fails).
2. Open the **new game** and check a few players.
3. Go to `docs/08-VERIFY.md` for a proper verification.

## Optional: no-scope fallback (advanced)

If your API key cannot write (missing `write` scope) you can instead have a
**Roblox Studio plugin** apply the ops from inside the game:

```bash
python scripts/migration_server.py mig/ops.json 8792
```

Then load `scripts/studio_plugin/RobloxStudioMCP.lua` as a Studio plugin (see
`docs/07-LEADERBOARDS.md` for details). This is slower but works without Open
Cloud write scopes.

Next → `docs/07-LEADERBOARDS.md`
