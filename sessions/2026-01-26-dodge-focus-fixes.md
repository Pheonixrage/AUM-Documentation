# Session Log: 2026-01-26 - Dodge, Focus Bar & Aiming State Fixes

## Summary
Fixed dodge going through walls, focus bar sync issues, and critical Aiming state synchronization bug.

## What Was Done

### Dodge Wall Collision Fix (Morning)
- **Root Cause**: Previous comment incorrectly claimed Legacy doesn't check walls - it DOES
- **Fix**: Re-enabled Layer 9 (walls) in `GetDodgePosition()` raycast
- **How it works**: Raycast PRE-CALCULATES safe landing spot before dodge starts, no runtime collision needed
- **Result**: Dodge stops before walls, animation plays smoothly

### Focus Bar High Water Mark Removal (Afternoon)
- **Root Cause**: Client was predicting focus gains, but server validated many as MISS
- **Previous Problem**: High water mark blocked server corrections (server=8, client=18 → blocked)
- **Fix 1**: ServerAuthority.AddFocus() now NO-OP - don't predict focus client-side
- **Fix 2**: SegmentedFillHighlighter simplified - only 2% noise threshold, accepts all server values
- **Result**: Focus bar now shows server-authoritative values

### CRITICAL: Aiming State Mismatch Fix (Afternoon)
- **Root Cause Found**: TickLocalPlayer creates NEW Simulation object each tick
- **Bug**: OnAimEnter sets `meleeAbility = AIMING` but only on first tick's simulation
- **Effect**: Subsequent ticks had `meleeAbility = NONE`, server never received AIMING signal
- **Logs showed**: 39+ state mismatches `Expected:Aiming Actual:Idle` during playtest
- **Fix**: Added `simulation.meleeAbility = AIMING` to OnAimUpdate() for ALL ranged characters
  - MantraMukthaPlayer.cs
  - YantramukthaPlayer.cs
  - PaniMukthaPlayer.cs

### StateManager Crash Guards (Morning)
- Added `HasAnimationData()` guard for states without animation data
- Prevents crashes on Idle, Stun, Water_Pushback, Special, Special_Anticipate states

### ControllerBase Fixes (Morning)
- Attack re-entry guard prevents duplicate attacks from reconciliation
- Reverted server-controlled state Update methods to empty (they crashed due to missing animation data)

## Key Decisions
- Legacy's approach is correct: raycast BEFORE dodge, not collision DURING dodge
- Server controls state transitions for Special, Stun, Pushback - client shouldn't call IsAnimationDone()
- Focus is now FULLY server-authoritative - no client prediction
- Simulation signals (meleeAbility, etc.) must be set EVERY tick, not just on state Enter

## Technical Deep Dive: Aiming State Bug

The previous "fix" on Jan 24-25 moved `meleeAbility = AIMING` from OnAimUpdate to OnAimEnter because of a perceived "race condition". But this introduced a worse bug:

```
TickLocalPlayer Flow:
1. new Simulation() ← Creates fresh simulation, all fields NONE
2. character.simulation = simulation ← Assigns to character
3. ProcessPlayer() ← Runs state machine
   └── OnAimEnter() sets simulation.meleeAbility = AIMING
4. AddSimulation(simulation) ← Queued for sending

NEXT TICK:
1. new Simulation() ← CREATES NEW OBJECT, AIMING is lost!
2. OnAimUpdate() runs but meleeAbility NOT set
3. Server receives meleeAbility = NONE
4. Server thinks player is in Idle, not Aiming
```

**Fix**: Set `simulation.meleeAbility = AIMING` in OnAimUpdate every tick.

## Files Changed
- `Assets/Scripts/Player/DodgeController.cs` - Wall raycast fix
- `Assets/Scripts/StateMachine/StateManager.cs` - HasAnimationData() guard
- `Assets/Scripts/Player/ControllerBase.cs` - Attack guard, empty Update methods
- `Assets/UI/New UI/Scripts/SegmentedFillHighlighter.cs` - Simplified noise threshold
- `Assets/Scripts/CombatAuthority/Authorities/ServerAuthority.cs` - AddFocus NO-OP
- `Assets/Characters/MantraMuktha/Scripts/MantraMukthaPlayer.cs` - OnAimUpdate fix
- `Assets/Characters/Yantramuktha/Scripts/YantramukthaPlayer.cs` - OnAimUpdate fix
- `Assets/Characters/PaniMuktha/Scripts/PaniMukthaPlayer.cs` - OnAimUpdate fix

## Commits
- `fe11ce2c` (AUM-The-Epic): Fix dodge wall collision, focus bar jitter, animation crash guards

## Open Items
- Test Aiming state synchronization after fix
- Verify focus bar shows correct server values during combat

## Next Session Should
- Playtest to verify Aiming state is now synchronized
- Check that focus generation works for aimed attacks
- Monitor bot behavior (was retreating indefinitely)
