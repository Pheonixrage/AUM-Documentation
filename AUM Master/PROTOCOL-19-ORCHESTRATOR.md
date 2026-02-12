# AUM Protocol - Orchestrator (Avatar-First Architecture)

**Version:** 1.0
**Date:** February 7, 2026
**Source:** `orchestrator/orchestrator.py` (Hetzner: 65.109.133.129)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Avatar-First Architecture](#2-avatar-first-architecture)
3. [API Endpoints](#3-api-endpoints)
4. [Data Structures](#4-data-structures)
5. [Edge Case Handling](#5-edge-case-handling)
6. [Client Integration](#6-client-integration)
7. [Connection Modes](#7-connection-modes)

---

## 1. Overview

### 1.1 Purpose

The Orchestrator is a Python Flask service that:
- Allocates game servers for PlayFab matchmaking
- **Collects full avatar data from ALL clients before spawning server**
- Manages server port pool (7850-7909)
- Handles match cancellation and timeout cleanup

### 1.2 Why Avatar-First?

**Problem with Old Architecture:**
```
OLD FLOW (BROKEN):
═══════════════════════════════════════════════════════════════════════════
Player A sends /allocate → Orchestrator spawns server IMMEDIATELY
                           Server has placeholder for Player B (Amuktha/Brahma)
Player B sends /allocate → TOO LATE! Server already created with wrong data

RESULT: MantraMuktha player created as Amuktha → No Aiming state → Attacks fail
```

**New Avatar-First Architecture:**
```
NEW FLOW (FIXED):
═══════════════════════════════════════════════════════════════════════════
Player A sends /allocate → Orchestrator stores data, returns "WAITING"
Player B sends /allocate → Orchestrator has ALL data, spawns server NOW

RESULT: Server has complete, correct avatar data for both players
```

### 1.3 Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────┐       ┌──────────────────┐       ┌─────────────────┐ │
│  │    Client A   │       │                  │       │   Game Server   │ │
│  │   (PC/Mobile) │──────►│   ORCHESTRATOR   │──────►│     Pool        │ │
│  └───────────────┘       │                  │       │  (Ports 7850+)  │ │
│                          │  Flask :8080     │       └─────────────────┘ │
│  ┌───────────────┐       │                  │                           │
│  │    Client B   │──────►│  - /allocate     │       ┌─────────────────┐ │
│  │   (PC/Mobile) │       │  - /match-status │       │  Avatar Config  │ │
│  └───────────────┘       │  - /cancel       │──────►│  JSON Files     │ │
│                          └──────────────────┘       └─────────────────┘ │
│                                                                          │
│  Hetzner: 65.109.133.129                                                │
│  Orchestrator: :8080                                                    │
│  Game Servers: :7850-7909                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Avatar-First Architecture

### 2.1 Collection Phase

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COLLECTION PHASE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PLAYER A (PC)              ORCHESTRATOR              PLAYER B (Mobile) │
│                                                                          │
│  PlayFab match ────────────────────────────────────► PlayFab match      │
│  matchId: "abc"                                       matchId: "abc"     │
│                                                                          │
│  POST /allocate ───────────►┐                                           │
│  {                          │ pendingMatches["abc"] = {                 │
│    matchId: "abc",          │   expectedPlayers: 2,                     │
│    playerId: "A",           │   receivedPlayers: {                      │
│    avatar: {                │     "A": { MantraMuktha, Vishnu }         │
│      style: MantraMuktha,   │   },                                      │
│      god: Vishnu,           │   status: "COLLECTING"                    │
│      elementals: [0,1,2,4]  │ }                                         │
│    }                        │                                           │
│  }                          │                       POST /allocate ─────┤
│                             │                       {                   │
│  ◄──────────────────────────┤                         matchId: "abc",   │
│  Response: {                │                         playerId: "B",    │
│    status: "WAITING",       │                         avatar: { ... }   │
│    playersReady: 1,         │                       }                   │
│    playersNeeded: 2         │                                           │
│  }                          │ ALL PLAYERS READY!                        │
│                             │ → spawn_server()                          │
│                             │ → write avatar_config.json                │
│                             │                       ◄───────────────────┤
│                             │                       Response: {         │
│                             │                         status: "READY",  │
│                             │                         ip: "65.109...",  │
│                             │                         port: 7850        │
│  GET /match-status/abc ────►│                       }                   │
│  ◄──────────────────────────┤                                           │
│  Response: {                │                                           │
│    status: "READY",         │                                           │
│    ip: "65.109.133.129",    │                                           │
│    port: 7850               │                                           │
│  }                          │                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 State Machine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR MATCH STATES                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                              ┌─────────────┐                            │
│                              │   (start)   │                            │
│                              └──────┬──────┘                            │
│                                     │                                    │
│                         First /allocate received                        │
│                                     ▼                                    │
│                         ┌───────────────────┐                           │
│                         │    COLLECTING     │◄──────┐                   │
│                         │                   │       │                   │
│                         │ • Waiting for all │       │ More players      │
│                         │   players' data   │       │ join              │
│                         │ • Timer: 60s      │───────┘                   │
│                         └────────┬──────────┘                           │
│                                  │                                      │
│             ┌────────────────────┼────────────────────┐                 │
│             │                    │                    │                 │
│      All players     Timer expires        All players cancel            │
│         ready        (not all joined)                 │                 │
│             │                    │                    │                 │
│             ▼                    ▼                    ▼                 │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │    SPAWNING     │  │     EXPIRED     │  │    CANCELLED    │        │
│   │                 │  │                 │  │                 │        │
│   │ • Starting      │  │ • Timeout       │  │ • All players   │        │
│   │   server        │  │ • Cleanup       │  │   left          │        │
│   │ • Writing       │  │   resources     │  │ • Cleanup       │        │
│   │   config        │  │                 │  │                 │        │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│            │                    │                    │                 │
│     ┌──────┴──────┐             │                    │                 │
│     │             │             │                    │                 │
│  Success       Failure          │                    │                 │
│     │             │             │                    │                 │
│     ▼             ▼             ▼                    ▼                 │
│  ┌──────┐   ┌───────────┐   ┌───────────────────────────┐              │
│  │READY │   │SPAWN_FAIL │   │         CLEANED           │              │
│  │      │   │           │   │                           │              │
│  │• IP  │   │• Error    │   │ • Match removed from      │              │
│  │• Port│   │  message  │   │   pendingMatches          │              │
│  └──────┘   └───────────┘   └───────────────────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. API Endpoints

### 3.1 POST /allocate

**Purpose:** Register player's avatar data for a match

**Request:**
```json
{
    "matchId": "playfab-match-abc123",
    "matchType": "SOLO_1V1",
    "playerId": "player-entity-id",
    "minPlayers": 2,
    "players": [
        {
            "playFabId": "ABC123",
            "teamId": "Team1",
            "nickName": "ProPlayer",
            "fightingStyle": 1,
            "godSelected": 1,
            "elementalSelected": [0, 1, 2, 4],
            "wearItems": [0, 0, 0, 0, 0, 0],
            "bronze": 1000,
            "guna": 50,
            "lives": 3,
            "isBot": false
        }
    ]
}
```

**Response (waiting for other players):**
```json
{
    "success": true,
    "matchId": "playfab-match-abc123",
    "status": "waiting",
    "playersReady": 1,
    "playersNeeded": 2,
    "message": "Waiting for 1 more player(s)"
}
```

**Response (all players ready):**
```json
{
    "success": true,
    "ip": "65.109.133.129",
    "port": 7850,
    "matchId": "playfab-match-abc123",
    "status": "ready"
}
```

### 3.2 GET /match-status/{matchId}

**Purpose:** Poll for match status (used after initial /allocate returns "waiting")

**Response (collecting):**
```json
{
    "success": true,
    "status": "COLLECTING",
    "playersReady": 1,
    "playersNeeded": 2,
    "message": "Waiting for 1 more player(s)"
}
```

**Response (ready):**
```json
{
    "success": true,
    "status": "READY",
    "ip": "65.109.133.129",
    "port": 7850,
    "matchId": "playfab-match-abc123"
}
```

**Response (expired/cancelled):**
```json
{
    "success": false,
    "status": "EXPIRED",
    "reason": "TIMEOUT",
    "message": "Match not found - may have expired or been cancelled"
}
```

### 3.3 POST /cancel-allocation

**Purpose:** Remove player from pending match (when user cancels matchmaking)

**Request:**
```json
{
    "matchId": "playfab-match-abc123",
    "playerId": "player-entity-id"
}
```

**Response:**
```json
{
    "success": true,
    "status": "CANCELLED",
    "message": "Removed from match, 1 player(s) remaining",
    "matchCancelled": false
}
```

**Response (last player cancels):**
```json
{
    "success": true,
    "status": "CANCELLED",
    "message": "Match cancelled - no players remaining",
    "matchCancelled": true
}
```

### 3.4 Other Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (no auth) |
| `/status` | GET | Server pool status (no auth) |
| `/release` | POST | Release server port |
| `/heartbeat` | POST | Server keepalive |

---

## 4. Data Structures

### 4.1 Pending Match

```python
@dataclass
class PendingMatch:
    matchId: str
    match_type: str
    min_players: int
    players_data: List[dict]      # Full avatar data per player
    players_seen: Set[str]        # playFabIds that have allocated
    created_at: datetime          # For timeout cleanup
```

### 4.2 Avatar Config JSON

Written to `/root/orchestrator/logs/matches/{matchId}.json`:

```json
{
    "matchId": "playfab-match-abc123",
    "matchType": "SOLO_1V1",
    "avatarCount": 2,
    "avatars": [
        {
            "UniqueID": 1,
            "playFabId": "ABC123",
            "teamID": 1,
            "nickName": "PlayerA",
            "fightingStyle": 1,
            "fighterClass": 0,
            "godSelected": 1,
            "elementalSelected": [0, 1, 2, 4],
            "weaponVariant": 0,
            "wearItems": [0, 0, 0, 0, 0, 0],
            "bronze": 1000,
            "lives": 3,
            "guna": 50,
            "isBot": false
        },
        {
            "UniqueID": 2,
            "playFabId": "DEF456",
            "teamID": 2,
            "nickName": "PlayerB",
            "fightingStyle": 0,
            "fighterClass": 0,
            "godSelected": 2,
            "elementalSelected": [0, 1, 0, 0],
            "weaponVariant": 0,
            "wearItems": [0, 0, 0, 0, 0, 0],
            "bronze": 500,
            "lives": 3,
            "guna": 30,
            "isBot": false
        }
    ]
}
```

---

## 5. Edge Case Handling

### 5.1 Player Cancels While Waiting

```
PLAYER A                   ORCHESTRATOR              PLAYER B

POST /allocate ───────────►
◄── { status: "WAITING" }  pendingMatches["abc"] = { A }

[User taps CANCEL]

DELETE /cancel ───────────►
                           Remove A from match
                           CHECK: 0 players left
                           DELETE match entirely
◄── { matchCancelled: true }

[Re-queue in PlayFab]                  POST /allocate ───

                           Match doesn't exist!
                           ◄── { status: "EXPIRED" }

                           [Re-queue in PlayFab]
```

### 5.2 Duplicate /allocate Calls (Idempotent)

```
PLAYER A                   ORCHESTRATOR

POST /allocate ───────────►
◄── { status: "WAITING" }  pendingMatches["abc"].players["A"] = data

[Network retry]

POST /allocate ───────────►
                           CHECK: players["A"] exists!
                           ACTION: Update data (don't add twice)
                           DO NOT increment player count
◄── { status: "WAITING",
      playersReady: 1 }    Same response - idempotent
```

### 5.3 Timeout - One Player Never Sends Data

```
PLAYER A                   ORCHESTRATOR              PLAYER B
                                                     [App crashed]
POST /allocate ───────────►
◄── { status: "WAITING" }  createdAt: T0

[Polling...]
GET /match-status ────────►
◄── { status: "COLLECTING" }

[60 seconds pass...]
                           BACKGROUND CLEANUP:
                           now - createdAt > 60s
                           match.status = "EXPIRED"
                           DELETE match

GET /match-status ────────►
◄── { status: "EXPIRED",
      reason: "TIMEOUT" }

[Show "Opponent left"]
```

### 5.4 Race Condition - Both Players Call Simultaneously

```python
# Thread-safe with lock per matchId
with server_manager.lock:
    if match_id in self.pending_matches:
        # Update existing match atomically
        pending["players_seen"].add(playfab_id)
        if len(pending["players_seen"]) >= min_players:
            # All players ready - start server
            return self._start_pending_match(...)
```

---

## 6. Client Integration

### 6.1 PlayFabMatchmaker Flow

```csharp
// PlayFabMatchmaker.cs - RequestServerAllocationDirect()

// STEP 1: Build LOCAL player's avatar data ONLY
var localPlayerData = new Dictionary<string, object>
{
    { "playFabId", localEntityId },
    { "teamId", localTeamId },
    { "nickName", localAvatar.nickName },
    { "fightingStyle", (int)localAvatar.fightingStyle },
    { "godSelected", (int)localAvatar.godSelected },
    { "elementalSelected", elementals },
    // ... other fields
};

// STEP 2: Send allocation (orchestrator collects from all clients)
var requestData = new Dictionary<string, object>
{
    { "matchId", matchId },
    { "playerId", localEntityId },
    { "minPlayers", playerIds.Count },
    { "players", new List<object> { localPlayerData } }  // ONLY local player
};

// POST /allocate
yield return SendRequest(orchestratorUrl, requestData);

// STEP 3: If "waiting", poll /match-status
if (status == "waiting")
{
    while (pollAttempt < 30)
    {
        yield return new WaitForSeconds(1f);
        var statusResponse = await GET($"/match-status/{matchId}");

        if (statusResponse.status == "READY")
        {
            ConnectToServer(statusResponse.ip, statusResponse.port);
            break;
        }
    }
}
```

### 6.2 Cancel Match Flow

```csharp
public void CancelMatch()
{
    // Cancel orchestrator allocation
    if (!string.IsNullOrEmpty(pendingMatchId))
    {
        StartCoroutine(SendCancelAllocation(matchId, playerId));
    }

    // Cancel PlayFab ticket
    PlayFabMultiplayerAPI.CancelMatchmakingTicket(...);
}

private IEnumerator SendCancelAllocation(string matchId, string playerId)
{
    var cancelData = new { matchId, playerId };
    yield return POST("/cancel-allocation", cancelData);
}
```

---

## 7. Connection Modes

### 7.1 Mode Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CONNECTION MODES                                   │
├──────────────┬──────────────┬──────────────┬────────────────────────────┤
│   PlayFab    │    Local     │   Hetzner    │   LAN                      │
│  (Production)│   (Testing)  │   (Direct)   │   (Events)                 │
├──────────────┼──────────────┼──────────────┼────────────────────────────┤
│ Matchmaking  │ Instant      │ Instant      │ Instant                    │
│ 3-120s poll  │ allocation   │ allocation   │ allocation                 │
├──────────────┼──────────────┼──────────────┼────────────────────────────┤
│ ORCHESTRATOR │ TestMode     │ ORCHESTRATOR │ TestMode                   │
│ avatar-first │ local bots   │ avatar-first │ manual config              │
├──────────────┼──────────────┼──────────────┼────────────────────────────┤
│ Port: 7850+  │ Port: 6006   │ Port: 7850+  │ Port: 6006                 │
└──────────────┴──────────────┴──────────────┴────────────────────────────┘
```

### 7.2 ServerAllocator Settings

```csharp
public enum ConnectionMode
{
    PlayFab,   // Uses orchestrator, avatar-first collection
    Local,     // Direct to 127.0.0.1:6006, TestModeManager bots
    Hetzner,   // Direct to 65.109.133.129:6006, TestModeManager bots
    LAN        // Direct to custom IP:port, TestModeManager bots
}
```

### 7.3 When Each Mode Uses Orchestrator

| Mode | Uses Orchestrator | Avatar Source |
|------|-------------------|---------------|
| PlayFab | YES | Client → Orchestrator → avatarConfig.json → Server |
| Local | NO | TestModeManager random bots |
| Hetzner | YES (if production build) | Same as PlayFab |
| LAN | NO | TestModeManager configured bots |

---

## Appendix A: Troubleshooting

### A.1 "Mobile player attacks not working"

**Symptom:** MantraMuktha player on mobile can't attack
**Cause:** Server created character as Amuktha (no Aiming state)
**Solution:** Verify avatar-first flow is working:

1. Check client logs for `[Matchmaker] ★ Sending LOCAL player data: ... style=MantraMuktha`
2. Check orchestrator logs for both players' data received
3. Check avatar config JSON has correct fightingStyle for both players

### A.2 "Opponent shows wrong appearance"

**Symptom:** Opponent has default costume/weapon
**Cause:** wearItems not sent in avatar data
**Solution:** Verify client sends full wearItems array in /allocate

### A.3 "Match stuck in WAITING"

**Symptom:** Player A stuck polling, never gets READY
**Cause:** Player B never called /allocate or crashed
**Solution:**
1. Check timeout cleanup is running (60s)
2. Client should show "Opponent left" after 30s poll timeout

---

## Appendix B: API Reference

| Endpoint | Auth | Method | Purpose |
|----------|------|--------|---------|
| `/health` | No | GET | Liveness check |
| `/status` | No | GET | Pool status |
| `/allocate` | Yes | POST | Register player avatar |
| `/match-status/{id}` | Yes | GET | Poll match state |
| `/cancel-allocation` | Yes | POST | Remove player from match |
| `/release` | Yes | POST | Free server port |
| `/heartbeat` | Yes | POST | Server keepalive |

**Auth Header:** `X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8`

---

**Document Info:**
- Created: February 7, 2026
- Part: 19 of Protocol Series
- Related: PROTOCOL-4-MATCHKEEPER.md, PROTOCOL-5-PLAYFAB.md

---

*End of Orchestrator Protocol Document*
