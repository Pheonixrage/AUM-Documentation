# Legacy MariaDB → PlayFab Migration — Implementation Log

**Date:** March 3, 2026
**Project:** AUM-2.0 Production Client
**Branch:** `legacy-working-oct29`
**Commit:** `3325f610a` — `feat: Legacy MariaDB migration — claimLegacyAccount CloudScript + client CheckLegacyMigration`
**Status:** DEV deployed and ready for testing. PROD deployment pending.

---

## Overview

139 legacy players (288 avatars) from the old MariaDB database need their data restored when they log into the new PlayFab-based 2.0 client. This session implemented the full migration pipeline: client-side trigger, CloudScript handler with name conflict resolution, existing player merge, and per-avatar karma field support.

## Migration Data

- **Source:** MariaDB legacy database → parsed by `parse_legacy_db.py`
- **Output:** `legacy_migration.json` (411 KB, 10 chunks of ~15 players each)
- **Upload:** `upload_to_playfab.py` → Title Internal Data keys `LegacyMigration_0..9` + `_Meta` + `_Names` + `_Claimed`
- **Stats:** 139 players, 288 avatars, 1728 inventory items, 573 email-only accounts (no avatars) skipped

## Files Modified

### PlayFabDataBridge.cs (252 insertions, 18 deletions)

| Change | Purpose |
|--------|---------|
| `migrationCheckComplete` flag | Defers scene transition until migration resolves |
| `_dataLoadGeneration` counter | Prevents stale async callbacks after migration reload |
| `CheckLegacyMigration()` method | Called on every login, sends email to CloudScript |
| Karma fields in `AvatarCurrencyData` | `sattva`, `rajas`, `tamas`, `guna` (percentage 0-100) |
| Karma in `ConvertToAvatarInfo` / `ConvertToPlayFabAvatarData` | Round-trip serialization |
| `LoadAvatarCurrenciesToPlayerRewards` karma sync | Per-avatar karma loaded into PlayerRewards |
| `UNITY_EDITOR` test email override | Dev-only — remove before production release |

### temp_cloudscript_dev.js (495 insertions)

`claimLegacyAccount` handler appended (~435 lines):

| Step | What |
|------|------|
| 1 | Fast early-return: `LegacyMigrated` → "already_claimed" |
| 1b | Fast early-return: `LegacyChecked` → "already_checked" (no chunk re-scan) |
| 2 | Email hash → direct chunk lookup, fallback to sequential scan |
| 3 | Match email against chunk data |
| 4 | Lock via `LegacyMigration_Claimed` registry (duplicate protection) |
| 5 | **AN_ name registry** — legacy player keeps original name, conflicting new player gets `_2` suffix |
| 6 | Existing player merge: append legacy avatars (dedup by uniqueID), `Math.max` currencies |
| 6b | New player: write all legacy data as-is |
| 7 | **Karma conversion**: `KARMA_BASELINE=1`, percentage formula from raw action counts |
| 7b | `karmaState` initialization: `{ accumulatedKarma, sattvaCount, rajasCount, tamasCount }` |
| 8 | Meditation state (hellTime/maxHellTime) |
| 9 | Virtual currency sync via `aumEnsureCurrencies()` |
| 10 | Set `LegacyMigrated` + `LegacyChecked` flags |
| 11 | Set `LegacyChecked` on ALL outcomes (even "no data found") |
| 12 | PlayStream events for tracking |

## Karma System Details

### Formula
```
total = sattvaActions + rajasActions + tamasActions + KARMA_BASELINE
sattva% = round((sattvaActions + KARMA_BASELINE/3) / total * 100)
rajas%  = round((rajasActions + KARMA_BASELINE/3) / total * 100)
tamas%  = 100 - sattva% - rajas%  (remainder to prevent rounding errors)
guna    = whichever is highest (0=sattva, 1=rajas, 2=tamas)
```

- **KARMA_BASELINE=1** for migration (legacy action counts dominate)
- **KARMA_BASELINE=33** for live game (gradual shifts from neutral)

### karmaState (per-avatar)
Stored in PlayFab User Data alongside avatar data:
```json
{
  "accumulatedKarma": 0,
  "sattvaCount": <from legacy>,
  "rajasCount": <from legacy>,
  "tamasCount": <from legacy>
}
```

## Name Conflict Resolution (AN_ Keys)

The 2.0 production uses individual `AN_{lowercaseName}` keys (not the legacy `AvatarNameRegistry` blob).

**Priority:** Legacy player always keeps their original name.

When conflict detected:
1. Look up `AN_{name}` → parse `avatarId|playFabId` value
2. If owned by different player → that player's avatar gets `_2` suffix
3. Write new `AN_` key for suffixed name, update avatar data
4. Legacy player gets the original `AN_` key
5. PlayStream event `legacy_migration_name_conflict` logged for manual follow-up

## Existing Player Merge Logic

When `args.hasExistingAvatars == true`:
- Load existing avatars via `aumLoadAvatars(playFabId)`
- Append legacy avatars (skip duplicates by uniqueID)
- Preserve current `ActiveAvatarId` (don't change active avatar)
- Currencies: `Math.max(existing, legacy)` per field
- Keep existing Progress/KarmaState if already set

## Deployment Status

| Environment | Migration Data | CloudScript | Client Build |
|-------------|---------------|-------------|-------------|
| **DEV (15F2B7)** | Uploaded (10 chunks) | Deployed (rev 131) | Needs new build |
| **PROD (158C02)** | Not yet | Not yet | Needs new build |

### PROD Deployment Steps (when ready)
```bash
# 1. Upload migration chunks
cd /Users/mac/Documents/GitHub/AUM-Documentation/migration
python3 upload_to_playfab.py --env prod

# 2. Deploy CloudScript to PROD title
# Use curl or deploy script with PROD credentials (158C02 / 3YET9HU3F5ZBZ5FUQ3DEUOZECKPFDP1FEND8TKKUY5466DESZH)

# 3. Build + release new client with CheckLegacyMigration()
```

### Pre-PROD Checklist
- [ ] Remove `#if UNITY_EDITOR` test email override in `CheckLegacyMigration()`
- [ ] Verify PlayFab VC types have no explicit caps (largest legacy value: 3.3M bronze)
- [ ] Test all 6 scenarios on DEV:
  - New player with legacy email → restore
  - Existing player with legacy email → merge
  - Player with no legacy data → "no_legacy_data", LegacyChecked set
  - Re-login after migration → "already_claimed" (instant)
  - Re-login after "no data" → "already_checked" (instant)
  - Name conflict → legacy keeps name, new player gets suffix

## Reused Helpers (already in 2.0 CloudScript)

| Helper | Line | Purpose |
|--------|------|---------|
| `aumEnsureCurrencies()` | ~1103 | Create/sync VC types |
| `aumLoadAvatars()` | ~1038 | Load avatar list from User Data |
| `aumSaveAvatars()` | ~1056 | Save avatar list to User Data |
| `AUM_CURRENCY_DEFAULTS` | ~1018 | Default currency values |
| `AUM_CURRENCY_CODES` | ~1031 | PlayFab VC code mapping |

## Match Connection Issues (Investigated, Deferred)

During this session, we also investigated PREGAME stuck at 15s in Hetzner matches. Root cause identified as PvP ID FIX incorrectly remapping `localPlayerID` when bot's CREATECHAR arrives before local player's async model load completes. Fixes were prototyped but reverted per user request — these are pre-existing issues unrelated to migration. To be addressed in a separate session.

---

*Session duration: ~3 hours. Migration pipeline complete, DEV deployed, PROD pending client build.*
