# PlayFab Cosmetic Set + Currency Grant — Teammate Account

**Date:** 2026-04-22
**Title:** Staging `1A4AA8` (P2 elemental-progression)
**Target account:** PlayFabId `93302B985015F027`
**Scope:** Initially YANTRA only, then extended to **all 5 avatars** on the account
**Goal:** Grant full Lohitha cosmetic set + gold currency for social-media gameplay recording
**Outcome:** SUCCESS — all 5 avatars rendering correctly after full app cold-launch

---

## What Was Granted

**All 5 avatars on the account received:** Lohitha Gold armor (ident=6) × Head/Torso/Hands/Pants/Legs + Lohitha weapon (ident=4) equipped and added to GrantedCosmetics.

### Final wearItemCodes per avatar

| Avatar | Style | Class | Head | Torso | Hands | Pants | Legs | Weapon |
|---|---|---|---|---|---|---|---|---|
| YANTRA | YantraMuktha (4) | Male (0) | 3076 | 3108 | 3140 | 3172 | 3204 | **2212** |
| AMUUKHTA | Amuktha (0) | Male (0) | 3072 | 3104 | 3136 | 3168 | 3200 | **2208** |
| mantra | MantraMuktha (1) | Female (1) | 3089 | 3121 | 3153 | 3185 | 3217 | **2225** |
| pani | PaniMuktha (3) | Male (0) | 3075 | 3107 | 3139 | 3171 | 3203 | **2211** |
| mukhtaa | MukthaMuktha (2) | Female (1) | 3090 | 3122 | 3154 | 3186 | 3218 | **2226** |

Plus:
- `GrantedCosmetics` = 31 entries (1 pre-existing FTUE reward `1124` + 30 new codes across 5 avatars)
- Gold currency: `VC.GD = 1000` + active avatar `currencies.gold = 1000` (synced on both stores)

### Grant sequence

1. **YANTRA first** (single-avatar proof of concept). Needed the full flow: lookup via Game Manager URL → backup → compute codes → UpdateUserData → verify. Had to iterate through a failed tier-6 weapon attempt (`3236`) before landing on tier-4 Lohitha (`2212`) — this is where the "weapons only ship at ident 1 + 4" gotcha was discovered.
2. **Remaining 4 avatars** (AMUUKHTA, mantra, pani, mukhtaa) — single atomic `UpdateUserData` call. Verified all 4 `(Style, Class)` combinations have tier-6 armor assets and tier-4 weapons before writing. All codes applied cleanly on first attempt.

---

## Data Model

**Ownership vs equipped — two separate UserData keys:**

| Key | Type | Purpose |
|---|---|---|
| `GrantedCosmetics` | JSON array of uint | Permanent ownership list. Client reads on login via `PlayFanInventoryService.FetchGrantedCosmeticsAsync`, populates `InterfaceManager.grantedCosmetics` HashSet, each code becomes an inventory item with deterministic UUID. |
| `Avatars` | JSON wrapper `{"avatars":[...]}` | Per-avatar state. Each avatar has `uniqueID`, `nickName`, `fightingStyle`, `fighterClass`, `weaponVariant`, `wearItemCodes[6]`, `currencies{}`. `wearItemCodes[]` controls what's visibly equipped. |
| `ActiveAvatarId` | string | GUID of currently selected avatar |

**Currency (gold) must be written to BOTH stores:**

1. PlayFab Virtual Currency (`GD`) — `Admin/AddUserVirtualCurrency` with `VirtualCurrency: "GD"`
2. Active avatar's `currencies.gold` inside the `Avatars` JSON

If they diverge, the client's login reconciliation (`Math.Max` pattern in `PlayFabDataBridge`) will resync. But safer to write both atomically.

---

## Item Code Bit-Packing

From [AssetManager.cs:1133](../../../AUM-Unity-Staging-Legacy/Assets/Scenes/AssetManager.cs):

```
itemCode = (identifier << 9) | (itemType << 5) | (fighterClass << 4) | fightingStyle
```

**Enum values:**
- FightingStyles: `Amuktha=0, MantraMuktha=1, MukthaMuktha=2, PaniMuktha=3, YantraMuktha=4`
- FighterClass: `Male=0, Female=1`
- ItemType: `Head=0, Torso=1, Hands=2, Pants=3, Legs=4, Weapons=5, Treasure=6, Sets=7`
- Identifier: `1=Aranya Bronze, 2=Aranya Silver, 3=Aranya Gold, 4=Lohitha Bronze, 5=Lohitha Silver, 6=Lohitha Gold`

**Python helper:**

```python
def item_code(style, fighter_class, item_type, identifier):
    return (identifier << 9) | (item_type << 5) | (fighter_class << 4) | style

# YantraMuktha Male Lohitha Gold full set:
# [item_code(4, 0, t, 6) for t in range(6)] → [3076, 3108, 3140, 3172, 3204, 3236]
```

---

## Multi-Avatar Grant Script (Proven)

Use this Python snippet to grant the full Lohitha Gold set + Lohitha weapon to **every avatar** on an account in one atomic write. Preserves existing avatars you don't touch, dedupes GrantedCosmetics.

