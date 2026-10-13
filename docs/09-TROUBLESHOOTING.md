# 09 — Troubleshooting

Every problem we actually hit, and the fix.

## API / key

### `403 Forbidden` on ordered stores only
Your key is missing the **ordered** scopes. Standard stores still work. Either add
`universe.ordered-data-store.scope.entry:read` / `:write`, or use the Studio plugin
(see `docs/07-LEADERBOARDS.md`).

### `403` on delete
Keys usually do **not** have the *delete* scope. You cannot delete entries via the
API — clean up test keys from inside Studio instead.

### `401 Unauthorized`
Key is wrong, expired, or has a typo/space. Re-copy it.

### `403` on a whole universe
The key's **Universe access** does not include that experience. Edit the key and add
both experiences (or choose *All*).

### "I gave it all permissions but it still 403s"
Two different things are easy to confuse:
- **Scopes** = what operations (read, write, list, delete…).
- **Universe access** = which experiences.
You must set **both**. Also, editing an existing key does **not** regenerate it —
you do not need a new secret, just tick the missing boxes and Save.

## Rate limits

### Lots of `429`
Normal on big migrations. The scripts back off and retry automatically. If it is
constant, lower `max_workers` (in `migrate_oc.py`) from 10 to 5.

### Writes "wedge" when using the Studio plugin
Roblox allows ~60 writes/minute to a DataStore. Sending a big burst can make the
plugin's request queue stall. Fix: write in **small batches** and `task.wait()`
between them, or use the Open Cloud API instead (it handles throttling better).

## The `404 DatastoreNotFound` trap

Reading an **OrderedDataStore** through the **standard** v1 endpoint returns
`404 DatastoreNotFound` — that is *expected*, not a bug. Ordered stores need the
v2 ordered endpoint or the Studio plugin. Do not spend hours "fixing" this.

## Data problems

### Keys with special characters (`@`, spaces) break the v2 path
URL-encode with `urllib.parse.quote(key, safe="")`. For awkward keys, prefer the
**v1 query-param** endpoint, which tolerates them better.

### Store-name suffix mismatch
Old game: `PlayerData_v1_<oldPlaceId>`, new game: `PlayerData_v1_<newPlaceId>`.
If you forget to rewrite the suffix, data goes to a store the new game never reads.
`build_ops.py` does the rewrite — make sure `OLD_SUFFIX`/`NEW_SUFFIX` are right.

### Values differ between two sources
Sometimes a value lives both in a DataStore and in a derived store (e.g. a
leaderboard vs a TimeStats entry) and they disagree. Prefer the **authoritative**
source (the one the game actually reads). In this toolkit that is usually the
DataStore the game checks at runtime.

## Studio plugin

### "Studio plugin is not connected"
Checklist:
1. Plugin file is in `%LOCALAPPDATA%\Roblox\Plugins\`.
2. Studio was **restarted** after installing.
3. Game Settings → Security → **Allow HTTP Requests** is ON.
4. The bridge server (`server.py --standalone`) is running.

### Plugin says `ToolTip is not a valid member`
An old Studio API quirk — the plugin wraps that in `pcall` so it cannot crash. If
you see it and the plugin loaded, ignore it.

### Plugin goes silent after being idle
The bridge marks Studio "disconnected" after ~15s of no polling. Send a dummy
`POST /hello` to wake it, or just click the MCP toolbar button in Studio.

## Merge / conflicts

### A player's new value is smaller than the old one
The key already existed in the new game and a `skip-existing`/`keep-new` rule fired.
Open `mig/conflicts.txt`, find it, and if you want the old value, change the rule for
that store in `build_ops.py`.

### I want to force old values to win everywhere
Change `merge_max` to always return `old`, or set `merge=False, skip_if_new=False`.
**Careful:** this can overwrite real new progress. Back up first.

Next → `docs/10-GAMEPASSES.md`
