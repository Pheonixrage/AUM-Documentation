# AUM Changelog

All notable changes across both AUM-The-Epic (Client) and AUM-Headless (Server).

---

## [2026-02-19] Nakama Migration Commit + MantraMuktha Aim Fix

### AUM-The-Epic (Client) — `AUM_BODY`
- **feat**: Full Nakama migration committed (154 files, +13,457 / -1,632 lines)
- **feat**: 17 Nakama service classes (auth, data bridge, economy, matchmaking, social, chat, leaderboards, karma, IAP, remote config)
- **feat**: 8 shared Data types extracted from PlayFab to `Assets/Scripts/Data/` (KarmaTypes, InventoryTypes, SocialTypes, AvatarCurrencyData, CatalogItemData, CatalogItemMapper, StoreTypes, LeaderboardTypes)
- **feat**: Go server with 34+ RPCs in `nakama-server/` (match_end, currency, purchase, karma, inventory, etc.)
- **feat**: Analytics scaffolding (AUMAnalyticsManager)
- **fix**: StateManager BlockFlags — removed Block_Melee from WeaponStrike, Block_Dodge from EnterAiming_Weapon
- **chore**: PlayFab imports removed from 61 non-PlayFab files
- **chore**: PlayFabItemData/PlayFabItemMapper deleted (moved to CatalogItemData/CatalogItemMapper in Data/)

### AUM-Headless (Server) — `AUM_MIND`
- **fix**: State renames synced with client (Melee→WeaponStrike, Aiming→EnterAiming_Weapon, Third_Eye→ThirdEye, Teleport→MatchTeleport)
- **fix**: MantraMuktha SetAnimStateLengthStartPoint restored in OnAttackEnter
- **fix**: animStateLength uses clientTickRateMS (matches client timing)
- **fix**: MantraMuktha teleport moved from dead OnSpecialAnticipateUpdate to OnSpecialAbilityEnter
- **fix**: WeaponStrike/EnterAiming_Weapon BlockFlags aligned with client
- **debug**: `[AIM-DBG]` logging added to MantraMuktha OnAimEnter/Update/Exit and PlayerManager PROGRESS/AIMING handlers
- **chore**: Package manifests updated

### AUM-Documentation — `AUM_SPIRIT`
- **docs**: Session log for Nakama migration + MantraMuktha aim fix
- **docs**: Changelog updated

### Known Issue
- MantraMuktha aim-to-attack partially fixed but not fully resolved — debug logging in place for next playtest

---

## [2026-02-12] Grand Merge Verification & Branch Structure

### AUM-The-Epic (Client) — `AUM_BODY`
- **fix**: IsBotMatch bug in PlayFabMatchmaker.cs (line 799: false -> true)
- **feat**: ApplyBuildModeSync() in ServerAllocator for auto ConnectionMode sync
- **fix**: AUMAuthConfig moved to Resources/ for Resources.Load compatibility
- **chore**: PreConnectManager.cs.meta added
- **verified**: MatchFoundPopup Cancel/Accept flow (programmatic + UI)
- **verified**: Full post-match flow on loss (Panel_2 -> Panel_3 -> MainMenu)
- **verified**: Zero client errors across full match lifecycle

### AUM-Headless (Server) — `AUM_MIND`
- **chore**: ProjectSettings updated for Unity version compatibility
- **known**: PreConnect avatar sync timeout on Singapore (auth succeeds, AvatarSync=False)

### AUM-Documentation — `AUM_SPIRIT`
- **docs**: Grand Merge verification session log
- **docs**: MCP playtest pipeline documentation

### Branch Structure Established
| Branch | Project | Purpose |
|--------|---------|---------|
| `AUM_BODY` | AUM-The-Epic | Client (UI, input, rendering) |
| `AUM_MIND` | AUM-Headless | Server (authority, validation) |
| `AUM_SPIRIT` | AUM-Documentation | Context, logs, architecture |

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
