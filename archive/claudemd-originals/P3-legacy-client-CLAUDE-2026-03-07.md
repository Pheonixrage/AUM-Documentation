# AUM Legacy Client

**Repo:** `AUM-Unity-Staging-Legacy` | **Branch:** `legacy-working-oct29` | **Unity 6**
**Goal:** Add PlayFab integration to working legacy code. DO NOT refactor gameplay.

---

## Quick Reference (MUST SURVIVE COMPACTION)

| Key | Value |
|-----|-------|
| PlayFab DEV | Title: `15F2B7` / Secret: `JOAWWZ87KNU9KIXBTRG1PFXUHMGBSMQNSSMKKIR6F76GIIAFW3` |
| PlayFab PROD | Title: `158C02` / Secret: `3YET9HU3F5ZBZ5FUQ3DEUOZECKPFDP1FEND8TKKUY5466DESZH` |
| Hetzner VPS | `65.109.133.129` / Dev: port `6006` / Prod: ports `7850-7909` |
| Orchestrator | Port `8080` / API key: `AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8` |
| Queue fix script | `C:\Users\PC_01\fix_all_queues.ps1` or `fix_queues_curl.bat` |
| CloudScript | Dev revision 131 / Prod revision 53 |
| Android Keystore | `C:\Keystore\AUM-google-upload.keystore` / Pass: `brahman123` / Alias: `aum` / SHA1: `D5:7B:AD:56:79:BA:CB:E4:C7:0E:AC:DE:60:7B:D5:99:9E:81:41:A0` |
| Server repo | `D:\dll test windows deply\AUM-Server` / Branch: `legacy-working-oct6` |
| Client repo | `c:\23rd Jan Reimport` / Branch: `legacy-working-oct29` |
| Orchestrator repo | `D:\dll test windows deply\AUM-Server\orchestrator\orchestrator.py` |

### PlayFab REST API (proven working process)
```bash
# Authenticate (get entity token)
curl -X POST "https://{TITLE_ID}.playfabapi.com/Authentication/GetEntityToken" -H "Content-Type: application/json" -H "X-SecretKey: {SECRET_KEY}" -d "{}"

# Set matchmaking queue
curl -X POST "https://{TITLE_ID}.playfabapi.com/Match/SetMatchmakingQueue" -H "Content-Type: application/json" -H "X-EntityToken: {TOKEN}" -d "{...}"

# List queues / Get queue
curl -X POST "https://{TITLE_ID}.playfabapi.com/Match/ListMatchmakingQueues" ...
curl -X POST "https://{TITLE_ID}.playfabapi.com/Match/GetMatchmakingQueue" -d "{\"QueueName\":\"queue_solo_1v1\"}" ...
```

---

## Architecture

```
CLIENT (This Repo)                     SERVER (AUM-Server repo)
├── LiteNetLib UDP (native DLL)        ├── LiteNetLib UDP, 60Hz server-authoritative
├── 60Hz tick, FSM (20+ states)        ├── Hetzner 65.109.133.129
├── PlayFab matchmaking + store        └── Orchestrator: port 8080 (Python)
└── ClockSyncManager (tick sync)
```

---

## Core Files

| File | Purpose |
|------|---------|
| `Assets/Scripts/Managers/GameManager.cs` | Match state machine (NONE→PREGAME→TELEPORT→MATCHRUNNING→ENDMATCH→POSTMATCH→END) |
| `Assets/Scripts/Managers/NetworkManager.cs` | UDP/LiteNetLib — DO NOT MODIFY |
| `Assets/Scripts/Managers/TestModeClient.cs` | Direct Hetzner bypass (65.109.133.129:6006) |
| `Assets/Scripts/StateMachine/StateManager.cs` | FSM core — DO NOT MODIFY |
| `Assets/Scripts/Network/Packet.cs` | Binary packet structures — DO NOT MODIFY |
| `Assets/Scripts/PlayFab/PlayFabMatchmaker.cs` | PlayFab matchmaking + bot fallback |
| `Assets/Scripts/Network/PreConnectManager.cs` | Pre-match server connection, auth, AVATARSYNC deferral |
| `Assets/Scripts/Managers/MainEntranceController.cs` | Match entry, PvP team assignment, server allocation |
| `Assets/Scripts/Managers/CastManager.cs` | Spell casting, aiming, channeling |
| `Assets/Scripts/Player/PlayerInput.cs` | Input processing (elemental/special buttons) |
| `Assets/Scripts/Player/PCInput.cs` | PC keyboard/mouse input (mouseSensitivityScale=0.15) |
| `Assets/Scripts/Input/GamepadInputManager.cs` | Gamepad/controller input (cameraSensitivity=5.0, scene-configurable) |
| `Assets/Scenes/AssetManager.cs` | Addressable loading, GetKeysFromUniqueID, avatar mesh combining |
| `Assets/Scripts/UI/Managers/StoreManager.cs` | Store UI, Set generation, featured filter, icon loading |
| `Assets/Scripts/UI/Managers/FighterManager.cs` | Avatar creation, name validation (CloudScript) |
| `Assets/Scripts/PlayFab/PlayFabDataBridge.cs` | Avatar data ↔ PlayFab sync, wearItems conversion, login currency reconciliation |
| `Assets/Scripts/PlayFab/PlayFabCurrencyService.cs` | Currency conversion via CloudScript (bronze→silver→gold) |
| `Assets/Scripts/UI/CurrencyConversion.cs` | Currency conversion UI, confirmation popup, loading screen |
| `Assets/Scripts/PlayFab/PlayFanInventoryService.cs` | Inventory sync, default wearItems generation |
| `Assets/Scripts/Utils/MeshCombiner.cs` | Mesh combining, blend shape handling |
| `Assets/Scripts/UI/AcceptMatch.cs` | Scene-based match found popup (themed, serialized refs) |
| `Assets/Scripts/PlayFab/PlayFabSocialService.cs` | Friends: code gen, search, requests, list, heartbeat, notifications |
| `Assets/Scripts/PlayFab/PlayFabLobbyService.cs` | Lobby system: CloudScript calls, polling, orchestrator allocation, match start (DEV ONLY) |
| `Assets/Scripts/Managers/LobbyManager.cs` | Lobby data model, 10 PlayFab-delegated stubs, JSON constructor |
| `Assets/UI/Lobby/LobbyUIManager.cs` | Lobby UI: settings, slots, chat, ready/cancel, create/join (831 lines) |
| `Assets/Scripts/Auth/CredentialManagerBridge.cs` | Android Credential Manager JNI bridge (replaces dead google-signin-support:1.0.4) |
| `Assets/Scripts/Auth/BrowserOAuthHandler.cs` | Browser OAuth fallback (implicit flow via `aum://oauth` deep link) |
| `Assets/Scripts/Auth/AUMAuthConfig.cs` | Auth config: webRedirectUri, googleClientId, redirectScheme |
| `Assets/Scripts/Auth/FirebaseRESTAuth.cs` | Firebase REST auth: SignInWithGoogleIdToken, SignInWithGoogleAccessToken |
| `Assets/Inputs/NewButtonScript.cs` | Button input: drag thresholds, button phases, VFX |
| `Assets/Inputs/CustomButton.cs` | Touch drag handler: direction detection, cancel button hit test |
| `Assets/Scripts/UI/GunaGraph.cs` | Guna wheel rendering: 3 radial-fill Images, DOTween animation, KillActiveSequence |
| `Assets/Scripts/UI/RevisedUI/Screens/PostMatchScreens/PostMatchPlayers.cs` | Post-match player display, guna graph refresh from CloudScript |
| `Assets/Scripts/UI/RevisedUI/Screens/HellTimeScreen.cs` | Hell time display, UseHellShard CloudScript integration |
| `Assets/Scripts/PlayFab/PlayFabDailyRewardService.cs` | Daily rewards: per-avatar CloudScript calls, FetchDailyRewardState + ClaimDailyReward |
| `Assets/Scripts/UI/Managers/DailyRewardsScreen.cs` | Daily rewards UI: 7-day calendar, claim buttons, countdown timer |

---

## Critical Rules

**DO NOT MODIFY:** StateManager.cs, NetworkManager.cs, Packet.cs, animation timing, 60Hz tick rate
**ALWAYS:** Check `stateManager.IsBlockingInput()` before state transitions. Test PC + mobile.
**NEVER WITHOUT PERMISSION:** Commit, delete files, change gameplay code, modify core systems.

---

## Characters & Gods

**Styles:** Amuktha (melee/dash), MukthaMuktha (melee/axe), MantraMuktha (ranged/teleport), PaniMuktha (ranged/discus), Yantramuktha (ranged/arrow). Ranged use Aiming state (hold attack). Scripts: `Assets/Characters/{Name}/Scripts/{Name}Player.cs`
**Gods:** Brahma (shield, +3 focus), Vishnu (+30% speed, stamina discount), Shiva (Third Eye, +20% dmg)

