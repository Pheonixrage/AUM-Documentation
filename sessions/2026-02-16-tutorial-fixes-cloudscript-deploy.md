# Session Log: 2026-02-16 - Tutorial Fixes, CloudScript Deploy, Map Rename

## Summary
Fixed tutorial loading in Staging mode, deployed CloudScript to staging PlayFab title, renamed Map_Hell→Bhuloka across client, and fixed bot NullRef crash in attack lifecycle.

## What Was Done

### CloudScript Deployment
- Pulled 32 handlers from dev title (15F2B7) Rev 70
- Deployed to staging title (1A4AA8) using staging secret key — now at Rev 5, 32 handlers synced
- Both titles now have identical CloudScript (97,995 chars)

### Map_Hell → Bhuloka Rename
- Fixed serialized field in `AvatarCreate.unity:112244` (`tutorialSceneName: Map_Hell → Bhuloka`) — ROOT CAUSE
- Updated `EditorBuildSettings.asset` scene path
- Updated `QuestFace.cs` debug log text
- Updated `AUM_MatchDiagnostics.cs` comment
- Note: AUM-Headless still uses `Map_Hell.unity` (correct, not renamed there)

### Tutorial Loading Fix (Staging Mode)
- **Root cause**: Staging mode orchestrator returns `success: true` with port 0 / empty IP. `HasAllocation=true` but no actual server for tutorial.
- Fix 1: `ShouldUseLocalTutorial()` now validates IP+port, not just `HasAllocation` flag
- Fix 2: `SetupTutorialMatch()` falls back to `SetupLocalTutorial()` when server info invalid
- Fix 3: `OnMapLoaded()` safety net — forces local tutorial if `match_Avatars` still empty

### Bot NullRef Fix (ControllerBase.cs)
- **Root cause**: Tutorial6 calls `stateManager.ChangeState(WeaponStrike)` on bot → `OnAttackEnter()` accesses `simulation.meleeAbility` → NullRef because bot has no simulation object (only created per-tick for ActivePlayer)
- Added null guards in `OnAttackEnter`, `OnAttackUpdate`, `OnAttackEnd` — matches existing pattern in `SetElementalEventState`/`ResetEventStateFields`

### MantraMuktha Aiming Investigation
- Logs show aiming flow working correctly — every TriggerShootDown→EnterAiming_Weapon→TriggerShootUP→WeaponStrike completes
- "RAPID OnAttackEnter" warnings are diagnostic noise, not stuck state
- User likely experienced tutorial breaking (NullRef) disrupting overall flow

### Spell Data Warning Investigation
- "Failed to load spell data for FIRE" is pre-existing (not a regression)
- Player's elementals default to byte 0 (=FIRE) when `Player_elementals` is null in tutorial
- `FIRE_0_0.asset` exists — failure likely in PrefabManager `filePaths` serialized config

## Key Decisions
- Staging secret key stored only in session memory (not committed to repo)
- Bot simulation null guards are surgical — don't create simulation for bots (unnecessary overhead)
- Spell data warning deferred — pre-existing, non-blocking

## Files Changed

### AUM-The-Epic (AUM_BODY) — Commit `a9169d35`
- `Assets/Scripts/Player/ControllerBase.cs` — Null guards on simulation in melee lifecycle
- `Assets/Scripts/Managers/GameManager.cs` — Tutorial local fallback (3 fixes)
- `Assets/Scenes/AvatarCreate.unity` — tutorialSceneName serialized field
- `ProjectSettings/EditorBuildSettings.asset` — Scene path rename
- `Assets/QuestSystem/QuestFace.cs` — Debug log text
- `Assets/Scripts/Utils/AUM_MatchDiagnostics.cs` — Comment
- `Assets/Resources/AUMAuthConfig.asset` — buildMode→Staging
- `Assets/Resources/LocalTestingSettings.asset` — Config updates
- `Assets/Scenes/Initiate.unity` — Environment/devAccountIndex
- `Assets/AddressableAssetsData/AddressableAssetSettings.asset` — Builder index

### AUM-Headless (AUM_MIND) — Commit `4380d10`
- `Packages/manifest.json` — Package version bumps
- `Packages/packages-lock.json` — Lock file update
- `ProjectSettings/ProjectVersion.txt` — Unity 6000.0.62f1

## Open Items
- "Failed to load spell data for FIRE" warning — needs PrefabManager filePaths investigation
- Legacy port plan phases S4-S6 still pending (meleeAimState was reverted, AVATARUPLOAD reinit, Tutorial overhaul)

## Next Session Should
- Test tutorial end-to-end after these fixes
- Investigate PrefabManager SPELLDATA filePaths if spell warnings persist
- Continue legacy port plan (S5: AVATARUPLOAD, S6: Tutorial overhaul) if prioritized
