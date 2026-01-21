# PROTOCOL-14-SERVER-SYSTEMS.md
# Core Server Systems - PlayerManager, CastManager, PrefabManager

## Overview

This document covers the core server-side management systems that handle player lifecycle, spell casting visualization, and asset loading. These systems are critical for match initialization and gameplay flow.

**Key Files:**
- `Assets/Scripts/Player/PlayerManager.cs` - Player lifecycle and input processing
- `Assets/Scripts/Managers/CastManager.cs` - Spell cast visualization
- `Assets/Scripts/Managers/PrefabManager.cs` - Asset/resource loading

---

## 1. PlayerManager

### 1.1 Overview

`PlayerManager` is a **static class** that manages all connected players, handles authentication, and processes player input on the server.

```csharp
public static class PlayerManager
{
    static System.Random r = new System.Random();

    // Active players indexed by network peer
    public static ConcurrentDictionary<UDPServerSocket.Peer, Player> playerList = new();

    // Expected players from MatchKeeper (pre-match data)
    public static ConcurrentDictionary<string, MKPacket.MKMatchAvatar> avatarList = new();
}
```

### 1.2 Data Structures

| Dictionary | Key | Value | Purpose |
|------------|-----|-------|---------|
| `playerList` | `UDPServerSocket.Peer` | `Player` | Active connected players |
| `avatarList` | `string` (SessionUUID) | `MKPacket.MKMatchAvatar` | Expected players from MatchKeeper |

### 1.3 Authentication Flow

```csharp
public static Player AuthenticatePlayer(UDPServerSocket.Peer peer, string SessionUUID)
{
    // 1. Validate match state (must be PREMATCH or TELEPORT)
    var currentState = MatchState.Instance.GetMatchState();
    if (currentState != MatchState.MatchStates.PREMATCH &&
        currentState != MatchState.MatchStates.TELEPORT)
    {
        return null;  // Reject late connections
    }

    // 2. Check for wildcard mode (PlayFab bot matches)
    bool wildcardMode = TestModeManager.AcceptAnySession;

    // 3. Look up session in avatarList
    foreach (var playerData in avatarList.ToArray())
    {
        bool isMatch = playerData.Key == SessionUUID;
        bool isWildcard = wildcardMode && playerData.Key == "*" && playerData.Value.IsBot == 0;

        if (!isMatch && !isWildcard) continue;

        // 4. Check for duplicate player
        foreach (Player player in playerList.Values)
        {
            if (player.uniqueCode == avatar.UniqueID)
                return null;  // Already joined
        }

        // 5. Initialize player
        Player newPlayer = InitializeAvatar(peer, playerData.Value);

        // 6. Broadcast authentication to all players
        BroadcastAuthenticateReply(newPlayer);

        // 7. Send existing players to new player
        SendExistingPlayersToNewPlayer(newPlayer);

        return newPlayer;
    }

    // Session not found - close connection
    peer.Close();
    return null;
}
```

### 1.4 Player Initialization

```csharp
private static Player InitializeAvatar(UDPServerSocket.Peer peer, MKPacket.MKMatchAvatar avatar)
{
    // 1. Create GameObject
    GameObject playerGameObject = GameManager.Instance.CreatePlayerGameObject(
        "Player-" + avatar.UniqueID,
        (int)avatar.teamID
    );

    // 2. Create Player instance
    Player newPlayer = new Player(
        (FightingStyles)avatar.fightingStyle,
        (TrinityGods)avatar.godSelected
    )
    {
        peer = peer,
        uniqueCode = avatar.UniqueID,
        avatarUUID = new Guid(avatar.avatarUniqueID),
        nickName = avatar.nickName,
        pGameObject = playerGameObject,
        team = (byte)avatar.teamID,
        WeaponType = (byte)avatar.weaponVariant,
        IsBot = avatar.IsBot == 1,
        spawnPosition = new Vector2(playerGameObject.transform.position.x,
                                    playerGameObject.transform.position.z),
        spawnRotation = playerGameObject.transform.localEulerAngles.y
    };

    // 3. Initialize elementals (MantraMuktha gets 4, others get 2)
    int elementalCount = (newPlayer.fightingStyle == FightingStyles.MantraMuktha) ? 4 : 2;
    newPlayer.elementals = new Elemental[elementalCount];
    for (int i = 0; i < elementalCount; i++)
    {
        newPlayer.elementals[i] = new Elemental(avatar.elementalSelected[i]);
    }

    // 4. Initialize PlayerBase component
    PlayerBase playerBase = playerGameObject.GetComponent<PlayerBase>();
    playerBase.Initialize(newPlayer);
    newPlayer.playerStats.SetAttackSpeeds(playerBase.AttackAnim_Divider, playerBase.Animation_Divider);

    // 5. Initialize CastManager
    newPlayer.character.castManager = playerGameObject.AddComponent<CastManager>()
        .Instantiate(newPlayer.elementals, newPlayer);

    // 6. Add to player list
    playerList.TryAdd(peer, newPlayer);

    return newPlayer;
}
```

