# Session: Client-Only Tutorial System

**Date:** 2026-01-23
**Focus:** PlayFab-only deployment with client-side tutorial

---

## Overview

Implemented a **client-only tutorial system** that runs entirely without a game server. This enables:
- Tutorial to work with just PlayFab authentication (no WebSocket/game server)
- Local bot AI that mimics server behavior
- Reduced infrastructure costs for tutorial mode

---

## Architecture

### Before (Server-Based Tutorial)
```
Client → WebSocket → Matchmaking Server → Game Server
                                              ↓
                                         Bot spawns on server
                                         Damage calculated on server
                                         Results sent to client
```

### After (Client-Only Tutorial)
```
Client → PlayFab Auth → Load Map_Hell
                            ↓
                    LocalTutorialManager spawns:
                    - Local player (via PlayerManager)
                    - Local bot (with LocalBot AI)
                    - All damage calculated locally
```

---

## New Files Created

### 1. LocalTutorialManager.cs
**Path:** `Assets/Scripts/Managers/LocalTutorialManager.cs`

Core controller for client-only tutorial:
- Spawns local player and bot without server
- Handles tutorial state progression
- Manages bot behavior states (DISABLED, MELEEACTION, SPELLMELEEACTION, FULL)
- Calculates tutorial damage multipliers

Key Methods:
- `InitializeLocalTutorial()` - Coroutine that waits for dependencies and spawns players
- `SpawnLocalPlayer()` - Creates player via PlayerManager.CreateCharacter
- `SpawnLocalBot()` - Creates bot with LocalBot AI component
- `ProcessTutorialState()` - Handles quest state changes (replaces server packets)
- `GetTutorialDamageMultiplier()` - Returns damage multipliers for tutorial

### 2. LocalBot.cs
**Path:** `Assets/Scripts/Bot/LocalBot.cs`

Client-side bot controller:
- 60Hz tick rate matching server
- Processes behavior tree decisions
- Handles movement, melee attacks, spells, shields
- Applies damage to local player when attacking

### 3. LocalBotBT.cs
**Path:** `Assets/Scripts/Bot/LocalBotBT.cs`

Behavior tree for local bot (ported from server):
- `LocalBotIsDead` - Check if bot is dead
- `LocalBotStateEnabled/Melee/Spells` - Check bot state allows actions
- `LocalBotGetTarget` - Targets local player
- `LocalBotTargetInRange` - Distance check
- `LocalBotMoveToTarget` - Movement toward player
- `LocalBotAttack` - Melee attack execution
- `LocalBotCastDefense/Spell` - Spell casting

---

## Modified Files

### TrainingMapConfig.cs
Added redirect to LocalTutorialManager:
```csharp
if (LocalTutorialManager.Instance != null && LocalTutorialManager.Instance.IsTutorialActive)
{
    LocalTutorialManager.Instance.ProcessTutorialState(stateNum, botState, botDamageIncrease);
    return;
}
```

### Tutorial Quest Files
Updated to support LocalBotPlayer:
- `Tutorial6.cs` - Dodge tutorial
- `TutorialBot.cs` - Bot death detection
- `TutorialKillBotAction.cs`
- `TutorialKillTheBotFaith.cs`
- `TutorialKillTheBotKnowledge.cs`
- `TutorialStart.cs`

### GameManager.cs
Skip server packet when in client-only tutorial:
```csharp
bool isClientOnlyTutorial = InterfaceManager.Instance.currentMatchType == MatchType.Tutorial &&
                            LocalTutorialManager.Instance != null &&
                            LocalTutorialManager.Instance.IsTutorialActive;
if (isClientOnlyTutorial)
{
    // Skip SendMatchConfirmState(4) - no server to confirm with
}
```

### TestModeClient.cs
Added tutorial test mode:
- `testTutorialMode` flag
- Sets `MatchType.Tutorial`
- Creates only 1 avatar (player, not bot)
- Skips server connection

### WebSocket Guards
Added guards to prevent WebSocket calls in PlayFab mode:
- `MainMenuPacketManager.cs`
- `FriendsManager.cs`
- `PartyManager.cs`
- `LobbyManager.cs`

### Node.cs (Behavior Tree)
Added `GetRootNode()` method for behavior tree traversal.

---

## How to Test

1. Open Map_Hell scene in Unity
2. Find TestModeClient component
3. Enable `testTutorialMode = true`
4. Press Play
5. Tutorial should start with local player and bot

---

## Known Limitations

### Not Yet Implemented
- **Player → Bot damage** - Bot doesn't take damage from player attacks yet
- Need to add damage detection in LocalTutorialManager.Update()

### Workaround for Testing
The tutorial uses 10x damage multipliers, so adding a simple distance-based damage check will work for all fighting styles.

---

## Next Steps

1. Add player → bot damage handling
2. Test full tutorial flow
3. Android build and deployment
