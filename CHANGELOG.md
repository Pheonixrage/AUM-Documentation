# AUM Changelog

All notable changes across both AUM-The-Epic (Client) and AUM-Headless (Server).

---

## [2026-02-15] Store Icons, WearItems, Name Uniqueness, Cancel Race Condition, Karma

### AUM-The-Epic (Client)
- **fix**: Set bundle icons — AssetManager.GetKeysFromUniqueID now allows Sets for Icon objectType, loads proper 120 Set addressable icon assets instead of falling back to individual piece icons
- **fix**: Store Featured tab — inherits PlayFab "featured" tags from catalog Set items before they're skipped; only Lohithavastra Gold featured
- **fix**: Store Set labels — proper set name (Aranyavastra/Lohithavastra), tier (Bronze/Silver/Gold), "SET" slot label
- **fix**: wearItems filter — ConvertToAvatarInfo filters out Treasure/Sets items from corrupted PlayFab data on load
- **fix**: wearItems fallback — uses explicit 6 physical ItemTypes instead of `Enum.GetValues(typeof(ItemType)).Length` (was 8, creating bogus Treasure+Sets items)
- **fix**: New avatar wearItems — GenerateDefaultWearItems() now called during AddDefaultItemsForAvatar() (was dead code)
- **fix**: Blend shape crash — MeshCombiner CombineBlendShapes adds bounds check + try-catch for duplicate Head items from match rewards
- **fix**: CancelMatch race condition — immediately sets IsSearching=false + botMatchRequested=true + stops coroutines BEFORE async PlayFab cancel
- **fix**: Cross-player karma effects — delayed currency refresh for losers in MatchEndManager
- **fix**: Post-match guna display fixes in GunaScreen
- **feat**: Global avatar name uniqueness — FighterManager calls CloudScript checkAndRegisterAvatarName before creating avatar

### PlayFab CloudScript (Dev rev 69, Prod rev 25)
- **feat**: `checkAndRegisterAvatarName` — atomic check+register using Title Internal Data "AvatarNameRegistry"
- **feat**: `unregisterAvatarName` — remove name from registry on avatar deletion

### PlayFab Configuration
- **fix**: All 7 matchmaking queues set to MinTeamSize=0, MinMatchSize=2 on both DEV and PROD titles

### AUM-Headless (Server/Orchestrator)
- **fix**: Orchestrator FFA bot team collision — reads occupied teams from players_data, assigns bots to free slots only
- **fix**: Bot names unified — 100 Indian human-like names via BOT_NAMES constant

### Key Learnings
- **ItemType enum pitfall**: Head=0..Weapons=5 are physical (6 items). Treasure=6, Sets=7 are virtual. Never use Enum.GetValues length for wearItems count.
- **Set icons exist**: 120 assets in `Assets/AUM_Addressables/Icons/` with `itemType: 7` (Sets). AssetManager was blocking ALL Sets in GetKeysFromUniqueID — must allow for Icon objectType.
- **Featured inheritance**: PlayFab catalog Set items tagged "featured" were skipped at catalog processing line. Must capture featured status BEFORE the skip.
- **Name registry**: Title Internal Data is atomic per-key, suitable for global name uniqueness. Key format: `{lowercaseName: "playFabId_avatarGuid"}`.

---

## [2026-02-13] Store Purchase Bugs — Currency, Inventory, WearItems

### AUM-The-Epic (Client)
- **fix**: Currency reconciliation uses `Math.Max(VC, AvatarData)` for BZ/SV/GD — prevents stale avatar data from zeroing out Virtual Currencies on login
- **fix**: Inventory sync preloads PlayFab catalog before processing items — old purchases without itemCode CustomData now resolve via catalog lookup
- **fix**: Set purchase popup shows individual piece icons via async Addressable loading (was showing set icon 5x)
- **fix**: CustomizationScreen saves wearItems to PlayFab on confirm — replaces stubbed `SendCustomizationItemUUIDs` left from WebSocket removal
- **fix**: Client passes itemCode in `PurchaseItem()` calls for server-side CustomData tagging
- **fix**: "No avatar loaded" error guard with `EnsureAvatarId` helper in PlayFabAvatarCurrencyService
- **fix**: Transparent overlay stuck on purchase error — `buyItemPanel.Close()` in error handler
- **feat**: Currency conversion UI improvements and null guards
- **feat**: CloudScript backfill call (fire-and-forget) tags old inventory items with itemCode after sync

