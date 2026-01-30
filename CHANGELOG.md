# AUM Changelog

All notable changes across both AUM-The-Epic (Client) and AUM-Headless (Server).

---

## [2026-01-30] 🏆 LEGENDARY FIX

### AUM-The-Epic (Client)
- **fix**: Character sync - client now sends full character data (fightingStyle, godSelected, elementals) in auth packet
- **fix**: NetworkManager.AuthenticatePlayer() sends activeAvatarInfo to server
- **fix**: Packet.Authenticate_Player extended with character fields
- **fix**: Elemental[] to byte[] conversion for packet serialization
- **chore**: Merged 42 commits from feature/authoritative-architecture to main

### AUM-Headless (Server)
- **fix**: Character sync - server overrides MatchKeeper avatar data with client's actual selection
- **fix**: Socket.cs logs client character data on auth
- **fix**: PlayerManager.AuthenticatePlayer() accepts full packet and overrides avatar
- **chore**: Merged 30 commits from feature/authoritative-architecture to main

### Root Cause
Server was using hardcoded MatchKeeper avatar data (defaulting to Amuktha) instead of client's actual character selection. This caused ranged characters (MantraMuktha) to be treated as melee, blocking the Aiming state and causing position pullback.

### Result
- ✅ Zero errors in playtest
- ✅ Butter smooth gameplay
- ✅ No jitter or snapping
- ✅ Ranged aiming works perfectly
- ✅ All 5 fighting styles working correctly

---

## [2026-01-29]

### AUM-The-Epic (Client)
- **fix**: Micro-jitter fixed - SimulationManager threshold increased to 1.0f
- **fix**: Blocked duplicate input events in same frame
- **fix**: PlayerInput logic overhauled for clean Melee vs Ranged behavior
- **feat**: Input system reset on match start
- **fix**: JitterCompensator EMA smoothing (low-pass filter)
- **fix**: VisualRootController rotation slerp speed increased
- **fix**: 5cm deadzone added for tiny drifts
- **fix**: Multi-tick interpolation jitter in GameManager
- **fix**: Character mesh parented to VisualRoot (smooth) instead of Player (discrete)

### AUM-Headless (Server)
- **fix**: Bot Melee Damage - 1.0m handicap range and 30-degree angle grace
- **fix**: Spell System - mapped initialization by Elemental enum
- **fix**: Water Elemental - auto-calibrate moveSpeed from distance/duration
- **fix**: Tick-to-seconds conversion mismatch for bot timing

---

## [2026-01-24]

### AUM-Headless
- **fix**: StateManager idempotent state registration - prevents ArgumentException on duplicate Add()
- **fix**: Stamina regeneration trap - eliminated negative cooldown blocking regen forever
- **fix**: PlayerBase stamina cooldown changed from -1f (trap) to 2f (direct cooldown)
- **fix**: PlayerManager stamina regen simplified to 2-state system (removed negative check)
- **feat**: Focus system debug logging - ConsumeFocusSegments visibility for debugging
- **feat**: StateManager defensive logging for unregistered state transitions

### Deployment
- **chore**: Hetzner VPS production deployment - 65.109.133.129:7777
- **chore**: Clean server directory structure - removed 89MB of old builds
- **feat**: Orchestrator dual build support - Mac/Windows build selection via API
- **feat**: Systemd service auto-restart (aum-jan24) with dedicated logging
- **docs**: Comprehensive Hetzner deployment guide with API reference

### Fixes Impact
- ✅ MantraMuktha Aiming state now works (state registration fixed)
- ✅ Stamina regenerates correctly after dodge (cooldown trap eliminated)
- ✅ Dodge snapback auto-resolved (was symptom of stamina issue)
- ✅ Focus generation visible in logs (debugging enabled)

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
