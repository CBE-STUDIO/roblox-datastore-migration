# Studio plugin (optional path)

Use this when your Open Cloud key cannot do something the standard API needs —
most commonly **OrderedDataStores / leaderboards** (see
[`docs/07-LEADERBOARDS.md`](../../docs/07-LEADERBOARDS.md)).

## Files

| File | Purpose |
|------|---------|
| `RobloxStudioMCP.lua` | Roblox Studio plugin. Polls the bridge and runs Lua. |
| `server.py` | Localhost HTTP bridge (stdlib only). |

## Setup

1. Copy `RobloxStudioMCP.lua` to `%LOCALAPPDATA%\Roblox\Plugins\`
   (Windows) and restart Studio.
2. In Studio: **Game Settings → Security → Allow HTTP Requests: ON**.
3. Start the bridge:
   ```bash
   python scripts/studio_plugin/server.py
   ```
4. In another terminal, run Lua inside Studio:
   ```bash
   python scripts/studio_plugin/server.py --lua "return game.PlaceId"
   python scripts/studio_plugin/server.py --lua-file my_code.lua
   ```

## Example: write one ordered (leaderboard) entry

Create `write_board.lua`:

```lua
local s = game:GetService("DataStoreService"):GetOrderedDataStore("TopTimePlayed")
local ok, err = pcall(function()
    s:SetAsync("TimePlayed123456789", 42309)
end)
return { ok = ok, err = err }
```

```bash
python scripts/studio_plugin/server.py --lua-file write_board.lua
```

## Notes / gotchas

- Ordered writes are **throttled** (~60/minute). Write in small batches with
  `task.wait()` between them.
- If the bridge says *"plugin is not connected"*: check the plugin is installed,
  Studio was restarted, HTTP requests are allowed, and `server.py` is running.
- Send `POST http://127.0.0.1:8791/hello` (empty body `{}`) to wake an idle bridge.
