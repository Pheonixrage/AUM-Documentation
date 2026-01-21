# AUM Legacy Protocol Documentation

**Complete Network Protocol Reference for AUM (Arena of Ultimate Masters)**

**Version:** 1.0
**Date:** January 21, 2026
**Repositories:** `AUM-Unity-Staging-Legacy` (Client) | `AUM-Unity-Server-Legacy` (Server)
**Branch:** `legacy-working-oct29`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Authentication Layer](#3-authentication-layer)
4. [WebSocket Backend Protocol (WSS)](#4-websocket-backend-protocol-wss)
5. [MatchKeeper Protocol (MK)](#5-matchkeeper-protocol-mk)
6. [PlayFab Cloud Protocol](#6-playfab-cloud-protocol)
7. [In-Game UDP Protocol](#7-in-game-udp-protocol)
8. [State Machines](#8-state-machines)
9. [Game Data Systems](#9-game-data-systems)
10. [Complete Enums Reference](#10-complete-enums-reference)
11. [Migration Guide](#11-migration-guide)

---

## 1. Overview

### 1.1 What This Document Covers

This document provides a complete specification of the AUM Legacy networking protocol, including:

- **142+ packet structures** with byte-level layouts
- **70+ enums** with all values
- **4 protocol layers** (Auth, WSS, MK, UDP)
- **12 PlayFab services** with data structures
- **Complete state machines** (Match states + Player FSM)
- **Game balance data** (attributes, bonuses, spell data)

### 1.2 Protocol Statistics

| Metric | Count |
|--------|-------|
| Total Packet Structs | 142+ |
| Total Enums | 70+ |
| Protocol Layers | 4 |
| WSS Packet Types | 60+ |
| UDP Packet Types | 15 |
| MK Packet Types | 3 |
| PlayFab Services | 12 |
| Fighting Styles | 5 |
| Trinity Gods | 3 |
| Player FSM States | 31 |
| Match States | 7 |

---

## 2. Architecture Summary

### 2.1 Four Protocol Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Auth      │  │    WSS      │  │   PlayFab   │  │    UDP     │ │
│  │  Manager    │  │  Connector  │  │   Services  │  │  Network   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │
└─────────┼────────────────┼────────────────┼───────────────┼─────────┘
          │                │                │               │
          ▼                ▼                ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│    Firebase     │ │   Backend   │ │   PlayFab   │ │  Game Server    │
│    REST API     │ │  WebSocket  │ │    Cloud    │ │  (UDP:6006+)    │
│                 │ │   Server    │ │   Services  │ │                 │
└─────────────────┘ └─────────────┘ └─────────────┘ └────────┬────────┘
                                                             │
                                                    ┌────────┴────────┐
                                                    │  MatchKeeper    │
                                                    │   (TCP:6767)    │
                                                    └─────────────────┘
```

### 2.2 Layer Summary

| Layer | Transport | Port | Purpose | Tick Rate |
|-------|-----------|------|---------|-----------|
| **Auth** | HTTPS | 443 | Firebase/PlayFab authentication | On-demand |
| **WSS** | WebSocket | Backend | Login, matchmaking, social, store | On-demand |
| **MK** | TCP | 6767 | Server↔Orchestrator coordination | On-demand |
| **UDP** | UDP/LiteNetLib | 6006+ | Real-time combat | 60Hz |

### 2.3 Connection Flow Overview

```
1. CLIENT STARTUP
   └─> AUMAuthManager.AutoLogin()
       ├─> Firebase REST Auth (if configured)
       └─> PlayFab OpenID Auth
           └─> OnLoginSuccess → PlayFabDataBridge.InitializeAfterLogin()

2. MAIN MENU
   └─> WebSocketConnector.Connect()
       └─> WSS: LOGIN_REQUEST → LOGIN_REPLY
           └─> WSS: AVATARLIST_REQUEST → AVATARLIST_REPLY
               └─> Load player data, friends, inventory

3. MATCHMAKING
   └─> WSS: MATCHMAKING_REQUEST
       └─> WSS: MATCHMAKING_RESPONSE (polling)
           └─> WSS: SERVER_DATA (IP:Port)
               └─> Connect to Game Server (UDP)

4. IN-GAME
   └─> UDP: AUTHENTICATE → AUTHENTICATE_REPLY
       └─> UDP: TICKINPUT (60Hz client→server)
           └─> UDP: WORLDSNAPSHOT (60Hz server→client)

5. MATCH END
   └─> Server: MK_MATCHEND → MatchKeeper
       └─> Client: ENDGAMEDATA → Process rewards
           └─> PlayFab: Update stats, karma, currency
```

---

## 3. Authentication Layer

### 3.1 Overview

The authentication system supports multiple providers with automatic fallback:

```
┌─────────────────────────────────────────────────────────┐
│                    AUMAuthManager                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Firebase   │  │   PlayFab   │  │  Dev Accounts   │ │
│  │  REST Auth  │  │ OpenID Auth │  │  (Editor Only)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Auth Configuration

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
    PlayFabDirect,      // PlayFab only
    FirebaseToPlayFab,  // Firebase → PlayFab OpenID
    DevAccount          // Editor dev accounts
}
```

### 3.3 AUMAuthManager

**File:** `Assets/Scripts/Auth/AUMAuthManager.cs`

**Key Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `IsLoggedIn` | bool | Login complete |
| `PlayFabId` | string | Current PlayFab ID |
| `DisplayName` | string | Player display name |
| `SessionTicket` | string | PlayFab session ticket |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `AutoLogin()` | Attempt automatic login with saved credentials |
| `LoginWithEmail(email, password)` | Email/password login |
| `LoginAsGuest()` | Anonymous guest login |
| `LoginWithGoogle()` | Google OAuth login |
| `LoginWithApple()` | Apple Sign-In |
| `Logout()` | Clear session and logout |

**Events:**
| Event | Parameters | Description |
|-------|------------|-------------|
| `OnLoginSuccess` | PlayFabId, DisplayName | Login completed |
| `OnLoginFailed` | ErrorMessage | Login failed |
| `OnLogout` | - | Logged out |

### 3.4 Firebase REST Auth

**File:** `Assets/Scripts/Auth/FirebaseRESTAuth.cs`

Used when `AuthMode.FirebaseToPlayFab` is configured.

**Flow:**
```
1. FirebaseRESTAuth.SignInWithEmail(email, password)
   └─> POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword
       └─> Response: { idToken, refreshToken, localId }

2. PlayFabOpenIdAuth.LoginWithOpenIdConnect(idToken)
   └─> PlayFab validates Firebase token
       └─> Returns PlayFab session
```

### 3.5 PlayFab OpenID Auth

**File:** `Assets/Scripts/Auth/PlayFabOpenIdAuth.cs`

**Methods:**
| Method | Description |
|--------|-------------|
| `LoginWithOpenIdConnect(idToken)` | Login with Firebase/Google token |
| `LinkOpenIdConnect(idToken)` | Link OpenID to existing account |
| `RefreshToken()` | Refresh expired token |

### 3.6 Dev Accounts (Editor Only)

**File:** `Assets/Scripts/Auth/DevAccountManager.cs`

Pre-configured test accounts for development:

```csharp
public class DevAccount
{
    public string name;           // Display name
    public string email;          // Login email
    public string password;       // Login password
    public string playFabId;      // Expected PlayFab ID
    public FightingStyles style;  // Default character
    public TrinityGods god;       // Default god
}
```

---

## 4. WebSocket Backend Protocol (WSS)

### 4.1 Overview

The WebSocket protocol handles all non-realtime backend communication:
- Login/Logout
- Avatar management
- Matchmaking
- Friends system
- Party system
- Lobby system
- Store/Inventory
- Rewards

**File:** `Assets/Scripts/Network/WSS/SocketPacket.cs`

### 4.2 Packet Structure

All WSS packets use `StructLayout.Sequential, Pack = 1` for binary serialization.

**Base Format:**
```
┌────────────────┬────────────────┬─────────────────────┐
│  PacketType    │  PacketLength  │     Payload         │
│   (2 bytes)    │   (2 bytes)    │   (variable)        │
└────────────────┴────────────────┴─────────────────────┘
```

### 4.3 Packet Type IDs

```csharp
public enum PacketType
{
    // === LOGIN/AUTH (0x1400-0x150F) ===
    LOGIN_REQUEST               = 0x1400,
    TRY_LOGIN                   = 0x1401,
    LOGIN_REPLY                 = 0x1402,
    AVATARLIST_REQUEST          = 0x1403,
    AVATARLIST_REPLY            = 0x1404,
    CREATE_AVATAR_NEW_REQUEST   = 0x1405,
    CREATE_AVATAR_NEW_REPLY     = 0x1406,
    AVATAR_NAME_VALIDATION_REQUEST = 0x1408,
    AVATAR_NAME_VALIDATION_REPLY   = 0x1409,
    LOGININFO_REQUEST           = 0x140A,
    LOGININFO_REPLY             = 0x140B,
    SOCIALINFO_REPLY            = 0x140C,
    DELETE_AVATAR_REQUEST       = 0x1500,
    DELETE_AVATAR_REPLY         = 0x1501,
    CREATE_AVATAR_NEW_CONFIRM   = 0x1502,
    SET_AVATAR_ACTIVE           = 0x1503,
    CHANGE_ELEMENTAL_GOD        = 0x1504,
    LOGOUT                      = 0x1505,
    SET_AVATAR_RESPONSE         = 0x1506,

    // === MATCHMAKING (0x2000-0x2018) ===
    MATCHMAKING_REQUEST         = 0x2000,
    MATCHMAKING_RESPONSE        = 0x2001,
    MATCHMAKING_DATA            = 0x2002,
    MATCHMAKING_READYSTATE      = 0x2003,
    FCM_TOKEN                   = 0x2004,
    INVENTORY_REPLY             = 0x2005,
    SERVER_DATA                 = 0x2006,
    CUSTOMIZATION_REQUEST       = 0x2007,
    MATCH_REWARDS               = 0x2008,
    PLAYER_REWARDS_REQUEST      = 0x2009,
    PLAYER_REWARDS_REPLY        = 0x2010,
    CONSUME_SHARD               = 0x2011,
    MEDITATION_STATE            = 0x2012,
    MEDITATION_COMPLETE_REQUEST = 0x2013,
    MEDITATION_BEGIN_REQUEST    = 0x2014,
    GUEST_LOGIN                 = 0x2015,
    BOT_LOGIN                   = 0x2016,
    OAUTH_LOGIN                 = 0x2017,
    FORFEIT_MATCH               = 0x2018,

    // === LEADERBOARD/SETTINGS (0x2050-0x2060) ===
    LEADERBOARD_REQUEST         = 0x2050,
    LEADERBOARD_REPLY           = 0x2051,
    USERSETTINGS                = 0x2060,

    // === FRIENDS (0x2071-0x2111) ===
    FRIENDS_DATA_RESPONSE       = 0x2071,
    FRIENDS_SEARCH_REQUEST      = 0x2072,
    FRIENDS_SEARCH_RESPONSE     = 0x2073,
    FRIEND_REQUEST              = 0x2077,
    FRIEND_REQUEST_RESPONSE     = 0x2079,
    FRIENDS_DATA_REQUEST        = 0x2090,
    REMOVE_FRIEND               = 0x2091,
    TOGGLE_FAVOURITE            = 0x2092,
    FRIEND_EVENT                = 0x2093,
    UPDATE_PROFILE              = 0x2098,
    CHECK_FRIEND                = 0x2102,
    FRIEND_APPEND               = 0x2107,
    FRIEND_REMOVED              = 0x2108,
    FRIENDREQUEST_PROCESSED     = 0x2110,
    FRIEND_TOGGLE_FAV           = 0x2111,

    // === PARTY (0x2114-0x2125) ===
    PARTY_INVITE_REQUEST        = 0x2114,
    PARTY_INVITE_RECEIVED       = 0x2115,
    PARTY_INVITE_REPLY          = 0x2116,
    PARTY_INVITE_RESPONSE       = 0x2117,
    PARTY_INVITE_CANCEL         = 0x2118,
    PARTY_DATA_PACKET           = 0x2119,
    PARTY_READY                 = 0x2120,
    PARTY_READY_RESPONSE        = 0x2121,
    PARTY_MAKE_LEADER           = 0x2122,
    PARTY_KICKOUT_PLAYER        = 0x2123,
    LEAVE_PARTY                 = 0x2124,
    PARTY_PLAYER_LEFT           = 0x2125,

    // === LOBBY (0x2128-0x2147) ===
    LOBBY_CREATE_REQUEST        = 0x2128,
    LOBBY_DATA_PACKET           = 0x2129,
    LOBBY_LIST_REQUEST          = 0x2130,
    LOBBY_LIST_RESPONSE         = 0x2131,
    LOBBY_INVITE_REQUEST        = 0x2132,
    LOBBY_INVITE_RECEIVED       = 0x2133,
    LOBBY_JOIN_REQUEST          = 0x2137,
    LOBBY_JOIN_RESPONSE         = 0x2138,
    LOBBY_JOIN_INVITE           = 0x2139,
    LOBBY_READY                 = 0x2140,
    LOBBY_KICKOUT_PLAYER        = 0x2142,
    LOBBY_LEAVE                 = 0x2143,
    LOBBY_PLAYER_SLOT_UPDATE    = 0x2144,
    PARTY_LOBBY_DATA            = 0x2145,
    TOGGLE_LOBBY_BOTS           = 0x2146,
    LOBBY_RESPONSE              = 0x2147,

    // === STORE/REWARDS (0x2080-0x2106) ===
    DAILY_REWARDS               = 0x2081,
    DAILY_REWARDS_CLAIM         = 0x2082,
    STORE_INFO                  = 0x2080,
    MATCH_DATA                  = 0x2101,
    REQUEST_STORE_INFO          = 0x2103,
    REQUEST_PURCHASE            = 0x2104,
    PURCHASE_COMPLETE           = 0x2106,
    CURRENCY_CONVERSION         = 0x2100,

    // === CHAT/FEEDBACK (0x2150-0x2152) ===
    CHAT_MESSAGE                = 0x2150,
    FEEDBACK_FORM_REQUEST       = 0x2151,
    FEEDBACK_FORM_SUBMIT        = 0x2152,
}
```

### 4.4 Login/Avatar Packets

#### 4.4.1 DeviceInfo
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct DeviceInfo
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)]
    public string deviceUniqueId;      // Device unique identifier

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
    public string deviceModel;         // Device model name

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string operatingSystem;     // OS name

    public byte platform;              // 0=Unknown, 1=Android, 2=iOS, 3=PC
}
```

#### 4.4.2 LoginData
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LoginData
{
    public UInt16 packetType;          // LOGIN_REQUEST
    public DeviceInfo deviceInfo;      // Device information

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionUUID;         // Session UUID (16 bytes)
}
```

#### 4.4.3 SessionID (Response)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SessionID
{
    public UInt16 packetType;          // LOGIN_REPLY

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionUUID;         // Assigned session UUID

    public byte loginStatus;           // LoginStatus enum
}
```

#### 4.4.4 AvatarList
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct AvatarList
{
    public UInt16 packetType;          // AVATARLIST_REPLY
    public byte avatarCount;           // Number of avatars (0-5)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public Avatar_Info[] avatars;      // Up to 5 avatars
}
```

#### 4.4.5 Avatar_Info
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Avatar_Info
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] avatarUUID;          // Avatar unique ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;            // Display name (max 12 chars)

    public byte fightingStyle;         // FightingStyles enum
    public byte fighterClass;          // FighterClass enum (Male/Female)
    public byte godSelected;           // TrinityGods enum

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementals;          // 4 equipped elementals

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public ItemInfo[] wearItems;       // 6 equipped items (slots)

    public byte weaponVariant;         // Weapon skin variant
    public byte isActive;              // 1 = active avatar
}
```

### 4.5 Matchmaking Packets

#### 4.5.1 Matchmaking_Request
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Matchmaking_Request
{
    public UInt16 packetType;          // MATCHMAKING_REQUEST
    public byte matchType;             // MatchType enum
    public byte state;                 // 0=Cancel, 1=Start
}
```

#### 4.5.2 Matchmaking_Response
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Matchmaking_Response
{
    public UInt16 packetType;          // MATCHMAKING_RESPONSE
    public UInt32 elapsedTime;         // Time spent searching (seconds)
    public byte state;                 // 0=Searching, 1=Found, 2=Cancelled
}
```

#### 4.5.3 Match_Avatar (Critical - Player Match Data)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Avatar
{
    public UInt32 playerID;            // Unique player ID for this match
    public byte team;                  // Team number

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;            // Display name

    public byte fightingStyle;         // FightingStyles enum
    public byte fighterClass;          // FighterClass enum
    public byte godSelected;           // TrinityGods enum

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementals;          // Equipped elementals

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public ItemInfo[] wearItems;       // Equipped items

    public byte weaponVariant;         // Weapon skin
    public UInt32 bronze;              // Bronze currency
    public byte lives;                 // Remaining lives
    public byte guna;                  // Guna state
}
```

#### 4.5.4 Match_Server_Data
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Server_Data
{
    public UInt16 packetType;          // SERVER_DATA

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string serverIP;            // Game server IP

    public UInt16 serverPort;          // Game server port (6006+)
}
```

#### 4.5.5 Match_Confirm
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Confirm
{
    public UInt16 packetType;          // MATCHMAKING_DATA
    public byte matchType;             // MatchType enum
    public byte playerCount;           // Number of players

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public Match_Avatar[] players;     // Up to 6 players
}
```

### 4.6 Friends Packets

#### 4.6.1 Friends_Data
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friends_Data
{
    public UInt16 packetType;          // FRIENDS_DATA_RESPONSE
    public UInt16 totalFriends;        // Total friend count
    // Followed by Friend_Info[] array
}
```

#### 4.6.2 Friend_Info
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friend_Info
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
    public string friendID;            // Friend's unique ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;         // Display name

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string avatarName;          // Avatar name

    public byte fightingStyle;         // FightingStyles enum
    public byte status;                // Online status
    public byte isFavourite;           // Favourite flag
    public byte isPending;             // Pending request
    public byte isOnline;              // Online flag
}
```

#### 4.6.3 FriendSearch_Request
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendSearch_Request
{
    public UInt16 packetType;          // FRIENDS_SEARCH_REQUEST

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
    public string friendID;            // Friend ID to search
}
```

#### 4.6.4 FriendSearch_Reply
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendSearch_Reply
{
    public UInt16 packetType;          // FRIENDS_SEARCH_RESPONSE
    public byte isValid;               // 1 = found
    public byte isFriend;              // Already friends
    public byte isPending;             // Request pending
    public byte isTargetPending;       // They sent request to us

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;         // Their profile name

    public byte profileImage;          // Profile image ID
}
```

### 4.7 Party Packets

#### 4.7.1 PartyInviteRequest
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyInviteRequest
{
    public UInt16 packetType;          // PARTY_INVITE_REQUEST

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
    public string friendID;            // Friend to invite
}
```

#### 4.7.2 PartyDataPacket
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyDataPacket
{
    public UInt16 packetType;          // PARTY_DATA_PACKET
    public UInt32 partyID;             // Party unique ID
    public byte playerCount;           // Current player count

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
    public PartyPlayers[] players;     // Up to 3 party members
}
```

#### 4.7.3 PartyPlayers
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyPlayers
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
    public string friendID;            // Player ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;         // Display name

    public byte fightingStyle;         // FightingStyles enum
    public byte godSelected;           // TrinityGods enum

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementals;          // Equipped elementals

    public byte isHost;                // 1 = party leader
    public byte isReady;               // 1 = ready for match
}
```

### 4.8 Lobby Packets

#### 4.8.1 LobbyCreateRequest
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyCreateRequest
{
    public UInt16 packetType;          // LOBBY_CREATE_REQUEST
    public byte mode;                  // Match mode
    public byte loka;                  // Map selection
    public byte isPublic;              // 1 = public lobby
    public byte allowBots;             // 1 = fill with bots
    public byte region;                // ServerRegion enum

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string password;            // Optional password
}
```

#### 4.8.2 LobbyInfo
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyInfo
{
    public UInt32 lobbyID;             // Lobby unique ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string hostName;            // Host display name

    public byte loka;                  // Map
    public byte currentPlayers;        // Current player count
    public byte maxPlayers;            // Max players
    public byte mode;                  // Match mode
    public byte isPublic;              // Public flag
    public byte allowBots;             // Bots allowed
    public byte region;                // Server region
}
```

#### 4.8.3 LobbyDataPacket
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyDataPacket
{
    public UInt16 packetType;          // LOBBY_DATA_PACKET
    public UInt32 lobbyID;             // Lobby ID
    public byte playerCount;           // Current players
    public byte maxPlayers;            // Max players
    public byte mode;                  // Match mode
    public byte loka;                  // Map
    public byte isPublic;              // Public flag
    public byte allowBots;             // Bots flag
    public byte region;                // Region

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public LobbyPlayerInfo[] players;  // Up to 6 players
}
```

#### 4.8.4 LobbyPlayerInfo
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyPlayerInfo
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
    public string friendID;            // Player ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;         // Display name

    public byte profileImage;          // Profile image
    public byte slotPosition;          // Slot index (0-5)
    public byte isReady;               // Ready flag
    public byte isHost;                // Host flag
    public byte hasMic;                // Microphone flag

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementals;          // Equipped elementals

    public byte fightingStyle;         // FightingStyles
    public byte godSelected;           // TrinityGods
}
```

### 4.9 Store/Currency Packets

#### 4.9.1 PlayerRewards
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PlayerRewards
{
    public UInt16 packetType;          // PLAYER_REWARDS_REPLY
    public UInt32 timeShards;          // Time shards balance
    public UInt32 bronze;              // Bronze coins
    public UInt32 silver;              // Silver coins
    public UInt32 gold;                // Gold coins
    public byte lives;                 // Remaining lives
    public UInt32 hellTime;            // Hell time remaining
    public byte guna;                  // Guna state
    public UInt32 wins;                // Total wins
    public UInt32 losses;              // Total losses
    public UInt32 sattva;              // Sattva karma
    public UInt32 rajas;               // Rajas karma
    public UInt32 tamas;               // Tamas karma
    public UInt32 bhaktiTokens;        // Bhakti meditation tokens
    public UInt32 gnanaTokens;         // Gnana meditation tokens
}
```

#### 4.9.2 MatchRewards
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchRewards
{
    public UInt16 packetType;          // MATCH_REWARDS
    public UInt32 timeShards;          // Time shards earned
    public UInt32 bronze;              // Bronze earned
    public byte lives;                 // Lives change
    public UInt32 hellShards;          // Hell shards earned
    public byte guna;                  // New guna state
    public UInt32 rajas;               // Rajas change
    public UInt32 tamas;               // Tamas change
    public UInt32 sattva;              // Sattva change
    public byte itemCount;             // Items earned
    // Followed by MatchRewardItemInfo[] if itemCount > 0
}
```

#### 4.9.3 PurchaseRequest
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PurchaseRequest
{
    public UInt16 packetType;          // REQUEST_PURCHASE

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] itemUUID;            // Item to purchase
}
```

#### 4.9.4 PurchaseComplete
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PurchaseComplete
{
    public UInt16 packetType;          // PURCHASE_COMPLETE
    public byte success;               // 1 = success
    public byte itemType;              // Item type purchased
    public UInt32 bronzeRemaining;     // Bronze after purchase
    public UInt32 silverRemaining;     // Silver after purchase
    public UInt32 goldRemaining;       // Gold after purchase
}
```

### 4.10 Chat Packet

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ChatMessageRequest
{
    public UInt16 packetType;          // CHAT_MESSAGE

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)]
    public string friendID;            // Recipient ID

    public byte messageType;           // 1=friends, 2=party, 3=lobby

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 100)]
    public string message;             // Message content
}
```

---

## 5. MatchKeeper Protocol (MK)

### 5.1 Overview

The MatchKeeper is the orchestration layer between game servers and the backend.

**Transport:** TCP
**Port:** 6767 (localhost)
**File:** `Assets/Scripts/Managers/MKManager.cs` (Server)

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Backend   │ ──WSS── │ MatchKeeper │ ──TCP── │ Game Server │
│   Server    │         │   :6767     │         │   :6006+    │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              │ Assigns matches to servers
                              │ Receives match results
                              ▼
                        ┌─────────────┐
                        │   Client    │
                        │   (UDP)     │
                        └─────────────┘
```

### 5.2 Packet Types

```csharp
public enum PacketType
{
    MK_AUTH       = 0x1000,  // Server → MK: Authentication
    MK_STARTGAME  = 0x1001,  // MK → Server: Start match
    MK_MATCHEND   = 0x1002,  // Server → MK: Match completed
}
```

### 5.3 MK Packet Structures

#### 5.3.1 MKAuth (Server → MatchKeeper)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKAuth
{
    public UInt16 packetLen;           // Packet length
    public UInt16 packetType;          // MK_AUTH (0x1000)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] ServerUUID;          // Server unique ID

    public byte isUnityEditor;         // 1 = running in editor
}
```

#### 5.3.2 MKMatchData (MatchKeeper → Server)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchData
{
    public UInt16 packetLen;           // Packet length
    public UInt16 packetType;          // MK_STARTGAME (0x1001)
    public byte matchType;             // MatchType enum
    public byte IsFirstMatch;          // 1 = player's first match

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] MatchUUID;           // Match unique ID

    public int matchPort;              // Port to listen on
    public byte avatarCount;           // Number of players

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public MKMatchAvatar[] avatarInfo; // Player info (up to 6)
}
```

#### 5.3.3 MKMatchAvatar
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchAvatar
{
    public UInt32 UniqueID;            // In-match player ID

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] avatarUniqueID;      // Avatar UUID

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionUUID;         // Session UUID for auth

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string UserID;              // User ID

    public UInt32 teamID;              // Team number

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;            // Display name

    public byte fightingStyle;         // FightingStyles enum
    public byte fighterClass;          // FighterClass enum
    public byte godSelected;           // TrinityGods enum

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected;   // 4 elementals

    public byte weaponVariant;         // Weapon skin
    public byte IsBot;                 // 1 = bot player
}
```

#### 5.3.4 MKMatchEnd (Server → MatchKeeper)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchEnd
{
    public UInt16 packetLen;           // Packet length
    public UInt16 packetType;          // MK_MATCHEND (0x1002)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] MatchUUID;           // Match UUID

    public UInt32 matchTime;           // Match duration (seconds)
    public byte winningTeam;           // Winning team number
    public byte avatarCount;           // Number of players

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public MKMatchAvatarData[] avatarData; // Player results
}
```

#### 5.3.5 MKMatchAvatarData
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchAvatarData
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] avatarUniqueID;      // Avatar UUID

    public byte avatarTeam;            // Team number
    public byte karmaPlayerCount;      // Karma decisions made

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public KarmaDecision[] karmaDecision; // Karma choices

    public byte deadPosition;          // Final position (1st, 2nd, etc.)
    public UInt32 deadDuration;        // Time dead
    public UInt16 damageMeleeDealt;    // Melee damage dealt
    public UInt16 damageMeleeReceived; // Melee damage received
    public UInt16 damageSpellDealt;    // Spell damage dealt
    public UInt16 damageSpellReceived; // Spell damage received
    public UInt16 damageMeleeBlocked;  // Melee damage blocked
    public UInt16 damageSpellBlocked;  // Spell damage blocked
}
```

#### 5.3.6 KarmaDecision
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct KarmaDecision
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] AvatarUUID;          // Target avatar UUID

    public byte Decision;              // Karma enum (Sattva/Rajas/Tamas)
}
```

