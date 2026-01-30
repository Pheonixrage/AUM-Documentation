# AUM Git Branch Tree Visualization
**Generated:** January 25, 2026

---

## Repository Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUM PROJECT REPOSITORIES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │    AUM-The-Epic         │         │     AUM-Headless        │           │
│  │    (Unity Client)       │◄───────►│    (Unity Server)       │           │
│  │                         │  Shared │                         │           │
│  │  iOS / Android / Mac    │  Code   │  Linux Headless Build   │           │
│  └─────────────────────────┘         └─────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │   AUM-Documentation     │         │   AUM-Claude-Private    │           │
│  │   (Context/Logs)        │         │   (AI Memory)           │           │
│  └─────────────────────────┘         └─────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CLIENT (AUM-The-Epic) Branch Tree

```
                                 REMOTE: origin (GitHub)
                                 ════════════════════════
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    ▼                                           ▼
            origin/main                          origin/feature/authoritative-architecture
                 │                                              │
    [Production Release]                            [45bc7c47] Jan 25 2026
                 │                                              │
                 │                                              ├── Stamina sync to packet
                 │                                              ├── Animation index fix
                 │                                              └── 30 files changed
                                                                │
                                 LOCAL BRANCHES                 │
                                 ══════════════                 │
                                          │                     │
                    ┌─────────────────────┴─────────────────────┤
                    │                                           │
                    ▼                                           ▼
                 main                          feature/authoritative-architecture
            (tracks origin/main)                    (tracks origin/feature/...)
                    │                                           │
                    │                                   ┌───────┴───────┐
                    │                                   │               │
                    │                                   ▼               │
                    │                          [45bc7c47] HEAD          │
                    │                          "Jan 25 2026: Stamina    │
                    │                           sync, animation fixes"  │
                    │                                   │               │
                    │                          29 commits ahead ────────┘
                    │                          of main
                    │
                    └──────── Merge Point (after testing) ──────────────►
```

### CLIENT Commit History (feature/authoritative-architecture)

```
HEAD ──► 45bc7c47 Jan 25 2026: Stamina sync, animation fixes, authoritative
         │
         ├── 41f6da6c Fix touch input for iPhone production: TAP/HOLD + dodge
         ├── 5a6c19ca Fix focus generation and attack input issues (Jan 24)
         ├── 4eca6899 Add Jan 23 session documentation: visual smoothing
         ├── 9cf60c4f Enhance visual smoothing: tune reconciliation
         ├── e1befc14 Fix dodge distance: add Position Lock
         ├── dde3a9aa Fix position desync: remove rotation grace
         ├── 7af71c20 WIP: Almost working gameplay ticking (Jan 22)
         ├── f0b706c0 WIP: Jan 16 playtest fixes + input analysis
         ├── 990a83e2 Add ValidatedLogger to AUMInputManager
         ├── f4230ea1 Phase 3: Route input through AUMInputManager
         ├── 6c3d188f Merge unified-input-dashboard
         ├── 3aa17820 Merge unified-input-manager
         ├── 22168cf7 Add AUM Input Control Center
         ├── 5f8786e3 Add AUMInputManager unified entry point
         ├── 77e80c5f Add ScriptableObject config for input
         ├── d42cd452 Backup before unified input
         ├── ffe5fa15 Remove redundant ClientLog.cs
         ├── b5161c25 Fix ACTION REJECTION logging errors
         ├── 25f2e8a5 Add ACTION REJECTION logging
         ├── 23429aa4 Fix validated logging compilation
         ├── 94aba4bf ValidatedLogger cleanup
         ├── 7ae76fe5 Validated logging system
         ├── f3f055e2 Add Claude Code config
         ├── 592d04a6 UI + asset + spell updates (Jan 12)
         ├── 1b106f86 Combat authority + managers (Jan 12)
         ├── 7404aa22 State handler + sync fixes (Jan 12)
         ├── 1fcbe42e Smart logging for InputManager
         └── 84c34450 Movement in anticipate + UI + PaniMuktha
                     │
                     ▼
              (diverged from main)
```

---

## HEADLESS (AUM-Headless) Branch Tree

```
                                 REMOTE: origin (GitHub)
                                 ════════════════════════
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    ▼                                           ▼
            origin/main                          origin/feature/authoritative-architecture
                 │                                              │
    [Production Release]                            [7b19179] Jan 25 2026
                 │                                              │
                 │                                              ├── Server stamina sync
                 │                                              ├── Bot decision fixes
                 │                                              └── 12 files changed
                                                                │
                                 LOCAL BRANCHES                 │
                                 ══════════════                 │
                                          │                     │
                    ┌─────────────────────┴─────────────────────┤
                    │                                           │
                    ▼                                           ▼
                 main                          feature/authoritative-architecture
            (tracks origin/main)                    (tracks origin/feature/...)
                    │                                           │
                    │                                   ┌───────┴───────┐
                    │                                   │               │
                    │                                   ▼               │
                    │                          [7b19179] HEAD           │
                    │                          "Jan 25 2026: Server     │
                    │                           stamina sync, bot fixes"│
                    │                                   │               │
                    │                          21 commits ahead ────────┘
                    │                          of main
                    │
                    └──────── Merge Point (after testing) ──────────────►
```

