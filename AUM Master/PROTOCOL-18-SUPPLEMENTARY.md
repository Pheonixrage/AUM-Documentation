# PROTOCOL-18-SUPPLEMENTARY.md
# Supplementary Systems - Social, Lobby, Camera, Audio, Scene Management, Server Allocation

## Overview

This document covers supplementary systems that support the core gameplay, including social features (friends, parties, lobbies), server allocation, visual systems (camera, audio), and scene management.

**Key Files:**
- `Assets/Scripts/Network/ServerAllocator.cs` - Orchestrator server allocation
- `Assets/Scripts/Managers/LobbyManager.cs` - Custom lobby system
- `Assets/Scripts/Managers/PartyManager.cs` - Party grouping system
- `Assets/Scripts/Managers/FriendsManager.cs` - Friends/social system
- `Assets/Scripts/Managers/ServerManager.cs` - World state processing
- `Assets/Scripts/Managers/TestModeClient.cs` - Development test mode
- `Assets/Scripts/Managers/SceneLoader.cs` - Async scene loading
- `Assets/Scripts/Managers/FindMatch.cs` - Matchmaking UI
- `Assets/Scripts/Camera/CameraController.cs` - Cinemachine camera system
- `Assets/Scripts/Sound/AudioManager.cs` - Audio management

---

## 1. ServerAllocator

### 1.1 Overview

`ServerAllocator` is a unified server allocation system that handles obtaining game server connections for all match types. It supports both orchestrator-based production allocation and local server testing.

```csharp
public class ServerAllocator : MonoBehaviour
{
    public static ServerAllocator Instance { get; private set; }

    // Orchestrator Configuration
    private string orchestratorURL = "http://65.109.133.129:8080/allocate";
    private string apiKey = "AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8";

    // Local Server Testing
    public bool useLocalServer = false;
    public string localServerIP = "127.0.0.1";
    public int localServerPort = 7777;
    public bool waitForOtherPlayers = false;

    // Allocated Server Info
    public bool IsAllocating { get; private set; }
    public bool HasAllocation { get; private set; }
    public string AllocatedIP { get; private set; }
    public int AllocatedPort { get; private set; }
    public string AllocatedMatchId { get; private set; }
    public MatchType AllocatedMatchType { get; private set; }
}
```

### 1.2 Allocation Modes

| Mode | Description | Usage |
|------|-------------|-------|
| **Orchestrator** | HTTP request to central server allocator | Production |
| **Local Server** | Direct connection to local IP:Port | Development |

### 1.3 Request Server

```csharp
public void RequestServer(MatchType matchType, Action<string, int> onSuccess, Action<string> onFailed)
{
    if (IsAllocating) return;

    HasAllocation = false;
    AllocatedMatchType = matchType;

    if (useLocalServer)
    {
        // Local mode - immediate allocation
        AllocatedIP = localServerIP;
        AllocatedPort = localServerPort;
        AllocatedMatchId = $"local-{matchType}-{DateTime.Now.Ticks}";
        HasAllocation = true;
        onSuccess?.Invoke(AllocatedIP, AllocatedPort);
    }
    else
    {
        // Orchestrator mode - HTTP request
        StartCoroutine(RequestFromOrchestrator(matchType, onSuccess, onFailed));
    }
}
```

### 1.4 Orchestrator Request/Response

#### Request Format
```csharp
[Serializable]
private class AllocationRequest
{
    public string matchType;   // "TUTORIAL", "SOLO_1V1", etc.
    public string playerId;    // PlayFab ID
    public int minPlayers;     // Minimum players for match type
}
```

#### Response Format
```csharp
[Serializable]
private class AllocationResponse
{
    public bool success;
    public string ip;          // Allocated server IP
    public int port;           // Allocated server port
    public string matchId;     // Unique match identifier
    public string error;       // Error message if failed
}
```

### 1.5 Match Type Mapping

| MatchType | Name | MinPlayers |
|-----------|------|------------|
| Tutorial | "TUTORIAL" | 1 |
| Solo_1v1 | "SOLO_1V1" | 1 |
| Solo_1v2 | "SOLO_1V2" | 1 |
| Solo_1v5 | "SOLO_1V5" | 1 |
| Duo_2v2 | "DUO_2V2" | 2 |
| Duo_2v4 | "DUO_2V4" | 2 |
| Trio_3v3 | "TRIO_3V3" | 3 |
| Training | "TRAINING" | 1 |

