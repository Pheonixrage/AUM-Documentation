# AUM Project Context (Living Document)

**Last Updated**: 2026-01-12
**Updated By**: Claude Code Session

---

## Project Overview

**AUM** is a global cross-platform multiplayer fighting game. The architecture follows a server-authoritative pattern for all combat mechanics.

### Repository Structure
| Repo | Purpose | Path |
|------|---------|------|
| AUM-The-Epic | Unity Client (2022.3 LTS) | `/Users/mac/Documents/GitHub/AUM-The-Epic` |
| AUM-Headless | Unity Headless Server | `/Users/mac/Documents/GitHub/AUM-Headless` |
| AUM-Documentation | This docs repo | `/Users/mac/Documents/GitHub/AUM-Documentation` |

---

## Current Branch Status

### AUM-Headless
- **Branch**: `feature/authoritative-architecture`
- **Status**: Clean
- **Recent Focus**: Combat authority, MCP server updates, bot movement fixes

### AUM-The-Epic
- **Branch**: Check with `git branch`
- **Recent Focus**: Intent system, netcode infrastructure, visual smoothing

---

## Architecture Overview

### Combat Authority System
Central abstraction for combat state management. Lives in `Assets/Scripts/CombatAuthority/`.

```
ICombatAuthority (interface)
├── BaseAuthority (abstract - shared logic, state history)
├── LocalAuthority (Tutorial/Training - offline, no validation)
├── ServerAuthority (Multiplayer - server validates everything)
└── HybridAuthority (Solo modes - prediction + post-validation)
```

**Key Files**:
- `Core/ICombatAuthority.cs` - Interface definition
- `Core/BaseAuthority.cs` - State history buffer (128 ticks)
- `Authorities/ServerAuthority.cs` - Server reconciliation
- `Authorities/LocalAuthority.cs` - Tutorial mode (no stamina checks)
- `Integration/PlayerAuthorityLink.cs` - Unity component bridge
- `Integration/CombatAuthorityFactory.cs` - Creates appropriate authority per game mode

### State Machine
FSM-based character control. Key pattern: check `stateManager.IsBlockingInput()` before transitions.

**Files**:
- `Assets/Scripts/StateMachine/StateManager.cs`
- `Assets/Scripts/Player/ControllerBase.cs` - 20+ states defined

### Networking
LiteNetLib-based client-server communication with prediction and reconciliation.

**Files**:
- `Assets/Scripts/Managers/NetworkManager.cs`
- `Assets/Scripts/Managers/ServerManager.cs`

### Input System
Unified input through `UnifiedInputProvider` and `InputManager`.

**Files**:
- `Assets/Scripts/Managers/InputManager.cs`
- `Assets/Scripts/Managers/UnifiedInputProvider.cs`
- `Assets/Scripts/Input/Core/IntentProcessor.cs`
- `Assets/Scripts/Input/Core/IntentValidator.cs`

---

## Characters (5 Fighting Styles)

| Character | Path |
|-----------|------|
| Amuktha | `Assets/Characters/Amuktha/Scripts/AmukthaPlayer.cs` |
| MantraMuktha | `Assets/Characters/MantraMuktha/Scripts/MantraMukthaPlayer.cs` |
| MukthaMuktha | `Assets/Characters/MukthaMuktha/Scripts/MukthaMukthaPlayer.cs` |
| PaniMuktha | `Assets/Characters/PaniMuktha/Scripts/PaniMukthaPlayer.cs` |
| Yantramuktha | `Assets/Characters/Yantramuktha/Scripts/YantramukthaPlayer.cs` |

---

## Trinity Gods (Ultimate Types)

| God | Buff |
|-----|------|
| Brahma | Shield abilities, +3 focus streak start |
| Vishnu | +30% movement speed |
| Shiva | Third Eye immunity, +20% damage |

---

## Backend Stack

| Service | Purpose | Notes |
|---------|---------|-------|
| PlayFab (15F2B7) | Currencies, catalog, inventory, leaderboards | Title ID: 15F2B7 |
| Firebase | Google OAuth | Auth flow only |
| Hetzner VPS | Deployment | systemd managed |

---

## Known Issues (Active)

| ID | Issue | Severity | Notes |
|----|-------|----------|-------|
| #1 | Dodge animation plays but movement incomplete | High | WIP |
| #2 | Joystick cleared to (0,0) before dodge reads it | High | Investigating |
| #3 | State mismatch spam in editor logs | Medium | Rate-limited |

---

## Recent Session Summary

### 2026-01-12: Session Management System
- Created `/session` command for interactive workspace/workflow selection
- Created `session-management.md` rules for auto context loading
- Established wrap-up workflow for session logging

### 2026-01-11: Combat Authority + MCP Server Updates
- Combat authority system updates
- Bot movement and state machine stability fixes
- InputValidator compile error fixes (property names)

### 2026-01-09-10: Intent System + Camera Fixes
- Intent system implementation
- Camera jitter fixes
- Visual position smoothing

### 2026-01-08: Dodge System Fixes
- Fixed dodge teleport to map center
- Fixed dodge rubberbanding root cause
- Fixed dodge stamina system and scale mismatch
- Bot diagnostics improvements

### 2026-01-04-05: Tutorial Mode & Authority System
- Phase 0-7 implementation complete
- LocalAuthority for offline Tutorial/Training modes
- HybridAuthority for prediction + validation
- Spectator mode implementation
- Tutorial mode stamina bug fixed (root cause: missing NotifyQuestStarted calls)

---

## Critical Rules (Quick Reference)

### DO NOT
- Trust client-reported damage values
- Use `Update()` for networked game logic (use `FixedUpdate()`)
- Edit `Assets/Plugins/` or `Assets/PlayFabSDK/`

### ALWAYS
- Use ICombatAuthority for combat state queries/mutations
- Check `stateManager.IsBlockingInput()` before state transitions
- Route input through UnifiedInputProvider/InputManager
- Test both client AND headless server when changing shared code

---

## MCP Tools Available

| Tool | Use |
|------|-----|
| `mcp__unity__log_tail` | Client logs (last N lines) |
| `mcp__unity__log_errors` | Client errors (grouped) |
| `mcp__unity-headless__log_tail` | Server logs |
| `mcp__unity-headless__log_errors` | Server errors |

Log locations: `/tmp/aum/client_*.log`, `/tmp/aum/server_*.log`

---

## Session Start Checklist

When starting a new session, Claude should:
1. Read this CONTEXT.md
2. Check `sessions/` for recent session logs
3. Review any relevant ADRs in `decisions/`
4. Check git status on both repos