### 1.5 Input Processing

#### ProcessPlayerInput (Packet Handler)

```csharp
public static void ProcessPlayerInput(UDPServerSocket.Peer peer, byte[] packet)
{
    if (!playerList.TryGetValue(peer, out Player player)) return;

    int simulationCount = packet[2] - 1;
    Packet.TickInput latestInput = Serializer.Deserialize<Packet.TickInput>(packet.Skip(3).ToArray());

    // Discard old/duplicate ticks
    if (latestInput.currentTick <= player.currentTick) return;

    // Handle missing ticks (packet loss recovery)
    if (latestInput.currentTick != player.currentTick + 1)
    {
        int missingTicks = (int)latestInput.currentTick - (int)(player.currentTick + 1);
        missingTicks = Math.Min(missingTicks, simulationCount);

        // Read back previous inputs from packet
        for (int i = missingTicks; i > 0; i--)
        {
            Packet.TickInput oldInput = Serializer.Deserialize<Packet.TickInput>(
                packet.Skip(3 + (Utils.GetSize(typeof(Packet.TickInput)) * i)).ToArray()
            );
            player.inputs.EnqueuePlayerInput(oldInput);
        }
    }

    player.inputs.EnqueuePlayerInput(latestInput);
    player.currentTick = latestInput.currentTick;
}
```

#### ProcessPlayerInputTick (Per-Tick Logic)

The main input processing function handles all player actions:

```csharp
public static void ProcessPlayerInputTick(Player player, KeyInput input)
{
    // Extract joystick values from packed byte
    int joy_y = input.JoystickAxis & 0xF;
    int joy_x = ((int)input.JoystickAxis >> 4) & 0xF;
    joy_x = joy_x == 0xF ? -1 : joy_x;
    joy_y = joy_y == 0xF ? -1 : joy_y;

    MatchState.MatchStates currentMatchState = MatchState.Instance.GetMatchState();

    // TELEPORT state handling
    if (currentMatchState == MatchState.MatchStates.TELEPORT)
    {
        if (!player.teleportDone && input.state == FSM.StateType.Teleport)
        {
            player.character.stateManager.ChangeState(FSM.StateType.Teleport);
            player.teleportDone = true;
        }
        return;
    }

    // PREMATCH/MATCH input handling
    if (currentMatchState == MatchState.MatchStates.PREMATCH ||
        currentMatchState == MatchState.MatchStates.MATCH)
    {
        // Dodge handling
        HandleDodgeInput(player, input);
    }

    if (currentMatchState == MatchState.MatchStates.MATCH)
    {
        // Special ability (character-specific)
        HandleSpecialInput(player, input);

        // Astra (ultimate)
        HandleAstraInput(player, input);

        // Melee attack
        HandleMeleeInput(player, input);

        // God-specific abilities (Brahma shield, Shiva third eye)
        HandleAbilityExInput(player, input);

        // Elemental spells (4 buttons)
        HandleElementalInput(player, input);

        // Third Eye tick processing
        HandleThirdEyeTick(player);
    }

    // Camera rotation (if not blocked)
    if (!player.character.stateManager.IsBlockingInput((uint)FSM.BlockFlags.Block_Camera))
    {
        player.pGameObject.transform.rotation = Quaternion.AngleAxis(input.cameraRotation, Vector3.up);
    }

    // Movement (if not blocked)
    if (!player.character.stateManager.IsBlockingInput((uint)FSM.BlockFlags.Block_JoystickAxis))
    {
        float speed = GetMovementSpeed(player, joy_x, joy_y);
        player.pGameObject.GetComponent<CharacterController>().Move(
            (player.pGameObject.transform.right * joy_x +
             player.pGameObject.transform.forward * joy_y).normalized * speed * 0.02f
        );
    }

    // Execute state update
    player.character.stateManager.ExecuteStateUpdate(input.serverTick, input.tick);

    // State recovery handling (pushback, special, astra, spell, third eye)
    HandleStateRecovery(player, input);

    // Send simulation result to client
    SendSimulationResult(player, input);
}
```

