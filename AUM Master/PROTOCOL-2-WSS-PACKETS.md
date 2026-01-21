# AUM Protocol - WebSocket Packets (Complete)

**Version:** 2.0 (Complete)
**Date:** January 21, 2026
**Source:** `Assets/Scripts/Network/WSS/SocketPacket.cs`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Packet Type IDs](#2-packet-type-ids)
3. [Common Structures](#3-common-structures)
4. [Login/Auth Packets](#4-loginauth-packets)
5. [Avatar Packets](#5-avatar-packets)
6. [Matchmaking Packets](#6-matchmaking-packets)
7. [Friends Packets](#7-friends-packets)
8. [Party Packets](#8-party-packets)
9. [Lobby Packets](#9-lobby-packets)
10. [Store/Currency Packets](#10-storecurrency-packets)
11. [Rewards Packets](#11-rewards-packets)
12. [Meditation Packets](#12-meditation-packets)
13. [Settings Packets](#13-settings-packets)
14. [Chat Packets](#14-chat-packets)
15. [Leaderboard Packets](#15-leaderboard-packets)

---

## 1. Overview

### 1.1 Packet Format

All WSS packets use `StructLayout.Sequential, Pack = 1`:

```
┌────────────────┬─────────────────────────────────────────┐
│  PacketType    │          Payload                        │
│   (2 bytes)    │         (variable)                      │
└────────────────┴─────────────────────────────────────────┘
```

### 1.2 Serialization Rules

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ExamplePacket
{
    public UInt16 packetType;                              // Always first

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = N)]
    public byte[] fixedByteArray;                          // Fixed-size byte array

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = N)]
    public string fixedString;                             // Fixed-size null-terminated string

    public byte singleByte;
    public UInt16 twoBytes;
    public UInt32 fourBytes;
    public float floatValue;
}
```

### 1.3 Total Struct Count: 83

| Category | Count |
|----------|-------|
| Login/Auth | 12 |
| Avatar | 8 |
| Matchmaking | 11 |
| Friends | 14 |
| Party | 10 |
| Lobby | 14 |
| Store/Currency | 7 |
| Rewards | 5 |
| Meditation | 4 |
| Settings | 2 |
| Chat | 2 |
| Leaderboard | 2 |
| Utility | 2 |

---

## 2. Packet Type IDs

### 2.1 Complete PacketType Enum

```csharp
public enum PacketType
{
    // ═══════════════════════════════════════════════════════════════
    // LOGIN/AUTH (0x1400-0x1506)
    // ═══════════════════════════════════════════════════════════════
    LOGIN_REQUEST               = 0x1400,  // Client → Server: Initial login
    TRY_LOGIN                   = 0x1401,  // Client → Server: Login attempt
    LOGIN_REPLY                 = 0x1402,  // Server → Client: Login response
    AVATARLIST_REQUEST          = 0x1403,  // Client → Server: Request avatars
    AVATARLIST_REPLY            = 0x1404,  // Server → Client: Avatar list
    CREATE_AVATAR_NEW_REQUEST   = 0x1405,  // Client → Server: Create avatar
    CREATE_AVATAR_NEW_REPLY     = 0x1406,  // Server → Client: Creation result
    AVATAR_NAME_VALIDATION_REQUEST = 0x1408, // Client → Server: Check name
    AVATAR_NAME_VALIDATION_REPLY   = 0x1409, // Server → Client: Name valid?
    LOGININFO_REQUEST           = 0x140A,  // Client → Server: Request info
    LOGININFO_REPLY             = 0x140B,  // Server → Client: Login info
    SOCIALINFO_REPLY            = 0x140C,  // Server → Client: Social info
    DELETE_AVATAR_REQUEST       = 0x1500,  // Client → Server: Delete avatar
    DELETE_AVATAR_REPLY         = 0x1501,  // Server → Client: Delete result
    CREATE_AVATAR_NEW_CONFIRM   = 0x1502,  // Server → Client: Confirm creation
    SET_AVATAR_ACTIVE           = 0x1503,  // Client → Server: Switch avatar
    CHANGE_ELEMENTAL_GOD        = 0x1504,  // Client → Server: Change loadout
    LOGOUT                      = 0x1505,  // Client → Server: Logout
    SET_AVATAR_RESPONSE         = 0x1506,  // Server → Client: Switch result

    // ═══════════════════════════════════════════════════════════════
    // MATCHMAKING (0x2000-0x2018)
    // ═══════════════════════════════════════════════════════════════
    MATCHMAKING_REQUEST         = 0x2000,  // Client → Server: Start/cancel queue
    MATCHMAKING_RESPONSE        = 0x2001,  // Server → Client: Queue status
    MATCHMAKING_DATA            = 0x2002,  // Server → Client: Match found data
    MATCHMAKING_READYSTATE      = 0x2003,  // Both: Ready check
    FCM_TOKEN                   = 0x2004,  // Client → Server: Push token
    INVENTORY_REPLY             = 0x2005,  // Server → Client: Inventory data
    SERVER_DATA                 = 0x2006,  // Server → Client: Game server IP/port
    CUSTOMIZATION_REQUEST       = 0x2007,  // Client → Server: Equip items
    MATCH_REWARDS               = 0x2008,  // Server → Client: Match rewards
    PLAYER_REWARDS_REQUEST      = 0x2009,  // Client → Server: Request currencies
    PLAYER_REWARDS_REPLY        = 0x2010,  // Server → Client: Currency data
    CONSUME_SHARD               = 0x2011,  // Client → Server: Use shard
    MEDITATION_STATE            = 0x2012,  // Both: Meditation state
    MEDITATION_COMPLETE_REQUEST = 0x2013,  // Client → Server: Complete meditation
    MEDITATION_BEGIN_REQUEST    = 0x2014,  // Client → Server: Start meditation
    GUEST_LOGIN                 = 0x2015,  // Client → Server: Guest login
    BOT_LOGIN                   = 0x2016,  // Internal: Bot login
    OAUTH_LOGIN                 = 0x2017,  // Client → Server: OAuth login
    FORFEIT_MATCH               = 0x2018,  // Client → Server: Forfeit

    // ═══════════════════════════════════════════════════════════════
    // LEADERBOARD (0x2050-0x2060)
    // ═══════════════════════════════════════════════════════════════
    LEADERBOARD_REQUEST         = 0x2050,  // Client → Server: Get leaderboard
    LEADERBOARD_REPLY           = 0x2051,  // Server → Client: Leaderboard data
    USERSETTINGS                = 0x2060,  // Both: User settings

    // ═══════════════════════════════════════════════════════════════
    // FRIENDS (0x2071-0x2111)
    // ═══════════════════════════════════════════════════════════════
    FRIENDS_DATA_RESPONSE       = 0x2071,  // Server → Client: Friends list
    FRIENDS_SEARCH_REQUEST      = 0x2072,  // Client → Server: Search friend
    FRIENDS_SEARCH_RESPONSE     = 0x2073,  // Server → Client: Search result
    FRIEND_REQUEST              = 0x2077,  // Client → Server: Send request
    FRIEND_REQUEST_RESPONSE     = 0x2079,  // Client → Server: Accept/decline
    FRIENDS_DATA_REQUEST        = 0x2090,  // Client → Server: Get friends
    REMOVE_FRIEND               = 0x2091,  // Client → Server: Remove friend
    TOGGLE_FAVOURITE            = 0x2092,  // Client → Server: Toggle favorite
    FRIEND_EVENT                = 0x2093,  // Server → Client: Friend status change
    UPDATE_PROFILE              = 0x2098,  // Client → Server: Update profile
    CHECK_FRIEND                = 0x2102,  // Client → Server: Check if friend
    FRIEND_APPEND               = 0x2107,  // Server → Client: Friend added
    FRIEND_REMOVED              = 0x2108,  // Server → Client: Friend removed
    FRIENDREQUEST_PROCESSED     = 0x2110,  // Server → Client: Request processed
    FRIEND_TOGGLE_FAV           = 0x2111,  // Server → Client: Favorite toggled

    // ═══════════════════════════════════════════════════════════════
    // PARTY (0x2114-0x2125)
    // ═══════════════════════════════════════════════════════════════
    PARTY_INVITE_REQUEST        = 0x2114,  // Client → Server: Invite to party
    PARTY_INVITE_RECEIVED       = 0x2115,  // Server → Client: Invite received
    PARTY_INVITE_REPLY          = 0x2116,  // Client → Server: Accept/decline
    PARTY_INVITE_RESPONSE       = 0x2117,  // Server → Client: Response result
    PARTY_INVITE_CANCEL         = 0x2118,  // Client → Server: Cancel invite
    PARTY_DATA_PACKET           = 0x2119,  // Server → Client: Party data
    PARTY_READY                 = 0x2120,  // Client → Server: Toggle ready
    PARTY_READY_RESPONSE        = 0x2121,  // Server → Client: Ready status
    PARTY_MAKE_LEADER           = 0x2122,  // Client → Server: Transfer leader
    PARTY_KICKOUT_PLAYER        = 0x2123,  // Client → Server: Kick player
    LEAVE_PARTY                 = 0x2124,  // Client → Server: Leave party
    PARTY_PLAYER_LEFT           = 0x2125,  // Server → Client: Player left

    // ═══════════════════════════════════════════════════════════════
    // LOBBY (0x2128-0x2147)
    // ═══════════════════════════════════════════════════════════════
    LOBBY_CREATE_REQUEST        = 0x2128,  // Client → Server: Create lobby
    LOBBY_DATA_PACKET           = 0x2129,  // Server → Client: Lobby data
    LOBBY_LIST_REQUEST          = 0x2130,  // Client → Server: List lobbies
    LOBBY_LIST_RESPONSE         = 0x2131,  // Server → Client: Lobby list
    LOBBY_INVITE_REQUEST        = 0x2132,  // Client → Server: Invite to lobby
    LOBBY_INVITE_RECEIVED       = 0x2133,  // Server → Client: Invite received
    LOBBY_JOIN_REQUEST          = 0x2137,  // Client → Server: Join lobby
    LOBBY_JOIN_RESPONSE         = 0x2138,  // Server → Client: Join result
    LOBBY_JOIN_INVITE           = 0x2139,  // Client → Server: Join via invite
    LOBBY_READY                 = 0x2140,  // Client → Server: Toggle ready
    LOBBY_KICKOUT_PLAYER        = 0x2142,  // Client → Server: Kick player
    LOBBY_LEAVE                 = 0x2143,  // Client → Server: Leave lobby
    LOBBY_PLAYER_SLOT_UPDATE    = 0x2144,  // Both: Slot change
    PARTY_LOBBY_DATA            = 0x2145,  // Server → Client: Party in lobby
    TOGGLE_LOBBY_BOTS           = 0x2146,  // Client → Server: Toggle bots
    LOBBY_RESPONSE              = 0x2147,  // Server → Client: Generic response

    // ═══════════════════════════════════════════════════════════════
    // STORE/REWARDS (0x2080-0x2106)
    // ═══════════════════════════════════════════════════════════════
    STORE_INFO                  = 0x2080,  // Server → Client: Store catalog
    DAILY_REWARDS               = 0x2081,  // Server → Client: Daily rewards
    DAILY_REWARDS_CLAIM         = 0x2082,  // Client → Server: Claim reward
    MATCH_DATA                  = 0x2101,  // Server → Client: Match stats
    REQUEST_STORE_INFO          = 0x2103,  // Client → Server: Get store
    REQUEST_PURCHASE            = 0x2104,  // Client → Server: Purchase item
    PURCHASE_COMPLETE           = 0x2106,  // Server → Client: Purchase result
    CURRENCY_CONVERSION         = 0x2100,  // Client → Server: Convert currency

    // ═══════════════════════════════════════════════════════════════
    // CHAT/FEEDBACK (0x2150-0x2152)
    // ═══════════════════════════════════════════════════════════════
    CHAT_MESSAGE                = 0x2150,  // Both: Chat message
    FEEDBACK_FORM_REQUEST       = 0x2151,  // Client → Server: Request form
    FEEDBACK_FORM_SUBMIT        = 0x2152,  // Client → Server: Submit feedback
}
```

---

## 3. Common Structures

### 3.1 DeviceInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct DeviceInfo
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 36)]
    public string deviceUniqueID;    // Offset: 0, Size: 36 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 36)]
    public string deviceModel;       // Offset: 36, Size: 36 bytes

    public UInt16 deviceType;        // Offset: 72, Size: 2 bytes
}
// Total Size: 74 bytes

// deviceType values:
// 0 = Unknown
// 1 = Android
// 2 = iOS
// 3 = PC/Editor
```

### 3.2 Version_Info

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Version_Info
{
    public UInt16 major;             // Offset: 0, Size: 2 bytes
    public UInt16 minor;             // Offset: 2, Size: 2 bytes
    public UInt16 build;             // Offset: 4, Size: 2 bytes
}
// Total Size: 6 bytes
```

### 3.3 ItemInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ItemInfo
{
    public UInt32 ItemCode;          // Offset: 0, Size: 4 bytes
                                     // Item type encoded in code

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] ItemUUID;          // Offset: 4, Size: 16 bytes
                                     // Unique item instance ID
}
// Total Size: 20 bytes
```

### 3.4 ItemInfo_New

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ItemInfo_New
{
    public UInt32 ItemCode;          // Offset: 0, Size: 4 bytes

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] ItemUUID;          // Offset: 4, Size: 16 bytes

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] activeAvatar;      // Offset: 20, Size: 16 bytes
                                     // Avatar this item belongs to

    public byte IsNewItem;           // Offset: 36, Size: 1 byte
                                     // 1 = newly acquired
}
// Total Size: 37 bytes
```

### 3.5 ItemUUIDInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ItemUUIDInfo
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] ItemUUID;          // Offset: 0, Size: 16 bytes
}
// Total Size: 16 bytes
```

### 3.6 PacketWithOnlyType

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PacketWithOnlyType
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
}
// Total Size: 2 bytes
// Used for requests that need no additional data
```

---

## 4. Login/Auth Packets

### 4.1 LoginData (LOGIN_REQUEST - 0x1400)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LoginData
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1400

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string userName;          // Offset: 2, Size: 13 bytes
                                     // User login name

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string password;          // Offset: 15, Size: 13 bytes
                                     // User password (hashed)

    public byte sessionActive;       // Offset: 28, Size: 1 byte
                                     // 1 = has existing session

    public DeviceInfo deviceInfo;    // Offset: 29, Size: 74 bytes
                                     // Device information

    public Version_Info versionInfo; // Offset: 103, Size: 6 bytes
                                     // Client version
}
// Total Size: 109 bytes
```

### 4.2 SessionID (LOGIN_REPLY - 0x1402)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SessionID
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1402

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionUUID;       // Offset: 2, Size: 16 bytes
                                     // Assigned session UUID

    public byte sessionActive;       // Offset: 18, Size: 1 byte
                                     // LoginStatus enum

    public Version_Info versionInfo; // Offset: 19, Size: 6 bytes
                                     // Server version
}
// Total Size: 25 bytes
```

### 4.3 GuestLogin_Request (GUEST_LOGIN - 0x2015)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct GuestLogin_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2015

    public DeviceInfo deviceInfo;    // Offset: 2, Size: 74 bytes
                                     // Device information

    public Version_Info versionInfo; // Offset: 76, Size: 6 bytes
                                     // Client version
}
// Total Size: 82 bytes
```

### 4.4 OAuthLogin_Request (OAUTH_LOGIN - 0x2017)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct OAuthLogin_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2017

    public DeviceInfo deviceInfo;    // Offset: 2, Size: 74 bytes
                                     // Device information

    public Version_Info versionInfo; // Offset: 76, Size: 6 bytes
                                     // Client version
}
// Total Size: 82 bytes
// Note: OAuth token sent separately or in extended payload
```

### 4.5 LoginInfo_Request (LOGININFO_REQUEST - 0x140A)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LoginInfo_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x140A
}
// Total Size: 2 bytes
```

### 4.6 LoginInfo_Reply (LOGININFO_REPLY - 0x140B)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LoginInfo_Reply
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x140B
}
// Total Size: 2 bytes
// Note: Extended data follows in message payload
```

### 4.7 SocialInfo (SOCIALINFO_REPLY - 0x140C)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SocialInfo
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x140C

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Player's friend code

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 11, Size: 13 bytes
                                     // Display name

    public byte profileImageID;      // Offset: 24, Size: 1 byte
                                     // Profile picture index
}
// Total Size: 25 bytes
```

### 4.8 Logout (LOGOUT - 0x1505)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Logout
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1505

    public byte LogoutType;          // Offset: 2, Size: 1 byte
                                     // 0 = Normal, 1 = Forced, 2 = Timeout
}
// Total Size: 3 bytes
```

---

## 5. Avatar Packets

### 5.1 AvatarList (AVATARLIST_REPLY - 0x1404)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct AvatarList
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1404

    public byte avatarCount;         // Offset: 2, Size: 1 byte
                                     // Number of avatars (0-5)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public Avatar_Info[] avatarInfo; // Offset: 3, Size: 5 * sizeof(Avatar_Info)
                                     // Up to 5 avatars
}
// Total Size: 3 + (5 * Avatar_Info size)
```

### 5.2 Avatar_Info

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Avatar_Info
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Context-dependent

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] uniqueID;          // Offset: 2, Size: 16 bytes
                                     // Avatar UUID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;          // Offset: 18, Size: 13 bytes
                                     // Display name (max 12 chars)

    public byte fightingStyle;       // Offset: 31, Size: 1 byte
                                     // FightingStyles enum (0-4)

    public byte fighterClass;        // Offset: 32, Size: 1 byte
                                     // FighterClass enum (0=Male, 1=Female)

    public byte godSelected;         // Offset: 33, Size: 1 byte
                                     // TrinityGods enum (0-2)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected; // Offset: 34, Size: 4 bytes
                                     // 4 equipped elemental spells

    public byte weaponVariant;       // Offset: 38, Size: 1 byte
                                     // Weapon skin variant

    public byte lastActive;          // Offset: 39, Size: 1 byte
                                     // 1 = most recently used

    public byte isCompleted;         // Offset: 40, Size: 1 byte
                                     // 1 = tutorial completed

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public ItemInfo[] wearItems;     // Offset: 41, Size: 6 * 20 = 120 bytes
                                     // 6 equipped cosmetic items
}
// Total Size: 161 bytes
```

### 5.3 Avatar_Name (NAME_VALIDATION - 0x1408/0x1409)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Avatar_Name
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // 0x1408 (request) or 0x1409 (reply)

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;          // Offset: 2, Size: 13 bytes
                                     // Name to validate

    public bool isValid;             // Offset: 15, Size: 1 byte
                                     // 1 = name is available (reply only)
}
// Total Size: 16 bytes
```

### 5.4 Avatar_Delete (DELETE_AVATAR_REQUEST - 0x1500)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Avatar_Delete
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1500

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] uniqueID;          // Offset: 2, Size: 16 bytes
                                     // Avatar to delete
}
// Total Size: 18 bytes
```

### 5.5 Avatar_ID (SET_AVATAR_ACTIVE - 0x1503)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Avatar_ID
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1503

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] uniqueID;          // Offset: 2, Size: 16 bytes
                                     // Avatar to activate
}
// Total Size: 18 bytes
```