### 5.4 MK Connection Flow

```
1. Server Startup
   └─> MKManager.Initialize()
       └─> TCP Connect to 127.0.0.1:6767

2. Connection Accepted
   └─> OnMKConnectionAccepted()
       └─> Send MKAuth packet
           └─> MK registers server as available

3. Match Assignment
   └─> MK sends MK_STARTGAME
       └─> OnMKMessageReceived()
           └─> Parse MKMatchData
               └─> Socket.Initialize(matchPort)
                   └─> Populate avatarList
                       └─> MatchState.SignalMatchReady()

4. Match End
   └─> SendMKMatchEnd()
       └─> MK processes results
           └─> Updates backend database
```

---

## 6. PlayFab Cloud Protocol

### 6.1 Overview

PlayFab provides cloud backend services for persistent data, leaderboards, and economy.

**File Location:** `Assets/Scripts/PlayFab/`

### 6.2 Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PlayFabManager                              │
│                    (Main Orchestrator)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ PlayerData   │  │ DataBridge   │  │ AvatarCurrencyService│  │
│  │              │  │ (Single      │  │ (Per-Avatar Economy) │  │
│  │              │  │  Source)     │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Matchmaker   │  │ Leaderboard  │  │ KarmaManager         │  │
│  │              │  │              │  │ (Lives/Hell/Guna)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ StoreService │  │ Inventory    │  │ CurrencyService      │  │
│  │              │  │ Service      │  │ (Conversion)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 PlayFabManager

