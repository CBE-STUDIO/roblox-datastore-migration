# 07 — Leaderboards (OrderedDataStores)

Normal DataStores are easy to migrate with the standard API. **OrderedDataStores**
(used for leaderboards like "Top Time Played" or "Top Donors") are different and
need special care.

## What is an OrderedDataStore?

- Same idea as a DataStore, but numbers are stored so they can be **sorted**.
- The game calls `GetSortedAsync(false, 10, 1)` to show the **top 10**.
- Keys are usually like `"TimePlayed" .. userId`, and the value is a number
  (e.g. minutes).

Example (from a `TimePlayedClass` script):

```lua
local store = DataStoreService:GetOrderedDataStore("TopTimePlayed")
local pages = store:GetSortedAsync(false, 10, 1)   -- descending, 10 per page
```

## Why they are awkward

The standard v1 API **cannot read** an OrderedDataStore (you get
`404 DatastoreNotFound`). To touch them you need:

- Open Cloud scopes `universe.ordered-data-store.scope.entry:read` and `:write`, **or**
- a **Roblox Studio plugin** running inside the game (no scope needed).

## Option A — Open Cloud (fast)

Add the two ordered scopes to your key, then use the v2 endpoint:

```
GET  /cloud/v2/universes/<U>/ordered-data-stores/<store>/scopes/global/entries
POST /cloud/v2/universes/<U>/ordered-data-stores/<store>/scopes/global/entries
```

## Option B — Studio plugin (no scopes needed)

1. In Studio, open the **new** game (published, with *Allow HTTP Requests* ON).
2. Install the plugin file `scripts/studio_plugin/RobloxStudioMCP.lua`
   into `%LOCALAPPDATA%\Roblox\Plugins\` and restart Studio.
3. Run the local bridge: `python scripts/studio_plugin/server.py --standalone`.
4. Send Lua over the bridge, e.g.:

   ```lua
   local s = game:GetService("DataStoreService"):GetOrderedDataStore("TopTimePlayed")
   return s:SetAsync("TimePlayed123456789", 42309)
   ```

> Writing ordered entries from Studio works but is **throttled** — expect roughly
> **0.5–1 second per write**. Roblox allows ~60 writes/minute before it starts
> queueing.

## Reading the *old* leaderboard

`GetSortedAsync` returns the ranking **oldest-first** and only the top slice. To get
the real values for a rank range, read page by page:

```lua
local store = game:GetService("DataStoreService"):GetOrderedDataStore("TopTimePlayed")
local page = store:GetSortedAsync(false, 100, 1)   -- descending, 100 per page
for _, entry in ipairs(page:GetCurrentPage()) do
    print(entry.key, entry.value)
end
```

## A note about scope

The public leaderboard usually only shows the **top 10**. Migrating positions
**11+** is therefore **cosmetic** — nice for a full history, but not visible.
Decide how deep you need:

| Depth | Effort |
|-------|--------|
| top 10 | seconds |
| top 100 | ~1 minute |
| everything | longer, may be throttled |

## Gold / secondary boards

If your game defines a second ordered store (e.g. `AquaClub_GoldLeaderboard_v1`),
check whether it is actually **written** anywhere. Many games define a store but
never call `SetAsync`/`IncrementAsync` on it, which means it is empty and there is
**nothing to migrate**.

To check: search the obfuscated scripts for `SetAsync`, `IncrementAsync`,
`UpdateAsync` on that store name. If none exist, skip it.

Next → `docs/08-VERIFY.md`
