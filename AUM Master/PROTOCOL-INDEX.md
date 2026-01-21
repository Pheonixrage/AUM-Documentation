# AUM Protocol Documentation - Master Index

> **Version:** 1.3
> **Last Updated:** January 21, 2026
> **Total Documents:** 18
> **Total Lines of Documentation:** ~23,500+

---

## Document Overview

| # | Document | Description | Lines | Key Contents |
|---|----------|-------------|-------|--------------|
| 1 | [PROTOCOL-1-OVERVIEW.md](PROTOCOL-1-OVERVIEW.md) | Architecture & Flows | ~800 | System architecture, connection flows, 4 protocol layers |
| 2 | [PROTOCOL-2-WSS-PACKETS.md](PROTOCOL-2-WSS-PACKETS.md) | WebSocket Structures | ~2,000 | 83 WSS structs with byte layouts |
| 3 | [PROTOCOL-3-UDP-PACKETS.md](PROTOCOL-3-UDP-PACKETS.md) | In-Game Packets | ~1,500 | All UDP packet structures |
| 4 | [PROTOCOL-4-MATCHKEEPER.md](PROTOCOL-4-MATCHKEEPER.md) | MatchKeeper Protocol | ~1,000 | MK TCP:6767 authentication |
| 5 | [PROTOCOL-5-PLAYFAB.md](PROTOCOL-5-PLAYFAB.md) | PlayFab Services | ~1,400 | 13 services, 7,364 lines of code |
| 6 | [PROTOCOL-6-STATE-MACHINES.md](PROTOCOL-6-STATE-MACHINES.md) | FSM Implementation | ~1,200 | 31 states, BlockFlags, transitions |
| 7 | [PROTOCOL-7-GAME-DATA.md](PROTOCOL-7-GAME-DATA.md) | Attributes & Bonuses | ~1,000 | Fighter stats, God bonuses, Focus |
| 8 | [PROTOCOL-8-CHARACTERS.md](PROTOCOL-8-CHARACTERS.md) | Character Implementations | ~1,500 | All 5 fighters with code |
| 9 | [PROTOCOL-9-SPELLS.md](PROTOCOL-9-SPELLS.md) | Spell System | ~1,800 | 5 elements, effects, shields |
| 10 | [PROTOCOL-10-ENUMS.md](PROTOCOL-10-ENUMS.md) | Enum Reference | ~1,200 | 70+ enums with all values |
| 11 | [PROTOCOL-11-BOT-AI.md](PROTOCOL-11-BOT-AI.md) | Bot AI System | ~1,000 | Behavior tree, action nodes, bot states |
| 12 | [PROTOCOL-12-ENTITIES.md](PROTOCOL-12-ENTITIES.md) | Entity System | ~1,850 | Projectiles, astras, damage calculation |
| 13 | [PROTOCOL-13-MAPS.md](PROTOCOL-13-MAPS.md) | Map Configuration | ~400 | Arena configs, spawn system, tutorial |
| 14 | [PROTOCOL-14-SERVER-SYSTEMS.md](PROTOCOL-14-SERVER-SYSTEMS.md) | Server Managers | ~900 | PlayerManager, CastManager, PrefabManager |
| 15 | [PROTOCOL-15-DIAGNOSTICS.md](PROTOCOL-15-DIAGNOSTICS.md) | Logging & Telemetry | ~520 | ClientLog, DebugLogTracker, AUMFileLogger |
| 16 | [PROTOCOL-16-SHIELDS.md](PROTOCOL-16-SHIELDS.md) | Shield System | ~450 | ElementalShield mechanics, interactions |
| 17 | [PROTOCOL-17-UTILITIES.md](PROTOCOL-17-UTILITIES.md) | Utility Systems | ~450 | FInt, FileHandler, JitterCompensator |
| 18 | [PROTOCOL-18-SUPPLEMENTARY.md](PROTOCOL-18-SUPPLEMENTARY.md) | Supplementary Systems | ~950 | ServerAllocator, Lobby, Party, Friends, Camera, Audio |
| — | PROTOCOL-INDEX.md | This Document | ~350 | Master index and quick reference |

---

## Quick Navigation

### By Topic

