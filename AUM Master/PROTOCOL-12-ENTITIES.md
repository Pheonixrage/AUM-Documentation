# PROTOCOL-12-ENTITIES.md
# Entity System, Projectiles, and Damage Calculation

## Overview

The AUM server uses an **Entity** system to track server-side game objects that have lifecycle, position, and player ownership. This includes spell projectiles, astra (ultimate) effects, thrown weapons, and zone-based damage areas.

**Key Files:**
- `Assets/Scripts/Managers/EntityManager.cs` - Entity lifecycle management
- `Assets/Scripts/Managers/ProjectileManager.cs` - Ranged projectile management
- `Assets/Scripts/Projectile.cs` - Base projectile class
- `Assets/Scripts/GenericProjectile.cs` - Arrow/Magic/Discus projectiles
- `Assets/Scripts/SpellProjectile.cs` - Spell entity with triggers
- `Assets/Scripts/Player/Characters/PlayerBase.cs` - Damage calculation

---

## 1. Entity System Architecture

### 1.1 Entity Base Class

```csharp
public class Entity : MonoBehaviour
{
    public UInt32 UniqueID;          // Random 1-10,000,000
    public UInt32 EntityType;        // Encoded type (element << 5 | spellType)
    public Player EntityPlayer;       // Owning player
    public UInt32 FrameNumber;        // Server tick at creation
    public byte EntityState;          // Current state
    public Vector3 SourceLocation;    // Start position
    public Vector3 CurrentLocation;   // Current position
    public Vector3 EntityEndLocation; // Target/end position

    // Override in subclasses
    public virtual bool Process(float deltaTime)
    {
        return false;  // Return false to destroy entity
    }
}
```

### 1.2 EntityManager

```csharp
public class EntityManager
{
    public Dictionary<UInt32, Entity> entityList;

    // Called every server tick
    public void ProcessTick(float deltaTime)
    {
        foreach (Entity entity in entityList.Values.ToArray())
        {
            if (!entity.Process(deltaTime))
            {
                RemoveEntity(entity);
            }
        }
    }

    public void AddEntity(Entity newEntity);
    public void RemoveEntity(Entity removeEntity);
    public Entity[] GetActiveEntities();
    public bool isEntityPresent(UInt32 entityUniqueID);
}
```

### 1.3 Entity Lifecycle

```
Creation:
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Player Action ──► Instantiate Entity ──► Generate UniqueID      │
│                         │                                        │
│                         ▼                                        │
│               AddEntity(EntityManager)                           │
│                         │                                        │
│                         ▼                                        │
│               Send Entity Packet to Clients                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

Processing:
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Server Tick ──► EntityManager.ProcessTick()                     │
│                         │                                        │
│                         ▼                                        │
│            For each Entity: entity.Process(deltaTime)            │
│                         │                                        │
│                    ┌────┴────┐                                   │
│               true │         │ false                             │
│                    ▼         ▼                                   │
│              Continue   RemoveEntity() ──► Destroy(gameObject)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Projectile System

### 2.1 ProjectileManager

Separate from EntityManager, handles ranged character projectiles.

```csharp
public static class ProjectileManager
{
    public static List<ProjectileInfo> projectileList = new();

    public static void ProcessTick(float deltaTime)
    {
        foreach (ProjectileInfo projectile in projectileList.ToArray())
        {
            if (!projectile.activeProjectile.Process(deltaTime, projectile.serverTick))
            {
                RemoveProjectile(projectile);
            }
        }
    }

    public static void AddProjectile(Player usePlayer, GameObject projectileObj, UInt32 serverTick)
    {
        Projectile projectile = projectileObj.GetComponent<Projectile>();
        projectile.usePlayer = usePlayer;

        ProjectileInfo projectileInfo = new()
        {
            activeProjectile = projectile,
            projectileObject = projectileObj,
            serverTick = serverTick
        };
        projectileList.Add(projectileInfo);
    }

    public static void OnServerTick()
    {
        foreach (ProjectileInfo projectile in projectileList.ToArray())
        {
            projectile.serverTick++;  // Track projectile age
        }
    }
}

public class ProjectileInfo
{
    public Projectile activeProjectile;
    public GameObject projectileObject;
    public UInt32 serverTick;
}
```

### 2.2 ProjectileType Enum

```csharp
public enum ProjectileType
{
    ARROW = 1,     // YantraMuktha
    MAGICBALL = 2, // MantraMuktha
    DISCUSS = 3    // PaniMuktha (Chakra)
}
```

### 2.3 Base Projectile Class

```csharp
public class Projectile : MonoBehaviour
{
    public Player usePlayer;

