# 03 — Setup

## 1. Get the files

Either clone the repo:

```bash
git clone https://github.com/CBE-STUDIO/roblox-datastore-migration.git
cd roblox-datastore-migration
```

…or just download it as a ZIP and unzip it.

Make sure you can see the `scripts/` folder.

## 2. Create your config file

Copy the example:

**Windows (PowerShell):**
```powershell
Copy-Item scripts\config.example.py scripts\config.py
```

**macOS / Linux:**
```bash
cp scripts/config.example.py scripts/config.py
```

Now **open `scripts/config.py`** in any text editor and fill in your values:

```python
# Path to the file that contains your Open Cloud API key
API_KEY_FILE = r"C:\Users\You\Downloads\roblox key data.txt"

# Universe + Place IDs
OLD_UNIVERSE = 1111111111
NEW_UNIVERSE = 2222222222
OLD_PLACE    = 111111111111
NEW_PLACE    = 222222222222

# Names of the DataStores in your game
STORES = [
    "TimeStats",
    "Donation",
    "PlayerData",
    # ... add the ones your game uses
]
```

> The example file is full of comments explaining each setting.

## 3. Put your key file in place

Create the key file and paste your key into it (just the key, on one line):

```
xU6ZP...your...key...here
```

`scripts/config.py` points at this file. **Do not** put the key inside the repo.

## 4. Check everything works

From the repository root, run:

```bash
python scripts/old_backup.py --selftest
```

> If your copy of `old_backup.py` does not have `--selftest`, just run it and
> watch the first lines — it prints `self-test OK` before doing anything else.

You should see something like:

```
self-test OK in 0.42s entries=100
```

If you see `self-test FAIL`, fix that first. Common causes:

- Wrong key path in `config.py` (check the file exists).
- Key has no access to the old universe → add it in the dashboard.
- Wrong Universe ID.

## 5. Folder layout after setup

```
roblox-datastore-migration/
├── scripts/
│   ├── config.py          ← YOUR settings (git-ignored, never commit)
│   ├── config.example.py
│   └── ...
├── old_backup/            ← created by the backup (git-ignored)
└── mig/                   ← created by the plan + migration (git-ignored)
```

## 6. Running the scripts

All commands are run **from the repository root**:

| Command | What it does |
|---------|--------------|
| `python scripts/old_backup.py` | back up the old game |
| `python scripts/retry_errors.py` | retry anything that failed |
| `python scripts/build_ops.py` | build the migration plan |
| `python scripts/board_fetch.py` | special-case the donation board (optional) |
| `python scripts/migrate_oc.py` | run the migration |

Next → `docs/04-BACKUP-OLD.md`
