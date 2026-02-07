# Session: LEGENDARY Elemental Fix

**Date:** February 7, 2026
**Type:** Critical Bug Fix
**Status:** COMPLETE - LEGENDARY

---

## Problem Statement

Elemental buttons (Elemental1-4) and SpecialAbility button were NOT working like the Attack button for ranged fighters:
- **Expected:** HOLD = enter aiming state + camera control, RELEASE = cast spell
- **Actual:** Only Fire elemental worked, other elements (ETHER, EARTH) spawned Fire spells

---

## Root Cause Analysis

### Issue 1: Wrong Elemental Data Source

**Client CastManager.cs** was using:
```csharp
// WRONG - stale data set to FIRE defaults before correct values arrive
Elemental[] elementals = InterfaceManager.Instance.Player_elementals;
```

Should use:
```csharp
// CORRECT - authoritative source from matchAvatar.elementalSelected
Elemental[] elementals = player.m_elementals;
```

### Issue 2: Server Not Syncing Elementals

**Server PlayerManager.cs - ProcessAvatarUpload()** was:
- Updating `avatarList` from AVATARUPLOAD packet
- NOT updating `player.elementals` array
- NOT reinitializing CastManager

### Issue 3: Button Phase Handling

**PlayerInput.cs** elemental buttons had issues:
- `BEGINDRAG` immediately entered aiming (before knowing drag direction)
- No camera control during `DRAG`
- `HELD` blocked by `dragDirection != DOWN` check
- Missing `ENDDRAG` handler

### Issue 4: Focus Timing Desync

**SegmentedFillHighlighter.cs** used animated value:
```csharp
// WRONG - DOTween animation causes value to lag
int activeSegments = Mathf.FloorToInt(fillBar.fillAmount * count);
```

---

## Solutions Implemented

### Fix 1: Client CastManager.cs
```csharp
public void InitializeCastObjects(Player _player)
{
    player = _player;
    // Use player.m_elementals (authoritative source from matchAvatar.elementalSelected)
    Elemental[] elementals = _player.m_elementals;
    // ... initialization
}
```

### Fix 2: Server PlayerManager.cs
```csharp
// In ProcessAvatarUpload()
if (data.elementalSelected != null && data.elementalSelected.Length >= 2)
{
    int elementalCount = (player.fightingStyle == FightingStyles.MantraMuktha) ? 4 : 2;
    player.elementals = new Elemental[elementalCount];
    for (int i = 0; i < elementalCount && i < data.elementalSelected.Length; i++)
    {
        player.elementals[i] = new Elemental(data.elementalSelected[i]);
    }

    // Reinitialize CastManager with correct elementals
    if (player.character != null && player.character.castManager != null)
    {
        player.character.castManager = player.pGameObject.AddComponent<CastManager>()
            .Instantiate(player.elementals, player);
    }
}
```

### Fix 3: PlayerInput.cs Button Phases
```csharp
// Elemental buttons
if (buttonEvent.phase == ButtonPhase.BEGINDRAG)
{
    // Don't enter aiming on BEGINDRAG - wait to determine drag direction
}
else if (buttonEvent.phase == ButtonPhase.DRAG)
{
    var elemButton = elementalButtons[(int)buttonEvent.type];
    if (elemButton != null && elemButton.dragDirection == DragDirection.DOWN &&
        Mathf.Abs(elemButton.dragThreshold) > NewButtonScript.minDragThreshold_Vertical)
    {
        inputManager.TriggerDefenseCast(spellIndex); // Shield on drag DOWN
    }
    else
    {
        if (player.character.stateManager.GetState() != FSM.StateType.Spell_Aiming)
            inputManager.TriggerSpellAiming(spellIndex);
        inputManager.ChangeCameraAngleTest(TouchButtonsNew[(int)buttonEvent.type]);
    }
}
// ... similar for ENDDRAG, HELD, RELEASE, TAP
```

### Fix 4: SegmentedFillHighlighter.cs
```csharp
public void UpdateFill(float incomingFocus, float totalFocus)
{
    float targetFillAmount = incomingFocus * 0.01f;
    fillBar.DOFillAmount(targetFillAmount, 0.25f).SetEase(Ease.OutQuad);
    // Use TARGET fill amount for segment calculation, not current animated value
    ApplyVisuals(targetFillAmount);
}

private void ApplyVisuals(float filledAmount)
{
    filledAmount = Mathf.Clamp01(filledAmount);
    // Add small epsilon to prevent floating point edge cases
    int activeSegments = Mathf.FloorToInt(filledAmount * count + 0.001f);
    // ...
}
```

---

## Commits

### Client
```
cbed84eb9 [LEGENDARY] fix: Elemental/SpecialAbility controls fully working
```

### Server
```
ace8c99 [LEGENDARY] fix: Server elemental sync from AVATARUPLOAD
```

---

## Technical Details

### Spell Index Bit Packing
- Format: `(int)elementalType << 5 | spellType`
- ElementalType values: FIRE=0, WATER=1, AIR=2, ETHER=3, EARTH=4
- Example values: ETHER=96 (3<<5), EARTH=128 (4<<5)

### Data Flow
```
matchAvatar.elementalSelected → player.m_elementals → CastManager.ActiveCasts
                                      ↓
                              SpellIndex.elementalType
                                      ↓
                              Correct spell spawned
```

### Button Phase Flow
```
BEGINDRAG → (wait for direction)
DRAG → Check direction: DOWN=shield, else=aiming+camera
HELD → Enter aiming state
RELEASE → Cast spell
TAP → Instant cast
```

---

## Files Modified

| File | Changes |
|------|---------|
| `Assets/Scripts/Managers/CastManager.cs` | Use player.m_elementals |
| `Assets/Scripts/Player/PlayerInput.cs` | Button phase handling |
| `Assets/UI/New UI/Scripts/SegmentedFillHighlighter.cs` | Focus timing fix |
| Server: `PlayerManager.cs` | ProcessAvatarUpload elemental sync |

---

## Verification

- [x] All 4 elemental buttons work correctly
- [x] SpecialAbility button works correctly
- [x] Shield cast on drag down works
- [x] Focus activates at correct thresholds (25, 50, 75, 100)
- [x] Astra activates immediately at 100 focus
- [x] Works for all fighting styles
- [x] Works on PC and Mobile

---

*Session completed: February 7, 2026*
