# AUM Changelog

All notable changes across both AUM-The-Epic (Client) and AUM-Headless (Server).

---

## [2026-02-07] - LEGENDARY FIXES

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