### 5.6 Avatar_Switch_Response (SET_AVATAR_RESPONSE - 0x1506)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Avatar_Switch_Response
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1506

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] uniqueID;          // Offset: 2, Size: 16 bytes
                                     // Affected avatar

    public byte IsDelete;            // Offset: 18, Size: 1 byte
                                     // 1 = was delete operation
}
// Total Size: 19 bytes
```

### 5.7 Elemental_God_Info (CHANGE_ELEMENTAL_GOD - 0x1504)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Elemental_God_Info
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x1504

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] uniqueID;          // Offset: 2, Size: 16 bytes
                                     // Avatar to update

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected; // Offset: 18, Size: 4 bytes
                                     // New elemental loadout

    public byte godSelected;         // Offset: 22, Size: 1 byte
                                     // New god selection
}
// Total Size: 23 bytes
```

### 5.8 CustomizeAvatar (CUSTOMIZATION_REQUEST - 0x2007)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct CustomizeAvatar
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2007

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public ItemUUIDInfo[] ItemUUID;  // Offset: 2, Size: 6 * 16 = 96 bytes
                                     // 6 items to equip
}
// Total Size: 98 bytes
```

---

## 6. Matchmaking Packets

### 6.1 Matchmaking_Request (MATCHMAKING_REQUEST - 0x2000)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Matchmaking_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2000

    public byte matchType;           // Offset: 2, Size: 1 byte
                                     // MatchType enum (bit flags)

    public byte state;               // Offset: 3, Size: 1 byte
                                     // 0 = Cancel, 1 = Start
}
// Total Size: 4 bytes
```

