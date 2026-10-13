# 02 — Requirements: everything you need before you start

You do **not** need to be a programmer. You need these things.

## 1. Your game IDs

| Thing | Where to find it |
|-------|------------------|
| **Universe ID** (old + new) | Roblox Creator Dashboard → your experience. The Universe ID is in the URL / Settings. |
| **Place ID** (old + new) | Open the experience; the Place ID is in the URL, or in Studio → Game Settings. |

We use the **Universe ID** for the API calls, and the **Place ID** only to build
the `_<placeid>` suffix some stores use.

> Tip: in Studio, `game.UniverseId` and `game.PlaceId` print both instantly.

## 2. An Open Cloud API key

This is the password your script uses. Steps:

1. Go to **create.roblox.com** → **Credentials** (or *Open Cloud*).
2. Click **Create API Key**.
3. **Name:** e.g. `datastore-migration`.
4. **Access Permissions** — add the DataStore scopes you need. For a full migration
   of **standard** DataStores you want:
   - `universe-datastores.control:list`
   - `universe-datastores.control:read`
   - `universe-datastores.control:write`
   - `universe-datastores.objects:read`
   - `universe-datastores.objects:write`
   - (optional) `universe.ordered-data-store.scope.entry:read` and `:write`

   > The labels in the dashboard say things like
   > **"DataStore · List / Read / Write"**. Tick every DataStore permission
   > available — it is easier to tick all than to debug a `403` later.

5. **Universe access:** choose the **specific experiences** (both old and new) or
   *All*. Make sure **both** universes are included.
6. Create the key and **copy it immediately** (Roblox only shows it once).
7. Save it to a text file, e.g. `C:\Users\You\Downloads\roblox key data.txt`.

> 🔴 **Never paste the key into a public repo, Discord, or screenshot.**

## 3. Python

- **Python 3.8 or newer** (3.10+ recommended). Get it from python.org.
- Verify by running `python --version` in a terminal.
- The scripts use **only the standard library** — **no `pip install` needed.**
  (`migration_server.py` also uses only the standard library.)

## 4. Git + curl (for publishing / debugging)

- **Git** — to clone/commit (optional, only if you push the repo).
- **curl** — handy for testing the API by hand (optional; Windows 10+ has it).

## 5. The store names you want to migrate

Open the old game's scripts and note which DataStore names it uses, e.g.:

```lua
game:GetService("DataStoreService"):GetDataStore("PlayerData")
```

Write each name into `config.py` → `STORES`.

> Tip: you can also list them via the API. `docs/04-BACKUP-OLD.md` shows a
> one-liner that lists every DataStore in the universe.

## 6. A test plan (recommended)

Before trusting it on the live game:

1. Pick **one** player you know.
2. Note their coins / stats in the old game.
3. Run the migration on a copy of the new game (or accept the merge rules).
4. Check that player's data in the new game.

## Checklist

- [ ] Old Universe ID
- [ ] New Universe ID
- [ ] Old Place ID
- [ ] New Place ID
- [ ] Open Cloud key (saved to a file)
- [ ] Key has DataStore **read + write** scopes
- [ ] Key has access to **both** universes
- [ ] Python 3.8+
- [ ] List of DataStore names

Ready? → `docs/03-SETUP.md`
