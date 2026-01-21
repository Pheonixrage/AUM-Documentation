# AUM Protocol Overview - Complete Architecture Reference

**Version:** 2.0 (Complete)
**Date:** January 21, 2026
**Repositories:** `AUM-Unity-Staging-Legacy` (Client) | `AUM-Unity-Server-Legacy` (Server)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Four Protocol Layers](#2-four-protocol-layers)
3. [Complete Connection Flow](#3-complete-connection-flow)
4. [Authentication Architecture](#4-authentication-architecture)
5. [Network Architecture](#5-network-architecture)
6. [Serialization System](#6-serialization-system)
7. [Tick System](#7-tick-system)
8. [Client-Side Prediction](#8-client-side-prediction)
9. [Server Architecture](#9-server-architecture)
10. [File Reference](#10-file-reference)

---

## 1. System Overview

### 1.1 What is AUM?

AUM (Arena of Ultimate Masters) is a multiplayer fighting game with:
- Server-authoritative combat at 60Hz
- Client-side prediction with rollback
- 5 unique fighting styles
- 3 trinity gods (ultimates)
- 5 elemental spell types
- Custom binary protocol over UDP

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                      CLIENT                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────┐ │
│  │  AUMAuthManager │   │ WebSocketConn   │   │ PlayFabManager  │   │ NetworkMgr  │ │
│  │                 │   │                 │   │                 │   │             │ │
│  │ - Firebase Auth │   │ - Login/Logout  │   │ - PlayerData    │   │ - UDP Send  │ │
│  │ - PlayFab Auth  │   │ - Matchmaking   │   │ - Leaderboard   │   │ - UDP Recv  │ │
│  │ - Dev Accounts  │   │ - Friends/Party │   │ - Karma/Lives   │   │ - Tick Sync │ │
│  │ - Guest Login   │   │ - Lobby/Store   │   │ - Store/Items   │   │ - Predict   │ │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘   └──────┬──────┘ │
│           │                     │                     │                    │        │
└───────────┼─────────────────────┼─────────────────────┼────────────────────┼────────┘
            │                     │                     │                    │
            ▼                     ▼                     ▼                    ▼
┌───────────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────────┐
│    Firebase       │   │   Backend     │   │   PlayFab     │   │   Game Server     │
│    REST API       │   │   WebSocket   │   │    Cloud      │   │   UDP:6006+       │
│                   │   │    Server     │   │   Services    │   │                   │
│  - Sign In        │   │               │   │               │   │  - Combat         │
│  - Token Refresh  │   │  - Sessions   │   │  - Data       │   │  - Physics        │
│  - ID Token       │   │  - Matchmake  │   │  - Currency   │   │  - State          │
└───────────────────┘   │  - Social     │   │  - Stats      │   │  - Broadcast      │
                        └───────┬───────┘   └───────────────┘   └─────────┬─────────┘
                                │                                         │
                                │                                         │
                                ▼                                         ▼
                        ┌───────────────────────────────────────────────────────────┐
                        │                      MatchKeeper                           │
                        │                      TCP:6767                              │
                        ├───────────────────────────────────────────────────────────┤
                        │  - Server Registration (MK_AUTH)                          │
                        │  - Match Assignment (MK_STARTGAME)                        │
                        │  - Results Processing (MK_MATCHEND)                       │
                        └───────────────────────────────────────────────────────────┘
```

### 1.3 Protocol Statistics

| Component | Count | Description |
|-----------|-------|-------------|
| **WSS Structs** | 83 | WebSocket packet structures |
| **WSS Packet Types** | 60+ | Unique packet type IDs |
| **UDP Structs** | 26 | In-game packet structures |
| **UDP Packet Types** | 12 | IN: 12, OUT: 7 |
| **MK Structs** | 6 | MatchKeeper structures |
| **MK Packet Types** | 3 | Auth, StartGame, MatchEnd |
| **PlayFab Services** | 12 | Cloud service modules |
| **Enums (Game)** | 25+ | Game logic enums |
| **Enums (Network)** | 10+ | Protocol enums |
| **FSM States** | 31 | Player state machine states |
| **Match States** | 7 | Match lifecycle states |
| **Block Flags** | 11 | Input blocking flags |

---

## 2. Four Protocol Layers

### 2.1 Layer Summary

| Layer | Transport | Port | Direction | Purpose | Frequency |
|-------|-----------|------|-----------|---------|-----------|
| **Auth** | HTTPS | 443 | C→Firebase→PlayFab | Login/Token | On-demand |
| **WSS** | WebSocket | Backend | C↔Backend | Social, Matchmaking | On-demand |
| **MK** | TCP | 6767 | S↔Orchestrator | Server coordination | On-demand |
| **UDP** | LiteNetLib | 6006+ | C↔S | Real-time combat | 60Hz |

### 2.2 Layer Details

#### 2.2.1 Authentication Layer (HTTPS)

**Purpose:** Authenticate users via Firebase or PlayFab

**Components:**
- `AUMAuthManager` - Main orchestrator
- `FirebaseRESTAuth` - Firebase REST API wrapper
- `PlayFabOpenIdAuth` - PlayFab OpenID Connect
- `DevAccountManager` - Editor test accounts

**Flow:**
```
1. User launches app
2. AUMAuthManager.AutoLogin() checks saved credentials
3. If Firebase mode: FirebaseRESTAuth.SignInWithEmail()
   └─> Returns ID token
4. PlayFabOpenIdAuth.LoginWithOpenIdConnect(idToken)
   └─> Returns PlayFab session ticket
5. OnLoginSuccess event fires
6. PlayFabDataBridge.InitializeAfterLogin()
```

#### 2.2.2 WebSocket Layer (WSS)

**Purpose:** Handle all non-realtime backend communication

**File:** `Assets/Scripts/Network/WSS/SocketPacket.cs` (83 structs)

**Categories:**
| Category | Packet Range | Count | Examples |
|----------|--------------|-------|----------|
| Login/Auth | 0x1400-0x1506 | 17 | LOGIN_REQUEST, AVATARLIST_REPLY |
| Matchmaking | 0x2000-0x2018 | 19 | MATCHMAKING_REQUEST, SERVER_DATA |
| Leaderboard | 0x2050-0x2060 | 3 | LEADERBOARD_REQUEST/REPLY |
| Friends | 0x2071-0x2111 | 15 | FRIENDS_DATA_RESPONSE, FRIEND_REQUEST |
| Party | 0x2114-0x2125 | 12 | PARTY_INVITE_REQUEST, PARTY_DATA_PACKET |
| Lobby | 0x2128-0x2147 | 16 | LOBBY_CREATE_REQUEST, LOBBY_DATA_PACKET |
| Store | 0x2080-0x2106 | 8 | STORE_INFO, PURCHASE_COMPLETE |
| Chat | 0x2150-0x2152 | 3 | CHAT_MESSAGE, FEEDBACK_FORM |

**Serialization:** `StructLayout.Sequential, Pack = 1` with Marshal

#### 2.2.3 MatchKeeper Layer (TCP)

**Purpose:** Coordinate game servers with backend

**File:** `Assets/Scripts/Managers/MKManager.cs` (Server)

**Port:** 6767 (localhost only)

**Packets:**
| Type | ID | Direction | Purpose |
|------|-----|-----------|---------|
| MK_AUTH | 0x1000 | S→MK | Server registration |
| MK_STARTGAME | 0x1001 | MK→S | Match assignment |
| MK_MATCHEND | 0x1002 | S→MK | Match results |

**Flow:**
```
1. Server starts
2. MKManager.Initialize() connects to 127.0.0.1:6767
3. OnMKConnectionAccepted() sends MKAuth
4. MK registers server as available
5. When match ready: MK sends MK_STARTGAME with player data
6. Server initializes Socket on assigned port
7. Match plays
8. Server sends MK_MATCHEND with results
9. MK processes karma, stats, rewards
```

#### 2.2.4 UDP Layer (LiteNetLib)

**Purpose:** Real-time combat communication

**Files:**
- Client: `Assets/Scripts/Managers/NetworkManager.cs`
- Server: `Assets/Scripts/Network/Socket.cs`, `UDPSocket.cs`

**Port:** 6006 (default), dynamic in production

**Tick Rate:** 60Hz (16.67ms)

**Packet Types (Client → Server):**
| Type | ID | Size | Purpose |
|------|-----|------|---------|
| NETWORKEVENT | 0x1400 | 3 | Disconnect |
| CREATECHARACTER | 0x1401 | 18 | Authenticate |
| PLAYERINPUT | 0x1403 | 34 | Tick input (60Hz) |
| RESPAWNCHARACTER | 0x1405 | 6 | Request respawn |
| LOGDATA | 0x1406 | var | Debug log |
| PLAYERKARMA | 0x1409 | 11 | Karma decision |
| TUTORIALPROGRESS | 0x140B | 9 | Tutorial state |

**Packet Types (Server → Client):**
| Type | ID | Size | Purpose |
|------|-----|------|---------|
| NETWORKEVENT | 0x1400 | 3 | Disconnect |
| CREATECHARACTER | 0x1401 | 18 | Auth reply |
| REMOVECHARACTER | 0x1402 | 6 | Player left |
| WORLDSNAPSHOT | 0x1403 | var | World state (60Hz) |
| SIMULATIONRESULT | 0x1404 | 21 | Prediction verify |
| RESPAWNCHARACTER | 0x1405 | 6 | Respawn confirmed |
| LOGDATA | 0x1406 | 24 | Combat log |
| ENDGAMEDATA | 0x1407 | ~60 | Match over |
| MATCHSTATEINFO | 0x1408 | 4 | State change |
| PLAYERKARMA | 0x1409 | 11 | Karma update |
| FORFEITMATCH | 0x140A | 3 | Forfeit |
| TUTORIALPROGRESS | 0x140B | 9 | Tutorial sync |

---

## 3. Complete Connection Flow

### 3.1 Full Lifecycle Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE CONNECTION LIFECYCLE                           │
└──────────────────────────────────────────────────────────────────────────────────┘

PHASE 1: AUTHENTICATION
═══════════════════════
Client                          Firebase                         PlayFab
  │                                │                                │
  ├──[AutoLogin()]─────────────────┤                                │
  │                                │                                │
  ├──[SignInWithEmail]────────────►│                                │
  │                                │                                │
  │◄─────────[idToken, refreshToken]                                │
  │                                                                 │
  ├──[LoginWithOpenIdConnect(idToken)]─────────────────────────────►│
  │                                                                 │
  │◄──────────────────────────[SessionTicket, PlayFabId, DisplayName]
  │                                                                 │
  ├──[OnLoginSuccess]──────────────────────────────────────────────►│
  │                                                                 │
  ├──[PlayFabDataBridge.InitializeAfterLogin()]────────────────────►│
  │                                                                 │

PHASE 2: DATA LOADING
═════════════════════
Client                          PlayFab                         WebSocket
  │                                │                                │
  ├──[LoadPlayerData()]───────────►│                                │
  │                                │                                │
  │◄───────────[Stats, Inventory, Settings, Progress]               │
  │                                                                 │
  ├──[WebSocketConnector.Connect()]────────────────────────────────►│
  │                                                                 │
  ├──[LOGIN_REQUEST + DeviceInfo + VersionInfo]────────────────────►│
  │                                                                 │
  │◄──────────────────────────────────────────[LOGIN_REPLY + sessionUUID]
  │                                                                 │
  ├──[AVATARLIST_REQUEST]──────────────────────────────────────────►│
  │                                                                 │
  │◄──────────────────────────────────────────[AVATARLIST_REPLY + avatars]
  │                                                                 │
  ├──[PLAYER_REWARDS_REQUEST]──────────────────────────────────────►│
  │                                                                 │
  │◄──────────────────────────────[PLAYER_REWARDS_REPLY + currencies]
  │                                                                 │
  ├──[FRIENDS_DATA_REQUEST]────────────────────────────────────────►│
  │                                                                 │
  │◄──────────────────────────────[FRIENDS_DATA_RESPONSE + friends]  │

PHASE 3: MATCHMAKING
════════════════════
Client                          WebSocket                      MatchKeeper
  │                                │                                │
  ├──[MATCHMAKING_REQUEST(type, state=1)]──────────────────────────►│
  │                                │                                │
  │◄──────────────────────────[MATCHMAKING_RESPONSE(elapsed, state=0)]
  │                                │                                │
  │    ... (polling continues) ... │                                │
  │                                │                                │
  │◄──────────────────────────[MATCHMAKING_RESPONSE(elapsed, state=1)]
  │                                │                                │
  │◄──────────────────────────[MATCHMAKING_DATA + Match_Avatar[]]    │
  │                                │                                │
  │◄──────────────────────────[SERVER_DATA(ipAddr, ipPort)]          │
  │                                ├───────[Assigns to Server]─────►│
  │                                │                                │

PHASE 4: GAME SERVER CONNECTION
═══════════════════════════════
Client                         Game Server                     MatchKeeper
  │                                │                                │
  │                                │◄──────────[MK_STARTGAME]───────│
  │                                │   (MatchUUID, avatarInfo[])    │
  │                                │                                │
  │                                ├──[Socket.Initialize(port)]     │
  │                                │                                │
  ├──[UDP Connect(ip, port)]──────►│                                │
  │                                │                                │
  │◄────────────────────[ConnectionAccepted]                        │
  │                                │                                │
  ├──[CREATECHARACTER(sessionUUID)]►│                               │
  │                                │                                │
  │                                ├──[Validate sessionUUID]        │
  │                                │   against avatarList           │
  │                                │                                │
  │◄────────[CREATECHARACTER_REPLY(uniqueID, pos, rot)]             │
  │                                │                                │
  │◄────────[MATCHSTATEINFO(PREMATCH, countdown)]                   │
  │                                │                                │

PHASE 5: MATCH LIFECYCLE
════════════════════════
  │                                │                                │
  │◄────────[MATCHSTATEINFO(TELEPORT, 2)]                           │
  │                                │                                │
  │◄────────[WORLDSNAPSHOT]────────┤   (spawning)                   │
  │                                │                                │
  │◄────────[MATCHSTATEINFO(MATCH, 0)]                              │
  │                                │                                │
  ├══════════════════════════════════════════════════════════════════╗
  ║                        60Hz COMBAT LOOP                          ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Client                    Server                                ║
  ║    │                          │                                  ║
  ║    ├──[PLAYERINPUT(tick)]────►│  Process input                   ║
  ║    │                          │  Update physics                  ║
  ║    │                          │  Check collisions                ║
  ║    │                          │  Apply damage                    ║
  ║    │◄──[WORLDSNAPSHOT]────────│  Broadcast state                 ║
  ║    │◄──[SIMULATIONRESULT]─────│  (if position diverged)         ║
  ║    │◄──[LOGDATA]──────────────│  (damage events)                ║
  ║    │                          │                                  ║
  ║    │   ... 60 times/second ...│                                  ║
  ╚══════════════════════════════════════════════════════════════════╝
  │                                │                                │
  │◄────────[MATCHSTATEINFO(ENDMATCH, 3)]                           │
  │                                │                                │
  │◄────────[ENDGAMEDATA(winner, stats)]                            │
  │                                │                                │
  │◄────────[MATCHSTATEINFO(POSTMATCH, 30)]                         │
  │                                │                                │
  ├──[PLAYERKARMA(receiver, karma)]►│                               │
  │                                │                                │
  │◄────────[MATCHSTATEINFO(END, 0)]                                │
  │                                │                                │
  │                                ├──[MK_MATCHEND]────────────────►│
  │                                │   (results, karma, stats)      │
  │                                │                                │

PHASE 6: CLEANUP
════════════════
Client                         Game Server                     WebSocket
  │                                │                                │
  │◄────────[NETWORKEVENT(DC)]─────│                                │
  │                                │                                │
  ├──[UDP Disconnect]──────────────►                                │
  │                                                                 │
  ├──[MATCH_REWARDS request]───────────────────────────────────────►│
  │                                                                 │
  │◄──────────────────────────────────────────────[MATCH_REWARDS]    │
  │   (timeShards, bronze, lives, karma changes)                    │
  │                                                                 │
```

### 3.2 Test Mode Flow (Direct Connection)

For development, TestModeClient bypasses MatchKeeper:

```
Client                                          Server (Hetzner)
  │                                                   │
  │  TestModeClient.Initialize()                      │ TestModeManager.Setup()
  │                                                   │
  │  sessionUUID = MD5("test-player-1-session")       │ sessionUUID = MD5("test-player-1-session")
  │  = 3d46e7bc-914e-fca2-c3ae-1ae23d72aa34          │ = 3d46e7bc-914e-fca2-c3ae-1ae23d72aa34
  │                                                   │
  ├──[UDP Connect 65.109.133.129:6006]───────────────►│
  │                                                   │
  ├──[CREATECHARACTER(sessionUUID)]──────────────────►│
  │                                                   │ Validate: UUIDs match!
  │◄──────────────────────[CREATECHARACTER_REPLY]─────│
  │                                                   │
```

---

## 4. Authentication Architecture

### 4.1 Auth Configuration

**File:** `Assets/Scripts/Auth/AUMAuthConfig.cs`

```csharp
public enum AuthEnvironment
{
    Development,    // Dev PlayFab title
    Staging,        // Staging PlayFab title
    Production      // Production PlayFab title
}

public enum AuthMode
{
    PlayFabDirect,      // PlayFab only (simplest)
    FirebaseToPlayFab,  // Firebase → PlayFab OpenID
    DevAccount          // Editor dev accounts
}

public class AUMAuthConfig
{
    public AuthEnvironment environment;
    public AuthMode mode;
    public string firebaseApiKey;
    public string firebaseProjectId;
    public string playFabTitleId;
    public string openIdConnectionId;
}
```

### 4.2 AUMAuthManager API

**File:** `Assets/Scripts/Auth/AUMAuthManager.cs`

**Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `Instance` | AUMAuthManager | Singleton |
| `IsLoggedIn` | bool | Login complete |
| `PlayFabId` | string | Current PlayFab ID |
| `DisplayName` | string | Player display name |
| `SessionTicket` | string | PlayFab session ticket |
| `CurrentEnvironment` | AuthEnvironment | Active environment |

**Methods:**
| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `AutoLogin()` | - | Task<bool> | Try saved credentials |
| `LoginWithEmail()` | email, password | Task<bool> | Email/password |
| `LoginAsGuest()` | - | Task<bool> | Anonymous guest |
| `LoginWithGoogle()` | - | Task<bool> | Google OAuth |
| `LoginWithApple()` | - | Task<bool> | Apple Sign-In |
| `Logout()` | - | void | Clear session |
| `RefreshToken()` | - | Task<bool> | Refresh expired token |

**Events:**
| Event | Parameters | When |
|-------|------------|------|
| `OnLoginSuccess` | playFabId, displayName | Login completed |
| `OnLoginFailed` | errorMessage | Login failed |
| `OnLogout` | - | Logged out |
| `OnTokenRefreshed` | - | Token refreshed |

### 4.3 Session UUID Generation

For test mode, session UUIDs are deterministically generated:

```csharp
// Client: TestModeClient.cs
public static Guid GenerateSessionUUID(string identifier)
{
    using (MD5 md5 = MD5.Create())
    {
        byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(identifier));
        return new Guid(hash);
    }
}

// Server: TestModeManager.cs (identical algorithm)
// Input: "test-player-1-session"
// Output: 3d46e7bc-914e-fca2-c3ae-1ae23d72aa34
```

---

## 5. Network Architecture

### 5.1 Client Network Stack

```
┌───────────────────────────────────────────────────────────────┐
│                        Application Layer                       │
├───────────────────────────────────────────────────────────────┤
│  GameManager ◄──► StateManager ◄──► PlayerInput               │
│       │              │                  │                     │
│       ▼              ▼                  ▼                     │
├───────────────────────────────────────────────────────────────┤
│                     Network Manager Layer                      │
├───────────────────────────────────────────────────────────────┤
│  NetworkManager                    SimulationManager          │
│  - SendTickInput()                 - Predict()                │
│  - ProcessSnapshot()               - Rollback()               │
│  - ProcessSimResult()              - Reconcile()              │
│       │                                 │                     │
│       ▼                                 ▼                     │
├───────────────────────────────────────────────────────────────┤
│                      Serialization Layer                       │
├───────────────────────────────────────────────────────────────┤
│  Serializer                        JitterCompensator          │
│  - Serialize<T>()                  - GetFactor()              │
│  - Deserialize<T>()                - min=2, max=5             │
│       │                                                       │
│       ▼                                                       │
├───────────────────────────────────────────────────────────────┤
│                       Transport Layer                          │
├───────────────────────────────────────────────────────────────┤
│  LiteNetLib (Native DLL)                                      │
│  - UDP reliable/unreliable                                    │
│  - Connection management                                      │
│  - Fragmentation                                              │
└───────────────────────────────────────────────────────────────┘
```

### 5.2 Server Network Stack

```
┌───────────────────────────────────────────────────────────────┐
│                        Application Layer                       │
├───────────────────────────────────────────────────────────────┤
│  GameManager ◄──► PlayerManager ◄──► EntityManager            │
│       │               │                   │                   │
│       ▼               ▼                   ▼                   │
├───────────────────────────────────────────────────────────────┤
│                      Processing Layer                          │
├───────────────────────────────────────────────────────────────┤
│  ProcessPlayerInputTick()                                     │
│  - Decode joystick                                            │
│  - Apply movement                                             │
│  - Process abilities                                          │
│  - Check collisions                                           │
│  - Apply damage                                               │
│       │                                                       │
│       ▼                                                       │
├───────────────────────────────────────────────────────────────┤
│                     Broadcast Layer                            │
├───────────────────────────────────────────────────────────────┤
│  BroadcastWorldSnapshot()          BroadcastSimulationResult()│
│  - Build See_MoveCharacter[]       - Per-player correction    │
│  - Append EntityData[]             - Position/State           │
│  - Send to all clients             - Send to affected client  │
│       │                                                       │
│       ▼                                                       │
├───────────────────────────────────────────────────────────────┤
│                      Transport Layer                           │
├───────────────────────────────────────────────────────────────┤
│  Socket ◄──► UDPSocket (LiteNetLib Native DLL)               │
│  - ConnectionAccepted event                                   │
│  - MessageReceived event                                      │
│  - ConnectionClosed event                                     │
└───────────────────────────────────────────────────────────────┘
```

### 5.3 Connection Events

**Socket Events (Server):**
```csharp
public class Socket
{
    public static event Action ConnectionAccepted;
    public static event Action ConnectionClosed;
    public static event MessageHandler MessageReceived;

    public delegate void MessageHandler(ref byte[] message, NetPeer peer);
}
```

**NetworkManager Events (Client):**
```csharp
public class NetworkManager
{
    public event Action OnConnected;
    public event Action OnDisconnected;
    public event Action<int> OnPeerDisconnected;  // reason code
}
```

---

## 6. Serialization System

### 6.1 Binary Serialization

**File:** `Assets/Scripts/Network/Serializer.cs`

All packets use `StructLayout.Sequential, Pack = 1` for deterministic binary layout:

```csharp
public static class Serializer
{
    public static byte[] Serialize<T>(T obj)
    {
        int size = Marshal.SizeOf(typeof(T));
        byte[] bytes = new byte[size];
        IntPtr ptr = Marshal.AllocHGlobal(size);
        try
        {
            Marshal.StructureToPtr(obj, ptr, false);
            Marshal.Copy(ptr, bytes, 0, size);
        }
        finally
        {
            Marshal.FreeHGlobal(ptr);
        }
        return bytes;
    }

    public static T Deserialize<T>(byte[] bytes)
    {
        int size = Marshal.SizeOf(typeof(T));
        IntPtr ptr = Marshal.AllocHGlobal(size);
        try
        {
            Marshal.Copy(bytes, 0, ptr, size);
            return (T)Marshal.PtrToStructure(ptr, typeof(T));
        }
        finally
        {
            Marshal.FreeHGlobal(ptr);
        }
    }
}
```

### 6.2 Struct Layout Rules

**Required Attributes:**
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ExamplePacket
{
    public UInt16 packetType;           // 2 bytes - always first
    public UInt32 someInt;              // 4 bytes
    public float someFloat;             // 4 bytes
    public byte someByte;               // 1 byte

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] fixedArray;           // 16 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string fixedString;          // 13 bytes (null-terminated)
}
// Total: 2 + 4 + 4 + 1 + 16 + 13 = 40 bytes
```

### 6.3 Joystick Axis Encoding

Movement input packed into single byte:

```csharp
// Encoding (Client)
public static byte EncodeJoystick(int x, int y)
{
    // x: -1 = 0xF, 0 = 0x0, 1 = 0x1
    // y: -1 = 0xF, 0 = 0x0, 1 = 0x1
    byte xBits = (byte)(x == -1 ? 0xF : x);
    byte yBits = (byte)(y == -1 ? 0xF : y);
    return (byte)((xBits << 4) | yBits);
}

// Decoding (Server)
public static (int x, int y) DecodeJoystick(byte axis)
{
    int x = (axis >> 4) & 0xF;
    int y = axis & 0xF;
    if (x == 0xF) x = -1;
    if (y == 0xF) y = -1;
    return (x, y);
}

// Examples:
// 0x00 = (0, 0)   - No input
// 0x10 = (1, 0)   - Right
// 0xF0 = (-1, 0)  - Left
// 0x01 = (0, 1)   - Forward
// 0x0F = (0, -1)  - Backward
// 0x11 = (1, 1)   - Forward-Right
// 0xFF = (-1, -1) - Backward-Left
```

### 6.4 Elemental Spell Encoding

```csharp
// SpellData.cs
public UInt16 GetSpellIndex()
{
    // 3 bits for element (0-4), 5 bits for spell type (0-31)
    return (UInt16)((int)Elemental << 5 | spellType);
}

// Decoding
public Elementals GetElemental(byte encoded)
{
    return (Elementals)((encoded >> 5) & 0x7);
}

public int GetSpellType(byte encoded)
{
    return encoded & 0x1F;
}

// Examples:
// FIRE (0) spell 1:   (0 << 5) | 1 = 0x01
// WATER (1) spell 2:  (1 << 5) | 2 = 0x22
// AIR (2) spell 3:    (2 << 5) | 3 = 0x43
// ETHER (3) spell 4:  (3 << 5) | 4 = 0x64
// EARTH (4) spell 5:  (4 << 5) | 5 = 0x85
```

---

## 7. Tick System

### 7.1 Server Tick Loops

**File:** `Assets/Scripts/Managers/GameManager.cs` (Server)

```csharp
// Tick intervals
private float fastLoopTick = 0.001f;       // 1ms - input processing
private float fixedLoopTick = 0.06f;       // 60ms - world snapshots
private float projectileLoopTick = 0.02f;  // 20ms - entity updates
private float regenLoopTick = 0.5f;        // 500ms - stamina regen

// Tick counters
private UInt32 serverTick;                 // Increments every fixedLoopTick
private UInt32 projectileTick;             // Increments every projectileLoopTick
```

**Loop Responsibilities:**

| Loop | Interval | Hz | Purpose |
|------|----------|-----|---------|
| FastLoop | 1ms | 1000 | Poll network, process input queue |
| FixedLoop | 60ms | 16.67 | Broadcast world snapshot |
| ProjectileLoop | 20ms | 50 | Update projectiles/entities |
| RegenLoop | 500ms | 2 | Regenerate stamina/willpower |

### 7.2 Tick Synchronization

```csharp
// Client sends with every input
public struct TickInput
{
    public UInt32 currentTick;  // Client's tick number
    public UInt32 serverTick;   // Last received server tick
    // ... other fields
}

// Server responds with verification
public struct SimulationResult
{
    public UInt32 currentTick;  // Tick being verified
    public float positionX;     // Authoritative position
    public float positionZ;
    public UInt32 state;        // Authoritative state
    // ...
}
```

### 7.3 Input Processing Order

```
1. FastLoop (1ms)
   ├── Poll LiteNetLib for messages
   ├── Queue incoming TickInput packets
   └── Process input queue:
       ├── Decode joystick
       ├── Apply movement based on state
       ├── Process ability inputs
       └── Update player state

2. FixedLoop (60ms)
   ├── Build See_MoveCharacter for each player
   ├── Build EntityData for active entities
   ├── Pack into world snapshot
   └── Broadcast to all clients

3. ProjectileLoop (20ms)
   ├── Update projectile positions
   ├── Check projectile collisions
   ├── Apply damage on hit
   └── Remove expired entities

4. RegenLoop (500ms)
   ├── Regenerate player stamina
   ├── Regenerate willpower
   └── Update buff/debuff durations
```

---

## 8. Client-Side Prediction

### 8.1 Prediction System

**File:** `Assets/Scripts/Managers/SimulationManager.cs`

```csharp
public enum StateVerifyResult
{
    NOFAIL,           // Prediction was correct
    NORMAL,           // Minor correction needed
    UNHANDLED,        // Unknown state mismatch
    RESIMUL_NORECURSE // Needs resimulation
}

public class SimulationManager
{
    private Queue<SimulationData> pendingInputs;
    private Dictionary<UInt32, SimulationData> tickHistory;

    public void RecordInput(TickInput input);
    public void ProcessSimulationResult(SimulationResult result);
    public void Rollback(UInt32 toTick);
    public void Resimulate();
}
```

### 8.2 Prediction Flow

```
CLIENT PREDICTION FLOW
══════════════════════

1. Input Recorded
   ├── Store input in tickHistory[currentTick]
   ├── Predict local movement
   ├── Update local state immediately
   └── Send TickInput to server

2. Server Processes
   ├── Apply input to authoritative state
   ├── Check if prediction matches
   └── Send SimulationResult if diverged

3. Client Receives SimulationResult
   ├── Compare predicted vs authoritative
   ├── If match: discard pending inputs up to tick
   ├── If mismatch:
   │   ├── Rollback to authoritative state
   │   ├── Reapply pending inputs
   │   └── Reconcile visual position
   └── Log mismatch for debugging
```

### 8.3 Jitter Compensation

**File:** `Assets/Scripts/Network/JitterCompensator.cs`

```csharp
public static class JitterCompensator
{
    public const int MIN_BUFFER = 2;
    public const int MAX_BUFFER = 5;

    public static float GetFactor(int queueSize)
    {
        if (queueSize >= MAX_BUFFER)
            return 0.95f;  // Speed up playback
        else if (queueSize <= MIN_BUFFER)
            return 1.05f;  // Slow down playback
        else
            return 1.00f;  // Normal speed
    }
}

// Usage in snapshot processing:
float jitterFactor = JitterCompensator.GetFactor(snapshotQueue.Count);
Time.timeScale = jitterFactor;
```

---

## 9. Server Architecture

### 9.1 Server Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         GAME SERVER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ GameManager │    │ MatchState  │    │ PlayerManager       │ │
│  │             │    │             │    │                     │ │
│  │ - Tick loops│◄──►│ - State FSM │◄──►│ - playerList        │ │
│  │ - Broadcast │    │ - Countdown │    │ - avatarList        │ │
│  │ - EndGame   │    │ - Timers    │    │ - ProcessInput      │ │
│  └──────┬──────┘    └─────────────┘    └──────────┬──────────┘ │
│         │                                          │            │
│         ▼                                          ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │EntityManager│    │   Player    │    │ MKManager           │ │
│  │             │    │   (each)    │    │                     │ │
│  │ - Projectile│◄──►│ - FSM State │    │ - MK Connection     │ │
│  │ - Spell zone│    │ - Position  │    │ - Auth              │ │
│  │ - Astra     │    │ - Combat    │    │ - MatchEnd          │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                         NETWORK LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                       Socket                                 ││
│  │  - ConnectionAccepted  - MessageReceived  - ConnectionClosed ││
│  │                            │                                 ││
│  │                            ▼                                 ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │                     UDPSocket                          │  ││
│  │  │              (LiteNetLib Native DLL)                   │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Match State Machine

```
┌────────┐
│  NONE  │ ←── Server waiting
└────┬───┘
     │ SignalMatchReady() (MK_STARTGAME received)
     ▼
┌────────────┐
│  PREMATCH  │ ←── 15 second countdown
│  (15s)     │     Waiting for human players
└────┬───────┘
     │ countdownTimer == 0 && allPlayersReady
     ▼
┌────────────┐
│  TELEPORT  │ ←── 2 seconds
│  (2s)      │     Spawn players at positions
└────┬───────┘
     │ countdownTimer == 0
     ▼
┌────────────┐
│   MATCH    │ ←── Combat active
│  (until    │     60Hz tick loop
│   winner)  │     All abilities enabled
└────┬───────┘
     │ SignalMatchEnd() (win condition)
     ▼
┌────────────┐
│  ENDMATCH  │ ←── 3 seconds
│  (3s)      │     Victory animation
└────┬───────┘
     │ countdownTimer == 0
     ▼
┌────────────┐
│  POSTMATCH │ ←── 30 seconds
│  (30s)     │     Karma selection
└────┬───────┘
     │ countdownTimer == 0
     ▼
┌────────────┐
│    END     │ ←── Cleanup
│            │     Send MK_MATCHEND
└────────────┘     Disconnect clients
```

---

## 10. File Reference

### 10.1 Client Files

| File | Purpose |
|------|---------|
| `Assets/Scripts/Auth/AUMAuthManager.cs` | Main auth orchestrator |
| `Assets/Scripts/Auth/AUMAuthConfig.cs` | Auth configuration |
| `Assets/Scripts/Auth/FirebaseRESTAuth.cs` | Firebase REST API |
| `Assets/Scripts/Auth/PlayFabOpenIdAuth.cs` | PlayFab OpenID |
| `Assets/Scripts/Auth/DevAccountManager.cs` | Dev test accounts |
| `Assets/Scripts/Network/WSS/SocketPacket.cs` | All WSS structs |
| `Assets/Scripts/Network/WSS/WebSocketConnector.cs` | WSS connection |
| `Assets/Scripts/Network/Packet.cs` | UDP packet structs |
| `Assets/Scripts/Network/Serializer.cs` | Binary serialization |
| `Assets/Scripts/Network/Simulation.cs` | Simulation data |
| `Assets/Scripts/Network/JitterCompensator.cs` | Jitter handling |
| `Assets/Scripts/Managers/NetworkManager.cs` | UDP networking |
| `Assets/Scripts/Managers/SimulationManager.cs` | Client prediction |
| `Assets/Scripts/Managers/ServerManager.cs` | Snapshot processing |
| `Assets/Scripts/Managers/TestModeClient.cs` | Direct connection |
| `Assets/Scripts/Managers/InterfaceManager.cs` | Global data |
| `Assets/Scripts/StateMachine/StateManager.cs` | Player FSM |
| `Assets/Scripts/Player/ControllerBase.cs` | State definitions |

### 10.2 Server Files

| File | Purpose |
|------|---------|
| `Assets/Scripts/Network/Packet.cs` | UDP packet structs |
| `Assets/Scripts/Network/Socket.cs` | UDP server wrapper |
| `Assets/Scripts/Network/UDPSocket.cs` | LiteNetLib integration |
| `Assets/Scripts/Network/Serializer.cs` | Binary serialization |
| `Assets/Scripts/Network/JitterCompensator.cs` | Jitter handling |
| `Assets/Scripts/Managers/MKManager.cs` | MatchKeeper protocol |
| `Assets/Scripts/Managers/GameManager.cs` | Main game loop |
| `Assets/Scripts/Managers/TestModeManager.cs` | Test mode setup |
| `Assets/Scripts/Player/PlayerManager.cs` | Player management |
| `Assets/Scripts/Player/Player.cs` | Player entity |
| `Assets/Scripts/MatchState.cs` | Match state machine |
| `Assets/Scripts/StateMachine/StateManager.cs` | Player FSM |
| `Assets/Scripts/Enum.cs` | Game enums |
| `Assets/Scripts/Spells/Effects/Effects.cs` | Effect types |

### 10.3 Related Documentation

| Document | Contents |
|----------|----------|
| `PROTOCOL-2-WSS-PACKETS.md` | All 83 WebSocket structs |
| `PROTOCOL-3-UDP-PACKETS.md` | All in-game UDP packets |
| `PROTOCOL-4-MATCHKEEPER.md` | Complete MK protocol |
| `PROTOCOL-5-PLAYFAB.md` | All 12 PlayFab services |
| `PROTOCOL-6-STATE-MACHINES.md` | FSM details |
| `PROTOCOL-7-GAME-DATA.md` | Attributes, bonuses |
| `PROTOCOL-8-CHARACTERS.md` | All 5 fighters |
| `PROTOCOL-9-SPELLS.md` | All 5 elements |
| `PROTOCOL-10-ENUMS.md` | Every enum value |
| `PROTOCOL-INDEX.md` | Master index |

---

**Document Info:**
- Lines: ~900
- Created: January 21, 2026
- Part: 1 of 11

---

*End of Protocol Overview Document*
