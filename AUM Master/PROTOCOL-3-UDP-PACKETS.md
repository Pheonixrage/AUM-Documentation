# AUM Protocol - UDP In-Game Packets (Complete)

**Version:** 2.0 (Complete)
**Date:** January 21, 2026
**Sources:**
- Client: `Assets/Scripts/Network/Packet.cs`
- Server: `Assets/Scripts/Network/Packet.cs`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Packet Type IDs](#2-packet-type-ids)
3. [Client to Server Packets](#3-client-to-server-packets)
4. [Server to Client Packets](#4-server-to-client-packets)
5. [Log Packets](#5-log-packets)
6. [World Snapshot Format](#6-world-snapshot-format)
7. [Input Processing](#7-input-processing)
8. [Byte Layout Reference](#8-byte-layout-reference)

---

## 1. Overview

### 1.1 Transport Layer

- **Protocol:** UDP via LiteNetLib (native DLL)
- **Port:** 6006 (default), dynamic in production
- **Tick Rate:** 60Hz (16.67ms per tick)
- **Delivery:** ReliableOrdered for critical, Unreliable for snapshots

### 1.2 Packet Format

All packets use `StructLayout.Sequential, Pack = 1`:

```
┌────────────────┬─────────────────────────────────────────┐
│  PacketType    │          Payload                        │
│   (2 bytes)    │         (variable)                      │
└────────────────┴─────────────────────────────────────────┘
```

### 1.3 Statistics

| Direction | Count | Purpose |
|-----------|-------|---------|
| Client → Server | 7 | Input, state, karma |
| Server → Client | 11 | World state, combat logs |
| Bidirectional | 4 | Shared packet types |

---

## 2. Packet Type IDs

### 2.1 Client to Server (PacketTypeOUT - Client)

```csharp
public enum PacketTypeOUT
{
    NETWORKEVENT      = 0x1400,  // Disconnect/network events
    CREATECHARACTER   = 0x1401,  // Authentication request
    PLAYERINPUT       = 0x1403,  // 60Hz tick input
    RESPAWNCHARACTER  = 0x1405,  // Request respawn
    LOGDATA           = 0x1406,  // Debug/combat log
    PLAYERKARMA       = 0x1409,  // Karma decision
    TUTORIALPROGRESS  = 0x140B   // Tutorial state
}
```

### 2.2 Server to Client (PacketTypeOUT - Server)

```csharp
public enum PacketTypeOUT
{
    NETWORKEVENT        = 0x1400,  // Disconnect/network events
    AUTHENTICATE_REPLY  = 0x1401,  // Authentication response
    REMOVECHARACTER     = 0x1402,  // Player disconnected
    WORLDSNAPSHOT       = 0x1403,  // World state (60Hz)
    SIMULATIONRESULT    = 0x1404,  // Prediction correction
    RESPAWNCHARACTER    = 0x1405,  // Respawn confirmed
    LOGDATA             = 0x1406,  // Combat log
    ENDGAMEDATA         = 0x1407,  // Match over data
    MATCHSTATEINFO      = 0x1408,  // Match state change
    PLAYERKARMA         = 0x1409,  // Karma update
    FORFEITMATCH        = 0x140A   // Forfeit notification
}
```

### 2.3 Server Inbound (PacketTypeIN - Server)

```csharp
public enum PacketTypeIN
{
    NETWORKEVENT      = 0x1400,
    AUTHENTICATE      = 0x1401,
    PLAYERINPUT       = 0x1403,
    RESPAWNCHARACTER  = 0x1405,
    LOGDATA           = 0x1406,
    PLAYERKARMA       = 0x1409,
    TUTORIALPROGRESS  = 0x140B
}
```

### 2.4 Client Inbound (PacketTypeIN - Client)

```csharp
public enum PacketTypeIN
{
    NETWORKEVENT      = 0x1400,
    CREATECHARACTER   = 0x1401,
    REMOVECHARACTER   = 0x1402,
    WORLDSNAPSHOT     = 0x1403,
    SIMULATIONRESULT  = 0x1404,
    RESPAWNCHARACTER  = 0x1405,
    LOGDATA           = 0x1406,
    ENDGAMEDATA       = 0x1407,
    MATCHSTATEINFO    = 0x1408,
    PLAYERKARMA       = 0x1409,
    FORFEITMATCH      = 0x140A,
    TUTORIALPROGRESS  = 0x140B
}
```

---

## 3. Client to Server Packets

### 3.1 GracefullDC (NETWORKEVENT - 0x1400)

**Purpose:** Graceful disconnect notification

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct GracefullDC
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1400

    public byte eventType;       // Offset: 2, Size: 1 byte
                                 // 0 = Normal DC
                                 // 1 = Application paused
                                 // 2 = Connection lost
                                 // 3 = Kicked
}
// Total Size: 3 bytes
```

**Byte Layout:**
```
Offset  Size  Field       Example
0       2     packetType  0x00 0x14 (0x1400 little-endian)
2       1     eventType   0x00 (Normal DC)
─────────────────────────────────
Total: 3 bytes
```

### 3.2 Authenticate_Player (CREATECHARACTER - 0x1401)

**Purpose:** Client authentication with session UUID

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Authenticate_Player
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1401

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 16)]
    public byte[] sessionID;     // Offset: 2, Size: 16 bytes
                                 // Session UUID from matchmaking
}
// Total Size: 18 bytes
```

**Byte Layout:**
```
Offset  Size  Field       Description
0       2     packetType  0x01 0x14 (0x1401 little-endian)
2       16    sessionID   GUID bytes (16 bytes)
                          Example: 3d46e7bc-914e-fca2-c3ae-1ae23d72aa34
                          = bc e7 46 3d 4e 91 a2 fc ae c3 34 aa 72 3d e2 1a
─────────────────────────────────
Total: 18 bytes
```

### 3.3 TickInput (PLAYERINPUT - 0x1403)

**Purpose:** Per-tick player input (60Hz)

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct TickInput
{
    public byte JoystickAxis;       // Offset: 0, Size: 1 byte
                                    // 4-bit X + 4-bit Y packed
                                    // X: high nibble, Y: low nibble
                                    // -1 = 0xF, 0 = 0x0, 1 = 0x1

    public float cameraRotation;    // Offset: 1, Size: 4 bytes
                                    // Camera Y rotation in degrees

    public UInt32 currentTick;      // Offset: 5, Size: 4 bytes
                                    // Client's current tick number

    public UInt32 serverTick;       // Offset: 9, Size: 4 bytes
                                    // Last received server tick

    public UInt32 state;            // Offset: 13, Size: 4 bytes
                                    // Client's current FSM state
                                    // (StateType enum cast to UInt32)

    public byte specialAbility;     // Offset: 17, Size: 1 byte
                                    // 0 = none, 1 = pressed, 2 = held, 3 = released

    public float abilityX;          // Offset: 18, Size: 4 bytes
                                    // Ability aim X direction

    public float abilityY;          // Offset: 22, Size: 4 bytes
                                    // Ability aim Y direction

    public byte meleeAbility;       // Offset: 26, Size: 1 byte
                                    // 0 = none, 1 = pressed, 2 = held, 3 = released

    public byte abilityEx;          // Offset: 27, Size: 1 byte
                                    // Extended ability info

    public byte elementalAbility1;  // Offset: 28, Size: 1 byte
                                    // Fire slot: 0/1/2/3

    public byte elementalAbility2;  // Offset: 29, Size: 1 byte
                                    // Water slot: 0/1/2/3

    public byte elementalAbility3;  // Offset: 30, Size: 1 byte
                                    // Air slot: 0/1/2/3

    public byte elementalAbility4;  // Offset: 31, Size: 1 byte
                                    // Earth slot: 0/1/2/3

    public byte dodgeAbility;       // Offset: 32, Size: 1 byte
                                    // 0/1/2/3

    public byte astraAbility;       // Offset: 33, Size: 1 byte
                                    // Ultimate ability: 0/1/2/3
}
// Total Size: 34 bytes
```

**Byte Layout:**
```
Offset  Size  Field              Description
0       1     JoystickAxis       0xFF = (-1,-1), 0x00 = (0,0), 0x11 = (1,1)
1       4     cameraRotation     float, e.g., 180.0f
5       4     currentTick        uint32, client tick
9       4     serverTick         uint32, last server tick
13      4     state              uint32, StateType enum
17      1     specialAbility     0=none, 1=press, 2=hold, 3=release
18      4     abilityX           float, aim direction X
22      4     abilityY           float, aim direction Y
26      1     meleeAbility       0/1/2/3
27      1     abilityEx          extended flags
28      1     elementalAbility1  Fire slot
29      1     elementalAbility2  Water slot
30      1     elementalAbility3  Air slot
31      1     elementalAbility4  Earth slot (or Ether)
32      1     dodgeAbility       0/1/2/3
33      1     astraAbility       0/1/2/3
─────────────────────────────────
Total: 34 bytes
```

**Ability Button States:**
```
0 = Not pressed
1 = Just pressed (this frame)
2 = Held down
3 = Just released (this frame)
```

**Joystick Encoding:**
```csharp
// Encoding
byte axis = (byte)((x == -1 ? 0xF : x) << 4 | (y == -1 ? 0xF : y));

// Examples:
0x00 = (0, 0)   - No movement
0x10 = (1, 0)   - Right
0xF0 = (-1, 0)  - Left
0x01 = (0, 1)   - Forward
0x0F = (0, -1)  - Backward
0x11 = (1, 1)   - Forward-Right
0xFF = (-1, -1) - Backward-Left
0xF1 = (-1, 1)  - Forward-Left
0x1F = (1, -1)  - Backward-Right
```

### 3.4 RespawnCharacter (RESPAWNCHARACTER - 0x1405)

**Purpose:** Request player respawn

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct RespawnCharacter
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1405

    public UInt32 pUniqueID;     // Offset: 2, Size: 4 bytes
                                 // Player's unique ID
}
// Total Size: 6 bytes
```

### 3.5 PlayerKarma (PLAYERKARMA - 0x1409)

**Purpose:** Submit karma decision post-match

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct PlayerKarma
{
    public UInt16 packetType;       // Offset: 0, Size: 2 bytes
                                    // Value: 0x1409

    public UInt32 givingPlayer;     // Offset: 2, Size: 4 bytes
                                    // Player giving karma

    public UInt32 receivingPlayer;  // Offset: 6, Size: 4 bytes
                                    // Player receiving karma

    public byte karma;              // Offset: 10, Size: 1 byte
                                    // 0 = Positive (Sattva)
                                    // 1 = Neutral (Rajas)
                                    // 2 = Negative (Tamas)
}
// Total Size: 11 bytes
```

### 3.6 Tutorial_Progress (TUTORIALPROGRESS - 0x140B)

**Purpose:** Update tutorial state

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Tutorial_Progress
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x140B

    public byte state;           // Offset: 2, Size: 1 byte
                                 // Tutorial step

    public byte botState;        // Offset: 3, Size: 1 byte
                                 // Bot behavior mode

    public byte botDamageIncrease; // Offset: 4, Size: 1 byte
                                   // Bot damage multiplier

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 4)]
    public byte[] elementals;    // Offset: 5, Size: 4 bytes
                                 // Elementals to learn

    public byte god;             // Offset: 9, Size: 1 byte
                                 // God to learn
}
// Total Size: 10 bytes
```

---

## 4. Server to Client Packets

### 4.1 Authenticate_PlayerReply (CREATECHARACTER - 0x1401)

**Purpose:** Authentication response with spawn position

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct Authenticate_PlayerReply
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1401

    public UInt32 uniqueID;      // Offset: 2, Size: 4 bytes
                                 // Assigned in-match player ID

    public float positionX;      // Offset: 6, Size: 4 bytes
                                 // Spawn X position

    public float positionZ;      // Offset: 10, Size: 4 bytes
                                 // Spawn Z position

    public float rotation;       // Offset: 14, Size: 4 bytes
                                 // Spawn Y rotation
}
// Total Size: 18 bytes
```

**Byte Layout:**
```
Offset  Size  Field       Description
0       2     packetType  0x01 0x14 (0x1401)
2       4     uniqueID    In-match ID (1, 2, 3...)
6       4     positionX   Spawn X (float)
10      4     positionZ   Spawn Z (float)
14      4     rotation    Spawn rotation (float, degrees)
─────────────────────────────────
Total: 18 bytes
```

### 4.2 RemoveCharacter (REMOVECHARACTER - 0x1402)

**Purpose:** Notify of player disconnect

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct RemoveCharacter
{
    public UInt16 packetType;      // Offset: 0, Size: 2 bytes
                                   // Value: 0x1402

    public UInt32 playerUniqueID;  // Offset: 2, Size: 4 bytes
                                   // Player who left
}
// Total Size: 6 bytes
```

### 4.3 See_MoveCharacter (In WORLDSNAPSHOT)

**Purpose:** Per-player state in world snapshot

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct See_MoveCharacter
{
    public UInt32 pUniqueID;        // Offset: 0, Size: 4 bytes
                                    // Player ID

    public byte JoystickAxis;       // Offset: 4, Size: 1 byte
                                    // Current movement input

    public float cameraRotation;    // Offset: 5, Size: 4 bytes
                                    // Camera Y rotation

    public float positionX;         // Offset: 9, Size: 4 bytes
                                    // World X position

    public float positionZ;         // Offset: 13, Size: 4 bytes
                                    // World Z position

    public UInt32 state;            // Offset: 17, Size: 4 bytes
                                    // FSM StateType

    public float abilityX;          // Offset: 21, Size: 4 bytes
                                    // Aim direction X

    public float abilityY;          // Offset: 25, Size: 4 bytes
                                    // Aim direction Y

    public float abilityRotation;   // Offset: 29, Size: 4 bytes
                                    // Ability facing angle

    public UInt16 currStamina;      // Offset: 33, Size: 2 bytes
                                    // Current stamina (0-1000)

    public UInt16 willPower;        // Offset: 35, Size: 2 bytes
                                    // Current willpower

    public UInt16 currFocus;        // Offset: 37, Size: 2 bytes
                                    // Current focus meter

    public UInt32 impactIndicator;  // Offset: 39, Size: 4 bytes
                                    // Damage indicator flags

    public UInt32 impactMeleePlayer;// Offset: 43, Size: 4 bytes
                                    // Player hit by melee

    public byte attributeEx;        // Offset: 47, Size: 1 byte
                                    // Extended attributes
                                    // Bits: shield, buff flags

    public byte activeElemental;    // Offset: 48, Size: 1 byte
                                    // Currently active elemental spell
}
// Total Size: 49 bytes
```

**Byte Layout:**
```
Offset  Size  Field              Description
0       4     pUniqueID          Player ID
4       1     JoystickAxis       Packed movement
5       4     cameraRotation     float
9       4     positionX          float
13      4     positionZ          float
17      4     state              StateType enum
21      4     abilityX           float
25      4     abilityY           float
29      4     abilityRotation    float
33      2     currStamina        0-1000
35      2     willPower          0-1000
37      2     currFocus          0-300 (depends on config)
39      4     impactIndicator    damage flags
43      4     impactMeleePlayer  melee hit target
47      1     attributeEx        bit flags
48      1     activeElemental    Elementals enum
─────────────────────────────────
Total: 49 bytes per player
```

### 4.4 SimulationResult (SIMULATIONRESULT - 0x1404)

**Purpose:** Correct client prediction

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SimulationResult
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1404

    public UInt32 currentTick;   // Offset: 2, Size: 4 bytes
                                 // Tick being corrected

    public float rotation;       // Offset: 6, Size: 4 bytes
                                 // Authoritative rotation

    public float positionX;      // Offset: 10, Size: 4 bytes
                                 // Authoritative X

    public float positionZ;      // Offset: 14, Size: 4 bytes
                                 // Authoritative Z

    public UInt32 state;         // Offset: 18, Size: 4 bytes
                                 // Authoritative state

    public byte moveSpeed;       // Offset: 22, Size: 1 byte
                                 // Current move speed modifier
                                 // (for slowed/buffed states)
}
// Total Size: 23 bytes
```

### 4.5 EntityData (In WORLDSNAPSHOT)

**Purpose:** Projectile/entity state

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct EntityData
{
    public UInt32 UniqueID;         // Offset: 0, Size: 4 bytes
                                    // Entity ID

    public UInt32 EntityType;       // Offset: 4, Size: 4 bytes
                                    // Elemental spell index
                                    // (Elemental << 5 | spellType)

    public UInt32 EntityPlayer;     // Offset: 8, Size: 4 bytes
                                    // Owner player ID

    public UInt32 frameNumber;      // Offset: 12, Size: 4 bytes
                                    // Spawn frame

    public byte EntityState;        // Offset: 16, Size: 1 byte
                                    // 0=Active, 1=Hit, 2=Expired

    public float SourceLocationX;   // Offset: 17, Size: 4 bytes
                                    // Start X position

    public float SourceLocationY;   // Offset: 21, Size: 4 bytes
                                    // Start Y/Z position

    public float EntityEndLocationX;// Offset: 25, Size: 4 bytes
                                    // Target/end X

    public float EntityEndLocationY;// Offset: 29, Size: 4 bytes
                                    // Target/end Y

    public byte hasExtendedInfo;    // Offset: 33, Size: 1 byte
                                    // 1 = EntityDataEx follows
}
// Total Size: 34 bytes
```

### 4.6 EntityDataEx (Extended Entity Info)

**Purpose:** Additional entity info when needed

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct EntityDataEx
{
    public byte EntityType;      // Offset: 0, Size: 1 byte
                                 // Additional type info

    public UInt32 EntityTarget;  // Offset: 1, Size: 4 bytes
                                 // Target player ID
}
// Total Size: 5 bytes
```

### 4.7 LogData (LOGDATA - 0x1406)

**Purpose:** Combat log event

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct LogData
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1406

    public UInt32 targetPlayer;  // Offset: 2, Size: 4 bytes
                                 // Player receiving effect

    public UInt32 sourcePlayer;  // Offset: 6, Size: 4 bytes
                                 // Player causing effect

    public float damage;         // Offset: 10, Size: 4 bytes
                                 // Damage/heal amount

    public byte LogType;         // Offset: 14, Size: 1 byte
                                 // 0=Damage, 1=Heal, 2=Shield, 3=Death

    public byte DamageType;      // Offset: 15, Size: 1 byte
                                 // DamageType enum

    public byte EffectType;      // Offset: 16, Size: 1 byte
                                 // EffectType enum

    public UInt16 playerStamina; // Offset: 17, Size: 2 bytes
                                 // Target's stamina after

    public float shieldHealth;   // Offset: 19, Size: 4 bytes
                                 // Shield remaining HP
}
// Total Size: 23 bytes
```

**LogType Values:**
```
0 = Damage dealt
1 = Healing
2 = Shield block
3 = Death
4 = Respawn
5 = Effect applied
6 = Effect removed
```

### 4.8 MatchOver_Data (ENDGAMEDATA - 0x1407)

**Purpose:** Match results

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchOver_Data
{
    public UInt16 packetType;       // Offset: 0, Size: 2 bytes
                                    // Value: 0x1407

    public byte winningTeam;        // Offset: 2, Size: 1 byte
                                    // 1 or 2

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 6)]
    public UInt32[] playerOrder;    // Offset: 3, Size: 24 bytes
                                    // Players sorted by performance

    public byte karmaPlayerCount;   // Offset: 27, Size: 1 byte
                                    // Players eligible for karma

    [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
    public UInt32[] karmaPlayers;   // Offset: 28, Size: 20 bytes
                                    // Players to vote karma for

    public UInt32 karmaGivingPlayer;// Offset: 48, Size: 4 bytes
                                    // Player giving karma

    public UInt16 damageMeleeDealt; // Offset: 52, Size: 2 bytes
                                    // Your melee damage dealt

    public UInt16 damageMeleeReceived;// Offset: 54, Size: 2 bytes

    public UInt16 damageSpellDealt; // Offset: 56, Size: 2 bytes

    public UInt16 damageSpellReceived;// Offset: 58, Size: 2 bytes

    public UInt16 damageMeleeBlocked;// Offset: 60, Size: 2 bytes

    public UInt16 damageSpellBlocked;// Offset: 62, Size: 2 bytes

    // Client version adds:
    public UInt16 damageAstraDealt; // Offset: 64, Size: 2 bytes

    public UInt16 damageAstraReceived;// Offset: 66, Size: 2 bytes

    public UInt16 damageAstraBlocked;// Offset: 68, Size: 2 bytes
}
// Total Size: 70 bytes (client), 64 bytes (server)
```

### 4.9 MatchStateInfo (MATCHSTATEINFO - 0x1408)

**Purpose:** Match state transition

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct MatchStateInfo
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1408

    public byte timeRemaining;   // Offset: 2, Size: 1 byte
                                 // Countdown seconds

    public byte matchState;      // Offset: 3, Size: 1 byte
                                 // MatchStates enum:
                                 // 0=NONE, 1=PREMATCH, 2=TELEPORT
                                 // 3=MATCH, 4=ENDMATCH, 5=POSTMATCH
                                 // 6=END
}
// Total Size: 4 bytes
```

### 4.10 ForfeitMatch (FORFEITMATCH - 0x140A)

**Purpose:** Player forfeit notification

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct ForfeitMatch
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x140A

    public byte reason;          // Offset: 2, Size: 1 byte
                                 // 0=Quit, 1=AFK, 2=Disconnect
}
// Total Size: 3 bytes
```

---

## 5. Log Packets

### 5.1 SimulationFailLog

**Purpose:** Debug: Position prediction failed

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct SimulationFailLog
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1406

    public byte logType;         // Offset: 2, Size: 1 byte
                                 // Log category

    public UInt32 frameNumber;   // Offset: 3, Size: 4 bytes
                                 // Tick where fail occurred

    public float curX;           // Offset: 7, Size: 4 bytes
                                 // Predicted X

    public float curY;           // Offset: 11, Size: 4 bytes
                                 // Predicted Y

    public float realX;          // Offset: 15, Size: 4 bytes
                                 // Authoritative X

    public float realY;          // Offset: 19, Size: 4 bytes
                                 // Authoritative Y

    public byte state;           // Offset: 23, Size: 1 byte
                                 // State at time of fail

    public byte moveSpeed;       // Offset: 24, Size: 1 byte
                                 // Move speed at time
}
// Total Size: 25 bytes
```

### 5.2 StateMismatchLog

**Purpose:** Debug: State prediction failed

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct StateMismatchLog
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1406

    public byte logType;         // Offset: 2, Size: 1 byte

    public UInt32 frameNumber;   // Offset: 3, Size: 4 bytes
                                 // Tick where mismatch occurred

    public byte curState;        // Offset: 7, Size: 1 byte
                                 // Predicted state

    public byte realState;       // Offset: 8, Size: 1 byte
                                 // Authoritative state
}
// Total Size: 9 bytes
```

### 5.3 StateChangeLog

**Purpose:** Debug: State transition log

```csharp
[StructLayout(LayoutKind.Sequential, Pack = 1)]
public struct StateChangeLog
{
    public UInt16 packetType;    // Offset: 0, Size: 2 bytes
                                 // Value: 0x1406

    public byte logType;         // Offset: 2, Size: 1 byte

    public UInt32 frameNumber;   // Offset: 3, Size: 4 bytes

    public byte curState;        // Offset: 7, Size: 1 byte
                                 // Previous state

    public byte newState;        // Offset: 8, Size: 1 byte
                                 // New state
}
// Total Size: 9 bytes
```

---

## 6. World Snapshot Format

### 6.1 Snapshot Structure

The WORLDSNAPSHOT (0x1403) packet contains:

```
┌────────────────────────────────────────────────────────────────┐
│  Header (2 bytes)                                              │
├────────────────────────────────────────────────────────────────┤
│  packetType: UInt16 = 0x1403                                   │
├────────────────────────────────────────────────────────────────┤
│  Player Count (1 byte)                                         │
├────────────────────────────────────────────────────────────────┤
│  See_MoveCharacter[playerCount] (49 bytes each)               │
├────────────────────────────────────────────────────────────────┤
│  Entity Count (1 byte)                                         │
├────────────────────────────────────────────────────────────────┤
│  EntityData[entityCount] (34 bytes each)                      │
│  + EntityDataEx (5 bytes each, if hasExtendedInfo == 1)       │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Snapshot Size Calculation

```
Minimum (0 players, 0 entities):
  2 (header) + 1 (player count) + 1 (entity count) = 4 bytes

6v6 Match (6 players, 0 entities):
  2 + 1 + (6 * 49) + 1 + 0 = 298 bytes

6v6 with 10 entities:
  2 + 1 + (6 * 49) + 1 + (10 * 34) = 638 bytes

Max with extended info (6 players, 20 entities with extended):
  2 + 1 + (6 * 49) + 1 + (20 * 34) + (20 * 5) = 1078 bytes
```

### 6.3 Snapshot Processing (Client)

```csharp
// NetworkManager.cs / ServerManager.cs
void ProcessWorldSnapshot(byte[] data)
{
    int offset = 2; // Skip packet type

    byte playerCount = data[offset++];
    for (int i = 0; i < playerCount; i++)
    {
        See_MoveCharacter playerState = Serializer.DeserializeAt<See_MoveCharacter>(data, offset);
        offset += 49;

        // Apply to local player or interpolate for others
        if (playerState.pUniqueID == myUniqueID)
        {
            // Compare with prediction, reconcile if needed
            SimulationManager.Reconcile(playerState);
        }
        else
        {
            // Update other player's visual state
            otherPlayer.Interpolate(playerState);
        }
    }

    byte entityCount = data[offset++];
    for (int i = 0; i < entityCount; i++)
    {
        EntityData entity = Serializer.DeserializeAt<EntityData>(data, offset);
        offset += 34;

        if (entity.hasExtendedInfo == 1)
        {
            EntityDataEx extended = Serializer.DeserializeAt<EntityDataEx>(data, offset);
            offset += 5;
        }

        EntityManager.UpdateEntity(entity);
    }
}
```

---

## 7. Input Processing

### 7.1 Server Input Processing

```csharp
// PlayerManager.cs
void ProcessPlayerInputTick(Player player, Packet.TickInput input)
{
    // 1. Decode joystick
    (int x, int y) = DecodeJoystick(input.JoystickAxis);

    // 2. Check if state allows movement
    if (!player.stateManager.IsBlockingInput(BlockFlags.Block_JoystickAxis))
    {
        ApplyMovement(player, x, y, input.cameraRotation);
    }

    // 3. Process ability inputs
    ProcessAbilities(player, input);

    // 4. Update state tick
    player.currentTick = input.currentTick;

    // 5. Check for prediction verification
    if (NeedSimulationResult(player, input))
    {
        SendSimulationResult(player);
    }
}

void ProcessAbilities(Player player, Packet.TickInput input)
{
    // Melee
    if (input.meleeAbility == 1) // Just pressed
    {
        if (!player.stateManager.IsBlockingInput(BlockFlags.Block_Melee))
        {
            player.TryMelee();
        }
    }

    // Elemental 1-4
    if (input.elementalAbility1 == 1)
    {
        if (!player.stateManager.IsBlockingInput(BlockFlags.Block_Elemental_Spell))
        {
            player.CastElemental(0, input.abilityX, input.abilityY);
        }
    }
    // ... repeat for elementalAbility2-4

    // Special ability
    if (input.specialAbility == 1)
    {
        if (!player.stateManager.IsBlockingInput(BlockFlags.Block_Unique))
        {
            player.UseSpecialAbility(input.abilityX, input.abilityY);
        }
    }

    // Dodge
    if (input.dodgeAbility == 1)
    {
        if (!player.stateManager.IsBlockingInput(BlockFlags.Block_Dodge))
        {
            player.Dodge();
        }
    }

    // Astra (Ultimate)
    if (input.astraAbility == 1)
    {
        if (!player.stateManager.IsBlockingInput(BlockFlags.Block_Astra))
        {
            player.UseAstra();
        }
    }
}
```

### 7.2 Input Timing

```
Client Frame N:
  1. Capture input
  2. Create TickInput packet
  3. Apply locally (prediction)
  4. Send to server

Server receives (variable latency):
  1. Queue input
  2. Process in next FastLoop
  3. Update authoritative state
  4. Include in next world snapshot

Client Frame N+RTT/2:
  1. Receive world snapshot
  2. Compare with prediction
  3. Reconcile if needed
```

---

## 8. Byte Layout Reference

### 8.1 All Packet Sizes

| Packet | ID | Size (bytes) | Direction |
|--------|-----|--------------|-----------|
| GracefullDC | 0x1400 | 3 | Both |
| Authenticate_Player | 0x1401 | 18 | C→S |
| Authenticate_PlayerReply | 0x1401 | 18 | S→C |
| RemoveCharacter | 0x1402 | 6 | S→C |
| TickInput | 0x1403 | 34 | C→S |
| WorldSnapshot | 0x1403 | 4-1078 | S→C |
| SimulationResult | 0x1404 | 23 | S→C |
| RespawnCharacter | 0x1405 | 6 | Both |
| LogData | 0x1406 | 23 | Both |
| SimulationFailLog | 0x1406 | 25 | C→S |
| StateMismatchLog | 0x1406 | 9 | C→S |
| StateChangeLog | 0x1406 | 9 | C→S |
| MatchOver_Data | 0x1407 | 64-70 | S→C |
| MatchStateInfo | 0x1408 | 4 | S→C |
| PlayerKarma | 0x1409 | 11 | Both |
| ForfeitMatch | 0x140A | 3 | S→C |
| Tutorial_Progress | 0x140B | 10 | Both |

### 8.2 Nested Structure Sizes

| Structure | Size (bytes) | Used In |
|-----------|--------------|---------|
| See_MoveCharacter | 49 | WorldSnapshot |
| EntityData | 34 | WorldSnapshot |
| EntityDataEx | 5 | WorldSnapshot |

### 8.3 Complete TickInput Byte Map

```
Byte  Field              Type    Notes
────  ─────────────────  ──────  ─────────────────────────────────
0     JoystickAxis       byte    X=high nibble, Y=low nibble
1-4   cameraRotation     float   Little-endian
5-8   currentTick        uint32  Little-endian
9-12  serverTick         uint32  Little-endian
13-16 state              uint32  StateType enum
17    specialAbility     byte    0/1/2/3
18-21 abilityX           float   Little-endian
22-25 abilityY           float   Little-endian
26    meleeAbility       byte    0/1/2/3
27    abilityEx          byte    Extended flags
28    elementalAbility1  byte    Fire slot
29    elementalAbility2  byte    Water slot
30    elementalAbility3  byte    Air slot
31    elementalAbility4  byte    Earth/Ether slot
32    dodgeAbility       byte    0/1/2/3
33    astraAbility       byte    0/1/2/3
────────────────────────────────────────────────────────────────
Total: 34 bytes
```

### 8.4 Complete See_MoveCharacter Byte Map

```
Byte   Field              Type    Notes
─────  ─────────────────  ──────  ─────────────────────────────────
0-3    pUniqueID          uint32  Player ID
4      JoystickAxis       byte    Current movement
5-8    cameraRotation     float   Camera Y angle
9-12   positionX          float   World X
13-16  positionZ          float   World Z
17-20  state              uint32  StateType enum
21-24  abilityX           float   Aim X
25-28  abilityY           float   Aim Y
29-32  abilityRotation    float   Ability facing
33-34  currStamina        uint16  0-1000
35-36  willPower          uint16  0-1000
37-38  currFocus          uint16  Focus meter
39-42  impactIndicator    uint32  Damage flags
43-46  impactMeleePlayer  uint32  Melee hit target
47     attributeEx        byte    Shield/buff flags
48     activeElemental    byte    Active elemental
─────────────────────────────────────────────────────────────────
Total: 49 bytes
```

---

**Document Info:**
- Total Packet Types: 12
- Lines: ~1100
- Created: January 21, 2026
- Part: 3 of 11

---

*End of UDP Packets Document*