### 6.2 Matchmaking_Response (MATCHMAKING_RESPONSE - 0x2001)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Matchmaking_Response
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2001

    public UInt32 elapsedTime;       // Offset: 2, Size: 4 bytes
                                     // Seconds in queue

    public byte state;               // Offset: 6, Size: 1 byte
                                     // 0 = Searching
                                     // 1 = Match Found
                                     // 2 = Cancelled
}
// Total Size: 7 bytes
```

### 6.3 Matchmaking_Respond_Request (MATCHMAKING_READYSTATE - 0x2003)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Matchmaking_Respond_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2003

    public byte confirmState;        // Offset: 2, Size: 1 byte
                                     // 0 = Decline, 1 = Accept
}
// Total Size: 3 bytes
```

### 6.4 Match_Avatar

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Avatar
{
    public UInt32 uniqueID;          // Offset: 0, Size: 4 bytes
                                     // In-match player ID (not avatar UUID)

    public byte teamID;              // Offset: 4, Size: 1 byte
                                     // Team number (1 or 2)

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;          // Offset: 5, Size: 13 bytes
                                     // Display name

    public byte fightingStyle;       // Offset: 18, Size: 1 byte
                                     // FightingStyles enum

    public byte fighterClass;        // Offset: 19, Size: 1 byte
                                     // FighterClass enum

    public byte godSelected;         // Offset: 20, Size: 1 byte
                                     // TrinityGods enum

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected; // Offset: 21, Size: 4 bytes
                                     // Equipped elementals

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public UInt32[] wearItems;       // Offset: 25, Size: 24 bytes
                                     // Equipped item codes

    public byte weaponVariant;       // Offset: 49, Size: 1 byte
                                     // Weapon skin

    public UInt32 bronze;            // Offset: 50, Size: 4 bytes
                                     // Bronze currency

    public UInt16 lives;             // Offset: 54, Size: 2 bytes
                                     // Current lives

    public byte guna;                // Offset: 56, Size: 1 byte
                                     // Karma guna state
}
// Total Size: 57 bytes
```

### 6.5 Match_Confirm (MATCHMAKING_DATA - 0x2002)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Confirm
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2002

    public byte confirmState;        // Offset: 2, Size: 1 byte
                                     // Match confirmation state

    public byte matchType;           // Offset: 3, Size: 1 byte
                                     // MatchType enum

    public byte team;                // Offset: 4, Size: 1 byte
                                     // Player's assigned team

    public UInt32 uniqueID;          // Offset: 5, Size: 4 bytes
                                     // Player's match ID

    public byte avatarCount;         // Offset: 9, Size: 1 byte
                                     // Number of players

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public Match_Avatar[] avatarInfo;// Offset: 10, Size: 6 * 57 = 342 bytes
                                     // All players in match
}
// Total Size: 352 bytes
```

