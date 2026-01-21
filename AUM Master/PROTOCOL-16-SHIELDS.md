# PROTOCOL-16-SHIELDS.md
# Elemental Shield System - Detailed Mechanics

## Overview

The Elemental Shield system provides defensive blocking with complex damage mitigation based on attack type, weapon, and elemental interactions. Shields have **integrity** that depletes with hits and can be destroyed.

**Key Files:**
- `Assets/Scripts/Player/ElementalShield.cs` - Shield mechanics
- `Assets/Scripts/ShieldCastAttributes.cs` - Shield resource costs

---

## 1. Shield Structure

### 1.1 ElementalShield Class

```csharp
public class ElementalShield
{
    public byte shieldButtonIndex;              // Which elemental button (0-3)
    public Elemental shieldElemental;           // Shield's element type
    private float shieldDuration;               // Frames active
    private List<Entity> registeredEntities;    // Entities that hit this shield
    public float shieldHitCount;                // Current integrity damage

    private const float BaseShieldIntegrity = 3.0f;  // Max integrity
}
```

### 1.2 Shield Lifecycle

```csharp
public bool Process(float deltaTime)
{
    shieldDuration++;

    // Shield expires after 10 seconds
    if (shieldDuration >= 10 / deltaTime)
    {
        return false;  // Destroy shield
    }

    // Shield destroyed if integrity depleted
    if (shieldHitCount >= BaseShieldIntegrity)
    {
        return false;  // Destroy shield
    }

    return true;  // Shield still active
}
```

### 1.3 Shield Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `BaseShieldIntegrity` | 3.0 | Max integrity points |
| Max Duration | 10s | Shield auto-expires |
| Focus Cost | 2 segments | From focus bar |

---

## 2. AttackInfo Structure

### 2.1 Attack Metadata

```csharp
public class AttackInfo
{
    public WeaponType Weapon = WeaponType.None;           // Sword, Axe, Bow, Chakra, Magic
    public AttackCharge Charge = AttackCharge.Basic;      // Basic or Charged
    public Elementals? SpellElement;                       // For spell attacks
    public AttackDamageComponent Component = AttackDamageComponent.Physical;
    public CoatedType CoatedDamageType = CoatedType.None; // Elemental coating
    public bool IsThirdEyeActive = false;                  // Third Eye buff
    public Player targetPlayer;                            // Defender
    public Player sourcePlayer;                            // Attacker
    public DamageType damageType = DamageType.NONE;       // Damage classification
    public Effects.EffectType effectType = Effects.EffectType.EFFECT_NONE;
}
```

### 2.2 RegisterShieldResult

```csharp
public class RegisterShieldResult
{
    public bool result;                    // true = attack passed or shield broken
    public float integrityDamageApplied;   // Integrity damage dealt this hit
    public float damagePassFraction;       // Fraction of damage that passes (0-1)
}
```

---

## 3. Shield Hit Registration

### 3.1 Main Entry Point

```csharp
public RegisterShieldResult RegisterShieldHit(DamageType damageType, Entity sourceEntity, AttackInfo attack = null)
{
    // Backwards compatibility: infer AttackInfo if not provided
    if (attack == null)
    {
        attack = InferAttackInfo(damageType);
    }

    RegisterShieldResult returnResult = new RegisterShieldResult()
    {
        result = false,
        integrityDamageApplied = 0f,
        damagePassFraction = 0f
    };

    // Shield already broken
    if (shieldHitCount >= BaseShieldIntegrity)
    {
        returnResult.result = true;
        return returnResult;
    }

    // Check if entity is new (prevents double-counting)
    bool isNewEntity = (sourceEntity != null && !CheckEntity(sourceEntity));

    // Delegate to specific handler
    switch (damageType)
    {
        case DamageType.MELEE:
            return HandlePhysicalAttack(attack, sourceEntity, isNewEntity, returnResult);

        case DamageType.FIRE:
        case DamageType.WATER:
        case DamageType.AIR:
        case DamageType.EARTH:
        case DamageType.ETHER:
            return HandleElementalAttack(attack, sourceEntity, isNewEntity, returnResult);

        case DamageType.ASTRA_SHIVA:
        case DamageType.ASTRA_BRAHMA:
        case DamageType.ASTRA_VISHNU:
            return HandleAstraAttack(attack, sourceEntity, isNewEntity, returnResult);

        case DamageType.AXETHROW:
            ApplyIntegrityDamage(1.0f, returnResult, attack);
            break;
    }

    if (isNewEntity)
    {
        AddEntity(sourceEntity);
    }

    return returnResult;
}
```

---

## 4. Physical Attack Handling

