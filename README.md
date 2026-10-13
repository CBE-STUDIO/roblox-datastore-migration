# Roblox DataStore Migration Toolkit

**Move all your players' saved data from one Roblox experience to another — safely, without losing anything, without touching the old game, and with a full backup first.**

Written for **beginners**. If you can copy-paste and run a command, you can do this.

> **Credit / License:** This project is by **CBE-STUDIO**. See [LICENSE](LICENSE), [NOTICE](NOTICE) and [CITATION.cff](CITATION.cff).
> If you reuse this, **you must keep the credit**. See [Crediting this work](#crediting-this-work).

---

## What problem does this solve?

You built a new version of your Roblox game (a new "place" / "experience"). But all your players' data — coins, items, time played, donations, clans, favourites — lives **only in the old game**.

DataStores are **not** shared between two different experiences. So when players open the new game, they start empty. 😢

This toolkit **copies every saved key** from the old experience into the new one, so players keep everything.

```
   OLD EXPERIENCE (source)                 NEW EXPERIENCE (target)
   ┌───────────────────────┐               ┌───────────────────────┐
   │  DataStore: TimeStats │               │  DataStore: TimeStats │
   │  DataStore: Donation  │   ── copy ──► │  DataStore: Donation  │
   │  DataStore: PlayerData│               │  DataStore: PlayerData│
   │  ...                  │               │  ...                  │
   └───────────────────────┘               └───────────────────────┘
        READ-ONLY            Open Cloud API      write (merge only)
```

**Golden rules this toolkit follows:**

1. The old game is **read-only** — we never change or delete anything there.
2. We **back up** the old data to local files first.
3. We **merge** — we never wipe data that already exists in the new game.
4. Every write is logged, so a crash can **resume** instead of starting over.

---

## Quick start (the short version)

> Full beginner walkthrough: read the docs **in order**, `docs/01-OVERVIEW.md` → `docs/10-GAMEPASSES.md`.

1. **Get an Open Cloud API key** (see [docs/02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md)).
2. **Set up Python** (`docs/03-SETUP.md`).
3. **Copy config:** `scripts/config.example.py` → `scripts/config.py` and fill in your IDs.
4. **Back up the old game:** `python scripts/old_backup.py`
5. **Fix anything that failed:** `python scripts/retry_errors.py`
6. **Build the migration plan:** `python scripts/build_ops.py`
7. **Run the migration:** `python scripts/migrate_oc.py`
8. **Verify:** follow `docs/08-VERIFY.md`.

That's it. If it crashes at step 7, just run step 7 again — it resumes.

---

## Repository structure

```
roblox-datastore-migration/
├── README.md                ← you are here
├── LICENSE                  ← Apache-2.0 (keeps credit)
├── NOTICE                   ← credit line
├── CITATION.cff             ← how to cite
├── SECURITY.md              ← keep your API key safe
├── CHANGELOG.md
├── .gitignore               ← blocks your key + player data
├── docs/
│   ├── 01-OVERVIEW.md
│   ├── 02-REQUIREMENTS.md
│   ├── 03-SETUP.md
│   ├── 04-BACKUP-OLD.md
│   ├── 05-BUILD-OPS.md
│   ├── 06-MIGRATE.md
│   ├── 07-LEADERBOARDS.md
│   ├── 08-VERIFY.md
│   ├── 09-TROUBLESHOOTING.md
│   └── 10-GAMEPASSES.md
├── scripts/
│   ├── config.example.py    ← copy to config.py, fill in your IDs
│   ├── old_backup.py
│   ├── retry_errors.py
│   ├── build_ops.py
│   ├── board_fetch.py
│   ├── migrate_oc.py
│   ├── migration_server.py
│   └── studio_plugin/
│       ├── RobloxStudioMCP.lua
│       └── server.py
└── examples/
    ├── ops.sample.json
    └── old_backup.sample.jsonl
```

---

## The ideas you need to understand

You don't need to be an expert, but these 5 words are used everywhere:

| Word | Plain meaning |
|------|---------------|
| **Experience / Universe** | Your game as a whole. Has a **Universe ID**. |
| **Place** | A single level inside an experience. Has a **Place ID**. |
| **DataStore** | A cloud folder where the game saves player data. |
| **Key** | One entry inside a DataStore (usually one player). |
| **Open Cloud API key** | The secret that lets a script read/write your DataStores. |

Read `docs/01-OVERVIEW.md` for the full explanation.

---

## Safety notes

- ✅ **Your old game is never modified.** All old-game calls are read-only (`GET`).
- ✅ **Backup happens first.** If anything looks wrong, you still have the old data on your PC.
- ✅ **Merge, never overwrite.** Numbers are merged with `max()`, lists are unioned, and existing new data is kept when unsure.
- ✅ **Writes are logged** to `mig/applied_keys.jsonl` so the migration is resumable.
- ⛔ **Never commit your API key.** `.gitignore` already blocks it.

---

## Crediting this work

This project is licensed under **Apache-2.0**, which **requires** that you keep the copyright notice and the `NOTICE` file.

If you use this toolkit, publish a tutorial about it, or build on it, please:

- Keep the `LICENSE` and `NOTICE` files.
- Credit **CBE-STUDIO** and link back to this repository.
- Cite it using [CITATION.cff](CITATION.cff).

See [LICENSE](LICENSE) for the exact terms.

---

## Disclaimer

This tool talks to **your own** Roblox experiences using **your own** API key. Only ever migrate data you own or are authorised to migrate. Use at your own risk; always keep a backup.
