# Networking System

## Overview

LiteNetLib-based client-server architecture with client-side prediction and server reconciliation.

## Architecture

```
Client (AUM-The-Epic)          Server (AUM-Headless)
├── NetworkManager.cs          ├── ServerManager.cs
├── UnifiedInputProvider.cs    ├── NetworkManager.cs
├── IntentProcessor.cs         ├── IntentValidator.cs
└── VisualInterpolator.cs      └── SimulationManager.cs
```

## Tick System

- **Tick Rate**: 60 Hz (16.67ms per tick)
- **History Buffer**: 128 ticks (~2.1 seconds)
- All networked game logic runs in `FixedUpdate()`

## Client-Server Flow

### Input Flow
1. Client captures input → `UnifiedInputProvider`
2. Creates `CombatIntent` with tick number
3. Sends to server via `NetworkManager`
4. Server validates in `IntentValidator`
5. Server broadcasts authoritative state

### Prediction & Reconciliation
1. Client predicts locally (immediate response)
2. Server sends authoritative state
3. Client compares prediction vs server
4. If mismatch: rollback to server state, resimulate

## Key Messages

| Message | Direction | Purpose |
|---------|-----------|---------|
| `PlayerInput` | C→S | Movement, actions |
| `CombatIntent` | C→S | Combat actions with context |
| `StateUpdate` | S→C | Authoritative player states |
| `DamageEvent` | S→C | Confirmed damage |

## ServerAuthority Reconciliation

```csharp
// In ServerAuthority.cs
public void ReconcileWithServer(PlayerStateSnapshot serverState, uint serverTick) {
    var localState = GetStateAtTick(serverTick);
    if (StatesDiffer(localState, serverState)) {
        RestoreSnapshot(serverTick);
        // SimulationManager resimulates forward
    }
}
```

## State Snapshots

Each tick, `BaseAuthority.Tick()` saves:
```csharp
struct PlayerStateSnapshot {
    uint Tick;
    float Stamina, Willpower;
    int Focus;
    float Health;
    Vector3 Position;
    StateType CurrentState;
}
```

## Visual Smoothing

`VisualPositionSmoother` decouples visual from simulation:
- Simulation runs at tick rate
- Visuals interpolate smoothly
- Prevents jitter on state corrections

## Connection Flow

1. Client connects to server IP:Port
2. `AUTHENTICATE_REQUEST` with PlayFab session
3. Server validates session (MD5 hash check)
4. `AUTHENTICATE_REPLY` with player slot
5. Game state synchronization begins

## Key Files

| File | Purpose |
|------|---------|
| `Managers/NetworkManager.cs` | Client networking |
| `Managers/ServerManager.cs` | Server networking |
| `Input/Core/IntentProcessor.cs` | Creates intents |
| `Input/Core/IntentValidator.cs` | Server validation |
| `Visuals/VisualInterpolator.cs` | Smooth rendering |

## Common Issues

### Rubberbanding
- Usually state mismatch between client prediction and server
- Check `IntentValidator` logs for rejected inputs
- Verify tick synchronization

### Connection Drops
- Check session validation (MD5 of PlayFabId)
- Verify server is listening on correct port
- Check firewall rules on Hetzner VPS