    public virtual bool Process(float deltaTime, UInt32 serverTick)
    {
        return true;  // Return false to destroy
    }
}
```

---

## 3. GenericProjectile (Arrow/MagicBall)

Handles ranged attacks for YantraMuktha and MantraMuktha.

### 3.1 Properties

```csharp
public class GenericProjectile : Projectile
{
    public ProjectileType projectileType;
    public Vector3 projectileDestination;
    public float projectileRadius;
    public float projectileSpeed;
    public float chargeSpeed;
    public bool thirdEyeActive;
    public float thirdEyeAOERange;
    public bool isCharged;
    public bool overlapCheck = false;
}
```

### 3.2 Processing Logic

```csharp
override public bool Process(float deltaTime, UInt32 serverTick)
{
    bool hitRegister = false;
    if (!usePlayer.active)
    {
        Destroy(this.gameObject);
        return false;
    }

    // Rollback for lag compensation
    RollBackData data = GameManager.RollbackState(serverTick, usePlayer);
    if (data != null)
    {
        bool projDestroyed = false;
        transform.LookAt(projectileDestination);

        float moveDistance = deltaTime * projectileSpeed * ((isCharged) ? chargeSpeed : 1);

        // Initial overlap check (prevents spawning inside walls)
        if (!overlapCheck)
        {
            Collider[] hitColliders = Physics.OverlapSphere(transform.position, projectileRadius);
            foreach (var hitCollider in hitColliders)
            {
                if (GameManager.CheckEnvironmentTag(hitCollider.tag))
                    projDestroyed = true;
            }
            overlapCheck = true;
        }

        // SphereCast for collision detection
        if (Physics.SphereCast(transform.position, projectileRadius, transform.forward,
                              out RaycastHit objectHit, moveDistance))
        {
            Collider hitCollider = objectHit.collider;

            if (GameManager.CheckEnvironmentTag(hitCollider.tag))
            {
                projDestroyed = true;  // Hit wall/environment
            }
            else if (hitCollider.tag == "Player")
            {
                Player hitPlayer = hitCollider.GetComponent<PlayerBase>().character.player;

                if (hitPlayer != usePlayer && !hitPlayer.IsDead() &&
                    hitPlayer.team != usePlayer.team)
                {
                    if (!thirdEyeActive)
                    {
                        usePlayer.character.playerBase.DoMeleeDamage(hitPlayer, isCharged);
                        hitRegister = true;
                    }
                    projDestroyed = true;
                }
            }
        }

        // Move projectile
        if (!projDestroyed)
        {
            transform.position = Vector3.MoveTowards(
                transform.position, projectileDestination, moveDistance);
        }

        // Restore world state after rollback
        GameManager.ForwardState(usePlayer, data);

        // Check if reached destination or destroyed
        float distToDestination = (transform.position - projectileDestination).magnitude;
        if (distToDestination <= 0.1f || projDestroyed)
        {
            Destroy(this.gameObject);

            // Shiva Third Eye AOE damage
            if (thirdEyeActive)
            {
                foreach (Player player in PlayerManager.playerList.Values)
                {
                    float dist = (player.character.playerBase.ContactPoint.transform.position -
                                 transform.position).magnitude;
                    if (dist <= thirdEyeAOERange)
                    {
                        usePlayer.character.playerBase.DoMeleeDamage(player, isCharged);
                        hitRegister = true;
                    }
                }
            }

            usePlayer.focus.OnHitLanded(hitRegister);
            return false;
        }
    }
    else
    {
        // No rollback data available - destroy projectile
        return false;
    }
    return true;
}
```

---

## 4. SpellProjectile (Elemental Spells)

Extends Entity for spell zones with trigger collision.

### 4.1 Structure

```csharp
public class SpellProjectile : Entity
{
    public SpellAttributes spellAttributes;
    public GameObject entityObject;
    private Spell activeSpell;
    private List<Player> playersInside = new();

    public void InitializeSpellProjectile(Player sourcePlayer, Vector3 endLocation)
    {
        spellAttributes = GetComponent<SpellAttributes>();

        UniqueID = (UInt32)Random.Range(1, 10000000);
        EntityType = spellAttributes.GetSpellIndex();  // (element << 5 | spellType)
        EntityPlayer = sourcePlayer;
        FrameNumber = GameManager.serverTick;
        SourceLocation = sourcePlayer.pGameObject.transform.position;
        EntityEndLocation = endLocation;

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
}
```

### 4.2 Trigger Callbacks

```csharp
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

private void OnTriggerStay(Collider other)
{
    if (other.tag != "Player") return;
    PlayerBase pb = other.GetComponent<PlayerBase>();
    if (pb == null || pb.character.player == EntityPlayer) return;

    activeSpell.OnTriggerStayPlayer(pb.character);
}

private void OnTriggerExit(Collider other)
{
    if (other.tag != "Player") return;
    PlayerBase pb = other.GetComponent<PlayerBase>();
    if (pb == null) return;

    Player p = pb.character.player;
    if (playersInside.Contains(p))
    {
        playersInside.Remove(p);
        activeSpell.OnTriggerExitPlayer(pb.character);
    }
}
```

---

## 5. Astra System (Ultimate Abilities)

### 5.1 AstraEntityType Enum

```csharp
public enum AstraEntityType
{
    BRAHMASTRA = 1,     // Expanding explosion
    NARAYANASTRA = 2,   // Homing missiles
    SHIVASTRA = 3       // Cone beam with burn
}
```

### 5.2 AstraManager

```csharp
public class AstraManager : MonoBehaviour
{
    public GameObject[] astraPrefabs;  // Indexed by TrinityGods

