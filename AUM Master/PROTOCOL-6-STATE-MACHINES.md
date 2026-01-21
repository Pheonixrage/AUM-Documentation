# AUM Protocol Documentation: State Machines

**Version:** 1.0
**Last Updated:** January 21, 2026
**Namespace:** `FSM`
**Repo:** `AUM-Unity-Server-Legacy`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Player State Machine (FSM)](#2-player-state-machine-fsm)
3. [StateType Enum](#3-statetype-enum)
4. [BlockFlags System](#4-blockflags-system)
5. [State Definition](#5-state-definition)
6. [StateManager Class](#6-statemanager-class)
7. [Match State Machine](#7-match-state-machine)
8. [State Transitions](#8-state-transitions)
9. [Animation Integration](#9-animation-integration)
10. [Effect-Triggered Transitions](#10-effect-triggered-transitions)
11. [Character-Specific States](#11-character-specific-states)
12. [State Callbacks Reference](#12-state-callbacks-reference)

---

## 1. Overview

AUM uses two primary state machines:

1. **Player FSM** - 31 states controlling character behavior
2. **Match FSM** - 7 states controlling match lifecycle

Both are server-authoritative with client prediction for responsiveness.

---

## 2. Player State Machine (FSM)

**File:** `Assets/Scripts/StateMachine/StateManager.cs`
**Namespace:** `FSM`

### Core Concepts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Player State Machine                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Input System                                                               │
│       │                                                                      │
│       ├── IsBlockingInput(flag)?                                            │
│       │   ├── YES → Input blocked                                           │
│       │   └── NO  → Process input                                           │
│       │                                                                      │
│   State Flow                                                                 │
│       │                                                                      │
│       │    Enter()                                                           │
│       │       │                                                              │
│       │       v                                                              │
│       │  ┌─────────────┐                                                    │
│       │  │ Update()    │ ←── Every tick (0.02s)                             │
│       │  │ Loop        │                                                    │
│       │  └─────────────┘                                                    │
│       │       │                                                              │
│       │       │  ChangeState()                                              │
│       │       v                                                              │
│       │    Exit()                                                            │
│       │       │                                                              │
│       │       v                                                              │
│       │    Enter() (new state)                                               │
│       │                                                                      │
│   Animation Timing                                                           │
│       │                                                                      │
│       ├── animStateLength += 0.02f per tick                                 │
│       └── IsAnimationDone() checks completion                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. StateType Enum

**File:** `Assets/Scripts/StateMachine/StateManager.cs:8-42`

### Complete State List (31 States)

| Index | State | Description | Category |
|-------|-------|-------------|----------|
| 0 | `Idle` | Default state, all inputs allowed | Movement |
| 1 | `Melee` | First melee attack | Combat |
| 2 | `Try_Shield_Block` | Attempting shield block | Defense |
| 3 | `Shield_Block` | Active shield blocking | Defense |
| 4 | `Shield_Attack` | Shield bash/attack | Combat |
| 5 | `Aiming` | Ranged attack aim (weapon) | Combat |
| 6 | `Spell_Aiming` | Spell targeting | Magic |
| 7 | `Channel` | Spell channeling | Magic |
| 8 | `Cast_Spell` | Spell cast execution | Magic |
| 9 | `Spell_Anticipate` | Spell anticipation frame | Magic |
| 10 | `Special` | Character unique ability active | Ability |
| 11 | `Special_Aiming` | Unique ability aiming | Ability |
| 12 | `Axe_Callback` | MukthaMuktha axe return | Ability |
| 13 | `State_Unused` | Reserved | - |
| 14 | `Death` | Death state | Combat |
| 15 | `Cast_Shield` | Elemental shield cast | Defense |
| 16 | `Water_Pushback` | Water spell knockback | Effect |
| 17 | `Pushback_Land` | Landing after knockback | Effect |
| 18 | `Special_Anticipate` | Unique ability anticipation | Ability |
| 19 | `Stun` | Stunned (Earth spell) | Effect |
| 20 | `Melee_Second` | Second melee attack (combo) | Combat |
| 21 | `Third_Eye` | Third Eye active | Ability |
| 22 | `Third_Eye_Anticipate` | Third Eye anticipation | Ability |
| 23 | `Dodge` | Dodge roll | Movement |
| 24 | `Astra_Anticipate` | Ultimate ability anticipation | Ultimate |
| 25 | `Astra_Channel` | Ultimate ability channeling | Ultimate |
| 26 | `Astra_Cast` | Ultimate ability cast | Ultimate |
| 27 | `Jump` | Jumping | Movement |
| 28 | `Teleport` | Teleport (match start) | Movement |
| 29 | `Vulnerable` | Vulnerable state | Effect |
| 30 | `Victory` | Victory pose | End |
| 31 | `Undefined` | Unknown/error state | - |

### State Categories

```csharp
// Movement States
Idle, Dodge, Jump, Teleport

// Combat States
Melee, Melee_Second, Aiming, Shield_Attack

// Defense States
Try_Shield_Block, Shield_Block, Cast_Shield

// Magic States
Channel, Spell_Aiming, Cast_Spell, Spell_Anticipate

// Ability States
Special, Special_Aiming, Special_Anticipate, Axe_Callback
Third_Eye, Third_Eye_Anticipate

// Ultimate States
Astra_Anticipate, Astra_Channel, Astra_Cast

// Effect States
Water_Pushback, Pushback_Land, Stun, Vulnerable

// End States
Death, Victory
```

---

## 4. BlockFlags System

**File:** `Assets/Scripts/StateMachine/StateManager.cs:227-242`

### BlockFlags Enum

```csharp
[System.Flags]
public enum BlockFlags
{
    Block_Elemental_Spell   = 1 << 0,   // 0x001
    Block_JoystickAxis      = 1 << 1,   // 0x002
    Block_Melee             = 1 << 2,   // 0x004
    Block_Camera            = 1 << 3,   // 0x008
    Block_Astra             = 1 << 4,   // 0x010
    Block_Shield            = 1 << 5,   // 0x020
    Block_ThirdEye          = 1 << 6,   // 0x040
    Block_Unique            = 1 << 7,   // 0x080
    Block_Elemental_Shield  = 1 << 8,   // 0x100
    Block_Dodge             = 1 << 9,   // 0x200
    Block_Jump              = 1 << 10,  // 0x400

    BlockAll = Block_Elemental_Spell | Block_Elemental_Shield |
               Block_JoystickAxis | Block_Melee | Block_Camera |
               Block_Astra | Block_Shield | Block_ThirdEye |
               Block_Unique | Block_Dodge | Block_Jump
}
```

### BlockFlags Binary Values

| Flag | Binary | Hex | Decimal |
|------|--------|-----|---------|
| Block_Elemental_Spell | 00000000001 | 0x001 | 1 |
| Block_JoystickAxis | 00000000010 | 0x002 | 2 |
| Block_Melee | 00000000100 | 0x004 | 4 |
| Block_Camera | 00000001000 | 0x008 | 8 |
| Block_Astra | 00000010000 | 0x010 | 16 |
| Block_Shield | 00000100000 | 0x020 | 32 |
| Block_ThirdEye | 00001000000 | 0x040 | 64 |
| Block_Unique | 00010000000 | 0x080 | 128 |
| Block_Elemental_Shield | 00100000000 | 0x100 | 256 |
| Block_Dodge | 01000000000 | 0x200 | 512 |
| Block_Jump | 10000000000 | 0x400 | 1024 |
| BlockAll | 11111111111 | 0x7FF | 2047 |

### StateBlockFlags Per State

```csharp
public enum StateBlockFlags
{
    // Idle: Nothing blocked
    Idle = BlockFlags.BlockAll & ~(BlockFlags.BlockAll),  // 0x000

    // Melee: Allow movement and camera
    Melee = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera),

    // Shield_Attack: Allow movement and camera
    Shield_Attack = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera),

    // Shield_Block: Allow movement, camera, and shield release
    Shield_Block = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Shield),

    // Aiming: Allow movement, camera, and melee interrupt
    Aiming = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Melee),

    // Spell_Aiming: Allow movement, camera, and spell cast
    Spell_Aiming = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Elemental_Spell),

    // Channel: Allow movement and camera
    Channel = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera),

    // All inputs blocked states
    Spell_Anticipate = BlockFlags.BlockAll,
    Cast_Spell = BlockFlags.BlockAll,
    Special = BlockFlags.BlockAll,
    Death = BlockFlags.BlockAll,
    Water_Pushback = BlockFlags.BlockAll,
    Pushback_Land = BlockFlags.BlockAll,
    Special_Anticipate = BlockFlags.BlockAll,
    Stun = BlockFlags.BlockAll,
    Third_Eye_Anticipate = BlockFlags.BlockAll,
    Astra_Channel = BlockFlags.BlockAll,
    Astra_Anticipate = BlockFlags.BlockAll,
    Astra_Cast = BlockFlags.BlockAll,
    Dodge = BlockFlags.BlockAll,
    Jump = BlockFlags.BlockAll,
    Teleport = BlockFlags.BlockAll,
    Vulnerable = BlockFlags.BlockAll,
    Victory = BlockFlags.BlockAll,

    // Special_Aiming: Allow movement, camera, and unique ability
    Special_Aiming = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Unique),

    // Axe_Callback: Allow movement, camera, and unique ability
    Axe_Callback = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera | BlockFlags.Block_Unique),

    // Cast_Shield: Allow movement and camera
    Cast_Shield = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera),

    // Third_Eye: Allow movement and camera
    Third_Eye = BlockFlags.BlockAll & ~(BlockFlags.Block_JoystickAxis | BlockFlags.Block_Camera),

    // Astra_Cast_Shiva: Allow camera only (Shiva can aim during cast)
    Astra_Cast_Shiva = BlockFlags.BlockAll & ~(BlockFlags.Block_Camera),
}
```

### Input Blocking Matrix

| State | Spell | Move | Melee | Camera | Astra | Shield | 3rdEye | Unique | E.Shield | Dodge | Jump |
|-------|-------|------|-------|--------|-------|--------|--------|--------|----------|-------|------|
| Idle | - | - | - | - | - | - | - | - | - | - | - |
| Melee | X | - | X | - | X | X | X | X | X | X | X |
| Shield_Block | X | - | X | - | X | - | X | X | X | X | X |
| Aiming | X | - | - | - | X | X | X | X | X | X | X |
| Spell_Aiming | - | - | X | - | X | X | X | X | X | X | X |
| Channel | X | - | X | - | X | X | X | X | X | X | X |
| Cast_Spell | X | X | X | X | X | X | X | X | X | X | X |
| Special_Aiming | X | - | X | - | X | X | X | - | X | X | X |
| Third_Eye | X | - | X | - | X | X | X | X | X | X | X |
| Death | X | X | X | X | X | X | X | X | X | X | X |
| Stun | X | X | X | X | X | X | X | X | X | X | X |

*X = Blocked, - = Allowed*

---

## 5. State Definition

### State Class

```csharp
public class State
{
    public StateType type;
    public uint blockInputs;

    public delegate void onStateEvent();
    public onStateEvent Enter;
    public onStateEvent Update;
    public onStateEvent Exit;

    public State(
        onStateEvent _Enter,
        onStateEvent _Update,
        onStateEvent _Exit,
        uint _blockInputs)
    {
        Enter = _Enter;
        Update = _Update;
        Exit = _Exit;
        blockInputs = _blockInputs;
    }
}
```

### State Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        State Lifecycle                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ChangeState(newState)                                           │
│       │                                                          │
│       ├── currentState.Exit()                                    │
│       │                                                          │
│       ├── previousState = currentState                           │
│       │                                                          │
│       ├── animStateLength = 0                                    │
│       │                                                          │
│       ├── currentState = stateList[newState]                     │
│       │                                                          │
│       └── currentState.Enter()                                   │
│                                                                  │
│  ExecuteStateUpdate(tick)                                        │
│       │                                                          │
│       └── while (currentState changes) {                         │
│               currentState.Update()                              │
│               animStateLength += 0.02f                           │
│           }                                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. StateManager Class

### Properties

```csharp
public class StateManager
{
    private State runningState;          // Current active state
    private State previousState;         // Last state (for SwitchtoPrevious)
    public Dictionary<StateType, State> stateList;
    private Dictionary<int, AnimationData> animationStateLengthList;
    FInt animStateLength;                // Current animation progress
    public UInt32 stateTick;             // Server tick
    private UInt32 playerTick;           // Player tick
    private Player player;               // Owner player
}
```

### Core Methods

```csharp
// Constructor - loads animation data per fighting style
public StateManager(Player _player)

// Add state to state list (chainable)
public StateManager AddState(StateType type, State newState)

// Change to new state (calls Exit → Enter)
public void ChangeState(StateType nextState)

// Run state update loop
public void ExecuteStateUpdate(UInt32 currentStateTick, UInt32 currentPlayerTick)

// Return to previous state
public void SwitchtoPrevious()

// Check if input is blocked by current state
public bool IsBlockingInput(uint blockFlag)

// Animation timing checks
public bool IsAnimationDone()
public bool IsAnimationDone(int index)
public bool IsAnimationDone(float animFrameFactor)
public bool IsAnimationDone(float animFrameFactor, int index)
public bool isAnimationHalfDone(float animFrameFactor, float mainFactor)
public bool isAnimationHalfDone(float animFrameFactor, float mainFactor, int index)

// Set animation start point
public void SetAnimStateLengthStartPoint(float startPoint, int animIndex, float animFrameFactor)

// Get current and previous state
public StateType GetState()
public StateType GetPreviousState()

// Check melee state
public static bool IsInMeleeState(StateType stateType)
```

### Animation Data

```csharp
[Serializable]
public class AnimationData
{
    public int state;           // StateType as int
    public float[] animLength;  // Animation lengths per index
    public float[] transitionTime;  // Transition times per index

    public AnimationData(int _state, float[] _animLength, float[] _transitionTime)
}
```

---

## 7. Match State Machine

**File:** `Assets/Scripts/MatchState.cs`

### MatchStates Enum

```csharp
public enum MatchStates
{
    NONE,       // 0 - Waiting for initialization
    PREMATCH,   // 1 - Countdown before teleport
    TELEPORT,   // 2 - Spawning players
    MATCH,      // 3 - Active combat
    ENDMATCH,   // 4 - Post-kill cooldown
    POSTMATCH,  // 5 - Results display
    END         // 6 - Cleanup
}
```

### State Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Match State Flow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   NONE ──────────────> PREMATCH                                             │
│         SignalMatchReady()  │                                               │
│                             │ Countdown (preMatchTime)                      │
│                             │ Wait for all players                          │
│                             v                                               │
│                         TELEPORT                                            │
│                             │ Countdown (teleportTimer)                     │
│                             │ Players spawn at positions                    │
│                             v                                               │
│                          MATCH ←────────────────────────┐                   │
│                             │ Active combat              │                   │
│                             │ matchTimer running         │                   │
│                             v                            │                   │
│                        ENDMATCH                          │                   │
│         SignalMatchEnd()    │ Post-kill timer           │                   │
│                             │ (postMatchReadyTime)       │                   │
│                             v                            │                   │
│                        POSTMATCH                         │                   │
│                             │ Results display            │                   │
│                             │ Karma selection            │                   │
│                             │ (postMatchTime)            │                   │
│                             v                            │                   │
│                           END                            │                   │
│                             │ EndGame() called           │                   │
│                             └────────────────────────────┘                   │
│                                  (if continuing)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MatchState Properties

```csharp
public class MatchState : MonoBehaviour
{
    public static MatchState Instance;

    // Timers
    public float matchTimer;           // Time elapsed in MATCH state
    public float preMatchTime;         // Countdown before teleport (default: 5s)
    public float teleportTimer;        // Teleport duration
    public float postMatchTime;        // Post-match results time
    public float postMatchReadyTime;   // Pre-postmatch buffer

    // State
    public MatchStates state;
    private byte countdownTimer;       // Current countdown value
    private bool signalMatchReady;     // Ready to start
    private bool proceedPostGame;      // Ready to end post-game
}
```

### State Transition Logic

```csharp
// NONE → PREMATCH
if (signalMatchReady)
{
    state = MatchStates.PREMATCH;
    countdownTimer = (byte)preMatchTime;
    GameManager.Instance.Intialize();
}

// PREMATCH → TELEPORT
// Wait for all human players to connect
bool allHumansConnected = connectedHumans >= expectedHumans;
if (countdownTimer == 0 && allPlayersReady)
{
    state = MatchStates.TELEPORT;
    countdownTimer = (byte)teleportTimer;
    GameManager.Instance.StartMatchTeleport();
}

// TELEPORT → MATCH
if (countdownTimer == 0)
{
    state = MatchStates.MATCH;
    GameManager.Instance.StartMatch();
    matchTimer = 0;
}

// MATCH → ENDMATCH
// Triggered by SignalMatchEnd() when winner determined

// ENDMATCH → POSTMATCH
if (countdownTimer == 0)
{
    state = MatchStates.POSTMATCH;
    countdownTimer = (byte)postMatchTime;
    GameManager.Instance.EndMatch();
}

// POSTMATCH → END
// Wait for karma selection if first match
if (countdownTimer == 0)
{
    state = MatchStates.END;
    GameManager.Instance.EndGame(false);
}
```

---

## 8. State Transitions

### Base State Transitions (All Characters)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Base State Transitions                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              ┌────────────┐                                  │
│                              │    Idle    │◄───────────────────┐            │
│                              └────────────┘                    │            │
│                                    │                           │            │
│          ┌──────────┬──────────┬──┴───┬──────────┬──────────┬─┴─────┐      │
│          │          │          │      │          │          │       │      │
│          v          v          v      v          v          v       v      │
│     ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │
│     │ Melee  │ │Channel │ │Shield  │ │ Dodge  │ │Third   │ │ Astra  │     │
│     │        │ │        │ │ Block  │ │        │ │  Eye   │ │Anticip │     │
│     └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘     │
│          │          │          │           │         │          │          │
│          v          v          │           │         v          v          │
│     ┌────────┐ ┌────────┐      │           │    ┌────────┐ ┌────────┐     │
│     │ Melee  │ │ Spell  │      │           │    │Third   │ │ Astra  │     │
│     │ Second │ │ Aiming │      │           │    │Eye Act │ │Channel │     │
│     └────────┘ └────────┘      │           │    └────────┘ └────────┘     │
│          │          │          │           │         │          │          │
│          │          v          v           │         │          v          │
│          │    ┌────────────────────┐       │         │    ┌────────┐      │
│          │    │ Spell_Anticipate   │       │         │    │ Astra  │      │
│          │    └────────────────────┘       │         │    │  Cast  │      │
│          │               │                 │         │    └────────┘      │
│          │               v                 │         │          │          │
│          │    ┌────────────────────┐       │         │          │          │
│          │    │    Cast_Spell      │       │         │          │          │
│          │    └────────────────────┘       │         │          │          │
│          │               │                 │         │          │          │
│          └───────────────┴─────────────────┴─────────┴──────────┘          │
│                                    │                                        │
│                                    v                                        │
│                              ┌────────────┐                                 │
│                              │    Idle    │                                 │
│                              └────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Melee Combo Flow

```
Idle
  │
  │ Attack Input
  v
Melee (First Attack)
  │
  │ Attack Input (during Melee)
  v
Melee_Second (Second Attack)
  │
  │ Animation Done
  v
Idle
```

### Spell Cast Flow

```
Idle
  │
  │ Spell Input (hold)
  v
Channel
  │
  │ Channeling Done
  v
Spell_Aiming
  │
  │ Spell Input (release)
  v
Spell_Anticipate
  │
  │ Focus Check Pass
  v
Cast_Spell
  │
  │ Animation Done
  v
Idle
```

### Astra (Ultimate) Flow

```
Idle
  │
  │ Astra Input
  v
Astra_Anticipate
  │
  │ Animation Done
  v
Astra_Channel
  │
  │ Animation Done
  v
Astra_Cast
  │
  │ Animation 50% → Spawn Astra
  │ Animation Done
  v
Idle
```

### Third Eye Flow

```
Idle
  │
  │ Third Eye Input
  v
Third_Eye_Anticipate
  │
  │ Focus Check Pass
  v
Third_Eye
  │
  │ Animation Done
  v
Idle
```

### Death Flow

```
Any State
  │
  │ Health <= 0
  v
Death
  │
  │ (No recovery)
  v
(Remain in Death)
```

---

## 9. Animation Integration

### Animation Timing Check

```csharp
// Check if animation is complete
public bool IsAnimationDone(float animFrameFactor, int index)
{
    // animStateLength increments by 0.02f per tick
    // Check against stored animation length + transition time
    if (animStateLength >=
        (FInt)(animationStateLengthList[(int)runningState.type].animLength[index])
        * (1 / (FInt)animFrameFactor)
        + (FInt)(animationStateLengthList[(int)runningState.type].transitionTime[index]))
    {
        return true;
    }
    return false;
}

// Check if animation is at specified percentage
public bool isAnimationHalfDone(float animFrameFactor, float mainFactor, int index)
{
    if (animStateLength >=
        ((FInt)(animationStateLengthList[(int)runningState.type].animLength[index])
         * (1 / (FInt)animFrameFactor)
         + (FInt)(animationStateLengthList[(int)runningState.type].transitionTime[index]))
        * (FInt)mainFactor)
    {
        return true;
    }
    return false;
}
```

### Animation Speed Factors

```csharp
// Elemental attack speeds (from player stats)
float GetElementalAttackSpeed(Elementals elemental)
{
    switch(elemental)
    {
        case Elementals.FIRE:  return player.playerStats.fire_AttackSpeed;
        case Elementals.WATER: return player.playerStats.water_AttackSpeed;
        case Elementals.AIR:   return player.playerStats.air_AttackSpeed;
        case Elementals.ETHER: return player.playerStats.ether_AttackSpeed;
        case Elementals.EARTH: return player.playerStats.earth_AttackSpeed;
        default: return 0f;
    }
}
```

### Animation Events (50% Triggers)

Many states trigger actions at 50% animation completion:

```csharp
// Cast_Spell: Spawn spell at 50%
if (stateManager.isAnimationHalfDone(elementalAttackSpeed, 0.5f) && !entitySpawnDone)
{
    entitySpawnDone = true;
    GameManager.Instance.SpellManager.InstantiateSelectedSpell(...);
}

// Cast_Shield: Activate shield at 30%
if (stateManager.isAnimationHalfDone(1f, 0.3f) && !elementalShieldDone)
{
    player.character.playerBase.ActivateElementalShield(currentShieldIndex);
    elementalShieldDone = true;
}

// Astra_Cast: Spawn astra at 50%
if (stateManager.isAnimationHalfDone(1f, 0.5f) && !entitySpawnDone)
{
    entitySpawnDone = true;
    GameManager.Instance.AstraManager.SpawnAstra(player);
}
```

---

## 10. Effect-Triggered Transitions

### Ethermute Effect

```csharp
// Ethermute cancels spell casting
if (effect.type == Effects.EffectType.EFFECT_ETHERMUTE)
{
    switch (stateManager.GetState())
    {
        case StateType.Channel:
        case StateType.Spell_Aiming:
        case StateType.Spell_Anticipate:
        case StateType.Astra_Anticipate:
        case StateType.Astra_Channel:
            stateManager.ChangeState(StateType.Idle);
            break;
    }
}
```

### Impair Effect

```csharp
// Impair cancels special abilities and dodge
if (effect.type == Effects.EffectType.EFFECT_IMPAIR)
{
    switch (stateManager.GetState())
    {
        case StateType.Special_Aiming:
        case StateType.Special_Anticipate:
        case StateType.Special:
            // Only affects MantraMuktha and Amuktha
            if (player.fightingStyle == FightingStyles.MantraMuktha ||
                player.fightingStyle == FightingStyles.Amuktha)
            {
                stateManager.ChangeState(StateType.Idle);
            }
            break;
        case StateType.Dodge:
            stateManager.ChangeState(StateType.Idle);
            break;
    }
}
```

### Stun Effect

```csharp
public void DoStun(float stunDuration)
{
    if (stateManager.GetState() != StateType.Death && !player.IsThirdEyeActive())
    {
        Effects stunEffect = new EarthStun(stunDuration, player);
        AddEffect(stunEffect);
        stateManager.ChangeState(StateType.Stun);
    }
}
```

### Water Pushback

```csharp
public bool DoWaterPushback(ElementalShield.AttackInfo attackInfo, Entity sourceEntity)
{
    if (player.IsThirdEyeActive())
    {
        return false;  // Third Eye immune
    }

    // Check shield
    if (playerBase.activeElementalShield != null)
    {
        var result = playerBase.activeElementalShield.RegisterShieldHit(
            DamageType.WATER, sourceEntity, attackInfo);
        if (result.damagePassFraction <= 0f)
        {
            return false;  // Shield blocked
        }
    }

    stateManager.ChangeState(StateType.Water_Pushback);
    return true;
}
```

---

## 11. Character-Specific States

### Amuktha (Sword Fighter)

```csharp
States Used:
├── Idle
├── Melee
├── Melee_Second
├── Special_Aiming    // Dash aim
├── Special           // Dash execute
├── Shield_Block
├── Shield_Attack
└── (All base states)
```

### MantraMuktha (Staff Mage)

```csharp
States Used:
├── Idle
├── Melee
├── Channel           // Primary spell method
├── Spell_Aiming
├── Cast_Spell
├── Teleport          // Unique ability
├── Special_Aiming    // Teleport aim
└── (All base states)
```

### MukthaMuktha (Axe Fighter)

```csharp
States Used:
├── Idle
├── Melee
├── Melee_Second
├── Special_Aiming    // Axe throw aim
├── Special           // Axe throw
├── Axe_Callback      // Axe return (unique state)
├── Shield_Block
└── (All base states)
```

### PaniMuktha (Bow/Disc)

```csharp
States Used:
├── Idle
├── Aiming            // Ranged weapon aim
├── Melee             // Melee attack
├── Special_Aiming    // Disc throw aim
├── Special           // Disc throw
└── (All base states)
```

### YantraMuktha (Ranged)

```csharp
States Used:
├── Idle
├── Aiming            // Arrow aim
├── Melee             // Melee attack
├── Special_Aiming    // Special arrow aim
├── Special           // Special arrow
└── (All base states)
```

---

## 12. State Callbacks Reference

### All Callbacks in ControllerBase

| Callback | State | Purpose |
|----------|-------|---------|
| `OnIdleEnter()` | Idle | Initialize idle state |
| `OnIdleUpdate()` | Idle | Process idle tick |
| `OnIdleExit()` | Idle | Cleanup idle state |
| `OnAttackEnter()` | Melee | Reduce stamina |
| `OnAttackUpdate()` | Melee | Process attack |
| `OnAttackEnd()` | Melee | Cleanup attack |
| `OnChannelEnter()` | Channel | Set cast object |
| `OnChannelUpdate()` | Channel | Check channeling done |
| `OnChannelExit()` | Channel | Reset channels |
| `OnSpellAimEnter()` | Spell_Aiming | Initialize aim |
| `OnSpellAimUpdate()` | Spell_Aiming | Process aim |
| `OnSpellAimExit()` | Spell_Aiming | Cleanup aim |
| `OnCastSpellEnter()` | Cast_Spell | Initialize cast |
| `OnCastSpellUpdate()` | Cast_Spell | Spawn spell at 50%, check done |
| `OnCastSpellExit()` | Cast_Spell | Reset flags |
| `OnSpecialAimEnter()` | Special_Aiming | Initialize unique aim |
| `OnSpecialAimUpdate()` | Special_Aiming | Process unique aim |
| `OnSpecialAimExit()` | Special_Aiming | Cleanup unique aim |
| `OnSpecialAbilityEnter()` | Special | Check/consume focus |
| `OnSpecialAbilityUpdate()` | Special | Process unique ability |
| `OnSpecialAbilityExit()` | Special | Reset specialDone |
| `OnShieldBlockEnter()` | Shield_Block | Reduce stamina |
| `OnShieldBlockUpdate()` | Shield_Block | Process block |
| `OnShieldBlockExit()` | Shield_Block | Cleanup block |
| `OnShieldAttackEnter()` | Shield_Attack | Reduce stamina |
| `OnShieldAttackUpdate()` | Shield_Attack | Process bash |
| `OnShieldAttackExit()` | Shield_Attack | Cleanup bash |
| `OnSpellAnticipateEnter()` | Spell_Anticipate | Initialize |
| `OnSpellAnticipateUpdate()` | Spell_Anticipate | Check focus, transition |
| `OnSpellAnticipateExit()` | Spell_Anticipate | Cleanup |
| `OnCastShieldEnter()` | Cast_Shield | Check/consume focus |
| `OnCastShieldUpdate()` | Cast_Shield | Activate shield at 30% |
| `OnCastShieldExit()` | Cast_Shield | Reset flag |
| `OnDeathEnter()` | Death | Clear all effects |
| `OnDeathUpdate()` | Death | Process death |
| `OnDeathExit()` | Death | Cleanup |
| `OnPushBackEnter()` | Water_Pushback | Initialize pushback |
| `OnPushBackUpdate()` | Water_Pushback | Process knockback |
| `OnPushBackExit()` | Water_Pushback | Cleanup |
| `OnPushbackLandEnter()` | Pushback_Land | Initialize landing |
| `OnPushbackLandUpdate()` | Pushback_Land | Check animation done |
| `OnPushbackLandExit()` | Pushback_Land | Reset flag |
| `OnSpecialAnticipateEnter()` | Special_Anticipate | Initialize |
| `OnSpecialAnticipateUpdate()` | Special_Anticipate | Process |
| `OnSpecialAnticipateExit()` | Special_Anticipate | Cleanup |
| `OnStunEnter()` | Stun | Initialize stun |
| `OnStunUpdate()` | Stun | Process stun |
| `OnStunExit()` | Stun | Cleanup |
| `OnThirdEyeEnter()` | Third_Eye | Initialize third eye |
| `OnThirdEyeUpdate()` | Third_Eye | Check animation done |
| `OnThirdEyeExit()` | Third_Eye | Reset flag |
| `OnThirdEyeAnticipateEnter()` | Third_Eye_Anticipate | Check/consume focus |
| `OnThirdEyeAnticipateUpdate()` | Third_Eye_Anticipate | Process |
| `OnThirdEyeAnticipateExit()` | Third_Eye_Anticipate | Cleanup |
| `OnDodgeEnter()` | Dodge | Check/consume stamina |
| `OnDodgeUpdate()` | Dodge | Execute dodge movement |
| `OnDodgeExit()` | Dodge | Cleanup |
| `OnJumpEnter()` | Jump | Initialize jump |
| `OnJumpUpdate()` | Jump | Check animation done |
| `OnJumpExit()` | Jump | Cleanup |
| `OnAstraAnticipateEnter()` | Astra_Anticipate | Initialize |
| `OnAstraAnticipateUpdate()` | Astra_Anticipate | Process |
| `OnAstraAnticipateExit()` | Astra_Anticipate | Cleanup |
| `OnAstraChannelEnter()` | Astra_Channel | Initialize |
| `OnAstraChannelUpdate()` | Astra_Channel | Check done, transition |
| `OnAstraChannelExit()` | Astra_Channel | Cleanup |
| `OnAstraCastEnter()` | Astra_Cast | Initialize |
| `OnAstraCastUpdate()` | Astra_Cast | Spawn at 50%, check done |
| `OnAstraCastExit()` | Astra_Cast | Reset flags |
| `OnTeleportEnter()` | Teleport | Initialize |
| `OnTeleportUpdate()` | Teleport | Move to spawn at 100% |
| `OnTeleportExit()` | Teleport | Cleanup |
| `OnVulnerableEnter()` | Vulnerable | Initialize |
| `OnVulnerableUpdate()` | Vulnerable | Process |
| `OnVulnerableExit()` | Vulnerable | Cleanup |
| `OnVictoryEnter()` | Victory | Initialize |
| `OnVictoryUpdate()` | Victory | Process |
| `OnVictoryExit()` | Victory | Cleanup |

---

## Cross-Reference

- **Protocol Overview:** [PROTOCOL-1-OVERVIEW.md](./PROTOCOL-1-OVERVIEW.md)
- **WSS Packets:** [PROTOCOL-2-WSS-PACKETS.md](./PROTOCOL-2-WSS-PACKETS.md)
- **UDP Packets:** [PROTOCOL-3-UDP-PACKETS.md](./PROTOCOL-3-UDP-PACKETS.md)
- **MatchKeeper:** [PROTOCOL-4-MATCHKEEPER.md](./PROTOCOL-4-MATCHKEEPER.md)
- **PlayFab:** [PROTOCOL-5-PLAYFAB.md](./PROTOCOL-5-PLAYFAB.md)
- **Game Data:** [PROTOCOL-7-GAME-DATA.md](./PROTOCOL-7-GAME-DATA.md)
- **Characters:** [PROTOCOL-8-CHARACTERS.md](./PROTOCOL-8-CHARACTERS.md)
- **Spells:** [PROTOCOL-9-SPELLS.md](./PROTOCOL-9-SPELLS.md)
- **Enums:** [PROTOCOL-10-ENUMS.md](./PROTOCOL-10-ENUMS.md)
- **Index:** [PROTOCOL-INDEX.md](./PROTOCOL-INDEX.md)

---

*Document generated from AUM-Unity-Server-Legacy codebase*
*Total Player States: 31*
*Total Match States: 7*
*Total Block Flags: 11*
*Total State Callbacks: 72*