### 6.6 Match_ReadyState (MATCHMAKING_READYSTATE - 0x2003)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_ReadyState
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2003

    public byte matchDecline;        // Offset: 2, Size: 1 byte
                                     // Number of declines

    public byte readyPlayers;        // Offset: 3, Size: 1 byte
                                     // Players who accepted

    public byte totalPlayers;        // Offset: 4, Size: 1 byte
                                     // Total players in match
}
// Total Size: 5 bytes
```

### 6.7 Match_Server_Data (SERVER_DATA - 0x2006)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Server_Data
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2006

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string ipAddr;            // Offset: 2, Size: 16 bytes
                                     // Game server IP address

    public UInt16 ipPort;            // Offset: 18, Size: 2 bytes
                                     // Game server UDP port
}
// Total Size: 20 bytes
```

### 6.8 Match_Forfeit (FORFEIT_MATCH - 0x2018)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Match_Forfeit
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2018

    public byte forfeitReason;       // Offset: 2, Size: 1 byte
                                     // 0 = Quit, 1 = AFK, 2 = Disconnect
}
// Total Size: 3 bytes
```

### 6.9 FCM_Token (FCM_TOKEN - 0x2004)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FCM_Token
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2004

    public UInt16 tokenSize;         // Offset: 2, Size: 2 bytes
                                     // Size of FCM token
                                     // Token follows in payload
}
// Total Size: 4 bytes + tokenSize
```

### 6.10 InventoryInfo (INVENTORY_REPLY - 0x2005)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct InventoryInfo
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2005

    public UInt16 itemCount;         // Offset: 2, Size: 2 bytes
                                     // Number of items
                                     // ItemInfo_New[] follows
}
// Total Size: 4 bytes + (itemCount * 37)
```

### 6.11 Find_Match (Internal)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Find_Match
{
    public byte matchMode;           // Offset: 0, Size: 1 byte
                                     // MatchType enum
}
// Total Size: 1 byte
// Internal structure, not a packet
```

---

## 7. Friends Packets

### 7.1 Friends_Data (FRIENDS_DATA_RESPONSE - 0x2071)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friends_Data
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2071

    public UInt16 totalFriendsCount; // Offset: 2, Size: 2 bytes
                                     // Number of friends
                                     // Friend_Info[] follows
}
// Total Size: 4 bytes + (count * sizeof(Friend_Info))
```

### 7.2 Friend_Info

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friend_Info
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 0, Size: 9 bytes
                                     // Friend's unique ID code

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 9, Size: 13 bytes
                                     // Friend's display name

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string avatarName;        // Offset: 22, Size: 13 bytes
                                     // Friend's avatar name

    public byte fightingStyle;       // Offset: 35, Size: 1 byte
                                     // FightingStyles enum

    public byte gameState;           // Offset: 36, Size: 1 byte
                                     // 0=MainMenu, 1=Party, 2=Lobby, 3=InGame

    public byte isFav;               // Offset: 37, Size: 1 byte
                                     // 1 = favorited

    public byte isPending;           // Offset: 38, Size: 1 byte
                                     // 1 = request pending

    public byte isOnline;            // Offset: 39, Size: 1 byte
                                     // 1 = currently online

    public byte isSourcePlayer;      // Offset: 40, Size: 1 byte
                                     // 1 = we sent the request

    public byte profileImageIndex;   // Offset: 41, Size: 1 byte
                                     // Profile picture index
}
// Total Size: 42 bytes
```

