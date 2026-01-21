# AUM Protocol - MatchKeeper (Complete)

**Version:** 2.0 (Complete)
**Date:** January 21, 2026
**Source:** `Assets/Scripts/Managers/MKManager.cs` (Server)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Connection Flow](#2-connection-flow)
3. [Packet Structures](#3-packet-structures)
4. [Packet Type IDs](#4-packet-type-ids)
5. [Complete MKManager Implementation](#5-complete-mkmanager-implementation)
6. [Data Formats](#6-data-formats)
7. [Test Mode Bypass](#7-test-mode-bypass)

---

## 1. Overview

### 1.1 Purpose

MatchKeeper is the orchestration service that:
- Registers game servers as available
- Assigns matches to servers
- Receives match results for backend processing
- Coordinates with WebSocket backend

### 1.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INFRASTRUCTURE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────┐         ┌──────────────────┐         ┌─────────────┐│
│  │  WebSocket    │◄───────►│   MatchKeeper    │◄───────►│ Game Server ││
│  │  Backend      │         │   (Orchestrator) │         │   Pool      ││
│  │               │         │                  │         │             ││
│  │  - Clients    │ HTTP    │  - Server Pool   │  TCP    │  - Server 1 ││
│  │  - Matchmake  │◄───────►│  - Match Queue   │◄───────►│  - Server 2 ││
│  │  - Results    │         │  - Assignment    │  6767   │  - Server N ││
│  └───────────────┘         └──────────────────┘         └─────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Protocol Summary

| Aspect | Value |
|--------|-------|
| Transport | TCP |
| Port | 6767 |
| Connection | localhost (127.0.0.1) |
| Serialization | Marshal with Pack=1 |
| Packet Count | 3 types, 6 structs |

---

## 2. Connection Flow

### 2.1 Server Registration Flow

```
Game Server                                    MatchKeeper
     │                                              │
     │  Initialize()                                │
     │  Connect(127.0.0.1:6767)                     │
     ├─────────────────────────────────────────────►│
     │                                              │
     │             ConnectionAccepted               │
     │◄─────────────────────────────────────────────│
     │                                              │
     │  MK_AUTH (ServerUUID, isUnityEditor)         │
     ├─────────────────────────────────────────────►│
     │                                              │
     │  [Server registered in available pool]       │
     │                                              │
```

### 2.2 Match Assignment Flow

```
MatchKeeper                                   Game Server
     │                                              │
     │  [Match ready in queue]                      │
     │                                              │
     │  MK_STARTGAME (MatchUUID, avatarInfo[])      │
     ├─────────────────────────────────────────────►│
     │                                              │
     │                     [Server initializes]     │
     │                     Socket.Initialize(port)  │
     │                                              │
     │                     [Clients connect]        │
     │                     [Match plays]            │
     │                                              │
     │  MK_MATCHEND (results, karma, stats)         │
     │◄─────────────────────────────────────────────│
     │                                              │
     │  [Process results, update database]          │
     │                                              │
```

### 2.3 Complete Lifecycle

```
PHASE 1: REGISTRATION
═════════════════════
Server Start
    │
    ▼
MKManager.Initialize()
    │
    ├── ClientSocket.Connect("127.0.0.1", 6767)
    │
    ├── Register event handlers:
    │   ├── ConnectionAccepted → OnMKConnectionAccepted
    │   ├── ConnectionClosed → OnMKConnectionClosed
    │   └── MessageReceived → OnMKMessageReceived
    │
    ▼
OnMKConnectionAccepted()
    │
    ├── Build MKAuth packet:
    │   ├── ServerUUID (16 bytes)
    │   └── isUnityEditor (1 = editor, 0 = build)
    │
    └── Send MKAuth to MatchKeeper

PHASE 2: WAITING
════════════════
Server idles, waiting for MK_STARTGAME
    │
    ▼
OnMKMessageReceived(MK_STARTGAME)
    │
    ├── Deserialize MKMatchData
    │   ├── MatchUUID
    │   ├── matchPort (assigned port)
    │   ├── matchType
    │   ├── IsFirstMatch
    │   └── avatarInfo[] (player data)
    │
    ├── Store match data:
    │   ├── GameManager.Instance.MatchUUID = MatchUUID
    │   ├── GameManager.Instance.matchType = matchType
    │   └── GameManager.Instance.IsFirstMatch = IsFirstMatch
    │
    ├── Add players to avatarList:
    │   └── PlayerManager.avatarList.TryAdd(sessionUUID, avatarInfo)
    │
    ├── Initialize game socket:
    │   └── Socket.Initialize(matchPort)
    │
    └── Signal ready:
        └── MatchState.Instance.SignalMatchReady()

PHASE 3: MATCH
══════════════
Match plays through states:
    PREMATCH → TELEPORT → MATCH → ENDMATCH → POSTMATCH → END
    │
    ▼
GameManager.EndGame()
    │
    └── MKManager.SendMKMatchEnd()

PHASE 4: RESULTS
════════════════
SendMKMatchEnd()
    │
    ├── Build MKMatchEnd packet:
    │   ├── MatchUUID
    │   ├── matchTime
    │   ├── winningTeam
    │   ├── avatarCount
    │   └── avatarData[] (per-player stats)
    │       ├── avatarUniqueID
    │       ├── team
    │       ├── karmaDecision[]
    │       ├── deadPosition
    │       ├── deadDuration
    │       └── damage stats
    │
    └── Send to MatchKeeper
```

---

## 3. Packet Structures

### 3.1 MKAuth (0x1000)

**Direction:** Server → MatchKeeper
**Purpose:** Register server as available

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKAuth
{
    public UInt16 packetLen;         // Offset: 0, Size: 2 bytes
                                     // Total packet size

    public UInt16 packetType;        // Offset: 2, Size: 2 bytes
                                     // Value: 0x1000

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] ServerUUID;        // Offset: 4, Size: 16 bytes
                                     // Unique server identifier

    public byte isUnityEditor;       // Offset: 20, Size: 1 byte
                                     // 1 = running in Unity Editor
                                     // 0 = standalone build
}
// Total Size: 21 bytes
```

**Byte Layout:**
```
Offset  Size  Field          Description
0       2     packetLen      0x15 0x00 (21 in little-endian)
2       2     packetType     0x00 0x10 (0x1000)
4       16    ServerUUID     Server's GUID bytes
20      1     isUnityEditor  0x00 or 0x01
────────────────────────────────────────────
Total: 21 bytes
```

### 3.2 MKMatchAvatar

**Purpose:** Player data in match assignment

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchAvatar
{
    public UInt32 UniqueID;          // Offset: 0, Size: 4 bytes
                                     // Player's unique ID

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] avatarUniqueID;    // Offset: 4, Size: 16 bytes
                                     // Avatar UUID

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionUUID;       // Offset: 20, Size: 16 bytes
                                     // Session UUID for auth

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string UserID;            // Offset: 36, Size: 13 bytes
                                     // User ID string

    public UInt32 teamID;            // Offset: 49, Size: 4 bytes
                                     // Team assignment (1 or 2)

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
    public string nickName;          // Offset: 53, Size: 13 bytes
                                     // Display name

    public byte fightingStyle;       // Offset: 66, Size: 1 byte
                                     // FightingStyles enum

    public byte fighterClass;        // Offset: 67, Size: 1 byte
                                     // FighterClass enum

    public byte godSelected;         // Offset: 68, Size: 1 byte
                                     // TrinityGods enum

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementalSelected; // Offset: 69, Size: 4 bytes
                                     // 4 elemental slots

    public byte weaponVariant;       // Offset: 73, Size: 1 byte
                                     // Weapon skin

    public byte IsBot;               // Offset: 74, Size: 1 byte
                                     // 1 = AI bot, 0 = human
}
// Total Size: 75 bytes
```

**Byte Layout:**
```
Offset  Size  Field              Description
0       4     UniqueID           Player ID
4       16    avatarUniqueID     Avatar GUID
20      16    sessionUUID        Session GUID
36      13    UserID             User string
49      4     teamID             1 or 2
53      13    nickName           Display name
66      1     fightingStyle      0-4
67      1     fighterClass       0-1
68      1     godSelected        0-2
69      4     elementalSelected  4 elementals
73      1     weaponVariant      Skin ID
74      1     IsBot              0 or 1
────────────────────────────────────────────
Total: 75 bytes per player
```

### 3.3 MKMatchData (0x1001)

**Direction:** MatchKeeper → Server
**Purpose:** Assign match to server

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchData
{
    public UInt16 packetLen;         // Offset: 0, Size: 2 bytes

    public UInt16 packetType;        // Offset: 2, Size: 2 bytes
                                     // Value: 0x1001

    public byte matchType;           // Offset: 4, Size: 1 byte
                                     // MatchType enum

    public byte IsFirstMatch;        // Offset: 5, Size: 1 byte
                                     // 1 = first match (tutorial)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] MatchUUID;         // Offset: 6, Size: 16 bytes
                                     // Unique match identifier

    public int matchPort;            // Offset: 22, Size: 4 bytes
                                     // UDP port to use

    public byte avatarCount;         // Offset: 26, Size: 1 byte
                                     // Number of players (1-6)

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public MKMatchAvatar[] avatarInfo; // Offset: 27, Size: 6 * 75 = 450 bytes
                                       // Player data
}
// Total Size: 477 bytes
```

**Byte Layout:**
```
Offset  Size  Field          Description
0       2     packetLen      477 bytes
2       2     packetType     0x01 0x10 (0x1001)
4       1     matchType      MatchType enum
5       1     IsFirstMatch   0 or 1
6       16    MatchUUID      Match GUID
22      4     matchPort      UDP port (e.g., 6006)
26      1     avatarCount    1-6
27      450   avatarInfo     6 x MKMatchAvatar
────────────────────────────────────────────
Total: 477 bytes
```

### 3.4 KarmaDecision

**Purpose:** Per-player karma choice

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct KarmaDecision
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] AvatarUUID;        // Offset: 0, Size: 16 bytes
                                     // Target player

    public byte Decision;            // Offset: 16, Size: 1 byte
                                     // 0 = Sattva (positive)
                                     // 1 = Rajas (neutral)
                                     // 2 = Tamas (negative)

    public KarmaDecision(byte[] _avatarUUID, byte _decision)
    {
        AvatarUUID = _avatarUUID;
        Decision = _decision;
    }
}
// Total Size: 17 bytes
```

### 3.5 MKMatchAvatarData

**Purpose:** Per-player match results

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchAvatarData
{
    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] avatarUniqueID;    // Offset: 0, Size: 16 bytes
                                     // Player's avatar UUID

    public byte avatarTeam;          // Offset: 16, Size: 1 byte
                                     // Team (1 or 2)

    public byte karmaPlayerCount;    // Offset: 17, Size: 1 byte
                                     // Number of karma decisions

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public KarmaDecision[] karmaDecision; // Offset: 18, Size: 5 * 17 = 85 bytes
                                          // Up to 5 karma decisions

    public byte deadPosition;        // Offset: 103, Size: 1 byte
                                     // Death placement (1st to 6th)

    public UInt32 deadDuration;      // Offset: 104, Size: 4 bytes
                                     // Time spent dead (seconds)

    public UInt16 damageMeleeDealt;  // Offset: 108, Size: 2 bytes
    public UInt16 damageMeleeReceived; // Offset: 110, Size: 2 bytes
    public UInt16 damageSpellDealt;  // Offset: 112, Size: 2 bytes
    public UInt16 damageSpellReceived; // Offset: 114, Size: 2 bytes
    public UInt16 damageMeleeBlocked; // Offset: 116, Size: 2 bytes
    public UInt16 damageSpellBlocked; // Offset: 118, Size: 2 bytes
}
// Total Size: 120 bytes
```

**Byte Layout:**
```
Offset  Size  Field                Description
0       16    avatarUniqueID       Player avatar GUID
16      1     avatarTeam           1 or 2
17      1     karmaPlayerCount     0-5
18      85    karmaDecision[]      5 x KarmaDecision (17 each)
103     1     deadPosition         Placement (1-6)
104     4     deadDuration         Seconds dead
108     2     damageMeleeDealt     Melee damage dealt
110     2     damageMeleeReceived  Melee damage taken
112     2     damageSpellDealt     Spell damage dealt
114     2     damageSpellReceived  Spell damage taken
116     2     damageMeleeBlocked   Melee damage blocked
118     2     damageSpellBlocked   Spell damage blocked
────────────────────────────────────────────
Total: 120 bytes per player
```

### 3.6 MKMatchEnd (0x1002)

**Direction:** Server → MatchKeeper
**Purpose:** Report match results

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MKMatchEnd
{
    public UInt16 packetLen;         // Offset: 0, Size: 2 bytes

    public UInt16 packetType;        // Offset: 2, Size: 2 bytes
                                     // Value: 0x1002

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] MatchUUID;         // Offset: 4, Size: 16 bytes
                                     // Match identifier

    public UInt32 matchTime;         // Offset: 20, Size: 4 bytes
                                     // Total match duration (seconds)

    public byte winningTeam;         // Offset: 24, Size: 1 byte
                                     // 1 or 2

    public byte avatarCount;         // Offset: 25, Size: 1 byte
                                     // Number of players

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public MKMatchAvatarData[] avatarData; // Offset: 26, Size: 6 * 120 = 720 bytes
                                           // Per-player results
}
// Total Size: 746 bytes
```

**Byte Layout:**
```
Offset  Size  Field          Description
0       2     packetLen      746 bytes
2       2     packetType     0x02 0x10 (0x1002)
4       16    MatchUUID      Match GUID
20      4     matchTime      Duration in seconds
24      1     winningTeam    1 or 2
25      1     avatarCount    1-6
26      720   avatarData     6 x MKMatchAvatarData
────────────────────────────────────────────
Total: 746 bytes
```

---

## 4. Packet Type IDs

### 4.1 PacketType Enum

```csharp
public enum PacketType
{
    MK_AUTH      = 0x1000,  // Server → MK: Register server
    MK_STARTGAME = 0x1001,  // MK → Server: Assign match
    MK_MATCHEND  = 0x1002,  // Server → MK: Report results
}
```

### 4.2 Packet Size Summary

| Packet | ID | Size (bytes) | Direction |
|--------|-----|--------------|-----------|
| MKAuth | 0x1000 | 21 | S → MK |
| MKMatchData | 0x1001 | 477 | MK → S |
| MKMatchEnd | 0x1002 | 746 | S → MK |

### 4.3 Nested Structure Sizes

| Structure | Size (bytes) |
|-----------|--------------|
| MKMatchAvatar | 75 |
| KarmaDecision | 17 |
| MKMatchAvatarData | 120 |

---

## 5. Complete MKManager Implementation

### 5.1 Full Source Code

```csharp
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using UnityEngine;

public class MKManager
{
    public static ClientSocket mkSocket;

    public static void Initialize()
    {
        mkSocket = new ClientSocket();
        mkSocket.Connect("127.0.0.1", 6767, 1024, false, 3);
        mkSocket.ConnectionAccepted += OnMKConnectionAccepted;
        mkSocket.ConnectionClosed += OnMKConnectionClosed;
        mkSocket.ConnectionFailed += OnMKConnectionClosed;
        mkSocket.MessageReceived += OnMKMessageReceived;
    }

    public static void DeInitialize()
    {
        if (mkSocket == null) return; // Skip in TestMode
        mkSocket.ConnectionAccepted -= OnMKConnectionAccepted;
        mkSocket.ConnectionClosed -= OnMKConnectionClosed;
        mkSocket.ConnectionFailed -= OnMKConnectionClosed;
        mkSocket.MessageReceived -= OnMKMessageReceived;
        mkSocket.Close();
    }

    public static void OnMKConnectionAccepted()
    {
        Debug.Log("[MatchKeeper] Connection Accepted");

        // Authenticate with the MatchKeeper
        MKPacket.MKAuth authPacket = new MKPacket.MKAuth()
        {
            packetLen = (UInt16)Utils.GetSize(typeof(MKPacket.MKAuth)),
            ServerUUID = GameManager.Instance.ServerUUID.ToByteArray(),
            packetType = (UInt16)MKPacket.PacketType.MK_AUTH,
            isUnityEditor = (byte)(Application.isEditor == true ? 1 : 0)
        };
        mkSocket.Send(Serializer.Serialize<MKPacket.MKAuth>(authPacket));
    }

    public static void OnMKConnectionClosed()
    {
        Debug.Log("[MatchKeeper] Connection Closed");
        // Could reconnect here if desired
        // Initialize();
    }

    public static void SendMKMatchEnd()
    {
        if (mkSocket == null) return; // Skip in TestMode

        MKPacket.MKMatchEnd matchEndPacket = new MKPacket.MKMatchEnd()
        {
            packetLen = (UInt16)Utils.GetSize(typeof(MKPacket.MKMatchEnd)),
            packetType = (UInt16)MKPacket.PacketType.MK_MATCHEND,
            MatchUUID = GameManager.Instance.MatchUUID.ToByteArray(),
            matchTime = (UInt32)MatchState.Instance.matchTimer,
            winningTeam = (byte)GameManager.Instance.winningTeam,
            avatarCount = (byte)PlayerManager.avatarList.Count
        };

        matchEndPacket.avatarData = new MKPacket.MKMatchAvatarData[6];

        int i = 0;
        foreach (Player player in PlayerManager.playerList.Values)
        {
            matchEndPacket.avatarData[i].avatarUniqueID = player.avatarUUID.ToByteArray();
            matchEndPacket.avatarData[i].avatarTeam = player.team;
            matchEndPacket.avatarData[i].karmaDecision = new MKPacket.KarmaDecision[5];

            // Get karma decisions this player made
            KarmaPlayer[] karmaPlayers = player.GetKarmaPlayers(
                ref matchEndPacket.avatarData[i].karmaPlayerCount
            );

            int karmaIndex = 0;
            foreach (KarmaPlayer karmaPlayer in karmaPlayers)
            {
                matchEndPacket.avatarData[i].karmaDecision[karmaIndex] =
                    new MKPacket.KarmaDecision(
                        karmaPlayer.player.avatarUUID.ToByteArray(),
                        (byte)karmaPlayer.karma
                    );
                karmaIndex++;
            }

            matchEndPacket.avatarData[i].deadPosition = player.deadPosition;
            matchEndPacket.avatarData[i].deadDuration = (UInt32)player.deadDuration;
            matchEndPacket.avatarData[i].damageMeleeBlocked = (UInt16)player.playerData.stats.damageMeleeBlocked;
            matchEndPacket.avatarData[i].damageMeleeDealt = (UInt16)player.playerData.stats.damageMeleeDealt;
            matchEndPacket.avatarData[i].damageMeleeReceived = (UInt16)player.playerData.stats.damageMeleeReceived;
            matchEndPacket.avatarData[i].damageSpellBlocked = (UInt16)player.playerData.stats.damageSpellBlocked;
            matchEndPacket.avatarData[i].damageSpellDealt = (UInt16)player.playerData.stats.damageSpellDealt;
            matchEndPacket.avatarData[i].damageSpellReceived = (UInt16)player.playerData.stats.damageSpellReceived;

            i++;
        }

        mkSocket.Send(Serializer.Serialize<MKPacket.MKMatchEnd>(matchEndPacket));
    }

    public static void OnMKMessageReceived(ref byte[] message)
    {
        UInt16 packetType = BitConverter.ToUInt16(message, 2);

        switch ((MKPacket.PacketType)packetType)
        {
            case MKPacket.PacketType.MK_STARTGAME:
            {
                MKPacket.MKMatchData matchData =
                    Serializer.Deserialize<MKPacket.MKMatchData>(message);

                Guid MatchUUID = new Guid(matchData.MatchUUID);
                Debug.Log($"[MatchKeeper] Received game information for:{MatchUUID}");

                // Set up socket on assigned port
                Socket.serverPort = matchData.matchPort;
                Socket.Initialize();

                // Store match configuration
                GameManager.Instance.matchType = (MatchType)matchData.matchType;
                GameManager.Instance.IsFirstMatch = matchData.IsFirstMatch == 1;
                GameManager.Instance.MatchUUID = MatchUUID;

                Debug.Log($"[MatchKeeper] Match Type: {GameManager.Instance.matchType} " +
                         $"Player Count:{matchData.avatarCount} " +
                         $"FirstMatch:{GameManager.Instance.IsFirstMatch}");

                // Register expected players
                for(int i = 0; i < matchData.avatarCount; i++)
                {
                    PlayerManager.avatarList.TryAdd(
                        new Guid(matchData.avatarInfo[i].sessionUUID).ToString(),
                        matchData.avatarInfo[i]
                    );
                }

                // Signal match is ready to start
                MatchState.Instance.SignalMatchReady();
                break;
            }
            default:
                break;
        }
    }
}
```

### 5.2 Packet Definitions

```csharp
public class MKPacket
{
    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct MKAuth
    {
        public UInt16 packetLen;
        public UInt16 packetType;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] ServerUUID;
        public byte isUnityEditor;
    }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct MKMatchAvatar
    {
        public UInt32 UniqueID;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] avatarUniqueID;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] sessionUUID;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
        public string UserID;
        public UInt32 teamID;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 13)]
        public string nickName;
        public byte fightingStyle;
        public byte fighterClass;
        public byte godSelected;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
        public byte[] elementalSelected;
        public byte weaponVariant;
        public byte IsBot;
    }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct MKMatchData
    {
        public UInt16 packetLen;
        public UInt16 packetType;
        public byte matchType;
        public byte IsFirstMatch;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] MatchUUID;
        public int matchPort;
        public byte avatarCount;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
        public MKMatchAvatar[] avatarInfo;
    }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct KarmaDecision
    {
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] AvatarUUID;
        public byte Decision;

        public KarmaDecision(byte[] _avatarUUID, byte _decision)
        {
            AvatarUUID = _avatarUUID;
            Decision = _decision;
        }
    }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct MKMatchAvatarData
    {
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] avatarUniqueID;
        public byte avatarTeam;
        public byte karmaPlayerCount;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
        public KarmaDecision[] karmaDecision;
        public byte deadPosition;
        public UInt32 deadDuration;
        public UInt16 damageMeleeDealt;
        public UInt16 damageMeleeReceived;
        public UInt16 damageSpellDealt;
        public UInt16 damageSpellReceived;
        public UInt16 damageMeleeBlocked;
        public UInt16 damageSpellBlocked;
    }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct MKMatchEnd
    {
        public UInt16 packetLen;
        public UInt16 packetType;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
        public byte[] MatchUUID;
        public UInt32 matchTime;
        public byte winningTeam;
        public byte avatarCount;
        [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
        public MKMatchAvatarData[] avatarData;
    }

    public enum PacketType
    {
        MK_AUTH = 0x1000,
        MK_STARTGAME = 0x1001,
        MK_MATCHEND = 0x1002,
    }
}
```

---

## 6. Data Formats

### 6.1 Karma System

```
Karma Decisions:
  0 = Sattva (Positive) - Good karma, +1 lives
  1 = Rajas (Neutral)   - No change
  2 = Tamas (Negative)  - Bad karma, -1 lives

Guna State (calculated from karma balance):
  Sattva > Rajas + Tamas → Sattva state
  Rajas > Sattva + Tamas → Rajas state
  Tamas > Sattva + Rajas → Tamas state
```

### 6.2 Match Types

```csharp
public enum MatchType
{
    SOLO_1V1   = 1 << 0,  // 1  - Solo 1v1
    SOLO_1V2   = 1 << 1,  // 2  - Solo vs 2 bots
    SOLO_1V5   = 1 << 2,  // 4  - Solo vs 5 bots
    DUO_2V2    = 1 << 3,  // 8  - 2v2 team
    DUO_2V4    = 1 << 4,  // 16 - 2 vs 4 bots
    TRIO_3V3   = 1 << 5,  // 32 - 3v3 team
    TRAINING   = 1 << 6,  // 64 - Training mode
    TUTORIAL   = 1 << 7,  // 128 - Tutorial
    FIRST_MATCH = 1 << 8, // 256 - First match (special)
    NONE       = 1 << 9   // 512 - No match
}
```

### 6.3 Fighting Styles

```csharp
public enum FightingStyles
{
    Amuktha       = 0,  // Close-range sword
    MantraMuktha  = 1,  // Ranged magic
    MukthaMuktha  = 2,  // Close-range axe
    PaniMuktha    = 3,  // Ranged discus
    YantraMuktha  = 4,  // Ranged bow
}
```

### 6.4 Trinity Gods

```csharp
public enum TrinityGods
{
    Brahma = 0,  // Shield, +3 focus streak
    Shiva  = 1,  // Third Eye, +20% damage
    Vishnu = 2,  // +30% speed, stamina discount
}
```

---

## 7. Test Mode Bypass

### 7.1 TestModeManager

When running in test mode, MatchKeeper is bypassed:

```csharp
// TestModeManager.cs (Server)
public static void Setup()
{
    // Don't connect to MatchKeeper
    // MKManager.Initialize() is NOT called

    // Generate deterministic session UUIDs
    for (int i = 0; i < maxPlayers; i++)
    {
        string identifier = $"test-player-{i + 1}-session";
        Guid sessionUUID = GenerateSessionUUID(identifier);

        MKPacket.MKMatchAvatar avatar = new MKPacket.MKMatchAvatar()
        {
            sessionUUID = sessionUUID.ToByteArray(),
            // ... other fields
        };

        PlayerManager.avatarList.TryAdd(sessionUUID.ToString(), avatar);
    }

    // Initialize socket directly
    Socket.serverPort = 6006;
    Socket.Initialize();

    // Signal ready
    MatchState.Instance.SignalMatchReady();
}

public static Guid GenerateSessionUUID(string identifier)
{
    using (MD5 md5 = MD5.Create())
    {
        byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(identifier));
        return new Guid(hash);
    }
}
```

### 7.2 Test Mode Check

```csharp
// In MKManager methods
public static void SendMKMatchEnd()
{
    if (mkSocket == null) return; // Skip in TestMode
    // ... send packet
}

public static void DeInitialize()
{
    if (mkSocket == null) return; // Skip in TestMode
    // ... cleanup
}
```

---

## Appendix A: Message Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MESSAGE SEQUENCE                                │
└─────────────────────────────────────────────────────────────────────────┘

    Server                           MatchKeeper                    Backend
      │                                   │                            │
      │  ┌──── TCP CONNECT ────────────►  │                            │
      │  │                                │                            │
      │  │  MK_AUTH (21 bytes)            │                            │
      │  │  ┌─────────────────────────►   │                            │
      │  │  │ • packetLen = 21            │                            │
      │  │  │ • packetType = 0x1000       │                            │
      │  │  │ • ServerUUID[16]            │                            │
      │  │  │ • isUnityEditor = 0|1       │                            │
      │  │  │                             │                            │
      │  │  │                             │  ┌── Register Server ────► │
      │  │  │                             │  │                         │
      │  │  │                             │  └─────────────────────────┘
      │  │  │                             │                            │
      │  │  │                             │  ◄── Match Ready ────────┐ │
      │  │  │                             │                          │ │
      │  │  │  MK_STARTGAME (477 bytes)   │                          │ │
      │  │  │  ◄─────────────────────────┐│                          │ │
      │  │  │  • packetLen = 477         ││                          │ │
      │  │  │  • packetType = 0x1001     ││                          │ │
      │  │  │  • matchType               ││                          │ │
      │  │  │  • IsFirstMatch            ││                          │ │
      │  │  │  • MatchUUID[16]           ││                          │ │
      │  │  │  • matchPort               ││                          │ │
      │  │  │  • avatarCount             ││                          │ │
      │  │  │  • avatarInfo[6]           ││                          │ │
      │  │  │                             │                            │
      │  │  │  [Match Plays]              │                            │
      │  │  │                             │                            │
      │  │  │  MK_MATCHEND (746 bytes)    │                            │
      │  │  │  ┌─────────────────────────►│                            │
      │  │  │  │ • packetLen = 746        │                            │
      │  │  │  │ • packetType = 0x1002    │                            │
      │  │  │  │ • MatchUUID[16]          │                            │
      │  │  │  │ • matchTime              │                            │
      │  │  │  │ • winningTeam            │  ┌── Process Results ────► │
      │  │  │  │ • avatarCount            │  │ • Update karma          │
      │  │  │  │ • avatarData[6]          │  │ • Update stats          │
      │  │  │  │   - avatarUniqueID       │  │ • Award rewards         │
      │  │  │  │   - avatarTeam           │  └─────────────────────────┘
      │  │  │  │   - karmaDecision[]      │                            │
      │  │  │  │   - damage stats         │                            │
      │  │  │                             │                            │
      │  └────────────────────────────────┘                            │
      │                                                                │
```

---

**Document Info:**
- Total Structs: 6
- Total Packet Types: 3
- Lines: ~650
- Created: January 21, 2026
- Part: 4 of 11

---

*End of MatchKeeper Protocol Document*
