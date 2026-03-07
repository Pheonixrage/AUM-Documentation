# AUM Headless Server

## Overview
Authoritative game server for AUM multiplayer fighting game. This is the **headless Unity build** that runs on Hetzner VPS and validates all combat, damage, and game state.

## Relationship to Client
- **Client Repo**: `AUM-The-Epic` (sibling directory)
- **Shared Code**: Most gameplay scripts are mirrored; server has authority
- **Build Target**: Linux64 headless (-nographics)

## Architecture
- **Authority**: Server-authoritative for ALL combat decisions
- **Networking**: LiteNetLib-based custom protocol
- **Backend**: PlayFab (Title ID: 15F2B7) for matchmaking, currencies, leaderboards

## Key Directories
```
Assets/Scripts/
├── CombatAuthority/     # ServerAuthority validates all hits/damage
├── Managers/            # GameManager, PlayerManager, BotManager
├── Network/             # LiteNetLibServer, ServerStartup, MatchController
├── Bots/                # AI opponents (Bot.cs, BotExecutor.cs)
└── PlayFab/             # PlayFabServerBridge for backend calls
```

## Build & Deploy
```bash
# Build headless server (from Unity)
# Target: Linux64, Headless Mode, IL2CPP

# Deploy to Hetzner
scp -r Build/* user@server:/opt/aum-server/
systemctl restart aum-server
```

## Critical Rules

### DO NOT
- Trust ANY client-reported values (damage, positions, state)
- Use `Update()` for game logic (use `FixedUpdate()`)
- Skip validation on any client packet

### ALWAYS
- Validate hits via ICombatAuthority.ServerAuthority
- Log suspicious activity for anti-cheat review
- Test changes against client build before deploying

## Current Focus
See `IMPLEMENTATION_REPORT_JAN4_2026.md` for latest sprint work.

## Related Workflows
See `.agent/workflows/` for common tasks.