**File:** `PlayFabManager.cs`

**Key Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `Instance` | PlayFabManager | Singleton |
| `IsReady` | bool | Logged in + data loaded |
| `IsLoggedIn` | bool | Connected to PlayFab |
| `PlayerData` | PlayFabPlayerData | Player data component |
| `Leaderboard` | PlayFabLeaderboard | Leaderboard component |

**Events:**
| Event | Description |
|-------|-------------|
| `OnReady` | All systems initialized |
| `OnError(string)` | Error occurred |

### 6.4 PlayFabDataBridge (Single Source of Truth)

**File:** `PlayFabDataBridge.cs`

This is the **primary data synchronization layer** between PlayFab and the game.

**Key Methods:**
| Method | Description |
|--------|-------------|
| `InitializeAfterLogin(playFabId)` | Initialize after login |
| `LoadPlayerData()` | Load all player data |
| `SaveAvatar(avatarData)` | Save avatar to PlayFab |
| `SetActiveAvatar(avatarId)` | Switch active avatar |
| `SaveSettings(settings)` | Save user settings |
| `AddCurrency(type, amount)` | Add currency |
| `MarkTutorialComplete()` | Mark tutorial done |

**Events:**
| Event | Parameters | Description |
|-------|------------|-------------|
| `OnAllDataLoaded` | - | Data load complete |
| `OnPlayerTypeDetected` | isNewPlayer | New or returning player |
| `OnDataLoadFailed` | error | Load failed |