    public void Initialize()
    {
        astraPrefabs = new GameObject[3];
        for (int i = 0; i < 3; i++)
        {
            astraPrefabs[i] = GameManager.Instance.PrefabManager.LoadAstraPrefab((TrinityGods)i);
        }
    }

    public void SpawnAstra(Player sourcePlayer)
    {
        switch (sourcePlayer.selectedGod)
        {
            case TrinityGods.Vishnu:
                // Spawn at map center
                Vector3 spawnPos = GameManager.Instance.mapConfig.MapCenter.position;
                GameObject astraObj = Instantiate(astraPrefabs[(int)TrinityGods.Vishnu], spawnPos, Quaternion.identity);
                astraObj.GetComponent<NarayanAstraProjectile>().Initialize(sourcePlayer, spawnPos);
                break;

            case TrinityGods.Shiva:
                // Spawn at player position
                spawnPos = sourcePlayer.pGameObject.transform.position;
                astraObj = Instantiate(astraPrefabs[(int)TrinityGods.Shiva], spawnPos, Quaternion.identity);
                astraObj.GetComponent<ShivaAstraProjectile>().Initialize(sourcePlayer);
                break;

            case TrinityGods.Brahma:
                // Spawn at map center
                spawnPos = GameManager.Instance.mapConfig.MapCenter.position;
                astraObj = Instantiate(astraPrefabs[(int)TrinityGods.Brahma], spawnPos, Quaternion.identity);
                astraObj.GetComponent<BrahmastraProjectile>().Initialize(sourcePlayer, spawnPos);
                break;
        }
    }
}
```

### 5.3 AstraProjectile Base Class

```csharp
public class AstraProjectile : Entity
{
    public virtual void Initialize(Player sourcePlayer, AstraEntityType entityType)
    {
        UniqueID = (UInt32)Random.Range(1, 10000000);
        EntityType = (UInt32)entityType << 17;  // Shifted for astra type encoding
        EntityPlayer = sourcePlayer;
        FrameNumber = GameManager.serverTick;
        SourceLocation = sourcePlayer.pGameObject.transform.position;

        GameManager.Instance.EntityManager.AddEntity(this);
    }
}
```

---

## 6. Brahmastra (Expanding Explosion)

### 6.1 Properties

```csharp
public class BrahmastraProjectile : AstraProjectile
{
    public float startRadius = 3f;
    public float maxRadius = 50f;
    public float rateOfExpansion;
    public int astraDamage;
    public float astraPercentDamage;
    float currentRadius;
    List<GameObject> AlreadyHitPlayers;
    bool isExploding = false;
    float explodeTimer = 0f;
    float maxWaitTime = 1f;  // 1 second delay before explosion
}
```

### 6.2 Processing

```csharp
public override bool Process(float deltaTime)
{
    if (isExploding)
    {
        if (currentRadius >= maxRadius)
        {
            Destroy(this.gameObject);
            return false;
        }
        RangeCheck();
        currentRadius += rateOfExpansion * deltaTime;
        return true;
    }
    else
    {
        // Wait before exploding
        if (explodeTimer >= maxWaitTime)
        {
            CreateExplosion();
            return true;
        }
        explodeTimer += deltaTime;
    }
    return true;
}

void RangeCheck()
{
    foreach (Player target in PlayerManager.playerList.Values)
    {
        if (target == sourcePlayer) continue;
        if (target.IsDead()) continue;
        if (sourcePlayer.IsInTeam(target.team)) continue;

        float dist = Vector3.Distance(transform.position, target.pGameObject.transform.position);
        if (dist < currentRadius && !AlreadyHitPlayers.Contains(target.pGameObject))
        {
            AlreadyHitPlayers.Add(target.pGameObject);

            // Shield interaction (astras destroy shields but damage passes through)
            if (target.character.playerBase.activeElementalShield != null)
            {
                ElementalShield.AttackInfo info = new()
                {
                    Component = AttackDamageComponent.Astra,
                    damageType = DamageType.ASTRA_BRAHMA,
                    targetPlayer = target,
                    sourcePlayer = sourcePlayer,
                };
                target.character.playerBase.activeElementalShield.RegisterShieldHit(
                    DamageType.ASTRA_BRAHMA, this, info);
                // Astras always do full damage regardless of shield result
            }

            float damage = astraDamage + target.playerData.willPower * astraPercentDamage;
            target.character.playerBase.DoAstraDamage(sourcePlayer, damage, DamageType.ASTRA_BRAHMA);
            target.character.playerBase.AddAstraImpactEffect(ImpactIndicatorType.BrahmaAstra);
        }
    }
}
```

---

## 7. Narayana Astra (Homing Missiles)

### 7.1 Properties

```csharp
public class NarayanAstraProjectile : AstraProjectile
{
    public GameObject weaponPrefab;
    public Transform dropPoint;
    public float fireRate = 3;          // Fire every 3 seconds
    public float maxAstraLifetime = 5f;
    public float minHitDistance;        // Distance to register hit
    public float speed;
    public float lerpDuration;
    public int maxWeaponCount = 7;      // Max missiles per player
    public float minMoveHit;            // Movement distance to spawn bonus missile
    public float initialDamage = 650f;
    public float initialDamagePercentage;
    public float moveDamage = 675;
    public float moveDamagePercentage;

