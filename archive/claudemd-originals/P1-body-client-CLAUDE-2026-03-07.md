# AUM - Multiplayer Fighting Game

## Core Vision
Global cross-platform multiplayer fighting game designed for scale. All changes must align with server-authoritative architecture, cross-platform compatibility, and scalability as player base grows.

## Architecture
- **Client**: Unity 2022.3 LTS (AUM-The-Epic) - prediction, input, rendering
- **Server**: Unity Headless (AUM-Headless at ../AUM-Headless) - authoritative game logic
- **Authority Pattern**: Server-authoritative for all combat (hits, damage, state changes)
- **Client Behavior**: Predicts locally, server validates and reconciles

## Backend Stack
- **Nakama** (self-hosted on Hetzner Singapore 5.223.55.127): auth, economy, inventory, matchmaking, social, leaderboards
  - Go runtime with 34+ RPCs registered in `nakama-server/main.go`
  - PostgreSQL 16 for all persistent data
  - Server key: `aum_server_dev_2026`, ports 7350-7352
- **Firebase**: Google OAuth (step 1 only), Crashlytics, FCM Push
- **Deployment**: Hetzner VPS with systemd + Docker (Nakama)
- **PlayFab** (Title ID: 15F2B7): LEGACY — being removed. Old services in `Assets/Scripts/PlayFab/`

## Key Systems
- **Combat Authority**: `Assets/Scripts/CombatAuthority/` - ICombatAuthority interface abstracts Local/Server/Hybrid modes
- **State Machine**: `Assets/Scripts/StateMachine/StateManager.cs` + `Assets/Scripts/Player/ControllerBase.cs`
- **Networking**: `Assets/Scripts/Managers/NetworkManager.cs` - LiteNetLib based
- **Input**: `Assets/Scripts/Managers/InputManager.cs` + UnifiedInputProvider
- **Nakama Services**: `Assets/Scripts/Nakama/` - all backend services (auth, data, economy, matchmaking, social, leaderboards)
- **Shared Data Types**: `Assets/Scripts/Data/` - backend-agnostic types used by both Nakama and legacy PlayFab services

## Characters (5 Fighting Styles)
- Amuktha, MantraMuktha, MukthaMuktha, PaniMuktha, Yantramuktha
- Each has: `Assets/Characters/{Name}/Scripts/{Name}Player.cs`

## Trinity Gods (3 Ultimate Types)
- **Brahma**: Shield abilities, +3 focus streak start
- **Vishnu**: +30% movement speed
- **Shiva**: Third Eye immunity, +20% damage

## Build Commands
```bash
# Client build (macOS)
/Applications/Unity/Hub/Editor/2022.3.*/Unity.app/Contents/MacOS/Unity -batchmode -projectPath . -buildTarget StandaloneOSX -quit

# Server build (Linux headless)
/Applications/Unity/Hub/Editor/2022.3.*/Unity.app/Contents/MacOS/Unity -batchmode -projectPath ../AUM-Headless -buildTarget Linux64 -nographics -quit
```

## Critical Rules

### DO NOT
- Trust client-reported damage values (server validates all)
- Use `Update()` for networked game logic (use `FixedUpdate()`)
- Edit `Assets/Plugins/` or generated code
- Modify shared types in `Assets/Scripts/Data/` without checking all consumers (Nakama + PlayFab services both depend on them)

### ALWAYS
- Use ICombatAuthority for combat state queries/mutations
- Check `stateManager.IsBlockingInput()` before state transitions
- Route input through UnifiedInputProvider/InputManager
- Test both client AND headless server when changing shared code

## Current Work
See @IMPLEMENTATION_STATE.md for sprint progress and known issues

## Domain Rules
See `.claude/rules/` for:
- `combat-system.md` - Combat, damage, elemental interactions
- `state-machine.md` - FSM patterns, state callbacks
- `networking.md` - Client prediction, server reconciliation
- `workflow.md` - How to work with this codebase (investigation before coding)
- `unity-debugging.md` - Architecture-aligned debugging approach
- `tutorial-mode.md` - LocalAuthority vs ServerAuthority, quest integration
- `playtest-workflow.md` - MCP log tools for debugging after playtests

## MCP Tools (Unity Log Access)

Custom MCP tools provide direct access to Unity console logs:

### Available Tools
| Tool | Description |
|------|-------------|
| `mcp__unity__log_tail` | Last N lines from client logs |
| `mcp__unity__log_errors` | Grouped errors from client |
| `mcp__unity__log_search` | Pattern search in client logs |
| `mcp__unity-headless__log_tail` | Last N lines from server logs |
| `mcp__unity-headless__log_errors` | Grouped errors from server |
| `mcp__unity-headless__log_search` | Pattern search in server logs |

### After Playtests
When user mentions testing or returns from a playtest:
1. Check `log_errors` on both client and server
2. Use `log_tail` to see recent activity
3. Search specific patterns with `log_search`

### Log Location
- `/tmp/aum/client_*.log` - Client session logs
- `/tmp/aum/server_*.log` - Server session logs
- Auto-rotation keeps last 5 sessions per type