### 6.5 PlayFab Data Classes

#### 6.5.1 PFPlayerGameData (Top Level)
```csharp
public class PFPlayerGameData
{
    public PFPlayerStats Stats;        // Match statistics
    public PFPlayerLoadout Loadout;    // Character loadout
    public PFPlayerInventory Inventory; // Owned items
    public PFPlayerSettings Settings;  // User settings
    public PFPlayerProgress Progress;  // Level/XP
    public PFAvatarData Avatar;        // Active avatar
}
```

#### 6.5.2 PFAvatarData
```csharp
public class PFAvatarData
{
    public string avatarId;            // Avatar UUID
    public string nickname;            // Display name
    public int fightingStyle;          // FightingStyles enum
    public int fighterClass;           // FighterClass enum
    public int godSelected;            // TrinityGods enum
    public int[] elementals;           // 4 equipped elementals
    public int[] wearItems;            // 6 equipped item codes
    public int weaponVariant;          // Weapon skin
    public bool isActive;              // Currently active
}
```

#### 6.5.3 PFPlayerStats
```csharp
public class PFPlayerStats
{
    public int totalMatches;           // Total matches played
    public int wins;                   // Total wins
    public int losses;                 // Total losses
    public int kills;                  // Total kills
    public int deaths;                 // Total deaths
    public int damageDealt;            // Total damage dealt
    public int damageReceived;         // Total damage received
    public int rating;                 // Player rating
    public int winStreak;              // Current win streak
    public int bestWinStreak;          // Best win streak
}
```

#### 6.5.4 PFPlayerLoadout
```csharp
public class PFPlayerLoadout
{
    public int fightingStyle;          // Selected fighter
    public int godSelected;            // Selected god
    public int[] elementals;           // 4 equipped spells
    public Dictionary<int, int> skins; // Equipped skins per slot
}
```

### 6.6 PlayFabKarmaManager (Lives/Hell System)

**File:** `PlayFabKarmaManager.cs`

Manages the karma/lives/hell punishment system.

**Key Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `CurrentLives` | int | Current lives (0-3) |
| `IsInHell` | bool | Currently in hell |
| `HellTimeRemaining` | TimeSpan | Hell time left |
| `CurrentGuna` | KarmaGunaState | Guna breakdown |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `LoadKarmaState()` | Load complete karma state |
| `ProcessMatchEnd(result)` | Process match result |
| `ModifyLives(delta)` | Add/remove lives |
| `UseHellShard()` | Use shard to reduce hell time |
| `CompleteMeditation()` | Restore life from meditation |

