# Combat System

## Overview

Server-authoritative combat system where all damage and state changes are validated by the server. Client predicts locally for responsiveness, server reconciles mismatches.

## Combat Authority Architecture

See [ADR-001](../decisions/ADR-001-combat-authority-pattern.md) for the decision rationale.

### Authority Types

| Type | Mode | Validation | Use Case |
|------|------|------------|----------|
| LocalAuthority | Offline | None | Tutorial, Training |
| ServerAuthority | Online | Server validates all | Multiplayer |
| HybridAuthority | Online | Prediction + post-validation | Solo modes |

### Key Interfaces

```csharp
interface ICombatAuthority {
    // Resource management
    bool ConsumeStamina(float amount);
    bool ConsumeWillpower(float amount);
    void AddFocus(int amount);

    // State queries
    bool IsAbilityAllowed(AbilityType ability);
    PlayerCombatState GetCurrentState();

    // Rollback support
    void SaveSnapshot(uint tick);
    void RestoreSnapshot(uint tick);
    PlayerStateSnapshot GetStateAtTick(uint tick);
}
```

## Player Stats

| Stat | Max | Regen | Notes |
|------|-----|-------|-------|
| Stamina | 100 | 15/sec | Dodge costs 70 |
| Willpower | 100 | 5/sec | Abilities cost varies |
| Focus | 100 | On hit | Builds to unlock Astra |
| Health | Varies | None | Character-specific |

## Damage Calculation

All damage flows through `CombatCalculator`:

```
BaseDamage * ElementalMultiplier * GodModifier * DefenseReduction
```

### Elemental System
- Fire > Wind > Earth > Water > Fire
- 1.5x damage when advantaged
- 0.75x damage when disadvantaged

### God Modifiers
- Shiva: +20% damage dealt
- Brahma: Shield abilities
- Vishnu: +30% movement speed

## State Integration

Combat state managed through `ControllerBase` FSM:
- Check `stateManager.IsBlockingInput()` before combat actions
- Combat states: Attacking, Casting, Dodging, Stunned, etc.

## Key Files

| File | Purpose |
|------|---------|
| `CombatAuthority/Core/ICombatAuthority.cs` | Interface |
| `CombatAuthority/Core/CombatCalculator.cs` | Damage math |
| `CombatAuthority/Authorities/*.cs` | Implementations |
| `CombatAuthority/Integration/PlayerAuthorityLink.cs` | Unity bridge |

## Common Issues

### Tutorial Mode Stamina Bug (Fixed 2026-01-05)
**Symptom**: Player can't dodge after first action in tutorial
**Cause**: `NotifyQuestStarted()` not called, `ResetPlayer()` never fires
**Fix**: `QuestFace.cs` now auto-calls `NotifyQuestStarted()` for all quests

### Dodge Not Working
1. Check stamina (requires 70)
2. Check `stateManager.IsBlockingInput()`
3. Check if LocalAuthority bypasses stamina (tutorial mode)
