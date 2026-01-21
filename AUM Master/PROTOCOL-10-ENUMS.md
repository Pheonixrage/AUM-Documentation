# PROTOCOL-10-ENUMS.md
# AUM Complete Enum Reference

> **Document Version:** 1.0
> **Last Updated:** January 21, 2026
> **Total Enums:** 70+
> **Source:** Client and Server codebases

---

## Table of Contents

1. [Core Game Enums](#1-core-game-enums)
2. [State Machine Enums](#2-state-machine-enums)
3. [Combat & Damage Enums](#3-combat--damage-enums)
4. [Spell System Enums](#4-spell-system-enums)
5. [Network & Packet Enums](#5-network--packet-enums)
6. [Player & Input Enums](#6-player--input-enums)
7. [UI & Visual Enums](#7-ui--visual-enums)
8. [System & Configuration Enums](#8-system--configuration-enums)

---

## 1. Core Game Enums

### FightingStyles
**Source:** `Enum.cs`
```csharp
public enum FightingStyles
{
    Amuktha = 0,        // Sword - Close-range melee
    MantraMuktha = 1,   // Staff - Ranged magic
    MukthaMuktha = 2,   // Axe - Close-range with throw
    PaniMuktha = 3,     // Discus - Ranged throw
    YantraMuktha = 4    // Bow - Ranged archer
}
```

### TrinityGods
**Source:** `Enum.cs`
```csharp
public enum TrinityGods
{
    Brahma = 0,   // Shield abilities, +3 focus streak start
    Shiva = 1,    // Third Eye immunity, +20% damage
    Vishnu = 2    // +30% movement speed, stamina discount
}
```

### Elementals
**Source:** `Enum.cs`
```csharp
public enum Elementals
{
    FIRE = 0,
    WATER = 1,
    AIR = 2,
    ETHER = 3,
    EARTH = 4
}
```

### MatchType
**Source:** `Enum.cs`
```csharp
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
    NONE        = 1 << 9    // 512
}
```

### Karma
**Source:** `Player.cs`
```csharp
public enum Karma
{
    Sattva = 0,   // Good karma
    Rajas = 1,    // Neutral karma
    Tamas = 2     // Bad karma
}
```

---

## 2. State Machine Enums

### FSM.StateType
**Source:** `StateManager.cs`
```csharp
namespace FSM
{
    public enum StateType
    {
        Idle = 0,
        Melee = 1,
        Try_Shield_Block = 2,
        Shield_Block = 3,
        Shield_Attack = 4,
        Aiming = 5,
        Spell_Aiming = 6,
        Channel = 7,
        Cast_Spell = 8,
        Spell_Anticipate = 9,
        Special = 10,
        Special_Aiming = 11,
        Axe_Callback = 12,
        State_Unused = 13,
        Death = 14,
        Cast_Shield = 15,
        Water_Pushback = 16,
        Pushback_Land = 17,
        Special_Anticipate = 18,
        Stun = 19,
        Melee_Second = 20,
        Third_Eye = 21,
        Third_Eye_Anticipate = 22,
        Dodge = 23,
        Astra_Anticipate = 24,
        Astra_Channel = 25,
        Astra_Cast = 26,
        Jump = 27,
        Teleport = 28,
        Vulnerable = 29,
        Victory = 30,
        Undefined = 31
    }
}
```

### BlockFlags
**Source:** `StateManager.cs`
```csharp
public enum BlockFlags
{
    Block_Elemental_Spell  = 1 << 0,   // 1
    Block_JoystickAxis     = 1 << 1,   // 2
    Block_Melee            = 1 << 2,   // 4
    Block_Camera           = 1 << 3,   // 8
    Block_Astra            = 1 << 4,   // 16
    Block_Shield           = 1 << 5,   // 32
    Block_ThirdEye         = 1 << 6,   // 64
    Block_Unique           = 1 << 7,   // 128
    Block_Elemental_Shield = 1 << 8,   // 256
    Block_Dodge            = 1 << 9,   // 512
    Block_Jump             = 1 << 10,  // 1024
    BlockAll               = 2047      // All flags combined
}
```

### StateBlockFlags
**Source:** `StateManager.cs`
```csharp
public enum StateBlockFlags
{
    Idle             = 0,     // No blocks
    Melee            = 2042,  // BlockAll & ~(Joystick | Camera)
    Shield_Attack    = 2042,  // BlockAll & ~(Joystick | Camera)
    Shield_Block     = 2010,  // BlockAll & ~(Joystick | Camera | Shield)
    Aiming           = 2038,  // BlockAll & ~(Joystick | Camera | Melee)
    Spell_Aiming     = 2044,  // BlockAll & ~(Joystick | Camera | Elemental_Spell)
    Channel          = 2042,  // BlockAll & ~(Joystick | Camera)
    Spell_Anticipate = 2047,  // BlockAll
    Cast_Spell       = 2047,  // BlockAll
    Special          = 2047,  // BlockAll
    Special_Aiming   = 1914,  // BlockAll & ~(Joystick | Camera | Unique)
    Axe_Callback     = 1914,  // BlockAll & ~(Joystick | Camera | Unique)
    Death            = 2047,  // BlockAll
    Cast_Shield      = 2042   // BlockAll & ~(Joystick | Camera)
}
```

### MatchStates (Server)
**Source:** `MatchState.cs`
```csharp
public enum MatchStates
{
    NONE = 0,
    PREMATCH = 1,
    TELEPORT = 2,
    MATCH = 3,
    ENDMATCH = 4,
    POSTMATCH = 5,
    END = 6
}
```

### MatchState (Client)
**Source:** `GameManager.cs`
```csharp
public enum MatchState
{
    NONE = 0,
    PREGAME = 1,
    TELEPORT = 2,
    MATCHRUNNING = 3,
    ENDMATCH = 4,
    POSTMATCH = 5,
    END = 6
}
```

### BotState
**Source:** `Bot.cs` / `BotManager.cs`
```csharp
public enum BotState
{
    DISABLED = 0,
    MELEEACTION = 1,
    SPELLMELEEACTION = 2,
    FULL = 3
}
```

### NodeState (Behavior Tree)
**Source:** `Node.cs`
```csharp
public enum NodeState
{
    RUNNING = 0,
    SUCCESS = 1,
    FAILURE = 2
}
```

---

## 3. Combat & Damage Enums

### AttackType
**Source:** `Enum.cs`
```csharp
public enum AttackType
{
    ASTRA = 0,
    ELEMENTAL1 = 1,
    ELEMENTAL2 = 2,
    ELEMENTAL3 = 3,
    ELEMENTAL4 = 4,
    THIRDEYE = 5,
    UNIQUE = 6,
    MELEE = 7,
    BRAHMASHIELD = 8,
    DODGE = 9,
    NONE = 10
}
```

### DamageType
**Source:** `Enum.cs`
```csharp
public enum DamageType
{
    NONE = 0,
    MELEE = 1,
    AXETHROW = 2,
    THIRDEYE = 3,
    FIRE = 4,
    WATER = 5,
    AIR = 6,
    ETHER = 7,
    EARTH = 8,
    ASTRA_BRAHMA = 9,
    ASTRA_VISHNU = 10,
    ASTRA_SHIVA = 11
}
```

### WeaponType
**Source:** `Enum.cs`
```csharp
public enum WeaponType
{
    Sword = 0,
    Axe = 1,
    Bow = 2,
    Chakra = 3,   // Discus
    Magic = 4,    // Staff
    None = 5
}
```

### AttackCharge
**Source:** `Enum.cs`
```csharp
public enum AttackCharge
{
    Basic = 0,
    Charged = 1
}
```

### AttackDamageComponent
**Source:** `Enum.cs`
```csharp
public enum AttackDamageComponent
{
    Physical = 0,    // Melee/ranged weapon
    Astra = 1,       // Ultimate ability
    SpellBurst = 2,  // Single big burst
    SpellZone = 3,   // Zone ticks
    SpellDoT = 4     // Effect DoT ticks
}
```

### MeleeImpactType
**Source:** `Enum.cs`
```csharp
public enum MeleeImpactType
{
    Force = 0,
    Slice = 1,
    Pierce = 2,
    ForceAndSlice = 3
}
```

### ImpactIndicatorType
**Source:** `Player.cs`
```csharp
public enum ImpactIndicatorType
{
    BrahmaMelee = 1,
    VishnuMelee = 2,
    ShivaMelee = 3,
    ShieldBlock = 4,
    BrahmaAstra = 5,
    ShivaAstra = 6,
    VishnuAstra = 7
}
```

### Interaction
**Source:** `Enum.cs`
```csharp
public enum Interaction
{
    Nullify = 0,    // 0% damage passes
    Vulnerable = 1, // 100% damage passes
    Mitigate = 2    // 50% damage passes
}
```

### CoatedType
**Source:** `Enum.cs`
```csharp
public enum CoatedType
{
    None = 0,
    Fire = 1,
    Water = 2,
    Air = 3,
    Earth = 4,
    Ether = 5
}
```

### AstraEntityType
**Source:** `AstraManager.cs`
```csharp
public enum AstraEntityType
{
    BRAHMASTRA = 1,
    NARAYANASTRA = 2,
    SHIVASTRA = 3
}
```

### AxeState
**Source:** `MukthaMuktha.cs`
```csharp
public enum AxeState
{
    ONHAND = 0,
    FLYING = 1,
    ONGROUND = 2,
    CALLBACK = 3
}
```

---

## 4. Spell System Enums

### Effects.EffectType
**Source:** `Effects.cs`
```csharp
public enum EffectType
{
    EFFECT_NONE = 0,
    EFFECT_FIREDAMAGE = 1,   // Burning DoT
    EFFECT_AIRSLOW = 2,       // Movement slow
    EFFECT_EARTHSTUN = 3,     // Stun
    EFFECT_ETHERMUTE = 4,     // Silence
    EFFECT_IMPAIR = 5,        // Reduced accuracy
    EFFECT_MAIM = 6,          // Reduced damage
    EFFECT_THIRDEYE = 7,      // Shiva buff
    EFFECT_SHIVAASTRA = 8     // Shiva ultimate burn
}
```

### SpellSubType
**Source:** `Enum.cs`
```csharp
public enum SpellSubType
{
    INSTANT = 0,
    CHANNELING = 1,
    CHARGED = 2,
    TRAPS = 3
}
```

### RangeType
**Source:** `Enum.cs`
```csharp
public enum RangeType
{
    CLOSE_RANGE = 0,
    LONG_RANGE = 1
}
```

### LevelType
**Source:** `Enum.cs`
```csharp
public enum LevelType
{
    Level1 = 0,
    Level2 = 1,
    Level3 = 2
}
```

### SpellDamageMode
**Source:** `Enum.cs`
```csharp
public enum SpellDamageMode
{
    BurstOnly = 0,          // Only burst on cast
    ZoneOnly = 1,           // Only repeated zone ticks
    EffectOnly = 2,         // Only effect/DoT/status
    BurstAndZone = 3,       // Burst + zone
    BurstAndEffect = 4,     // Burst + effect
    ZoneAndEffect = 5,      // Zone + effect
    BurstZoneAndEffect = 6  // All three
}
```

### CastDetectionType
**Source:** `Enum.cs`
```csharp
public enum CastDetectionType
{
    Circle = 0,   // Radius-based area
    Cone = 1,     // Angle-based cone
    Box = 2       // Box/rectangle area
}
```

### SpellDurationType
**Source:** `ShieldManager.cs`
```csharp
public enum SpellDurationType
{
    OneShot = 0,
    Timer = 1
}
```

### ProjectileType
**Source:** `Projectile.cs`
```csharp
public enum ProjectileType
{
    ARROW = 1,
    MAGICBALL = 2,
    DISCUSS = 3    // Discus
}
```

---

## 5. Network & Packet Enums

### PacketTypeIN (Client → Server)
**Source:** `Packet.cs`
```csharp
public enum PacketTypeIN
{
    NETWORKEVENT      = 0x1400,   // 5120
    AUTHENTICATE      = 0x1401,   // 5121
    PLAYERINPUT       = 0x1403,   // 5123
    RESPAWNCHARACTER  = 0x1405,   // 5125
    LOGDATA           = 0x1406,   // 5126
    PLAYERKARMA       = 0x1409,   // 5129
    TUTORIALPROGRESS  = 0x140B    // 5131
}
```

### PacketTypeOUT (Server → Client)
**Source:** `Packet.cs`
```csharp
public enum PacketTypeOUT
{
    NETWORKEVENT       = 0x1400,   // 5120
    AUTHENTICATE_REPLY = 0x1401,   // 5121
    REMOVECHARACTER    = 0x1402,   // 5122
    WORLDSNAPSHOT      = 0x1403,   // 5123
    SIMULATIONRESULT   = 0x1404,   // 5124
    RESPAWNCHARACTER   = 0x1405,   // 5125
    LOGDATA            = 0x1406,   // 5126
    ENDGAMEDATA        = 0x1407,   // 5127
    MATCHSTATEINFO     = 0x1408,   // 5128
    PLAYERKARMA        = 0x1409,   // 5129
    FORFEITMATCH       = 0x140A    // 5130
}
```

### MK.PacketType (MatchKeeper)
**Source:** `MKManager.cs`
```csharp
public enum PacketType
{
    MK_AUTH      = 0x1000,   // 4096
    MK_STARTGAME = 0x1001,   // 4097
    MK_MATCHEND  = 0x1002    // 4098
}
```

### SocketState
**Source:** `TCPSocket.cs`
```csharp
public enum SocketState
{
    Connecting = 0,
    Connected = 1,
    Disconnected = 2
}
```

### NetworkEvent
**Source:** `NetworkManager.cs`
```csharp
public enum NetworkEvent
{
    Connecting = 0,
    Connected = 1,
    Disconnected = 2
}
```

### ClientLogType
**Source:** `ClientLog.cs`
```csharp
public enum ClientLogType
{
    SIMULATIONFAIL = 0,
    STATEMISMATCH = 1,
    CHANGESTATE = 2
}
```

### CombatLogType
**Source:** `Utils.cs`
```csharp
public enum CombatLogType
{
    RECEIVE = 0,
    BLOCK = 1,
    DEATH = 2,
    SHIELD_BREAK = 3,
    NULLIFY = 4,
    MITIGATE = 5,
    VULNERABLE = 6
}
```

### LogSource
**Source:** `Utils.cs`
```csharp
public enum LogSource
{
    CLIENT = 0,
    SERVER = 1
}
```

### StateVerifyResult
**Source:** `SimulationManager.cs`
```csharp
public enum StateVerifyResult
{
    NOFAIL = 0,           // Default state
    NORMAL = 1,           // Reverify if applicable
    UNHANDLED = 2,        // State transition unhandled
    RESIMUL_NORECURSE = 3 // Adjust only current simulation
}
```

### ServerRegion
**Source:** `LobbyManager.cs`
```csharp
public enum ServerRegion
{
    INDIA = 0
}
```

---

## 6. Player & Input Enums

### EventState
**Source:** `PlayerInput.cs`
```csharp
public enum EventState
{
    NONE = 0,
    START = 1,
    PROGRESS = 2,
    PROGRESS_CONTINUOUS = 3,
    AIMING = 4,
    SHIELDUP = 5,
    CHANNELING = 6,
    DONE = 7
}
```

### NotifyEvent.NotifyType
**Source:** `Player.cs`
```csharp
public enum NotifyType
{
    MELEE_IMPACT = 0,
    ASTRA_IMPACT = 1,
    AIM_CHARGING = 2
}
```

### SlowType
**Source:** `Player.cs`
```csharp
public enum SlowType
{
    NONE = 0,
    FIFTY = 1,   // 50% slow
    ZERO = 2     // 100% slow (stopped)
}
```

### WillPowerBuffType
**Source:** `Player.cs`
```csharp
public enum WillPowerBuffType
{
    NONE = 0,
    TWENTY = 1,
    FORTY = 2,
    SIXTY = 3,
    EIGHTY = 4,
    MAX = 5
}
```

### ButtonType
**Source:** `ButtonHelper.cs`
```csharp
public enum ButtonType
{
    Elemental1 = 0,
    Elemental2 = 1,
    Elemental3 = 2,
    Elemental4 = 3,
    Attack = 4,
    SpecialAbility = 5,
    GodAbility = 6,
    ThirdEye = 7,
    Shield = 8,
    CancelSpell = 9,
    TouchField = 10,
    Dodge = 11
}
```

### ButtonAction
**Source:** `ButtonHelper.cs`
```csharp
public enum ButtonAction
{
    CLICK = 0,
    UP = 1,
    DOWN = 2,
    DRAG = 3,
    BEGINDRAG = 4,
    ENDDRAG = 5,
    ENTER = 6
}
```

### ActionStateResult
**Source:** `InputManager.cs`
```csharp
public enum ActionStateResult
{
    ACTIVE = 0,
    NOTALLOWED = 1,
    WILLPOWER = 2,
    STAMINA = 3,
    MUTE = 4,
    FOCUS = 5
}
```

### ActionStateType
**Source:** `InputManager.cs`
```csharp
public enum ActionStateType
{
    MOVE = 0,
    ROTATE = 1,
    ASTRA = 2,
    ELEMENTAL1 = 3,
    ELEMENTAL2 = 4,
    ELEMENTAL3 = 5,
    ELEMENTAL4 = 6,
    ELEMENTAL1SHIELD = 7,
    ELEMENTAL2SHIELD = 8,
    ELEMENTAL3SHIELD = 9,
    ELEMENTAL4SHIELD = 10,
    THIRDEYE = 11,
    UNIQUE = 12,
    MELEE = 13
}
```

---

## 7. UI & Visual Enums

### LoadType
**Source:** `MatchModeManager.cs`
```csharp
public enum LoadType
{
    Solo = 0,
    Duo = 1,
    Trio = 2
}
```

### AvatarMode
**Source:** `AvatarManager.cs`
```csharp
public enum AvatarMode
{
    CREATE_AVATAR = 0,
    SWITCH_AVATAR = 1,
    AVATARS_PRESENT = 2,
    CONTINUE_AVATAR_CREATE = 3,
    NONE = 4
}
```

### SelectionState
**Source:** `FighterManager.cs`
```csharp
public enum SelectionState
{
    Weapon_Select = 0,
    Fighter_Class_Select = 1,
    Claim_Weapon = 2,
    AvatarName_Create = 3
}
```

### DailyRewardType
**Source:** `DailyRewardsScreen.cs`
```csharp
public enum DailyRewardType
{
    Bronze = 0,
    Silver = 1,
    Gold = 2,
    Diamond = 3
}
```

### RewardType
**Source:** `PointsPanel.cs`
```csharp
public enum RewardType
{
    Bronze = 0,
    Silver = 1,
    Gold = 2,
    Bhakti_Tokens = 3,
    Gnana_Tokens = 4,
    Lives = 5,
    Time_Shards = 6,
    Hell_Shards = 7
}
```

### TokenType
**Source:** `PointsPanel.cs`
```csharp
public enum TokenType
{
    Bhakti = 0,
    Gnana = 1
}
```

### ItemTier
**Source:** `StoreManager.cs`
```csharp
public enum ItemTier
{
    Bronze = 0,
    Silver = 1,
    Gold = 2
}
```

### ButtonState
**Source:** `CustomizationScreen.cs`
```csharp
public enum ButtonState
{
    Selected = 0,
    Equipped = 1,
    Unequipped = 2,
    Disabled = 3
}
```

### TransitionType
**Source:** `Screen.cs`
```csharp
public enum TransitionType
{
    FADEIN = 0,
    FADEOUT = 1,
    FADEINOUT = 2,
    SLIDELEFT = 3,
    SLIDERIGHT = 4,
    SLIDETOP = 5,
    SLIDEBOTTOM = 6,
    CAMDOLLY = 7
}
```

### TweenType
**Source:** `TweenManager.cs`
```csharp
public enum TweenType
{
    Scale = 0,
    Move = 1,
    Rotate = 2,
    Fade = 3
}
```

### RenderQuality
**Source:** `SettingsManager.cs`
```csharp
public enum RenderQuality
{
    Low = 0,
    Medium = 1,
    High = 2
}
```

### AudioGroups
**Source:** `SettingsManager.cs`
```csharp
public enum AudioGroups
{
    BackGroundMusic = 0,
    UIButtons = 1,
    InGameSfx = 2
}
```

### EventStatus
**Source:** `MaitreyaScreen.cs`
```csharp
public enum EventStatus
{
    Ongoing = 0,
    Upcoming = 1,
    PreviouslyEnded = 2
}
```

### ButtonTypes
**Source:** `InterfaceManager.cs`
```csharp
public enum ButtonTypes
{
    Select = 0,
    Confirm = 1,
    Back = 2,
    slider = 3
}
```

### GameState
**Source:** `InterfaceManager.cs`
```csharp
public enum GameState
{
    Initiate = 0,
    MainMenu = 1,
    InGame = 2
}
```

### ConsumableItemType
**Source:** `InterfaceManager.cs`
```csharp
public enum ConsumableItemType
{
    Time_Shard_Bhakti = 0,
    Time_Shard_Gnana = 1,
    Hell_Shard = 2
}
```

### FriendGameState
**Source:** `FriendsManager.cs`
```csharp
public enum FriendGameState
{
    FreeToJoin = 0,
    InParty = 1,
    InPrivateLobby = 2,
    InPublicLobby = 3,
    InGame = 4
}
```

---

## 8. System & Configuration Enums

### PrefabType
**Source:** `PrefabManager.cs`
```csharp
public enum PrefabType
{
    CASTOBJECTS = 0,
    FIGHTINGSTYLES = 1,
    SPELLEFFECTS = 2,
    SHIELDS = 3,
    GODBONUS = 4,
    FIGHTERATTRIBUTES = 5,
    SPELLDATA = 6,
    ASTRAS = 7,
    MAP = 8,
    BRAHMASHIELD = 9
}
```

### MapType
**Source:** `GameManager.cs`
```csharp
public enum MapType
{
    Bhulok = 0,
    Tutorial = 1
}
```

### MapSize
**Source:** `GameManager.cs`
```csharp
public enum MapSize
{
    Default = 0,
    Small = 1,
    Large = 2
}
```

### AuthEnvironment
**Source:** `AUMAuthConfig.cs`
```csharp
public enum AuthEnvironment
{
    Development = 0,
    Staging = 1,
    Production = 2
}
```

### AuthMode
**Source:** `AUMAuthConfig.cs`
```csharp
public enum AuthMode
{
    FixedDevAccount = 0,   // No MAU consumption
    FirebaseOpenId = 1,    // Full Firebase + PlayFab flow
    Offline = 2            // Mock data mode
}
```

### PlatformTestMode
**Source:** `AUMAuthManager.cs`
```csharp
public enum PlatformTestMode
{
    Auto = 0,
    ForceMobile = 1,
    ForceDesktop = 2
}
```

### BotHandicapState
**Source:** `TutorialManager.cs`
```csharp
public enum BotHandicapState
{
    HANDICAPBOT = 0,
    HANDICAPPLAYER = 1
}
```

### PoolType
**Source:** `ParticleManager.cs`
```csharp
public enum PoolType
{
    Air_Effect = 0,
    Water_Effect = 1,
    Fire_Effect = 2,
    Ether_Effect = 3,
    Earth_Effect = 4,
    Astra_Vishnu_Effect = 5,
    Astra_Shiva_Effect = 6,
    Astra_Brahma_Effect = 7
}
```

### PlayParticleType
**Source:** `PlayParticle.cs`
```csharp
public enum PlayParticleType
{
    Primary = 0,
    Secondary = 1,
    Thirdeye = 2
}
```

### CameraStates
**Source:** `SmoothFollow.cs`
```csharp
public enum CameraStates
{
    FreeMoving = 0,
    Aiming = 1
}
```

### ShakableVirtualCams
**Source:** `CameraController.cs`
```csharp
public enum ShakableVirtualCams
{
    EARTH_CAST_CAM = 0,
    AXE_CALLBACK_CAM = 1
}
```

### ImpulseType
**Source:** `CameraShake.cs`
```csharp
public enum ImpulseType
{
    NormalHit = 0,
    HeavyHit = 1,
    NormalRecoil = 2,
    HeavyRecoil = 3,
    Fire = 4,
    Water = 5,
    Earth = 6,
    Air = 7,
    Ether = 8,
    AstraCast = 9,
    VishnuImpact = 10,
    BrahmaImpact = 11,
    ShivaImpact = 12
}
```

---

## Quick Reference Tables

### Fighting Style → Weapon Type Mapping
| FightingStyles | WeaponType |
|----------------|------------|
| Amuktha (0) | Sword (0) |
| MantraMuktha (1) | Magic (4) |
| MukthaMuktha (2) | Axe (1) |
| PaniMuktha (3) | Chakra (3) |
| YantraMuktha (4) | Bow (2) |

### Trinity God → Astra Type Mapping
| TrinityGods | AstraEntityType |
|-------------|-----------------|
| Brahma (0) | BRAHMASTRA (1) |
| Shiva (1) | SHIVASTRA (3) |
| Vishnu (2) | NARAYANASTRA (2) |

### Elemental → Effect Type Mapping
| Elementals | EffectType |
|------------|------------|
| FIRE (0) | EFFECT_FIREDAMAGE (1) |
| WATER (1) | (Pushback - no effect type) |
| AIR (2) | EFFECT_AIRSLOW (2) |
| ETHER (3) | EFFECT_ETHERMUTE (4) |
| EARTH (4) | EFFECT_EARTHSTUN (3) |

### Packet Type Ranges
| Range | Purpose |
|-------|---------|
| 0x1000-0x10FF | MatchKeeper (MK) |
| 0x1400-0x14FF | Game Server (UDP) |

---

*Document generated from source code analysis*
*Total enums documented: 70+*