### 4.1 Weapon vs Shield Matrix

The damage pass fraction and integrity damage depends on weapon type and shield element.

```csharp
private RegisterShieldResult HandlePhysicalAttack(AttackInfo attack, Entity sourceEntity,
                                                   bool isNewEntity, RegisterShieldResult returnResult)
{
    float passFraction = 0f;
    float integrityDamage = 0f;
    Elementals shieldElem = shieldElemental.GetElemental();

    switch (attack.Weapon)
    {
        case WeaponType.Sword:
            // ...
        case WeaponType.Axe:
            // ...
        case WeaponType.Bow:
            // ...
        case WeaponType.Chakra:
            // ...
        case WeaponType.Magic:
            // ...
    }
}
```

### 4.2 Sword (Amuktha)

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 50% | 0 |
| Water | 50% | 0 |
| Air | 0% (Blocked) | 0 |
| Earth | 0% (Blocked) | 0 |
| Ether | 0% (Blocked) | 0 |

```csharp
case WeaponType.Sword:
    passFraction = (shieldElem == Elementals.FIRE || shieldElem == Elementals.WATER) ? 0.5f : 0f;
    integrityDamage = 0f;
    break;
```

### 4.3 Axe (MukthaMuktha)

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 50% | 0 |
| Water | 50% | 0.75 |
| Air | 50% | 0.75 |
| Earth | 0% (Blocked) | 0.75 |
| Ether | 0% (Blocked) | 0.75 |

```csharp
case WeaponType.Axe:
    passFraction = (shieldElem == Elementals.FIRE || shieldElem == Elementals.WATER ||
                   shieldElem == Elementals.AIR) ? 0.5f : 0f;
    integrityDamage = (shieldElem == Elementals.WATER || shieldElem == Elementals.AIR ||
                      shieldElem == Elementals.EARTH || shieldElem == Elementals.ETHER) ? 0.75f : 0f;
    if (shieldElem == Elementals.EARTH || shieldElem == Elementals.ETHER) passFraction = 0f;
    break;
```

### 4.4 Bow (YantraMuktha)

**Basic Shot:**

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 100% | 0 |
| Water | 50% | 0 |
| Air | 50% | 0 |
| Earth | 0% (Blocked) | 0 |
| Ether | 0% (Blocked) | 0 |

**Charged Shot:**

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 100% | 0 |
| Water | 50% | 0.5 |
| Air | 100% | 0.5 |
| Earth | 0% (Blocked) | 0 |
| Ether | 0% (Blocked) | 0 |

```csharp
case WeaponType.Bow:
    if (attack.Charge == AttackCharge.Basic)
    {
        passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                       (shieldElem == Elementals.WATER || shieldElem == Elementals.AIR) ? 0.5f : 0f;
        integrityDamage = 0f;
    }
    else // Charged
    {
        passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                       (shieldElem == Elementals.WATER) ? 0.5f :
                       (shieldElem == Elementals.AIR) ? 1f : 0f;
        integrityDamage = (shieldElem == Elementals.WATER || shieldElem == Elementals.AIR) ? 0.5f : 0f;
        if (shieldElem == Elementals.EARTH || shieldElem == Elementals.ETHER) passFraction = 0f;
    }
    break;
```

### 4.5 Chakra (PaniMuktha)

**Basic Shot:**

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 100% | 0 |
| Water | 50% | 0 |
| Air | 0% (Blocked) | 0 |
| Earth | 0% (Blocked) | 0 |
| Ether | 0% (Blocked) | 0 |

**Charged Shot:**

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 100% | 0 |
| Water | 50% | 0 |
| Air | 50% | 0 |
| Earth | 0% (Blocked) | 0 |
| Ether | 0% (Blocked) | 0 |

```csharp
case WeaponType.Chakra:
    if (attack.Charge == AttackCharge.Basic)
    {
        passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                       (shieldElem == Elementals.WATER) ? 0.5f : 0f;
        integrityDamage = 0f;
    }
    else // Charged
    {
        passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                       (shieldElem == Elementals.WATER || shieldElem == Elementals.AIR) ? 0.5f : 0f;
        integrityDamage = 0f;
    }
    break;
```

### 4.6 Magic (MantraMuktha)

**Basic & Charged:**

| Shield | Pass Fraction | Integrity Damage |
|--------|---------------|------------------|
| Fire | 50% | 0.5 |
| Water | 0% (Blocked) | 0.5 |
| Air | 50% | 0.5 |
| Earth | 50% | 0.5 |
| Ether | 50% | 0.5 |