### 1.6 Utility Methods

```csharp
// Clear allocation data (call when returning to main menu)
public void ClearAllocation()
{
    HasAllocation = false;
    AllocatedIP = "";
    AllocatedPort = 0;
    AllocatedMatchId = "";
}

// Cancel ongoing allocation
public void CancelAllocation()
{
    if (allocationCoroutine != null)
    {
        StopCoroutine(allocationCoroutine);
        allocationCoroutine = null;
    }
    IsAllocating = false;
}
```

### 1.7 Usage Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SERVER ALLOCATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User starts match                                                      │
│       │                                                                 │
│       ▼                                                                 │
│  ServerAllocator.RequestServer(matchType, onSuccess, onFailed)          │
│       │                                                                 │
│       ├────────────────────┬────────────────────┐                       │
│       │                    │                    │                       │
│       ▼                    ▼                    │                       │
│  useLocalServer?      Orchestrator Mode        │                       │
│       │                    │                    │                       │
│       ▼                    ▼                    │                       │
│  Immediate return     POST /allocate           │                       │
│  (local IP:Port)      (HTTP request)           │                       │
│       │                    │                    │                       │
│       └────────────────────┴────────────────────┘                       │
│                            │                                            │
│                            ▼                                            │
│                   onSuccess(IP, Port)                                   │
│                            │                                            │
│                            ▼                                            │
│                   GameManager reads:                                    │
│                   - ServerAllocator.Instance.AllocatedIP                │
│                   - ServerAllocator.Instance.AllocatedPort              │
│                            │                                            │
│                            ▼                                            │
│                   NetworkManager.ConnectToServer()                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. LobbyManager

### 2.1 Overview

`LobbyManager` handles custom lobby creation, joining, and management for private/public matches.

```csharp
public class LobbyManager : Singleton<LobbyManager>
{
    public List<LobbyInfo> availableLobbies = new();
    public LobbyData currentLobby = null;
    public string selectedFriendId = string.Empty;

    public string currentLobbyId = string.Empty;
    public bool isLobbyHost = false;
    public bool isInLobby = false;
    public int lobbyPlayerCount = 0;
    public bool isSlotSwaping = false;
    public bool isPacketProcessPending = false;
}
```

### 1.2 Lobby Packet Operations

#### Create Lobby
```csharp
public void CreateLobby(byte loka, byte region, byte matchMode, bool allowBots, bool isPublic, string password)
{
    LobbyCreateRequest req = new()
    {
        packetType = (UInt16)PacketType.LOBBY_CREATE_REQUEST,
        matchMode = matchMode,
        loka = loka,
        isPublic = (byte)(isPublic ? 1 : 0),
        allowBots = (byte)(allowBots ? 1 : 0),
        region = (byte)region,
        password = password
    };
    byte[] serialized = Serializer.Serialize(req);
    WebSocketConnector.Instance.SendPacket(serialized);
}
```

#### Join Lobby
```csharp
public void JoinLobby(UInt32 lobbyId, string password)
{
    var requestPacket = new AUM.JoinLobbyRequest
    {
        packetType = (UInt16)PacketType.LOBBY_JOIN_REQUEST,
        lobbyID = lobbyId,
        password = password,
    };
    byte[] serialized = Serializer.Serialize(requestPacket);
    WebSocketConnector.Instance.SendPacket(serialized);
}
```

#### Lobby Invite
```csharp
public void LobbyInviteRequest(string friendId)
{
    var requestPacket = new AUM.LobbyInviteRequest
    {
        packetType = (UInt16)PacketType.LOBBY_INVITE_REQUEST,
        friendID = friendId
    };
    byte[] serialized = Serializer.Serialize(requestPacket);
    WebSocketConnector.Instance.SendPacket(serialized);
}
```

### 1.3 Lobby Join Response Codes

| Code | Meaning |
|------|---------|
| 0 | Lobby doesn't exist |
| 1 | Lobby is full |
| 2 | Successfully joined |
| 3 | Incorrect password |
| 4 | Game already started |

### 1.4 LobbyData Structure

```csharp
[Serializable]
public class LobbyData
{
    public string lobbyID;
    public string hostName;
    public string hostFriendID;
    public byte loka;
    public byte region;
    public byte matchMode;
    public bool isPublic;
    public bool allowBots;
    public byte playerCount;
    public byte maxPlayers;
    public string password;
    public List<LobbyPlayerInfo> playersInfos = new List<LobbyPlayerInfo>();
}
```

