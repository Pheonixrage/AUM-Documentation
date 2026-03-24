---
pipeline: P1
project: AUM-BODY
type: pattern
date: 2026-03-24
tags: [state-machine, FSM, states]
---

# State Machine Patterns — AUM BODY

## Core Pattern

`StateManager` + `ControllerBase` — 20+ states registered with BlockFlags.

```csharp
stateManager
    .AddState(StateType.Idle, new State(OnIdleEnter, OnIdleUpdate, OnIdleExit, (uint)BlockFlags.Idle))
    .AddState(StateType.Melee, new State(OnAttackEnter, OnAttackUpdate, OnAttackEnd, (uint)BlockFlags.Melee))
    // ... 20+ more
```

## State Callbacks

```csharp
OnXEnter()  — Setup: animations, effects, audio
OnXUpdate() — Per-tick logic (check animation done → Idle)
OnXExit()   — Cleanup: reset anim weights, cancel effects
```

## Input Blocking

Check `stateManager.IsBlockingInput(BlockFlags)` before allowing actions.

## State Mismatch

Server state always wins. `CheckStateMismatch()` reconciles with rate-limited logging.

## Key Files

- `Assets/Scripts/StateMachine/StateManager.cs`
- `Assets/Scripts/Player/ControllerBase.cs`
- Character-specific `*Player.cs` files override callbacks