### 7.3 FriendRequest_Info

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendRequest_Info
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 0, Size: 9 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 9, Size: 13 bytes

    public byte profileImageIndex;   // Offset: 22, Size: 1 byte
}
// Total Size: 23 bytes
```

### 7.4 FriendSearch_Request (FRIENDS_SEARCH_REQUEST - 0x2072)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendSearch_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2072

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Friend ID to search
}
// Total Size: 11 bytes
```

### 7.5 FriendSearch_Reply (FRIENDS_SEARCH_RESPONSE - 0x2073)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendSearch_Reply
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2073

    public byte isValid;             // Offset: 2, Size: 1 byte
                                     // 1 = user found

    public byte isFriend;            // Offset: 3, Size: 1 byte
                                     // 1 = already friends

    public byte isPending;           // Offset: 4, Size: 1 byte
                                     // 1 = request pending

    public byte isTargetPlayer;      // Offset: 5, Size: 1 byte
                                     // 1 = they sent us a request

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 6, Size: 9 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 15, Size: 13 bytes

    public byte profileImageIndex;   // Offset: 28, Size: 1 byte
}
// Total Size: 29 bytes
```

### 7.6 Friend_Request (FRIEND_REQUEST - 0x2077)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friend_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2077

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Target friend ID
}
// Total Size: 11 bytes
```

### 7.7 FriendRequest_Response (FRIEND_REQUEST_RESPONSE - 0x2079)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendRequest_Response
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2079

    public byte isAccepted;          // Offset: 2, Size: 1 byte
                                     // 0 = Decline, 1 = Accept

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 3, Size: 9 bytes
}
// Total Size: 12 bytes
```

### 7.8 Remove_Friend (REMOVE_FRIEND - 0x2091)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Remove_Friend
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2091

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
}
// Total Size: 11 bytes
```

### 7.9 Toggle_Favourite (TOGGLE_FAVOURITE - 0x2092)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Toggle_Favourite
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2092

    public byte isFavourite;         // Offset: 2, Size: 1 byte
                                     // New favorite state

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 3, Size: 9 bytes
}
// Total Size: 12 bytes
```

### 7.10 Friend_Event (FRIEND_EVENT - 0x2093)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friend_Event
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2093

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string avatarName;        // Offset: 2, Size: 13 bytes

    public byte fightingStyle;       // Offset: 15, Size: 1 byte

    public byte profileImageIndex;   // Offset: 16, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 17, Size: 13 bytes

    public byte gameState;           // Offset: 30, Size: 1 byte
                                     // 0=MainMenu, 1=Party, 2=Lobby, 3=InGame

    public byte isOnline;            // Offset: 31, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 32, Size: 9 bytes
}
// Total Size: 41 bytes
```

### 7.11 Friend_Modify_Event (FRIEND_APPEND/REMOVED - 0x2107/0x2108)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Friend_Modify_Event
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // 0x2107 (added) or 0x2108 (removed)

    public byte profileImageIndex;   // Offset: 2, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 3, Size: 13 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 16, Size: 9 bytes

    public byte IsPending;           // Offset: 25, Size: 1 byte

    public byte IsSourcePlayer;      // Offset: 26, Size: 1 byte
}
// Total Size: 27 bytes
```

### 7.12 UpdateProfile (UPDATE_PROFILE - 0x2098)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct UpdateProfile
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2098

    public byte imageId;             // Offset: 2, Size: 1 byte
                                     // New profile image

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 3, Size: 13 bytes
                                     // New profile name
}
// Total Size: 16 bytes
```

### 7.13 FriendFavToggleResponse (FRIEND_TOGGLE_FAV - 0x2111)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct FriendFavToggleResponse
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2111

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes

    public byte isFav;               // Offset: 11, Size: 1 byte
                                     // New favorite state
}
// Total Size: 12 bytes
```

---

## 8. Party Packets

### 8.1 PartyInviteRequest (PARTY_INVITE_REQUEST - 0x2114)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyInviteRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2114

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Friend to invite
}
// Total Size: 11 bytes
```

### 8.2 PartyInviteReceived (PARTY_INVITE_RECEIVED - 0x2115)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyInviteReceived
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2115

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Inviter's friend ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 11, Size: 13 bytes
                                     // Inviter's name

    public byte profileImageID;      // Offset: 24, Size: 1 byte
}
// Total Size: 25 bytes
```

### 8.3 PartyInviteReply (PARTY_INVITE_REPLY - 0x2116)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyInviteReply
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2116

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes

    public byte isAccepted;          // Offset: 11, Size: 1 byte
                                     // 0 = Decline, 1 = Accept
}
// Total Size: 12 bytes
```

### 8.4 PartyPlayers

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyPlayers
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 0, Size: 9 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 9, Size: 13 bytes

    public byte fightingStyle;       // Offset: 22, Size: 1 byte

    public byte godSelected;         // Offset: 23, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected; // Offset: 24, Size: 4 bytes

    public byte isHost;              // Offset: 28, Size: 1 byte
                                     // 1 = party leader

    public byte isReady;             // Offset: 29, Size: 1 byte
                                     // 1 = ready for match
}
// Total Size: 30 bytes
```

### 8.5 PartyDataPacket (PARTY_DATA_PACKET - 0x2119)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyDataPacket
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2119

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] partyId;           // Offset: 2, Size: 16 bytes
                                     // Party UUID

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 3)]
    public PartyPlayers[] partyPlayers; // Offset: 18, Size: 3 * 30 = 90 bytes
                                     // Up to 3 party members
}
// Total Size: 108 bytes
```

### 8.6 PartyReady (PARTY_READY - 0x2120)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyReady
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2120

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes

    public byte isReady;             // Offset: 11, Size: 1 byte
}
// Total Size: 12 bytes
```

### 8.7 PartyReadyResponse (PARTY_READY_RESPONSE - 0x2121)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyReadyResponse
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2121

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes

    public byte isReady;             // Offset: 11, Size: 1 byte
}
// Total Size: 12 bytes
```

### 8.8 PartyMakeLeaderRequest (PARTY_MAKE_LEADER - 0x2122)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyMakeLeaderRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2122

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // New leader
}
// Total Size: 11 bytes
```

### 8.9 PartyKickOutPlayerRequest (PARTY_KICKOUT_PLAYER - 0x2123)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyKickOutPlayerRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2123

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Player to kick
}
// Total Size: 11 bytes
```