**Data Classes:**
```csharp
public class KarmaGunaState
{
    public float sattvaPercent;        // Good karma %
    public float rajasPercent;         // Neutral karma %
    public float tamasPercent;         // Bad karma %
    public string dominantGuna;        // "sattva", "rajas", or "tamas"
}

public class KarmaHellStateData
{
    public DateTime hellEntryTime;     // When entered hell
    public DateTime hellExitTime;      // When can exit
    public bool isInHell;              // Currently in hell
}
```

### 6.7 PlayFabAvatarCurrencyService

**File:** `PlayFabAvatarCurrencyService.cs`

All currency is now per-avatar, not per-player.

**Currency Types:**
| Currency | Code | Description |
|----------|------|-------------|
| Bronze | BR | Basic currency |
| Silver | SV | Premium currency |
| Gold | GD | Premium currency |
| Lives | LV | Match lives |
| TimeShards | TS | Meditation shards |
| HellShards | HS | Hell reduction shards |
| BhaktiTokens | BT | Bhakti meditation tokens |
| GnanaTokens | GT | Gnana meditation tokens |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `LoadAvatarCurrencies()` | Load currencies for active avatar |
| `AddCurrency(type, amount)` | Add currency |
| `SubtractCurrency(type, amount)` | Subtract currency |
| `HasEnoughCurrency(type, amount)` | Check balance |

### 6.8 PlayFabStoreService

**File:** `PlayFabStoreService.cs`

**Key Methods:**
| Method | Description |
|--------|-------------|
| `LoadCatalogAsync()` | Load PlayFab catalog |
| `GetItemsForAvatarAsync(style, class)` | Filter items |
| `PurchaseItemAsync(itemId, currency)` | Purchase item |

**Data Classes:**
```csharp
public class PlayFabStoreItem
{
    public string ItemId;              // PlayFab item ID
    public string DisplayName;         // Display name
    public uint BronzePrice;           // Price in bronze
    public uint SilverPrice;           // Price in silver
    public uint GoldPrice;             // Price in gold
    public int itemCode;               // Game item code
    public PlayFabItemData ParsedData; // Parsed custom data
}
```

### 6.9 PlayFabLeaderboard

**File:** `PlayFabLeaderboard.cs`

**Leaderboard Names:**
| Name | Description |
|------|-------------|
| `Rating` | Player rating leaderboard |
| `TotalWins` | Total wins leaderboard |
| `TotalKills` | Total kills leaderboard |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `UpdateLeaderboard(name, value)` | Update score |
| `GetLeaderboard(name, count)` | Get top players |
| `GetLeaderboardAroundPlayer(name)` | Get nearby ranks |
| `GetPlayerRank(name)` | Get own rank |

---

## 7. In-Game UDP Protocol

### 7.1 Overview

The in-game protocol handles real-time combat using UDP with LiteNetLib.

**Transport:** UDP (LiteNetLib native DLL)
**Tick Rate:** 60Hz (16.67ms per tick)
**Port:** 6006 (default), dynamic in production

**Files:**
- Client: `Assets/Scripts/Managers/NetworkManager.cs`
- Server: `Assets/Scripts/Network/Socket.cs`, `UDPSocket.cs`

### 7.2 Packet Types

```csharp
// Client → Server
public enum PacketTypeOUT
{
    NETWORKEVENT      = 0x1400,  // Disconnect
    CREATECHARACTER   = 0x1401,  // Authenticate
    PLAYERINPUT       = 0x1403,  // Tick input (60Hz)
    RESPAWNCHARACTER  = 0x1405,  // Request respawn
    LOGDATA           = 0x1406,  // Debug log
    PLAYERKARMA       = 0x1409,  // Karma decision
    TUTORIALPROGRESS  = 0x140B,  // Tutorial progress
}

// Server → Client
public enum PacketTypeIN
{
    NETWORKEVENT      = 0x1400,  // Disconnect
    CREATECHARACTER   = 0x1401,  // Auth reply
    REMOVECHARACTER   = 0x1402,  // Player left
    WORLDSNAPSHOT     = 0x1403,  // World state (60Hz)
    SIMULATIONRESULT  = 0x1404,  // Prediction result
    RESPAWNCHARACTER  = 0x1405,  // Respawn confirmed
    LOGDATA           = 0x1406,  // Combat log
    ENDGAMEDATA       = 0x1407,  // Match over
    MATCHSTATEINFO    = 0x1408,  // Match state change
    PLAYERKARMA       = 0x1409,  // Karma update
    FORFEITMATCH      = 0x140A,  // Forfeit
    TUTORIALPROGRESS  = 0x140B,  // Tutorial progress
}
```

### 7.3 Authentication Packets

#### 7.3.1 Authenticate_Player (Client → Server)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Authenticate_Player
{
    public UInt16 packetType;          // CREATECHARACTER (0x1401)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionID;           // Session UUID (must match server's avatarList)
}
// Total Size: 18 bytes
```

#### 7.3.2 Authenticate_PlayerReply (Server → Client)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Authenticate_PlayerReply
{
    public UInt16 packetType;          // CREATECHARACTER (0x1401)
    public UInt32 uniqueID;            // Assigned player ID
    public float posX;                 // Spawn position X
    public float posZ;                 // Spawn position Z
    public float rotation;             // Spawn rotation
}
// Total Size: 18 bytes
```

### 7.4 Input Protocol (60Hz)

#### 7.4.1 TickInput (Client → Server)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct TickInput
{
    public UInt16 packetType;          // PLAYERINPUT (0x1403)
    public byte JoystickAxis;          // Packed X/Y (4 bits each)
    public float cameraRotation;       // Camera angle (0-360)
    public UInt32 currentTick;         // Client tick number
    public UInt32 serverTick;          // Last received server tick
    public UInt32 state;               // Current FSM state
    public byte specialAbility;        // Special ability state
    public float abilityX;             // Ability target X
    public float abilityY;             // Ability target Y
    public byte meleeAbility;          // Melee ability state
    public byte abilityEx;             // Extended ability state
    public byte elementalAbility1;     // Elemental 1 state
    public byte elementalAbility2;     // Elemental 2 state
    public byte elementalAbility3;     // Elemental 3 state
    public byte elementalAbility4;     // Elemental 4 state
    public byte dodgeAbility;          // Dodge state
    public byte astraAbility;          // Ultimate state
}
// Total Size: 34 bytes
```

**Joystick Encoding:**
```
Byte format: 0xXY where X = horizontal, Y = vertical
Values: 0x0 = 0, 0x1 = 1, 0xF = -1

Examples:
  0x00 = (0, 0)   - No input
  0x10 = (1, 0)   - Right
  0xF0 = (-1, 0)  - Left
  0x01 = (0, 1)   - Forward
  0x0F = (0, -1)  - Backward
  0x11 = (1, 1)   - Forward-Right
  0xFF = (-1, -1) - Backward-Left
```

**Ability State Values (EventState enum):**
```csharp
public enum EventState
{
    NONE              = 0,  // No action
    START             = 1,  // Button pressed
    PROGRESS          = 2,  // Button held
    PROGRESS_CONTINUOUS = 3, // Continuous attack
    AIMING            = 4,  // Aiming mode
    SHIELDUP          = 5,  // Shield raised
    CHANNELING        = 6,  // Channeling spell
    DONE              = 7,  // Button released
}
```

### 7.5 World Snapshot (60Hz)

#### 7.5.1 Snapshot Packet Structure
```
┌──────────────┬──────────────┬──────────────┬─────────────────────────────┐
│ PacketType   │ SnapshotCount│ Size         │ Snapshot Data               │
│ (2 bytes)    │ (1 byte)     │ (2 bytes)    │ (variable)                  │
└──────────────┴──────────────┴──────────────┴─────────────────────────────┘
                                              │
                    ┌─────────────────────────┘
                    ▼
┌──────────────┬──────────────┬─────────────────────────┬──────────────────┐
│ ServerTick   │ PlayerCount  │ See_MoveCharacter[]     │ Entities         │
│ (4 bytes)    │ (1 byte)     │ (50 bytes × N)          │ (variable)       │
└──────────────┴──────────────┴─────────────────────────┴──────────────────┘
```

#### 7.5.2 See_MoveCharacter (Per-Player State)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct See_MoveCharacter
{
    public UInt32 pUniqueID;           // Player ID
    public byte JoystickAxis;          // Last input joystick
    public float cameraRotation;       // Camera rotation
    public float positionX;            // World position X
    public float positionZ;            // World position Z
    public UInt32 state;               // Current FSM state
    public float abilityX;             // Ability target X
    public float abilityY;             // Ability target Y
    public float abilityRotation;      // Ability rotation
    public UInt16 currStamina;         // Current stamina
    public UInt16 willPower;           // Current willpower
    public UInt16 currFocus;           // Current focus
    public UInt32 impactIndicator;     // Impact effects
    public UInt32 impactMeleePlayer;   // Melee impact source
    public byte activeElemental;       // Active spell element
    public byte attributeEx;           // Extended attributes
}
// Total Size: 50 bytes
```