    public List<PlayerWeapons> playerWeapons;
}
```

### 7.2 Weapon Data Classes

```csharp
public class WeaponData
{
    public GameObject weaponObj;
    public float elapsedTime = 0f;
    public byte spawnIndex;
    public float distancePlayer;
    public bool initialWeapon;
}

public class PlayerWeapons
{
    public Player hitPlayer;
    public byte spawnCount;
    public Vector3 spawnPlayerLocation;
    public List<WeaponData> activeWeapons = new();
}
```

### 7.3 Processing

```csharp
public override bool Process(float deltaTime)
{
    // Check lifetime
    if (astraLifetime > maxAstraLifetime)
    {
        if (DestroyAstra())  // All missiles hit/destroyed
        {
            Destroy(this.gameObject);
            playerWeapons.Clear();
            return false;
        }
    }

    // Fire missiles at regular intervals
    if (timer >= fireRate)
    {
        foreach (Player player in PlayerManager.playerList.Values)
        {
            if (player == sourcePlayer) continue;
            if (player.IsInTeam(sourcePlayer.team)) continue;

            PlayerWeapons weapons = GetPlayerWeapons(player);
            if (weapons != null)
            {
                if (player.IsDead())
                {
                    DestroyPlayerWeapons(player);
                    RemoveTargetPlayer(player);
                    continue;
                }
            }
            else
            {
                if (!player.IsDead())
                {
                    weapons = new PlayerWeapons(player);
                    playerWeapons.Add(weapons);
                }
                else continue;
            }
            CheckWeaponFireCondition(weapons);
        }
        timer = 0f;
    }

    timer += deltaTime;
    astraLifetime += deltaTime;
    WeaponUpdate(deltaTime);
    return true;
}

void CheckWeaponFireCondition(PlayerWeapons weapons)
{
    if (astraLifetime > maxAstraLifetime) return;

    bool createMissile = false;
    bool initialWeapon = true;
    float playerDistance = 0f;

    if (weapons.spawnCount < maxWeaponCount)
    {
        createMissile = true;
    }
    else
    {
        // Bonus missile if player moves
        playerDistance = Vector3.Distance(
            weapons.hitPlayer.pGameObject.transform.position,
            weapons.spawnPlayerLocation);
        if (playerDistance >= minMoveHit)
        {
            createMissile = true;
            initialWeapon = false;
        }
    }

    if (createMissile)
    {
        GameObject weaponObj = Instantiate(weaponPrefab, dropPoint.position, Quaternion.identity);
        WeaponData weaponData = new(weaponObj, weapons.spawnCount, playerDistance, initialWeapon);
        weapons.activeWeapons.Add(weaponData);
        weapons.spawnCount++;
        weapons.spawnPlayerLocation = weapons.hitPlayer.pGameObject.transform.position;
    }
}
```

### 7.4 Missile Movement & Damage

```csharp
bool MoveWeapon(WeaponData weaponData, Player targetPlayer, float deltaTime)
{
    // Hit detection
    if (Vector3.Distance(weaponData.weaponObj.transform.position,
                        targetPlayer.pGameObject.transform.position) < minHitDistance)
    {
        Destroy(weaponData.weaponObj);

        // Damage calculation
        float astraDamage = initialDamage + targetPlayer.playerData.willPower * initialDamagePercentage;
        if (!weaponData.initialWeapon)
        {
            // Movement-based missiles do distance-scaled damage
            astraDamage = moveDamage * weaponData.distancePlayer +
                         targetPlayer.playerData.willPower * moveDamagePercentage;
        }

        // Shield interaction
        if (targetPlayer.character.playerBase.activeElementalShield != null)
        {
            ElementalShield.AttackInfo info = new()
            {
                Component = AttackDamageComponent.Astra,
                damageType = DamageType.ASTRA_VISHNU,
                targetPlayer = targetPlayer,
                sourcePlayer = sourcePlayer,
            };
            targetPlayer.character.playerBase.activeElementalShield.RegisterShieldHit(
                DamageType.ASTRA_VISHNU, this, info);
        }

        targetPlayer.character.playerBase.DoAstraDamage(sourcePlayer, astraDamage, DamageType.ASTRA_VISHNU);
        targetPlayer.character.playerBase.AddAstraImpactEffect(ImpactIndicatorType.VishnuAstra);
        return false;
    }

    // Homing movement
    Quaternion targetRotation = Quaternion.LookRotation(
        (targetPlayer.pGameObject.transform.position - weaponData.weaponObj.transform.position).normalized);
    weaponData.weaponObj.transform.rotation = Quaternion.Slerp(
        weaponData.weaponObj.transform.rotation, targetRotation,
        weaponData.elapsedTime / lerpDuration);
    weaponData.weaponObj.transform.position += weaponData.weaponObj.transform.forward * speed;
    weaponData.elapsedTime += deltaTime * speed;
    return true;
}
```

---

## 8. Shiva Astra (Cone Beam + Burn)

### 8.1 Properties

```csharp
public class ShivaAstraProjectile : AstraProjectile
{
    public float maxDistance;
    public float castRadius = 2.5f;
    public Vector3 castOffset;
    public float maxAstraLifetime = 5f;
    public float astraDamage;
    public float astraPercentDamage;
    public float burnTimer;      // DoT duration
    public float dpsTick;        // Damage per tick
}
```

### 8.2 Processing

```csharp
public override bool Process(float deltaTime)
{
    if (sourcePlayer.IsDead() || !sourcePlayer.active || astraLifetime >= maxAstraLifetime)
    {
        Destroy(this.gameObject);
        return false;
    }

    // SphereCast in player's forward direction
    Vector3 spawnPos = sourcePlayer.pGameObject.transform.TransformPoint(castOffset);
    hitObjs = Physics.SphereCastAll(spawnPos, castRadius,
                                    sourcePlayer.pGameObject.transform.forward, maxDistance);

    if (hitObjs != null && hitObjs.Length > 0)
    {
        for (int i = 0; i < hitObjs.Length; i++)
        {
            if (hitObjs[i].collider.tag != "Player") continue;
            if (hitObjs[i].collider.gameObject == sourcePlayer.pGameObject) continue;

            Player hitPlayer = hitObjs[i].collider.GetComponent<PlayerBase>().character.player;
            if (hitPlayer.IsDead()) continue;
            if (hitPlayer.IsInTeam(sourcePlayer.team)) continue;

            // Shield interaction
            if (hitPlayer.character.playerBase.activeElementalShield != null)
            {
                ElementalShield.AttackInfo info = new()
                {
                    Component = AttackDamageComponent.Astra,
                    damageType = DamageType.ASTRA_SHIVA,
                    targetPlayer = hitPlayer,
                    sourcePlayer = sourcePlayer,
                };
                hitPlayer.character.playerBase.activeElementalShield.RegisterShieldHit(
                    DamageType.ASTRA_SHIVA, this, info);
            }

            // Apply burn effect
            float damage = astraDamage + hitPlayer.playerData.willPower * astraPercentDamage;
            Effects shivaAstraEffect = new ShivaAstraBurn(
                burnTimer, hitPlayer, damage, dpsTick, this);
            hitPlayer.character.AddEffect(shivaAstraEffect);
        }
    }

    astraLifetime += deltaTime;
    return true;
}
```

---

## 9. Character-Specific Projectiles

### 9.1 Axe (MukthaMuktha)

The axe is a throwable entity with three states.

```csharp
public enum AxeState
{
    ONHAND,     // Held by player
    FLYING,     // In transit to destination
    ONGROUND,   // Waiting on ground
    CALLBACK    // Returning to player
}

public class Axe : Entity
{
    public float speed;
    public float pickupDistance = 0.5f;
    public float stunDuration;
    public float stunRadius;
    public float stunDamage;
    public float castRadius;
    List<GameObject> AlreadyHitPlayers;
}
```

**Processing:**

```csharp
public override bool Process(float deltaTime)
{
    if (throwPlayer.player.active == false)
    {
        Destroy(this.gameObject);
        throwPlayer.axeState = AxeState.ONHAND;
        return false;
    }

    switch (throwPlayer.axeState)
    {
        case AxeState.ONGROUND:
            return !OnDestinationReached();  // Auto-pickup when close

        case AxeState.CALLBACK:
            EntityState = (byte)throwPlayer.axeState;
            return !CallBackAxe(deltaTime);

        default:
            FlyingFunction(deltaTime);
            break;
    }
    return true;
}

void FlyingFunction(float deltaTime)
{
    if ((transform.position - LandPosition).magnitude > 0.01f)
    {
        CastSphere();  // Hit detection during flight
        transform.position = Vector3.MoveTowards(transform.position, LandPosition, deltaTime * speed);
        return;
    }

    // Landed
    throwPlayer.axeState = AxeState.ONGROUND;
    EntityState = (byte)throwPlayer.axeState;
    DoAOEStun();  // Stun nearby enemies on impact
}

void DoAOEStun()
{
    Player[] playerList = GetPlayersInAxeAOERange(stunRadius);
    foreach (Player player in playerList)
    {
        if (player == throwPlayer.player) continue;
        if (player.IsDead()) continue;
        if (throwPlayer.player.team == player.team) continue;

        // Shield check
        if (player.character.playerBase.activeElementalShield != null)
        {
            ElementalShield.RegisterShieldResult result =
                player.character.playerBase.activeElementalShield.RegisterShieldHit(
                    DamageType.AXETHROW, this, attackInfo);
            if (!result.result || result.damagePassFraction <= 0f)
            {
                continue;  // Blocked
            }
        }

        player.character.DoStun(stunDuration);
        player.character.playerBase.DoSpellDamage(throwPlayer.player, stunDamage, DamageType.AXETHROW);
    }
}
```

### 9.2 Discuss (PaniMuktha Chakra)

Elliptical boomerang projectile with god-specific behavior.

```csharp
public class Discuss : Projectile
{
    public float speed;
    public float lerpTime;
    public float minPathPercentage;  // 10-100%
    public float maxRangePoint;
    public float castRadius;
    private EllipseGenerator meleePath;
    private Vector3[] pathPoints;
    private List<GameObject> AlreadyHitPlayers;
    public bool isCharged;
    public bool hitRegister = false;