### 1.6 Movement Speed Calculation

```csharp
private static float GetMovementSpeed(Player player, int x, int y)
{
    float max_speed = player.GetMovementSpeed();
    float speed = max_speed;

    // Directional penalties
    if (y == -1 && x == 0)
        speed = max_speed * 0.7f;       // Backwards: 70%
    else if (y == -1 && x != 0)
        speed = max_speed * 0.7f;       // Backwards-diagonal: 70%
    else if (y == 1 && x != 0)
        speed = max_speed * 0.85f;      // Forward-diagonal: 85%
    else if (y == 0 && x != 0)
        speed = max_speed * 0.85f;      // Strafe: 85%

    // Vishnu speed bonus
    speed *= player.GetVishnuSpeedFactor(true);

    // Slow effect penalty
    speed *= player.GetSlowEffect();

    // Melee state penalty (40% speed while attacking)
    bool meleeMoveSlow = FSM.StateManager.IsInMeleeState(player.character.stateManager.GetState());
    return meleeMoveSlow ? speed * 0.4f : speed;
}
```

### 1.7 Stamina Regeneration

```csharp
public static void RegenStamina(float deltaTime)
{
    foreach (var player in playerList.Values)
    {
        if (player.IsDead()) continue;

        var data = player.playerData;
        float max = player.playerStats.stamina;

        // Third Eye: instant full stamina
        if (player.IsThirdEyeActive())
        {
            data.stamina = max;
            data.staminaCooldown = 0f;
        }

        // Cooldown > 0: still cooling down
        if (data.staminaCooldown > 0f)
        {
            data.staminaCooldown = MathF.Max(0f, data.staminaCooldown - deltaTime);
            continue;
        }

        // Cooldown < 0: waiting state (regen paused)
        if (data.staminaCooldown < 0f) continue;

        // Cooldown == 0: regenerate
        if (data.stamina < max)
        {
            float regenRate = max / 3f;  // Full bar in 3 seconds
            data.stamina = MathF.Min(max, data.stamina + regenRate * deltaTime);
        }
    }
}
```

### 1.8 Other Methods

| Method | Purpose |
|--------|---------|
| `GetTeamPlayerCount(int team)` | Count players on a team |
| `RemovePlayer(UDPServerSocket.Peer)` | Mark player inactive, clear inputs |
| `RespawnCharacter(peer, packet)` | Tutorial bot respawn |
| `ProcessPlayerKarma(peer, packet)` | Post-match karma voting |

---

## 2. CastManager

### 2.1 Overview

`CastManager` handles spell casting visualization - the aiming guides and channel indicators for elemental spells.

```csharp
public class CastManager : MonoBehaviour
{
    private SpellCastObject[] ActiveCasts;  // One per elemental
    private SpellCastObject currentSpell;   // Currently active spell
    private int currentChannel = 0;         // Channel progress (frames)
    private int maxChannelFrames = 0;       // Max channel time
}
```

### 2.2 Initialization

