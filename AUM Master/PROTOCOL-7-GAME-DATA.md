# AUM Protocol Documentation: Game Data Systems

**Version:** 1.0
**Last Updated:** January 21, 2026
**Repo:** `AUM-Unity-Server-Legacy`, `AUM-Unity-Staging-Legacy`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Fighter Attributes](#2-fighter-attributes)
3. [God Bonuses](#3-god-bonuses)
4. [Player Stats Calculation](#4-player-stats-calculation)
5. [Focus System](#5-focus-system)
6. [Spell Cast Attributes](#6-spell-cast-attributes)
7. [Effects System](#7-effects-system)
8. [Item Code Encoding](#8-item-code-encoding)
9. [Elemental Encoding](#9-elemental-encoding)
10. [Damage Types](#10-damage-types)
11. [Character Data](#11-character-data)
12. [Ability Data](#12-ability-data)
13. [Game Stats Tracking](#13-game-stats-tracking)
14. [Slow Effects](#14-slow-effects)
15. [Karma System](#15-karma-system)

---

## 1. Overview

AUM's game data system uses ScriptableObjects for configuration with runtime calculation of final stats.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Stats Calculation Flow                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FighterAttributes (ScriptableObject)                                       │
│       │ Base stats per FightingStyle                                         │
│       │                                                                      │
│       v                                                                      │
│   GodBonuses (ScriptableObject)                                              │
│       │ Modifiers per TrinityGod                                             │
│       │                                                                      │
│       v                                                                      │
│   Player.SetBonuses()                                                        │
│       │ base + bonus - penalty                                               │
│       │                                                                      │
│       v                                                                      │
│   PlayerStats (Runtime Class)                                                │
│       │ Final calculated values                                              │
│       │                                                                      │
│       v                                                                      │
│   PlayerData (Mutable State)                                                 │
│       Current stamina, willpower, etc.                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fighter Attributes

**File:** `Assets/ScriptableObjects/FighterAttributes.cs`
**Type:** ScriptableObject (per FightingStyle)

### Properties

```csharp
public class FighterAttributes : ScriptableObject
{
    // Core Stats
    public float obj_stamina;               // Base stamina pool
    [Range(0f, 10f)]
    public float obj_armor;                 // Damage reduction
    [Range(0f, 550f)]
    public float obj_movespeed;             // Movement speed
    [Range(1f, 100f)]
    public float obj_damage;                // Base damage multiplier
    public float obj_range;                 // Melee attack range
    public float obj_hpregen;               // HP regeneration rate
    public float obj_maxWillpower;          // Willpower pool (spell resource)
    public float maxFocus;                  // Focus bar maximum

    // Attack Speeds (1-10 scale, higher = faster)
    [Range(1f, 10f)]
    public float melee_AttackSpeed;         // First melee attack
    [Range(1f, 10f)]
    public float meleeSecond_AttackSpeed;   // Combo melee attack
    [Range(1f, 10f)]
    public float fire_AttackSpeed;          // Fire spell cast
    [Range(1f, 10f)]
    public float water_AttackSpeed;         // Water spell cast
    [Range(1f, 10f)]
    public float air_AttackSpeed;           // Air spell cast
    [Range(1f, 10f)]
    public float ether_AttackSpeed;         // Ether spell cast
    [Range(1f, 10f)]
    public float earth_AttackSpeed;         // Earth spell cast
    [Range(1f, 10f)]
    public float special_AttackSpeed;       // Unique ability

    // Melee Hold
    [Range(0.1f, 15f)]
    public float maxHoldTime;               // Max melee charge time

    // Focus Bar (Server-side)
    public float focusSegmentSize;          // Points per segment
    public float focusMaxPerHit;            // Max focus gain per hit
}
```

### Expected Values by Fighter

| Style | Stamina | Armor | MoveSpeed | Damage | Range |
|-------|---------|-------|-----------|--------|-------|
| Amuktha | 10000 | 5 | 350 | 50 | 2.5 |
| MantraMuktha | 8000 | 3 | 400 | 40 | 3.0 |
| MukthaMuktha | 12000 | 6 | 300 | 60 | 2.0 |
| PaniMuktha | 9000 | 4 | 380 | 45 | 4.0 |
| YantraMuktha | 9000 | 4 | 370 | 45 | 5.0 |

---

## 3. God Bonuses

**File:** `Assets/ScriptableObjects/GodBonuses.cs`
**Type:** ScriptableObject (per TrinityGod × FightingStyle)

### Properties

```csharp
public class GodBonuses : ScriptableObject
{
    public TrinityGods god;

    // Bonuses (Positive Modifiers)
    public float bonus_range_melee;         // +Melee range
    [Range(0f, 360f)]
    public float melee_angle;               // Melee attack cone angle
    public float bonus_stamina;             // +Stamina
    public float bonus_armor;               // +Armor
    public float bonus_movespeed;           // +Movement speed
    public float bonus_unique_range;        // +Unique ability range

    // Shiva Exclusive
    public float damage_buff;               // +20% damage (Shiva)
    [Range(1f, 10f)]
    public float willpower_Multiplier;      // Willpower scaling

    // Penalties (Negative Modifiers)
    public float move_speed_penalty;        // -Movement speed
    public float armor_penalty;             // -Armor
    public float range_penalty;             // -Range

    // Attack Speed Modifiers
    public float melee_speed;               // +/-Melee speed
    public float meleeSecond_speed;         // +/-Combo speed
    public float fire_speed;                // +/-Fire speed
    public float water_speed;               // +/-Water speed
    public float air_speed;                 // +/-Air speed
    public float ether_speed;               // +/-Ether speed
    public float earth_speed;               // +/-Earth speed
    public float special_speed;             // +/-Special speed
}
```

### God Passive Abilities

| God | Passive | Effect |
|-----|---------|--------|
| **Brahma** | Shield Master | Shield abilities, +3 focus streak start |
| **Vishnu** | Speed Demon | +30% movement speed, stamina discount on dodge |
| **Shiva** | Destruction | Third Eye immunity, +20% damage |

### Vishnu Speed Factor

```csharp
public float GetVishnuSpeedFactor(bool increment)
{
    float speedFactor = 0;
    if (selectedGod == TrinityGods.Vishnu)
    {
        speedFactor = 0.3f;  // 30% speed boost
    }
    return increment ? (1 + speedFactor) : (1 - speedFactor);
}
```

### Shiva Damage Factor

```csharp
public float GetShivaDamageFactor()
{
    if (selectedGod == TrinityGods.Shiva)
    {
        return 1.2f;  // 20% damage boost
    }
    return 1f;
}
```

---

## 4. Player Stats Calculation

**File:** `Assets/Scripts/Player/Player.cs:70-134`

### SetBonuses() Method

```csharp
public void SetBonuses()
{
    godBonuses = PrefabManager.LoadSelectedGodBonuses(selectedGod, fightingStyle);
    fighterAttributes = PrefabManager.LoadSelectedFighterAttributes(fightingStyle);

    // Start with base stats
    float obj_stamina = fighterAttributes.obj_stamina;
    float obj_armor = fighterAttributes.obj_armor;
    float obj_movespeed = fighterAttributes.obj_movespeed;
    // ... (all base stats)

    // Apply bonuses
    obj_stamina += godBonuses.bonus_stamina;
    obj_armor += godBonuses.bonus_armor;
    melee_AttackSpeed += godBonuses.melee_speed;
    // ... (all bonuses)

    // Apply penalties
    obj_movespeed += godBonuses.bonus_movespeed - godBonuses.move_speed_penalty;
    obj_range += godBonuses.bonus_range_melee - godBonuses.range_penalty;

    // Movement speed conversion
    obj_movespeed *= 0.014f;  // Convert to Unity units/tick

    // Create final PlayerStats
    playerStats = new PlayerStats(
        obj_stamina, obj_armor, obj_movespeed,
        melee_AttackSpeed, meleeSecond_AttackSpeed,
        fire_AttackSpeed, water_AttackSpeed, air_AttackSpeed,
        ether_AttackSpeed, earth_AttackSpeed, special_AttackSpeed,
        obj_damage, obj_range, obj_hpregen, godBonuses.melee_angle,
        bonus_unique_range, obj_willPower, obj_willPowerMulti, maxHoldTime
    );
}
```

### PlayerStats Class

```csharp
public class PlayerStats
{
    // Resources
    public float stamina;
    public float willPower;
    public float willPowerMulti;

    // Defense
    public float armour;

    // Movement
    public float moveSpeed;

    // Attack Speeds
    public float melee_AttackSpeed;
    public float meleeSecond_AttackSpeed;
    public float fire_AttackSpeed;
    public float water_AttackSpeed;
    public float air_AttackSpeed;
    public float ether_AttackSpeed;
    public float earth_AttackSpeed;
    public float special_AttackSpeed;

    // Combat
    public float damage;
    public float range;
    public float hpRegen;
    public float meleeAngle;
    public float uniqueRange;
    public float maxHoldTime;
}
```

### PlayerData Class (Mutable State)

```csharp
public class PlayerData
{
    public float stamina;           // Current stamina
    public float staminaCooldown;   // Regen cooldown timer
    public float armor;             // Current armor
    public float moveSpeed;         // Current movement speed
    public float willPower;         // Current willpower
    public PlayerGameStats stats;   // Match statistics
}
```

---

## 5. Focus System

**File:** `Assets/Scripts/Player/Player.cs:621-700+`

### Focus Class

```csharp
public class Focus
{
    int MaxFocus = 100;          // Maximum focus points
    int SegmentSize = 25;        // Points per segment (4 segments default)
    int MaxFocusPerHit = 10;     // Cap on focus gained per hit
    int StartingStreak = 0;      // Starting hit streak value
    int styleBonus = 1;          // MantraMuktha bonus

    public int CurrentFocus { get; private set; }
    public int CurrentStreak { get; private set; } = 0;
    private float lastHitTime = -9999f;
    private bool hasPartialSegment => (CurrentFocus % SegmentSize) != 0;
}
```

### Focus Mechanics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Focus System                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Focus Bar: [========|========|========|========] (4 segments)             │
│              0       25       50       75      100                           │
│                                                                              │
│   Gain Focus:                                                                │
│   ├── Hit lands → gain = min(currentStreak + styleBonus, MaxFocusPerHit)    │
│   ├── Streak increments each hit (max 10)                                   │
│   └── Miss resets streak to StartingStreak                                  │
│                                                                              │
│   Consume Focus:                                                             │
│   ├── Spells consume 1-2 segments                                           │
│   ├── Third Eye consumes segments                                           │
│   ├── Unique abilities consume segments                                      │
│   └── Must have complete segments to consume                                │
│                                                                              │
│   God Modifiers:                                                             │
│   ├── Brahma: StartingStreak = 3 (instead of 1)                             │
│   └── Others: StartingStreak = 1                                            │
│                                                                              │
│   Style Modifiers:                                                           │
│   ├── MantraMuktha: styleBonus = 1                                          │
│   └── Others: styleBonus = 0                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Focus Methods

```csharp
// Constructor
public Focus(int _maxFocus, int _segmentSize, int _maxFocusPerHit,
             TrinityGods _selectedGod, FightingStyles _fightingStyle)
{
    // Brahma gets +3 starting streak
    if (_selectedGod == TrinityGods.Brahma)
    {
        StartingStreak = 3;
    }

    // MantraMuktha gets style bonus
    if (_fightingStyle == FightingStyles.MantraMuktha)
    {
        styleBonus = 1;
    }
}

// On hit landed
public void OnHitLanded(bool hitLanded)
{
    if (hitLanded)
    {
        int rawGain = CurrentStreak + styleBonus;
        int gain = Mathf.Min(rawGain, MaxFocusPerHit);
        AddFocus(gain);

        if (CurrentStreak < 10)
            CurrentStreak++;
    }
    else
    {
        ResetStreak();
    }
}

// Check if enough focus for ability
public bool CheckFocusSegments(int segments)
{
    int requiredFocus = segments * SegmentSize;
    return CurrentFocus >= requiredFocus;
}

// Consume focus segments
public void ConsumeFocusSegments(int segments)
{
    int consumeAmount = segments * SegmentSize;
    CurrentFocus = Mathf.Max(0, CurrentFocus - consumeAmount);
}

// Set focus to percentage (Training mode)
public void SetFocusPercent(float percent)
{
    CurrentFocus = (int)(MaxFocus * percent);
}
```

---

## 6. Spell Cast Attributes

**File:** `Assets/Scripts/Entities/SpellCastAttributes.cs`

### SpellCastAttributes Class

```csharp
public class SpellCastAttributes : MonoBehaviour
{
    public Elementals Elemental;        // Fire, Water, Air, Ether, Earth
    public int spellType;               // Spell variant (0-31)

    // Detection
    public CastDetectionType detectionType;  // Circle, Cone, Box

    // Range (per God)
    [EnumNamedArray(typeof(TrinityGods))]
    public float[] spellDistance;       // [Brahma, Shiva, Vishnu]

    [EnumNamedArray(typeof(TrinityGods))]
    public float[] effectAngle;         // [Brahma, Shiva, Vishnu]

    public float minRange;
    public float maxRange;
    public float maxChannel;            // Max channel time

    // Cost
    public float stamina;               // Stamina cost
    public float willPower;             // Willpower cost (deprecated name)
    public float focusBarSegments;      // Focus segments required (renamed)

    // Get encoded spell index
    public UInt16 GetSpellIndex()
    {
        return (UInt16)((int)Elemental << 5 | spellType);
    }
}
```

### SpellData ScriptableObject

```csharp
[CreateAssetMenu(fileName = "SpellData", menuName = "Assets/ScriptableObjects/SpellData")]
public class SpellData : ScriptableObject
{
    public bool isRunning;
    public Elementals Elemental;
    public AttackType attackType = AttackType.NONE;
    public int spellType;

    public UInt16 GetSpellIndex()
    {
        return (UInt16)((int)Elemental << 5 | spellType);
    }
}
```

---

## 7. Effects System

**File:** `Assets/Scripts/Spells/Effects/Effects.cs`

### Effects Base Class

```csharp
public class Effects
{
    public EffectType type;
    public float duration;
    private float currentDuration;
    private float DPSTimer;

    public Player effectPlayer;      // Player affected
    public Player sourcePlayer;      // Player who applied
    public Entity sourceEntity;      // Entity that caused effect
    public DamageType damageType;

    public float tickInterval;       // Time between ticks
    public float damagePerTick;      // Damage per tick (DoT)

    // Process effect each frame
    public virtual bool Process(float deltaTime)
    {
        currentDuration += deltaTime;
        if (currentDuration >= duration)
        {
            return false;  // Effect expired
        }
        return true;  // Effect continues
    }

    // Check for DPS tick
    public bool DPSCounter(float deltaTime, float dpsTick = 1f)
    {
        DPSTimer += deltaTime;
        if (DPSTimer >= dpsTick)
        {
            DPSTimer -= dpsTick;
            return true;  // Tick occurred
        }
        return false;
    }

    // Reset duration (on reapplication)
    public void ResetDuration()
    {
        currentDuration = 0;
        DPSTimer = 0f;
    }
}
```

### EffectType Enum

```csharp
public enum EffectType
{
    EFFECT_NONE,         // 0 - No effect
    EFFECT_FIREDAMAGE,   // 1 - Fire DoT
    EFFECT_AIRSLOW,      // 2 - Air slow (50%)
    EFFECT_EARTHSTUN,    // 3 - Earth stun
    EFFECT_ETHERMUTE,    // 4 - Ether silence (blocks spells)
    EFFECT_IMPAIR,       // 5 - Water impair (0% speed)
    EFFECT_MAIM,         // 6 - Maim (50% speed)
    EFFECT_THIRDEYE,     // 7 - Third Eye active (Shiva)
    EFFECT_SHIVAASTRA    // 8 - Shiva's ultimate effect
}
```

### Effect Behaviors

| Effect | Behavior | Duration |
|--------|----------|----------|
| FIREDAMAGE | DoT ticks every 1s | Variable |
| AIRSLOW | 50% movement speed | Variable |
| EARTHSTUN | Cannot act, forced Stun state | Variable |
| ETHERMUTE | Cannot cast spells, cancels channeling | Variable |
| IMPAIR | 0% movement speed, cancels dodge/special | Variable |
| MAIM | 50% movement speed | Variable |
| THIRDEYE | Immunity to most effects, +damage | thirdEyeDuration |
| SHIVAASTRA | Shiva ultimate debuff | Variable |

---

## 8. Item Code Encoding

**File:** `Assets/Scenes/AssetManager.cs:587-624`

### WearItem Class

```csharp
public class WearItem
{
    public FightingStyles FightingStyle;
    public FighterClass FighterClass;
    public ItemType ItemType;
    public UInt32 ItemIdentifier;

    // Decode from itemCode
    public WearItem(UInt32 itemCode)
    {
        FightingStyle = (FightingStyles)(itemCode & 0xF);           // bits 0-3
        FighterClass = (FighterClass)((itemCode >> 4) & 0x1);       // bit 4
        ItemType = (ItemType)((itemCode >> 5) & 0xF);               // bits 5-8
        ItemIdentifier = (itemCode >> 9) & 0x7FFFFF;                // bits 9-31
    }

    // Encode to itemCode
    public UInt32 GetItemCode()
    {
        return (UInt32)(
            ((int)ItemIdentifier & 0x7FFFFF) << 9 |
            ((int)ItemType & 0xF) << 5 |
            ((int)FighterClass & 0x1) << 4 |
            ((int)FightingStyle & 0xF)
        );
    }

    // Static encode
    public static UInt32 GetItemCode(
        FightingStyles fightingStyle,
        FighterClass fighterClass,
        ItemType itemType,
        UInt32 itemIdentifier)
    {
        return (UInt32)(
            ((int)itemIdentifier & 0x7FFFFF) << 9 |
            ((int)itemType & 0xF) << 5 |
            ((int)fighterClass & 0x1) << 4 |
            ((int)fightingStyle & 0xF)
        );
    }
}
```

### Item Code Bit Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Item Code (32-bit)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Bit Layout:                                                                │
│   ┌────────────────────────┬────────┬───────────────┬─────┬────────────┐   │
│   │ ItemIdentifier (23-bit)│ ItemType│ FighterClass │ FightingStyle    │   │
│   │ bits 9-31              │ bits 5-8│ bit 4        │ bits 0-3         │   │
│   └────────────────────────┴────────┴───────────────┴─────┴────────────┘   │
│                                                                              │
│   FightingStyle (4 bits): 0-4                                               │
│   ├── 0: Amuktha                                                            │
│   ├── 1: MantraMuktha                                                       │
│   ├── 2: MukthaMuktha                                                       │
│   ├── 3: PaniMuktha                                                         │
│   └── 4: YantraMuktha                                                       │
│                                                                              │
│   FighterClass (1 bit): 0-1                                                 │
│   ├── 0: Male                                                               │
│   └── 1: Female                                                             │
│                                                                              │
│   ItemType (4 bits): 0-7                                                    │
│   ├── 0: Head                                                               │
│   ├── 1: Torso                                                              │
│   ├── 2: Hands                                                              │
│   ├── 3: Pants                                                              │
│   ├── 4: Legs                                                               │
│   ├── 5: Weapons                                                            │
│   ├── 6: Treasure                                                           │
│   └── 7: Sets                                                               │
│                                                                              │
│   ItemIdentifier (23 bits): 1-6 (typical)                                   │
│   ├── 1: Aranya Bronze                                                      │
│   ├── 2: Aranya Silver                                                      │
│   ├── 3: Aranya Gold                                                        │
│   ├── 4: Lohitha Bronze                                                     │
│   ├── 5: Lohitha Silver                                                     │
│   └── 6: Lohitha Gold                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example Encodings

```csharp
// Amuktha Male Head Aranya Bronze
// FightingStyle=0, FighterClass=0, ItemType=0, ItemIdentifier=1
// itemCode = (1 << 9) | (0 << 5) | (0 << 4) | 0 = 512

// MantraMuktha Female Torso Lohitha Gold
// FightingStyle=1, FighterClass=1, ItemType=1, ItemIdentifier=6
// itemCode = (6 << 9) | (1 << 5) | (1 << 4) | 1 = 3121

// YantraMuktha Male Weapons variant 2
// FightingStyle=4, FighterClass=0, ItemType=5, ItemIdentifier=2
// itemCode = (2 << 9) | (5 << 5) | (0 << 4) | 4 = 1188
```

---

## 9. Elemental Encoding

**File:** `Assets/Scripts/HelperClasses/Elemental.cs`

### Elemental Class

```csharp
public class Elemental
{
    private byte elementalValue;
    public byte ElementalValue { get { return elementalValue; } }

    // Construct from raw byte
    public Elemental(byte _elementalValue)
    {
        elementalValue = _elementalValue;
    }

    // Construct from components
    public Elemental(int _elemental, int _spellType)
    {
        elementalValue = (byte)(_elemental << 5 | _spellType);
    }

    // Get element type (Fire, Water, Air, Ether, Earth)
    public Elementals GetElementals()
    {
        return (Elementals)((elementalValue >> 5) & 0x7);
    }

    // Get spell variant (0-31)
    public int GetSpellType()
    {
        return elementalValue & 0x1F;
    }
}
```

### Elemental Encoding Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Elemental Byte (8-bit)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Bit Layout:                                                                │
│   ┌───────────────┬──────────────────────────────┐                          │
│   │ Element (3-bit)│ SpellType (5-bit)            │                          │
│   │ bits 5-7       │ bits 0-4                     │                          │
│   └───────────────┴──────────────────────────────┘                          │
│                                                                              │
│   Element Values:                                                            │
│   ├── 0: FIRE                                                                │
│   ├── 1: WATER                                                               │
│   ├── 2: AIR                                                                 │
│   ├── 3: ETHER                                                               │
│   └── 4: EARTH                                                               │
│                                                                              │
│   SpellType Values: 0-31 (varies per element)                               │
│                                                                              │
│   Formula:                                                                   │
│   └── elementalValue = (element << 5) | spellType                           │
│                                                                              │
│   Examples:                                                                  │
│   ├── Fire spell 0:  (0 << 5) | 0 = 0x00                                    │
│   ├── Water spell 1: (1 << 5) | 1 = 0x21                                    │
│   ├── Air spell 2:   (2 << 5) | 2 = 0x42                                    │
│   ├── Ether spell 0: (3 << 5) | 0 = 0x60                                    │
│   └── Earth spell 3: (4 << 5) | 3 = 0x83                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Damage Types

**File:** `Assets/Scripts/Enum.cs:48-62`

### DamageType Enum

```csharp
public enum DamageType
{
    NONE,           // 0 - No damage type
    MELEE,          // 1 - Physical melee damage
    AXETHROW,       // 2 - MukthaMuktha axe throw
    THIRDEYE,       // 3 - Third Eye burst damage
    FIRE,           // 4 - Fire elemental
    WATER,          // 5 - Water elemental
    AIR,            // 6 - Air elemental
    ETHER,          // 7 - Ether elemental
    EARTH,          // 8 - Earth elemental
    ASTRA_BRAHMA,   // 9 - Brahma ultimate
    ASTRA_VISHNU,   // 10 - Vishnu ultimate
    ASTRA_SHIVA     // 11 - Shiva ultimate
}
```

### Damage Type Interactions

| Damage | Shield Behavior |
|--------|-----------------|
| MELEE | Physical shield blocks |
| AXETHROW | Physical shield blocks |
| THIRDEYE | Ignores shields, area damage |
| FIRE | Elemental shield blocks |
| WATER | Elemental shield blocks, knockback |
| AIR | Elemental shield blocks, slow |
| ETHER | Elemental shield blocks, silence |
| EARTH | Elemental shield blocks, stun |
| ASTRA_* | Varies by ultimate |

---

## 11. Character Data

**File:** `Assets/Scripts/DataClass/CharacterData.cs`

### CharacterData Class

```csharp
public class CharacterData : MonoBehaviour
{
    public FightingStyles fightingStyle;
    public FighterClass fighterClass;
    public AbilityData[] abilityData;

    // Visuals
    public Renderer skin;
    public CharacterAccessoryTransform[] charAccessoryTransforms;

    // Animation
    public float ProjReleaseTime;          // Projectile release frame
    public float dodgeDistance;
    public float dodgeSpeed;

    // Weapon
    public Transform weaponTransform;
    public Transform holsterTransform;
    public GameObject weaponObj;
    public Animator charAnim;

    // Effects
    public ParticleSystem[] meleeChargeParticle;

    // IK
    public Transform ikTargetTransform;
    public RigLayer[] ikRigLayers;

    // Get ability data by type
    public AbilityData GetAbilityData(AttackType attackType)
    {
        return abilityData.FirstOrDefault(
            ability => ability.abilityType == attackType);
    }
}
```

### CharacterAccessoryTransform

```csharp
[System.Serializable]
public class CharacterAccessoryTransform
{
    public string transformName;      // "WeaponTransform", "HolsterTransform"
    public string targetBoneName;     // Bone to parent to
    public Vector3 position;          // Local offset
    public Vector3 rotation;          // Local rotation
    public GameObject objPrefab;      // Prefab to instantiate
}
```

---

## 12. Ability Data

**File:** `Assets/Scripts/DataClass/CharacterData.cs:225-232`

### AbilityData Class

```csharp
[Serializable]
public class AbilityData
{
    public AttackType abilityType;        // Which ability
    public float abilityStamina;          // Stamina cost
    public float abilityWillpower;        // Willpower cost
    public float focusBarSegments;        // Focus segments required (renamed from abilityFocusSegments)
}
```

### AttackType Enum

```csharp
public enum AttackType
{
    ASTRA = 0,      // Ultimate ability
    ELEMENTAL1,     // First equipped elemental
    ELEMENTAL2,     // Second equipped elemental
    ELEMENTAL3,     // Third equipped elemental
    ELEMENTAL4,     // Fourth equipped elemental
    THIRDEYE,       // Third Eye (Shiva)
    UNIQUE,         // Character unique ability
    MELEE,          // Basic melee attack
    BRAHMASHIELD,   // Brahma shield ability
    DODGE,          // Dodge roll
    NONE            // No attack
}
```

### Typical Ability Costs

| Ability | Stamina | Willpower | Focus Segments |
|---------|---------|-----------|----------------|
| MELEE | 0 | 0 | 0 |
| DODGE | 4500-10000 | 0 | 0 |
| ELEMENTAL | Variable | Variable | 1-2 |
| THIRDEYE | 0 | 0 | 2-3 |
| UNIQUE | 0 | 0 | 2 |
| ASTRA | 0 | 0 | 4 |

---

## 13. Game Stats Tracking

**File:** `Assets/Scripts/Player/Player.cs:491-499`

### PlayerGameStats Class

```csharp
public class PlayerGameStats
{
    public float damageMeleeDealt;      // Total melee damage dealt
    public float damageMeleeReceived;   // Total melee damage received
    public float damageSpellDealt;      // Total spell damage dealt
    public float damageSpellReceived;   // Total spell damage received
    public float damageMeleeBlocked;    // Melee damage blocked by shield
    public float damageSpellBlocked;    // Spell damage blocked by shield
    public float damageAstraDealt;      // Astra damage dealt
}
```

### MKMatchAvatarData (Sent at match end)

```csharp
public struct MKMatchAvatarData
{
    public byte[] avatarUniqueID;       // Avatar UUID (16 bytes)
    public byte avatarTeam;             // Team number
    public byte karmaPlayerCount;       // Number of karma choices
    public KarmaDecision[] karmaDecision;  // Karma decisions made
    public byte deadPosition;           // Death order (1st, 2nd, etc.)
    public UInt32 deadDuration;         // Time spent dead
    public UInt16 damageMeleeDealt;
    public UInt16 damageMeleeReceived;
    public UInt16 damageSpellDealt;
    public UInt16 damageSpellReceived;
    public UInt16 damageMeleeBlocked;
    public UInt16 damageSpellBlocked;
}
```

---

## 14. Slow Effects

**File:** `Assets/Scripts/Player/Player.cs:205-210`

### SlowType Enum

```csharp
public enum SlowType
{
    NONE,    // No slow, 100% speed
    FIFTY,   // 50% speed (Air, Maim)
    ZERO     // 0% speed (Impair/Water)
}
```

### GetSlowEffect Method

```csharp
public float GetSlowEffect()
{
    if (IsThirdEyeActive())
    {
        return 1;  // Third Eye immune to slows
    }
    switch (GetSlowEffectType())
    {
        case SlowType.ZERO:
            return 0;    // Impair = no movement
        case SlowType.FIFTY:
            return 0.5f; // Air/Maim = half speed
        case SlowType.NONE:
        default:
            return 1;    // Normal speed
    }
}
```

### GetSlowEffectType Method

```csharp
public SlowType GetSlowEffectType()
{
    if (IsThirdEyeActive())
    {
        return SlowType.NONE;
    }
    foreach (Effects effect in effects)
    {
        if (effect.type == Effects.EffectType.EFFECT_IMPAIR)
        {
            return SlowType.ZERO;
        }
        else if (effect.type == Effects.EffectType.EFFECT_AIRSLOW)
        {
            return SlowType.FIFTY;
        }
        else if (effect.type == Effects.EffectType.EFFECT_MAIM)
        {
            return SlowType.FIFTY;
        }
    }
    return SlowType.NONE;
}
```

---

## 15. Karma System

**File:** `Assets/Scripts/Player/Player.cs:372-408`

### KarmaPlayer Class

```csharp
public class KarmaPlayer
{
    public Player player;           // The defeated player
    public KarmaDecision karma;     // Winner's karma choice

    public KarmaPlayer(Player _player)
    {
        player = _player;
        karma = KarmaDecision.NONE;
    }
}
```

### Karma Enum

```csharp
public enum KarmaDecision
{
    NONE,     // No choice yet
    SATTVA,   // Grant mercy
    RAJAS,    // Steal bronze
    TAMAS     // Punish
}
```

### Karma Methods

```csharp
// Add player to karma list (called when killing)
public void AddKarmaPlayer(Player targetPlayer)
{
    KarmaPlayer karmaPlayer = new(targetPlayer);
    karmaPlayers.Add(karmaPlayer);
    targetPlayer.karmaPlayerGiver = this;
}

// Get karma player IDs for packet
public UInt32[] GetKarmaPlayersList(ref byte playerCount)
{
    UInt32[] karmaPlayersIDs = new UInt32[5];
    int playerIndex = 0;
    foreach (KarmaPlayer karmaPlayer in karmaPlayers)
    {
        karmaPlayersIDs[playerIndex] = karmaPlayer.player.uniqueCode;
        playerIndex++;
    }
    playerCount = (byte)karmaPlayers.Count;
    return karmaPlayersIDs;
}

// Get karma actions for packet
public byte[] GetKarmaActions()
{
    byte[] karmaActions = new byte[5];
    int playerIndex = 0;
    foreach (KarmaPlayer karmaPlayer in karmaPlayers)
    {
        karmaActions[playerIndex] = (byte)karmaPlayer.karma;
        playerIndex++;
    }
    return karmaActions;
}
```

---

## Cross-Reference

- **Protocol Overview:** [PROTOCOL-1-OVERVIEW.md](./PROTOCOL-1-OVERVIEW.md)
- **WSS Packets:** [PROTOCOL-2-WSS-PACKETS.md](./PROTOCOL-2-WSS-PACKETS.md)
- **UDP Packets:** [PROTOCOL-3-UDP-PACKETS.md](./PROTOCOL-3-UDP-PACKETS.md)
- **MatchKeeper:** [PROTOCOL-4-MATCHKEEPER.md](./PROTOCOL-4-MATCHKEEPER.md)
- **PlayFab:** [PROTOCOL-5-PLAYFAB.md](./PROTOCOL-5-PLAYFAB.md)
- **State Machines:** [PROTOCOL-6-STATE-MACHINES.md](./PROTOCOL-6-STATE-MACHINES.md)
- **Characters:** [PROTOCOL-8-CHARACTERS.md](./PROTOCOL-8-CHARACTERS.md)
- **Spells:** [PROTOCOL-9-SPELLS.md](./PROTOCOL-9-SPELLS.md)
- **Enums:** [PROTOCOL-10-ENUMS.md](./PROTOCOL-10-ENUMS.md)
- **Index:** [PROTOCOL-INDEX.md](./PROTOCOL-INDEX.md)

---

*Document generated from AUM-Unity-Server-Legacy and AUM-Unity-Staging-Legacy codebases*
*Total data classes: 25+*
*Total enums documented: 15+*
*Total calculated properties: 40+*
