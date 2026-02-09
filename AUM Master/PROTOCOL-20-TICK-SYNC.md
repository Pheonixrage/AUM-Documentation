# PROTOCOL-20: Tick Synchronization & Match Confirmation

> **Last Updated:** February 9, 2026
> **Affects:** Client (SimulationManager, NetworkManager, GameManager, PreConnectManager, MainEntranceController)
> **Affects:** Server (MatchState, PlayerManager, Packet)
> **Status:** Implemented & tested

---

## 1. Overview

This document covers two major systems added in the February 9, 2026 update:

1. **Dictionary-Based Tick Verification** (Client) — Replaces the destructive queue-drain approach with O(1) lookup, enabling state corrections to fire during PvP matches
2. **Server-Driven Match Confirmation** (Server + Client) — Server coordinates "Match Found" acceptance before map loading, preventing desynchronized match starts

---

## 2. The Tick Verification Problem

### 2.1 Root Cause

The original `VerifySimulation()` in `SimulationManager.cs` used a `ConcurrentQueue<Simulation>` for the local player's simulation history. When the server echoed back a tick number, the client searched the queue:

```csharp
// OLD CODE (BROKEN):
while (simulationList.TryDequeue(out Simulation simulation))
{
    if (simulation.simulationTick == currentTick) { /* verify */ }
    // ALL dequeued sims are DESTROYED even if no match found
}
```

**Problem:** `TryDequeue()` is destructive. If the server's tick wasn't found (common with network latency), the entire queue was drained. This caused:
- `lastACK` stayed at 0 permanently
- `CheckStateMismatch()` was never called — all state corrections were dead code
- Players got stuck in Cast_Spell, Astra_Cast, Spell_Anticipate forever during PvP

### 2.2 Evidence

From test logs (Feb 9, 2026):
```
[DESYNC] VERIFY tick mismatch: looking for tick=32 but got sim.tick=50
[DESYNC] NO matching simulation found for clientTick=50 (queue exhausted)
[DESYNC] VERIFY: historySize=0 lastACK=0  ← lastACK never advances
```

### 2.3 Additional Problem: Tick Rate Mismatch

| Component | Tick Rate | Hz |
|-----------|-----------|-----|
| Server GameManager | `fixedLoopTick = 0.01667f` | 60Hz |
| Server PlayerInput | `clientTickRate = 0.01667f` | 60Hz |
| Client GameManager (OLD) | `clientTickRate = 0.02f` | **50Hz** |
| Client GameManager (NEW) | `clientTickRate = 0.01667f` | 60Hz |

The 50Hz vs 60Hz mismatch caused additional tick drift between client and server.

---

## 3. The Dictionary-Based Solution

### 3.1 Dual Storage Architecture

```
LOCAL PLAYER PATH (verification):
  TickLocalPlayer() → RecordSimulation() → Dictionary<uint, Simulation>
  Server echoes tick → VerifySimulation() → O(1) dictionary lookup

ENEMY PLAYER PATH (interpolation — unchanged):
  ServerSnapshot → AddSimulation() → ConcurrentQueue<Simulation>
  TickEnemyPlayer() → GetNext() → TryDequeue() → Interpolate()
```

The queue is kept for enemy interpolation (ordered, consume-once) while the dictionary enables non-destructive, O(1) lookup by tick number for local player verification.

### 3.2 Key Data Structures

```csharp
// SimulationManager.cs
public ConcurrentQueue<Simulation> simulationList;     // Enemy interpolation (unchanged)
private Dictionary<uint, Simulation> localSimHistory;   // Local player verification (NEW)
private List<uint> localSimTicks;                       // Sorted tick list for pruning (NEW)
private const int MAX_HISTORY_SIZE = 120;               // ~2 seconds at 60Hz
```

### 3.3 RecordSimulation (Local Player)

```csharp
public void RecordSimulation(Simulation simulation)
{
    uint tick = simulation.simulationTick;
    localSimHistory[tick] = simulation;
    localSimTicks.Add(tick);
    // Prune old entries beyond history limit
    while (localSimTicks.Count > MAX_HISTORY_SIZE)
    {
        uint oldTick = localSimTicks[0];
        localSimTicks.RemoveAt(0);
        localSimHistory.Remove(oldTick);
    }
}
```

### 3.4 VerifySimulation Flow (Rewritten)

