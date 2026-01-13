# Character Jitter Fix Plan

**Date:** January 12, 2026
**Status:** Phase 4 - Bot Flickering/Rotation Fix Applied

---

## Problem Statement

Visual jitter affecting:
1. Local player character during movement
2. Bot/enemy flickering (new symptom after attempted fixes)

Symptoms: Constant jitter while moving, worse when changing direction, correlates with network lag.

---

## Root Cause Analysis

### Phase 1: Investigation (Partial Fix)

**Initial Hypothesis (WRONG):** Reconciliation tolerance too tight (0.7m)
- Increasing tolerance to 1.0m made jitter WORSE
- Bot started flickering (wasn't before)

**First Finding (Fixed but incomplete):**

`GameManager.cs` Update() was calling `TickEnemyPlayer()` **TWICE per frame**:

```csharp
// Line 1449
PlayerManager.TickEnemyPlayer();  // First call

// Line 1457
TimeEx.deltaTime = Time.deltaTime;  // Value changes here

// Line 1460
PlayerManager.TickEnemyPlayer();  // DUPLICATE - caused flickering!
```

**Fix Applied:** Removed duplicate call, reordered TimeEx assignment.

**Result:** Bot STILL flickering after fix.

---

### Phase 2: Deeper Investigation (Actual Root Cause)

**The REAL Root Cause:**

In `SimulationManager.Interpolate()`, when `lastSimulation == null`:

```csharp
if(lastSimulation == null)
{
    complete = true;  // <-- THIS CAUSED FLICKERING!
    // ... extrapolation code ...
    return ...;
}
```

**Why This Caused Flickering:**

1. When queue runs low or at startup, `lastSimulation` becomes null
2. `Interpolate()` sets `complete = true` immediately (no interpolation done)
3. Next frame, `GetNext()` sees `complete=true` and advances to next simulation
4. `lastSimulation` stays null (copied from old activeSimulation which was just moved)
5. Cycle repeats: rapid advance → null lastSim → immediate complete → advance again
6. Bot position jumps between simulation positions without smooth interpolation

**The Flow:**
```
Frame N: lastSim=null → complete=true → return extrapolated pos
Frame N+1: GetNext advances → lastSim=null → complete=true → return extrapolated pos
Frame N+2: Same pattern...
```

Bot cycles through simulations at ~60Hz (frame rate) instead of 50Hz (server tick rate).

---

## Fix Applied (Phase 2)

**File:** `/AUM-The-Epic/Assets/Scripts/Managers/SimulationManager.cs`

**Changes:**

1. **`Interpolate()`**: Do NOT set `complete=true` when `lastSimulation` is null
   - Hold position and wait for queue to have enough data
   - Continue extrapolating smoothly without advancing

2. **`GetNext()`**: Add "priming" logic when `lastSimulation` is null
   - If we have `activeSimulation` and queue has data, populate both endpoints
   - This ensures we have two points to interpolate between

```csharp
// NEW: Prime interpolation when lastSimulation is null but we have data
if (lastSimulation == null && activeSimulation != null && simulationList.Count > 0)
{
    lastSimulation = activeSimulation;
    activeSimulation = GetNextQueueSimulation();
    complete = false;
    interpolateTime = 0;
    return activeSimulation;
}
```

**Expected Result:**
- Bot only advances simulations when interpolation is complete (interpolateTime >= 0.9)
- When queue is low, bot holds position smoothly instead of rapidly cycling
- Smooth interpolation between simulation positions

**Result:** Bot flickering FIXED ✅

---

### Phase 3: Bot Attack Frenzy Fix

**New Symptom After Phase 2:**
- Bot flickering stopped, but bot attacks multiple times in rapid succession
- Server logs showed MELEE commits every ~600ms (30 ticks at 50Hz)

**Root Cause:**
`BotDecisionManager.ACTION_COMMIT_DURATION = 30` (0.5s) only prevents decision thrashing DURING animation, but there's no cooldown BETWEEN attacks:

```csharp
// Flow before fix:
Frame N: In melee range → Commit to MELEE for 30 ticks
Frame N+30: Commitment expires → Re-evaluate → Still in range → Commit to MELEE again
Frame N+60: Repeat...
```

Bot was attacking every 0.5s because the commitment duration ~= animation duration.

**Additional Issue:**
No check for `_state.IsAttacking` meant bot could decide to attack while mid-animation.

**Fix Applied:**

**File:** `/AUM-Headless/Assets/Scripts/Bots/Bot/Core/BotDecisionManager.cs`

**Changes:**

1. **Added melee cooldown tracking:**
   ```csharp
   private uint _lastMeleeEndTick;
   private const uint MELEE_COOLDOWN_MIN = 45;  // 0.75 seconds
   private const uint MELEE_COOLDOWN_MAX = 90;  // 1.5 seconds
   private uint _currentMeleeCooldown;
   ```

2. **Added `IsMeleeOnCooldown(currentTick)` method:**
   - Returns true if not enough time passed since last melee ended
   - First attack has no cooldown

3. **Added `EndMeleeCommitment(currentTick)` method:**
   - Called when melee commitment expires
   - Randomizes next cooldown based on personality aggression

4. **Modified `IsCommittedToCombatAction`:**
   - Now calls `EndMeleeCommitment` when melee commitment ends

5. **Modified `ShouldMelee`:**
   - Added check for `_state.IsAttacking` (don't melee mid-animation)
   - Added check for `IsMeleeOnCooldown` (enforce delay between attacks)

**Expected Result:**
- **Before:** Bot attacks every ~0.5 seconds
- **After:** Bot attacks every ~1.25-2.0 seconds (commit + cooldown)
- More natural, human-like attack pacing

---

### Phase 4: Bot Flickering + Rotation Fix

**New Symptoms After Phase 3:**
- Bot flickering returned
- Constant instant rotating in same place
- Bot attacking in opposite direction to player

**Root Cause:**

Bot was walking INTO the player (overlapping at 0.04m distance). At such close range, tiny position changes caused MASSIVE angle changes in `GetAngleToTarget()`:

```
Distance 0.04m → 0.17m (0.13m change)
At this range, that's potentially 90+ degree angle flip!
```

**Why Bot Walked Into Player:**
`ApplyMovement()` had NO distance check - it blindly set `joyY=1` (forward) regardless of proximity:

```csharp
// BEFORE: Always moved forward toward target
if (towards)
{
    joyY = 1;  // Always forward - even when 0.04m away!
}
```

**Fixes Applied:**

**File:** `/AUM-Headless/Assets/Scripts/Bots/Bot/Core/BotExecutor.cs`

**Changes:**

1. **Added distance check to `ApplyMovement()`:**
   ```csharp
   private const float STOP_DISTANCE = 2.0f;  // Stop when this close

   // Calculate distance
   float distanceToTarget = Vector3.Distance(...);

   if (distanceToTarget <= STOP_DISTANCE)
   {
       joyY = 0;  // Stop moving
       joyX = 0;
   }
   ```

2. **Added angle smoothing to `GetAngleToTarget()`:**
   - When < 1m away, maintain current facing (don't recalculate)
   - Ignore angle changes < 5°
   - Limit rotation speed to 15°/tick
   - Track `_lastCalculatedAngle` for smoothing

**Expected Result:**
- Bot stops at ~2m from target (comfortable melee range)
- No more overlapping positions
- Stable facing direction during combat
- Smooth rotation transitions

---

## Architecture Recommendations (Future)

### Short Term
- Test the Phase 2 fix thoroughly
- Monitor `[INTERP-DIAG]` logs for queue health

### Medium Term
If local player jitter persists (separate issue):

1. **Increase VerifySimulation tolerance** (carefully)
   - Current: 0.7m
   - Try: 0.8-0.9m (not 1.0m which made it worse)

2. **Add continuous blending** instead of discrete corrections
   - Blend 5-10% toward server position each frame
   - Eliminates visible correction events

### Long Term (Architecture)
- Replace global `TimeEx.deltaTime` with explicit parameters
- Separate tick-based logic from frame-based visual updates
- Use Unity's `Time.fixedDeltaTime` for physics, `Time.deltaTime` for visuals

---

## Testing Checklist

- [ ] Local player movement smooth (no micro-stutters)
- [ ] Bot movement smooth (no flickering)
- [ ] Bot attacks at reasonable pace (1-2 sec between attacks)
- [ ] Bot maintains ~2m distance from player (doesn't overlap)
- [ ] Bot faces player correctly during combat
- [ ] Direction changes feel responsive
- [ ] No rubberbanding during network lag
- [ ] Dodge/abilities don't cause snapback
- [ ] `[INTERP-DIAG]` shows stable queue size (3-6)
- [ ] `lastSim` shows SET (not NULL) during normal play
- [ ] `[BotDecision]` logs show melee cooldown being applied
- [ ] `AttackCheck` logs show distance > 2m during combat

---

## Related Files

| File | Changes |
|------|---------|
| GameManager.cs | Removed duplicate TickEnemyPlayer, reordered TimeEx assignment |
| SimulationManager.cs | **Phase 2:** Fixed complete=true when lastSim null, added GetNext priming, null safety |
| BotStateReader.cs | Fixed melee range for ranged characters |
| BotDecisionManager.cs | **Phase 3:** Added melee cooldown system, IsAttacking check |
| BotExecutor.cs | **Phase 4:** Stop distance check in ApplyMovement, angle smoothing in GetAngleToTarget |
| PlayerManager.cs | Dodge now uses Authority.ConsumeStamina, diagnostic logging |
| AssetManager.cs | Added null checks for assetPrefab |

---

## Diagnostic Output

The `[INTERP-DIAG]` log shows once per second:
```
[INTERP-DIAG] Calls/sec=60 | Queue=5 | lastSim=SET | activeSim=SET | interpTime=0.85 | complete=false
```

**Healthy values:**
- Calls/sec: ~60 (matches frame rate)
- Queue: 3-6 (deadband range)
- lastSim: SET (not NULL during normal play)
- activeSim: SET
- interpTime: 0.0-1.0 (gradually increasing)
- complete: alternates between true/false

**Problem indicators:**
- lastSim=NULL frequently → queue underrun issue
- Queue=0 frequently → server not sending fast enough
- Queue>10 → client falling behind