### 8.10 PartyLeaveRequest (LEAVE_PARTY - 0x2124)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyLeaveRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2124

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string friendId;          // Offset: 2, Size: 16 bytes
                                     // Player leaving (self)
}
// Total Size: 18 bytes
```

### 8.11 PartyPlayerLeft (PARTY_PLAYER_LEFT - 0x2125)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PartyPlayerLeft
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2125

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Player who left
}
// Total Size: 11 bytes
```

---

## 9. Lobby Packets

### 9.1 LobbyInfo (Internal Structure)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyInfo
{
    public UInt32 lobbyID;           // Offset: 0, Size: 4 bytes
                                     // Unique lobby ID

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string hostName;          // Offset: 4, Size: 16 bytes
                                     // Host display name

    public byte loka;                // Offset: 20, Size: 1 byte
                                     // Map selection

    public byte playerCount;         // Offset: 21, Size: 1 byte
                                     // Current players

    public byte maxPlayers;          // Offset: 22, Size: 1 byte
                                     // Max players

    public byte matchMode;           // Offset: 23, Size: 1 byte
                                     // MatchType

    public byte isPublic;            // Offset: 24, Size: 1 byte
                                     // 1 = public lobby

    public byte allowBots;           // Offset: 25, Size: 1 byte
                                     // 1 = bots allowed

    public byte region;              // Offset: 26, Size: 1 byte
                                     // ServerRegion enum
}
// Total Size: 27 bytes
```

### 9.2 LobbyCreateRequest (LOBBY_CREATE_REQUEST - 0x2128)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyCreateRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2128

    public byte matchMode;           // Offset: 2, Size: 1 byte
                                     // 0=1v1, 1=1v2, 2=1v5, 3=2v2, 4=2v4, 5=3v3

    public byte loka;                // Offset: 3, Size: 1 byte
                                     // Map type

    public byte isPublic;            // Offset: 4, Size: 1 byte
                                     // 0=Public, 1=Private

    public byte allowBots;           // Offset: 5, Size: 1 byte

    public byte region;              // Offset: 6, Size: 1 byte
                                     // ServerRegion enum

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string password;          // Offset: 7, Size: 16 bytes
                                     // For private lobbies
}
// Total Size: 23 bytes
```

### 9.3 LobbyList (LOBBY_LIST_RESPONSE - 0x2131)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyList
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2131

    public byte lobbyCount;          // Offset: 2, Size: 1 byte
                                     // Number of lobbies
                                     // LobbyInfo[] follows
}
// Total Size: 3 bytes + (count * 27)
```

### 9.4 LobbyPlayerInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyPlayerInfo
{
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendID;          // Offset: 0, Size: 9 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string profileName;       // Offset: 9, Size: 16 bytes

    public byte profileImageID;      // Offset: 25, Size: 1 byte

    public byte positionIndex;       // Offset: 26, Size: 1 byte
                                     // Slot 0-5

    public byte isReady;             // Offset: 27, Size: 1 byte

    public byte isHost;              // Offset: 28, Size: 1 byte

    public byte isMicOn;             // Offset: 29, Size: 1 byte
                                     // Voice chat enabled

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected; // Offset: 30, Size: 4 bytes

    public byte fightingStyle;       // Offset: 34, Size: 1 byte

    public byte godSelected;         // Offset: 35, Size: 1 byte
}
// Total Size: 36 bytes
```

### 9.5 LobbyDataPacket (LOBBY_DATA_PACKET - 0x2129)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyDataPacket
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2129

    public UInt32 lobbyID;           // Offset: 2, Size: 4 bytes

    public byte matchMode;           // Offset: 6, Size: 1 byte

    public byte loka;                // Offset: 7, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string hostName;          // Offset: 8, Size: 16 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string hostFriendID;      // Offset: 24, Size: 9 bytes

    public byte isPublic;            // Offset: 33, Size: 1 byte

    public byte allowBots;           // Offset: 34, Size: 1 byte

    public byte region;              // Offset: 35, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public LobbyPlayerInfo[] playersInfo; // Offset: 36, Size: 6 * 36 = 216 bytes

    public byte playerCount;         // Offset: 252, Size: 1 byte

    public byte maxPlayers;          // Offset: 253, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string password;          // Offset: 254, Size: 16 bytes
}
// Total Size: 270 bytes
```

### 9.6 LobbyInviteRequest (LOBBY_INVITE_REQUEST - 0x2132)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyInviteRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2132

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendID;          // Offset: 2, Size: 9 bytes
}
// Total Size: 11 bytes
```

### 9.7 LobbyInviteReceived (LOBBY_INVITE_RECEIVED - 0x2133)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyInviteReceived
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2133

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendID;          // Offset: 2, Size: 9 bytes

    public UInt32 lobbyId;           // Offset: 11, Size: 4 bytes
}
// Total Size: 15 bytes
```

### 9.8 JoinLobbyRequest (LOBBY_JOIN_REQUEST - 0x2137)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct JoinLobbyRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2137

    public UInt32 lobbyID;           // Offset: 2, Size: 4 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 16)]
    public string password;          // Offset: 6, Size: 16 bytes
}
// Total Size: 22 bytes
```

### 9.9 JoinLobbyInvite (LOBBY_JOIN_INVITE - 0x2139)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct JoinLobbyInvite
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2139

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Host's friend ID
}
// Total Size: 11 bytes
```

### 9.10 JoinLobbyResponse (LOBBY_JOIN_RESPONSE - 0x2138)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct JoinLobbyResponse
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2138

    public byte isJoined;            // Offset: 2, Size: 1 byte
                                     // 1 = successfully joined
}
// Total Size: 3 bytes
```

### 9.11 LobbyReady (LOBBY_READY - 0x2140)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyReady
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2140

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes

    public byte isReady;             // Offset: 11, Size: 1 byte
}
// Total Size: 12 bytes
```

### 9.12 LobbyKickOutPlayerRequest (LOBBY_KICKOUT_PLAYER - 0x2142)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyKickOutPlayerRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2142

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
}
// Total Size: 11 bytes
```

### 9.13 LobbyPlayerLeft (LOBBY_LEAVE - 0x2143)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyPlayerLeft
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2143

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
}
// Total Size: 11 bytes
```

### 9.14 LobbyPlayerSlotUpdate (LOBBY_PLAYER_SLOT_UPDATE - 0x2144)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyPlayerSlotUpdate
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2144

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes

    public int slotIndex;            // Offset: 11, Size: 4 bytes
                                     // New slot (0-5)
}
// Total Size: 15 bytes
```