```csharp
public CastManager Instantiate(Elemental[] elementals, Player player)
{
    ActiveCasts = new SpellCastObject[elementals.Length];

    for (int i = 0; i < ActiveCasts.Length; i++)
    {
        // Load cast prefab for this elemental
        GameObject castObj = GameManager.Instance.PrefabManager.LoadCastPrefab(
            elementals[i].GetElemental(), 0, 0
        );
        castObj.SetActive(false);

        // Create SpellCastObject wrapper
        ActiveCasts[i] = new SpellCastObject(castObj, castObj.GetComponent<SpellCastAttributes>());

        // Parent to player and position
        castObj.transform.SetParent(player.pGameObject.transform);
        castObj.transform.localPosition = new Vector3(0, 0.2f, 0);
        castObj.transform.localRotation = Quaternion.Euler(Vector3.zero);

        // Add shield attributes
        ShieldCastAttributes shieldCastAttributes = castObj.AddComponent<ShieldCastAttributes>();
        elementals[i].spellCastAttributes = ActiveCasts[i].castAttributes;
        elementals[i].shieldCastAttributes = shieldCastAttributes;
    }

    return this;
}
```

### 2.3 Spell Cast Control

```csharp
// Select the spell to cast
public void SetCurrentCastObject(Elemental castElemental)
{
    foreach (SpellCastObject castObject in ActiveCasts)
    {
        if (castObject.castAttributes.GetSpellIndex() == castElemental.Value)
        {
            currentSpell = castObject;
            maxChannelFrames = (currentSpell.castAttributes.maxChannel /
                               GameManager.clientTickRateMS).ToInt();
            return;
        }
    }
}

// Activate the visual indicator
public void TriggerSpellCast()
{
    if (currentSpell == null)
    {
        Debug.LogError("current spell cast object is null");
        return;
    }
    currentSpell.castGameObject.SetActive(true);
}

// Deactivate on cancel/completion
public void CancelSpellCast()
{
    if (currentSpell != null)
    {
        currentSpell.castGameObject.SetActive(false);
        currentSpell = null;
    }
}
```

### 2.4 Channel Progress

```csharp
public bool IsChanellingDone()
{
    if (currentSpell == null)
    {
        Debug.Log("Current Spell Cast Object not set");
    }

    if (currentChannel >= maxChannelFrames)
    {
        ResetChannels();
        return true;
    }

    currentChannel += 1;
    return false;
}

public void ResetChannels()
{
    currentChannel = 0;
    maxChannelFrames = 0;
}
```

### 2.5 SpellCastObject Class

```csharp
public class SpellCastObject
{
    public GameObject castGameObject;        // Aiming guide visual
    public SpellCastAttributes castAttributes;  // Spell metadata

    public SpellCastObject(GameObject _castGameObject, SpellCastAttributes _castAttributes)
    {
        castGameObject = _castGameObject;
        castAttributes = _castAttributes;
    }
}
```

---

## 3. PrefabManager

### 3.1 Overview

`PrefabManager` loads game assets from the Resources folder using a path-based system.