```python
import json, subprocess

PFID   = "<PLAYFABID>"
SECRET = "<TITLE_SECRET>"
TITLE  = "<TITLE_ID>"
SKIP_AVATAR_IDS = set()  # uniqueIDs already granted, skip these

def item_code(style, cls, itype, ident):
    return (ident << 9) | (itype << 5) | (cls << 4) | style

def full_set(style, cls):
    # 5 armor @ Lohitha Gold (ident=6) + weapon @ Lohitha (ident=4)
    return [item_code(style, cls, t, 6) for t in range(5)] + [item_code(style, cls, 5, 4)]

# Read + back up
r = subprocess.run(['curl','-s','-X','POST',
    f'https://{TITLE}.playfabapi.com/Admin/GetUserData',
    '-H','Content-Type: application/json','-H',f'X-SecretKey: {SECRET}',
    '-d', json.dumps({"PlayFabId":PFID,"Keys":["Avatars","GrantedCosmetics"]})],
    capture_output=True, text=True)
d = json.loads(r.stdout)['data']['Data']
w  = json.loads(d['Avatars']['Value'])
gc = json.loads(d['GrantedCosmetics']['Value'])
with open('/tmp/avatars_backup.json','w') as f: json.dump(w, f, indent=2)

# Mutate
for a in w['avatars']:
    if a.get('uniqueID') in SKIP_AVATAR_IDS: continue
    codes = full_set(a['fightingStyle'], a['fighterClass'])
    a['wearItemCodes'] = codes
    for c in codes:
        if c not in gc: gc.append(c)

# Write
payload = {"PlayFabId": PFID, "Data": {
    "Avatars": json.dumps(w, separators=(',',':')),
    "GrantedCosmetics": json.dumps(gc, separators=(',',':'))
}}
with open('/tmp/grant_payload.json','w') as f: json.dump(payload, f)
r2 = subprocess.run(['curl','-s','-X','POST',
    f'https://{TITLE}.playfabapi.com/Admin/UpdateUserData',
    '-H','Content-Type: application/json','-H',f'X-SecretKey: {SECRET}',
    '-d','@/tmp/grant_payload.json'], capture_output=True, text=True)
print(r2.stdout)
```

---

## Grant Process (Reference Script)

```bash
# 1. Lookup PlayFabId — check TitleInternalData reverse lookups first
curl -X POST "https://{TITLE_ID}.playfabapi.com/Admin/GetTitleInternalData" \
  -H "X-SecretKey: {SECRET}" -H "Content-Type: application/json" \
  -d '{"Keys":["PN_{profilename}","FC_{friendcode}"]}'

# If both empty, get PlayFabId directly from Game Manager URL:
# https://developer.playfab.com/en-us/r/t/{TITLE_ID}/players/{PLAYFABID}/overview

# 2. Read current state + back up
curl -X POST "https://{TITLE_ID}.playfabapi.com/Admin/GetUserData" \
  -H "X-SecretKey: {SECRET}" -H "Content-Type: application/json" \
  -d '{"PlayFabId":"{PLAYFABID}","Keys":["Avatars","ActiveAvatarId","GrantedCosmetics"]}' \
  > backup.json

# 3. Modify Avatars wrapper in Python — preserve all avatars, mutate target only
# 4. UpdateUserData with new Avatars JSON + appended GrantedCosmetics
curl -X POST "https://{TITLE_ID}.playfabapi.com/Admin/UpdateUserData" \
  -H "X-SecretKey: {SECRET}" -H "Content-Type: application/json" \
  -d @payload.json

# 5. Add gold currency
curl -X POST "https://{TITLE_ID}.playfabapi.com/Admin/AddUserVirtualCurrency" \
  -H "X-SecretKey: {SECRET}" -H "Content-Type: application/json" \
  -d '{"PlayFabId":"{PLAYFABID}","VirtualCurrency":"GD","Amount":1000}'

# 6. Verify — re-read UserData + GetUserInventory for VC
```

---

## Gotchas Learned (CRITICAL)

### 1. Weapons don't have 6 tiers — only 2
Armor ships at **identifiers `[1, 2, 3, 4, 5, 6]`** per slot. Weapons only ship at **`[1, 4]`** — Aranya (1) and Lohitha (4). By design: there is no "Aranya Silver bow" or "Lohitha Gold bow" prefab.

- Lohitha bow is the premium/gold-equivalent weapon.
- Writing `identifier=6` (code `3236`) to `wearItemCodes[weapon]` → client can't resolve Addressable → falls back to default → `SaveAvatarData` persists the fallback → write gets silently reverted.
- **Always use identifier 1 or 4 for weapon slot.**

