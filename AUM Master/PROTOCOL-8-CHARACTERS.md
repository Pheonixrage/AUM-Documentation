# AUM Protocol Documentation: Character Implementations

**Version:** 1.0
**Last Updated:** January 21, 2026
**Repo:** `AUM-Unity-Server-Legacy`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Character Hierarchy](#2-character-hierarchy)
3. [ControllerBase](#3-controllerbase)
4. [PlayerBase](#4-playerbase)
5. [Amuktha (Sword)](#5-amuktha-sword)
6. [MantraMuktha (Staff)](#6-mantramuktha-staff)
7. [MukthaMuktha (Axe)](#7-mukthamuktha-axe)
8. [PaniMuktha (Discus)](#8-panimuktha-discus)
9. [YantraMuktha (Bow)](#9-yantramuktha-bow)
10. [Combat Mechanics](#10-combat-mechanics)
11. [Character Configuration](#11-character-configuration)

---

## 1. Overview

AUM features 5 unique fighting styles, each with distinct melee mechanics and special abilities:

| Style | Weapon | Type | Attack | Special |
|-------|--------|------|--------|---------|
| Amuktha | Sword | Close-range | Combo melee | Dash |
| MantraMuktha | Staff | Ranged | Magic projectile | Teleport |
| MukthaMuktha | Axe | Close-range | Combo melee | Axe throw/recall |
| PaniMuktha | Discus | Ranged | Discus throw | Maim (AoE slow) |
| YantraMuktha | Bow | Ranged | Arrow shot | Impair (AoE root) |

---

## 2. Character Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Character Class Hierarchy                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   MonoBehaviour                                                              │
│       │                                                                      │
│       ├── ControllerBase (Base character controller)                         │
│       │       │                                                              │
│       │       ├── Amuktha (Sword fighter)                                   │
│       │       ├── MantraMuktha (Staff mage)                                 │
│       │       ├── MukthaMuktha (Axe fighter)                                │
│       │       ├── PaniMuktha (Discus thrower)                               │
│       │       └── YantraMuktha (Archer)                                     │
│       │                                                                      │
│       └── PlayerBase (Character physics/damage)                              │
│                                                                              │
│   CharacterData (ScriptableObject/MonoBehaviour)                             │
│       │                                                                      │
│       └── AmukthaData (Amuktha-specific config)                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ControllerBase

**File:** `Assets/Scripts/Player/ControllerBase.cs`
**Lines:** 598
**Purpose:** Base class for all character controllers

### Properties

```csharp
public class ControllerBase : MonoBehaviour
{
    // References
    public PlayerBase playerBase;
    public Player player;
    public StateManager stateManager;
    public CastManager castManager;
    public CharacterData characterData;

    // Combat state
    public Elemental currentSpellIndex;
    public byte currentShieldIndex;
    public bool attackDone = false;
    public bool spellCastDone = false;
    public bool elementalShieldDone = false;
    public bool thirdEyeDone = false;
    public bool pushBackDone = false;
    public bool pushBackInit = false;
    public bool specialDone = false;
    public bool entitySpawnDone = false;
    public bool astraDone = false;

    // Melee state
    public int meleeAnimIndex;
    public float meleeSpeed;
    public bool meleeAimReleaseState;
    public float meleeChargingTime;
}
```

### State Registration (Base)

```csharp
public virtual void InitializeFightingStyle()
{
    stateManager = new StateManager(player);
    stateManager
        .AddState(StateType.Melee, new State(...))
        .AddState(StateType.Idle, new State(...))
        .AddState(StateType.Channel, new State(...))
        .AddState(StateType.Spell_Aiming, new State(...))
        .AddState(StateType.Cast_Spell, new State(...))
        .AddState(StateType.Special_Aiming, new State(...))
        .AddState(StateType.Shield_Block, new State(...))
        .AddState(StateType.Shield_Attack, new State(...))
        .AddState(StateType.Spell_Anticipate, new State(...))
        .AddState(StateType.Cast_Shield, new State(...))
        .AddState(StateType.Death, new State(...))
        .AddState(StateType.Water_Pushback, new State(...))
        .AddState(StateType.Pushback_Land, new State(...))
        .AddState(StateType.Special_Anticipate, new State(...))
        .AddState(StateType.Stun, new State(...))
        .AddState(StateType.Third_Eye, new State(...))
        .AddState(StateType.Third_Eye_Anticipate, new State(...))
        .AddState(StateType.Dodge, new State(...))
        .AddState(StateType.Jump, new State(...))
        .AddState(StateType.Astra_Anticipate, new State(...))
        .AddState(StateType.Astra_Channel, new State(...))
        .AddState(StateType.Astra_Cast, new State(...))
        .AddState(StateType.Teleport, new State(...))
        .AddState(StateType.Vulnerable, new State(...))
        .AddState(StateType.Victory, new State(...));

    stateManager.ChangeState(StateType.Idle);
}
```

### Effect Handling

```csharp
public void AddEffect(Effects effect)
{
    if (player.IsDead()) return;

    // Check for existing same-type effect
    foreach (Effects activeEffect in player.effects.ToArray())
    {
        if (activeEffect.type == effect.type)
        {
            activeEffect.ResetDuration();
            activeEffect.sourcePlayer = effect.sourcePlayer;
            return;
        }
    }

    // Check shield
    if (playerBase.activeElementalShield != null)
    {
        var result = playerBase.activeElementalShield.RegisterShieldHit(
            effect.damageType, effect.sourceEntity);
        if (!result.result)
        {
            // Shield blocked
            return;
        }
    }

    player.effects.Add(effect);

    // Ethermute cancels spell casting
    if (effect.type == Effects.EffectType.EFFECT_ETHERMUTE)
    {
        switch (stateManager.GetState())
        {
            case StateType.Channel:
            case StateType.Spell_Aiming:
            case StateType.Spell_Anticipate:
            case StateType.Astra_Anticipate:
            case StateType.Astra_Channel:
                stateManager.ChangeState(StateType.Idle);
                break;
        }
    }
    // Impair cancels special abilities
    else if (effect.type == Effects.EffectType.EFFECT_IMPAIR)
    {
        switch (stateManager.GetState())
        {
            case StateType.Special_Aiming:
            case StateType.Special_Anticipate:
            case StateType.Special:
                if (player.fightingStyle == FightingStyles.MantraMuktha ||
                    player.fightingStyle == FightingStyles.Amuktha)
                {
                    stateManager.ChangeState(StateType.Idle);
                }
                break;
            case StateType.Dodge:
                stateManager.ChangeState(StateType.Idle);
                break;
        }
    }
}
```

---

## 4. PlayerBase

**File:** `Assets/Scripts/Player/Characters/PlayerBase.cs`
**Lines:** 400+
**Purpose:** Physics, damage, and combat calculations

### Properties

```csharp
public class PlayerBase : MonoBehaviour
{
    public GameObject[] charModels;
    public GameObject ContactPoint;

    // Animation settings
    [Range(0f, 30f)]
    public float Animation_Divider = 20f;
    [Range(0f, 40f)]
    float MoveAnim_Divider = 35f;
    [Range(1f, 10f)]
    public float AttackAnim_Divider = 1f;

    // Combat settings
    public ImpactIndicatorType impactMeleeType;
    public ElementalShield activeElementalShield;
    public float thirdEyeDuration;
    public float thirdEyeDamageMultiplier;
    public float chargeShotDamageMultiplier;
    public float dodgeSpeed;

    // Runtime
    public GameObject activeModel = null;
    public ControllerBase character;
}
```

### Range Detection

```csharp
public Player[] GetPlayersInRange(float distance)
{
    List<Player> playerList = new List<Player>();
    foreach (Player player in PlayerManager.playerList.Values)
    {
        if ((player.character.playerBase.ContactPoint.transform.position -
             ContactPoint.transform.position).magnitude <= distance)
        {
            playerList.Add(player);
        }
    }
    return playerList.ToArray();
}

public bool TargetWithinAngle(GameObject thisObject, GameObject CenterObject, float EffectAngle)
{
    return Vector3.Angle(
        CenterObject.transform.forward,
        thisObject.transform.position - CenterObject.transform.position
    ) < EffectAngle / 2f;
}
```

### Melee Damage Calculation

```csharp
public void DoMeleeDamage(Player targetPlayer, bool isChargedShot,
                          bool isCoated = false, CoatedType coatedType = CoatedType.None)
{
    if (targetPlayer.IsDead()) return;
    if (character.player.team == targetPlayer.team) return;

    // Base damage
    float willpowerReduce = character.player.playerStats.damage;

    // Modifiers
    willpowerReduce *= character.player.GetShivaDamageFactor();     // +20% for Shiva

    if (character.player.IsThirdEyeActive())
        willpowerReduce *= thirdEyeDamageMultiplier;                // Third Eye boost

    if (isChargedShot)
        willpowerReduce *= chargeShotDamageMultiplier;              // Charged shot boost

    if (targetPlayer.shieldBlockAbility)
        willpowerReduce *= 0.8f;                                     // -20% vs shield block

    // Bot handicap (bots deal less to players)
    if (!targetPlayer.IsBot && character.player.IsBot)
        willpowerReduce *= 0.8f;

    // Tutorial damage scaling
    if (GameManager.Instance.matchType == MatchType.TUTORIAL)
        willpowerReduce *= GameManager.Instance.TutorialManager
            .GetTutorialDamageMultiplier(character.player, targetPlayer);

    // First match bot scaling
    if (GameManager.Instance.IsFirstMatch)
        willpowerReduce *= GameManager.Instance.BotManager
            .GetFirstMatchDamgeMultiplier(character.player, targetPlayer);

    // Apply damage (with shield check)
    // ...
}
```

---

## 5. Amuktha (Sword)

**File:** `Assets/Scripts/Player/Characters/Amuktha/Amuktha.cs`
**Lines:** 118
**Type:** Close-range melee fighter
**Weapon:** Sword

### Class Definition

```csharp
public class Amuktha : ControllerBase
{
    // Combo system
    public bool continuousAttackTrigger;
    private bool continuousAttackState;
}
```

### Special States

```csharp
public override void InitializeFightingStyle()
{
    base.InitializeFightingStyle();
    characterData = GetComponent<AmukthaData>();

    stateManager
        .AddState(StateType.Special, new State(
            OnSpecialAbilityEnter,
            OnSpecialAbilityUpdate,
            OnSpecialAbilityExit,
            (uint)StateBlockFlags.Special))
        .AddState(StateType.Melee_Second, new State(
            OnAttackEnter,
            OnAttackUpdate,
            OnAttackEnd,
            (uint)StateBlockFlags.Melee));
}
```

### Melee Attack (Hitbox)

```csharp
public void PostMeleeAttack(UInt32 attackTick)
{
    bool hitRegister = false;

    // Rollback to tick for lag compensation
    RollBackData data = GameManager.RollbackState(attackTick, player);
    if (data != null)
    {
        // Get players in range
        Player[] playerList = playerBase.GetPlayersInRange(player.playerStats.range);
        foreach (Player targetPlayer in playerList)
        {
            if (player == targetPlayer) continue;

            // Check angle (or Third Eye = 360°)
            if (playerBase.TargetWithinAngle(
                    targetPlayer.character.playerBase.ContactPoint,
                    player.character.playerBase.ContactPoint,
                    player.playerStats.meleeAngle) ||
                player.IsThirdEyeActive())
            {
                playerBase.DoMeleeDamage(targetPlayer, false);
                player.focus.OnHitLanded(true);
                hitRegister = true;
            }
        }
        GameManager.ForwardState(player, data);

        if (!hitRegister)
            player.focus.OnHitLanded(false);
    }
}
```

### Special Ability: Dash

```csharp
private void OnDash()
{
    Vector3 dashPosition = new Vector3(player.abilityPos.x, 0, player.abilityPos.z);

    player.pGameObject.GetComponent<CharacterController>().enabled = false;
    player.pGameObject.transform.position = Vector3.MoveTowards(
        player.pGameObject.transform.position,
        dashPosition,
        ((AmukthaData)characterData).dashSpeed * 0.02f);

    if ((player.pGameObject.transform.position - dashPosition).magnitude <= 0.1f)
    {
        player.pGameObject.transform.position = dashPosition;
        stateManager.ChangeState(StateType.Idle);
    }
    player.pGameObject.GetComponent<CharacterController>().enabled = true;
}

public override void OnSpecialAbilityUpdate()
{
    base.OnSpecialAbilityUpdate();
    OnDash();
}
```

### Combo System

```csharp
public override void OnAttackUpdate()
{
    base.OnAttackUpdate();

    // Check for combo input
    if (continuousAttackTrigger && !continuousAttackState)
    {
        continuousAttackState = true;
    }

    // Damage at 50% animation
    if (stateManager.isAnimationHalfDone(meleeSpeed, 0.5f, meleeAnimIndex) && !attackDone)
    {
        PostMeleeAttack(stateManager.stateTick);
        attackDone = true;
    }

    // Animation complete
    if (stateManager.IsAnimationDone(meleeSpeed, meleeAnimIndex))
    {
        if (continuousAttackState)
        {
            // Continue combo: Melee → Melee_Second → Melee
            stateManager.ChangeState(
                stateManager.GetState() == StateType.Melee
                    ? StateType.Melee_Second
                    : StateType.Melee);
        }
        else
        {
            stateManager.ChangeState(StateType.Idle);
        }
    }
}
```

---

## 6. MantraMuktha (Staff)

**File:** `Assets/Scripts/Player/Characters/MantraMuktha/MantraMuktha.cs`
**Lines:** 131
**Type:** Ranged magic fighter
**Weapon:** Staff

### Class Definition

```csharp
public class MantraMuktha : ControllerBase
{
    public GameObject MagicSpawnPoint;
    public GameObject MaxRangePoint;
    public GameObject magicProjectile;
    public float shivaAOEDistance;
}
```

### Special States

```csharp
override public void InitializeFightingStyle()
{
    base.InitializeFightingStyle();
    characterData = GetComponent<CharacterData>();

    stateManager
        .AddState(StateType.Special, new State(
            OnSpecialAbilityEnter,
            OnSpecialAbilityUpdate,
            OnSpecialAbilityExit,
            (uint)StateBlockFlags.Special))
        .AddState(StateType.Aiming, new State(
            OnAimEnter,
            OnAimUpdate,
            OnAimExit,
            (uint)StateBlockFlags.Aiming))
        .AddState(StateType.Melee_Second, new State(
            OnAttackEnter,
            OnAttackUpdate,
            OnAttackEnd,
            (uint)StateBlockFlags.Melee));

    // Extend range point
    MaxRangePoint.transform.localPosition = new Vector3(
        MaxRangePoint.transform.localPosition.x,
        MaxRangePoint.transform.localPosition.y,
        MaxRangePoint.transform.localPosition.z + player.playerStats.range);
}
```

### Melee Attack (Projectile)

```csharp
public void PostMeleeAttack(UInt32 attackTick)
{
    Vector3 SpawnPoint = MagicSpawnPoint.transform.position;
    GameObject RangedProj = Instantiate(magicProjectile, SpawnPoint, MagicSpawnPoint.transform.rotation);

    GenericProjectile spawnProjectile = RangedProj.GetComponent<GenericProjectile>();
    spawnProjectile.projectileDestination = MaxRangePoint.transform.position;
    spawnProjectile.thirdEyeActive = player.IsThirdEyeActive();
    spawnProjectile.thirdEyeAOERange = shivaAOEDistance;
    spawnProjectile.isCharged = (meleeChargingTime >= player.playerStats.maxHoldTime);

    ProjectileManager.AddProjectile(player, RangedProj, attackTick);
    player.abilityPos = MagicSpawnPoint.transform.position;
    player.abilityRotation = MagicSpawnPoint.transform.eulerAngles.y;
}
```

### Aiming System (Hold Attack)

```csharp
public virtual void OnAimUpdate()
{
    if (stateManager.IsAnimationDone())
    {
        // Charge up while holding
        meleeChargingTime += (float)GameManager.clientTickRateMS.ToDouble();
        if (meleeChargingTime >= player.playerStats.maxHoldTime)
        {
            meleeChargingTime = player.playerStats.maxHoldTime;

            // Notify client of full charge
            player.notifyEvents.Enqueue(new NotifyEvent()
            {
                notifyType = NotifyEvent.NotifyType.AIM_CHARGING,
                notifyValue = 1,
                notifySourcePlayer = player.uniqueCode
            });
        }

        // Release fires
        if (meleeAimReleaseState)
        {
            stateManager.ChangeState(StateType.Melee);
        }
    }
    else
    {
        meleeChargingTime = 0;
    }
}
```

### Special Ability: Teleport

```csharp
private void OnTeleport()
{
    Vector3 teleportPosition = new Vector3(player.abilityPos.x, 0, player.abilityPos.z);

    player.pGameObject.GetComponent<CharacterController>().enabled = false;
    player.pGameObject.transform.position = teleportPosition;
    player.pGameObject.GetComponent<CharacterController>().enabled = true;
}

public override void OnSpecialAnticipateUpdate()
{
    base.OnSpecialAnticipateUpdate();
    stateManager.ChangeState(StateType.Special);
    OnTeleport();
}
```

---

## 7. MukthaMuktha (Axe)

**File:** `Assets/Scripts/Player/Characters/MukthaMuktha/MukthaMuktha.cs`
**Lines:** 157
**Type:** Close-range melee fighter
**Weapon:** Axe

### Class Definition

```csharp
public class MukthaMuktha : ControllerBase
{
    public GameObject throwSpawnPoint;
    public GameObject axeProjectile;
    public AxeState axeState;
    public bool continuousAttackTrigger;
    private bool continuousAttackState;
}

public enum AxeState
{
    ONHAND = 0,
    FLYING = 1,
    ONGROUND = 2,
    CALLBACK = 3
}
```

### Special States

```csharp
public override void InitializeFightingStyle()
{
    base.InitializeFightingStyle();
    characterData = GetComponent<CharacterData>();

    stateManager
        .AddState(StateType.Special, new State(
            OnSpecialAbilityEnter,
            OnSpecialAbilityUpdate,
            OnSpecialAbilityExit,
            (uint)StateBlockFlags.Special))
        .AddState(StateType.Axe_Callback, new State(
            OnAxeCallBackEnter,
            OnAxeCallbackUpdate,
            OnAxeCallbackExit,
            (uint)StateBlockFlags.Axe_Callback))
        .AddState(StateType.Melee_Second, new State(
            OnAttackEnter,
            OnAttackUpdate,
            OnAttackEnd,
            (uint)StateBlockFlags.Melee));
}
```

### Melee Attack (Same as Amuktha)

```csharp
public void PostMeleeAttack(UInt32 attackTick)
{
    bool hitRegister = false;
    RollBackData data = GameManager.RollbackState(attackTick, player);
    if (data != null)
    {
        Player[] playerList = playerBase.GetPlayersInRange(player.playerStats.range);
        foreach (Player targetPlayer in playerList)
        {
            if (player == targetPlayer) continue;

            if (playerBase.TargetWithinAngle(...) || player.IsThirdEyeActive())
            {
                playerBase.DoMeleeDamage(targetPlayer, false);
                player.focus.OnHitLanded(true);
                hitRegister = true;
            }
        }
        GameManager.ForwardState(player, data);
        if (!hitRegister) player.focus.OnHitLanded(false);
    }
}
```

### Special Ability: Axe Throw

```csharp
void ThrowAxe()
{
    Vector3 SpawnPoint = throwSpawnPoint.transform.position;
    GameObject axeEntity = Instantiate(axeProjectile, SpawnPoint, throwSpawnPoint.transform.rotation);

    axeEntity.GetComponent<Axe>().Initialize(
        new Vector3(player.abilityPos.x, 0, player.abilityPos.z),
        SpawnPoint,
        this);
}

public override void OnSpecialAbilityUpdate()
{
    base.OnSpecialAbilityUpdate();

    // Throw at 50% animation
    if (stateManager.isAnimationHalfDone(player.playerStats.special_AttackSpeed, 0.5f) &&
        axeState == AxeState.ONHAND)
    {
        ThrowAxe();
    }

    if (stateManager.IsAnimationDone(player.playerStats.special_AttackSpeed))
    {
        specialDone = true;
    }
}
```

### Axe Recall (Vishnu Exclusive)

```csharp
public void RecallAxe()
{
    if (player.selectedGod == TrinityGods.Vishnu)
    {
        axeState = AxeState.CALLBACK;
        stateManager.ChangeState(StateType.Axe_Callback);
    }
}

void OnAxeCallbackUpdate()
{
    if (stateManager.isAnimationHalfDone(1.0f, 0.5f))
    {
        stateManager.ChangeState(StateType.Idle);
    }
}
```

---

## 8. PaniMuktha (Discus)

**File:** `Assets/Scripts/Player/Characters/PaniMuktha/PaniMuktha.cs`
**Lines:** 167
**Type:** Ranged fighter
**Weapon:** Discus (Chakram)

### Class Definition

```csharp
public class PaniMuktha : ControllerBase
{
    public GameObject ThrowSpawnPoint;
    public GameObject MaxRangePoint;
    public GameObject discussProjectile;
    public GameObject ellipsePrefab;

    private float meleeAttackDelay = 0.2f;
    public float maimDistance;
    public float maimDuration;

    EllipseGenerator ellipseGenerator;
}
```

### Special States

```csharp
override public void InitializeFightingStyle()
{
    base.InitializeFightingStyle();
    characterData = GetComponent<CharacterData>();

    // Extend range
    MaxRangePoint.transform.localPosition = new Vector3(
        MaxRangePoint.transform.localPosition.x,
        MaxRangePoint.transform.localPosition.y,
        MaxRangePoint.transform.localPosition.z + player.playerStats.range);

    stateManager
        .AddState(StateType.Special, new State(
            OnSpecialAbilityEnter,
            OnSpecialAbilityUpdate,
            OnSpecialAbilityExit,
            (uint)StateBlockFlags.Special))
        .AddState(StateType.Aiming, new State(
            OnAimEnter,
            OnAimUpdate,
            OnAimExit,
            (uint)StateBlockFlags.Aiming));
}
```

### Melee Attack (Discus Throw)

```csharp
public void PostMeleeAttack(UInt32 attackTick)
{
    // Create ellipse path for Brahma/Shiva
    if (ellipseGenerator == null)
    {
        if (player.selectedGod == TrinityGods.Brahma ||
            player.selectedGod == TrinityGods.Shiva)
        {
            GameObject ellipseBrahmaPrefab = Instantiate(ellipsePrefab, ...);
            ellipseBrahmaPrefab.transform.SetParent(ThrowSpawnPoint.transform);
            ellipseGenerator = ellipseBrahmaPrefab.GetComponent<EllipseGenerator>();
            ellipseGenerator.yAxis = player.playerStats.range / 2f;
            ellipseGenerator.xAxis = player.playerStats.range / 6f;
            ellipseGenerator.offset = (player.playerStats.range / 2f * -1f) - 0.5f;
        }
    }

    Vector3 SpawnPoint = ThrowSpawnPoint.transform.position;
    GameObject RangedProj = Instantiate(discussProjectile, SpawnPoint, ThrowSpawnPoint.transform.rotation);
    Discuss discuss = RangedProj.GetComponent<Discuss>();

    // God-specific behavior
    if (player.selectedGod == TrinityGods.Brahma)
    {
        discuss.Initialize(ellipseGenerator, player);
    }
    else if (player.selectedGod == TrinityGods.Vishnu)
    {
        discuss.Initialize(player);  // Straight path
    }
    else if (player.selectedGod == TrinityGods.Shiva)
    {
        discuss.Initialize(ellipseGenerator, player, player.IsThirdEyeActive());
    }

    discuss.isCharged = (meleeChargingTime >= player.playerStats.maxHoldTime);
    ProjectileManager.AddProjectile(player, RangedProj, attackTick);
}
```

### Special Ability: Maim (AoE Slow)

```csharp
private void OnMaim()
{
    Player[] playerList = playerBase.GetPlayersInRange(maimDistance);
    foreach (Player targetPlayer in playerList)
    {
        if (targetPlayer == player) continue;
        if (targetPlayer.IsDead()) continue;
        if (targetPlayer.team == player.team) continue;

        Effects maimEffect = new Maim(maimDuration, targetPlayer, player);
        targetPlayer.character.AddEffect(maimEffect);
    }
}

public override void OnSpecialAnticipateUpdate()
{
    base.OnSpecialAnticipateUpdate();
    stateManager.ChangeState(StateType.Special);
    OnMaim();
}
```

---

## 9. YantraMuktha (Bow)

**File:** `Assets/Scripts/Player/Characters/YantraMuktha/YantraMuktha.cs`
**Lines:** 160
**Type:** Ranged fighter
**Weapon:** Bow & Arrow

### Class Definition

```csharp
public class YantraMuktha : ControllerBase
{
    public GameObject RangedSpawnPoint;
    public GameObject MaxRangePoint;
    public GameObject arrowProjectile;

    public float impairDuration;
    public float impairDistance;
    public float shivaAOEDistance;
}
```

### Special States

```csharp
override public void InitializeFightingStyle()
{
    base.InitializeFightingStyle();
    characterData = GetComponent<CharacterData>();

    // Extend range
    MaxRangePoint.transform.localPosition = new Vector3(
        MaxRangePoint.transform.localPosition.x,
        MaxRangePoint.transform.localPosition.y,
        MaxRangePoint.transform.localPosition.z + player.playerStats.range);

    stateManager
        .AddState(StateType.Special, new State(
            OnSpecialAbilityEnter,
            OnSpecialAbilityUpdate,
            OnSpecialAbilityExit,
            (uint)StateBlockFlags.Special))
        .AddState(StateType.Aiming, new State(
            OnAimEnter,
            OnAimUpdate,
            OnAimExit,
            (uint)StateBlockFlags.Aiming));
}
```

### Melee Attack (Arrow Shot)

```csharp
public void PostMeleeAttack(UInt32 attackTick)
{
    SpawnMeleeProjectile(
        RangedSpawnPoint.transform.position,
        MaxRangePoint.transform.position,
        RangedSpawnPoint.transform.rotation,
        attackTick);

    player.abilityPos = RangedSpawnPoint.transform.position;
    player.abilityRotation = RangedSpawnPoint.transform.eulerAngles.y;

    // Brahma: Triple shot
    if (player.selectedGod == TrinityGods.Brahma)
    {
        for (int i = -1; i < 2; i++)
        {
            if (i == 0) continue;

            Vector3 SpawnPoint = RangedSpawnPoint.transform.position;
            Vector3 DestinationPoint = MaxRangePoint.transform.position;
            DestinationPoint += (2f * i * MaxRangePoint.transform.right);

            SpawnMeleeProjectile(SpawnPoint, DestinationPoint,
                RangedSpawnPoint.transform.rotation, attackTick);
        }
    }
}

private void SpawnMeleeProjectile(Vector3 SpawnPoint, Vector3 MaxRangePoint,
                                  Quaternion rotation, UInt32 attackTick)
{
    GameObject RangedProj = Instantiate(arrowProjectile, SpawnPoint, rotation);
    GenericProjectile spawnProjectile = RangedProj.GetComponent<GenericProjectile>();
    spawnProjectile.projectileDestination = MaxRangePoint;
    spawnProjectile.thirdEyeActive = player.IsThirdEyeActive();
    spawnProjectile.thirdEyeAOERange = shivaAOEDistance;
    spawnProjectile.isCharged = (meleeChargingTime >= player.playerStats.maxHoldTime);
    ProjectileManager.AddProjectile(player, RangedProj, attackTick);
}
```

### Special Ability: Impair (AoE Root)

```csharp
private void OnImpair()
{
    Player[] playerList = playerBase.GetPlayersInRange(impairDistance);
    foreach (Player targetPlayer in playerList)
    {
        if (targetPlayer == player) continue;
        if (targetPlayer.IsDead()) continue;
        if (targetPlayer.team == player.team) continue;

        Effects impairEffect = new Impair(impairDuration, targetPlayer, player);
        targetPlayer.character.AddEffect(impairEffect);
    }
}

public override void OnSpecialAnticipateUpdate()
{
    base.OnSpecialAnticipateUpdate();
    stateManager.ChangeState(StateType.Special);
    OnImpair();
}
```

---

## 10. Combat Mechanics

### Damage Multipliers

| Source | Multiplier | Description |
|--------|------------|-------------|
| Base | × playerStats.damage | Base damage from stats |
| Shiva | × 1.2 | Shiva god passive |
| Third Eye | × thirdEyeDamageMultiplier | Third Eye active |
| Charged | × chargeShotDamageMultiplier | Held attack fully charged |
| Shield Block | × 0.8 | Target is shield blocking |
| Bot Handicap | × 0.8 | Bot attacking player |
| Tutorial | × variable | Tutorial damage scaling |
| First Match | × variable | First match bot scaling |

### Rollback System

```csharp
// Lag compensation for melee
RollBackData data = GameManager.RollbackState(attackTick, player);
if (data != null)
{
    // Hit detection at historical positions
    Player[] playerList = playerBase.GetPlayersInRange(range);
    // ...

    // Restore current state
    GameManager.ForwardState(player, data);
}
```

### Combo System (Amuktha, MukthaMuktha)

```
Melee → (continuous input) → Melee_Second → (continuous input) → Melee → ...
```

### Aiming System (Ranged Fighters)

```
Aiming (hold) → meleeChargingTime++ → (release) → Melee (projectile)
               │
               └→ Max charge → Notify client → Charged shot bonus
```

---

## 11. Character Configuration

### AmukthaData (Example)

```csharp
public class AmukthaData : CharacterData
{
    public float dashSpeed;       // Dash movement speed
    public float dashDistance;    // Maximum dash distance
}
```

### God-Specific Behaviors

| Character | Brahma | Vishnu | Shiva |
|-----------|--------|--------|-------|
| Amuktha | Shield abilities | +30% speed, stamina discount | Third Eye, +20% damage |
| MantraMuktha | Shield abilities | +30% speed | Third Eye AoE |
| MukthaMuktha | Shield abilities | Axe recall | Third Eye |
| PaniMuktha | Ellipse discus path | Straight path | Ellipse + Third Eye |
| YantraMuktha | Triple shot | +30% speed | Third Eye AoE |

---

## Cross-Reference

- **Protocol Overview:** [PROTOCOL-1-OVERVIEW.md](./PROTOCOL-1-OVERVIEW.md)
- **State Machines:** [PROTOCOL-6-STATE-MACHINES.md](./PROTOCOL-6-STATE-MACHINES.md)
- **Game Data:** [PROTOCOL-7-GAME-DATA.md](./PROTOCOL-7-GAME-DATA.md)
- **Spells:** [PROTOCOL-9-SPELLS.md](./PROTOCOL-9-SPELLS.md)
- **Enums:** [PROTOCOL-10-ENUMS.md](./PROTOCOL-10-ENUMS.md)
- **Index:** [PROTOCOL-INDEX.md](./PROTOCOL-INDEX.md)

---

*Document generated from AUM-Unity-Server-Legacy codebase*
*Total character classes: 5*
*Total lines of character code: 1,300+*
*Total unique abilities: 5*