---

## Recent Fixes

| Date | Fix | Files |
|------|-----|-------|
| **Mar 2** | **PaniMuktha character invisibility fix (Tamas karma + Shiva/Vishnu)** — PaniMuktha characters became completely invisible on PostMatchPlayers screen after receiving Tamas karma on GunaScreen, specifically when god=Shiva or Vishnu. Only weapons were visible floating in space. Root causes: (1) `StopDissolveEffect()` never restored PaniMuktha dual discus weapons — only handled standard `weaponObj` and Brahma shields, so leftDiscus/rightDiscus remained in dissolved state (`_Dissolve_ON_OFF=1`). (2) `PlayerDissolveEffect()` hardcoded `TrinityGods.Brahma` instead of using actual player's god (`godSelected_DissolvePlayer`). For Shiva/Vishnu, only `rightDiscus` exists (no `leftDiscus`). Hardcoded Brahma caused `Holster_Left.GetChild(0)` to return NULL → silent NullReferenceException via `?.` operator. Fix: (1) Added PaniMuktha weapon restoration in `StopDissolveEffect()` using pattern matching `is PaniMukthaData` — always restores `rightDiscus` (all gods), conditionally restores `leftDiscus` (Brahma only). Falls back to `weaponObj` for other fighting styles. (2) Fixed `PlayerDissolveEffect()` line 309 to use actual god: `TrinityGods.Brahma` → `godSelected_DissolvePlayer`. Direct `paniData.leftDiscus`/`rightDiscus` access with null checks. Only dissolves weapons that exist. Impact: PaniMuktha + Shiva/Vishnu + Tamas now fully visible on post-match screen with correct weapons. | GunaScreen.cs |
| **Mar 2** | **Lobby screen updates + password preservation + disband detection** — Three lobby fixes deployed and tested: (1) **Lobby screen not updating for other player after match return** — Root cause: `LobbyUIManager.Initialize()` never called automatically during scene lifecycle, only when browsing lobby list screen. Players returning from match bypassed lobby list → `Instance` singleton never set → `ApplyLobbyState()` silently failed. Fix: Call `Initialize()` from `OnEnable()` to ensure singleton set and `isPacketProcessPending` flag checked on every scene enable. Impact: Both players now see updated lobby UI after returning from matches. (2) **Password preservation during keyboard input on mobile** — Root cause: Prefab destruction cleared password text when keyboard opened on Android. Fix: Static `passwordCache` dictionary survives prefab recreation, restores cached password only if field empty (prevents keyboard closing). Impact: Password text no longer lost when keyboard appears. (3) **Members not getting disbanded when host leaves during match** — Root cause: `cancelMatch` CloudScript failure logged but `LobbyDisbanded` flag not checked immediately. Fix: Immediately call `PollLobbyState()` when `cancelMatch` fails with "not_in_lobby" error (line 799-812 PlayFabLobbyService.cs). Impact: Members instantly see "The lobby has been disbanded." message when host leaves. All fixes verified working by user testing. | LobbyUIManager.cs, LobbyListUIPrefab.cs, PlayFabLobbyService.cs, LobbyManager.cs |
| **Feb 26** | **iOS gold Set 3D preview fix (permanent cross-platform)** — Gold Set items showed icon in store but 3D avatar preview was blank on iOS. Worked on Android. Root cause: `AssetManager.EquipItem()` used `InstantiateAsync().WaitForCompletion()` — a synchronous block on a GPU async operation inside an `Addressables.LoadAssetsAsync` callback. iOS Metal has stricter GPU synchronization than Android OpenGLES3; blocking inside the callback deadlocked when GPU was still processing the previous asset load. Gold Sets triggered it because they load 5 high-poly mesh pieces sequentially. This was the ONLY place in the codebase using this pattern — every other instantiation (AvatarSpawner:68, AssetManager:129,227,589) uses standard `Instantiate()`. When `EquipItem` failed, it caught the exception and returned `null`, but callers at `StoreManager.cs:972` and `:911` didn't null-check `ItemObj` → `NullReferenceException` → silently swallowed by fire-and-forget `_ = EquipItemAsync()`. Fix: (1) Replaced `InstantiateAsync().WaitForCompletion()` with `Instantiate()` in `EquipItem` — matches proven pattern used everywhere else. (2) Added null checks on `equipItem.ItemObj` in Set preview loop (skip failed pieces with warning). (3) Added null check on `itemToEquip.ItemObj` for individual items. (4) Added null check on `iconAsset` in `AssignItemIconButton` before cast to `AddressableIcon`. (5) Wrapped `EquipItemAsync()` body in try-catch to log errors instead of silently swallowing. | AssetManager.cs, StoreManager.cs |
| **Feb 26** | **Daily reward system activated via PlayFab CloudScript** — Migrated daily rewards from removed WebSocket server to CloudScript following meditation timer pattern. Per-avatar state stored in `DailyRewardState_{avatarId}` (UserInternalData). Server-authoritative time via `Date.now()`. 24h strict streak reset (miss a day = restart from Day 1). 7-day cycle: Bronze rewards [50, 75, 100, 125, 150, 175, 200] configurable via TitleData `DailyRewardConfig`. CloudScript handlers: `getDailyRewardState` (schedule + cooldown + streak expiry check), `claimDailyReward` (validates cooldown, awards Bronze via `AddUserVirtualCurrency`, updates avatar UserData). New `PlayFabDailyRewardService.cs` singleton bridges client to CloudScript. `PacketManager.RequestDailyReward` NOP stub now delegates to service. Login trigger in `PlayFabDataBridge.CheckAllDataLoaded`. `MainEntranceController` catch-up for data loaded before MainMenu + FTUE gate. Avatar switching (AvatarViewScreen:237,260) automatically fetches new avatar's state. CloudScript Dev rev 113. | PlayFabDailyRewardService.cs (new), DailyRewardsScreen.cs, PacketManager.cs, PlayFabDataBridge.cs, MainEntranceController.cs, temp_cloudscript_dev.js |
| **Feb 26** | **PaniMuktha dual discus fix (all phases)** — Opponent's PaniMuktha disc weapon appeared at world origin (0,0,0) during match, prematch, AND post-match (karma selection). Root cause: all 3 weapon creation paths (`InstantiateMatchAvatars`, `RebuildAvatar`, `CreateBotAvatar`) always created two discus instances (`leftDiscus` + `rightDiscus`) regardless of god. But `EquipWeapon()` only parented `leftDiscus` to a bone when `god == TrinityGods.Brahma`. For Vishnu/Shiva, `leftDiscus` was instantiated at (0,0,0) by Unity and never reparented — floating at world center forever. Same `matchAvatars[]` persist across all phases (prematch, match, post-match/karma), so the stray disc was visible everywhere. Fix: (1) Only create `leftDiscus` for Brahma god in all 3 paths. (2) `PaniMukthaData.EquipWeapon` simplified: removed Brahma-only gate, now parents `leftDiscus` whenever it exists (null check sufficient since only Brahma creates one). (3) GunaScreen `EquipWeapon(0, 0)` changed to `EquipWeapon(0, TrinityGods.Brahma)` for clarity. | GameManager.cs, PaniMukthaData.cs, GunaScreen.cs |
| **Feb 26** | **Victory animation persistence fix** — After winning a match, victory animation played once then reverted to running/idle. Root causes: (1) `PlayVictoryAnim()` used `SetTrigger("victory")` (one-shot, auto-resets) so animator fell back to blend tree after clip finished. (2) `Move()` continued during Victory — `ProcessPlayer()` only checked `IsDead()`, not Victory. (3) AnyState→Victory transition had `m_CanTransitionToSelf:1` — with Bool staying true, animation restarted every frame. (4) Victory→Exit transition was unconditional. Fix: Changed `SetTrigger` to `SetBool("victory", true)` (persistent, mirrors Death's `isDead` pattern). Added Victory guard to `ProcessPlayer()` to skip `Move()`. `OnVictoryEnter` resets overlay layers + zeros movement params. `OnVictoryExit` resets victory bool. All 5 Animator Controllers updated: victory param Trigger→Bool, AnyState→Victory `m_CanTransitionToSelf:0`, Victory→Exit requires `victory==false`. | ControllerBase.cs, PlayerBase.cs, Amuktha.controller, MukthaMuktha.controller, MantraMuktha.controller, PaniMuktha.controller, Yantramuktha.controller |
| **Feb 26** | **PvP female character dress fix (AVATARSYNC rebuild)** — Opponent's female Amuktha character dress was messed up during PvP. Root cause: client-side timing race — server creates wildcard placeholder with `fighterClass=0` (Male) and empty wearItems. First AVATARSYNC arrives with stale Male data, client builds Male 3D model via `InstantiateMatchAvatars()`, then second AVATARSYNC arrives with correct Female data but model is already built and never rebuilt. Fix: (1) Added `RebuildAvatar()` async method in GameManager.cs — destroys stale 3D model, rebuilds from updated `match_Avatars` data with correct fighterClass/wearItems, loads weapons (PaniMuktha dual discus handled). (2) Added rebuild trigger in NetworkManager.cs `ApplyAvatarSyncToMatchAvatars()` — captures old fighterClass/wearItems before `UpdateAvatarFromServer()`, compares after, triggers `RebuildAvatar()` if changed and model already built. (3) GunaScreen: disable RigBuilder before unparenting avatars to prevent Burst crash from ambiguous bone paths during post-match. | GameManager.cs, NetworkManager.cs, GunaScreen.cs |
| **Feb 26** | **Currency panel hidden after leaving lobby** — PointsPanel disappeared after exiting lobby. Root cause: `FadeOption.OnDisable()` called `gameObject.SetActive(false)` which destroyed child activation state when parent was deactivated (Unity preserves explicit `activeSelf=false` on children even when parent re-activated). Fix: Changed `OnDisable()` to `group.DOKill(); busy = false;` (safe DOTween cleanup without destructive SetActive). Defense-in-depth: LobbyUIManager.OnDisable now calls `PointsPanel.Open()` after re-activating the panel. | FadeOption.cs, LobbyUIManager.cs |
| **Feb 25** | **Lobby system backend (DEV ONLY)** — PlayFab CloudScript lobby implementation following Party system architecture. (1) Created `PlayFabLobbyService.cs` (~1200 lines): singleton service with CreateLobby, JoinLobby, LeaveLobby, KickPlayer, SetReady, UpdateSlot, ToggleBots, StartLobbyMatch, SendLobbyChat, ListPublicLobbies, polling (3s), orchestrator `/allocate` for match start. (2) Rewrote `LobbyManager.cs`: filled all 10 TODO stubs delegating to PlayFabLobbyService, added JSON constructor on LobbyData, `LobbyPlayerAvatarData` class for extended fields, `playerEntityIds` dictionary for orchestrator. (3) Added 9 CloudScript handlers (~600 lines) to `temp_cloudscript_dev.js`: CreateLobby, JoinLobby, GetLobbyState, LeaveLobby, KickFromLobby, UpdateLobbyPlayer (7 actions), SendLobbyChat, ListPublicLobbies, CleanupLobbyOnLogin. (4) Fixed LobbyUIManager: match start → `LobbyManager.Instance.StartLobbyMatch()`, chat → `PlayFabLobbyService.Instance.SendLobbyChat()`. (5) Added PlayFab browse path: `LobbyListUIScreen.InitializeFromPlayFab()`, `LobbyListUIPrefab.Initialized(LobbyListItem)`. (6) Lobby invites in PlayFabSocialService: `type == "lobby"` in CheckForPendingInvites + ClearLobbyStateOnLogin. (7) MainEntranceController: StopLobbyPolling on match found. CloudScript Dev rev 107. | PlayFabLobbyService.cs (new), LobbyManager.cs, LobbyUIManager.cs, LobbyListUIScreen.cs, LobbyListUIPrefab.cs, PlayFabSocialService.cs, PlayFabDataBridge.cs, MainEntranceController.cs, temp_cloudscript_dev.js |
| **Feb 25** | **Fix mobile controls broken by gamepad commit** — (1) GamepadInputManager platform guard: entire class wrapped in `#if UNITY_EDITOR || UNITY_STANDALONE_WIN` so it doesn't compile on Android. Root cause: Unity OnScreenControl creates a virtual Gamepad device → `isRealGamepadConnected` check passed on mobile → GamepadInputManager activated → intercepted all touch button events. `AddComponent<GamepadInputManager>()` in GameManager.cs also guarded. NewButtonScript.OnButtonEvent GamepadInputManager gate wrapped in same `#if`. (2) Restored ElementalAbility1-4 action interactions from `"Press(behavior=1)"` back to `"Hold(duration=0.15),Tap,Press(behavior=1)"` — gamepad commit stripped Tap/Hold interactions, breaking mobile tap-to-cast (TapInteraction generates TAP phase) and hold-to-aim (HoldInteraction generates HELD phase). (3) Restored 6 shuffled/deleted gamepad bindings in PlayerControls.inputactions to match scene CustomButton m_ControlPath values: dpad/down→CancelSpell, rightShoulder→Melee, leftTrigger→BrahmaShield, dpad/left→ThirdEyeAbility, rightTrigger→AstraAbility, re-added deleted dpad/up→DodgeAbility. Gamepad commit remapped these paths to different actions but didn't update scene m_ControlPath — so touching Attack button fired BrahmaShield, touching Shield fired DodgeAbility, etc. (4) Restored Fire→rightTrigger binding interactions to empty (was wrongly changed to `"Hold(duration=0.2),Tap,Press(behavior=1)"`). (5) PCInput.cs null guard: disables duplicate PCInput instance with unassigned serialized fields. Zero PC/controller impact — GamepadInputManager handles all controller input directly on PC/Editor, bypassing Input System bindings. | GamepadInputManager.cs, GameManager.cs, NewButtonScript.cs, PCInput.cs, PlayerControls.inputactions, PlayerControls.cs |
| **Feb 24** | **Server-side currency conversion + FTUE cosmetics + post-match fixes + CloudScript rev 105** — (1) Currency conversion moved to CloudScript: `SubtractUserVirtualCurrency`/`AddUserVirtualCurrency` client APIs were disabled in PlayFab Game Manager. New `convertCurrency` CloudScript handler validates conversion path (bronze→silver=1000:1, silver→gold=100:1), atomically updates avatar UserData + syncs PlayFab VCs. `PlayFabCurrencyService.cs` rewritten to use `ExecuteCloudScript`. Avatar ID fallback via `InterfaceManager.activeAvatarInfo.uniqueID`. (2) Stale currency reconciliation: login detects missed conversion pattern (avatar source > VC source AND avatar target < VC target), trusts VCs, fixes local cache. `PlayFabAvatarCurrencyService.LoadAvatarCurrencies` syncs avatar cache from CloudScript. `getAvatarCurrencies` CloudScript does server-side VC comparison + auto-fix. (3) Post-match friend request: `PostMatchProfile` uses real PlayFab `friendId` from `SocialInfo` instead of mock "TEST" data. (4) FTUE cosmetic rewards: match grants + auto-equip on win. (5) `CurrencyConversion.cs` loading screen dismiss on insufficient balance early return. CloudScript Dev rev 105. | PlayFabCurrencyService.cs, PlayFabDataBridge.cs, PlayFabAvatarCurrencyService.cs, CurrencyConversion.cs, PostMatchProfile.cs, MatchEndManager.cs, CustomizationScreen.cs, PlayFanInventoryService.cs, InterfaceManager.cs, temp_cloudscript_dev.js |
| **Feb 24** | **Fibonacci guna wheel fix + hell time + CloudScript rev 102** — (1) Guna wheel 100% fill fix: CloudScript `computeGunaPercentages` added BASELINE=33 pseudo-counts so initial state=33.3/33.3/33.4%, first action nudges to ~34/33/33%. (2) Karma count persistence: moved counts from `Avatars` UserData (overwritten by client `SaveAvatarData`) to separate `KarmaState` UserData key (only written by CloudScript). (3) PostMatchPlayers guna refresh: screen renders before async CloudScript returns, so `Update()` polls `cloudScriptRewardsReady` flag then calls `RefreshGunaGraphsFromCloudScript()` reading from `playerRewards` (authoritative source). `KillActiveSequence()` prevents delayed DOTween from overwriting refresh. (4) MatchDetailScreen center icon fix: `matchRewardData.aPlayerGuna` now set from CloudScript dominant. (5) GunaGraph equal-thirds fallback: 85/85/85 instead of single-255 when no karma selected. (6) Hell time screen: UseHellShard CloudScript integration with timer reduction UI. (7) CloudScript try-catch + execution log forwarding. CloudScript Dev rev 102. | GunaGraph.cs, PostMatchPlayers.cs, MatchEndManager.cs, PlayFabAvatarCurrencyService.cs, HellTimeScreen.cs, temp_cloudscript_dev.js |
| **Feb 23** | **Gamepad controller support + sensitivity matching + settings panel fix** — (1) Full gamepad input via GamepadInputManager.cs: face buttons=elementals (deferred double-tap for shield), L1=special aiming, R1=ThirdEye/Shield, R2=cast/attack, L2=context-aware cancel-or-dodge, D-pad left=Astra, Start=settings toggle, right stick=camera. (2) Dual-subscriber fix: NewButtonScript gates combat buttons when gamepad active (prevents duplicate events). (3) Elemental slot validation: uses `m_elementals.Length` instead of unreliable SpellIndice null check (scene-serialized). Applied to GamepadInputManager + PCInput. (4) Sensitivity matching: gamepad `cameraSensitivity` reduced 25→5, PC mouse `mouseSensitivityScale=0.15` — matches mobile touch feel. Both scene-configurable via Inspector. (5) Settings panel empty on 2nd open fix: `settingsGeneralContent`/`settingsSoundContent` fields reset to GENERAL tab on every `Settings()` call. (6) AIR indicator jitter fix: clamp inside `AdjustCastPosition()`. (7) Special ability aiming: L1 release no longer cancels (persists until R2 cast or L2 cancel). **Android impact fixed Feb 25:** runtime guard was insufficient (OnScreenControl creates virtual Gamepad), replaced with compile-time `#if UNITY_EDITOR || UNITY_STANDALONE_WIN` platform guard + restored shuffled bindings. | GamepadInputManager.cs (new), PCInput.cs, NewButtonScript.cs, GameManager.cs, CastManager.cs, PlayerControls.inputactions |
| **Feb 23** | **PC automatic camera + simplified elemental aiming** — (1) Automatic camera rotation: mouse movement now rotates camera without requiring right-click (like modern FPS games). (2) Ultra-simplified aiming: press 1-4 to enter aiming, mouse adjusts aim automatically, left-click to cast, right-click to cancel. No holding/dragging required. (3) Fixed elemental indicator jitter: Fire/Water/Ether/Earth now have fixed indicators (only AIR moves forward/backward with vertical mouse). Root cause: double camera rotation (TouchField DRAG + ElementalDragTest both rotating camera) + conflicting sensitivities (same delta.y used for camera height AND indicator position). Fixed with state-based camera rotation (horizontal-only for AIR, normal for others) + direct indicator position adjustment. (4) E button Vishnu fix: disabled for Vishnu (no shield/third-eye). Platform guards preserve mobile touch controls. | PCInput.cs, PlayerInput.cs, InputManager.cs |
| **Feb 22** | **Android Credential Manager + Vulkan fix + Shield swipe fix** — (1) Replaced dead `google-signin-support:1.0.4` (2017) with Android Credential Manager API. Pure C# JNI bridge via `AndroidJavaObject`/`AndroidJavaProxy` — no AAR/Android Studio needed. Old plugin gated to iOS only. Browser OAuth auto-fallback on failure. Same Firebase `google.com` provider, zero user impact. (2) Forced OpenGLES3 on Android — Vulkan auto-select caused kernel panics on Mali-G76 (Redmi Note 8 Pro) during video decode. (3) Fixed elemental shield swipe-down: dead zone pattern (20px threshold before committing direction), state locking (once aiming/shield entered, no flipping). Root cause: 2px threshold + first DRAG frame always picked UP by a fraction, locking out shield via FSM `IsBlockingInput`. Took 4 iterations. See ANDROID_AUTH_STATUS.md for full history. | CredentialManagerBridge.cs (new), AUMAuthManager.cs, GoogleSignIn.cs, GoogleSignInImpl.cs, GoogleSignInDependencies.xml, mainTemplate.gradle, settingsTemplate.gradle, ProjectSettings.asset, PlayerInput.cs, NewButtonScript.cs, CustomButton.cs |
| **Feb 19** | **Profile system + friends list display** — Edit Profile saves profileName + image to PlayFab SocialInfo. Profile name uniqueness via CloudScript `checkAndRegisterProfileName` (PN_ prefix in TitleInternalData, stale owner check, old key cleanup on rename). Google display name captured from `FirebaseAuthResult.displayName` → auto-set as profileName on first login. Friends list: Line 1 = profile name, Line 2 = "avatarName (fightingStyle)" when online. Edit Profile popup auto-closes after confirm. Background friends list refresh every ~30s via NotificationPollRoutine. CloudScript Dev rev 82, Prod rev 38. | AUMAuthManager.cs, PlayFabDataBridge.cs, ProfileScreen.cs, FriendsUIData.cs, PlayFabSocialService.cs, CloudScript |
| **Feb 18** | **Friends system (Milestone 1)** — New PlayFabSocialService.cs singleton: 8-char friend code gen, search by code, send/accept/decline requests, remove friend, cancel outgoing request, toggle favourite, full friends list with enrichment, pending requests, online heartbeat (60s), notification polling (10s). FriendsManager 6 stubs filled. PostMatchProfile add-friend wired. SortFriends bug fix (Count==0→>0). **Key architecture: friend links only created on accept (server-side via AcceptFriendRequest), never on send.** Decline removes sender's stale link. Cancel outgoing removes from target's pending list. CloudScript: SearchByFriendCode reads active avatar (nickName/fightingStyle via ActiveAvatarId), GetFriendsEnrichmentData parses avatars wrapper + ActiveAvatarId, AcceptFriendRequest creates mutual links, ClearFriendRequest removes sender link on decline, CancelOutgoingFriendRequest for sender-side cancel. Accepted-request detection every ~30s. ProfileScreen refreshes friendId on enable. CloudScript Dev rev 79, Prod rev 35. | PlayFabSocialService.cs (new), FriendsManager.cs, PostMatchProfile.cs, PlayFabDataBridge.cs, ProfileScreen.cs, CloudScript |
| **Feb 18** | **Post-match lives bracket fix** — Lives only change from Tamas karma steal (not from losing alone). Added `cloudScriptRewardsReady` flag to gate MatchDetailScreen DOTween until CloudScript returns. Added `receivedKarma` param (client→CloudScript) so losers self-deduct on Tamas. Removed unreliable cross-player life deduction from winner's CloudScript. CloudScript Dev rev 72, Prod rev 28. | MatchEndManager.cs, MatchDetailScreen.cs, PlayFabAvatarCurrencyService.cs, CloudScript |
| **Feb 17** | **AcceptMatch popup** — Replaced programmatic MatchFoundPopup (code-built UI) with scene-based AcceptMatch panel using themed sprites. SetActive show/hide, serialized refs on MainEntranceController. Bot matches show no opponent name (server decides). PvP shows real name. | AcceptMatch.cs, MainEntranceController.cs, PlayFabMatchmaker.cs |
| **Feb 17** | **PC keyboard controls** — Full PC input: 1-4=elemental aim (left-click cast, right-click cancel), double-tap=shield, Q=special aim (drag-to-aim), E=ThirdEye/Shield, R=Astra, Space=Dodge. Cursor locked+hidden. Mobile UI hidden on PC (continuous enforcement vs InGameScreenController re-enable) | PCInput.cs, PlayerInput.cs |
| **Feb 17** | **Tutorial PreConnect fix** — AvatarCreationController.OnTutorialMatchFound now calls PreConnectManager.StartPreConnect() before loading Map_Hell. Previously skipped PreConnect → 0 buffered packets → match stuck. All platforms. | AvatarCreationController.cs |
| **Feb 17** | **Windows build support** — Firebase skip on Windows standalone, device login fallback, Addressables Windows build target | InitiateGame.cs, FirebaseManager.cs, AUMAuthManager.cs, AddressablesBuildHelper.cs |
| **Feb 16** | **1v5 match merging + collection window** — bot match sends totalPlayers, handles "waiting" merge status, polls /match-status, PvP merge detection (wasMergedIntoPvP), spawn Y=0 clamp | PlayFabMatchmaker.cs, SimulationManager.cs |
| **Feb 16** | **FFA team collision dedup (orchestrator)** — _merge_player_data detects occupied teams, reassigns merged bot-fallback players to next free team (prevents duplicate UniqueID from default Team1) | orchestrator.py |
| **Feb 16** | **FFA team colors** — EntityId vs PlayFabId comparison fix; local player never matched → all players same team color | MainEntranceController.cs |
| **Feb 16** | **PreConnectManager FFA team update** — update localPlayerTeam when server corrects ID in FFA modes + duplicate CREATECHARACTER guard | PreConnectManager.cs |
| **Feb 16** | **2v4 match auto-cancel** — orchestrator MATCH_CONFIGS missing DUO_2V4 key → duplicate UniqueIDs for teammates → match rejection | orchestrator.py |
| **Feb 16** | **Version bump** — 0.1.20→0.1.21, AndroidBundleVersionCode 13→14 | ProjectSettings.asset |
| **Feb 15** | **Set bundle icons** — AssetManager allows Sets for Icon objectType, proper addressable Set icons (120 assets) | AssetManager.cs, StoreManager.cs |
| **Feb 15** | **wearItems filter** — filter Treasure/Sets on load, fallback uses 6 physical types not Enum.GetValues(8), GenerateDefaultWearItems on creation | PlayFabDataBridge.cs, PlayFanInventoryService.cs |
| **Feb 15** | **Global name uniqueness** — CloudScript checkAndRegisterAvatarName + unregisterAvatarName (Dev rev 69, Prod rev 25) | FighterManager.cs, CloudScript |
| **Feb 15** | **Blend shape safety** — bounds check + try-catch in CombineBlendShapes for duplicate Head items (match rewards) | MeshCombiner.cs |
| **Feb 15** | **CancelMatch race condition** — immediate coroutine stop + botMatchRequested flag | PlayFabMatchmaker.cs |
| **Feb 15** | **Cross-player karma** — delayed currency refresh for losers, post-match guna display fixes | MatchEndManager.cs, GunaScreen.cs |
| **Feb 15** | **PlayFab queue config** — MinTeamSize=0 on all 7 queues, both titles | PlayFab API (no code) |
| **Feb 15** | **Orchestrator FFA bot team collision** — reads occupied teams, assigns bots to free slots | orchestrator.py |
| **Feb 14** | PaniMuktha weapon race condition, bronze reward _isBotMatch fix, prefab name clear, bot team colors, duplicate elementals fix, combat log gating | GameManager.cs, MatchEndManager.cs, PlayerBase.cs, BotAvatarFactory.cs |
| **Feb 13** | Store purchase: currency reconciliation Math.Max, inventory catalog preload, wearItems save | PlayFabDataBridge.cs, StoreManager.cs, CustomizationScreen.cs |
| **Feb 12** | All game modes working, lives/currency 3-layer persistence, post-match karma display | orchestrator.py, MatchEndManager.cs, PlayFabAvatarCurrencyService.cs |
| **Feb 10** | Legacy WebSocket removal — 45+ files deleted. Revert tag: `pre-websocket-removal` | ~35 files |
| **Feb 9** | Post-match disconnect/rewards fix for PlayFab, clock sync, dual server dirs | PostMatchPlayers.cs, MatchEndManager.cs, ClockSyncManager.cs |
| **Feb 7** | **Elemental/SpecialAbility controls + server elemental sync from AVATARUPLOAD** | PlayerInput.cs, CastManager.cs, Server:PlayerManager.cs |

---

## Key Knowledge (Patterns That Work)

### Android Auth (CRITICAL)
- **Credential Manager:** `CredentialManagerBridge.cs` — pure C# JNI bridge. Calls `CredentialManager.create()` → `GetGoogleIdOption` → `getCredentialAsync()` → extracts `GoogleIdTokenCredential.idToken`. No AAR/Android Studio needed.
- **Auth token chain:** Google ID token → `FirebaseRESTAuth.SignInWithGoogleIdToken()` → Firebase ID token → PlayFab OpenID Connect → PlayFab session. Same chain for both iOS and Android.
- **Browser OAuth fallback:** If Credential Manager fails (old device, user cancel, exception), `BrowserOAuthHandler` opens Chrome with implicit OAuth flow → `aum://oauth` deep link → access token → `FirebaseRESTAuth.SignInWithGoogleAccessToken()`.
- **iOS native SDK:** `GoogleSignIn 8.0` CocoaPod, unchanged. `GoogleSignIn.cs` and `GoogleSignInImpl.cs` gated to `#if UNITY_IOS` only.
- **Dead 2017 plugin:** `google-signin-support:1.0.4` crashes on AAB builds (Google Play re-signs, cert mismatch). DELETED. Never re-add.
- **Gradle deps:** `androidx.credentials:credentials:1.5.0`, `credentials-play-services-auth:1.5.0`, `googleid:1.1.1`. Hardcoded in `mainTemplate.gradle` — Force Resolve not required.
- **Graphics API:** Android forced to OpenGLES3 only (`m_Automatic: 0`). Vulkan auto-select causes kernel panics on Mali-G76 (Helio G90T). No Vulkan shaders in project.

### PC Controls (Windows Build - CRITICAL)
**Architecture:** Automatic free-look camera + ultra-simplified elemental aiming. Mouse movement alone rotates camera (no right-click). Elemental aiming: press key → aim with mouse → click to cast.

**Keyboard Layout:**
- **1-4 keys**: Elemental aiming (Fire/Water/AIR/Ether/Earth). Press to enter aiming state, left-click to cast, right-click to cancel. Double-tap for shield (Brahma only).
- **Q key**: Special ability aiming. Press to enter aiming state, left-click to cast, right-click to cancel.
- **E key**: Shiva Third Eye (instant) / Brahma Shield (tap=attack, hold=block). **Disabled for Vishnu** (no shield/third-eye).
- **R key**: Astra (god ability, instant cast)
- **Space key**: Dodge (instant)
- **WASD**: Character movement

**Elemental Behavior Table:**

| Elemental | Camera Rotation | Indicator Movement | Vertical Mouse Effect |
|-----------|----------------|-------------------|----------------------|
| **Fire** | Normal (H+V) | Fixed position | Camera tilts up/down |
| **Water** | Normal (H+V) | Fixed position | Camera tilts up/down |
| **AIR (Wind)** | Horizontal only | Moves forward/back | Adjusts indicator distance |
| **Ether** | Normal (H+V) | Fixed position | Camera tilts up/down |
| **Earth** | Normal (H+V) | Fixed position | Camera tilts up/down |

**Camera System:**
- **Automatic rotation**: PCInput.cs captures `Mouse.current.delta` every Update() → feeds to `CamTouchField.delta` → fires TouchField DRAG event (lines 183-192).
- **State-based routing** (PlayerInput.cs lines 429-487):
  - `Special_Aiming`: `ChangeCameraAngleTest()` (height adjustment for special abilities)
  - `Spell_Aiming` (AIR): `ChangeCameraAngleHorizontalOnly()` (vertical mouse adjusts indicator, not camera)
  - `Spell_Aiming` (Fire/Water/Ether/Earth): `ChangeCameraAnglePureView()` (normal camera, fixed indicators)
  - Normal states: `ChangeCameraAnglePureView()` (both horizontal + vertical rotation)

**Jitter Prevention:**
- Only AIR elemental allows indicator forward/backward movement (lines 466-481, PlayerInput.cs: `if (spellIndex.elementalType == Elementals.AIR)`)
- Single camera rotation per frame (no double rotation from TouchField + ElementalDragTest)
- Separate sensitivities: `horizontal_sensitivity` for camera X-axis, `spell_aim_senitivity` for AIR indicator Z-axis

**Platform Guards:**
- All PC changes wrapped in `#if UNITY_EDITOR || UNITY_STANDALONE_WIN`
- Mobile BEGINDRAG/DRAG/ENDDRAG preserved with `#if !UNITY_EDITOR && !UNITY_STANDALONE_WIN` (lines 173-220, 262-292 PlayerInput.cs)
- Mobile UI hidden after game starts (PCInput.cs lines 89-103)

### Gamepad Controller (CRITICAL)
**Architecture:** `GamepadInputManager.cs` — **platform-guarded** (`#if UNITY_EDITOR || UNITY_STANDALONE_WIN`), only compiles on Editor/Windows. Added at runtime via `AddComponent` on GameManager (also guarded). On PC, auto-disables if no real gamepad detected (`isRealGamepadConnected` guard). Feeds same `ButtonHelper.RegisterEvent()` pipeline as mobile/keyboard. **NEVER remove the platform guard** — Unity OnScreenControl creates a virtual Gamepad device on Android that fools `isRealGamepadConnected`, causing GamepadInputManager to intercept all mobile touch events.

**Controller Layout:**
- **Face buttons (A/B/X/Y)**: Elemental 1-4. Deferred double-tap (0.3s window) → single=aiming, double=shield.
- **L1 (Left Bumper)**: Special ability aiming. Press to enter, persists until R2 cast or L2 cancel.
- **R1 (Right Bumper)**: ThirdEye (Shiva) / Shield (Brahma tap=attack, hold=block).
- **R2 (Right Trigger)**: Attack (tap=melee, hold=ranged aim). Also casts active elemental/special aiming.
- **L2 (Left Trigger)**: Context-aware — cancels aiming if aiming, dodges if not. Must press L2 again after cancel to dodge.
- **D-Pad Left**: Astra (god ability, instant).
- **Start**: Toggle settings panel (with cursor unlock/lock).
- **Right Stick**: Camera rotation (continuous polling, not event-based).
- **Left Stick**: Movement (via existing OnScreenStick simulation).

**Dual-Subscriber Safety:**
- NewButtonScript.OnButtonEvent gates combat buttons when `GamepadInputManager.Instance.IsActive` (prevents duplicate events from Input System action subscriptions). Gate is wrapped in `#if UNITY_EDITOR || UNITY_STANDALONE_WIN` — on Android, GamepadInputManager doesn't exist so the gate is compiled out.
- `IsGamepadHandledButton()` covers: Elemental1-4, Dodge, SpecialAbility, GodAbility, ThirdEye, Shield.

**Elemental Slot Validation:**
- Uses `player.m_elementals.Length` as authoritative count (NOT SpellIndice null check — scene-serialized arrays always non-null).
- Applied in: GamepadInputManager, PCInput, DisableUnusedElementalBindings().

### Input Sensitivity (CRITICAL)
**All three input systems feed the same downstream pipeline** (InputManager.ChangeCameraAngle*, PlayerInput DRAG handler, CastManager.AdjustCastPosition). Sensitivity is matched by scaling raw deltas at the source:

| Input System | Raw Range | Scale Factor | Effective Delta | Config Location |
|-------------|-----------|-------------|-----------------|-----------------|
| **Mobile touch** | ~0-50 px/frame | None (1.0) | ~0-50 | N/A (baseline) |
| **PC mouse** | ~10-30 px/frame | `mouseSensitivityScale=0.15` | ~1.5-4.5 | PCInput Inspector (Map_Hell scene) |
| **Gamepad stick** | -1 to 1 | `cameraSensitivity=5.0` | -5 to 5 | GamepadInputManager Inspector (Map_Hell scene, or code default) |

**Downstream pipeline (unchanged, tuned for mobile):**
- Camera horizontal: `delta.x × horizontal_sensitivity(8) × 1.5 × deltaTime`
- Camera vertical: `delta.y × vertical_sensitivity(8) × 0.1 × deltaTime`
- AIR indicator: `delta.y × spell_aim_senitivity(3) × deltaTime`
- Special ability: `delta.y × special_aim__Sensitivity(8) × deltaTime`

**To tune:** Adjust `cameraSensitivity` (gamepad) or `mouseSensitivityScale` (mouse) in Inspector. Higher = faster. Both are `[SerializeField]`.

### Elemental Shield Swipe (Mobile - CRITICAL)
- **Dead zone pattern:** First 20px of drag movement ignored. Direction decided only after 20px threshold crossed. Once committed to `Spell_Aiming` or `Cast_Shield`, state is locked — no flipping mid-drag.
- **FSM blocks shield from aiming:** `IsBlockingInput(Block_Elemental_Shield)` returns true when in `Spell_Aiming`. If aiming locks in first (from sub-pixel UP movement), shield can NEVER activate. Dead zone prevents this.
- **Threshold:** `NewButtonScript.minDragThreshold_Vertical = 20f` (was 2f). Stored in `NewButtonScript.cs`.
- **Direction detection:** `CustomButton.cs` OnDrag: `dragThreshold = (eventData.position - pressPoint).y`. Negative Y = DOWN = shield. Positive Y = UP = aiming.

### Matchmaking (CRITICAL)
- **Queue config:** ALL queues MinTeamSize=0, MinMatchSize=2. If recreated with MinTeamSize=1, multi-player matching breaks for 3+ team modes.
- **PvP flow:** PlayFab fires match (2+ humans) → clients get same matchId → `/allocate` to orchestrator → groups by matchId → 15s collection window → bot backfill
- **Match merging:** Orchestrator redirects new allocations (PvP or bot-fallback) into existing pending PvP matches of same type with room. Bot-fallback clients get "waiting" status and poll `/match-status`.
- **Collection window:** 15s (`bot_backfill_timeout_seconds`). PvP matches return "waiting" until `total_players` met. Bot backfill uses `total_players` (mode size) not `min_players` (human threshold).
- **FFA team collision:** Bot-fallback clients send `teamId: "Team1"` (no PlayFab assignment). Orchestrator `_merge_player_data` detects collision and reassigns to next free team.
- **Bot fallback timeouts:** Tutorial=0s, Solo=12s, Team=20s. Client cancels ticket + requests bot match if no PlayFab match. Solo timeouts must be < orchestrator's 15s collection window.
- **CancelMatch:** Immediately sets IsSearching=false + botMatchRequested=true + stops coroutines BEFORE async PlayFab cancel.
- **Modes:** Solo_1v1(2), Solo_1v2(3, FFA), Solo_1v5(6, FFA), Duo_2v2(4), Duo_2v4(6, =2v2v2), Trio_3v3(6), Tutorial(2)

### PlayFab IDs (CRITICAL)
- **Two different IDs:** `PlayFabId` = Master Player Account ID (e.g. `42D12B65C673577D`). `EntityId` = title_player_account ID (e.g. `5D1705DADEC1C2E5`). These are NOT the same.
- **AUMAuthManager.EntityId** stores the title_player_account EntityId.
- **MatchPlayer** has both fields: `.PlayFabId` (master) and `.EntityId` (title_player_account).
- **Always compare with EntityId** when identifying local player (e.g. MainEntranceController team assignment).

### PreConnectManager (CRITICAL)
- **Duplicate CREATECHARACTER guard:** Server sends CREATECHARACTER for every player — only process the first (our auth reply). `IsAuthenticated` flag gates this.
- **FFA team = uniqueID:** In FFA/Solo modes, `localPlayerTeam` must update when server corrects `localPlayerID`. In team modes (2v2, 3v3), team stays as PlayFab assigned.
- **AVATARSYNC deferral:** In PvP (ExpectedHumanPlayers > 1), defer AVATARSYNC until CREATECHARACTER sets authoritative localPlayerID. Prevents wrong slot filling.
- **Tutorial PreConnect:** AvatarCreationController.OnTutorialMatchFound calls StartTutorialPreConnect (mirrors MainEntranceController pattern). Scene loads only on OnPreConnectReady callback. ExpectedHumanPlayers=1.

### Bot System
- **Detection:** Use `_isBotMatch` flag, NOT name-based. Orchestrator gives bots human-like names.
- **Avatar pipeline:** CreateBotAvatar (coroutine) + InstantiateMatchAvatars (async) — skip index if already populated. matchAvatars[i] set AFTER weapons load.
- **PaniMuktha:** Brahma gets leftDiscus + rightDiscus. Vishnu/Shiva only rightDiscus.

### Guna System (Fibonacci Switching — CRITICAL)
- **Baseline dampening:** CloudScript `computeGunaPercentages` adds BASELINE=33 to each guna count before computing percentages. Initial (0/0/0) → 33.33/33.33/33.34%. After 1 rajas (0/1/0) → 33/34/33%. Prevents 100% fill from single action.
- **Fibonacci switching:** Dominant guna only switches after consecutive non-dominant actions reach Fibonacci threshold (1, 1, 2, 3, 5, 8...). Chain breaks add penalty to threshold. See `processGunaSwitch()` in CloudScript.
- **KarmaState persistence:** Karma counts (`sattvaCount`, `rajasCount`, `tamasCount`, `accumulatedKarma`) stored in `KarmaState` UserData key — separate from `Avatars` UserData. Client's `SaveAvatarData()` overwrites `Avatars` but never touches `KarmaState`. Only CloudScript writes to `KarmaState`.
- **0-255 scale:** Client converts percentage (0-100) to byte (0-255) via `percentage * 2.55f` for guna wheel rendering. Rounding fix ensures sum=255 by adjusting tamas.
- **PostMatchPlayers timing fix:** Screen renders before async CloudScript returns. `PostMatchPlayers.Update()` polls `cloudScriptRewardsReady` → calls `RefreshGunaGraphsFromCloudScript()` → reads from `playerRewards` (authoritative, always updated by HandleCloudScriptRewards). `GunaGraph.KillActiveSequence()` kills the initial 1.5s-delayed DOTween sequence to prevent it from overwriting the refresh.
- **Data flow:** CloudScript → `HandleCloudScriptRewards` → updates `playerRewards` (0-255 scale) + `matchRewardData` + `matchPlayerData`. PostMatchPlayers reads `playerRewards`. MatchDetailScreen reads `matchRewardData`.
- **GunaGraph rendering:** 3 stacked radial-fill Images. `fillAmount = value/total`, rotation = cumulative. `Initialize()` = instant snap. `GenerateGraph()` = DOTween animated with delay.

### Economy
- **3-layer persistence:** Match end → CloudScript, Background/Quit → SyncAllToPlayFab, Login → reconcile (Math.Max)
- **Lives:** Only change from Tamas karma steal: winner +1 (cap 5), loser -1 (via `receivedKarma` self-deduction). Losing alone does NOT cost a life. Two stores: playerRewards.lives + activeAvatar.currencies.lives.
- **Rajas steal:** opponentReward + (storedBronze × 0.20). BOT_BRONZE_POOL=500. BOT_REWARD_MULTIPLIER=0.75.
- **CloudScript:** processAvatarMatchEnd (match), syncAvatarToVC (background), purchaseWithAvatarCurrency (store), convertCurrency (conversion)
- **Currency conversion:** MUST use CloudScript `convertCurrency` — client-side `SubtractUserVirtualCurrency`/`AddUserVirtualCurrency` APIs are DISABLED in PlayFab Game Manager. CloudScript updates avatar UserData + VCs atomically. Client caches updated values in `activeAvatarInfo.currencies` to prevent `SaveAllAvatars` from re-corrupting server data.
- **Stale conversion detection:** Login reconciliation in `PlayFabDataBridge` detects pattern (avatar bronze > VC bronze AND avatar silver < VC silver) → trusts VCs. `getAvatarCurrencies` CloudScript also checks VCs server-side and auto-fixes stale avatar data.
- **cloudScriptRewardsReady:** MatchEndManager flag that gates MatchDetailScreen DOTween animation until CloudScript returns server-authoritative values. Prevents bracket text showing stale mock data.
- **receivedKarma flow:** Client extracts karma applied TO the loser → passes string ("tamas"/"rajas"/"sattva") → CloudScript `processAvatarMatchEnd` self-deducts life on Tamas. Avoids unreliable cross-player deduction timing.

### Store & Addressable Icons (CRITICAL)
- **ItemType enum:** Head=0, Torso=1, Hands=2, Pants=3, Legs=4, Weapons=5, Treasure=6, Sets=7. Only 0-5 are physical wearables.
- **Set icons exist:** 120 dedicated Set icon assets in `Assets/AUM_Addressables/Icons/` (e.g. `MantraMuktha_Male_Sets_1_Icon.asset`). Keys: `[Style, Class, "Sets", Identifier, "Icon"]`.
- **AssetManager.GetKeysFromUniqueID:** Returns `null` for Treasure always. Returns `null` for Sets ONLY when objectType != Icon. Sets have icons but no 3D meshes.
- **Set generation:** Sets are synthetic — generated in StoreManager from groups of 5 armor pieces sharing same identifier. PlayFab catalog has both individual pieces AND Set items (Set items tagged "featured" etc).
- **Featured inheritance:** PlayFab Set items tagged "featured" are captured BEFORE the skip at line 405, then passed to `GenerateSetItemsFromIndividuals()` via `featuredSetIdentifiers` HashSet.
- **Item identifiers:** 1=Aranya Bronze, 2=Aranya Silver, 3=Aranya Gold, 4=Lohitha Bronze, 5=Lohitha Silver, 6=Lohitha Gold.

### WearItems (CRITICAL)
- **Physical types only:** wearItems must have exactly 6 items (Head, Torso, Hands, Pants, Legs, Weapons). NEVER use `Enum.GetValues(typeof(ItemType)).Length` (=8, includes Treasure+Sets).
- **Filter on load:** `ConvertToAvatarInfo` filters out Treasure/Sets items from corrupted PlayFab data.
- **Default initialization:** `GenerateDefaultWearItems()` in PlayFanInventoryService called during `AddDefaultItemsForAvatar()` for new avatars.
- **Blend shapes:** Two items of same type (e.g. Head 1 + Head 2 from match reward) cause duplicate blend shape names. MeshCombiner has HashSet dedup + try-catch safety.

### Avatar Name Uniqueness
- **CloudScript handlers:** `checkAndRegisterAvatarName` (atomic check+register), `unregisterAvatarName` (for deletion). Deployed Dev rev 69, Prod rev 25.
- **Registry:** PlayFab Title Internal Data key `AvatarNameRegistry` — JSON `{lowercaseName: "playFabId_avatarGuid"}`.
- **Client flow:** FighterManager.ConfirmName() → local check → CloudScript check → ProceedWithName() or error.

### Friends System (CRITICAL)
- **Architecture:** Friend links are ONLY created on accept (server-side via `AcceptFriendRequest` CloudScript). `SendFriendRequest` stores in target's `PendingFriendRequests` only — no `PlayFabClientAPI.AddFriend` on send.
- **Friend codes:** 8-char unique codes stored in `SocialInfo.friendId` (UserInternalData) + reverse lookup `FC_{code}` in TitleInternalData.
- **PlayFabSocialService.cs:** Singleton on MainMenu scene. Handles all PlayFab social API calls. `friendCodeToPlayFabId` dictionary for ID resolution.
- **Notification polling:** Every 10s checks for new incoming requests. Every ~30s checks if outgoing pending requests were accepted (via PlayFab friends list comparison).
- **Cancel outgoing:** Sender can cancel pending request via `CancelOutgoingFriendRequest` CloudScript (removes from target's pending list). FriendsManager detects pending outgoing via `isPending==1 && isSourcePlayer==1`.
- **Decline:** `ClearFriendRequest` CloudScript removes from receiver's pending list + removes sender's stale PlayFab friend link (safety net).
- **Avatar data in friends list:** `GetFriendsEnrichmentData` reads `Avatars` (wrapper `{"avatars":[...]}`) + `ActiveAvatarId`, finds active avatar by `uniqueID`, extracts `nickName`/`fightingStyle`. Client fallback: if profileName empty → use avatarName.
- **Friends list display:** Line 1 = profileName (from Edit Profile or auto-set from Google account). Line 2 = "avatarName (fightingStyle)" when online, empty when offline.
- **Profile name auto-set:** On login, `ApplySocialInfo()` checks if profileName empty → prefers `AUMAuthManager.GoogleDisplayName` (from Firebase auth), falls back to `DisplayName` (from PlayFab profile). One-time auto-set, saved back to PlayFab.
- **Profile name uniqueness:** `checkAndRegisterProfileName` CloudScript — PN_ prefix in TitleInternalData, value = playFabId. Stale owner check (verifies SocialInfo still has that name). Old PN_ key cleaned up on rename. ProfileScreen.UpdateProfile() validates format (3-20 chars) + CloudScript check before save.
- **Online status:** `LastSeen` timestamp updated every 60s by heartbeat. Online = within last 120s.
- **ProfileScreen:** `OnEnable()` refreshes friend code display, calls `GenerateOrLoadFriendCode` if empty. Edit Profile popup auto-closes after confirm via `editProfilePanel.SetActive(false)`.

### CloudScript Handlers (Current)
- **processAvatarMatchEnd** — match end rewards/penalties
- **syncAvatarToVC** — background currency sync
- **purchaseWithAvatarCurrency** — store purchase (tags itemCode in CustomData)
- **backfillInventoryItemCodes** — tags old inventory items
- **checkAndRegisterAvatarName** — global avatar name uniqueness check+register (AN_ prefix)
- **checkAndRegisterProfileName** — global profile name uniqueness check+register (PN_ prefix, stale owner check, old key cleanup on rename)
- **unregisterAvatarName** — remove name from registry
- **GenerateFriendCode** — generates unique 8-char friend code, stores in InternalData + TitleInternalData reverse lookup
- **SearchByFriendCode** — looks up player by code, returns profileName/profileImageId/isFriend/isPending
- **SendFriendRequest** — stores in target's PendingFriendRequests + sends push notification via server.SendPushNotification
- **ClearFriendRequest** — removes request from PendingFriendRequests + removes sender's unidirectional friend link on decline
- **AcceptFriendRequest** — creates mutual friend links (server.AddFriend both directions) + clears pending request
- **CancelOutgoingFriendRequest** — sender cancels own request: removes from target's PendingFriendRequests
- **GetPendingFriendRequests** — returns current player's pending friend requests array
- **GetFriendsEnrichmentData** — batch reads friendCode/avatarName/fightingStyle/profileName/LastSeen/GameState per friend (reads ActiveAvatarId + Avatars wrapper)
- **UseHellShard** — consumes 1 hell shard, reduces hell timer by 1 hour, returns remaining time/shards/exit status
- **checkHellStatus** — checks if player is in hell, returns remaining seconds/shards/gunaState, handles auto-exit
- **convertCurrency** — server-side currency conversion (bronze→silver=1000:1, silver→gold=100:1). Validates path, computes exact multiples, updates avatar UserData + syncs PlayFab VCs atomically. Replaces blocked client APIs.
- **SendInvite** — sends lobby/party invite with push notification (+ 3 more social handlers)
- **CreateLobby** — creates lobby room, stores LobbyState on host UserData, registers in PublicLobbies TitleInternalData if public
- **JoinLobby** — joins by lobbyId or hostPlayFabId (invite path), password validation, position assignment, returns join code (0-4)
- **GetLobbyState** — polling endpoint: returns full lobby state + chat messages from host's UserData
- **LeaveLobby** — removes player from lobby, disbands if host leaves, cleans up PublicLobbies
- **KickFromLobby** — host kicks player by friendCode, clears their LobbyMembership
- **UpdateLobbyPlayer** — multi-action handler: setReady, slotUpdate, updateSettings, startMatch, matchResult, cancelMatch, updateInfo
- **SendLobbyChat** — stores chat message in host's LobbyChatMessages UserData (max 50 messages)
- **ListPublicLobbies** — reads PublicLobbies from TitleInternalData, filters stale (>2hr) and full lobbies
- **CleanupLobbyOnLogin** — clears stale LobbyState/LobbyMembership on login (mirrors CleanupPartyOnLogin)
- **getDailyRewardState** — per-avatar daily reward state: 7-day schedule, streak expiry check (24h), cooldown timer. Storage: `DailyRewardState_{avatarId}` in UserInternalData. Config from TitleData `DailyRewardConfig`.
- **claimDailyReward** — validates cooldown + streak server-side, awards Bronze via `AddUserVirtualCurrency`, updates avatar UserData currencies, advances day counter. Returns updated schedule + next cooldown.
- **claimLegacyAccount** — legacy MariaDB migration (email→chunks→restore avatars/currencies/karma/names)

### Daily Reward System (CRITICAL)
- **Architecture:** PlayFab CloudScript backend following meditation timer pattern. Per-avatar state in `UserInternalData` (tamper-proof). Server time via `Date.now()` (authoritative).
- **Storage key:** `DailyRewardState_{avatarId}` — each avatar has independent streak. Fields: `currentDay` (1-7), `claimedDays[]`, `lastClaimTimestamp` (ms), `cycleStartTimestamp` (ms).
- **24h strict reset:** If `Date.now() - lastClaimTimestamp > 24h` AND not all 7 days claimed → streak resets to Day 1. Checked on every `getDailyRewardState` call.
- **7-day cycle:** After all 7 days claimed, cycle resets after 24h cooldown from last claim.
- **Config:** TitleData `DailyRewardConfig` = `{"rewardType":0,"rewards":[50,75,100,125,150,175,200]}`. `rewardType: 0` = Bronze.
- **Client service:** `PlayFabDailyRewardService.cs` singleton. `FetchDailyRewardState()` → converts to `RewardTypeInfo` → stores in `InterfaceManager.Instance.dailyRewardsData` → fires `OnDailyRewardRecieved` event.
- **Entry points:** Login (`PlayFabDataBridge.CheckAllDataLoaded`), avatar switch (`AvatarViewScreen:237,260` → `PacketManager.RequestDailyReward`), timer expiry (`DailyRewardsScreen.TimerCoroutine`), MainMenu catch-up (`MainEntranceController.OnEnable`).
- **FTUE gate:** `ActivateDailyReward()` returns early if `IsFTUEActive` — no popup during tutorial.
- **Production:** NOT deployed to PROD. CloudScript handlers only in DEV (revision 113).

### Lobby System (DEV ONLY — CRITICAL)
- **Architecture:** PlayFab CloudScript backend (same polling pattern as Party). Host stores `LobbyState` UserData, members track via `LobbyMembership` UserData. Public lobbies registered in `PublicLobbies` TitleInternalData.
- **Match start:** Host → CloudScript `UpdateLobbyPlayer(startMatch)` → client `AllocateLobbyServer()` → orchestrator `/allocate` → CloudScript `UpdateLobbyPlayer(matchResult)` with IP/port/matchId → members detect via poll → all connect via `PreConnectManager`.
- **Key files:** `PlayFabLobbyService.cs` (core service ~1200 lines), `LobbyManager.cs` (10 stubs filled), `LobbyUIManager.cs` (match start + chat), `LobbyListUIScreen.cs` + `LobbyListUIPrefab.cs` (PlayFab browse path).
- **Lobby ID:** String (not UInt32). PlayFab uses string-based IDs for CloudScript state keys.
- **Dual data paths:** `LobbyPlayerInfo` struct (binary, limited fields) vs `LobbyPlayerAvatarData` class (extended fields: entityId, fighterClass, weaponVariant, wearItemCodes). Extended data stored in `lobby.playerAvatarData` dictionary keyed by friendCode.
- **Production:** NOT deployed to PROD. CloudScript lobby handlers only in `temp_cloudscript_dev.js` (DEV title 15F2B7, revision 108).

### Legacy Migration (Mar 3)
- **Data:** 139 players, 288 avatars in `LegacyMigration_0..9` chunks (Title Internal Data)
- **Client:** `PlayFabDataBridge.CheckLegacyMigration()` fires on every login, sends email to CloudScript
- **CloudScript:** `claimLegacyAccount` — fast returns via `LegacyMigrated`/`LegacyChecked` flags, AN_ name registry, existing player merge, karma conversion (BASELINE=1)
- **Flags:** `LegacyMigrated` (User Internal Data) = already restored. `LegacyChecked` = already scanned (even if no data).
- **Name conflicts:** Legacy player keeps name, new player gets `_2` suffix. PlayStream event logged.
- **Karma:** Per-avatar sattva/rajas/tamas/guna fields in AvatarCurrencyData. karmaState with raw action counts.
- **DEV deployed:** Chunks uploaded + CloudScript rev 131. **PROD pending** — needs chunk upload + CloudScript deploy + new client build.
- **Pre-PROD:** Remove `#if UNITY_EDITOR` test email override in CheckLegacyMigration()

### Elemental Data Flow
- **Authoritative:** `player.m_elementals` (from matchAvatar.elementalSelected). DO NOT use InterfaceManager.Instance.Player_elementals.
- **Bit packing:** `(int)elementalType << 5 | spellType`. FIRE=0, WATER=1, AIR=2, ETHER=3, EARTH=4.

### Input Button Phases
BEGINDRAG→wait for direction, DRAG→DOWN=shield/else=aiming, ENDDRAG→cast, HELD→aiming, RELEASE→cast, TAP→instant cast

### PC Keyboard Controls (PCInput.cs — CRITICAL)
- **Platform guard:** Entire PCInput.cs wrapped in `#if UNITY_EDITOR || UNITY_STANDALONE_WIN` — not compiled on Android.
- **Elemental (1-4):** Deferred tap system. First press starts timer → if no second press within 0.3s, fires HELD (enters aiming). Double-tap within window fires DOUBLETAP (shield).
- **Elemental aiming:** Left-click → RELEASE (cast). Right-click → CancelSpell (cancel). Switching elemental keys auto-cancels previous.
- **Special (Q):** Fires HELD → Special_Aiming. Hold left-click → BEGINDRAG/DRAG (mouse delta moves aim indicator). Release → ENDDRAG (cast). Right-click → cancel.
- **Shield/ThirdEye (E):** Tap → ThirdEye PRESS (Shiva) + Shield TAP (Brahma attack). Hold past threshold → Shield HELD (Brahma block). Release after hold → Shield RELEASE.
- **Astra (R):** GodAbility PRESS (instant).
- **Dodge (Space):** Dodge PRESS (instant).
- **Cursor:** Locked + hidden in Start(). Restored in OnDisable().
- **Mobile UI hiding:** OnScreenStick and cancelButton are continuously forced `SetActive(false)` every frame (InGameScreenController.ToggleControlPanel re-enables them on state transitions). Touch buttons hidden once after game_started.
- **InGameScreenController conflict:** `disableObjects[]` includes OnScreenStick — re-enables on PREGAME/MATCHRUNNING/tutorial. PCInput overrides this every frame.

### Post-Match Flow
Panels: MatchVerdictScreen→GunaScreen→PostMatchPlayers→MatchDetailScreen→PlayerRewardScreen
Mode check pattern: `IsTestMode() || IsPlayFabModeEnabled()`

### Avatar Rebuild (PvP CRITICAL)
- **Problem:** Server creates wildcard placeholder with `fighterClass=0` (Male) + empty wearItems. First AVATARSYNC has stale data. Client builds 3D model from it. Second AVATARSYNC arrives with correct data but model is already built.
- **Fix:** `GameManager.RebuildAvatar(int avatarIndex)` — destroys old model, rebuilds from updated `match_Avatars` data. Triggered by `NetworkManager.ApplyAvatarSyncToMatchAvatars()` when fighterClass or wearItems change after model is built.
- **Bone naming:** Amuktha Male uses `LeftUpperArm/LeftLowerArm`. ALL females use `LeftArm/LeftForeArm`. Male clothing on Female skeleton = mesh corruption.
- **NEVER manually set animator params controlled by FSM states.** Winner = Victory state (`OnVictoryEnter()` → `SetBool("victory", true)`). Loser = Death state (`OnDeathEnter()` → `isDead=true`). Setting `isDead=false` or `victory=false` manually fights with FSM. The FSM exit handlers already handle resets.
- **Victory animation:** Uses `SetBool("victory", true)` (persistent Bool, NOT Trigger). `ProcessPlayer()` skips `Move()` during Victory state. `OnVictoryEnter` resets all overlay layers + zeros movement params. `OnVictoryExit` sets `victory=false`. Animator Controllers: AnyState→Victory `m_CanTransitionToSelf:0`, Victory→Exit requires `victory==false`. Mirrors Death pattern with `isDead` Bool.
- **GunaScreen RigBuilder:** Must disable RigBuilder before unparenting avatars (prevents Burst crash from ambiguous bone paths after reparenting).

### WebSocket Removal (Feb 10)
Fully removed. SocketPacket.cs kept for data structs (AUM.PacketType, AUM.AvatarInfo). Stubbed managers kept for method signatures.

---

## Server Deployment

See `D:\dll test windows deply\AUM-Server\CLAUDE.md` for full deployment docs.
**Key:** Deploy ALL files together (Server.x86_64 + GameAssembly.so + UnityPlayer.so + Server_Data/). Never deploy .x86_64 alone.

---

*Last Updated: March 3, 2026 (legacy MariaDB migration — claimLegacyAccount, per-avatar karma, AN_ name registry)*