```csharp
public class PrefabManager : MonoBehaviour
{
    [EnumNamedArray(typeof(PrefabType))]
    public string[] filePaths;  // Base paths for each prefab type
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

### 3.2 Loading Methods

#### Cast Prefabs

```csharp
public GameObject LoadCastPrefab(Elementals elemental, int SpellType, int EffectType)
{
    // Path: {CASTOBJECTS}/{Element}/{Element}_{SpellType}_{EffectType}
    GameObject castPrefab = Resources.Load<GameObject>(
        filePaths[(int)PrefabType.CASTOBJECTS] + "/" +
        elemental.ToString() + "/" +
        elemental.ToString() + "_" + SpellType + "_" + EffectType
    );
    return Instantiate(castPrefab, Vector3.zero, Quaternion.identity);
}
```

#### Character Prefabs

```csharp
public GameObject LoadAndInstantiateSelectedCharacterPrefab(FightingStyles selectedFightingStyle)
{
    // Path: {FIGHTINGSTYLES}/{FightingStyle}
    GameObject SelectedCharacterPrefab = Resources.Load<GameObject>(
        filePaths[(int)PrefabType.FIGHTINGSTYLES] + "/" + selectedFightingStyle
    );
    return Instantiate(SelectedCharacterPrefab, Vector3.zero, Quaternion.identity);
}
```

#### God Bonuses

```csharp
public GodBonuses LoadSelectedGodBonuses(TrinityGods selectedGod, FightingStyles selectedFighter)
{
    // Path: {GODBONUS}/{FightingStyle}/{GodIndex}
    GodBonuses godBonus = Resources.Load<GodBonuses>(
        filePaths[(int)PrefabType.GODBONUS] + "/" +
        selectedFighter + "/" + (int)selectedGod
    );
    return godBonus;
}
```

#### Fighter Attributes

```csharp
public FighterAttributes LoadSelectedFighterAttributes(FightingStyles selectedFightingStyle)
{
    // Path: {FIGHTERATTRIBUTES}/{FightingStyle}
    FighterAttributes fighterAttributes = Resources.Load<FighterAttributes>(
        filePaths[(int)PrefabType.FIGHTERATTRIBUTES] + "/" + selectedFightingStyle
    );
    return fighterAttributes;
}
```

#### Spell Effects

```csharp
public GameObject LoadSpellEffectPrefab(Elementals elemental, int spellType, int effectType)
{
    // Path: {SPELLEFFECTS}/{Element}/{Element}_{SpellType}_{EffectType}
    GameObject spellPrefab = Resources.Load<GameObject>(
        filePaths[(int)PrefabType.SPELLEFFECTS] + "/" +
        elemental.ToString() + "/" +
        elemental.ToString() + "_" + spellType + "_" + effectType
    );
    return spellPrefab;  // Note: returns prefab, not instantiated
}
```

#### Animation Frame Data

```csharp
public AnimationData[] LoadAnimFrameData(FightingStyles selectedFightingStyle)
{
    TextAsset animData = Resources.Load<TextAsset>("AnimationFrameData_" + selectedFightingStyle);
    return JsonHelper.FromJson<AnimationData>(animData.text);
}
```

#### Astra Prefabs

```csharp
public GameObject LoadAstraPrefab(TrinityGods selectedGod)
{
    // Path: {ASTRAS}/Astra_{GodName}
    GameObject astraPrefab = Resources.Load<GameObject>(
        filePaths[(int)PrefabType.ASTRAS] + "/Astra_" + selectedGod.ToString()
    );
    return astraPrefab;
}
```

#### Map Prefabs

```csharp
public GameObject LoadMapPrefab(GameManager.MapType mapType, GameManager.MapSize size)
{
    // Path: {MAP}/{MapType} or {MAP}/{MapType}_{Size}
    string loadMapPrefab = $"{filePaths[(int)PrefabType.MAP]}/{mapType}" +
                           (size != GameManager.MapSize.Default ? $"_{size}" : "");

    Debug.Log(loadMapPrefab);
    GameObject mapData = Resources.Load<GameObject>(loadMapPrefab);
    return Instantiate(mapData, Vector3.zero, Quaternion.identity);
}
```

### 3.3 Resource Path Summary

| PrefabType | Path Pattern | Example |
|------------|--------------|---------|
| CASTOBJECTS | `{base}/FIRE/FIRE_0_0` | Fire spell indicator |
| FIGHTINGSTYLES | `{base}/Amuktha` | Character prefab |
| SPELLEFFECTS | `{base}/WATER/WATER_1_2` | Spell VFX |
| GODBONUS | `{base}/Amuktha/0` | Brahma bonuses for Amuktha |
| FIGHTERATTRIBUTES | `{base}/MukthaMuktha` | Stats ScriptableObject |
| ASTRAS | `{base}/Astra_Vishnu` | Narayanastra prefab |
| MAP | `{base}/Bhulok_Small` | Small arena map |

---

## 4. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `PlayerManager.cs` | 677 | Player lifecycle, authentication, input processing |
| `CastManager.cs` | 131 | Spell cast visualization |
| `PrefabManager.cs` | 79 | Asset loading from Resources |

**Total: ~887 lines of code**

---

*Last Updated: January 21, 2026*
*Protocol Version: 14.0*