### 9.15 ToggleLobbyBots (TOGGLE_LOBBY_BOTS - 0x2146)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ToggleLobbyBots
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2146

    public byte allowBots;           // Offset: 2, Size: 1 byte
}
// Total Size: 3 bytes
```

### 9.16 LobbyResponse (LOBBY_RESPONSE - 0x2147)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LobbyResponse
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2147

    public byte status;              // Offset: 2, Size: 1 byte
                                     // Generic status code
}
// Total Size: 3 bytes
```

---

## 10. Store/Currency Packets

### 10.1 StoreInfo (STORE_INFO - 0x2080)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct StoreInfo
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2080

    public UInt16 itemCount;         // Offset: 2, Size: 2 bytes
                                     // Number of store items
                                     // StoreItemInfo[] follows
}
// Total Size: 4 bytes + (count * sizeof(StoreItemInfo))
```

### 10.2 StoreItemInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct StoreItemInfo
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] itemUUID;          // Offset: 0, Size: 16 bytes

    public UInt32 itemCode;          // Offset: 16, Size: 4 bytes
                                     // Item type/code

    public byte currency;            // Offset: 20, Size: 1 byte
                                     // currencyType enum

    public UInt32 price;             // Offset: 21, Size: 4 bytes

    public byte IsFeatured;          // Offset: 25, Size: 1 byte
                                     // 1 = featured item
}
// Total Size: 26 bytes
```

### 10.3 PurchaseRequest (REQUEST_PURCHASE - 0x2104)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PurchaseRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2104

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] itemUUID;          // Offset: 2, Size: 16 bytes
}
// Total Size: 18 bytes
```

### 10.4 PurchaseComplete (PURCHASE_COMPLETE - 0x2106)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PurchaseComplete
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2106

    public byte isSuccess;           // Offset: 2, Size: 1 byte

    public byte itemType;            // Offset: 3, Size: 1 byte
                                     // 0=item, 1=currency

    public UInt32 Bronze;            // Offset: 4, Size: 4 bytes
                                     // New bronze balance

    public UInt32 Silver;            // Offset: 8, Size: 4 bytes
                                     // New silver balance

    public UInt32 Gold;              // Offset: 12, Size: 4 bytes
                                     // New gold balance
}
// Total Size: 16 bytes
```

### 10.5 CurrencyConversionPacket (CURRENCY_CONVERSION - 0x2100)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct CurrencyConversionPacket
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2100

    public UInt32 amount;            // Offset: 2, Size: 4 bytes
                                     // Amount to convert

    public byte fromCurrency;        // Offset: 6, Size: 1 byte
                                     // currencyType enum

    public byte toCurrency;          // Offset: 7, Size: 1 byte
                                     // currencyType enum
}
// Total Size: 8 bytes
```

### 10.6 Shards_Consume (CONSUME_SHARD - 0x2011)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Shards_Consume
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2011

    public byte itemType;            // Offset: 2, Size: 1 byte
                                     // Shard type to consume
}
// Total Size: 3 bytes
```

---

## 11. Rewards Packets

### 11.1 PlayerRewards (PLAYER_REWARDS_REPLY - 0x2010)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PlayerRewards
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2010

    public UInt32 timeShards;        // Offset: 2, Size: 4 bytes

    public UInt32 bronze;            // Offset: 6, Size: 4 bytes

    public UInt32 silver;            // Offset: 10, Size: 4 bytes

    public UInt32 gold;              // Offset: 14, Size: 4 bytes

    public UInt16 lives;             // Offset: 18, Size: 2 bytes

    public UInt32 hellShards;        // Offset: 20, Size: 4 bytes

    public UInt32 hellTime;          // Offset: 24, Size: 4 bytes
                                     // Current hell time remaining

    public UInt32 maxHellTime;       // Offset: 28, Size: 4 bytes
                                     // Total hell time when entered

    public byte guna;                // Offset: 32, Size: 1 byte
                                     // Karma guna state

    public UInt32 wins;              // Offset: 33, Size: 4 bytes

    public UInt32 losses;            // Offset: 37, Size: 4 bytes

    public byte sattva;              // Offset: 41, Size: 1 byte
                                     // Good karma %

    public byte rajas;               // Offset: 42, Size: 1 byte
                                     // Neutral karma %

    public byte tamas;               // Offset: 43, Size: 1 byte
                                     // Bad karma %

    public UInt32 bhaktiTokens;      // Offset: 44, Size: 4 bytes

    public UInt32 gnanaTokens;       // Offset: 48, Size: 4 bytes
}
// Total Size: 52 bytes
```

### 11.2 PlayerRewards_Request (PLAYER_REWARDS_REQUEST - 0x2009)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PlayerRewards_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2009
}
// Total Size: 2 bytes
```

### 11.3 MatchRewards (MATCH_REWARDS - 0x2008)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchRewards
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2008

    public UInt32 iTimeShards;       // Offset: 2, Size: 4 bytes
                                     // Initial time shards

    public UInt32 aTimeShards;       // Offset: 6, Size: 4 bytes
                                     // After (new balance)

    public Int16 iBronze;            // Offset: 10, Size: 2 bytes
                                     // Initial bronze

    public UInt16 aBronze;           // Offset: 12, Size: 2 bytes
                                     // After bronze

    public Int16 iPlayerLives;       // Offset: 14, Size: 2 bytes
                                     // Initial lives

    public UInt16 aPlayerLives;      // Offset: 16, Size: 2 bytes
                                     // After lives

    public UInt32 iHellShards;       // Offset: 18, Size: 4 bytes

    public UInt32 aHellShards;       // Offset: 22, Size: 4 bytes

    public byte iGuna;               // Offset: 26, Size: 1 byte
                                     // Initial guna

    public byte aGuna;               // Offset: 27, Size: 1 byte
                                     // After guna

    public byte iRajas;              // Offset: 28, Size: 1 byte

    public byte aRajas;              // Offset: 29, Size: 1 byte

    public byte iTamas;              // Offset: 30, Size: 1 byte

    public byte aTamas;              // Offset: 31, Size: 1 byte

    public byte iSattva;             // Offset: 32, Size: 1 byte

    public byte aSattva;             // Offset: 33, Size: 1 byte

    public byte itemCount;           // Offset: 34, Size: 1 byte
                                     // MatchRewardItemInfo[] follows
}
// Total Size: 35 bytes + (itemCount * sizeof(MatchRewardItemInfo))
```

### 11.4 MatchRewardItemInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchRewardItemInfo
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] ItemUUID;          // Offset: 0, Size: 16 bytes

    public UInt32 ItemID;            // Offset: 16, Size: 4 bytes
}
// Total Size: 20 bytes
```

