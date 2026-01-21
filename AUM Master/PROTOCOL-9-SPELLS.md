# PROTOCOL-9-SPELLS.md
# AUM Complete Spell System Documentation

> **Document Version:** 1.0
> **Last Updated:** January 21, 2026
> **Source Files:** 16 files analyzed (~1,200 lines)

---

## Table of Contents

1. [Spell System Overview](#1-spell-system-overview)
2. [Base Spell Class](#2-base-spell-class)
3. [Spell Encoding](#3-spell-encoding)
4. [Fire Element](#4-fire-element)
5. [Water Element](#5-water-element)
6. [Air Element](#6-air-element)
7. [Earth Element](#7-earth-element)
8. [Ether Element](#8-ether-element)
9. [Effects System](#9-effects-system)
10. [Elemental Shield System](#10-elemental-shield-system)
11. [Spell Enums](#11-spell-enums)

---

## 1. Spell System Overview

### Architecture

```
SpellCastAttributes (client prefab)     SpellAttributes (server prefab)
        │                                       │
        ▼                                       ▼
┌─────────────────┐                   ┌─────────────────┐
│ Defines casting │                   │ Defines damage  │
│ - Distance[]    │                   │ - Elemental     │
│ - Angle[]       │                   │ - attackType    │
│ - Stamina cost  │                   │ - spellType     │
│ - Focus cost    │                   │ - effectType    │
└─────────────────┘                   └─────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ SpellProjectile │ ─────▶ Entity (base class)
            │ (spawned spell) │
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │    Spell      │ ─────▶ MonoBehaviour
            │ (damage logic)│
            └───────────────┘
                    │
        ┌───────────┼───────────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
      Fire       Water        Air        Earth       Ether
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
    FireBurn    Pushback    AirSlow    EarthStun   EtherMute
```

### Damage Flow

```
Spell Cast → InitiateDamage() → Check Shield → Apply Damage → Apply Effect
                  │                   │              │              │
                  │                   │              │              └─▶ AddEffect()
                  │                   │              └─▶ DoSpellDamage()
                  │                   └─▶ ElementalShield.RegisterShieldHit()
                  └─▶ GetPlayersInSpellRange()
```

---

## 2. Base Spell Class

**Source:** `/Assets/Scripts/Spells/Spell.cs` (123 lines)

### Class Definition

```csharp
[DisallowMultipleComponent]
public class Spell : MonoBehaviour
{
    // ═══════════════════════════════════════════════════════════════════
    // METADATA
    // ═══════════════════════════════════════════════════════════════════
    [Header("Spell Metadata")]
    public Elementals elemental;        // FIRE, WATER, AIR, EARTH, ETHER
    public SpellSubType subType;        // INSTANT, CHANNELING, CHARGED, TRAPS
    public RangeType rangeType;         // CLOSE_RANGE, LONG_RANGE
    public LevelType level;             // Level1, Level2, Level3

    // ═══════════════════════════════════════════════════════════════════
    // DAMAGE CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════
    [Header("Damage Mode")]
    public SpellDamageMode damageMode;  // BurstOnly, ZoneOnly, BurstAndEffect, etc.

    [Header("Damage values")]
    public float burstDamage;           // Initial burst damage
    public float zoneDamage;            // Damage per zone tick

    public float spellDuration;         // Total spell lifetime (seconds)
    public float spellTickInterval;     // Time between zone ticks
    public float spellDistance;         // Spell radius/range
    public float spellAngle;            // Cone angle (degrees)

    // ═══════════════════════════════════════════════════════════════════
    // EFFECT CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════
    public Effects.EffectType effectType;   // Status effect to apply
    public float effectDamage;              // Damage per effect tick
    public float effectDuration;            // Effect duration (seconds)
    public float effectTickInterval;        // Time between effect ticks

    // ═══════════════════════════════════════════════════════════════════
    // INTERNAL STATE
    // ═══════════════════════════════════════════════════════════════════
    [HideInInspector] public SpellProjectile spellEntity;
    private int spellFrameCount;
    private float DPSTimer;
}
```

### Damage Mode Checking Methods

```csharp
public bool ShouldApplyBurst()
{
    return damageMode == SpellDamageMode.BurstOnly
        || damageMode == SpellDamageMode.BurstAndZone
        || damageMode == SpellDamageMode.BurstAndEffect
        || damageMode == SpellDamageMode.BurstZoneAndEffect;
}

public bool ShouldApplyZone()
{
    return damageMode == SpellDamageMode.ZoneOnly
        || damageMode == SpellDamageMode.BurstAndZone
        || damageMode == SpellDamageMode.ZoneAndEffect
        || damageMode == SpellDamageMode.BurstZoneAndEffect;
}

public bool ShouldApplyEffect()
{
    return damageMode == SpellDamageMode.EffectOnly
        || damageMode == SpellDamageMode.BurstAndEffect
        || damageMode == SpellDamageMode.ZoneAndEffect
        || damageMode == SpellDamageMode.BurstZoneAndEffect;
}
```

### Core Methods

```csharp
// Called once when spell spawns
public virtual void Initialize() { }

// Called every frame - returns false to destroy spell
public virtual bool Process(float deltaTime)
{
    spellFrameCount++;
    if (spellFrameCount >= (int)(spellDuration / Mathf.Max(0.0001f, deltaTime)))
    {
        Destroy(this.gameObject);
        return false;
    }
    return true;
}

// DPS timer with configurable tick rate
public bool DPSCounter(float deltaTime, float dpsTick)
{
    DPSTimer += deltaTime;
    if (DPSTimer >= dpsTick)
    {
        DPSTimer -= dpsTick;
        return true;  // Time to apply damage tick
    }
    return false;
}

// Find players within spell range
public Player[] GetPlayersInSpellRange(float distance)
{
    List<Player> playerList = new List<Player>();
    foreach (Player player in PlayerManager.playerList.Values)
    {
        if ((player.character.playerBase.ContactPoint.transform.position
            - transform.position).magnitude <= distance)
        {
            playerList.Add(player);
        }
    }
    return playerList.ToArray();
}

// Check if target is within cone angle
public bool TargetWithinAngle(GameObject targetObject, float effect_angle)
{
    return Vector3.Angle(transform.forward,
        targetObject.transform.position - transform.position) < effect_angle / 2f;
}
```

### Virtual Damage Methods

```csharp
public virtual void InitiateDamage() { }
public virtual void InitiateDamage(bool isBurst) { }
public virtual void InitiateDamage(ControllerBase character) { }
public virtual void InitiateDamage(ControllerBase character, bool isBurst) { }
```

---

## 3. Spell Encoding

**Source:** `/Assets/Scripts/SpellAttributes.cs` (16 lines)

### Spell Index Formula

```csharp
// 16-bit spell identifier
// Bits [15-5]: Element type (3 bits used, 8 possible)
// Bits [4-0]:  Spell type (5 bits, 32 possible per element)
public UInt16 GetSpellIndex()
{
    return (UInt16)((int)Elemental << 5 | spellType);
}
```

### Encoding Examples

| Element | Elemental Value | spellType | Binary | SpellIndex |
|---------|-----------------|-----------|--------|------------|
| Fire | 0 | 1 | `00000 00001` | 1 |
| Fire | 0 | 2 | `00000 00010` | 2 |
| Water | 1 | 1 | `00001 00001` | 33 |
| Water | 1 | 2 | `00001 00010` | 34 |
| Air | 2 | 1 | `00010 00001` | 65 |
| Earth | 3 | 1 | `00011 00001` | 97 |
| Ether | 4 | 1 | `00100 00001` | 129 |

### SpellProjectile

**Source:** `/Assets/Scripts/SpellProjectile.cs` (77 lines)

```csharp
public class SpellProjectile : Entity
{
    public SpellAttributes spellAttributes;
    public GameObject entityObject;
    private Spell activeSpell;

    public void InitializeSpellProjectile(Player sourcePlayer, Vector3 endLocation)
    {
        spellAttributes = GetComponent<SpellAttributes>();

        UniqueID = (UInt32)UnityEngine.Random.Range(1, 10000000);
        EntityType = spellAttributes.GetSpellIndex();  // ◄── Encoded spell ID
        EntityPlayer = sourcePlayer;
        FrameNumber = GameManager.serverTick;
        SourceLocation = sourcePlayer.pGameObject.transform.position;
        EntityEndLocation = endLocation;

        // Register with EntityManager
        GameManager.Instance.EntityManager.AddEntity(this);

        activeSpell = GetComponent<Spell>();
        activeSpell.spellEntity = this;
        activeSpell.Initialize();
    }

    public override bool Process(float deltaTime)
    {
        if (!activeSpell.Process(deltaTime))
        {
            Destroy(this.gameObject);
            return false;
        }
        return true;
    }

    // Unity collision callbacks
    private void OnTriggerEnter(Collider other)
    {
        if (other.tag != "Player") return;
        PlayerBase pb = other.GetComponent<PlayerBase>();
        if (pb == null || pb.character.player == EntityPlayer) return;

        Player p = pb.character.player;
        if (playersInside.Contains(p)) return;

        playersInside.Add(p);
        activeSpell.OnTriggerEnterPlayer(pb.character);
    }
}
```

### SpellCastAttributes (Client)

**Source:** `/Assets/Scripts/Entities/SpellCastAttributes.cs` (27 lines)

```csharp
public class SpellCastAttributes : MonoBehaviour
{
    public Elementals Elemental;
    public int spellType;
    public CastDetectionType detectionType;     // Circle, Cone, Box

    [EnumNamedArray(typeof(TrinityGods))]
    public float[] spellDistance;               // Per-god distance values

    [EnumNamedArray(typeof(TrinityGods))]
    public float[] effectAngle;                 // Per-god angle values

    public float minRange;
    public float maxRange;
    public float maxChannel;
    public float stamina;                       // Stamina cost
    public float willPower;                     // Willpower cost
    public float focusBarSegments;              // Focus cost

    public UInt16 GetSpellIndex()
    {
        return (UInt16)((int)Elemental << 5 | spellType);
    }
}
```

---

## 4. Fire Element

**Source:** `/Assets/Scripts/Spells/Fire.cs` (136 lines)

### Class Implementation

```csharp
public class Fire : Spell
{
    private List<Player> playersInZone = new List<Player>();

    // ═══════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════
    public override void Initialize()
    {
        base.Initialize();

        // Initial burst damage on spawn
        if (ShouldApplyBurst())
            InitiateDamage(true);

        UpdatePlayersInZoneImmediate();
    }

    // ═══════════════════════════════════════════════════════════════════
    // TARGET VALIDATION
    // ═══════════════════════════════════════════════════════════════════
    private bool IsValidTarget(Player p)
    {
        return p != null
            && p != spellEntity.EntityPlayer      // Not self
            && !p.IsDead()                        // Not dead
            && p.team != spellEntity.EntityPlayer.team;  // Enemy team
    }

    // ═══════════════════════════════════════════════════════════════════
    // DAMAGE APPLICATION
    // ═══════════════════════════════════════════════════════════════════
    public override void InitiateDamage(bool isBurst)
    {
        if (isBurst && !ShouldApplyBurst()) return;
        if (!isBurst && !ShouldApplyZone()) return;

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.FIRE,
            Component = isBurst ? AttackDamageComponent.SpellBurst
                               : AttackDamageComponent.SpellZone,
            sourcePlayer = spellEntity.EntityPlayer,
            damageType = DamageType.FIRE,
        };

        foreach (Player player in GetPlayersInSpellRange(spellDistance))
        {
            if (!IsValidTarget(player)) continue;
            if (!TargetWithinAngle(player.character.playerBase.ContactPoint, spellAngle))
                continue;

            var targetBase = player.character.playerBase;

            // ─────────────────────────────────────────────────────────────
            // Shield Check
            // ─────────────────────────────────────────────────────────────
            if (targetBase.activeElementalShield != null)
            {
                info.targetPlayer = player;
                var result = targetBase.activeElementalShield
                    .RegisterShieldHit(DamageType.FIRE, spellEntity, info);

                if (result.damagePassFraction <= 0f)
                {
                    // Fully blocked
                    player.notifyEvents.Enqueue(new NotifyEvent
                    {
                        notifyType = NotifyEvent.NotifyType.MELEE_IMPACT,
                        notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                    });
                    continue;
                }

                // Apply reduced damage
                float applied = (isBurst ? burstDamage : zoneDamage)
                              * result.damagePassFraction;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied, DamageType.FIRE);

                // Apply FireBurn effect
                if (ShouldApplyEffect())
                {
                    var burn = new FireBurn(
                        effectDuration, player, spellEntity.EntityPlayer,
                        effectDamage, spellEntity, effectTickInterval,
                        spellDistance, spellAngle
                    );
                    player.character.AddEffect(burn, true);
                }
            }
            else
            {
                // ─────────────────────────────────────────────────────────────
                // No Shield - Full Damage
                // ─────────────────────────────────────────────────────────────
                float applied = isBurst ? burstDamage : zoneDamage;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied, DamageType.FIRE);

                if (ShouldApplyEffect())
                {
                    var burn = new FireBurn(
                        effectDuration, player, spellEntity.EntityPlayer,
                        effectDamage, spellEntity, effectTickInterval,
                        spellDistance, spellAngle
                    );
                    player.character.AddEffect(burn, true);
                }
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    // FRAME PROCESSING
    // ═══════════════════════════════════════════════════════════════════
    public override bool Process(float deltaTime)
    {
        // Zone damage ticks
        if (ShouldApplyZone() && base.DPSCounter(deltaTime, spellTickInterval))
            InitiateDamage(false);

        DetectZoneEnterExitToApplyDOT();

        if (!base.Process(deltaTime))
            return false;

        return true;
    }

    // ═══════════════════════════════════════════════════════════════════
    // ZONE TRACKING
    // ═══════════════════════════════════════════════════════════════════
    private void DetectZoneEnterExitToApplyDOT()
    {
        // Snapshot current players in zone
        HashSet<Player> currentlyInZone = new HashSet<Player>();
        foreach (Player p in GetPlayersInSpellRange(spellDistance))
        {
            if (IsValidTarget(p) && TargetWithinAngle(
                p.character.playerBase.ContactPoint, spellAngle))
                currentlyInZone.Add(p);
        }

        // Track entries
        foreach (Player p in currentlyInZone)
        {
            if (!playersInZone.Contains(p))
                playersInZone.Add(p);
        }

        // Track exits
        foreach (Player p in new List<Player>(playersInZone))
        {
            if (!currentlyInZone.Contains(p))
                playersInZone.Remove(p);
        }
    }
}
```

### Fire Mechanics Summary

| Property | Description |
|----------|-------------|
| **Damage Type** | `DamageType.FIRE` |
| **Effect** | `FireBurn` (DoT while outside zone) |
| **Zone Behavior** | Players inside zone take zone damage; DoT pauses |
| **Exit Behavior** | DoT resumes when player leaves zone |

---

## 5. Water Element

**Source:** `/Assets/Scripts/Spells/Water.cs` (108 lines)

### Class Implementation

```csharp
public class Water : Spell
{
    [Header("Movement Settings")]
    public float moveSpeed;

    private List<Player> playerEffectList = new List<Player>();

    // ═══════════════════════════════════════════════════════════════════
    // PROJECTILE MOVEMENT
    // ═══════════════════════════════════════════════════════════════════
    public override bool Process(float deltaTime)
    {
        if (!base.Process(deltaTime))
            return false;

        // Move projectile forward
        transform.position += (transform.forward * moveSpeed) * deltaTime;
        return true;
    }

    // ═══════════════════════════════════════════════════════════════════
    // DAMAGE APPLICATION
    // ═══════════════════════════════════════════════════════════════════
    public override void InitiateDamage(ControllerBase character, bool isBurst)
    {
        if (isBurst && !ShouldApplyBurst()) return;
        if (!isBurst && !ShouldApplyZone()) return;
        if (character.player.team == spellEntity.EntityPlayer.team) return;
        if (character.player.IsDead()) return;

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.WATER,
            Component = isBurst ? AttackDamageComponent.SpellBurst
                               : AttackDamageComponent.SpellZone,
            sourcePlayer = spellEntity.EntityPlayer,
            targetPlayer = character.player,
            damageType = DamageType.WATER,
        };

        // First hit only (prevents multi-hit)
        if (!playerEffectList.Contains(character.player))
        {
            playerEffectList.Add(character.player);
            var targetBase = character.player.character.playerBase;

            if (targetBase.activeElementalShield != null)
            {
                var result = targetBase.activeElementalShield
                    .RegisterShieldHit(DamageType.WATER, spellEntity, info);

                if (result.damagePassFraction <= 0f)
                {
                    character.player.notifyEvents.Enqueue(new NotifyEvent()
                    {
                        notifyType = NotifyEvent.NotifyType.MELEE_IMPACT,
                        notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                    });
                }
                else
                {
                    float applied = (isBurst ? burstDamage : zoneDamage)
                                  * result.damagePassFraction;
                    targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied,
                                            DamageType.WATER);
                }
            }
            else
            {
                float applied = isBurst ? burstDamage : zoneDamage;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied,
                                        DamageType.WATER);
            }
        }

        // ─────────────────────────────────────────────────────────────────
        // PUSHBACK EFFECT
        // ─────────────────────────────────────────────────────────────────
        if (character.DoWaterPushback(info, spellEntity))
        {
            character.player.pGameObject.GetComponent<CharacterController>()
                .Move(transform.forward * moveSpeed * Time.deltaTime);
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    // COLLISION HANDLER
    // ═══════════════════════════════════════════════════════════════════
    public override void OnTriggerEnterPlayer(ControllerBase character)
    {
        InitiateDamage(character, true);  // Burst on contact
    }

    // ═══════════════════════════════════════════════════════════════════
    // CLEANUP
    // ═══════════════════════════════════════════════════════════════════
    private void OnDestroy()
    {
        // Return pushed players to Pushback_Land state
        foreach (Player player in playerEffectList)
        {
            if (player.character.stateManager.GetState() == FSM.StateType.Water_Pushback)
            {
                player.character.stateManager.ChangeState(FSM.StateType.Pushback_Land);
            }
        }
    }
}
```

### Water Mechanics Summary

| Property | Description |
|----------|-------------|
| **Damage Type** | `DamageType.WATER` |
| **Movement** | Projectile moves forward at `moveSpeed` |
| **Effect** | Pushback (moves target with projectile) |
| **State Change** | Target enters `Water_Pushback` state |
| **Cleanup** | Targets return to `Pushback_Land` on spell destroy |

---

## 6. Air Element

**Source:** `/Assets/Scripts/Spells/Air.cs` (86 lines)

### Class Implementation

```csharp
public class Air : Spell
{
    public override void Initialize()
    {
        base.Initialize();
        if (ShouldApplyBurst())
            InitiateDamage(true);
    }

    public override bool Process(float deltaTime)
    {
        // Zone damage ticks
        if (ShouldApplyZone() && base.DPSCounter(deltaTime, spellTickInterval))
        {
            InitiateDamage(false);
        }

        if (!base.Process(deltaTime))
            return false;

        return true;
    }

    public override void InitiateDamage(bool isBurst)
    {
        if (isBurst && !ShouldApplyBurst()) return;
        if (!isBurst && !ShouldApplyZone()) return;

        Player[] playerList = GetPlayersInSpellRange(spellDistance);

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.AIR,
            Component = isBurst ? AttackDamageComponent.SpellBurst
                               : AttackDamageComponent.SpellZone,
            sourcePlayer = spellEntity.EntityPlayer,
            damageType = DamageType.AIR,
        };

        foreach (Player player in playerList)
        {
            if (player == spellEntity.EntityPlayer) continue;
            if (player.IsDead()) continue;
            if (player.team == spellEntity.EntityPlayer.team) continue;

            info.targetPlayer = player;
            var targetBase = player.character.playerBase;

            if (targetBase.activeElementalShield != null)
            {
                var result = targetBase.activeElementalShield
                    .RegisterShieldHit(DamageType.AIR, spellEntity, info);

                if (result.damagePassFraction <= 0f)
                {
                    player.notifyEvents.Enqueue(new NotifyEvent()
                    {
                        notifyType = NotifyEvent.NotifyType.MELEE_IMPACT,
                        notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                    });
                    continue;
                }

                float applied = (isBurst ? burstDamage : zoneDamage)
                              * result.damagePassFraction;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied, DamageType.AIR);

                // Apply slow effect
                if (ShouldApplyEffect())
                {
                    var airSlowEffect = new AirSlow(
                        effectDuration, player, spellEntity.EntityPlayer,
                        effectDamage, spellEntity, effectTickInterval
                    );
                    player.character.AddEffect(airSlowEffect, true);
                }
            }
            else
            {
                float applied = isBurst ? burstDamage : zoneDamage;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied, DamageType.AIR);

                if (ShouldApplyEffect())
                {
                    var airSlowEffect = new AirSlow(
                        effectDuration, player, spellEntity.EntityPlayer,
                        effectDamage, spellEntity, effectTickInterval
                    );
                    player.character.AddEffect(airSlowEffect, true);
                }
            }
        }
    }
}
```

### Air Mechanics Summary

| Property | Description |
|----------|-------------|
| **Damage Type** | `DamageType.AIR` |
| **Effect** | `AirSlow` (movement speed reduction) |
| **Zone Type** | Area effect (radius-based, no angle) |

---

## 7. Earth Element

**Source:** `/Assets/Scripts/Spells/Earth.cs` (88 lines)

### Class Implementation

```csharp
public class Earth : Spell
{
    public override void Initialize()
    {
        base.Initialize();
        if (ShouldApplyBurst())
            InitiateDamage(true);
    }

    public override bool Process(float deltaTime)
    {
        if (ShouldApplyZone() && base.DPSCounter(deltaTime, spellTickInterval))
        {
            InitiateDamage(false);
        }

        if (!base.Process(deltaTime))
            return false;

        return true;
    }

    public override void InitiateDamage(bool isBurst)
    {
        if (isBurst && !ShouldApplyBurst()) return;
        if (!isBurst && !ShouldApplyZone()) return;

        Player[] playerList = GetPlayersInSpellRange(spellDistance);

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.EARTH,
            Component = isBurst ? AttackDamageComponent.SpellBurst
                               : AttackDamageComponent.SpellZone,
            sourcePlayer = spellEntity.EntityPlayer,
            damageType = DamageType.EARTH,
        };

        foreach (Player player in playerList)
        {
            if (player == spellEntity.EntityPlayer) continue;
            if (player.IsDead()) continue;
            if (player.team == spellEntity.EntityPlayer.team) continue;

            info.targetPlayer = player;
            var targetBase = player.character.playerBase;

            if (targetBase.activeElementalShield != null)
            {
                var result = targetBase.activeElementalShield
                    .RegisterShieldHit(DamageType.EARTH, spellEntity, info);

                if (result.damagePassFraction <= 0f)
                {
                    player.notifyEvents.Enqueue(new NotifyEvent()
                    {
                        notifyType = NotifyEvent.NotifyType.MELEE_IMPACT,
                        notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                    });
                    continue;
                }

                float applied = (isBurst ? burstDamage : zoneDamage)
                              * result.damagePassFraction;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied, DamageType.EARTH);

                // STUN ONLY ON BURST
                if (isBurst && ShouldApplyEffect())
                {
                    Effects stunEffect = new EarthStun(
                        effectDuration, player, spellEntity.EntityPlayer,
                        effectDamage, spellEntity, effectTickInterval
                    );
                    player.character.AddEffect(stunEffect, true);
                    player.character.stateManager.ChangeState(FSM.StateType.Stun);
                }
            }
            else
            {
                float applied = isBurst ? burstDamage : zoneDamage;
                targetBase.DoSpellDamage(spellEntity.EntityPlayer, applied, DamageType.EARTH);

                if (isBurst && ShouldApplyEffect())
                {
                    Effects stunEffect = new EarthStun(
                        effectDuration, player, spellEntity.EntityPlayer,
                        effectDamage, spellEntity, effectTickInterval
                    );
                    player.character.AddEffect(stunEffect, true);
                    player.character.stateManager.ChangeState(FSM.StateType.Stun);
                }
            }
        }
    }
}
```

### Earth Mechanics Summary

| Property | Description |
|----------|-------------|
| **Damage Type** | `DamageType.EARTH` |
| **Effect** | `EarthStun` (ONLY on burst, not zone ticks) |
| **State Change** | Target enters `FSM.StateType.Stun` |
| **Zone Ticks** | Deal damage but do NOT stun |

---

## 8. Ether Element

**Source:** `/Assets/Scripts/Spells/Ether.cs` (82 lines)

### Class Implementation

```csharp
public class Ether : Spell
{
    public override void Initialize()
    {
        base.Initialize();
        if (ShouldApplyBurst())
            InitiateDamage(true);
    }

    public override bool Process(float deltaTime)
    {
        if (ShouldApplyZone() && base.DPSCounter(deltaTime, spellTickInterval))
        {
            InitiateDamage(false);
        }

        if (!base.Process(deltaTime))
            return false;

        return true;
    }

    public override void InitiateDamage(bool isBurst)
    {
        if (isBurst && !ShouldApplyBurst()) return;
        if (!isBurst && !ShouldApplyZone()) return;

        Player[] playerList = GetPlayersInSpellRange(spellDistance);

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.ETHER,
            Component = isBurst ? AttackDamageComponent.SpellBurst
                               : AttackDamageComponent.SpellZone,
            damageType = DamageType.ETHER,
            sourcePlayer = spellEntity.EntityPlayer,
        };

        foreach (Player player in playerList)
        {
            if (player == spellEntity.EntityPlayer) continue;
            if (player.IsDead()) continue;
            if (player.team == spellEntity.EntityPlayer.team) continue;

            info.targetPlayer = player;

            if (player.character.playerBase.activeElementalShield != null)
            {
                var result = player.character.playerBase.activeElementalShield
                    .RegisterShieldHit(DamageType.ETHER, spellEntity, info);

                if (result.damagePassFraction <= 0f)
                {
                    player.notifyEvents.Enqueue(new NotifyEvent()
                    {
                        notifyType = NotifyEvent.NotifyType.MELEE_IMPACT,
                        notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                    });
                    continue;
                }

                float applied = (isBurst ? burstDamage : zoneDamage)
                              * result.damagePassFraction;
                player.character.playerBase.DoSpellDamage(
                    spellEntity.EntityPlayer, applied, DamageType.ETHER);

                // Apply mute effect
                if (ShouldApplyEffect())
                {
                    var muteEffect = new EtherMute(effectDuration, player, spellEntity);
                    player.character.AddEffect(muteEffect, true);
                }
            }
            else
            {
                float applied = isBurst ? burstDamage : zoneDamage;
                player.character.playerBase.DoSpellDamage(
                    spellEntity.EntityPlayer, applied, DamageType.ETHER);

                if (ShouldApplyEffect())
                {
                    var muteEffect = new EtherMute(effectDuration, player, spellEntity);
                    player.character.AddEffect(muteEffect, true);
                }
            }
        }
    }
}
```

### Ether Mechanics Summary

| Property | Description |
|----------|-------------|
| **Damage Type** | `DamageType.ETHER` |
| **Effect** | `EtherMute` (silences abilities) |
| **Mute Check** | `Player.IsMuted()` checks for active effect |

---

## 9. Effects System

### Base Effects Class

**Source:** `/Assets/Scripts/Spells/Effects/Effects.cs` (69 lines)

```csharp
public class Effects
{
    // ═══════════════════════════════════════════════════════════════════
    // EFFECT TYPE ENUM
    // ═══════════════════════════════════════════════════════════════════
    public enum EffectType
    {
        EFFECT_NONE,
        EFFECT_FIREDAMAGE,      // Burning DoT
        EFFECT_AIRSLOW,         // Movement slow
        EFFECT_EARTHSTUN,       // Stun (locked in place)
        EFFECT_ETHERMUTE,       // Silenced (can't cast abilities)
        EFFECT_IMPAIR,          // Reduced accuracy
        EFFECT_MAIM,            // Reduced damage
        EFFECT_THIRDEYE,        // Ultimate buff (Shiva)
        EFFECT_SHIVAASTRA       // Shiva ultimate burn
    }

    // ═══════════════════════════════════════════════════════════════════
    // PROPERTIES
    // ═══════════════════════════════════════════════════════════════════
    public EffectType type;
    public float duration;
    private float currentDuration;
    private float DPSTimer;

    public Player effectPlayer;         // Target of the effect
    public Player sourcePlayer;         // Who applied the effect
    public Entity sourceEntity;         // Source spell/projectile
    public DamageType damageType;

    public float tickInterval;
    public float damagePerTick;

    // ═══════════════════════════════════════════════════════════════════
    // PROCESSING
    // ═══════════════════════════════════════════════════════════════════
    public virtual bool Process(float deltaTime)
    {
        currentDuration += deltaTime;
        if (currentDuration >= duration)
        {
            return false;  // Effect expired
        }
        return true;
    }

    public bool DPSCounter(float deltaTime, float dpsTick)
    {
        DPSTimer += deltaTime;
        if (DPSTimer >= dpsTick)
        {
            DPSTimer -= dpsTick;
            return true;  // Time to tick
        }
        return false;
    }

    public void ResetDuration()
    {
        currentDuration = 0;
        DPSTimer = 0f;  // Prevents immediate tick after refresh
    }
}
```

---

### FireBurn Effect

**Source:** `/Assets/Scripts/Spells/Effects/FireBurn.cs` (97 lines)

```csharp
public class FireBurn : Effects
{
    private float effect_distance;
    private float effect_angle;

    public FireBurn(float _duration, Player _effectPlayer, Player _sourcePlayer,
                    float _burnDamage, Entity _sourceEntity, float _tickInterval,
                    float _effectDistance, float _effectAngle)
    {
        type           = EffectType.EFFECT_FIREDAMAGE;
        damageType     = DamageType.FIRE;
        duration       = _duration;
        effectPlayer   = _effectPlayer;
        sourcePlayer   = _sourcePlayer;
        sourceEntity   = _sourceEntity;
        damagePerTick  = _burnDamage;
        tickInterval   = Mathf.Max(0.01f, _tickInterval);
        effect_distance = _effectDistance;
        effect_angle    = _effectAngle;
    }

    public override bool Process(float deltaTime)
    {
        // Expire if target invalid
        if (effectPlayer == null || effectPlayer.IsDead())
            return false;

        // PAUSE while inside source zone
        if (IsPlayerInsideSourceZone())
        {
            ResetDuration();  // Keep effect alive but don't tick
            return true;
        }

        // Outside zone - apply DoT ticks
        if (DPSCounter(deltaTime, tickInterval))
            ApplyTick();

        return base.Process(deltaTime);
    }

    private bool IsPlayerInsideSourceZone()
    {
        if (sourceEntity == null) return false;  // Spell expired

        var srcPos = sourceEntity.transform.position;
        var tgtPos = effectPlayer.character.playerBase.ContactPoint.transform.position;

        // Distance check
        if ((tgtPos - srcPos).magnitude > effect_distance) return false;

        // Angle check (cone)
        if (Vector3.Angle(sourceEntity.transform.forward, tgtPos - srcPos)
            > effect_angle / 2f) return false;

        return true;  // Inside zone
    }

    private void ApplyTick()
    {
        var targetBase = effectPlayer.character.playerBase;

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.FIRE,
            Component = AttackDamageComponent.SpellDoT,
            sourcePlayer = sourcePlayer,
            targetPlayer = effectPlayer,
            effectType = type,
            damageType = damageType,
        };

        if (targetBase.activeElementalShield != null)
        {
            var result = targetBase.activeElementalShield
                .RegisterShieldHit(damageType, sourceEntity, info);

            if (result.damagePassFraction <= 0f)
            {
                effectPlayer.notifyEvents.Enqueue(new NotifyEvent
                {
                    notifyType = NotifyEvent.NotifyType.MELEE_IMPACT,
                    notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                });
                return;
            }

            float applied = damagePerTick * result.damagePassFraction;
            targetBase.DoSpellDamage(sourcePlayer, applied, damageType, type);
        }
        else
        {
            targetBase.DoSpellDamage(sourcePlayer, damagePerTick, damageType, type);
        }
    }
}
```

**Key Mechanic:** FireBurn PAUSES while the player is inside the source fire zone. The DoT only ticks when the player leaves the zone.

---

### AirSlow Effect

**Source:** `/Assets/Scripts/Spells/Effects/AirSlow.cs` (70 lines)

```csharp
public class AirSlow : Effects
{
    public AirSlow(float _duration, Player _effectPlayer, Player _sourcePlayer,
                   float _slowDamage, Entity _sourceEntity, float _tickInterval)
    {
        type         = EffectType.EFFECT_AIRSLOW;
        damageType   = DamageType.AIR;
        duration     = _duration;
        effectPlayer = _effectPlayer;
        sourcePlayer = _sourcePlayer;
        sourceEntity = _sourceEntity;
        damagePerTick = _slowDamage;
        tickInterval  = _tickInterval;
    }

    public override bool Process(float deltaTime)
    {
        if (effectPlayer == null || effectPlayer.IsDead())
            return false;

        // Apply damage ticks if configured
        if (damagePerTick > 0f)
        {
            if (DPSCounter(deltaTime, tickInterval))
                ApplyTick();
        }

        return base.Process(deltaTime);
    }

    private void ApplyTick()
    {
        var targetBase = effectPlayer.character.playerBase;

        var info = new ElementalShield.AttackInfo
        {
            SpellElement = Elementals.AIR,
            Component = AttackDamageComponent.SpellDoT,
            targetPlayer = effectPlayer,
            sourcePlayer = sourcePlayer,
            effectType = EffectType.EFFECT_AIRSLOW,
            damageType = damageType,
        };

        if (targetBase.activeElementalShield != null)
        {
            var result = targetBase.activeElementalShield
                .RegisterShieldHit(DamageType.AIR, sourceEntity, info);

            if (result.damagePassFraction <= 0f)
            {
                effectPlayer.notifyEvents.Enqueue(new NotifyEvent
                {
                    notifyType  = NotifyEvent.NotifyType.MELEE_IMPACT,
                    notifyValue = (byte)ImpactIndicatorType.ShieldBlock
                });
                return;
            }

            float applied = damagePerTick * result.damagePassFraction;
            targetBase.DoSpellDamage(sourcePlayer, applied, damageType, type);
        }
        else
        {
            targetBase.DoSpellDamage(sourcePlayer, damagePerTick, damageType, type);
        }
    }
}
```

---

### EarthStun Effect

**Source:** `/Assets/Scripts/Spells/Effects/EarthStun.cs` (91 lines)

```csharp
public class EarthStun : Effects
{
    // Full constructor (from spell)
    public EarthStun(float _duration, Player _effectPlayer, Player _sourcePlayer,
                     float _damagePerTick, Entity _sourceEntity, float _tickInterval)
    {
        type = EffectType.EFFECT_EARTHSTUN;
        damageType = DamageType.NONE;  // Stun doesn't deal damage type
        duration = _duration;
        effectPlayer = _effectPlayer;
        sourcePlayer = _sourcePlayer;
        damagePerTick = _damagePerTick;
        sourceEntity = _sourceEntity;
        tickInterval = _tickInterval;
    }

    // Simple constructor (for manual stuns)
    public EarthStun(float _duration, Player _effectPlayer)
    {
        type = EffectType.EFFECT_EARTHSTUN;
        damageType = DamageType.NONE;
        duration = _duration;
        effectPlayer = _effectPlayer;
    }

    public override bool Process(float deltaTime)
    {
        if (effectPlayer == null || effectPlayer.IsDead())
            return false;

        // Effect ends early if player breaks out of stun
        if (effectPlayer.character.stateManager.GetState() != FSM.StateType.Stun)
            return false;

        // Apply damage ticks if configured
        if (damagePerTick > 0f)
        {
            if (DPSCounter(deltaTime, tickInterval))
                ApplyTick();
        }

        if (!base.Process(deltaTime))
        {
            // Effect expired - return player to Idle
            if (effectPlayer != null && !effectPlayer.IsDead())
            {
                effectPlayer.character.stateManager.ChangeState(FSM.StateType.Idle);
            }
            return false;
        }

        return true;
    }
}
```

**Key Mechanic:** EarthStun automatically returns the player to `Idle` state when the effect expires.

---

### EtherMute Effect

**Source:** `/Assets/Scripts/Spells/Effects/EtherMute.cs` (67 lines)

```csharp
public class EtherMute : Effects
{
    public EtherMute(float _duration, Player _effectPlayer, Entity _sourceEntity)
    {
        type = EffectType.EFFECT_ETHERMUTE;
        duration = _duration;
        effectPlayer = _effectPlayer;
        sourceEntity = _sourceEntity;
    }

    public override bool Process(float deltaTime)
    {
        if (damagePerTick > 0f)
        {
            if (DPSCounter(deltaTime, tickInterval))
                ApplyTick();
        }

        return base.Process(deltaTime);
    }
}
```

**Mute Check in Player:**
```csharp
public bool IsMuted()
{
    if (impactEffectsList != null)
    {
        if (impactEffectsList.ContainsKey(ImpactIndicatorType.Mute))
            return true;
    }
    return false;
}
```

---

### Impair Effect

**Source:** `/Assets/Scripts/Spells/Effects/Impair.cs` (23 lines)

```csharp
public class Impair : Effects
{
    public Impair(float _duration, Player _effectPlayer, Player _sourcePlayer)
    {
        type = EffectType.EFFECT_IMPAIR;
        duration = _duration;
        effectPlayer = _effectPlayer;
        sourcePlayer = _sourcePlayer;
    }

    public override bool Process(float deltaTime)
    {
        return base.Process(deltaTime);
    }
}
```

---

### Maim Effect

**Source:** `/Assets/Scripts/Spells/Effects/Maim.cs` (23 lines)

```csharp
public class Maim : Effects
{
    public Maim(float _duration, Player _effectPlayer, Player _sourcePlayer)
    {
        type = EffectType.EFFECT_MAIM;
        duration = _duration;
        effectPlayer = _effectPlayer;
        sourcePlayer = _sourcePlayer;
    }

    public override bool Process(float deltaTime)
    {
        return base.Process(deltaTime);
    }
}
```

---

### ThirdEye Effect

**Source:** `/Assets/Scripts/Spells/Effects/ThirdEye.cs` (28 lines)

```csharp
public class ThirdEye : Effects
{
    private int tickCount;

    public ThirdEye(float _duration)
    {
        type = EffectType.EFFECT_THIRDEYE;
        duration = _duration;
        tickCount = (duration / (FInt)GameManager.clientTickRateMS).ToInt();
    }

    public bool ThirdEyeTick()
    {
        if (tickCount > 0)
        {
            tickCount--;
        }
        return tickCount == 0 ? false : true;
    }

    public override bool Process(float deltaTime)
    {
        return true;  // Never expires via normal process
    }
}
```

**Key Mechanic:** ThirdEye uses tick-based duration rather than time-based. Uses `FInt` (fixed-point integer) for deterministic network sync.

---

### ShivaAstraBurn Effect

**Source:** `/Assets/Scripts/Spells/Effects/ShivaAstraBurn.cs` (33 lines)

```csharp
public class ShivaAstraBurn : Effects
{
    float burn_damage;
    float dpsTick;

    public ShivaAstraBurn(float _duration, Player _effectPlayer,
                          float _burn_damage, float _dpsTick, Entity _sourceEntity)
    {
        type = EffectType.EFFECT_SHIVAASTRA;
        damageType = DamageType.ASTRA_SHIVA;
        duration = _duration;
        effectPlayer = _effectPlayer;
        burn_damage = _burn_damage;
        sourceEntity = _sourceEntity;
        dpsTick = _dpsTick;
    }

    public override bool Process(float deltaTime)
    {
        // Apply damage ticks
        if (base.DPSCounter(deltaTime, dpsTick))
        {
            effectPlayer.character.playerBase.DoAstraDamage(
                effectPlayer, burn_damage, damageType);
        }

        return base.Process(deltaTime);
    }
}
```

**Key Mechanic:** ShivaAstraBurn uses `DoAstraDamage()` instead of `DoSpellDamage()` - bypasses normal spell damage reduction.

---

## 10. Elemental Shield System

**Source:** `/Assets/Scripts/Player/ElementalShield.cs` (436 lines)

### Shield Properties

```csharp
public class ElementalShield
{
    public byte shieldButtonIndex;
    public Elemental shieldElemental;
    private float shieldDuration;
    private List<Entity> registeredEntities = new List<Entity>();

    public float shieldHitCount;
    private const float BaseShieldIntegrity = 3.0f;  // Max hits before break

    public ElementalShield(byte buttonIndex, Elemental _shieldElemental)
    {
        shieldButtonIndex = buttonIndex;
        shieldElemental = _shieldElemental;
    }

    public bool Process(float deltaTime)
    {
        shieldDuration++;
        if (shieldDuration >= 10 / deltaTime)  // ~10 second max duration
            return false;
        if (shieldHitCount >= BaseShieldIntegrity)  // Broken
            return false;
        return true;
    }
}
```

### AttackInfo Structure

```csharp
public class AttackInfo
{
    public WeaponType Weapon = WeaponType.None;
    public AttackCharge Charge = AttackCharge.Basic;
    public Elementals? SpellElement;
    public AttackDamageComponent Component = AttackDamageComponent.Physical;
    public CoatedType CoatedDamageType = CoatedType.None;
    public bool IsThirdEyeActive = false;
    public Player targetPlayer;
    public Player sourcePlayer;
    public DamageType damageType = DamageType.NONE;
    public Effects.EffectType effectType = Effects.EffectType.EFFECT_NONE;
}
```

### RegisterShieldResult Structure

```csharp
public class RegisterShieldResult
{
    public bool result;                    // Shield consumed/broken or attack passed
    public float integrityDamageApplied;   // Integrity damage dealt this hit
    public float damagePassFraction;       // Fraction of damage that passed (0..1)
}
```

### Elemental Interaction Matrix

```csharp
// Interaction outcomes
public enum Interaction
{
    Nullify,    // 0% damage, 0 integrity damage
    Vulnerable, // 100% damage, 1.0 integrity multiplier
    Mitigate    // 50% damage, 0.5 integrity multiplier
}
```

#### Shield vs Spell Matrix

| Spell ▼ / Shield ► | Fire | Water | Air | Earth | Ether |
|-------------------|------|-------|-----|-------|-------|
| **Fire** | Mitigate | Nullify | Vulnerable | Mitigate | Mitigate |
| **Water** | Vulnerable | Mitigate | Mitigate | Nullify | Mitigate |
| **Air** | Nullify | Mitigate | Mitigate | Mitigate | Vulnerable |
| **Earth** | Mitigate | Vulnerable | Mitigate | Mitigate | Nullify |
| **Ether** | Mitigate | Mitigate | Nullify | Vulnerable | Mitigate |

**Elemental Wheel:**
```
        Fire
       /    \
    Air      Water
       \    /
        ─┼─
       /    \
   Ether    Earth
       \    /
```

- Fire > Air (Air Vulnerable to Fire)
- Air > Ether (Ether Vulnerable to Air)
- Ether > Earth (Earth Vulnerable to Ether)
- Earth > Water (Water Vulnerable to Earth)
- Water > Fire (Fire Vulnerable to Water)

### Physical Attack Shield Handling

```csharp
private RegisterShieldResult HandlePhysicalAttack(AttackInfo attack,
    Entity sourceEntity, bool isNewEntity, RegisterShieldResult returnResult)
{
    float passFraction = 0f;
    float integrityDamage = 0f;
    Elementals shieldElem = shieldElemental.GetElemental();

    switch (attack.Weapon)
    {
        case WeaponType.Sword:
            // Through-Reduced vs Fire/Water, Blocked vs Air/Earth/Ether
            passFraction = (shieldElem == Elementals.FIRE ||
                           shieldElem == Elementals.WATER) ? 0.5f : 0f;
            integrityDamage = 0f;
            break;

        case WeaponType.Axe:
            // Complex rules for Axe
            passFraction = (shieldElem == Elementals.FIRE ||
                           shieldElem == Elementals.WATER ||
                           shieldElem == Elementals.AIR) ? 0.5f : 0f;
            integrityDamage = (shieldElem == Elementals.WATER ||
                              shieldElem == Elementals.AIR ||
                              shieldElem == Elementals.EARTH ||
                              shieldElem == Elementals.ETHER) ? 0.75f : 0f;
            if (shieldElem == Elementals.EARTH || shieldElem == Elementals.ETHER)
                passFraction = 0f;
            break;

        case WeaponType.Bow:
            if (attack.Charge == AttackCharge.Basic)
            {
                // Basic: Through-Full vs Fire, Through-Reduced vs Water/Air
                passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                               (shieldElem == Elementals.WATER ||
                                shieldElem == Elementals.AIR) ? 0.5f : 0f;
            }
            else  // Charged
            {
                passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                               (shieldElem == Elementals.WATER) ? 0.5f :
                               (shieldElem == Elementals.AIR) ? 1f : 0f;
                integrityDamage = (shieldElem == Elementals.WATER ||
                                  shieldElem == Elementals.AIR) ? 0.5f : 0f;
            }
            break;

        case WeaponType.Chakra:
            if (attack.Charge == AttackCharge.Basic)
            {
                passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                               (shieldElem == Elementals.WATER) ? 0.5f : 0f;
            }
            else  // Charged
            {
                passFraction = (shieldElem == Elementals.FIRE) ? 1f :
                               (shieldElem == Elementals.WATER ||
                                shieldElem == Elementals.AIR) ? 0.5f : 0f;
            }
            break;

        case WeaponType.Magic:
            // Through-Reduced vs most, Blocked vs Water
            passFraction = (shieldElem == Elementals.WATER) ? 0f : 0.5f;
            integrityDamage = 0.5f;
            break;
    }

    // Third Eye doubles/quadruples integrity damage
    if (integrityDamage > 0f && attack.IsThirdEyeActive)
        integrityDamage *= attack.Charge == AttackCharge.Charged ? 4f : 2f;

    returnResult.damagePassFraction = passFraction;
    if (integrityDamage > 0f)
        ApplyIntegrityDamage(integrityDamage, returnResult, attack);

    return returnResult;
}
```

### Weapon vs Shield Matrix

| Weapon | Fire | Water | Air | Earth | Ether |
|--------|------|-------|-----|-------|-------|
| **Sword** | 50% pass | 50% pass | Blocked | Blocked | Blocked |
| **Axe** | 50% pass, 0 integ | 50% pass, 0.75 integ | 50% pass, 0.75 integ | Blocked, 0.75 integ | Blocked, 0.75 integ |
| **Bow Basic** | 100% pass | 50% pass | 50% pass | Blocked | Blocked |
| **Bow Charged** | 100% pass | 50% pass, 0.5 integ | 100% pass, 0.5 integ | Blocked | Blocked |
| **Chakra Basic** | 100% pass | 50% pass | Blocked | Blocked | Blocked |
| **Chakra Charged** | 100% pass | 50% pass | 50% pass | Blocked | Blocked |
| **Magic** | 50% pass, 0.5 integ | Blocked, 0.5 integ | 50% pass, 0.5 integ | 50% pass, 0.5 integ | 50% pass, 0.5 integ |

### Charged Spell Overrides

```csharp
if (attack.Charge == AttackCharge.Charged)
{
    // Charged spells can break through disadvantaged matchups
    if (spell == Elementals.ETHER && shieldElem == Elementals.EARTH)
    {
        burstFraction = 1f; statusFraction = 1f;
    }
    else if (spell == Elementals.AIR && shieldElem == Elementals.ETHER)
    {
        burstFraction = 1f; statusFraction = 1f;
    }
    else if (spell == Elementals.FIRE && shieldElem == Elementals.AIR)
    {
        burstFraction = 1f; statusFraction = 0.5f;
    }
    else if (spell == Elementals.WATER && shieldElem == Elementals.FIRE)
    {
        burstFraction = 1f; statusFraction = 1f;
    }
    else if (spell == Elementals.EARTH && shieldElem == Elementals.WATER)
    {
        burstFraction = 1f; statusFraction = 1f;
    }
}
```

### Astra Attack Handling

```csharp
private RegisterShieldResult HandleAstraAttack(AttackInfo attack,
    Entity sourceEntity, bool isNewEntity, RegisterShieldResult returnResult)
{
    // All Astras INSTANTLY DESTROY shield
    shieldHitCount = BaseShieldIntegrity;
    returnResult.result = true;

    Utils.SendLogData(attack.targetPlayer, Utils.CombatLogType.SHIELD_BREAK,
        attack.sourcePlayer, attack.damageType, Effects.EffectType.EFFECT_NONE,
        0, BaseShieldIntegrity - shieldHitCount);

    return returnResult;
}
```

---

## 11. Spell Enums

### Elementals

```csharp
public enum Elementals
{
    FIRE = 0,
    WATER = 1,
    AIR = 2,
    ETHER = 3,
    EARTH = 4
}
```

### SpellSubType

```csharp
public enum SpellSubType
{
    INSTANT,        // Immediate cast
    CHANNELING,     // Held down continuous
    CHARGED,        // Hold to charge, release to cast
    TRAPS           // Placed on ground
}
```

### RangeType

```csharp
public enum RangeType
{
    CLOSE_RANGE,
    LONG_RANGE
}
```

### LevelType

```csharp
public enum LevelType
{
    Level1,
    Level2,
    Level3
}
```

### SpellDamageMode

```csharp
public enum SpellDamageMode
{
    BurstOnly,          // Only burst on cast
    ZoneOnly,           // Only repeated zone ticks
    EffectOnly,         // Only effect/DoT/status (no burst/zone)
    BurstAndZone,       // Burst + zone
    BurstAndEffect,     // Burst + effect
    ZoneAndEffect,      // Zone + effect
    BurstZoneAndEffect  // All three
}
```

### CastDetectionType

```csharp
public enum CastDetectionType
{
    Circle = 0,     // Radius-based area
    Cone,           // Cone/angle-based
    Box             // Rectangle/box area
}
```

### AttackDamageComponent

```csharp
public enum AttackDamageComponent
{
    Physical,       // Melee/ranged weapon
    Astra,          // Ultimate ability
    SpellBurst,     // Single big burst
    SpellZone,      // Zone ticks
    SpellDoT        // Effect DoT ticks
}
```

### Interaction

```csharp
public enum Interaction
{
    Nullify,        // Completely blocked (0% damage)
    Vulnerable,     // Full damage (100%)
    Mitigate        // Reduced damage (50%)
}
```

### DamageType (Spell-Related)

```csharp
public enum DamageType
{
    NONE,
    MELEE,
    FIRE,
    WATER,
    AIR,
    EARTH,
    ETHER,
    ASTRA_SHIVA,
    ASTRA_BRAHMA,
    ASTRA_VISHNU,
    AXETHROW
}
```

### Effects.EffectType

```csharp
public enum EffectType
{
    EFFECT_NONE,
    EFFECT_FIREDAMAGE,      // Fire DoT
    EFFECT_AIRSLOW,         // Air slow
    EFFECT_EARTHSTUN,       // Earth stun
    EFFECT_ETHERMUTE,       // Ether silence
    EFFECT_IMPAIR,          // Reduced accuracy
    EFFECT_MAIM,            // Reduced damage
    EFFECT_THIRDEYE,        // Shiva ultimate buff
    EFFECT_SHIVAASTRA       // Shiva ultimate burn
}
```

---

## Quick Reference

### Spell Type Summary

| Element | Effect | State Change | Special Behavior |
|---------|--------|--------------|------------------|
| **Fire** | FireBurn (DoT) | None | DoT pauses while in zone |
| **Water** | Pushback | Water_Pushback → Pushback_Land | Projectile movement |
| **Air** | AirSlow | None | Area effect |
| **Earth** | EarthStun | Stun → Idle | Stun on burst only |
| **Ether** | EtherMute | None | Silences abilities |

### Effect Stacking

| Effect | Stackable | Refreshable | Notes |
|--------|-----------|-------------|-------|
| FireBurn | No | Yes | Duration reset on re-apply |
| AirSlow | No | Yes | Duration reset on re-apply |
| EarthStun | No | Yes | State-locked while active |
| EtherMute | No | Yes | Blocks ability casting |
| Impair | No | Yes | Status effect only |
| Maim | No | Yes | Status effect only |
| ThirdEye | No | No | Tick-based duration |
| ShivaAstraBurn | No | No | Astra damage type |

---

*Document generated from source code analysis*
*Files analyzed: 16*
*Total lines: ~1,200*
