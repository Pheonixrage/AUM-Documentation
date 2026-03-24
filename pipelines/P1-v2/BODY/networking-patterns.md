---
pipeline: P1
project: AUM-BODY
type: pattern
date: 2026-03-24
tags: [networking, prediction, reconciliation, LiteNetLib]
---

# Networking Patterns — AUM BODY

## Stack

- **Library:** LiteNetLib (UDP)
- **Tick Rate:** 60Hz (`GameManager.clientTickRate`)
- **Pattern:** Server-authoritative with client prediction

## Client Prediction Flow

1. Client captures input in `FixedUpdate()`
2. Input stored in `InputBuffer` with tick number
3. Client applies input locally (prediction)
4. Input sent to server via PacketManager
5. Server validates and broadcasts authoritative state
6. Client reconciles on receiving server state

## Critical Rules

- **ALL network logic in `FixedUpdate()`** — never `Update()`
- Include tick number with all network messages
- Validate on server before broadcasting
- Use interpolation for remote players, prediction for local

## Key Files

- `Assets/Scripts/Managers/NetworkManager.cs`
- `Assets/Scripts/Managers/SimulationManager.cs`
- `Assets/Scripts/Managers/PacketManager.cs`
- `Assets/Scripts/Managers/InputBuffer.cs`
