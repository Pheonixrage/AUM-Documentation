---
pipeline: P1
project: AUM-MIND
type: pattern
date: 2026-03-24
tags: [server, authority, validation, bots]
---

# Server Authority Patterns — AUM MIND

## Core Principle

Server validates ALL combat: hits, damage, state changes. Never trust client-reported values.

## Bot Processing

Bots generate `KeyInput` via `BotBrain.Think()` → processed through `PlayerManager.ProcessPlayerInputTick()` — same pipeline as real players.

## Match Lifecycle

```
NONE → PREMATCH → TELEPORT → MATCH → ENDMATCH → POSTMATCH → END
```

## Headless Build

- Target: Linux64, no graphics, IL2CPP
- Unity 2022.3.62f2

## Key Files

- `Assets/Scripts/Managers/GameManager.cs` — server game loop
- `Assets/Scripts/Managers/PlayerManager.cs` — player management
- `Assets/Scripts/Bots/Bot/Core/BotBrain.cs` — AI decisions
- `Assets/Scripts/Network/MatchController.cs` — match state