### 7.6 Simulation/Prediction Packets

#### 7.6.1 SimulationResult (Server → Client)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SimulationResult
{
    public UInt16 packetType;          // SIMULATIONRESULT (0x1404)
    public UInt32 currentTick;         // Tick being verified
    public float positionX;            // Authoritative X
    public float positionZ;            // Authoritative Z
    public float rotation;             // Authoritative rotation
    public byte state;                 // Authoritative state
    public byte moveSpeed;             // Movement speed modifier
}
// Total Size: 21 bytes
```

**MoveSpeed Encoding:**
```
Bits 0-1: SlowType (0=NONE, 1=FIFTY, 2=ZERO)
Bits 2-7: Reserved
```

### 7.7 Entity Packets

#### 7.7.1 EntityData
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct EntityData
{
    public UInt32 UniqueID;            // Entity unique ID
    public UInt32 EntityType;          // Entity type
    public UInt32 EntityPlayer;        // Owner player ID
    public UInt32 frameNumber;         // Creation frame
    public byte EntityState;           // Current state
    public float SourceLocationX;      // Origin X
    public float SourceLocationY;      // Origin Z
    public float EntityEndLocationX;   // Target X
    public float EntityEndLocationY;   // Target Z
    public byte hasExtendedInfo;       // 1 = has EntityDataEx
}
// Total Size: 37 bytes
```

#### 7.7.2 EntityDataEx (For Astra Projectiles)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct EntityDataEx
{
    public UInt32 EntityType;          // Extended type
    public UInt32 TargetPlayer;        // Target player ID
}
// Total Size: 8 bytes
```

### 7.8 Combat Log Packets

#### 7.8.1 LogData (Damage/Effects)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LogData
{
    public UInt16 packetType;          // LOGDATA (0x1406)
    public UInt32 targetPlayer;        // Who received damage
    public UInt32 sourcePlayer;        // Who dealt damage
    public UInt16 damage;              // Damage amount
    public byte logType;               // CombatLogType enum
    public byte damageType;            // DamageType enum
    public byte effectType;            // EffectType enum
    public UInt16 staminaDamage;       // Stamina damage
    public UInt16 shieldHealth;        // Shield health remaining
}
// Total Size: 24 bytes
```

**CombatLogType:**
```csharp
public enum CombatLogType
{
    DAMAGE_DEALT = 0,
    DAMAGE_BLOCKED = 1,
    EFFECT_APPLIED = 2,
    EFFECT_REMOVED = 3,
    KILL = 4,
    DEATH = 5,
}
```

### 7.9 Match State Packets

#### 7.9.1 MatchStateInfo
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchStateInfo
{
    public UInt16 packetType;          // MATCHSTATEINFO (0x1408)
    public UInt16 timeRemaining;       // Seconds remaining
    public byte matchState;            // MatchStates enum
}
// Total Size: 5 bytes
```

#### 7.9.2 MatchOver_Data
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchOver_Data
{
    public UInt16 packetType;          // ENDGAMEDATA (0x1407)
    public byte winningTeam;           // Winning team number

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public UInt32[] playerOrder;       // Final standings

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public UInt32[] karmaPlayers;      // Karma recipients

    public UInt32 karmaPlayerGiver;    // Karma giver
    public UInt16 damageMeleeDealt;    // Total melee dealt
    public UInt16 damageMeleeReceived; // Total melee received
    public UInt16 damageSpellDealt;    // Total spell dealt
    public UInt16 damageSpellReceived; // Total spell received
    public UInt16 damageAstraDealt;    // Total astra dealt
    public UInt16 damageAstraReceived; // Total astra received
    public UInt16 damageMeleeBlocked;  // Melee blocked
    public UInt16 damageSpellBlocked;  // Spell blocked
    public UInt16 damageAstraBlocked;  // Astra blocked
}
// Total Size: ~60 bytes
```

### 7.10 Debug/Logging Packets

#### 7.10.1 SimulationFailLog
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SimulationFailLog
{
    public UInt16 packetType;          // LOGDATA (0x1406)
    public byte logType;               // ClientLogType.SIMULATION_FAIL
    public UInt32 frameNumber;         // Tick number
    public float curX;                 // Client predicted X
    public float curY;                 // Client predicted Y
    public float realX;                // Server authoritative X
    public float realY;                // Server authoritative Y
    public byte state;                 // State at failure
    public byte speed;                 // Speed modifier
}
```

#### 7.10.2 StateMismatchLog
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct StateMismatchLog
{
    public UInt16 packetType;          // LOGDATA (0x1406)
    public byte logType;               // ClientLogType.STATE_MISMATCH
    public UInt32 frameNumber;         // Tick number
    public byte curState;              // Client state
    public byte realState;             // Server state
}
```

### 7.11 Server Tick System

The server runs multiple loops at different rates:

| Loop | Interval | Purpose |
|------|----------|---------|
| FastLoop | 1ms | Network polling, input processing |
| FixedLoop | 60ms | World snapshots, state broadcast |
| ProjectileLoop | 20ms | Projectile/entity updates |
| RegenLoop | 500ms | Stamina regeneration |

```csharp
// Server tick rates (GameManager.cs)
private float fastLoopTick = 0.001f;       // 1ms
private float fixedLoopTick = 0.06f;       // 60ms (16.67Hz)
private float projectileLoopTick = 0.02f;  // 20ms (50Hz)
private float regenLoopTick = 0.5f;        // 500ms (2Hz)
```

### 7.12 Jitter Compensation

**File:** `JitterCompensator.cs`

```csharp
public static float GetFactor(int queueSize, int min, int max)
{
    if (queueSize >= max)      return 0.95f;  // Speed up
    else if (queueSize <= min) return 1.05f;  // Slow down
    else                       return 1.00f;  // Normal
}
```

**Buffer Thresholds:**
- Min: 2 packets
- Max: 5 packets

---

## 8. State Machines

### 8.1 Match State Machine

**File:** `Assets/Scripts/MatchState.cs` (Server)

```
┌────────┐     ┌──────────┐     ┌──────────┐     ┌───────┐
│  NONE  │────▶│ PREMATCH │────▶│ TELEPORT │────▶│ MATCH │
└────────┘     └──────────┘     └──────────┘     └───┬───┘
                                                     │
┌────────┐     ┌──────────┐     ┌──────────┐         │
│  END   │◀────│ POSTMATCH│◀────│ ENDMATCH │◀────────┘
└────────┘     └──────────┘     └──────────┘
```

```csharp
public enum MatchStates
{
    NONE      = 0,  // Waiting for connection
    PREMATCH  = 1,  // Countdown (15s, waiting for humans)
    TELEPORT  = 2,  // Spawning players
    MATCH     = 3,  // Combat active (60Hz)
    ENDMATCH  = 4,  // Winner determined
    POSTMATCH = 5,  // Results, karma voting
    END       = 6,  // Cleanup, disconnect
}
```

**State Durations:**
| State | Duration | Description |
|-------|----------|-------------|
| NONE | Until all connect | Waiting for players |
| PREMATCH | 15 seconds | Countdown |
| TELEPORT | 2 seconds | Spawn animation |
| MATCH | Until win condition | Combat |
| ENDMATCH | 3 seconds | Victory animation |
| POSTMATCH | 30 seconds | Karma selection |
| END | Immediate | Cleanup |

### 8.2 Player FSM (Finite State Machine)

**File:** `Assets/Scripts/StateMachine/StateManager.cs`

