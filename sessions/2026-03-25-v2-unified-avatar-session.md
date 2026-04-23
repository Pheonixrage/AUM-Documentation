# Session: V2 Unified Avatar System — March 25, 2026

## What Was Done This Session

### 1. Git Cleanup (Phase A)
- Deleted stale local branches in AUM-The-Epic and AUM-Headless
- Kept only `v2` and `AUM_MIND` branches

### 2. V2 Naming Cleanup
- Renamed `ConnectionMode.PlayFab` → `ConnectionMode.Online`
- Renamed `ConnectionMode.Hetzner` → `ConnectionMode.DirectServer`
- Renamed `BuildMode.Development_PlayFab` → `BuildMode.Development_Online`
- Renamed `AuthMode.FirebaseOpenId` → `AuthMode.Firebase`
- Renamed `UsePlayFabMatchmaking` → `UseOnlineMatchmaking`
- Files: ServerAllocator.cs, AUMAuthConfig.cs, AUMAuthManager.cs, AUMAuthManagerEditor.cs

### 3. Combat Authority Fixes
- **ServerManager.cs** — Gated V1→V2 authority sync (only when MIND server connected)
- **SimulationManager.cs** — Skip V1 position verification for HybridAuthority
- **NakamaManager.cs** — WebSocket reconnect guard for play mode exit
- **NetworkManager.cs** — ConnectToServer blocked for HybridAuthority + DisconnectedFromServer guard
- **GameManager.cs** — CheckNetworkStatus skips for HybridAuthority, cleanup hook for LocalMatchController
- **CombatAuthorityFactory.cs** (both copies) — Server→HybridAuthority fallback restored back to ServerAuthority after MIND deployed

### 4. LocalMatchController Created
- `Assets/Scripts/CombatAuthority/Integration/LocalMatchController.cs` — NEW
- Handles local match flow without MIND: state progression, bot AI, simulation generation
- Uses `LocalTutorialBotAI` in Fight mode for bots
- Tested and verified working (bot attacks, match ends on death)

### 5. MIND Server Deployed to Singapore
- Upgraded AUM-Headless from Unity 2022.3 to Unity 6 (6000.0.62f1)
- Installed Linux IL2CPP build support
- Built fresh server binary
- Deployed to Singapore `5.223.55.127:7800` via Docker
- Fixed `/server/Logs/` directory missing in Dockerfile
- Server runs, client connects, bot AI works, basic combat functions

### 6. Current State of Play
- Client connects to MIND server on Singapore:7800 ✅
- PREGAME → TELEPORT → MATCH state machine works ✅
- Bot AI runs (BotBrain decisions) ✅
- Bot melee attacks land ✅
- **Issues remaining:** desyncs, player spells not spawning entities, death state not triggering visually, disconnects after extended play

## Plan Going Forward: Unified Avatar System

**Full plan saved at:** `/Users/mac/.claude/plans/staged-dancing-salamander.md`

### Summary
Replace 5 fighting styles (Amuktha, MukthaMuktha, MantraMuktha, PaniMuktha, Yantramuktha) with:
- **1 universal male mesh + 1 universal female mesh** (use existing Amuktha mesh as base)
- **5 interchangeable weapons** (Sword, Axe, Staff, Bow, Chakra) — any body + any weapon
- **Weapon animation swapping** via AnimatorOverrideController (Layer 1 combat anims swap per weapon)
- **Start with 1 weapon, unlock rest** via Gnana Tokens in Train section
- **Body customization** via 4 blendshape sliders (muscular/lean/tall/short)

### Phase Order
1. **Phase 1** — Universal mesh + animator + 5 weapon animation overrides
2. **Phase 3** — Wire AvatarBuilder into match loading (GameManager)
3. **Phase 2** — Redesign avatar creation UI (LokaIntroScreen)
4. **Phase 4** — Weapon selection screen in Train section
5. **Phase 5** — MIND server unified avatar support
6. **Phase 6** — Cosmetic system migration
7. **Phase 7** — Progression integration

### V2 Code Already Built (Ready to Wire)
- `_AUM/Scripts/Avatar/Core/AvatarIdentity.cs` — data model ✅
- `_AUM/Scripts/Avatar/Core/AvatarBuilder.cs` — assembly pipeline ✅
- `_AUM/Scripts/Avatar/Core/PlayerCombat.cs` — unified combat controller ✅
- `_AUM/Scripts/Avatar/Weapons/*.cs` — all 5 IWeaponBehavior implementations ✅
- `_AUM/Scripts/Avatar/Bodies/BodyMorpher.cs` — blendshape morphing ✅
- `_AUM/Scripts/Progression/WeaponMasteryManager.cs` — weapon XP tracking ✅
- `nakama-server/progression.go` — backend RPCs ✅

## Infrastructure State

| Server | IP | What's Running |
|--------|-----|----------------|
| Singapore | 5.223.55.127 | Nakama (7350-7352) + MIND V2 (7800/UDP) + P2 game server (7777) + P2 orchestrator (8080) |
| Helsinki | 65.109.133.129 | P3 Legacy (inactive) |

## Files Modified This Session

### AUM-The-Epic (BODY)
1. `Assets/Scripts/Network/ServerAllocator.cs` — renamed enums
2. `Assets/Scripts/Auth/AUMAuthConfig.cs` — V2 naming
3. `Assets/Scripts/Auth/AUMAuthManager.cs` — AuthMode.Firebase
4. `Assets/Scripts/Auth/AUMAuthManagerEditor.cs` — AuthMode.Firebase
5. `Assets/Scripts/Nakama/NakamaManager.cs` — WebSocket guard
6. `Assets/Scripts/Managers/ServerManager.cs` — V1→V2 sync gate
7. `Assets/Scripts/Managers/SimulationManager.cs` — position verify gate
8. `Assets/Scripts/Managers/NetworkManager.cs` — ConnectToServer block + disconnect guard
9. `Assets/Scripts/Managers/GameManager.cs` — LocalMatchController wiring + cleanup
10. `Assets/Scripts/CombatAuthority/Integration/CombatAuthorityFactory.cs` — ServerAuthority restored
11. `Assets/_AUM/Scripts/Combat/Integration/CombatAuthorityFactory.cs` — ServerAuthority restored
12. `Assets/Scripts/CombatAuthority/Integration/LocalMatchController.cs` — **NEW**
13. `Assets/Resources/AUMAuthConfig.asset` — gameServerPort 7777→7800

### AUM-Headless (MIND)
1. `Dockerfile` — added `mkdir -p /server/Logs`
2. `ProjectSettings/ProjectVersion.txt` — upgraded to Unity 6 (6000.0.62f1)
3. Fresh Linux IL2CPP build in `Build/`

## Key Architecture Decisions
- **Approach B** for multiplayer: Nakama (backend) + MIND headless (60Hz combat) + LiteNetLib UDP
- **HybridAuthority** for local testing, **ServerAuthority** for online play
- **LocalMatchController** as fallback when MIND server unavailable
- **Body-weapon decoupling** is the V2 core design — already built, needs wiring