#### Networking
- **Connection Flow** → [PROTOCOL-1-OVERVIEW.md#connection-flow](PROTOCOL-1-OVERVIEW.md#connection-flow)
- **WebSocket Messages** → [PROTOCOL-2-WSS-PACKETS.md](PROTOCOL-2-WSS-PACKETS.md)
- **UDP Game Packets** → [PROTOCOL-3-UDP-PACKETS.md](PROTOCOL-3-UDP-PACKETS.md)
- **MatchKeeper Auth** → [PROTOCOL-4-MATCHKEEPER.md](PROTOCOL-4-MATCHKEEPER.md)
- **Network Enums** → [PROTOCOL-10-ENUMS.md#5-network--packet-enums](PROTOCOL-10-ENUMS.md#5-network--packet-enums)

#### Backend Services
- **PlayFab Integration** → [PROTOCOL-5-PLAYFAB.md](PROTOCOL-5-PLAYFAB.md)
- **Authentication** → [PROTOCOL-5-PLAYFAB.md#1-playFabauthservice](PROTOCOL-5-PLAYFAB.md#1-playfabauthservice)
- **Inventory** → [PROTOCOL-5-PLAYFAB.md#4-playfabinventoryservice](PROTOCOL-5-PLAYFAB.md#4-playfabinventoryservice)
- **Matchmaking** → [PROTOCOL-5-PLAYFAB.md#6-playfabmatchmaker](PROTOCOL-5-PLAYFAB.md#6-playfabmatchmaker)

#### Gameplay Systems
- **State Machine** → [PROTOCOL-6-STATE-MACHINES.md](PROTOCOL-6-STATE-MACHINES.md)
- **Character Data** → [PROTOCOL-7-GAME-DATA.md](PROTOCOL-7-GAME-DATA.md)
- **Character Classes** → [PROTOCOL-8-CHARACTERS.md](PROTOCOL-8-CHARACTERS.md)
- **Spell System** → [PROTOCOL-9-SPELLS.md](PROTOCOL-9-SPELLS.md)
- **Shield System** → [PROTOCOL-16-SHIELDS.md](PROTOCOL-16-SHIELDS.md)
- **Bot AI** → [PROTOCOL-11-BOT-AI.md](PROTOCOL-11-BOT-AI.md)
- **Entities & Projectiles** → [PROTOCOL-12-ENTITIES.md](PROTOCOL-12-ENTITIES.md)
- **Maps & Spawns** → [PROTOCOL-13-MAPS.md](PROTOCOL-13-MAPS.md)

#### Server Systems
- **Player Management** → [PROTOCOL-14-SERVER-SYSTEMS.md#1-playermanager](PROTOCOL-14-SERVER-SYSTEMS.md#1-playermanager)
- **Cast Management** → [PROTOCOL-14-SERVER-SYSTEMS.md#2-castmanager](PROTOCOL-14-SERVER-SYSTEMS.md#2-castmanager)
- **Prefab Management** → [PROTOCOL-14-SERVER-SYSTEMS.md#3-prefabmanager](PROTOCOL-14-SERVER-SYSTEMS.md#3-prefabmanager)

#### Diagnostics & Logging
- **Client Debug Logs** → [PROTOCOL-15-DIAGNOSTICS.md#1-clientlog-system](PROTOCOL-15-DIAGNOSTICS.md#1-clientlog-system)
- **Debug Log Tracker** → [PROTOCOL-15-DIAGNOSTICS.md#2-debuglogtracker](PROTOCOL-15-DIAGNOSTICS.md#2-debuglogtracker)
- **Combat Telemetry** → [PROTOCOL-15-DIAGNOSTICS.md#4-utils-combat-logging](PROTOCOL-15-DIAGNOSTICS.md#4-utils-combat-logging)

#### Utilities
- **Fixed-Point Math** → [PROTOCOL-17-UTILITIES.md#1-fint-fixed-point-integer](PROTOCOL-17-UTILITIES.md#1-fint-fixed-point-integer)
- **File Handling** → [PROTOCOL-17-UTILITIES.md#2-filehandler](PROTOCOL-17-UTILITIES.md#2-filehandler)
- **Jitter Compensation** → [PROTOCOL-17-UTILITIES.md#3-jittercompensator](PROTOCOL-17-UTILITIES.md#3-jittercompensator)

#### Server Allocation
- **Server Allocator** → [PROTOCOL-18-SUPPLEMENTARY.md#1-serverallocator](PROTOCOL-18-SUPPLEMENTARY.md#1-serverallocator)

#### Social & Lobby Systems
- **Lobby Manager** → [PROTOCOL-18-SUPPLEMENTARY.md#2-lobbymanager](PROTOCOL-18-SUPPLEMENTARY.md#2-lobbymanager)
- **Party Manager** → [PROTOCOL-18-SUPPLEMENTARY.md#3-partymanager](PROTOCOL-18-SUPPLEMENTARY.md#3-partymanager)
- **Friends Manager** → [PROTOCOL-18-SUPPLEMENTARY.md#4-friendsmanager](PROTOCOL-18-SUPPLEMENTARY.md#4-friendsmanager)
- **Server Manager** → [PROTOCOL-18-SUPPLEMENTARY.md#5-servermanager](PROTOCOL-18-SUPPLEMENTARY.md#5-servermanager)

#### Visual & Audio Systems
- **Camera Controller** → [PROTOCOL-18-SUPPLEMENTARY.md#8-cameracontroller](PROTOCOL-18-SUPPLEMENTARY.md#8-cameracontroller)
- **Camera Shake** → [PROTOCOL-18-SUPPLEMENTARY.md#9-camerashake](PROTOCOL-18-SUPPLEMENTARY.md#9-camerashake)
- **Audio Manager** → [PROTOCOL-18-SUPPLEMENTARY.md#11-audiomanager](PROTOCOL-18-SUPPLEMENTARY.md#11-audiomanager)
- **Scene Loader** → [PROTOCOL-18-SUPPLEMENTARY.md#6-sceneloader](PROTOCOL-18-SUPPLEMENTARY.md#6-sceneloader)

#### Development Tools
- **Test Mode Client** → [PROTOCOL-18-SUPPLEMENTARY.md#5-testmodeclient](PROTOCOL-18-SUPPLEMENTARY.md#5-testmodeclient)

---

## Key Reference Tables

### Protocol Layers

| Layer | Transport | Port | Purpose |
|-------|-----------|------|---------|
| **WSS** | WebSocket | 443 | Lobby, matchmaking, chat |
| **MK** | TCP | 6767 | Match authentication |
| **UDP** | LiteNetLib | 6006 | In-game data @ 60Hz |
| **HTTPS** | REST | 443 | PlayFab services |

### Fighting Styles Summary

| Style | Weapon | Type | Special |
|-------|--------|------|---------|
| **Amuktha** | Sword | Melee | Dash |
| **MukthaMuktha** | Axe | Melee | Throw/Recall |
| **MantraMuktha** | Staff | Ranged | Teleport |
| **PaniMuktha** | Discus | Ranged | Throw |
| **YantraMuktha** | Bow | Ranged | Arrow Special |

**Details:** [PROTOCOL-8-CHARACTERS.md](PROTOCOL-8-CHARACTERS.md)

### Trinity Gods Summary

| God | Ultimate | Passive Bonus |
|-----|----------|---------------|
| **Brahma** | Brahmastra | Shield abilities, +3 focus streak |
| **Shiva** | Shivastra | Third Eye immunity, +20% damage |
| **Vishnu** | Narayanastra | +30% move speed, stamina discount |

**Details:** [PROTOCOL-7-GAME-DATA.md#god-bonuses](PROTOCOL-7-GAME-DATA.md)

### Elemental System Summary

| Element | Effect | Damage Type | Shield Interaction |
|---------|--------|-------------|-------------------|
| **Fire** | Burn DoT | FIRE | Vulnerable to Water |
| **Water** | Pushback | WATER | Vulnerable to Earth |
| **Air** | Slow | AIR | Vulnerable to Fire |
| **Earth** | Stun | EARTH | Vulnerable to Ether |
| **Ether** | Mute | ETHER | Vulnerable to Air |

**Details:** [PROTOCOL-9-SPELLS.md](PROTOCOL-9-SPELLS.md)

### State Machine Overview

| Category | Count | Examples |
|----------|-------|----------|
| **Combat States** | 12 | Melee, Aiming, Cast_Spell |
| **Defensive States** | 5 | Shield_Block, Dodge, Stun |
| **Ultimate States** | 3 | Astra_Anticipate, Astra_Channel, Astra_Cast |
| **Movement States** | 3 | Idle, Jump, Teleport |
| **Special States** | 8 | Death, Victory, Third_Eye |

**Details:** [PROTOCOL-6-STATE-MACHINES.md](PROTOCOL-6-STATE-MACHINES.md)

---

## Encoding Reference

### Spell Index Encoding
```
16-bit: [Element(3)] [SpellType(5)]
Formula: (Elemental << 5) | spellType
```

### Item Code Encoding
```
32-bit: [FightingStyle(4)] [FighterClass(1)] [ItemType(4)] [Identifier(23)]
```

### BlockFlags Bitmask
```
Bit 0: Elemental_Spell    (1)
Bit 1: JoystickAxis       (2)
Bit 2: Melee              (4)
Bit 3: Camera             (8)
Bit 4: Astra              (16)
Bit 5: Shield             (32)
Bit 6: ThirdEye           (64)
Bit 7: Unique             (128)
Bit 8: Elemental_Shield   (256)
Bit 9: Dodge              (512)
Bit 10: Jump              (1024)
BlockAll: 2047
```

---

## Match Flow Reference

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MATCH LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. NONE          → Waiting for connection                           │
│       │                                                              │
│       ▼                                                              │
│  2. PREGAME       → 5 second countdown                              │
│       │                                                              │
│       ▼                                                              │
│  3. TELEPORT      → Players spawn/teleport to positions             │
│       │                                                              │
│       ▼                                                              │
│  4. MATCHRUNNING  → COMBAT ACTIVE (60Hz tick rate)                  │
│       │                                                              │
│       ▼                                                              │
│  5. ENDMATCH      → Winner determined                               │
│       │                                                              │
│       ▼                                                              │
│  6. POSTMATCH     → Results, rewards calculation                    │
│       │                                                              │
│       ▼                                                              │
│  7. END           → Cleanup, disconnect                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Details:** [PROTOCOL-6-STATE-MACHINES.md#match-state-machine](PROTOCOL-6-STATE-MACHINES.md)

---

## Currency Codes

| Code | Currency | Purpose |
|------|----------|---------|
| BZ | Bronze | Basic currency |
| SV | Silver | Premium currency |
| GD | Gold | Rare currency |
| LV | Lives | Match entry |
| TS | Time Shards | Limited events |
| HS | Hell Shards | Special events |
| BT | Bhakti Tokens | Progression |
| GT | Gnana Tokens | Progression |

**Details:** [PROTOCOL-5-PLAYFAB.md#currency-codes](PROTOCOL-5-PLAYFAB.md)

---

## File Structure Reference

### Client Repository (AUM-Unity-Staging-Legacy)
```
Assets/
├── Scripts/
│   ├── Auth/                  # Authentication (AUMAuthManager)
│   ├── Camera/                # Camera systems
│   ├── Managers/              # Core managers
│   │   ├── GameManager.cs     # Match state machine
│   │   ├── NetworkManager.cs  # UDP/LiteNetLib
│   │   ├── InputManager.cs    # Input handling
│   │   └── ...
│   ├── Network/               # Packet structures
│   ├── Player/                # Player classes
│   │   ├── ControllerBase.cs  # FSM states
│   │   └── Characters/        # 5 fighting styles
│   ├── PlayFab/               # 13 PlayFab services
│   ├── StateMachine/          # FSM implementation
│   └── UI/                    # UI systems
└── ScriptableObjects/         # Data assets
```

### Server Repository (AUM-Unity-Server-Legacy)
```
Assets/
├── Scripts/
│   ├── Bots/                  # Bot AI
│   ├── Managers/              # Server managers
│   ├── MatchState.cs          # Match lifecycle
│   ├── Network/               # Server packets
│   ├── Player/                # Server player logic
│   │   ├── Characters/        # Character implementations
│   │   └── ElementalShield.cs # Shield system
│   ├── Spells/                # Spell implementations
│   │   ├── Fire.cs, Water.cs, etc.
│   │   └── Effects/           # Status effects
│   └── StateMachine/          # Server FSM
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 21, 2026 | Initial complete documentation (10 documents) |
| 1.1 | Jan 21, 2026 | Added Bot AI, Entities, Maps documentation (13 total) |
| 1.2 | Jan 21, 2026 | Added Server Systems, Diagnostics, Shields, Utilities (17 total) |
| 1.3 | Jan 21, 2026 | Added Supplementary Systems - Social, Camera, Audio (18 total) |

---

## Document Maintenance

### Updating Documentation
When game code changes, update the relevant protocol document:

1. **New packets** → Update PROTOCOL-2 (WSS) or PROTOCOL-3 (UDP)
2. **New states** → Update PROTOCOL-6 (State Machines)
3. **New enums** → Update PROTOCOL-10 (Enums)
4. **Character changes** → Update PROTOCOL-8 (Characters)
5. **Spell changes** → Update PROTOCOL-9 (Spells)
6. **Shield changes** → Update PROTOCOL-16 (Shields)
7. **PlayFab changes** → Update PROTOCOL-5 (PlayFab)
8. **Server manager changes** → Update PROTOCOL-14 (Server Systems)
9. **Logging changes** → Update PROTOCOL-15 (Diagnostics)
10. **Utility changes** → Update PROTOCOL-17 (Utilities)
11. **Social/Lobby/Camera changes** → Update PROTOCOL-18 (Supplementary)

### Source Code References
All documentation is derived from:
- `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy/` (Client)
- `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/` (Server)

---

*This index provides quick access to all AUM protocol documentation.*
*For detailed information, navigate to the specific document.*