### 11.5 RewardInfoPacket (DAILY_REWARDS - 0x2081)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct RewardInfoPacket
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2081

    public int rewardCount;          // Offset: 2, Size: 4 bytes
                                     // RewardTypeInfo[] follows
}
// Total Size: 6 bytes + (count * sizeof(RewardTypeInfo))
```

### 11.6 RewardScheduleEntry

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct RewardScheduleEntry
{
    public byte Day;                 // Offset: 0, Size: 1 byte
                                     // Day of week (0-6)

    public int Amount;               // Offset: 1, Size: 4 bytes
                                     // Reward amount

    public byte IsClaimed;           // Offset: 5, Size: 1 byte

    public byte IsClaimable;         // Offset: 6, Size: 1 byte
}
// Total Size: 7 bytes
```

### 11.7 RewardTypeInfo

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct RewardTypeInfo
{
    public byte RewardType;          // Offset: 0, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 7)]
    public RewardScheduleEntry[] Schedule; // Offset: 1, Size: 7 * 7 = 49 bytes

    public UInt32 NextClaimInSeconds;// Offset: 50, Size: 4 bytes

    public UInt32 ExpiresInSeconds;  // Offset: 54, Size: 4 bytes
}
// Total Size: 58 bytes
```

### 11.8 MatchPlayerData (MATCH_DATA - 0x2101)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchPlayerData
{
    public UInt32 UniqueID;          // Offset: 0, Size: 4 bytes

    public byte KarmaChoice;         // Offset: 4, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileNames;      // Offset: 5, Size: 13 bytes

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendID;          // Offset: 18, Size: 9 bytes

    public byte iSattva;             // Offset: 27, Size: 1 byte
    public byte iRajas;              // Offset: 28, Size: 1 byte
    public byte iTamas;              // Offset: 29, Size: 1 byte
    public byte aSattva;             // Offset: 30, Size: 1 byte
    public byte aRajas;              // Offset: 31, Size: 1 byte
    public byte aTamas;              // Offset: 32, Size: 1 byte
    public byte iGuna;               // Offset: 33, Size: 1 byte
    public byte aGuna;               // Offset: 34, Size: 1 byte
}
// Total Size: 35 bytes
```

### 11.9 MatchDataEx (MATCH_DATA - 0x2101)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchDataEx
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2101

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public MatchPlayerData[] matchPlayerData; // Offset: 2, Size: 6 * 35 = 210 bytes
}
// Total Size: 212 bytes
```

---

## 12. Meditation Packets

### 12.1 Meditation_Info (MEDITATION_STATE - 0x2012)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Meditation_Info
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2012

    public byte meditationState;     // Offset: 2, Size: 1 byte
                                     // 0=None, 1=Bhakti, 2=Gnana

    public UInt32 bhakti_timer_remaining; // Offset: 3, Size: 4 bytes
    public UInt32 bhakti_timer_total;     // Offset: 7, Size: 4 bytes
    public UInt32 gnana_timer_remaining;  // Offset: 11, Size: 4 bytes
    public UInt32 gnana_timer_total;      // Offset: 15, Size: 4 bytes

    public UInt32 timeShards;        // Offset: 19, Size: 4 bytes
}
// Total Size: 23 bytes
```

### 12.2 Meditation_Complete_Request (MEDITATION_COMPLETE_REQUEST - 0x2013)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Meditation_Complete_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2013
}
// Total Size: 2 bytes
```

### 12.3 Meditation_Begin_Request (MEDITATION_BEGIN_REQUEST - 0x2014)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Meditation_Begin_Request
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2014

    public byte meditationState;     // Offset: 2, Size: 1 byte
                                     // 1=Bhakti, 2=Gnana
}
// Total Size: 3 bytes
```

---

## 13. Settings Packets

### 13.1 UserSettings_Info (USERSETTINGS - 0x2060)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct UserSettings_Info
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2060

    public UInt16 screenTutorialInfo;// Offset: 2, Size: 2 bytes
                                     // Bit flags for completed tutorials

    public UInt16 buttonIndicatorInfo;// Offset: 4, Size: 2 bytes
                                     // Bit flags for seen indicators

    public byte profileImageID;      // Offset: 6, Size: 1 byte
}
// Total Size: 7 bytes
```

---

## 14. Chat Packets

### 14.1 ChatMessageRequest (CHAT_MESSAGE - 0x2150)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ChatMessageRequest
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2150

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 2, Size: 9 bytes
                                     // Recipient ID

    public byte messageType;         // Offset: 11, Size: 1 byte
                                     // 1=Friends, 2=Party, 3=Lobby

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 100)]
    public string message;           // Offset: 12, Size: 100 bytes
}
// Total Size: 112 bytes
```

### 14.2 ChatMessageResponse (CHAT_MESSAGE - 0x2150)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ChatMessageResponse
{
    public UInt16 packetType;        // Offset: 0, Size: 2 bytes
                                     // Value: 0x2150

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string profileName;       // Offset: 2, Size: 13 bytes
                                     // Sender name

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 9)]
    public string friendId;          // Offset: 15, Size: 9 bytes
                                     // Sender ID

    public byte messageType;         // Offset: 24, Size: 1 byte

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 100)]
    public string message;           // Offset: 25, Size: 100 bytes
}
// Total Size: 125 bytes
```

---

## 15. Leaderboard Packets

### 15.1 Leaderboard Request/Reply

Leaderboard packets use LEADERBOARD_REQUEST (0x2050) and LEADERBOARD_REPLY (0x2051).

Structure details depend on implementation - typically include:
- Leaderboard type
- Page/offset
- Count
- LeaderboardEntry[] with rank, playerId, name, score

---

## Appendix A: Enum Reference

### A.1 LoginStatus

```csharp
public enum LoginStatus
{
    SESSION_EXPIRED = 0,
    LOGIN_SUCCESSFUL = 1,
    ERROR = 2
}
```

### A.2 currencyType

```csharp
public enum currencyType
{
    Bronze = 0,
    Silver = 1,
    Gold = 2
}
```

---

## Appendix B: Size Summary

| Struct | Size (bytes) |
|--------|--------------|
| DeviceInfo | 74 |
| Version_Info | 6 |
| ItemInfo | 20 |
| Avatar_Info | 161 |
| Match_Avatar | 57 |
| Match_Confirm | 352 |
| Friend_Info | 42 |
| PartyPlayers | 30 |
| PartyDataPacket | 108 |
| LobbyPlayerInfo | 36 |
| LobbyDataPacket | 270 |
| PlayerRewards | 52 |
| MatchRewards | 35+ |
| ChatMessageRequest | 112 |
| ChatMessageResponse | 125 |

---

**Document Info:**
- Total Structs: 83
- Lines: ~2000
- Created: January 21, 2026
- Part: 2 of 11

---

*End of WebSocket Packets Document*
