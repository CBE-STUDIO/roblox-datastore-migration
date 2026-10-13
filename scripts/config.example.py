# =============================================================================
#  config.example.py  --  COPY THIS FILE TO  config.py  AND EDIT IT
# -----------------------------------------------------------------------------
#  cp scripts/config.example.py scripts/config.py
#
#  config.py is git-ignored. NEVER commit your real key or your real config.
# =============================================================================

# --- 1. Where your Open Cloud API key lives -----------------------------------
#     Put the key in its own file (one line) and point this at it.
#     Keep it OUTSIDE the repository.
API_KEY_FILE = r"C:\Users\You\Downloads\roblox key data.txt"

def load_key():
    """Read the API key from API_KEY_FILE."""
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


# --- 2. Universes and places --------------------------------------------------
#     Universe id  -> used for all API calls.
#     Place id     -> used only to build the "_<placeid>" store-name suffix.
OLD_UNIVERSE = 1111111111
NEW_UNIVERSE = 2222222222
OLD_PLACE    = 111111111111
NEW_PLACE    = 222222222222

OLD_SUFFIX = "_" + str(OLD_PLACE)
NEW_SUFFIX = "_" + str(NEW_PLACE)


# --- 3. Folders ---------------------------------------------------------------
BACKUP_DIR = "old_backup"   # raw backup of the old game lands here
WORK_DIR   = "mig"          # migration plan + ledger land here


# --- 4. DataStores to back up from the OLD universe ---------------------------
#     Replace these with the REAL store names your game uses.
#     Names ending in OLD_SUFFIX get rewritten to NEW_SUFFIX by build_ops.py.
STORES = [
    "ProfileStore V1",
    "TimeStats",
    "Donation",
    "DanceFavorites_v1",
    "PlayerGroupIcons",
    "Donation Board v4",

    # stores that include the place id in their name:
    "PlayerData_v1"  + OLD_SUFFIX,
    "AllPlayerIds_v1" + OLD_SUFFIX,
    "PendingGifts_v1" + OLD_SUFFIX,
    "ClanData_v1"     + OLD_SUFFIX,

    # optional legacy store with no suffix
    "PlayerData_v1",
]

# Stores whose key is a single aggregate (not one-key-per-user).
# build_ops.py has special handling for these.
AGGREGATE_KEYS = {
    "Donation Board v4": ["donationboard@donations",
                          "donationboard@settings",
                          "donationboard@transferreddata"],
}


# --- 5. Ordered / leaderboard stores (see docs/07-LEADERBOARDS.md) -------------
TIME_PLAYED_STORE = "TopTimePlayed"          # ordered store, value = minutes
GOLD_STORE_PREFIX = "GoldLeaderboard_v1"     # ordered store (may be unused/empty)


# --- 6. Helpers ---------------------------------------------------------------

def new_name(old_store: str) -> str:
    """Map an OLD store name to its NEW equivalent (rewrites the place suffix)."""
    if old_store.endswith(OLD_SUFFIX):
        return old_store[: -len(OLD_SUFFIX)] + NEW_SUFFIX
    return old_store


def safe_filename(s: str) -> str:
    import re
    return re.sub(r'[^A-Za-z0-9._-]', '_', s)
