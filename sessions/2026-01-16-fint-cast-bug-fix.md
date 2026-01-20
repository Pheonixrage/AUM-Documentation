# Session Log: 2026-01-16 - FInt Cast Bug & Post-Playtest Fixes

## Summary
Fixed critical FInt type casting bug causing melee animations to never complete, plus resolved 1991 CharacterController errors and 2786 bot warning spam from playtest analysis.

## What Was Done

### 1. Critical Fix: StateDuration Always 0.000 (Root Cause of Continuous Attack Bug)

**Problem:** `GetStateDuration()` in StateManager.cs returned 0.000 even after multiple ticks in Melee state.

**Root Cause Discovery:**
- `animStateLength` is type `FInt` (fixed-point integer with 12-bit shift = 4096 scale)
- Code used `(float)animStateLength` which C# resolved as `(float)(int)animStateLength`
- `FInt` has `explicit operator int` that does `RawValue >> 12`
- For small values like 0.0167 (one tick at 60Hz): `RawValue = 68`, `68 >> 12 = 0`
- Result: All sub-1-second durations truncated to 0!

**Fix:** Changed `GetStateDuration()` to use `animStateLength.ToFloat()` instead of `(float)animStateLength`
- `ToFloat()` properly computes `RawValue / 4096.0f`

**File:** `AUM-The-Epic/Assets/Scripts/StateMachine/StateManager.cs:357-360`

### 2. Fix: CharacterController Inactive Error (1991 errors)

**Problem:** "CharacterController.Move called on inactive controller" spam during match end.

**Root Cause:** Checks verified `controller.enabled` but not whether the GameObject was active in hierarchy.

**Fix:** Added `controller.gameObject.activeInHierarchy` check to:
- `PlayerBase.cs:1121` - MoveLogic
- `PlayerBase.cs:1220` - Interpolate
- `DodgeController.cs:182` - DodgeInterpolate

### 3. Fix: Bot Death State Warning Spam (2786 warnings)

**Problem:** "[BotMove] BLOCKED | State:Death" logged every 30 ticks even when bot correctly sent zero joystick.

**Root Cause:** Warning condition didn't check if there was actual joystick input being blocked.

**Fix:** Added `(joy_x != 0 || joy_y != 0)` condition to warning log.

**File:** `AUM-Headless/Assets/Scripts/Player/PlayerManager.cs:1762`

### 4. Previously Completed (from earlier in session)

- **Phase 1:** ServerAuthority willpower sync + focus accumulation on hit
- **Phase 2:** Verified melee state exit logic (already correct)
- **Phase 3:** 60Hz upgrade across client and server
- **Phase 4:** Playtest analysis with multi-agent log inspection

## Key Technical Insight

**FInt (Fixed-Point Integer) Casting Pitfall:**
```csharp
// WRONG - truncates to 0 for small values
float value = (float)fintValue;  // Goes through (int) cast first!

// CORRECT - preserves decimal precision
float value = fintValue.ToFloat();  // Divides RawValue by scale factor
```

This is a subtle C# behavior: when no explicit `float` cast exists, it uses the available `int` cast as intermediate, losing precision.

## Files Changed

### Client (AUM-The-Epic)
| File | Change |
|------|--------|
| `Assets/Scripts/StateMachine/StateManager.cs` | FInt ToFloat() fix |
| `Assets/Scripts/Player/PlayerBase.cs` | activeInHierarchy checks |
| `Assets/Scripts/Player/DodgeController.cs` | activeInHierarchy check |

### Server (AUM-Headless)
| File | Change |
|------|--------|
| `Assets/Scripts/Player/PlayerManager.cs` | Warning spam fix |
| `Assets/Scripts/CombatAuthority/Server/ServerAuthority.cs` | Willpower sync + focus (earlier) |

## Expected Improvements After Next Playtest

1. **Melee attacks exit naturally** - StateDuration now increments properly
2. **No continuous attack bug** - IsAnimationDone() will return true when animation completes
3. **~1991 fewer errors** - CharacterController checks prevent inactive controller calls
4. **~2786 fewer warnings** - Bot death state no longer spams logs
5. **Focus accumulates** - ServerAuthority adds focus on successful hits

## Open Items

- Verify fixes in next playtest
- Movement lag mentioned by user - may need further investigation
- Consider removing diagnostic log in AmukthaPlayer.OnAttack() after verification

## Technical Debt Identified

- FInt type should probably have an explicit `float` operator to prevent this bug pattern
- Could add compile-time warning for `(float)FInt` casts

---

*Session Duration: ~45 minutes*
*Primary Fix: FInt casting bug in GetStateDuration()*
