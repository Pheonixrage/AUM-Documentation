# PROTOCOL-13-MAPS.md
# Map Configuration, Arena Systems, and Spawn Logic

## Overview

The AUM server uses a **MapConfig** system to define arena layouts, spawn points, and environmental colliders. Maps are loaded dynamically based on match type and player count, with different sizes for different game modes.

**Key Files:**
- `Assets/Scripts/Maps/MapConfig.cs` - Base map configuration
- `Assets/Scripts/Maps/BhulokMapConfig.cs` - Standard arena config
- `Assets/Scripts/Maps/TutorialMapConfig.cs` - Tutorial map config
- `Assets/Scripts/Managers/PrefabManager.cs` - Map loading
- `Assets/Scripts/Managers/TutorialManager.cs` - Tutorial-specific logic
- `Assets/Scripts/Managers/GameManager.cs` - Map initialization

---

## 1. Map Configuration Architecture

### 1.1 MapConfig Base Class

```csharp
public abstract class MapConfig : MonoBehaviour
{
    [SerializeField] protected Transform mapCentre;
    [SerializeField] protected Transform mapVertical;
    [SerializeField] protected Transform[] spawnPoints;
    [SerializeField] protected Transform[] obstacleColliders;

    public Transform MapCenter { get { return mapCentre; } }
    public Transform MapVertical { get { return mapVertical; } }
    public Transform[] SpawnPoints { get { return spawnPoints; } }
    public Transform[] ObstacleColliders { get { return obstacleColliders; } }

    public void ActiveAll(Transform[] hideObjs, bool active)
    {
        foreach (Transform t in hideObjs)
        {
            t.gameObject.SetActive(active);
        }
    }
}
```

### 1.2 Map Configuration Properties

| Property | Type | Purpose |
|----------|------|---------|
| `mapCentre` | Transform | Center point for astra spawning |
| `mapVertical` | Transform | Vertical reference point |
| `spawnPoints` | Transform[] | Team spawn locations (indexed by team - 1) |
| `obstacleColliders` | Transform[] | Environmental collision objects |

### 1.3 Specialized Map Configs

#### BhulokMapConfig (Standard Arena)

```csharp
public class BhulokMapConfig : MapConfig
{
    // No additional properties - uses base class
}
```

#### TutorialMapConfig

```csharp
public class TutorialMapConfig : MapConfig
{
    public Transform BotSpawnPoint;  // Special spawn for tutorial bot respawn
}
```

---

## 2. Map Types and Sizes

### 2.1 MapType Enum

```csharp
public enum MapType
{
    Bhulok,    // Standard arena
    Tutorial   // Tutorial-specific map
}
```

### 2.2 MapSize Enum

```csharp
public enum MapSize
{
    Default,   // No size suffix
    Small,     // "_Small" suffix
    Large      // "_Large" suffix
}
```

### 2.3 Match Type to Map Size Mapping

| Match Type | Map Size | Player Count |
|------------|----------|--------------|
| SOLO_1V1 | Small | 2 |
| SOLO_1V2 | Small | 3 |
| DUO_2V2 | Small | 4 |
| TRAINING | Small | Variable |
| FIRST_MATCH | Small | 2+ |
| SOLO_1V5 | Large | 6 |
| DUO_2V4 | Large | 6 |
| TRIO_3V3 | Large | 6 |
| TUTORIAL | Default | 2 |

---

## 3. Map Loading System

### 3.1 PrefabManager Map Loading

```csharp
public class PrefabManager : MonoBehaviour
{
    [EnumNamedArray(typeof(PrefabType))]
    public string[] filePaths;

    public GameObject LoadMapPrefab(GameManager.MapType mapType, GameManager.MapSize size)
    {
        // Build path: "{basePath}/{mapType}" or "{basePath}/{mapType}_{size}"
        string loadMapPrefab = $"{filePaths[(int)PrefabType.MAP]}/{mapType}" +
                               (size != GameManager.MapSize.Default ? $"_{size}" : "");

        Debug.Log(loadMapPrefab);

        GameObject mapData = Resources.Load<GameObject>(loadMapPrefab);
        GameObject mapPrefab = Instantiate(mapData, Vector3.zero, Quaternion.identity);
        return mapPrefab;
    }
}

public enum PrefabType
{
    CASTOBJECTS = 0,
    FIGHTINGSTYLES,
    SPELLEFFECTS,
    GODBONUS,
    FIGHTERATTRIBUTES,
    ASTRAS,
    MAP
}
```

