# ADR-001: Combat Authority Pattern

**Date**: 2026-01-03
**Status**: Accepted
**Deciders**: Development team

## Context

AUM needs to support multiple game modes with different authority models:
- **Tutorial Mode**: Offline, no server, player actions should always succeed
- **Training Mode**: Offline practice against bots
- **Solo Mode**: Online but with client prediction
- **Multiplayer Mode**: Full server authority, all combat validated server-side

The challenge: How do we abstract these differences so game code doesn't need mode-specific conditionals everywhere?

## Decision

Implement the **Combat Authority Pattern** using an interface-based abstraction:

```csharp
interface ICombatAuthority {
    bool IsAbilityAllowed(AbilityType ability);
    bool ConsumeStamina(float amount);
    bool ConsumeWillpower(float amount);
    void AddFocus(int amount);
    PlayerCombatState GetCurrentState();
    // ... rollback methods for netcode
}
```

With concrete implementations:
- `LocalAuthority` - Always allows actions, no validation
- `ServerAuthority` - Validates with server, handles reconciliation
- `HybridAuthority` - Client prediction with post-validation

A `CombatAuthorityFactory` creates the appropriate authority based on `GameModeSettings`.

## Alternatives Considered

### 1. Mode Flags Throughout Code
```csharp
if (GameMode.IsMultiplayer) { validateWithServer(); }
else { justDoIt(); }
```
**Rejected**: Creates spaghetti code, hard to maintain, easy to miss cases.

### 2. Single Authority with Mode Parameter
```csharp
authority.ConsumeStamina(amount, GameMode.Current);
```
**Rejected**: Still requires mode awareness in calling code, violates single responsibility.

### 3. Server Authority Everywhere (Even Offline)
Run a local server for tutorial mode.
**Rejected**: Overhead for offline modes, complexity for simple tutorials.

## Consequences

### Positive
- Game code is mode-agnostic - just calls `authority.ConsumeStamina()`
- Easy to add new modes by creating new authority implementations
- Clear separation of concerns
- Rollback/reconciliation logic isolated to `ServerAuthority`

### Negative
- Additional abstraction layer
- Must ensure correct authority is created per mode
- State sync between authority and Unity components needs `PlayerAuthorityLink`

## Implementation Notes

### Key Files
- `Assets/Scripts/CombatAuthority/Core/ICombatAuthority.cs`
- `Assets/Scripts/CombatAuthority/Core/BaseAuthority.cs`
- `Assets/Scripts/CombatAuthority/Authorities/LocalAuthority.cs`
- `Assets/Scripts/CombatAuthority/Authorities/ServerAuthority.cs`
- `Assets/Scripts/CombatAuthority/Authorities/HybridAuthority.cs`
- `Assets/Scripts/CombatAuthority/Integration/CombatAuthorityFactory.cs`
- `Assets/Scripts/CombatAuthority/Integration/PlayerAuthorityLink.cs`

### Usage Pattern
```csharp
// In PlayerManager - auto-registers on spawn
PlayerManager.RegisterPlayerWithAuthority(player);

// In character code - mode-agnostic
if (combatAuthority.ConsumeStamina(70)) {
    TriggerDodge();
}
```

## Related
- ADR-002: Rollback Netcode Integration (future)
- Feature doc: `features/combat-system.md`
