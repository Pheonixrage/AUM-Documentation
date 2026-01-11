# AUM Changelog

All notable changes across both AUM-The-Epic (Client) and AUM-Headless (Server).

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
