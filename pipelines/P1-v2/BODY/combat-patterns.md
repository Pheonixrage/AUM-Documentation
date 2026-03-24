---
pipeline: P1
project: AUM-BODY
type: pattern
date: 2026-03-24
tags: [combat, authority, elemental]
---

# Combat Patterns — AUM BODY (Client)

## ICombatAuthority Pattern

All combat state queries and mutations go through `ICombatAuthority`:

| Mode | Use Case | Behavior |
|------|----------|----------|
| LocalAuthority | Tutorial/Training | Everything runs locally |
| HybridAuthority | First Match | Local physics + damage multipliers |
| ServerAuthority | Multiplayer | Wraps NetworkManager for server validation |

```csharp
var authority = InterfaceManager.Instance?.playerInput?.InputManager?.GetCombatAuthority();
float stamina = authority.GetStamina(playerId);
authority.ConsumeStamina(playerId, cost);
```

**Never** access `player.playerData.stamina` directly — always go through authority.

## Damage Flow

1. Client detects hit locally (immediate VFX feedback)
2. Client sends hit attempt to server via authority
3. Server validates: frame timing, distance, state validity
4. Server broadcasts result to all clients
5. Clients reconcile prediction with server result

## Elemental Interactions

```
ETHER → AIR → FIRE → WATER → EARTH → (back to ETHER)
```

- **Child → Parent:** NULLIFY (cancel damage)
- **Parent → Child:** VULNERABLE (+25% damage)
- **Other:** MITIGATE (-25% damage)

## Resource Values

| Resource | Max | Purpose |
|----------|-----|---------|
| Willpower | 15,000 | Health (reduce to 0 to win) |
| Stamina | 100 | Dodge (costs 70, Vishnu 45) |
| Focus | 100 (4 bars) | Abilities (25/50/75/100 costs) |

## Key Files

- `Assets/Scripts/CombatAuthority/Core/ICombatAuthority.cs`
- `Assets/Scripts/CombatAuthority/Core/BaseAuthority.cs`
- `Assets/Scripts/CombatAuthority/Core/CombatCalculator.cs`
- `Assets/Scripts/CombatAuthority/Config/AbilityCosts.cs`
