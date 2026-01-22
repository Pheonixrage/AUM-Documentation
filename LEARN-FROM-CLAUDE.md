# Learn From Claude - AUM Project Context

This document captures key learnings, patterns, and context for Claude to understand when working on AUM.

---

## Project Overview

**AUM** is a multiplayer fighting game built in Unity with:
- **Client**: `AUM-The-Epic` / `dll test windows deply` (Unity 6.2)
- **Server**: `AUM-Headless` / `AUM-Server` (Unity headless server)
- **Backend**: PlayFab (auth, data sync, matchmaking) + Hetzner (game servers)

---

## Architecture Patterns

### 1. Server-Authoritative Combat
- Client sends `PLAYERINPUT` packets (movement, button presses)
- Server calculates damage, positions, states
- Server sends `WORLDSNAPSHOT` with results
- Client interpolates/predicts based on server data

### 2. Client Prediction + Rollback
- Client runs simulation locally (SimulationManager)
- Server verifies and corrects if mismatch
- Rollback buffer: 150 ticks for correction window
- Key file: `ControllerBase.cs` (CheckStateMismatch)

### 3. Bot System
- Server: `BotManager` + `BotBT` (behavior tree)
- Client: `LocalBot` + `LocalBotBT` (for client-only tutorial)
- Bot states: DISABLED, MELEEACTION, SPELLMELEEACTION, FULL

### 4. Tutorial System
- Quest-based: `QuestManager` runs quests sequentially
- Each quest: `Start()` → `Condition()` → `End()`
- `TrainingMapConfig.SendTutorialData()` communicates state
- Client-only mode: `LocalTutorialManager` handles locally

---

## User's Communication Style

The user prefers:
- **Direct answers** - No fluff, get to the point
- **Confirm before acting** - Ask before major changes
- **Summaries** - Brief explanations of what will be done
- **Tables** - For comparing options or showing status
- **Code examples** - When explaining what will be added

Common phrases and what they mean:
- "just do it" → Proceed without asking more questions
- "checkout and push" → Commit current changes to git
- "is this 100% possible" → Check if solution is complete
- "what all do you need" → List everything required

---

## Key Files Reference

### Client Core
| File | Purpose |
|------|---------|
| `GameManager.cs` | Match state, avatar instantiation |
| `PlayerManager.cs` | Player spawning, NetworkPlayers dict |
| `NetworkManager.cs` | UDP connection, packet handling |
| `InterfaceManager.cs` | UI state, match data, session info |
| `TestModeClient.cs` | Test mode setup, tutorial toggle |

### Combat
| File | Purpose |
|------|---------|
| `ControllerBase.cs` | Character controller, state mismatch |
| `StateManager.cs` | FSM states (Idle, Melee, Cast_Spell, etc.) |
| `SimulationManager.cs` | Client prediction, rollback |
| `InputManager.cs` | Button events, input handling |

### Tutorial
| File | Purpose |
|------|---------|
| `LocalTutorialManager.cs` | Client-only tutorial controller |
| `LocalBot.cs` | Client-side bot AI |
| `LocalBotBT.cs` | Bot behavior tree |
| `TrainingMapConfig.cs` | Tutorial state communication |
| `Tutorial*.cs` | Individual tutorial quests |

### Network
| File | Purpose |
|------|---------|
| `WebSocketConnector.cs` | Main menu WebSocket connection |
| `Packet.cs` | Packet type enums and structs |
| `InGamePacketManager.cs` | In-game packet handling |

---

## Common Tasks

### Testing Tutorial Mode
1. Open Map_Hell scene
2. Find TestModeClient on "TestMode" object
3. Enable `testTutorialMode = true`
4. Press Play

### Testing 1v1 Mode
1. Start server: `AUM-Server` with `useTestMode = true`
2. Open Map_Hell on client
3. Disable `testTutorialMode`
4. Press Play (connects to localhost:7777)

### Committing Changes
```bash
cd "D:\dll test windows deply"
git add <files>
git commit -m "message"
git push origin legacy-working-oct29
```

---

## Important Commits

- **LEGENDARY**: `221c567ad` - Stable gameplay reference
- **Rollback buffer fix**: Increased 20→150 in server GameManager
- **CheckStateMismatch**: Keep LEGENDARY version in ControllerBase

---

## Current Branch Strategy

- `legacy-working-oct29` - Main working branch
- `playfab-integration` - PlayFab integration work
- `Unity_6.2` - Unity 6.2 upgrade work

---

## PlayFab Integration Status

| Feature | Status |
|---------|--------|
| Authentication | ✅ Working |
| Data Sync | ✅ Working |
| Matchmaking | ✅ Working |
| Tutorial (client-only) | 🟡 90% - needs player→bot damage |
| Training Mode | ⏳ Needs testing |
| 1v1/2v2 | ⏳ Needs testing |

---

## Known Issues / Gaps

1. **Player → Bot damage in tutorial** - Not implemented yet
   - Need to add damage detection in LocalTutorialManager.Update()
   - Check player attack state + distance to bot

2. **WebSocket dependency** - Some managers still have WebSocket code
   - Guards added but not fully tested

---

## Session Handoff Template

When ending a session, provide:
1. What was completed
2. What files were changed
3. What's still pending
4. Any blockers or issues
5. Git status (committed or not)