### PlayFab CloudScript (Dev — Revision 60)
- **feat**: `purchaseWithAvatarCurrency` stores itemCode in granted item's CustomData
- **feat**: `backfillInventoryItemCodes` handler — iterates inventory, resolves itemCode from catalog, tags items missing CustomData

---

## [2026-02-11] PlayFab Social Services & Lobby System

### AUM-The-Epic (Client)
- **feat**: Wire friends, party, lobby systems to PlayFab REST APIs
- **feat**: PlayFabLobbyService - create, join, leave, browse, invite via PlayFab Multiplayer API
- **feat**: PlayFabFriendsService - friend code generation, search, friend requests via CloudScript
- **feat**: PlayFabPartyService - party management skeleton
- **feat**: Discord SDK scaffold (DiscordManager, DiscordRichPresence, DiscordChatService)
- **feat**: Training mode local match bypass (no server needed)
- **feat**: MCP autonomous dev tools (execute_code, screenshot, simulate_input, get_ui_state)
- **fix**: Lobby creation UI transition (forceNextPoll flag, immediate GetLobbyState)
- **fix**: Lobby polling backoff (5s base, +5s/error, 30s max, auto-stop after 10)
- **fix**: Stale lobby auto-cleanup on browse and app quit
- **fix**: LobbyData constructor skipping players with empty friendID
- **fix**: OnLobbyLeft not stopping polling (caused rate-limit spam)
- **fix**: Double lobby creation guard (isCreatingLobby flag)
- **fix**: Profile screen blank friend ID (handle missing SocialInfo for new players)
- **fix**: Lobby toggle hidden on Karma Marga (removed wins>0 gate)
- **fix**: 10 compilation errors in PlayFab social services

### PlayFab CloudScript
- **feat**: Deployed 7 new social handlers (Revision 51, 24 total)
- GenerateFriendCode, SearchByFriendCode, SendFriendRequest, ClearFriendRequest
- GetFriendsEnrichmentData, SendInvite, ClearProcessedInvites

---

## [2026-02-11] Autonomous Development Pipeline

### Infrastructure
- **feat**: Expanded MCP server suite from 4 to 12 servers (all connected)
- **feat**: Added Context7 (live SDK docs), Docker, Playwright, GitHub, Hetzner Cloud, SSH, Sentry, Firebase MCP servers
- **feat**: Built 5 custom MCP tools: execute_code, screenshot, set_property, simulate_input, get_ui_state
- **feat**: Unity Headless MCP bridge connected (port 6401)
- **feat**: Docker v29.2.0 installed and MCP connected

### Autodev Skill (`/autodev`)
- **feat**: Created 10-phase autonomous development pipeline skill
- **feat**: Full deployment pipeline: local verify → staging → user gate → production

### Configuration
- **chore**: All credentials discovered autonomously from codebase/system
- **chore**: MCP servers split: 4 project-level (.mcp.json) + 8 user-level (~/.claude.json)

---

## [2026-02-07] - LEGENDARY FIXES

### AUM-The-Epic (Client)
- **fix**: Focus system - ServerAuthority.ConsumeFocus sync-back via SetFocusRaw()
- **fix**: AUMLogger level fix for proper debug output
- **fix**: Earth stun always applies regardless of elemental cycle

---

## [2026-01-30] LEGENDARY FIX

### AUM-The-Epic (Client)
- **[LEGENDARY] fix**: Elemental/SpecialAbility controls fully working
  - Fixed elemental buttons (1-4) to match Attack button behavior
  - HOLD = enter aiming state, RELEASE = cast spell
  - Added proper drag direction detection before entering aiming
  - Shield cast on drag DOWN now works correctly
- **fix**: CastManager uses `player.m_elementals` instead of stale `Player_elementals`
- **fix**: Focus timing - uses target fill amount for segment activation (not animated value)
- **fix**: Added epsilon to prevent floating point edge cases in focus thresholds