### HEADLESS Commit History (feature/authoritative-architecture)

```
HEAD ──► 7b19179 Jan 25 2026: Server stamina sync, bot fixes, authoritative
         │
         ├── 2c1b74d Fix focus generation - Server AddFocus (Jan 24)
         ├── 4fe787f Revert server dodge to legacy pattern
         ├── 63da581 Fix infinite attack loop: melee re-entry grace
         ├── 506be01 WIP: Almost working gameplay ticking (Jan 22)
         ├── 9a3d903 WIP: Jan 16 playtest fixes + 60Hz tick
         ├── 5f04475 Add shared AI configuration (CLAUDE.md)
         ├── 1ce05eb Backup before unified input
         ├── 8ceafc6 Remove redundant ClientLog.cs, SyncDebugger.cs
         ├── 3e53174 Fix ACTION REJECTION logging errors
         ├── 2d89c42 Add ACTION REJECTION logging
         ├── 85eec73 Remove duplicate ValidatedLogger
         ├── f1016f3 ValidatedLogger cleanup
         ├── f859d52 Validated logging for server
         ├── f962576 Add Claude Code + MCP config
         ├── f4c12fa Entity, network, combat fixes (Jan 12)
         ├── 15d4b9e Combat Authority enhancements (Jan 12)
         ├── 61ee0c0 Bot AI enhancements (Jan 12)
         ├── 354c276 Timing + validation fixes (Jan 12)
         ├── d16e5c1 Fix Bot attack frenzy + flickering
         ├── bb80247 Smart logging workflow
         └── 7d0479b Movement in anticipate states
                     │
                     ▼
              (diverged from main)
```

---

## Sync Status Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SYNC STATUS (Jan 25, 2026)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AUM-The-Epic (CLIENT)                                                      │
│  ═══════════════════════════════════════════════════════════════════════    │
│  Branch: feature/authoritative-architecture                                 │
│  Local:  45bc7c47  ◄──── SYNCED ────► origin: 45bc7c47                     │
│  Status: ✓ PUSHED TO ORIGIN                                                 │
│  Ahead of main: 29 commits                                                  │
│                                                                             │
│  AUM-Headless (SERVER)                                                      │
│  ═══════════════════════════════════════════════════════════════════════    │
│  Branch: feature/authoritative-architecture                                 │
│  Local:  7b19179   ◄──── SYNCED ────► origin: 7b19179                      │
│  Status: ✓ PUSHED TO ORIGIN                                                 │
│  Ahead of main: 21 commits                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Workflow

```
                    DEVELOPMENT CYCLE
═══════════════════════════════════════════════════════════════════════════════

  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
  │ Develop │────►│  Commit │────►│  Push   │────►│  Build  │────►│  Test   │
  │ & Fix   │     │         │     │ origin  │     │   iOS   │     │ Device  │
  └─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
       │                                                               │
       │                                                               │
       │                                                               ▼
       │                                                        ┌─────────────┐
       │                                          ┌─────────────│ Tests Pass? │
       │                                          │             └─────────────┘
       │                                          │                    │
       │                                    NO    │              YES   │
       │                                    ┌─────┘                    ▼
       │                                    │                   ┌─────────┐
       ◄────────────────────────────────────┘                   │  Merge  │
       Fix issues found                                         │ to main │
                                                                └─────────┘
                                                                      │
                                                                      ▼
                                                                ┌─────────┐
                                                                │ Deploy  │
                                                                │ Server  │
                                                                │ Hetzner │
                                                                └─────────┘

═══════════════════════════════════════════════════════════════════════════════

                    CURRENT POSITION: ● PUSHED TO ORIGIN
                    NEXT STEP: Build iOS for device testing
```

---

## File Change Summary (This Session)

### CLIENT Changes (30 files)
```
┌─────────────────────────────────────────────────────────────────┐
│ Category          │ Files │ Key Changes                        │
├───────────────────┼───────┼────────────────────────────────────┤
│ Characters        │   7   │ Animation fixes, state callbacks   │
│ Combat Authority  │   4   │ Focus streak prep, validation      │
│ Managers          │   5   │ Stamina sync, simulation           │
│ Network/Player    │   6   │ Packet stamina field, input        │
│ Config/Editor     │   8   │ LocalTestingSettings, builds       │
└───────────────────┴───────┴────────────────────────────────────┘
```

### HEADLESS Changes (12 files)
```
┌─────────────────────────────────────────────────────────────────┐
│ Category          │ Files │ Key Changes                        │
├───────────────────┼───────┼────────────────────────────────────┤
│ Bots              │   1   │ Decision timing, state reading     │
│ Combat Authority  │   2   │ Server validation, base auth       │
│ Managers          │   2   │ Logger, GameManager                │
│ Network           │   2   │ Packet stamina, local config       │
│ Player            │   3   │ PlayerManager stamina sync         │
│ State Machine     │   1   │ Transition handling                │
│ Config            │   1   │ Build settings                     │
└───────────────────┴───────┴────────────────────────────────────┘
```