### 1.5 Server Region Enum

```csharp
public enum ServerRegion
{
    INDIA = 0
}
```

---

## 2. PartyManager

### 2.1 Overview

`PartyManager` handles party creation and management for grouped matchmaking.

```csharp
public class PartyManager : Singleton<PartyManager>
{
    public string currentPartyId = string.Empty;
    public bool isPartyHost;
    public bool isInParty;
    public PartyData currentParty;
    public string selectedFriendId = string.Empty;
    public string hostId = string.Empty;
    public bool PartyEnabled { get; set; }
}
```

### 2.2 Party Packet Operations

#### Invite to Party
```csharp
public void PartyInviteRequest(string friendId)
{
    AUM.PartyInviteRequest packet = new()
    {
        packetType = (UInt16)AUM.PacketType.PARTY_INVITE_REQUEST,
        friendId = friendId,
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

#### Reply to Invite
```csharp
public void PartyInviteReply(byte isAccepted, string friendID)
{
    AUM.PartyInviteReply packet = new()
    {
        packetType = (UInt16)AUM.PacketType.PARTY_INVITE_REPLY,
        friendId = friendID,
        isAccepted = isAccepted
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

#### Leave Party
```csharp
public void LeavePartyRequest()
{
    AUM.PartyLeaveRequest packet = new()
    {
        packetType = (UInt16)AUM.PacketType.LEAVE_PARTY,
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

#### Make Leader
```csharp
public void MakeLeaderRequest(string friendID)
{
    AUM.PartyMakeLeaderRequest packet = new()
    {
        packetType = (UInt16)AUM.PacketType.PARTY_MAKE_LEADER,
        friendId = friendID,
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

### 2.3 PartyData Structure

```csharp
[Serializable]
public class PartyData
{
    public string partyId;
    public List<PartyPlayers> partyPlayers = new List<PartyPlayers>();
}
```

---

## 3. FriendsManager

### 3.1 Overview

`FriendsManager` handles the friends list, friend requests, and social interactions.

```csharp
public class FriendsManager : Singleton<FriendsManager>
{
    public int requestCount = 0;
    public string myFriendId;
    public string profileName;
    public List<Friend_Info> friendsList = new List<Friend_Info>();
}
```

### 3.2 Friend Packet Operations

#### Search for Friend
```csharp
public void SendFrienSearchRequest(string uniqueID)
{
    AUM.FriendSearch_Request packet = new()
    {
        packetType = (UInt16)AUM.PacketType.FRIENDS_SEARCH_REQUEST,
        friendId = uniqueID
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

#### Send Friend Request
```csharp
public void SendFriendRequest(string friendId, Action onCompleted)
{
    AUM.Friend_Request packet = new()
    {
        packetType = (UInt16)AUM.PacketType.FRIEND_REQUEST,
        friendId = friendId
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
    onCompleted?.Invoke();
}
```

#### Remove Friend
```csharp
public void RemoveFriend(string friendId)
{
    AUM.Remove_Friend packet = new()
    {
        packetType = (UInt16)AUM.PacketType.REMOVE_FRIEND,
        friendId = friendId,
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

#### Toggle Favourite
```csharp
public void ToggleFavourite(string friendId, byte isFav)
{
    AUM.Toggle_Favourite packet = new()
    {
        packetType = (UInt16)AUM.PacketType.TOGGLE_FAVOURITE,
        isFavourite = isFav,
        friendId = friendId,
    };
    byte[] serializedPacket = Serializer.Serialize(packet);
    WebSocketConnector.Instance.SendPacket(serializedPacket);
}
```

### 3.3 FriendGameState Enum

```csharp
public enum FriendGameState
{
    FreeToJoin = 0,
    InParty = 1,
    InPrivateLobby = 2,
    InPublicLobby = 3,
    InGame = 4,
}
```

### 3.4 Friend Sorting

Friends are sorted by priority:
1. Online + Favourite (alphabetically)
2. Online (alphabetically)
3. Offline (alphabetically)
4. Pending (alphabetically)

```csharp
friendsList = friendsList
    .OrderByDescending(f => f.isOnline == 1)
    .ThenByDescending(f => f.isFav == 1)
    .ThenBy(f => f.isPending != 0)
    .ThenBy(f => f.profileName)
    .ToList();
```

---

## 4. ServerManager

### 4.1 Overview

`ServerManager` processes world state snapshots received from the game server.

```csharp
public class ServerManager : MonoBehaviour
{
    public UInt32 currentServerSnaphot;
    public UInt32 processedServerSnapshot;

    public static ServerManager Instance => GameManager.Instance.ServerManager;
}
```

### 4.2 World State Processing

```csharp
public void ProcessWorldStateMessage(byte[] packetData, long receivedTimestamp)
{
    int worldStates = packetData[2] - 1;
    UInt16 snapshotSize = BitConverter.ToUInt16(packetData, 3);
    UInt32 snapshotIndex = BitConverter.ToUInt32(packetData, 5);

    // Skip if already processed
    if (snapshotIndex <= currentServerSnaphot)
        return;

    // Handle missing snapshots by reading previous states
    else if (snapshotIndex != currentServerSnaphot + 1)
    {
        if (worldStates > 0)
        {
            // Read from previous snapshots in packet
            for (int i = 0; i < worldStates; i++)
            {
                // Process historical snapshots...
            }
        }
    }

    // Process latest snapshot
    ProcessSnapshot(packetData.Skip(3 + 2).Take(snapshotSize).ToArray(), receivedTimestamp);
    currentServerSnaphot = snapshotIndex;
}
```

### 4.3 Snapshot Processing

Each snapshot contains:
- Player positions and states
- Entity data (projectiles, spells)
- Stamina, willpower, focus values

```csharp
private void ProcessSnapshot(byte[] snapshotData, long receivedTimestamp)
{
    UInt32 snapshotIndex = BitConverter.ToUInt32(snapshotData, 0);
    int numSnapshotPlayers = snapshotData[4];

    for (int i = 0; i < numSnapshotPlayers; i++)
    {
        Packet.See_MoveCharacter moveCharacter = Serializer.Deserialize<Packet.See_MoveCharacter>(...);

        if (PlayerManager.Instance.NetworkPlayers.TryGetValue(moveCharacter.pUniqueID, out Player player))
        {
            // Update player simulation data
            player.simulationManager.AddSimulation(new Simulation()
            {
                simulationTick = snapshotIndex,
                position = new Vector2(moveCharacter.positionX, moveCharacter.positionZ),
                state = (FSM.StateType)moveCharacter.state,
                // ...
            });
        }
    }

    // Process entities
    GameManager.Instance.EntityManager.CheckEntity(entityData);
}
```

---

## 5. TestModeClient

### 5.1 Overview

`TestModeClient` enables direct server connection for development testing, bypassing MatchKeeper authentication.

```csharp
[DefaultExecutionOrder(-100)]  // Runs BEFORE GameManager
public class TestModeClient : MonoBehaviour
{
    private const string PLAYER_1_SESSION = "test-player-1-session";
    private const string PLAYER_2_SESSION = "test-player-2-session";

    public static bool DidSetupThisSession { get; private set; } = false;

    public int playerSlot = 1;
    public string testServerIP = "65.109.133.129";
    public int testServerPort = 6006;
    public bool autoSetup = true;
    public bool autoConnect = true;
}
```

### 5.2 Session ID Generation

Uses MD5 hash to create deterministic GUIDs matching server expectations:

```csharp
private static Guid CreateDeterministicGuid(string input)
{
    using (var md5 = MD5.Create())
    {
        byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(input));
        return new Guid(hash);
    }
}
```

### 5.3 Test Mode vs PlayFab Mode

```csharp
private bool IsPlayFabModeActive()
{
    bool isPlayFabSession = PlayerPrefs.GetInt("IsPlayFabMatchSession", 0) == 1;
    if (!isPlayFabSession) return false;

    string serverIP = PlayerPrefs.GetString("GameServerIP", "");
    int serverPort = PlayerPrefs.GetInt("GameServerPort", 0);
    bool hasMatchData = InterfaceManager.Instance?.match_Avatars?.Length > 0;

    return !string.IsNullOrEmpty(serverIP) && serverPort > 0 && hasMatchData;
}
```

### 5.4 Match Avatar Setup

```csharp
private void SetupMatchAvatars()
{
    InterfaceManager.Instance.match_Avatars = new AUM.Match_Avatar[2];

    // Player 1
    InterfaceManager.Instance.match_Avatars[0] = new AUM.Match_Avatar
    {
        uniqueID = 1,
        teamID = 1,
        nickName = player1Name,
        fightingStyle = (byte)player1Style,
        godSelected = (byte)player1God,
        elementalSelected = new byte[] { 0, 1, 2, 3 },
        // ...
    };

    // Player 2 (Bot)
    InterfaceManager.Instance.match_Avatars[1] = new AUM.Match_Avatar
    {
        uniqueID = 2,
        teamID = 2,
        // ...
    };

    InterfaceManager.Instance.localPlayerID = (uint)playerSlot;
}
```

---

## 6. SceneLoader

### 6.1 Overview

`SceneLoader` handles asynchronous scene transitions with a loading screen.

```csharp
public class SceneLoader : Singleton<SceneLoader>
{
    readonly string loadingSceneName = "Loading";
    private string currentLoadingScene;
    private bool isLoadingScene;
    public string LoadingText;
}
```

### 6.2 Async Scene Loading Flow

```
1. Load "Loading" scene (additive)
2. Unload current active scene
3. Unload unused assets
4. Load target scene (additive)
5. Set target as active scene
6. Unload "Loading" scene
7. Unload unused assets again
```

```csharp
public IEnumerator AsyncSceneLoader(string sceneName)
{
    redo:
    Scene activeScene = SceneManager.GetActiveScene();

    // Load loading screen
    AsyncOperation sceneOp = SceneManager.LoadSceneAsync(loadingSceneName, LoadSceneMode.Additive);
    while (!sceneOp.isDone) yield return null;

    // Unload previous scene
    AsyncOperation unloadActiveSceneOp = SceneManager.UnloadSceneAsync(activeScene);
    while (!unloadActiveSceneOp.isDone) yield return null;

    // Clean up
    AsyncOperation unloadPreviousSceneAssetsOp = Resources.UnloadUnusedAssets();
    while (!unloadPreviousSceneAssetsOp.isDone) yield return null;

    // Load target scene
    AsyncOperation loadNextScene = SceneManager.LoadSceneAsync(sceneName, LoadSceneMode.Additive);
    while (!loadNextScene.isDone) yield return null;

    SceneManager.SetActiveScene(SceneManager.GetSceneByName(sceneName));

    // Unload loading screen
    AsyncOperation unloadLoadingOp = SceneManager.UnloadSceneAsync(loadingSceneName);
    while (!unloadLoadingOp.isDone) yield return null;

    // Handle scene change during load
    if (SceneManager.GetActiveScene().name != currentLoadingScene)
    {
        sceneName = currentLoadingScene;
        goto redo;
    }

    isLoadingScene = false;
}
```

---

## 7. FindMatch

### 7.1 Overview

`FindMatch` is a UI component that displays matchmaking progress with an animated timer.

```csharp
public class FindMatch : MonoBehaviour
{
    [SerializeField] Text findmatchText;
    [SerializeField] Vector3 offset;
    float currentTime = 0f;

    public delegate void OnMatchFinding(bool enable);
    public OnMatchFinding onMatchFinding;
}
```

### 7.2 Timer Display

```csharp
void Update()
{
    currentTime += Time.deltaTime;
    TimeSpan timer = TimeSpan.FromSeconds(currentTime);
    findmatchText.text = timer.ToString(@"mm\:ss");  // Format: 00:00
}
```

### 7.3 Animation

Uses DOTween for slide-in/slide-out animations:

```csharp
void OnEnable()
{
    transform.position = startPos;
    transform.DOMove(endPos, 0.4f);
    // ...
}

public void OnDecline()
{
    transform.DOKill();
    transform.DOMove(startPos, 0.5f).OnComplete(delegate {
        gameObject.SetActive(false);
    });
    onMatchFinding?.Invoke(true);
}
```

---

## 8. CameraController

### 8.1 Overview

`CameraController` manages Cinemachine virtual cameras for gameplay, using Unity Events for state-driven transitions.

```csharp
public class CameraController : MonoBehaviour
{
    CinemachineStateDrivenCamera cm_StateMachine;
    CinemachineVirtualCameraBase freeFollowCam;
    CinemachineCamera currentShakeCam;

    public CinemachineCamera astraCam;
    public CinemachineCamera teleportCam;
    public CinemachineCamera attackCam;
    public CinemachineCamera aimCam;
    public CinemachineVirtualCameraBase spectatorCam;
}
```

### 8.2 Camera Events

```csharp
public static UnityEvent<string> OnPlayerAttack = new UnityEvent<string>();
public static UnityEvent<string, bool> OnPlayerAim = new UnityEvent<string, bool>();
public static UnityEvent<int> OnAstraChannel = new UnityEvent<int>();
public static UnityEvent<int> OnAstraCast = new UnityEvent<int>();
public static UnityEvent<int> OnSpellAim = new UnityEvent<int>();
public static UnityEvent<int> OnSpellCast = new UnityEvent<int>();
public static UnityEvent<bool> OnTeleport = new UnityEvent<bool>();
public static UnityEvent<bool> OnVictory = new UnityEvent<bool>();
public static UnityEvent<CinemachineCamera, float, float> OnCameraShake = new UnityEvent<CinemachineCamera, float, float>();
public static UnityEvent<Transform, Player> OnCameraAim = new UnityEvent<Transform, Player>();
```

### 8.3 Initialization

```csharp
public void Initialize(Transform _target, Transform teleportTarget)
{
    cm_StateMachine = GetComponent<CinemachineStateDrivenCamera>();
    freeFollowCam = cm_StateMachine.ChildCameras[0];
    anim = GetComponent<Animator>();

    cm_StateMachine.Follow = _target;
    cm_StateMachine.LookAt = _target;

    followCamTransposer = freeFollowCam.GetCinemachineComponent(CinemachineCore.Stage.Body) as CinemachineFollow;
    followCamComposer = freeFollowCam.GetCinemachineComponent(CinemachineCore.Stage.Aim) as CinemachineRotationComposer;

    followCamTransposer.FollowOffset = originalFollowOffset;
    followCamComposer.TargetOffset = originalAimOffset;
}
```

### 8.4 Camera Shake

```csharp
void TriggerCamShake(CinemachineCamera selectedCam, float intensity, float time)
{
    CinemachineBasicMultiChannelPerlin multiChannelPerlin =
        selectedCam.GetCinemachineComponent(CinemachineCore.Stage.Noise) as CinemachineBasicMultiChannelPerlin;

    if (multiChannelPerlin != null)
        multiChannelPerlin.AmplitudeGain = intensity;

    currentShakeCam = selectedCam;
    shakerTimer = time;
}
```

### 8.5 ShakableVirtualCams Enum

```csharp
public enum ShakableVirtualCams
{
    EARTH_CAST_CAM,
    AXE_CALLBACK_CAM,
}
```

---

## 9. CameraShake

### 9.1 Overview

`CameraShake` provides Cinemachine Impulse-based camera shake for combat feedback.

```csharp
public class CameraShake : MonoBehaviour
{
    const float initShakeDisableTime = 2f;

    [SerializeField] CinemachineImpulseSource normalHit;
    [SerializeField] CinemachineImpulseSource heavyHit;
    [SerializeField] CinemachineImpulseSource normalRecoil;
    [SerializeField] CinemachineImpulseSource heavyRecoil;
    [SerializeField] CinemachineImpulseSource fireShake;
    [SerializeField] CinemachineImpulseSource waterShake;
    [SerializeField] CinemachineImpulseSource earthShake;
    [SerializeField] CinemachineImpulseSource airShake;
    [SerializeField] CinemachineImpulseSource etherShake;
    [SerializeField] CinemachineImpulseSource astraCast;
    [SerializeField] CinemachineImpulseSource vishnuImpact;
    [SerializeField] CinemachineImpulseSource brahmaImpact;
    [SerializeField] CinemachineImpulseSource shivaImpact;

    public delegate void ImpulseDelegate(Vector3 position, ImpulseType type);
    static public ImpulseDelegate Shaker;
}
```

### 9.2 ImpulseType Enum

```csharp
public enum ImpulseType
{
    NormalHit,
    HeavyHit,
    NormalRecoil,
    HeavyRecoil,
    Fire,
    Water,
    Earth,
    Air,
    Ether,
    AstraCast,
    VishnuImpact,
    BrahmaImpact,
    ShivaImpact
}
```

---

## 10. SmoothFollow

### 10.1 Overview

`SmoothFollow` provides smooth camera following with height and rotation damping.

```csharp
public class SmoothFollow : MonoBehaviour
{
    public Transform target = null;
    public bool shouldRotate = true;
    public float max_distance = 30f;
    public float heightDamping = 15f;
    public float rotationDamping = 10f;
}
```

### 10.2 CameraStates Enum

```csharp
public enum CameraStates
{
    FreeMoving,
    Aiming
}
```

---

## 11. AudioManager

### 11.1 Overview

`AudioManager` handles global audio playback for music and UI sound effects.

```csharp
public class AudioManager : Singleton<AudioManager>
{
    public AudioSource audioSource_music;
    public AudioSource audioSource_UIfx;
    public AudioContainer audioScriptableObject;
    public PrefabManager prefabManager;
    public AudioClip mainBG;
}
```

### 11.2 Initialization

```csharp
public void Initialize()
{
    if (prefabManager == null)
    {
        prefabManager = gameObject.GetOrAddComponent<PrefabManager>();
        audioScriptableObject = prefabManager.LoadGlobalAudioContainer();
    }

    if (audioSource_UIfx == null)
    {
        audioSource_UIfx = gameObject.AddComponent<AudioSource>();
        AudioMixer audioMixer = Resources.Load<AudioMixer>("Audio/Mixers/Music_UIFx");
        audioSource_UIfx.outputAudioMixerGroup = audioMixer.FindMatchingGroups("UIFx")[0];
    }
}
```

### 11.3 Audio Playback

```csharp
public void Trigger3DSound(AudioSource targetSource, AudioClip targetClip)
{
    targetSource.PlayOneShot(targetClip);
}

public void TriggerUISound(AudioClip audioClip)
{
    audioSource_UIfx?.PlayOneShot(audioClip);
}
```

### 11.4 AudioType Enum

```csharp
public enum AudioType
{
    Effects,
    Music
}
```

---

## 13. System Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SUPPLEMENTARY SYSTEMS FLOW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SERVER ALLOCATION                                                      │
│  ┌────────────────┐                                                     │
│  │ ServerAllocator│───▶ Orchestrator (HTTP) OR Local Server            │
│  └────────────────┘                                                     │
│         │                                                               │
│         ▼                                                               │
│  ┌────────────────┐                                                     │
│  │ NetworkManager │───▶ UDP Connection to allocated server             │
│  └────────────────┘                                                     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SOCIAL LAYER                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │FriendsManager│───▶│ PartyManager│───▶│ LobbyManager│                 │
│  │ (friends)   │    │ (grouping)  │    │ (matches)   │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         │                  │                  │                         │
│         └──────────────────┴──────────────────┘                         │
│                           │                                             │
│                           ▼                                             │
│                  WebSocketConnector                                     │
│                  (WSS packets)                                          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GAME CONNECTION                                                        │
│                                                                         │
│  ┌──────────────┐         ┌──────────────┐                             │
│  │TestModeClient│    OR   │PlayFab Match │                             │
│  │ (dev/debug)  │         │ (production) │                             │
│  └──────────────┘         └──────────────┘                             │
│         │                        │                                      │
│         └────────────┬───────────┘                                      │
│                      ▼                                                  │
│              ServerManager                                              │
│              (world state processing)                                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  VISUAL LAYER                                                           │
│                                                                         │
│  ┌────────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │CameraController│───▶│ CameraShake │    │ SmoothFollow│              │
│  │ (Cinemachine)  │    │ (impulses)  │    │ (fallback)  │              │
│  └────────────────┘    └─────────────┘    └─────────────┘              │
│                                                                         │
│  ┌─────────────┐       ┌─────────────┐                                 │
│  │AudioManager │       │ SceneLoader │                                 │
│  │ (sfx/music) │       │ (async load)│                                 │
│  └─────────────┘       └─────────────┘                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 14. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `ServerAllocator.cs` | 329 | Orchestrator server allocation |
| `LobbyManager.cs` | 392 | Custom lobby system |
| `PartyManager.cs` | 272 | Party grouping |
| `FriendsManager.cs` | 498 | Friends/social system |
| `ServerManager.cs` | 161 | World state processing |
| `TestModeClient.cs` | 449 | Development test mode |
| `SceneLoader.cs` | 78 | Async scene loading |
| `FindMatch.cs` | 74 | Matchmaking UI |
| `CameraController.cs` | 236 | Cinemachine controller |
| `CameraShake.cs` | 168 | Impulse-based shake |
| `SmoothFollow.cs` | 73 | Smooth camera follow |
| `AudioManager.cs` | 58 | Audio management |

**Total: ~2,788 lines of code**

---

*Last Updated: January 21, 2026*
*Protocol Version: 18.0*