### AUM-Headless (Server)
- **[LEGENDARY] fix**: Server elemental sync from AVATARUPLOAD packet
  - `ProcessAvatarUpload()` now updates `player.elementals` array
  - CastManager reinitialized with correct elementals from client

### Technical Details
- **Root Cause**: `InterfaceManager.Instance.Player_elementals` was stale (FIRE defaults)
- **Solution**: Use `player.m_elementals` which comes from `matchAvatar.elementalSelected`
- **Spell Index Format**: `(int)elementalType << 5 | spellType`
- **Button Phases**: BEGINDRAG waits for drag direction, DRAG determines shield vs aiming

---

## [2026-01-23]

### AUM-The-Epic (Client)
- **feat**: Client-only tutorial system - runs without game server
- **feat**: LocalTutorialManager - spawns player and bot locally
- **feat**: LocalBot + LocalBotBT - client-side bot AI (ported from server)
- **feat**: TestModeClient tutorial mode toggle
- **fix**: Tutorial quests updated for local bot support (Tutorial6, TutorialBot, TutorialKillBot*)
- **fix**: GameManager skips server packet in client-only tutorial
- **fix**: WebSocket guards for PlayFab mode (FriendsManager, PartyManager, LobbyManager, MainMenuPacketManager)
- **fix**: Node.cs GetRootNode() method for behavior tree

---

## [2026-01-11]

### AUM-Headless
- **chore**: Combat authority + MCP server updates
- **fix**: Bot movement + state machine stability fixes
- **fix**: InputValidator compile errors - correct property names
- **feat**: Phase 3-5 Security & Performance infrastructure
- **feat**: Server-side ControllerBase improvements + SyncDebugger

### AUM-The-Epic
- **fix**: MeshSerializer color space + cache invalidation
- **chore**: Addressables + CDN setup + remaining code updates
- **fix**: Tick synchronization + SimulationList overflow fixes
- **fix**: Skip runtime texture packing for pre-packed addressable items
- **feat**: CombatCalculator + Intent system updates

---

## [2026-01-09 - 2026-01-10]

### AUM-The-Epic
- **feat**: Intent System + Camera Jitter Fixes
- **feat**: Esports-grade netcode infrastructure (Phases 1-3)
- **fix**: Critical fixes for VisualPositionSmoother
- **feat**: Visual Decoupling: VisualPositionSmoother for camera
- **fix**: Sensitivity fixes + Interpolator urgency enhancement

---

## [2026-01-08]

### AUM-Headless
- **fix**: Dodge teleport to map center + state mismatch
- **fix**: Dodge rubberbanding root cause + bot diagnostics
- **fix**: Dodge stamina system and scale mismatch

### AUM-The-Epic
- **fix**: Astra button, shield drag, and screen transitions

---

## [2026-01-04 - 2026-01-05]

### Both Projects
- **feat**: Phase 7: Tutorial mode fixes + PrefabManager improvements
- **feat**: Phase 6: HybridAuthority for prediction + validation
- **feat**: Phase 5: Combo Training Mode
- **feat**: Phase 4: Spectate Mode - SpectatorAuthority and SpectatorManager
- **feat**: Phase 3: TrainingDummy for offline practice modes
- **feat**: Phase 2: LocalAuthority for offline Tutorial/Training modes
- **feat**: Phase 1: Combat Authority damage event integration
- **feat**: Phase 0: Focus system fixes & legacy cleanup
- **feat**: Add CombatAuthority system and enhanced GameModeSettings

### Key Fix
- **fix**: Tutorial mode stamina bug - missing `NotifyQuestStarted()` calls in 28/32 quests

---

## [2026-01-02]

### AUM-Headless
- **fix**: SessionID validation - MD5(PlayFabId) matching
- **feat**: GameModeSettings, MatchController wait mode, MatchState realtime countdown

---

## [2025-12-31]

### AUM-Headless
- **feat**: Add waitForOtherPlayers feature for local 2-player testing
- **fix**: Connection stability & countdown timing
- **fix**: Bot synchronization - Broadcast AUTHENTICATE_REPLY inside InitializeBots

---

## Format Guide

When adding entries:
```
## [YYYY-MM-DD]

### {Project Name}
- **{type}**: {description}
```

Types: feat, fix, chore, refactor, docs, test, perf