### 2. Weapons use a different Addressable key format than armor
From [AssetManager.cs:282-309](../../../AUM-2.0 Production/Client/Assets/Scenes/AssetManager.cs#L282):

- **Armor keys:** `[FightingStyle, FighterClass, ItemType, Identifier, ObjectType]` → file `YantraMuktha_Male_Head_6_Item.asset`
- **Weapon keys:** `[FightingStyle, ItemType, Identifier, ObjectType]` (no FighterClass) → file `YantraMuktha_Weapons_4_Item.asset`

Weapons are gender-neutral. File-scanning with the armor pattern misses weapons and vice versa.

### 3. Inventory population is login-only, never polled mid-session
[PlayFanInventoryService.AddDefaultItemsForAvatar](../../../AUM-2.0 Production/Client/Assets/Scripts/PlayFab/PlayFanInventoryService.cs):
1. Adds tier-1 Aranya defaults (`identifier=1`) for every slot
2. Adds `avatar.wearItems` entries **only if identifier ≠ 1**
3. UUID sync
4. Adds `GrantedCosmetics` array entries

**Grant only takes effect after full app kill + cold launch.** Background/foreground cycles are NOT enough — the client caches UserData in memory on login and never re-polls.

### 4. Client can silently overwrite grants
If the client can't resolve an equipped item's Addressable (e.g. we wrote an invalid code like `3236`), the CDN-fallback path substitutes the default **and persists that fallback back to PlayFab** on the next `SaveAvatarData`. Symptom: you write `wearItemCodes[5] = 3236`, check 10 minutes later and it's back to `676`. **Always verify codes correspond to shipped assets before writing.**

### 5. Profile name / friend code reverse lookups are incomplete
`TitleInternalData.PN_{name}` and `FC_{code}` only exist for accounts that completed the MainMenu initialisation where `GenerateFriendCode` + `checkAndRegisterProfileName` run. Accounts that only completed avatar creation won't have them. **Best identifier is always the PlayFabId from Game Manager URL.**

### 6. Friend code alphabet excludes `I/O/0/1`
Valid friend code chars: `"ABCDEFGHJKLMNPQRSTUVWXYZ23456789"`. A code containing any of `I/O/0/1` is either mistyped or manually entered — not auto-generated by `GenerateFriendCode` CloudScript.

### 7. Flicker after grant = client-side cache, not PlayFab issue
After a series of grant attempts (including any bad writes), the client's in-memory `inventoryItems` list + `Addressables.LoadAssetsAsync` handles may hold stale state. Avatar rebuild on scene change picks whichever cached prefab is found first. **Fix:** kill from recents task switcher + cold launch. If still flickering, clear app data to rebuild Addressables disk cache.

---

## Final Working State (for reference)

```json
{
  "GrantedCosmetics": [1124, 3076, 3108, 3140, 3172, 3204, 2212,
                       3072, 3104, 3136, 3168, 3200, 2208,
                       3089, 3121, 3153, 3185, 3217, 2225,
                       3075, 3107, 3139, 3171, 3203, 2211,
                       3090, 3122, 3154, 3186, 3218, 2226],
  "YANTRA.wearItemCodes":   [3076, 3108, 3140, 3172, 3204, 2212],
  "AMUUKHTA.wearItemCodes": [3072, 3104, 3136, 3168, 3200, 2208],
  "mantra.wearItemCodes":   [3089, 3121, 3153, 3185, 3217, 2225],
  "pani.wearItemCodes":     [3075, 3107, 3139, 3171, 3203, 2211],
  "mukhtaa.wearItemCodes":  [3090, 3122, 3154, 3186, 3218, 2226],
  "active_avatar.currencies.gold": 1000,
  "VC.GD": 1000
}
```

Confirmed all 5 avatars rendering correctly in-game after full app cold-launch.

### Open question for PaniMuktha

`pani` (PaniMuktha Male) uses **dual discus weapons** — the `weaponVariant` field (enum `WeaponType { WeaponA=0, WeaponB=1 }`) decides which variant model renders. Only WeaponA was set (the currently-stored variant). If you ever report one disc missing post-grant, suspect the WeaponB variant needs its own grant path or there's an EquipWeapon branch gated on Brahma god that only activates `leftDiscus` + `rightDiscus` together. Was not hit in this session — flagged for future.

---

## Backup Files (local `/tmp/`)

- `/tmp/yantra_playfab_before.json` — full initial GetUserData response
- `/tmp/yantra_avatars_backup.json` — pretty-printed Avatars wrapper pre-grant
- `/tmp/yantra_avatars_pre_gold.json` — Avatars wrapper before currency write

---

## Related Files

- Client code: [PlayFanInventoryService.cs](../../../AUM-2.0 Production/Client/Assets/Scripts/PlayFab/PlayFanInventoryService.cs), [AssetManager.cs](../../../AUM-2.0 Production/Client/Assets/Scenes/AssetManager.cs), [PlayFabDataBridge.cs](../../../AUM-2.0 Production/Client/Assets/Scripts/PlayFab/PlayFabDataBridge.cs)
- Legacy equivalent: [PlayFanInventoryService.cs (P3)](../../../AUM-Unity-Staging-Legacy/Assets/Scripts/PlayFab/PlayFanInventoryService.cs)
- PlayFab REST reference: see `CLAUDE.md` "PlayFab REST API (proven working process)"