```csharp
case WeaponType.Magic:
    passFraction = (shieldElem == Elementals.WATER) ? 0f : 0.5f;
    integrityDamage = 0.5f;
    break;
```

### 4.7 Third Eye Multiplier

When Third Eye is active, integrity damage is multiplied:
- Basic attack: ×2
- Charged attack: ×4

```csharp
if (attack.IsThirdEyeActive)
    integrityDamage *= attack.Charge == AttackCharge.Charged ? 4f : 2f;
```

---

## 5. Elemental Attack Handling

### 5.1 Elemental Interaction Matrix

```csharp
private RegisterShieldResult HandleElementalAttack(AttackInfo attack, Entity sourceEntity,
                                                    bool isNewEntity, RegisterShieldResult returnResult)
{
    Elementals spell = attack.SpellElement.Value;
    Elementals shieldElem = shieldElemental.GetElemental();

    Interaction interaction = DetermineInteraction(spell, shieldElem);
    // ...
}
```

### 5.2 Interaction Types

```csharp
public enum Interaction
{
    Nullify,      // 0% damage, 0% integrity
    Vulnerable,   // 100% damage, 100% integrity
    Mitigate      // 50% damage, 50% integrity
}
```

### 5.3 Full Interaction Matrix

| Shield ↓ / Spell → | FIRE | WATER | AIR | EARTH | ETHER |
|---------------------|------|-------|-----|-------|-------|
| **FIRE** | Mitigate | **Nullify** | **Vulnerable** | Mitigate | Mitigate |
| **WATER** | **Vulnerable** | Mitigate | Mitigate | **Nullify** | Mitigate |
| **AIR** | **Nullify** | Mitigate | Mitigate | Mitigate | **Vulnerable** |
| **EARTH** | Mitigate | **Vulnerable** | Mitigate | Mitigate | **Nullify** |
| **ETHER** | Mitigate | Mitigate | **Nullify** | **Vulnerable** | Mitigate |

```csharp
if (shieldElem == Elementals.ETHER)
{
    if (spell == Elementals.AIR) interaction = Interaction.Nullify;
    else if (spell == Elementals.EARTH) interaction = Interaction.Vulnerable;
    else interaction = Interaction.Mitigate;
}
else if (shieldElem == Elementals.AIR)
{
    if (spell == Elementals.ETHER) interaction = Interaction.Vulnerable;
    else if (spell == Elementals.FIRE) interaction = Interaction.Nullify;
    else interaction = Interaction.Mitigate;
}
else if (shieldElem == Elementals.FIRE)
{
    if (spell == Elementals.AIR) interaction = Interaction.Vulnerable;
    else if (spell == Elementals.WATER) interaction = Interaction.Nullify;
    else interaction = Interaction.Mitigate;
}
else if (shieldElem == Elementals.WATER)
{
    if (spell == Elementals.FIRE) interaction = Interaction.Vulnerable;
    else if (spell == Elementals.EARTH) interaction = Interaction.Nullify;
    else interaction = Interaction.Mitigate;
}
else if (shieldElem == Elementals.EARTH)
{
    if (spell == Elementals.ETHER) interaction = Interaction.Nullify;
    else if (spell == Elementals.WATER) interaction = Interaction.Vulnerable;
    else interaction = Interaction.Mitigate;
}
```

### 5.4 Damage Fractions by Interaction

| Interaction | Burst | Zone | Status/DoT | Integrity |
|-------------|-------|------|------------|-----------|
| Nullify | 0% | 0% | 0% | 0× |
| Mitigate | 50% | 50% | 50% | 0.5× |
| Vulnerable | 100% | 100% | 100% | 1× |

### 5.5 Charged Spell Overrides

Charged spells can override to higher damage:

```csharp
if (attack.Charge == AttackCharge.Charged)
{
    // Ether → Earth shield
    if (attack.SpellElement == Elementals.ETHER && shieldElem == Elementals.EARTH)
    {
        burstFraction = Math.Max(burstFraction, 1f);
        statusFraction = Math.Max(statusFraction, 1f);
    }
    // Air → Ether shield
    else if (attack.SpellElement == Elementals.AIR && shieldElem == Elementals.ETHER)
    {
        burstFraction = Math.Max(burstFraction, 1f);
        statusFraction = Math.Max(statusFraction, 1f);
    }
    // Fire → Air shield
    else if (attack.SpellElement == Elementals.FIRE && shieldElem == Elementals.AIR)
    {
        burstFraction = Math.Max(burstFraction, 1f);
        statusFraction = Math.Max(statusFraction, 0.5f);
    }
    // Water → Fire shield
    else if (attack.SpellElement == Elementals.WATER && shieldElem == Elementals.FIRE)
    {
        burstFraction = Math.Max(burstFraction, 1f);
        statusFraction = Math.Max(statusFraction, 1f);
    }
    // Earth → Water shield
    else if (attack.SpellElement == Elementals.EARTH && shieldElem == Elementals.WATER)
    {
        burstFraction = Math.Max(burstFraction, 1f);
        statusFraction = Math.Max(statusFraction, 1f);
    }
}
```

