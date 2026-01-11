# State Machine System

## Overview

Finite State Machine (FSM) controlling character states. All state transitions go through `StateManager`.

## Architecture

```
StateManager.cs           - FSM controller
ControllerBase.cs         - State definitions & callbacks
{Character}Player.cs      - Character-specific overrides
```

## State Types

Defined in `ControllerBase.StateType` enum:

| State | Blocks Input | Description |
|-------|--------------|-------------|
| Idle | No | Default standing state |
| Walking | No | Movement active |
| Running | No | Fast movement |
| Attacking | Yes | Attack animation playing |
| Casting | Yes | Ability being cast |
| Dodging | Yes | Dodge in progress |
| Stunned | Yes | Hit stun |
| Blocking | Partial | Shield active |
| Dead | Yes | Character defeated |

## Core Pattern

### State Transition
```csharp
// Always check before transitioning
if (!stateManager.IsBlockingInput()) {
    stateManager.ChangeState(StateType.Attacking);
}
```

### State Callbacks
Each state can have:
- `OnEnter` - Called when entering state
- `OnUpdate` - Called every frame while in state
- `OnExit` - Called when leaving state

## StateManager API

```csharp
// Query current state
stateManager.CurrentState
stateManager.IsBlockingInput()
stateManager.IsInState(StateType.Attacking)

// Change state
stateManager.ChangeState(StateType newState)
stateManager.ForceChangeState(StateType newState)  // Bypasses checks
```

## Integration with Combat Authority

Combat actions check authority before state changes:

```csharp
// In character code
public void TriggerDodge() {
    // 1. Check authority allows it
    if (!combatAuthority.IsAbilityAllowed(AbilityType.Dodge)) return;

    // 2. Check state machine allows it
    if (stateManager.IsBlockingInput()) return;

    // 3. Consume resources
    if (!combatAuthority.ConsumeStamina(70)) return;

    // 4. Change state
    stateManager.ChangeState(StateType.Dodging);
}
```

## Common Issues

### State Mismatch Logging
**Symptom**: Console spam with state mismatch warnings
**Solution**: Rate-limited logging implemented (1 log per second max)

### Stuck in State
1. Check if blocking animation completed
2. Verify `OnExit` callback fired
3. Check for interrupted transitions

### Transition Not Working
1. Is `IsBlockingInput()` returning true?
2. Is target state valid from current state?
3. Are callbacks throwing exceptions?

## Key Files

| File | Purpose |
|------|---------|
| `StateMachine/StateManager.cs` | FSM controller |
| `Player/ControllerBase.cs` | State definitions |
| `Characters/*/Scripts/*Player.cs` | Character implementations |

## State Priority (Planned)

Future improvement: Priority system for simultaneous transition requests.
Currently: First-come-first-served, which can cause issues with competing inputs.
