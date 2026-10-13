# 01 — Overview: what we are doing and why

## The problem in one picture

Roblox games store player data in **DataStores**. A DataStore belongs to **one
experience (universe)**. When you make a brand-new experience, its DataStores are
**empty** — even if you copied the whole game.

So players who had 1,000,000 coins in the old game see 0 in the new one. Not great.

## The solution in one picture

We read **every key** out of the old experience's DataStores, write them into the
new experience's DataStores, and make sure we never wipe anything that is already
there.

```
        STEP 1: BACKUP (read-only)            STEP 2: PLAN (local, no internet)
   ┌──────────────┐                     ┌──────────────────────────────┐
   │ OLD universe │  ── GET ──►  JSONL  │ old_backup/*.jsonl (on disk) │
   └──────────────┘   files             └──────────────┬───────────────┘
                                                       │
                                                       ▼
                                          ┌──────────────────────────────┐
                                          │  build_ops.py                │
                                          │  merge old + existing new    │
                                          │  → ops.json (the plan)       │
                                          └──────────────┬───────────────┘
                                                         │
        STEP 3: APPLY (write)                            ▼
   ┌──────────────┐                          ┌──────────────────────────┐
   │ NEW universe │  ◄── POST (upsert) ───── │  migrate_oc.py           │
   └──────────────┘                          │  (10 threads, resume)    │
                                             └──────────────────────────┘
```

## Why it is safe

| Risk | How we avoid it |
|------|------------------|
| Deleting old data | We **only ever GET** from the old universe. No write, no delete. |
| Losing data on a crash | Everything is written to disk first (`old_backup/`), then planned (`ops.json`), then applied with a **ledger** so re-running resumes. |
| Overwriting new progress | We **merge** (see below) and keep the new value when unsure. |
| Leaking your API key | The key is read from a file, never hard-coded, and `.gitignore` blocks it. |
| Hitting Roblox rate limits | Every request retries with exponential back-off on `429`/`5xx`. |

## The merge rules (very important)

When a key already exists in the **new** game (maybe a player already played), we
combine old + new instead of blindly overwriting:

| Type of value | What we do |
|---------------|------------|
| Number (coins, minutes, donations) | keep the **maximum** (`max(old, new)`) |
| Table / object | merge **field by field**, recursively |
| List | take the **union** (no duplicates) |
| Text / string (e.g. clan tag) | keep the **new** one (it is the current state) |
| Anything else / unsure | keep the **new** one |

Every time a rule fires, it is written to `mig/conflicts.txt` so you can review it.

## What gets migrated

The set of DataStores is defined in `scripts/config.py` (copied from
`config.example.py`). A typical game has stores like:

- `TimeStats` — time played / cash
- `Donation` — who raised and donated
- `PlayerData` — coins, items, VIP flags, …
- `AllPlayerIds` — a list of every player who ever joined
- `ClanData`, `PendingGifts`, `DanceFavorites`, `PlayerGroupIcons`
- `Donation Board v4` — the donation leaderboard

> ⚠️ Store names sometimes include a **place-id suffix**, e.g.
> `AquaClub_PlayerData_v1_79229339887184`. The old game uses the **old** place id
> and the new game uses the **new** place id. `config.py` handles this with
> `OLD_SUFFIX` / `NEW_SUFFIX`, and `build_ops.py` rewrites the names for you.

## What is NOT migrated (and why)

- **Game passes / VIP ownership** — Roblox stores this on *their* side, not in
  DataStores. Read `docs/10-GAMEPASSES.md`.
- **Anything your game does not save to a DataStore** — if it was never saved, we
  cannot copy it.

## Next steps

1. `docs/02-REQUIREMENTS.md` — collect the things you need.
2. `docs/03-SETUP.md` — install and configure.
3. `docs/04-BACKUP-OLD.md` — make the backup.