### 3.2 Map Resource Paths

Based on the loading convention:
- `{MAP_BASE_PATH}/Bhulok` - Default Bhulok map
- `{MAP_BASE_PATH}/Bhulok_Small` - Small variant
- `{MAP_BASE_PATH}/Bhulok_Large` - Large variant
- `{MAP_BASE_PATH}/Tutorial` - Tutorial map

---

## 4. Map Initialization Flow

### 4.1 GameManager.Initialize()

```csharp
public void Initialize(byte[] data)
{
    // ... packet parsing ...

    // Determine map size based on match type
    MapSize size = MapSize.Large;  // Default to large

    switch (matchType)
    {
        case MatchType.SOLO_1V1:
        case MatchType.SOLO_1V2:
        case MatchType.DUO_2V2:
        case MatchType.TRAINING:
        case MatchType.FIRST_MATCH:
            size = MapSize.Small;
            break;
        default:
            break;  // Keep Large
    }

    // Load appropriate map
    GameObject mapObj;
    if (matchType == MatchType.TUTORIAL)
    {
        mapObj = PrefabManager.LoadMapPrefab(MapType.Tutorial, MapSize.Default);
        TutorialManager = gameObject.AddComponent<TutorialManager>();
    }
    else
    {
        mapObj = PrefabManager.LoadMapPrefab(MapType.Bhulok, size);
    }

    // Configure map
    if (mapObj != null)
    {
        mapObj.SetActive(true);
        mapObj.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        mapConfig = mapObj.GetComponent<MapConfig>();

        // Disable obstacle colliders during pregame
        mapConfig.ActiveAll(mapConfig.ObstacleColliders, false);
    }
}
```

### 4.2 Match Start - Enable Colliders

```csharp
public void StartMatch()
{
    // Enable obstacle colliders when match begins
    mapConfig.ActiveAll(mapConfig.ObstacleColliders, true);
}
```

---

## 5. Spawn System

### 5.1 Team-Based Spawning

```csharp
// GameManager.SpawnGameObject()
public GameObject SpawnGameObject(Player player, int team)
{
    // Calculate spawn position with team offset
    Vector3 spawnPosition = mapConfig.SpawnPoints[team - 1].transform.position +
                           new Vector3(1 * PlayerManager.GetTeamPlayerCount(team), 0, 0);

    // Face toward center (opposite spawn)
    Quaternion spawnRotation = Quaternion.LookRotation(
        mapConfig.SpawnPoints[team - 1].transform.forward, Vector3.up);

    // Instantiate player at spawn
    player = Instantiate(playerPrefab, spawnPosition, spawnRotation);
    return player;
}
```

### 5.2 Spawn Point Layout

```
Team-Based Spawn Points:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  SpawnPoints[0] (Team 1)            SpawnPoints[1] (Team 2) │
│  ┌─────────────────┐                ┌─────────────────┐     │
│  │ P1  P2  P3      │                │      P1  P2  P3 │     │
│  │ ───────────►    │                │    ◄─────────── │     │
│  │ (Facing Right)  │                │  (Facing Left)  │     │
│  └─────────────────┘                └─────────────────┘     │
│                                                             │
│                      ┌───────────┐                          │
│                      │ MapCenter │                          │
│                      │  (Astra)  │                          │
│                      └───────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Player Offset Calculation

```csharp
// Multiple players on same team spread horizontally
// TeamPlayerCount = 1: offset = 1 (1 * 1)
// TeamPlayerCount = 2: offset = 2 (1 * 2)
// TeamPlayerCount = 3: offset = 3 (1 * 3)