#### 8.2.1 State Types (31 States)
```csharp
public enum StateType
{
    Idle                = 0,
    Melee               = 1,
    Try_Shield_Block    = 2,
    Shield_Block        = 3,
    Shield_Attack       = 4,
    Aiming              = 5,
    Spell_Aiming        = 6,
    Channel             = 7,
    Cast_Spell          = 8,
    Spell_Anticipate    = 9,
    Special             = 10,
    Special_Aiming      = 11,
    Axe_Callback        = 12,
    State_Unused        = 13,
    Death               = 14,
    Cast_Shield         = 15,
    Water_Pushback      = 16,
    Pushback_Land       = 17,
    Special_Anticipate  = 18,
    Stun                = 19,
    Melee_Second        = 20,
    Third_Eye           = 21,
    Third_Eye_Anticipate = 22,
    Dodge               = 23,
    Astra_Anticipate    = 24,
    Astra_Channel       = 25,
    Astra_Cast          = 26,
    Jump                = 27,
    Teleport            = 28,
    Vulnerable          = 29,
    Victory             = 30,
    Undefined           = 31,
}
```

#### 8.2.2 Block Flags
```csharp
[System.Flags]
public enum BlockFlags
{
    Block_Elemental_Spell   = 1 << 0,   // Can't cast spells
    Block_JoystickAxis      = 1 << 1,   // Can't move
    Block_Melee             = 1 << 2,   // Can't melee
    Block_Camera            = 1 << 3,   // Can't rotate camera
    Block_Astra             = 1 << 4,   // Can't use ultimate
    Block_Shield            = 1 << 5,   // Can't use shield
    Block_ThirdEye          = 1 << 6,   // Can't use third eye
    Block_Unique            = 1 << 7,   // Can't use unique ability
    Block_Elemental_Shield  = 1 << 8,   // Can't cast shield spell
    Block_Dodge             = 1 << 9,   // Can't dodge
    Block_Jump              = 1 << 10,  // Can't jump
    BlockAll = Block_Elemental_Spell | Block_Elemental_Shield |
               Block_JoystickAxis | Block_Melee | Block_Camera |
               Block_Astra | Block_Shield | Block_ThirdEye |
               Block_Unique | Block_Dodge | Block_Jump
}
```

#### 8.2.3 State Block Configurations
```csharp
public enum StateBlockFlags
{
    // Full freedom
    Idle = BlockFlags.BlockAll & ~(BlockFlags.BlockAll),

    // Movement + Camera allowed
    Melee = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera),
    Shield_Block = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Shield),

    // Aiming states
    Aiming = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Melee),
    Spell_Aiming = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Elemental_Spell),

    // Locked states
    Death = BlockFlags.BlockAll,
    Stun = BlockFlags.BlockAll,
    Water_Pushback = BlockFlags.BlockAll,
    Teleport = BlockFlags.BlockAll,
    Victory = BlockFlags.BlockAll,

    // ... (more states)
}
```

### 8.3 State Transition Rules

**Common Transitions:**
```
Idle ──────────────────────────────────────────────────────────────────┐
 │                                                                     │
 ├──[Attack Button]────▶ Aiming ──[Release]────▶ Melee ──[Done]───────┤
 │                                                                     │
 ├──[Special Button]───▶ Special_Anticipate ──▶ Special ──[Done]──────┤
 │                                                                     │
 ├──[Spell Button]─────▶ Channel ──▶ Spell_Aiming ──▶ Cast_Spell ─────┤
 │                                                                     │
 ├──[Shield Button]────▶ Shield_Block ──[Attack]──▶ Shield_Attack ────┤
 │                                                                     │
 ├──[Astra Button]─────▶ Astra_Anticipate ──▶ Astra_Channel ──────────┤
 │                       ──▶ Astra_Cast ──[Done]──────────────────────┤
 │                                                                     │
 ├──[Dodge Button]─────▶ Dodge ──[Done]───────────────────────────────┤
 │                                                                     │
 └──[Hit by Water]─────▶ Water_Pushback ──▶ Pushback_Land ──[Done]────┘
```

---

## 9. Game Data Systems

### 9.1 Fighter Attributes

**File:** `Assets/ScriptableObjects/FighterAttributes.cs`

```csharp
public class FighterAttributes : ScriptableObject
{
    // Base Stats
    public float obj_stamina;          // Max stamina (10000)
    public float obj_armor;            // Damage reduction (0-10)
    public float obj_movespeed;        // Movement speed (0-550)
    public float obj_damage;           // Base damage (100)
    public float obj_range;            // Attack range (3.5)
    public float obj_hpregen;          // HP regen rate (2)
    public float obj_maxWillpower;     // Max willpower (15000)

    // Focus System
    public float maxFocus;             // Max focus (100)
    public float focusSegmentSize;     // Segment size (25)
    public float focusMaxPerHit;       // Max gain per hit (10)

    // Attack Speeds (multipliers)
    public float melee_AttackSpeed;        // 1.0-10.0
    public float meleeSecond_AttackSpeed;  // 1.0-10.0
    public float fire_AttackSpeed;         // 1.0-10.0
    public float water_AttackSpeed;        // 1.0-10.0
    public float air_AttackSpeed;          // 1.0-10.0
    public float ether_AttackSpeed;        // 1.0-10.0
    public float earth_AttackSpeed;        // 1.0-10.0
    public float special_AttackSpeed;      // 1.0-10.0
    public float maxHoldTime;              // Charge time (0.1-15)
}
```

**Character Base Values:**
| Character | Stamina | Armor | MoveSpeed | Damage | Range |
|-----------|---------|-------|-----------|--------|-------|
| Amuktha | 10000 | 7 | 465 | 100 | 3.5 |
| MantraMuktha | 10000 | 5 | 450 | 100 | 5.0 |
| MukthaMuktha | 10000 | 8 | 440 | 110 | 4.0 |
| PaniMuktha | 10000 | 5 | 460 | 95 | 6.0 |
| YantraMuktha | 10000 | 4 | 470 | 90 | 7.0 |

### 9.2 God Bonuses

**File:** `Assets/ScriptableObjects/GodBonuses.cs`

```csharp
public class GodBonuses : ScriptableObject
{
    public TrinityGods god;

    // Bonuses
    public float bonus_range_melee;      // Melee range bonus
    public float melee_angle;            // Melee angle (0-360)
    public float bonus_stamina;          // Stamina bonus
    public float bonus_armor;            // Armor bonus
    public float bonus_movespeed;        // Move speed bonus
    public float bonus_unique_range;     // Unique ability range
    public float damage_buff;            // Damage multiplier (Shiva)
    public float willpower_Multiplier;   // Willpower multiplier

    // Penalties
    public float move_speed_penalty;
    public float armor_penalty;
    public float range_penalty;

    // Attack Speed Modifiers
    public float melee_speed;
    public float meleeSecond_speed;
    public float fire_speed;
    public float water_speed;
    public float air_speed;
    public float ether_speed;
    public float earth_speed;
    public float special_speed;
}
```

**God Characteristics:**
| God | Primary Bonus | Special Ability |
|-----|---------------|-----------------|
| Brahma | +3 focus streak start | Shield Block/Attack |
| Vishnu | +30% movement speed | Speed buff ability |
| Shiva | +20% damage buff | Third Eye immunity |

### 9.3 Elemental/Spell System

**Elemental Encoding:**
```csharp
// Elemental byte = (elementType << 5) | spellType
// 3 bits for element (0-4), 5 bits for spell type (0-31)

public Elementals GetElemental()
{
    return (Elementals)((Value >> 5) & 0x7);
}

public int GetSpellType()
{
    return Value & 0x1F;
}
```

**Elements:**
```csharp
public enum Elementals
{
    FIRE  = 0,
    WATER = 1,
    AIR   = 2,
    ETHER = 3,
    EARTH = 4,
}
```

**Spell Damage Modes:**
```csharp
public enum SpellDamageMode
{
    BurstOnly,          // Single hit on cast
    ZoneOnly,           // Repeated zone ticks
    EffectOnly,         // DoT/status only
    BurstAndZone,       // Hit + zone
    BurstAndEffect,     // Hit + DoT
    ZoneAndEffect,      // Zone + DoT
    BurstZoneAndEffect, // All three
}
```

**Effect Types:**
```csharp
public enum EffectType
{
    EFFECT_NONE         = 0,
    EFFECT_FIREDAMAGE   = 1,  // Fire DoT
    EFFECT_AIRSLOW      = 2,  // Movement slow
    EFFECT_EARTHSTUN    = 3,  // Stun
    EFFECT_ETHERMUTE    = 4,  // Silence (can't cast)
    EFFECT_IMPAIR       = 5,  // Damage reduction
    EFFECT_MAIM         = 6,  // Attack speed slow
    EFFECT_THIRDEYE     = 7,  // Immunity
    EFFECT_SHIVAASTRA   = 8,  // Shiva ultimate burn
}
```