    // Shiva Third Eye expansion
    public float maxRadius;
    public float rateOfExpansion;
    private float shivaRadius;
    private bool thirdEyeActive;
}
```

**God-Specific Behavior:**

| God | Behavior |
|-----|----------|
| **Brahma** | Elliptical path outward, Bezier curve return |
| **Vishnu** | Straight throw to MaxRangePoint, straight return |
| **Shiva (Normal)** | Same as Brahma |
| **Shiva (Third Eye)** | Expanding AOE ring |

```csharp
override public bool Process(float deltaTime, UInt32 serverTick)
{
    if (!usePlayer.active) return false;

    if (usePlayer.selectedGod == TrinityGods.Brahma ||
        (usePlayer.selectedGod == TrinityGods.Shiva && !thirdEyeActive))
    {
        // Elliptical path behavior
        CastSphere(deltaTime, serverTick);
        if (currentPoint > PathPercentageToPoints(minPathPercentage))
        {
            // Return phase - Bezier curve
            ReturnPath(pathPoints[currentPoint], currentTarget, maxOffset, deltaTime);
        }
        else
        {
            // Outward phase - follow ellipse
            MoveProjectileMelee(speed, minPathPercentage, deltaTime);
        }
    }
    else if (usePlayer.selectedGod == TrinityGods.Vishnu)
    {
        // Straight throw/return
        CastSphere(deltaTime, serverTick);
        if (!HasReachedDestination(currentTarget) && !isOnTheWayBack)
        {
            transform.position = Vector3.MoveTowards(transform.position, currentTarget, deltaTime * speed);
        }
        else
        {
            isOnTheWayBack = true;
            currentTarget = usePlayer.pGameObject.transform.position + Vector3.up * 2.5f;
            transform.position = Vector3.MoveTowards(transform.position, currentTarget, deltaTime * speed);
        }
    }
    else if (usePlayer.selectedGod == TrinityGods.Shiva && thirdEyeActive)
    {
        // Expanding AOE ring
        if (shivaRadius >= maxRadius)
        {
            usePlayer.focus.OnHitLanded(hitRegister);
            Destroy(this.gameObject);
            return false;
        }
        ShivaRangeCheck(serverTick);
        shivaRadius += rateOfExpansion * deltaTime;
    }
    return true;
}
```

---

## 10. Damage Calculation System

### 10.1 DamageType Enum

```csharp
public enum DamageType
{
    NONE,
    MELEE,
    AXETHROW,
    THIRDEYE,
    FIRE,
    WATER,
    AIR,
    ETHER,
    EARTH,
    ASTRA_BRAHMA,
    ASTRA_VISHNU,
    ASTRA_SHIVA
}
```

### 10.2 AttackDamageComponent Enum

```csharp
public enum AttackDamageComponent
{
    Physical,     // Melee/projectile physical hit
    Astra,        // Ultimate ability
    SpellBurst,   // Single spell hit
    SpellZone,    // Zone tick damage
    SpellDoT      // DoT tick damage
}
```

### 10.3 DoMeleeDamage

```csharp
public void DoMeleeDamage(Player targetPlayer, bool isChargedShot,
                          bool isCoated = false, CoatedType coatedType = CoatedType.None)
{
    if (targetPlayer.IsDead()) return;
    if (character.player.team == targetPlayer.team) return;

    // Base damage from player stats
    float willpowerReduce = character.player.playerStats.damage;

    // Damage modifiers
    willpowerReduce *= character.player.GetShivaDamageFactor();  // +20% if Shiva god
    if (character.player.IsThirdEyeActive())
        willpowerReduce *= thirdEyeDamageMultiplier;
    if (isChargedShot)
        willpowerReduce *= chargeShotDamageMultiplier;
    if (targetPlayer.shieldBlockAbility)
        willpowerReduce *= 0.8f;  // 20% reduction if shield ability active

    // Bot handicap (bot vs player)
    if (!targetPlayer.IsBot && character.player.IsBot)
        willpowerReduce *= 0.8f;

    // Tutorial/First Match modifiers
    if (GameManager.Instance.matchType == MatchType.TUTORIAL)
        willpowerReduce *= GameManager.Instance.TutorialManager.GetTutorialDamageMultiplier(...);
    if (GameManager.Instance.IsFirstMatch)
        willpowerReduce *= GameManager.Instance.BotManager.GetFirstMatchDamgeMultiplier(...);

    // Focus system - receiver loses streak
    targetPlayer.focus.OnHitReceived();

    // Shield interaction
    if (targetPlayer.character.playerBase.activeElementalShield != null)
    {
        ElementalShield.RegisterShieldResult result =
            targetPlayer.character.playerBase.activeElementalShield.RegisterShieldHit(
                DamageType.MELEE, null, attackInfo);

        if (result.result)
        {
            // Shield allowed damage through
            ApplyDamage(targetPlayer, willpowerReduce);
            character.player.focus.OnHitLanded(true);
        }
        else
        {
            // Shield blocked
            character.player.focus.OnHitLanded(false);
        }
    }
    else
    {
        // No shield - full damage
        ApplyDamage(targetPlayer, willpowerReduce);
    }
}

void ApplyDamage(Player target, float damage)
{
    target.character.playerBase.ReduceWillPower(damage);
    target.character.playerBase.CheckDeath();
    target.playerData.stats.damageMeleeReceived += damage;
    character.player.playerData.stats.damageMeleeDealt += damage;
    Utils.SendLogData(target, Utils.CombatLogType.RECEIVE, character.player, DamageType.MELEE, ...);
}
```

### 10.4 DoSpellDamage

```csharp
public bool DoSpellDamage(Player sourcePlayer, float spellDamage, DamageType damageType,
                          Effects.EffectType effectType = Effects.EffectType.EFFECT_NONE)
{
    if (character.player.IsDead()) return false;

    // Modifiers
    spellDamage *= sourcePlayer.GetShivaDamageFactor();
    if (sourcePlayer.IsThirdEyeActive())
        spellDamage *= thirdEyeDamageMultiplier;

    // Bot handicap
    if (sourcePlayer.IsBot && !character.player.IsBot)
        spellDamage *= 0.8f;

    // Tutorial modifier
    if (GameManager.Instance.matchType == MatchType.TUTORIAL)
        spellDamage *= GameManager.Instance.TutorialManager.GetTutorialDamageMultiplier(...);

    // Apply damage
    character.player.focus.OnHitReceived();
    sourcePlayer.playerData.stats.damageSpellDealt += spellDamage;
    character.player.playerData.stats.damageSpellReceived += spellDamage;
    ReduceWillPower(spellDamage);
    CheckDeath();

    // Attacker focus
    if (spellDamage > 0f)
        sourcePlayer.focus.OnHitLanded(true);

    return true;
}
```

### 10.5 DoAstraDamage

```csharp
public bool DoAstraDamage(Player sourcePlayer, float astraDamage, DamageType damageType)
{
    if (character.player.IsDead()) return false;

    // Tutorial modifier only (no third eye/shiva bonus for astras)
    if (GameManager.Instance.matchType == MatchType.TUTORIAL)
        astraDamage *= GameManager.Instance.TutorialManager.GetTutorialDamageMultiplier(...);

    // Apply damage
    character.player.focus.OnHitReceived();
    sourcePlayer.playerData.stats.damageAstraDealt += astraDamage;
    character.player.playerData.stats.damageAstraReceived += astraDamage;
    ReduceWillPower(astraDamage);
    CheckDeath();

    // Attacker focus
    if (astraDamage > 0f)
        sourcePlayer.focus.OnHitLanded(true);

    return true;
}
```

### 10.6 Damage Multiplier Summary

| Condition | Multiplier | Applies To |
|-----------|-----------|------------|
| Shiva God | +20% | Melee, Spell |
| Third Eye Active | ×`thirdEyeDamageMultiplier` | Melee, Spell |
| Charged Shot | ×`chargeShotDamageMultiplier` | Melee |
| Shield Block Ability | ×0.8 | Melee |
| Bot vs Player | ×0.8 | Melee, Spell |
| First Match (Bot source) | ×0.2 | Melee |
| First Match (Player source) | ×3.0 | Melee |
| Tutorial | Variable | All |

---

## 11. Death & Respawn

### 11.1 CheckDeath

```csharp
public void CheckDeath()
{
    if (character.player.playerData.willPower == 0)
    {
        // Tutorial/First Match: Players cannot die
        if (GameManager.Instance.matchType == MatchType.TUTORIAL ||
            GameManager.Instance.IsFirstMatch)
        {
            if (!character.player.IsBot)
                return;  // Only bots can die
        }

        character.stateManager.ChangeState(FSM.StateType.Death);
        Utils.SendLogData(character.player, Utils.CombatLogType.DEATH, ...);
        GameManager.Instance.DeadPlayers.Add(character.player);
        character.player.deadPosition = (byte)GameManager.Instance.DeadPlayers.Count;
        character.player.deadDuration = MatchState.Instance.matchTimer;
    }
}
```

### 11.2 RespawnCharacter

```csharp
public void RespawnCharacter()
{
    if (character.player.IsDead())
    {
        // Restore resources
        character.player.playerData.stamina = character.player.playerStats.stamina;
        character.player.playerData.willPower = character.player.playerStats.willPower;

        character.stateManager.ChangeState(FSM.StateType.Idle);

        // Tutorial: respawn at bot spawn point
        if (GameManager.Instance.matchType == MatchType.TUTORIAL)
        {
            character.player.pGameObject.GetComponent<CharacterController>().enabled = false;
            character.player.pGameObject.transform.position =
                ((TutorialMapConfig)GameManager.Instance.mapConfig).BotSpawnPoint.position;
            character.player.pGameObject.GetComponent<CharacterController>().enabled = true;
        }
    }
}
```

---

## 12. Entity Type Encoding

### 12.1 Spell Entity Type

```csharp
// SpellAttributes.GetSpellIndex()
EntityType = (UInt16)((int)Elemental << 5 | spellType);
```

| Bits | Meaning |
|------|---------|
| 0-4 | Spell Type (0-31) |
| 5-7 | Elemental (0=Fire, 1=Water, 2=Air, 3=Ether, 4=Earth) |

### 12.2 Astra Entity Type

```csharp
// AstraProjectile.Initialize()
EntityType = (UInt32)entityType << 17;
```

| Bits | Meaning |
|------|---------|
| 17-18 | Astra Type (1=Brahma, 2=Vishnu, 3=Shiva) |

### 12.3 Axe Entity Type

```csharp
// Axe.Initialize()
EntityType = 1 << 16;  // Fixed value for axe
```

---

## 13. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `EntityManager.cs` | 73 | Entity lifecycle management |
| `ProjectileManager.cs` | 57 | Ranged projectile management |
| `Projectile.cs` | 20 | Base projectile class |
| `GenericProjectile.cs` | 112 | Arrow/MagicBall projectile |
| `SpellProjectile.cs` | 78 | Spell entity with triggers |
| `AstraManager.cs` | 92 | Astra spawn management |
| `AstraProjectile.cs` | 20 | Base astra entity class |
| `BrahmastraProjectile.cs` | 106 | Expanding explosion astra |
| `NarayanAstraProjectile.cs` | 287 | Homing missiles astra |
| `ShivaAstraProjectile.cs` | 86 | Cone beam astra |
| `Axe.cs` | 197 | MukthaMuktha thrown axe |
| `Discuss.cs` | 308 | PaniMuktha chakra projectile |
| `PlayerBase.cs` | 426 | Damage calculation methods |

**Total Entity System: ~1,862 lines of code**

---

*Last Updated: January 21, 2026*
*Protocol Version: 12.0*