```
Server echoes tick N in SimulationResult
         │
         ▼
Is tick N <= lastACKTick?  ──yes──▶ Discard (already processed)
         │ no
         ▼
Dictionary lookup: localSimHistory[N]
         │
    ┌────┴────┐
    │         │
  FOUND     NOT FOUND
    │         │
    ▼         ▼
Compare     Still apply state correction!
predicted   (Key fix: don't skip just because
vs server   tick is missing from history)
state &     │
position    ▼
    │       CheckStateMismatch(serverState, clientCurrentState)
    ▼       │
CheckState  ▼
Mismatch    lastACK = N
    │       PruneHistory(N)
    ▼
Position correction
(hysteresis, rate-limited)
    │
    ▼
Resimulate unacknowledged
    │
    ▼
lastACK = N
PruneHistory(N)
```

**Critical difference from old code:** When a tick is NOT found in the dictionary, state corrections still fire. The old queue approach silently returned, leaving the player stuck.

### 3.5 PruneHistory

After acknowledging tick N, all entries with tick <= N are removed:

```csharp
private void PruneHistory(uint acknowledgedTick)
{
    while (localSimTicks.Count > 0 && localSimTicks[0] <= acknowledgedTick)
    {
        localSimHistory.Remove(localSimTicks[0]);
        localSimTicks.RemoveAt(0);
    }
}
```

### 3.6 GetUnacknowledgedSimulations

Used by `NetworkManager.SendKeyDataState()` to read recent inputs for resending:

```csharp
public Simulation[] GetUnacknowledgedSimulations(int maxCount)
{
    // Returns the latest N simulations from the dictionary, ordered by tick
}
```

---

## 4. Tick Rate Fix

### 4.1 Change

```csharp
// GameManager.cs (Client)
// BEFORE:
public static float clientTickRate = 0.02f;     // 50Hz — WRONG
public static float serverTickRate = 0.02f;     // 50Hz — WRONG

// AFTER:
public static float clientTickRate = 0.01667f;  // 60Hz — matches server
public static float serverTickRate = 0.01667f;  // 60Hz — matches server
```

### 4.2 Why This Matters

At 50Hz client vs 60Hz server:
- Client generates ~50 ticks/sec, server expects ~60 ticks/sec
- Server's `PlayerInput` uses `clientTickRate = 0.01667f` for jitter compensation
- Mismatch causes input timing errors and tick drift

---

## 5. Files Modified (Tick Sync)

| File | Repo | Change |
|------|------|--------|
| `SimulationManager.cs` | Client | Dictionary + RecordSimulation + VerifySimulation rewrite |
| `NetworkManager.cs` | Client | SendKeyDataState reads from GetUnacknowledgedSimulations() |
| `PlayerManager.cs` | Client | TickLocalPlayer: AddSimulation → RecordSimulation |
| `GameManager.cs` | Client | clientTickRate: 0.02f → 0.01667f (60Hz) |

---

## 6. Server-Driven Match Confirmation Flow

### 6.1 Problem

In PvP mode, each client independently detected "match found" from AVATARSYNC data changes and loaded Map_Hell on its own. With no synchronization, both clients ran independent matches.

### 6.2 Solution: WAITINGFORCONFIRMATION State

```
Server MatchState Flow (PvP — 2+ humans):

NONE → PREMATCH (waiting for connections)
         │
         ▼ (all humans connected)
WAITINGFORCONFIRMATION
  │  - Broadcast MATCHSTATEINFO(flags=0x01 CONFIRM_REQUIRED)
  │  - Both clients show "MATCH FOUND!" popup
  │  - 12 second timeout
  │
  ├─ All accept → PLAYER_READY(0) from each
  │     │
  │     ▼
  │  Broadcast MATCHSTATEINFO(flags=0x02 ALL_ACCEPTED)
  │  → Transition to PREMATCH countdown
  │  → Both clients load Map_Hell simultaneously
  │
  └─ Any decline / timeout
        │
        ▼
     Broadcast MATCHSTATEINFO(flags=0x04 MATCH_CANCELLED)
     → All clients return to menu
     → Server shuts down
```

For solo/bot matches (1 human), the WAITINGFORCONFIRMATION phase is skipped entirely.

### 6.3 PLAYER_READY State Values

| readyState | Meaning | When Sent |
|-----------|---------|-----------|
| 0 | `match_accepted` | Client accepted match confirmation popup |
| 1 | `avatars_loaded` | Client finished loading character models |
| 2 | `match_ready` | Client ready for MATCHRUNNING |

State 0 is tracked separately via `HashSet<uint> matchAcceptedPlayers` because the existing `playerReadyStates` dictionary uses an "only upgrade" check (`readyState > currentState`), and 0 > 0 would fail.

### 6.4 MatchStateInfo Flags Field

Added `flags` byte to existing `MatchStateInfo` packet:

| Flag | Value | Meaning |
|------|-------|---------|
| CONFIRM_REQUIRED | 0x01 | Show accept/decline popup on all clients |
| ALL_ACCEPTED | 0x02 | All players accepted — load map now |
| MATCH_CANCELLED | 0x04 | Someone declined or timeout — return to menu |
| (none) | 0x00 | Default — no confirmation (solo/bot mode) |

### 6.5 Bot Fallback Timeout

If a human player doesn't connect within 10 seconds during PREMATCH, their slot is automatically converted to a bot:

```
PREMATCH wait:
  - Start 10s timer when first human connects
  - If second human doesn't connect by timeout:
    → Convert missing slot to bot
    → Broadcast updated AVATARSYNC
    → Skip WAITINGFORCONFIRMATION (now solo/bot match)
    → Proceed with PREMATCH countdown
```

---

## 7. Files Modified (Match Confirmation)

| File | Repo | Change |
|------|------|--------|
| `MatchState.cs` | Server | WAITINGFORCONFIRMATION state, flags, bot fallback |
| `PlayerManager.cs` | Server | matchAcceptedPlayers HashSet, AllHumansAccepted() |
| `Packet.cs` | Server | flags field in MatchStateInfo |
| `Packet.cs` | Client | flags field in MatchStateInfo |
| `PreConnectManager.cs` | Client | Handle MATCHSTATEINFO flags, send PLAYER_READY(0) |
| `MainEntranceController.cs` | Client | Server-driven map loading, multi-mode match flow |
| `MatchFoundPopup.cs` | Client | Accept/decline UI with "Waiting..." state |

---

## 8. Server Debug System (Also Added)

### 8.1 Debug Flags

```csharp
// Server GameManager.cs
public static bool DEBUG_ROLLBACK = true;
public static bool DEBUG_MATCH_STATE = true;
public static bool DEBUG_PLAYER_INIT = true;
public static bool DEBUG_COMBAT = true;
public static bool DEBUG_VERBOSE = false;

// Server PlayerBase.cs
public static bool DEBUG_DAMAGE = true;
public static bool DEBUG_DAMAGE_DETAIL = false;
public static bool DEBUG_DEATH = true;
```

### 8.2 Combat Debug Logging

- **Range checks:** Null-safe with distance/angle logging on miss
- **Damage events:** Full trace (attacker, target, amount, type)
- **Rollback:** Accept/reject with tick diff and buffer size
- **DESYNC diagnostic:** All player positions logged every 50 server ticks

### 8.3 AVATARUPLOAD Character Reinitialization

When the server receives AVATARUPLOAD with a different fighting style than the placeholder, it now:
1. Detects the style change
2. Rebuilds `playerStats` with correct FighterAttributes
3. Reinitializes the character model (calls `Player.Reinitialize()`)

This fixes a bug where a MantraMuktha player would get MukthaMuktha's melee range on the server.

---

## 9. Backward Compatibility

| Feature | Solo/Bot Mode | PvP Mode |
|---------|---------------|----------|
| `flags` byte | Always 0x00 — no change | Used for confirmation flow |
| PLAYER_READY(0) | Never sent | Sent on match accept |
| WAITINGFORCONFIRMATION | Skipped | 12s confirmation phase |
| Dictionary verification | Works identically | Works identically |
| 60Hz tick rate | Matches server | Matches server |
| Bot fallback | N/A (already has bot) | Converts missing humans after 10s |

---

## 10. Testing Checklist

### Tick Verification
- [ ] `lastACK` advances beyond 0 during PvP match
- [ ] `CheckStateMismatch` fires when states differ (check for `"forcing server state"` logs)
- [ ] Cast_Spell / Astra_Cast / Spell_Anticipate no longer get stuck permanently
- [ ] Enemy player interpolation still smooth (queue path unchanged)
- [ ] Position corrections work with hysteresis (no oscillation)

### Match Confirmation
- [ ] Both clients show popup simultaneously
- [ ] Accept → "Waiting for opponent..." state
- [ ] Both accept → both load Map_Hell together
- [ ] One declines → both return to menu
- [ ] Timeout (12s) → both return to menu
- [ ] Solo/bot mode → no popup, direct PREMATCH

### Tick Rate
- [ ] Client diagnostic logs show `historySize` staying reasonable (~3-10)
- [ ] No `"tick not in history"` spam (occasional is OK)
- [ ] Combat feels responsive (state corrections within 1-2 ticks)

---

*This document covers the February 9, 2026 tick synchronization fix and match confirmation flow.*
*See [PROTOCOL-3-UDP-PACKETS.md](PROTOCOL-3-UDP-PACKETS.md) for updated MatchStateInfo packet structure.*
