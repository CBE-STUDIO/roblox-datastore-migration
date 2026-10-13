# 10 — Game passes and purchases (what DataStores can NOT move)

Players often ask: *"I bought VIP in the old game — will I still have it in the new
one?"* This is **not** a DataStore problem, so it needs its own answer.

## The two separate things

| | What it is | Cross-game? |
|---|---|---|
| **Ownership check** `MarketplaceService:UserOwnsGamePassAsync(userId, passId)` | "does this player own this pass?" | ✅ **Yes, always** — even if the pass belongs to another experience |
| **Selling** `MarketplaceService:PromptGamePassPurchase(player, passId)` | "let this player buy this pass" | ⚠️ Tied to the experience that sells it |

## Key facts

1. **Ownership is stored on the pass ID**, not on the place. If a player bought a
   pass in the old game, `UserOwnsGamePassAsync` returns `true` for that pass ID
   **inside the new game too**.
2. This works even if the old game is **private / unlisted**. Ownership does not
   care about the experience's visibility.
3. **Do not delete the old passes.** Deleting the pass deletes ownership.
4. The passes must be owned by the **same account or group** as the new game.

## Recommended solution: reuse the OLD pass IDs

The simplest fix is to **not create new passes**. In the new game's scripts, use the
**same pass IDs** as the old game. Then:

- Old buyers keep the perk automatically (ownership carried over). ✅
- New players can buy it (the pass belongs to your group). ✅
- **Nothing needs to be migrated in DataStores.** ✅

## Fallback: create new passes AND check both

If you want brand-new passes in the new game, keep the old IDs around and grant the
perk if the player owns **either**:

```lua
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local OLD_PASS_IDS = { 1234567, 7654321 }   -- passes from the OLD game
local NEW_PASS_IDS = { 1111111, 2222222 }   -- passes in the NEW game

local function ownsAny(player, ids)
    for _, id in ipairs(ids) do
        local ok, has = pcall(function()
            return MarketplaceService:UserOwnsGamePassAsync(player.UserId, id)
        end)
        if ok and has then return true end
    end
    return false
end

Players.PlayerAdded:Connect(function(player)
    if ownsAny(player, OLD_PASS_IDS) or ownsAny(player, NEW_PASS_IDS) then
        -- grant VIP here
    end
end)

-- also grant instantly on a new purchase
MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, passId, purchased)
    if purchased and table.find(NEW_PASS_IDS, passId) then
        -- grant VIP here
    end
end)
```

## Testing ownership cross-game

Inside the **new** game (server), with a known old buyer's user id and the old pass id:

```lua
print(game:GetService("MarketplaceService")
    :UserOwnsGamePassAsync(PASTE_OLD_BUYER_USERID, PASTE_OLD_PASSID))
```

- Prints `true` → the player still owns it. You can grant the perk. 🎉
- Prints `false` → they never owned it, or it was refunded/deleted.

## What about VIP stored as a data field?

If your game saved VIP as a **Boolean in the player's data** (e.g. `GiftedVIP = true`),
then that field **is** migrated by this toolkit like any other data — nothing extra
to do.

## Summary

- DataStore migration **cannot** move game-pass ownership, because ownership is not
  in DataStores.
- But you do not *need* to move it: **reuse the old pass IDs**, or **check both old
  and new IDs** on join.
- **Never delete the old passes.**

You're done! 🎉
