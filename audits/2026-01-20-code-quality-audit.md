# Code Quality Audit - January 20, 2026

**Project:** AUM-Unity-Staging-Legacy (Client)
**Auditor:** Claude Code
**Scope:** Recent changes (January 2026) and critical paths

---

## Summary

| Category | Count | Severity |
|----------|-------|----------|
| Critical Bugs | 1 | CRITICAL |
| High Priority | 5 | HIGH |
| Medium Priority | 3 | MEDIUM |
| Low Priority (TODOs) | 2 | LOW |
| **Total Issues** | **11** | - |

---

## Critical Bugs

### 1. Logic Operator Bug in MantraMukthaPlayer.cs (Line 580)

```csharp
// WRONG - Always evaluates to true!
if (selectedSpellIndex.elementalType != Elementals.FIRE || selectedSpellIndex.elementalType != Elementals.AIR)

// CORRECT - Should use AND
if (selectedSpellIndex.elementalType != Elementals.FIRE && selectedSpellIndex.elementalType != Elementals.AIR)
```

**Impact:** Condition always returns true, bypassing intended logic.

---

## High Priority Issues

### 1. Hardcoded Server Configuration (TestModeClient.cs)

| Line | Issue |
|------|-------|
| 42 | Server IP hardcoded: `"65.109.133.129"` |
| 45 | Server port hardcoded: `6006` |
| 178-179 | Fallback values: `"127.0.0.1"` and `7777` |

**Recommendation:** Move to ScriptableObject or configuration file.

### 2. Missing Null Checks (PCInput.cs)

```csharp
void Start()
{
    OnScreenStick.SetActive(false);  // NO NULL CHECK
    cancelButton.SetActive(false);   // NO NULL CHECK
}
```

**Risk:** NullReferenceException if GameObjects unassigned in inspector.

### 3. Performance - Repeated LayerMask Lookup (MantraMukthaPlayer.cs:126)

```csharp
LayerMask.GetMask("EnemyUnits")  // Called every frame!
```

**Recommendation:** Cache as static readonly field.

### 4. Overly Broad Exception Handling (CamTouchField.cs:75-79)

```csharp
catch (Exception ex) {
#if UNITY_EDITOR
    Debug.LogError($"{ex.Message} - {ex.StackTrace}");
#endif
}
```

**Issues:**
- Catches generic Exception
- Silently swallowed in builds
- 30+ lines in try block

### 5. Missing Component Null Check (MantraMukthaPlayer.cs:19)

```csharp
meleeGuideComponents = GetComponent<MeleeGuideComponents>();
// No null check - could crash later
```

---

## Medium Priority

### 1. Platform-Specific Code Gaps

- PC input returns early from CamTouchField
- No fallback for Mac/Linux standalone
- `#if UNITY_EDITOR || UNITY_STANDALONE_WIN` excludes other platforms

### 2. Raycast Performance Issues

- `Physics.RaycastAll()` without pooling
- Chained transform access without null checks
- String tag comparisons in loops

### 3. Defensive Re-initialization Pattern

```csharp
public override void SetMeleeGuide()
{
    if (AimingGuide == null)
    {
        InitializeFightingStyle();  // Suggests race condition
    }
}
```

---

## Low Priority (TODOs)

### CustomButton.cs

```csharp
////TODO: custom icon for OnScreenButton component  (Line 6)
////TODO: pressure support  (Line 74-83)
```

---

## Files Reviewed

| File | Path |
|------|------|
| TestModeClient.cs | Assets/Scripts/Managers/ |
| PCInput.cs | Assets/Scripts/Player/ |
| CamTouchField.cs | Assets/Scripts/UI/ |
| CustomButton.cs | Assets/Inputs/ |
| MantraMukthaPlayer.cs | Assets/Characters/MantraMuktha/Scripts/ |

---

## Top 3 Fixes Required

1. **Fix logic operator** in MantraMukthaPlayer.cs:580 (OR → AND)
2. **Add null checks** in PCInput.cs for OnScreenStick and cancelButton
3. **Externalize server config** from TestModeClient.cs

---

## Notes

This audit focused on recent changes and critical paths. A full codebase audit would require more time. The identified issues are non-blocking for Republic Day launch but should be addressed for stability.

---

*Audit completed: January 20, 2026*