Vector3 offset = new Vector3(1 * PlayerManager.GetTeamPlayerCount(team), 0, 0);
```

---

## 6. Tutorial Map System

### 6.1 TutorialMapConfig

```csharp
public class TutorialMapConfig : MapConfig
{
    public Transform BotSpawnPoint;  // Used for bot respawn during tutorial
}
```

### 6.2 Tutorial Bot Respawn

```csharp
// PlayerBase.RespawnCharacter()
public void RespawnCharacter()
{
    if (character.player.IsDead())
    {
        // Restore stats
        character.player.playerData.stamina = character.player.playerStats.stamina;
        character.player.playerData.willPower = character.player.playerStats.willPower;

        character.stateManager.ChangeState(FSM.StateType.Idle);

        // Tutorial: teleport bot to special spawn point
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

## 7. Tutorial Manager

### 7.1 Tutorial State Progression

```csharp
public class TutorialManager : MonoBehaviour
{
    public BotState botState;
    bool botDamageIncrease;

    public void OnTutorialStateChange(UDPServerSocket.Peer peer, byte[] packet)
    {
        if (GameManager.Instance.matchType != MatchType.TUTORIAL)
            return;

        Packet.Tutorial_Progress pPacket = Serializer.Deserialize<Packet.Tutorial_Progress>(packet);
        Player player = PlayerManager.playerList[peer];

        switch (pPacket.state)
        {
            case 2:  // Set elementals
                SetupPlayerElementals(player, pPacket);
                break;

            case 3:  // Set god
                player.selectedGod = (TrinityGods)pPacket.god;
                player.SetBonuses();
                RestorePlayerStats(player);
                break;

            case 4:  // Restore focus (full)
                RestoreAllPlayersFocus(1f);
                break;

            case 5:  // Restore focus (half for player)
            case 6:  // Restore focus (zero for player)
                RestoreNonBotPlayersFocus(pPacket.state == 6 ? 0f : 0.5f);
                break;
        }

        // Update bot state
        botState = (BotState)pPacket.botState;
        botDamageIncrease = pPacket.botDamageIncrease != 0;
        UpdateBotStates();
    }
}
```

### 7.2 Tutorial State Values

| State | Purpose |
|-------|---------|
| 2 | Player selects elementals |
| 3 | Player selects god |
| 4 | Restore all focus to 100% |
| 5 | Restore player focus to 50% |
| 6 | Restore player focus to 0% |

### 7.3 Tutorial Damage Multipliers

```csharp
public float GetTutorialDamageMultiplier(Player sourcePlayer, Player targetPlayer)
{
    if (sourcePlayer.IsBot)
    {
        if (botDamageIncrease)
            return 10.0f;  // Bot damage increased (for teaching defense)
        else
            return 0.2f;   // Bot damage reduced to 20%
    }
    else
    {
        // Player damage
        if (botState == BotState.FULL)
            return 8f;     // Normal combat mode - 8x damage
        else if (botState == BotState.DISABLED)
            return 0f;     // No damage when bot disabled
        else
            return 10.0f;  // Training mode - 10x damage
    }
}
```

### 7.4 Tutorial Damage Multiplier Summary

| Source | Bot State | Damage Increase | Multiplier |
|--------|-----------|-----------------|------------|
| Bot | Any | Yes | 10.0× |
| Bot | Any | No | 0.2× |
| Player | FULL | - | 8.0× |
| Player | DISABLED | - | 0× |
| Player | Other | - | 10.0× |

---

## 8. Obstacle Collider System

### 8.1 Collider Activation

```csharp
// MapConfig.ActiveAll()
public void ActiveAll(Transform[] hideObjs, bool active)
{
    foreach (Transform t in hideObjs)
    {
        t.gameObject.SetActive(active);
    }
}
```

### 8.2 Collider State Transitions

```
Match Flow with Colliders:
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  Initialize()                StartMatch()           EndMatch() │
│       │                           │                     │      │
│       ▼                           ▼                     │      │
│  Colliders OFF              Colliders ON                │      │
│  (Players can move freely   (Environmental collision   │      │
│   during pregame)            active)                   │      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 8.3 Environment Tag Checking

```csharp
// Used by projectiles to detect environment collisions
public static bool CheckEnvironmentTag(string tag)
{
    // Returns true if tag is environment/wall
    return tag == "Environment" || tag == "Wall" || tag == "Obstacle";
}
```

---

## 9. MapCenter Usage (Astras)

### 9.1 Astra Spawn Locations

```csharp
// AstraManager.SpawnAstra()
public void SpawnAstra(Player sourcePlayer)
{
    switch (sourcePlayer.selectedGod)
    {
        case TrinityGods.Vishnu:  // Narayana Astra
            // Spawn at map center
            Vector3 spawnPosition = GameManager.Instance.mapConfig.MapCenter.position;
            // ...
            break;

        case TrinityGods.Shiva:  // Shiva Astra
            // Spawn at player position (not map center)
            spawnPosition = sourcePlayer.pGameObject.transform.position;
            // ...
            break;

        case TrinityGods.Brahma:  // Brahma Astra
            // Spawn at map center
            spawnPosition = GameManager.Instance.mapConfig.MapCenter.position;
            // ...
            break;
    }
}
```

### 9.2 Astra Spawn Positions

| Astra | Spawn Location |
|-------|----------------|
| Brahmastra | MapCenter |
| Narayana Astra | MapCenter |
| Shiva Astra | Player Position |

---

## 10. Scene Files

Based on the Unity project structure:

| Scene | Purpose |
|-------|---------|
| `Map_Hell.unity` | Main arena scene |
| `Collider_Heaven.unity` | Collision testing scene |
| `Collider_Hell.unity` | Collision testing scene |

---

## 11. Map Configuration Diagram

```
Map Structure:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        ARENA LAYOUT                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │   Team 1 Spawn        Map Center        Team 2 Spawn    │   │
│  │   ┌───────────┐      ┌───────────┐     ┌───────────┐   │   │
│  │   │ P1 P2 P3  │      │           │     │  P1 P2 P3 │   │   │
│  │   │    ───►   │      │     X     │     │   ◄───    │   │   │
│  │   │(forward)  │      │ (astras)  │     │(forward)  │   │   │
│  │   └───────────┘      └───────────┘     └───────────┘   │   │
│  │                                                         │   │
│  │   ┌─────┐                               ┌─────┐        │   │
│  │   │ OBS │  ◄── Obstacle Colliders ──►   │ OBS │        │   │
│  │   └─────┘                               └─────┘        │   │
│  │                                                         │   │
│  │                    ┌───────────┐                        │   │
│  │                    │ MapVertical│                       │   │
│  │                    │(reference) │                       │   │
│  │                    └───────────┘                        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Tutorial Map Additional:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│        ┌────────────────┐                                       │
│        │ BotSpawnPoint  │  ← Bot respawns here                  │
│        │   (Tutorial)   │                                       │
│        └────────────────┘                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. MatchType to Map Configuration

| MatchType | Map | Size | Notes |
|-----------|-----|------|-------|
| SOLO_1V1 | Bhulok | Small | 2 players |
| SOLO_1V2 | Bhulok | Small | 3 players |
| SOLO_1V5 | Bhulok | Large | 6 players |
| DUO_2V2 | Bhulok | Small | 4 players |
| DUO_2V4 | Bhulok | Large | 6 players |
| TRIO_3V3 | Bhulok | Large | 6 players |
| TRAINING | Bhulok | Small | Variable |
| TUTORIAL | Tutorial | Default | 1 player + bot |
| FIRST_MATCH | Bhulok | Small | New player match |
| NONE | N/A | N/A | No map loaded |

---

## 13. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `MapConfig.cs` | 30 | Base map configuration |
| `BhulokMapConfig.cs` | 9 | Standard arena config |
| `TutorialMapConfig.cs` | 7 | Tutorial map with bot spawn |
| `PrefabManager.cs` | 79 | Map/prefab loading system |
| `TutorialManager.cs` | 116 | Tutorial state management |
| `GameManager.cs (map section)` | ~50 | Map initialization logic |

**Total Map System: ~291 lines of code**

---

## 14. Environment Detection

### 14.1 Tag-Based Collision

Projectiles and entities use tag-based detection to identify environment:

```csharp
// Common environment tags
"Environment"
"Wall"
"Obstacle"
"Ground"
"Boundary"

// Check function
public static bool CheckEnvironmentTag(string tag)
{
    return tag == "Environment" ||
           tag == "Wall" ||
           tag == "Obstacle" ||
           tag == "Ground" ||
           tag == "Boundary";
}
```

### 14.2 Layer Mask Usage

```csharp
// Axe.cs uses LayerMask for enemy detection
public LayerMask enemyLayer;

// SphereCast with layer filtering
RaycastHit[] hits = Physics.SphereCastAll(
    transform.position,
    castRadius,
    direction,
    distance,
    enemyLayer
);
```

---

*Last Updated: January 21, 2026*
*Protocol Version: 13.0*