### 9.4 Character-Specific Data

#### 9.4.1 Amuktha (Close-Range Melee)
```csharp
public class AmukthaData : CharacterData
{
    public float MaxDashDistance;      // Dash ability range
    public float dashSpeed;            // Dash movement speed
}
```
**Special:** Dash attack

#### 9.4.2 MukthaMuktha (Axe Warrior)
```csharp
public enum AxeState
{
    ONHAND,     // Axe in hand
    THROWN,     // Axe in flight
    ONGROUND,   // Axe on ground
    RECALLING,  // Axe returning
}
```
**Special:** Axe throw and recall

#### 9.4.3 MantraMuktha (Ranged Mage)
**Special:** Teleport ability

#### 9.4.4 PaniMuktha (Discus Thrower)
**Special:** Discus with elliptical path

#### 9.4.5 YantraMuktha (Archer)
**Special:** Arrow with shockwave/impair

### 9.5 Animation Frame Data

**Location:** `Assets/Characters/{Name}/Resources/AnimationFrameData_{Name}.json`

```json
{
    "state": 1,                    // StateType enum value
    "animLength": [0.5, 0.3],      // Animation durations
    "transitionTime": [0.1, 0.1]   // Blend times
}
```

---

## 10. Complete Enums Reference

### 10.1 Game Enums

```csharp
// Fighting Styles (5)
public enum FightingStyles
{
    Amuktha       = 0,
    MantraMuktha  = 1,
    MukthaMuktha  = 2,
    PaniMuktha    = 3,
    YantraMuktha  = 4,
}

// Fighter Gender/Class
public enum FighterClass
{
    Male   = 0,
    Female = 1,
}

// Trinity Gods (3)
public enum TrinityGods
{
    Brahma = 0,
    Shiva  = 1,
    Vishnu = 2,
}

// Match Types (10)
public enum MatchType
{
    SOLO_1V1    = 1 << 0,   // 1
    SOLO_1V2    = 1 << 1,   // 2
    SOLO_1V5    = 1 << 2,   // 4
    DUO_2V2     = 1 << 3,   // 8
    DUO_2V4     = 1 << 4,   // 16
    TRIO_3V3    = 1 << 5,   // 32
    TRAINING    = 1 << 6,   // 64
    TUTORIAL    = 1 << 7,   // 128
    FIRST_MATCH = 1 << 8,   // 256
    NONE        = 1 << 9,   // 512
}

// Teams
public enum Teams
{
    None  = 0,
    Team1 = 1,
    Team2 = 2,
}
```

### 10.2 Combat Enums

```csharp
// Damage Types (12)
public enum DamageType
{
    NONE         = 0,
    MELEE        = 1,
    AXETHROW     = 2,
    THIRDEYE     = 3,
    FIRE         = 4,
    WATER        = 5,
    AIR          = 6,
    ETHER        = 7,
    EARTH        = 8,
    ASTRA_BRAHMA = 9,
    ASTRA_VISHNU = 10,
    ASTRA_SHIVA  = 11,
}

// Attack Types (11)
public enum AttackType
{
    ASTRA        = 0,
    ELEMENTAL1   = 1,
    ELEMENTAL2   = 2,
    ELEMENTAL3   = 3,
    ELEMENTAL4   = 4,
    THIRDEYE     = 5,
    UNIQUE       = 6,
    MELEE        = 7,
    BRAHMASHIELD = 8,
    DODGE        = 9,
    NONE         = 10,
}

// Weapon Types
public enum WeaponType
{
    Sword  = 0,
    Axe    = 1,
    Bow    = 2,
    Chakra = 3,
    Magic  = 4,
    None   = 5,
}

// Impact Types
public enum MeleeImpactType
{
    Force        = 0,
    Slice        = 1,
    Pierce       = 2,
    ForceAndSlice = 3,
}

// Impact Indicators
public enum ImpactIndicatorType
{
    BrahmaMelee  = 1,
    VishnuMelee  = 2,
    ShivaMelee   = 3,
    ShieldBlock  = 4,
    BrahmaAstra  = 5,
    ShivaAstra   = 6,
    VishnuAstra  = 7,
}
```

### 10.3 Status Enums

```csharp
// Slow Types
public enum SlowType
{
    NONE  = 0,  // No slow
    FIFTY = 1,  // 50% slow
    ZERO  = 2,  // Complete stop
}

// Willpower Buff Types
public enum WillPowerBuffType
{
    NONE   = 0,
    TWENTY = 1,
    FORTY  = 2,
    SIXTY  = 3,
    EIGHTY = 4,
    MAX    = 5,
}

// Karma Types
public enum Karma
{
    Sattva = 0,  // Good
    Rajas  = 1,  // Neutral
    Tamas  = 2,  // Bad
}
```

### 10.4 Spell Enums

```csharp
// Spell Sub-Types
public enum SpellSubType
{
    INSTANT    = 0,
    CHANNELING = 1,
    CHARGED    = 2,
    TRAPS      = 3,
}

// Range Types
public enum RangeType
{
    CLOSE_RANGE = 0,
    LONG_RANGE  = 1,
}

// Cast Detection Types
public enum CastDetectionType
{
    Circle = 0,
    Cone   = 1,
    Box    = 2,
}

// Element Interaction
public enum Interaction
{
    Nullify   = 0,  // Cancels out
    Vulnerable = 1, // Takes extra damage
    Mitigate  = 2,  // Reduced damage
}
```

### 10.5 Network Enums

```csharp
// Network Events
public enum NetworkEvent
{
    Connected    = 0,
    Disconnected = 1,
    Timeout      = 2,
}

// Socket States
public enum SocketState
{
    Disconnected = 0,
    Connecting   = 1,
    Connected    = 2,
    Disconnecting = 3,
}

// Login Status
public enum LoginStatus
{
    SESSION_EXPIRED  = 0,
    LOGIN_SUCCESSFUL = 1,
    ERROR            = 2,
}

// Currency Types
public enum currencyType
{
    Bronze = 0,
    Silver = 1,
    Gold   = 2,
}

// Server Regions
public enum ServerRegion
{
    Auto    = 0,
    NA_East = 1,
    NA_West = 2,
    EU      = 3,
    Asia    = 4,
}
```

### 10.6 UI/Game State Enums

```csharp
// Game States
public enum GameState
{
    Initiate = 0,
    MainMenu = 1,
    InGame   = 2,
}

// Camera States
public enum CameraStates
{
    Follow   = 0,
    Orbit    = 1,
    Fixed    = 2,
    Spectate = 3,
}

// Bot States
public enum BotState
{
    Idle      = 0,
    Attacking = 1,
    Defending = 2,
    Chasing   = 3,
    Fleeing   = 4,
}
```

---

## 11. Migration Guide

### 11.1 Adapting to Epic Online Services

**Transport Layer:**
```
LiteNetLib UDP → Epic P2P or Relay
- Keep packet structures identical
- Replace Socket.cs wrapper with EOS SDK calls
- Map EOS connection events to existing NetworkEvent enum
```

**Authentication:**
```
Firebase/PlayFab → Epic Account Services
- Replace AUMAuthManager with EOS Auth
- Map PlayFab IDs to EOS Product User IDs
- Keep avatar/loadout data structures
```

### 11.2 Adapting to Mirror/Netcode

**Transport Layer:**
```
LiteNetLib → Mirror Transport
- Create Mirror NetworkMessages from packet structs
- Use [ClientRpc]/[Command] attributes
- Map to existing state machine
```

### 11.3 Key Components to Keep

| Component | Reason |
|-----------|--------|
| Packet structures | Binary layout is transport-agnostic |
| State machines | Game logic, not transport-specific |
| Tick system | Server-authoritative design |
| Serializer | Marshal-based, works anywhere |
| Enums | Game constants, not network-specific |

### 11.4 Key Components to Replace

| Component | Replacement |
|-----------|-------------|
| LiteNetLib DLL | Target transport (EOS/Mirror) |
| WebSocket backend | Epic backend or custom |
| PlayFab services | Epic Game Services or custom |
| Firebase auth | Epic Account Services |

---

## Document Info

**Generated:** January 21, 2026
**Source Repositories:**
- `AUM-Unity-Staging-Legacy` (Client)
- `AUM-Unity-Server-Legacy` (Server)

**Total Lines:** ~2800
**Sections:** 11
**Packet Definitions:** 50+
**Enum Definitions:** 40+

---

*End of Protocol Documentation*