### 5.6 Integrity Damage by Component

| Component | Base Integrity |
|-----------|---------------|
| SpellBurst | 1.0 |
| SpellZone | 0.5 |
| SpellDoT | 0.5 |

```csharp
float integrityThisHit = 0f;
if (attack.Component == AttackDamageComponent.SpellBurst)
    integrityThisHit = 1.0f * integrityMultiplier;
else if (attack.Component == AttackDamageComponent.SpellZone)
    integrityThisHit = 0.5f * integrityMultiplier;
else if (attack.Component == AttackDamageComponent.SpellDoT)
    integrityThisHit = 0.5f * integrityMultiplier;
```

---

## 6. Astra Attack Handling

### 6.1 Astra vs Shield

**All Astras instantly destroy shields.**

```csharp
private RegisterShieldResult HandleAstraAttack(AttackInfo attack, Entity sourceEntity,
                                                bool isNewEntity, RegisterShieldResult returnResult)
{
    // Astras: instantly destroy shield
    shieldHitCount = BaseShieldIntegrity;
    returnResult.result = true;
    Utils.SendLogData(attack.targetPlayer, Utils.CombatLogType.SHIELD_BREAK,
        attack.sourcePlayer, attack.damageType, Effects.EffectType.EFFECT_NONE, 0,
        BaseShieldIntegrity - shieldHitCount);
    return returnResult;
}
```

---

## 7. ShieldCastAttributes

### 7.1 Resource Costs

```csharp
public class ShieldCastAttributes : MonoBehaviour
{
    public Elementals Elemental;

    // Resource costs (hardcoded)
    public int stamina = 50;
    public int willpower = 250;
}
```

| Resource | Cost |
|----------|------|
| Stamina | 50 |
| Willpower | 250 |
| Focus | 2 segments |

---

## 8. Shield Activation

### 8.1 PlayerBase.ActivateElementalShield

```csharp
public void ActivateElementalShield(byte buttonIndex)
{
    if (character.AllowSpellCasting())
    {
        activeElementalShield = new ElementalShield(buttonIndex, character.player.elementals[buttonIndex]);
    }
}
```

### 8.2 Shield Processing

```csharp
public void Process(float deltaTime)
{
    // Process Elemental Shields
    if (activeElementalShield != null)
    {
        if (!activeElementalShield.Process(deltaTime))
        {
            activeElementalShield = null;  // Shield expired or broken
        }
    }
    // ... process effects
}
```

---

## 9. Entity Tracking

Shields track which entities have already hit them to prevent double-counting.

```csharp
private void AddEntity(Entity entity)
{
    if (entity != null && !registeredEntities.Contains(entity))
    {
        registeredEntities.Add(entity);
    }
}

private bool CheckEntity(Entity entity)
{
    // Returns true if entity already registered
    if (entity == null || registeredEntities.Contains(entity))
    {
        return true;
    }
    return false;
}
```

---

## 10. Combat Logging Integration

Shield hits are logged for combat telemetry:

```csharp
// On block
Utils.SendLogData(attack.targetPlayer, Utils.CombatLogType.BLOCK,
    attack.sourcePlayer, attack.damageType, Effects.EffectType.EFFECT_NONE,
    integrityDamage, BaseShieldIntegrity - shieldHitCount);

// On shield break
if (shieldHitCount >= BaseShieldIntegrity)
    Utils.SendLogData(attack.targetPlayer, Utils.CombatLogType.SHIELD_BREAK,
        attack.sourcePlayer, attack.damageType, Effects.EffectType.EFFECT_NONE);

// Elemental interaction logging
Utils.CombatLogType combatLogType = interaction switch
{
    Interaction.Mitigate => Utils.CombatLogType.MITIGATE,
    Interaction.Vulnerable => Utils.CombatLogType.VULNERABLE,
    Interaction.Nullify => Utils.CombatLogType.NULLIFY,
    _ => Utils.CombatLogType.RECEIVE
};
```

---

## 11. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `ElementalShield.cs` | 437 | Complete shield mechanics |
| `ShieldCastAttributes.cs` | 15 | Shield resource costs |

**Total: ~452 lines of code**

---

*Last Updated: January 21, 2026*
*Protocol Version: 16.0*
