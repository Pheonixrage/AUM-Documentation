# AUM Architecture Blueprint — World-Class Fighting Game

**Version:** 3.0 (Body/Mind/Spirit)
**Date:** February 22, 2026
**Target:** Full Global Launch — June 2026
**Scale:** 1,000–5,000 CCU (regional → global)
**Platforms:** iOS + Android + Windows

---

## 1. VISION & DESIGN PILLARS

### What Makes AUM World-Class

AUM competes at the intersection of three markets no game has combined:

| Pillar | Standard | Benchmark |
|--------|----------|-----------|
| **Competitive Fighting** | Frame-perfect combat, rollback netcode, esports-ready | Tekken 8, Street Fighter 6 |
| **Mobile-First UX** | 60fps on phones, thumb-friendly, 3-second match entry | Brawl Stars, Genshin Impact |
| **Mythology Depth** | Karma/Guna/Trinity as living game systems, not skins | Unique — no competitor |

### Core Principles

1. **Server Authority is Non-Negotiable** — Every combat outcome validated server-side
2. **Predict Locally, Reconcile Gracefully** — Responsive feel despite network latency
3. **Design for 5K CCU, Architect for 50K** — Horizontal scaling from day 1
4. **Three Pillars, One Vision** — Body (Client), Mind (Server), Spirit (Design) evolve together
5. **Hindu Philosophy as Gameplay, Not Cosmetics** — Karma affects matchmaking, Guna shapes abilities

---

## 2. THE THREE PILLARS

```
                        ┌─────────────────┐
                        │     SPIRIT      │
                        │  (Design/Docs)  │
                        │  AUM-Documentation│
                        │  AUM_SPIRIT     │
                        └────────┬────────┘
                                 │ Defines
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐          ┌──────▼─────┐
              │   BODY    │          │    MIND    │
              │  (Client) │◄════════►│  (Server)  │
              │ AUM-Epic  │ LiteNet  │AUM-Headless│
              │ AUM_BODY  │   Lib    │ AUM_MIND   │
              └─────┬─────┘          └──────┬─────┘
                    │                       │
                    │    ┌──────────┐       │
                    └───►│  NAKAMA  │◄──────┘
                         │(Backend) │
                         │Singapore │
                         └──────────┘
```

### BODY (Client — AUM-The-Epic)
- Unity 2022.3 LTS
- Handles: Rendering, Input, Prediction, VFX, Audio, UI
- Branch: `AUM_BODY`
- Talks to: Mind (LiteNetLib UDP), Nakama (WebSocket + REST)

### MIND (Server — AUM-Headless)
- Unity Headless Linux Build
- Handles: Authority, Validation, State, Bots, Match Logic
- Branch: `AUM_MIND`
- Talks to: Body (LiteNetLib UDP), Nakama (HTTP RPCs)

### SPIRIT (Design — AUM-Documentation)
- Architecture decisions, session logs, protocol specs
- Branch: `AUM_SPIRIT`
- Guides: Both Body and Mind implementation

### NAKAMA (Backend — Self-Hosted)
- Go runtime with 34+ RPCs
- PostgreSQL 16 for persistence
- Docker Compose on Hetzner Singapore (5.223.55.127)
- Handles: Auth, Economy, Inventory, Social, Matchmaking queue, Leaderboards

---

## 3. SYSTEM ARCHITECTURE (12 Core Systems)

```
┌─────────────────────────── CLIENT (BODY) ──────────────────────────────┐
│                                                                         │
│  ┌─INPUT──┐  ┌─STATE──┐  ┌─COMBAT─┐  ┌─ENTITY─┐  ┌──SYNC──┐         │
│  │InputMgr│→ │StateMgr│→ │ICombat │→ │SpellMgr│→ │Reconcil│         │
│  │Unified │  │20+State│  │Authrity│  │Projecti│  │Visual  │         │
│  │Provider│  │Machine │  │3 Modes │  │Manager │  │Interp  │         │
│  └────┬───┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘         │
│       │          │           │           │           │                │
│       ▼          ▼           ▼           ▼           ▼                │
│  ┌───────────────────── NETWORK LAYER ──────────────────────┐         │
│  │  NetworkManager → PacketManager → SimulationManager      │         │
│  │  InputBuffer → ClockSyncManager → LiteNetLib UDP         │         │
│  └──────────────────────────┬───────────────────────────────┘         │
│                             │                                         │
└─────────────────────────────┼─────────────────────────────────────────┘
                              │ UDP Packets (60 Hz)
                              ▼
┌─────────────────────── SERVER (MIND) ──────────────────────────────────┐
│                                                                         │
│  ┌──TICK──┐  ┌──MATCH─┐  ┌─COMBAT─┐  ┌───BOT──┐  ┌──END───┐         │
│  │Server  │→ │Match   │→ │Server  │→ │BotBrain│→ │MatchEnd│         │
│  │Manager │  │Control │  │Authrity│  │Executor│  │Manager │         │
│  │GameLoop│  │States  │  │Validate│  │Decision│  │Rewards │         │
│  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘         │
│      │           │           │           │           │                │
│      ▼           ▼           ▼           ▼           ▼                │
│  ┌───────────────────── AUTHORITY LAYER ────────────────────┐         │
│  │  ICombatAuthority → ServerAuthority → PlayerManager      │         │
│  │  All mutations validated → Broadcast to clients          │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP RPCs
                             ▼
┌─────────────────────── NAKAMA (BACKEND) ────────────────────────────────┐
│                                                                         │
│  ┌──AUTH──┐  ┌─ECONOMY┐  ┌─SOCIAL─┐  ┌─MATCH──┐  ┌─KARMA──┐         │
│  │Google→ │  │8 Curr/ │  │Friends │  │Property│  │Guna   │         │
│  │Firebase│  │Avatar  │  │Party   │  │Based   │  │Hell   │         │
│  │→Nakama │  │Wallets │  │Chat    │  │Queue   │  │Meditat│         │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘         │
│                                                                         │
│  PostgreSQL 16 │ Docker Compose │ Go Runtime │ 34+ RPCs               │
│  Singapore VPS │ 5.223.55.127   │ Ports 7350-7352                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. AUTHORITY HIERARCHY

```
                    ICombatAuthority (Interface)
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
LocalAuthority      HybridAuthority      ServerAuthority
(Tutorial/Training) (First Match)        (Competitive)

 - No network        - Local physics     - Full server validation
 - Instant feedback   - Damage multipliers- Prediction + reconciliation
 - Bot via local AI   - Bot fallback      - Authoritative state
```

### Authority Contract (ICombatAuthority)
Every combat operation flows through this interface:
- **Queries**: `GetStamina()`, `GetFocus()`, `GetWillpower()`, `IsAbilityAllowed()`
- **Mutations**: `ConsumeStamina()`, `ConsumeFocus()`, `ApplyDamage()`, `ResetPlayer()`
- **Events**: `OnDamageApplied`, `OnPlayerDeath`, `OnStateChanged`
- **Rollback**: `SaveSnapshot()`, `RestoreSnapshot()`, `GetStateAtTick()`

---

## 5. COMBAT ARCHITECTURE — Frame-Perfect Design

### Tick-Based Combat Loop (60 Hz)
```
Every FixedUpdate (16.67ms):
  CLIENT:
    1. Poll input → InputBuffer.Add(tick, input)
    2. Predict locally → StateManager.ExecuteStateUpdate(tick)
    3. Send input to server → PacketManager.Send(PlayerInput)
    4. Apply visual interpolation → VisualInterpolator.Smooth()

  SERVER:
    1. Receive input → InputValidator.Validate(input)
    2. Process → PlayerManager.ProcessPlayerInputTick(player, input)
    3. Update state → StateManager.ExecuteStateUpdate(tick)
    4. Broadcast → WorldSnapshot to all clients
    5. Bot tick → BotBrain.Think(serverTick) → process same as player
```

### State Machine (20+ States)
```
Idle ←→ Melee ←→ Melee_Second
  ↕         ↕
Channel → Spell_Aiming → Spell_Anticipate → Cast_Spell
  ↕
Dodge ←→ Idle
  ↕
Stun → Idle
  ↕
Death → Respawn → Teleport → Idle
  ↕
Special_Aiming → Special_Anticipate → Special
  ↕
Third_Eye_Anticipate → Third_Eye → Idle
  ↕
Astra_Anticipate → Astra_Channel → Astra_Cast → Idle
```

### Hit Confirmation Flow
```
CLIENT (attacker):
  1. Detect hit collision locally
  2. Play VFX immediately (prediction)
  3. Send HitAttempt(tick, targetId, damage) to server

SERVER:
  4. Validate: distance, timing, attacker state, target state
  5. Calculate: elemental interaction, god modifier, shield reduction
  6. Apply: authority.ApplyDamage(targetId, finalDamage)
  7. Broadcast: DamagePacket to all clients

CLIENT (all):
  8. Reconcile: adjust prediction if server disagrees
  9. Display: damage number, health bar update, hit effects
```

### Elemental Creation Cycle
```
        ETHER ──creates──► AIR
          ▲                  │
          │               creates
       creates               │
          │                  ▼
        EARTH ◄──creates── FIRE
          ▲                  │
          │               creates
           ─── WATER ◄─────┘

Child → Parent = NULLIFY (cancel)
Parent → Child = VULNERABLE (+25%)
Other = MITIGATE (-25%)
```

### Resource Economy
| Resource | Max | Regen | Strategic Role |
|----------|-----|-------|----------------|
| Willpower | 15,000 | None | Win condition — reduce to 0 |
| Stamina | 100 | 10/sec | Dodge economy — when to commit |
| Focus | 100 (4 bars) | Via hit-streak | Ability access — aggression rewards |

---

## 6. BOT AI ARCHITECTURE — World-Class Net-First Design

### Design Philosophy
Bots must be **indistinguishable from human players** at the network level. Every bot action flows through the same authority pipeline as player input.

### Architecture
```
┌────────────────── BOT PIPELINE (Server-Side Only) ──────────────────┐
│                                                                      │
│  ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌───────────┐      │
│  │BotState  │───►│BotBrain │───►│BotDecision│───►│BotExecutor│      │
│  │Reader    │    │         │    │Manager   │    │          │      │
│  └──────────┘    └─────────┘    └──────────┘    └───────────┘      │
│       │               │              │               │              │
│  Observes:       Thinks:        Decides:        Executes:          │
│  - Enemy state   - Threats      - Attack type   - Generates       │
│  - Own resources - Opportunities- Target        - KeyInput        │
│  - Match state   - Risk/reward  - Timing        - Fed into        │
│  - Distance      - Personality  - Resource use  - PlayerManager   │
│                                                                      │
│  ┌──────────────── INTELLIGENCE MODULES ─────────────────┐          │
│  │                                                        │          │
│  │  ┌─ThreatAssess─┐  ┌─OpportunityDet┐  ┌─ResourceTrk┐│          │
│  │  │ Incoming dmg  │  │ Vuln windows  │  │ Stamina pred││          │
│  │  │ Ability cooldn│  │ Punish frames │  │ Focus track ││          │
│  │  │ Position risk │  │ Elemental adv │  │ HP threshold││          │
│  │  └───────────────┘  └───────────────┘  └─────────────┘│          │
│  │                                                        │          │
│  │  ┌─ElementalAI──┐  ┌─Humanization──┐  ┌─Personality─┐│          │
│  │  │ Cycle aware   │  │ Reaction delay│  │ Aggression  ││          │
│  │  │ Counter-pick  │  │ Input noise   │  │ Defense pref││          │
│  │  │ Combo setup   │  │ Occasional err│  │ Risk toler  ││          │
│  │  └───────────────┘  └───────────────┘  └─────────────┘│          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                      │
│  ┌──────────────── DIFFICULTY SCALING ───────────────────┐          │
│  │  Easy: 300ms react, 40% accuracy, passive style       │          │
│  │  Medium: 200ms react, 60% accuracy, balanced          │          │
│  │  Hard: 100ms react, 80% accuracy, aggressive          │          │
│  │  Extreme: 50ms react, 95% accuracy, optimal play      │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                      │
│  CRITICAL: Bot → KeyInput → PlayerManager.ProcessPlayerInputTick()  │
│  Same pipeline as human players. No state shortcuts.                │
└──────────────────────────────────────────────────────────────────────┘
```

### Bot Behaviors (World-Class Requirements)
| Behavior | Easy | Medium | Hard | Extreme |
|----------|------|--------|------|---------|
| **Melee combos** | 1-2 hit chains | 3-hit chains | Full combos + mix-ups | Frame-perfect chains |
| **Dodging** | Random dodge | Dodge on hit-react | Dodge on animation read | I-frame dodge |
| **Spell usage** | Random element | Counter-element | Cycle-aware combos | Optimal DPS rotation |
| **Shield play** | Never | On low HP | Read enemy casting | Perfect timing |
| **Focus management** | Spam at 1 bar | Save for 2 bars | Strategic 3-bar plays | Optimal resource use |
| **Positioning** | Stand still | Maintain range | Zone control | Perfect spacing |

---

## 7. NETWORKING ARCHITECTURE — Rollback-Style Design

### Network Stack
```
Application Layer:  StateManager, CombatAuthority, PlayerManager
                         ↕
Transport Layer:    PacketManager (serialize/deserialize)
                         ↕
Protocol Layer:     SimulationManager (prediction, reconciliation)
                         ↕
Network Layer:      LiteNetLib (reliable/unreliable UDP channels)
                         ↕
Clock Layer:        ClockSyncManager (server tick synchronization)
```

### Packet Types
| Packet | Direction | Channel | Purpose |
|--------|-----------|---------|---------|
| PlayerInput | C→S | Unreliable | Input per tick |
| WorldSnapshot | S→C | Unreliable | Full state per tick |
| DamagePacket | S→C | Reliable | Damage events |
| StateChange | S→C | Reliable | State transitions |
| SpellCast | Bidirectional | Reliable | Spell data |
| PositionSync | S→C | Unreliable | Position corrections |

### Reconciliation Strategy
```
On receiving WorldSnapshot(serverTick, serverState):
  1. Compare serverState vs localPrediction[serverTick]
  2. If match → prediction correct, continue
  3. If mismatch:
     a. Snap to server state
     b. Replay all inputs from serverTick to currentTick
     c. Apply visual smoothing (150-250ms lerp)
     d. Log mismatch for analytics
```

### Latency Targets
| Metric | Target | Current |
|--------|--------|---------|
| Input-to-server | < 50ms (same region) | ~30ms Singapore |
| Server-to-display | < 100ms perceived | ~80ms with prediction |
| Hit confirm | < 3 frames (50ms) | 2 frames with local predict |
| Reconciliation | < 250ms visual | 150-250ms tuned |

---

## 8. NAKAMA BACKEND ARCHITECTURE

### Service Map (17 Unity Services → 34+ Go RPCs)

```
┌─────────────── NAKAMA GO SERVER ──────────────────────┐
│                                                        │
│  Auth & Session                                        │
│  ├── AfterAuthenticateCustom (new player init)         │
│  └── Session lifecycle (auto-reconnect from client)    │
│                                                        │
│  Player Data                                           │
│  ├── rpc_get_player_data                               │
│  ├── rpc_save_avatar_data                              │
│  ├── rpc_avatar_sync                                   │
│  └── rpc_player_init                                   │
│                                                        │
│  Economy (Per-Avatar Wallets)                          │
│  ├── rpc_get_avatar_currencies                         │
│  ├── rpc_add_avatar_currency                           │
│  ├── rpc_subtract_avatar_currency                      │
│  ├── rpc_match_end_payout                              │
│  └── rpc_convert_currency (atomic 1000 BZ → 1 SV)     │
│                                                        │
│  Inventory & Store                                     │
│  ├── rpc_get_inventory                                 │
│  ├── rpc_purchase_item                                 │
│  ├── rpc_catalog_items                                 │
│  └── rpc_expand_set                                    │
│                                                        │
│  Karma / Guna / Hell / Meditation                      │
│  ├── rpc_get_karma_state                               │
│  ├── rpc_update_karma                                  │
│  ├── rpc_enter_hell / rpc_check_hell_status            │
│  ├── rpc_meditation_start / rpc_meditation_complete    │
│  └── rpc_modify_lives / rpc_hell_shard                 │
│                                                        │
│  Matchmaking                                           │
│  ├── Nakama matchmaker (property-based WebSocket)      │
│  ├── Bot fallback (timer-based)                        │
│  └── Party matchmaking (group properties)              │
│                                                        │
│  Social                                                │
│  ├── Nakama Friends API (native)                       │
│  ├── rpc_friend_enrichment (career stats)              │
│  ├── rpc_search_friend_code                            │
│  ├── Nakama Groups (party/lobby)                       │
│  ├── Nakama Chat (party + DM channels)                 │
│  └── Nakama Presence (online status)                   │
│                                                        │
│  Leaderboards                                          │
│  ├── Nakama Leaderboard API (native)                   │
│  └── rpc_career_stats_submit                           │
│                                                        │
│  Infrastructure                                        │
│  ├── rpc_name_registry (unique name validation)        │
│  ├── Remote Config (storage-based feature flags)       │
│  └── IAP Receipt Validation (store → Nakama verify)    │
│                                                        │
│  ┌──────────── MISSING (To Build) ──────────┐         │
│  │ rpc_match_history (record + query)        │         │
│  │ rpc_profile_public (public player card)   │         │
│  │ rpc_ranked_season (ELO, ranks, rewards)   │         │
│  │ rpc_tournament (brackets, scheduling)     │         │
│  │ rpc_clan_system (guild management)        │         │
│  │ rpc_daily_rewards (login streaks)         │         │
│  │ rpc_battle_pass (seasonal progression)    │         │
│  └───────────────────────────────────────────┘         │
│                                                        │
│  PostgreSQL 16 │ Docker Compose │ Hetzner Singapore    │
└────────────────────────────────────────────────────────┘
```

### Data Model
```
Collections:
  players/          → Player account data, preferences
  avatars/          → Per-avatar stats, loadout, cosmetics
  inventory/        → Owned items per avatar
  catalog/          → System-owned item definitions
  name_registry/    → Unique name reservations
  karma/            → Karma state, guna percentages
  hell/             → Hell dimension progress

Wallets (per avatar):
  bronze, silver, gold, lives, timeShards, hellShards, bhaktiTokens, gnanaTokens

Leaderboards:
  kills_weekly, wins_monthly, karma_alltime, elo_ranked
```

---

## 9. SOCIAL SYSTEMS — Party, Friends, Chat

### Party System (Nakama Groups)
```
Create Party → NakamaPartyService.CreateParty()
  → Nakama Group created (max 3 players for Trio)
  → Party leader sets match preferences
  → Members join group chat channel

Invite Friend → NakamaPartyService.InviteToParty()
  → Nakama notification sent
  → Friend joins group
  → Party state synced via presence

Start Match → NakamaMatchmaker.FindMatch(partyProperties)
  → All party members enter matchmaker together
  → Property-based matching (ELO range, party size)
  → On match found → all members get MatchFoundPopup
```

### Friends System (Nakama Native)
```
Add Friend → NakamaFriendsService.SendFriendRequest()
  → Nakama friend request (native API)
  → Notification to target player
  → Accept/Decline via UI

Friend Code → NakamaFriendsService.SearchByFriendCode()
  → RPC lookup in name_registry
  → Return enriched friend data (avatar, stats, online status)

Presence → NakamaSocialManager.TrackPresence()
  → WebSocket presence events
  → Real-time online/offline/in-match status
```

---

## 10. MYTHOLOGY INTEGRATION — The Differentiator

### Karma as Matchmaking Factor
```
Player Karma Score → Affects matchmaking pool:
  High Karma (Sattvic) → Matched with other honorable players
  Medium Karma (Rajasic) → Standard pool
  Low Karma (Tamasic) → Toxic pool, longer queues

Karma earned by:
  + Fair play, completing matches, helping newer players
  - Rage quitting, toxic behavior, exploiting
```

### Guna System (Character Growth)
```
Three Gunas shape ability scaling:
  Sattva (Purity) → Enhanced healing, shields, support
  Rajas (Passion) → Enhanced damage, speed, aggression
  Tamas (Inertia) → Enhanced durability, control, disruption

Player choices in matches shift Guna balance:
  Defensive play → +Sattva
  Aggressive play → +Rajas
  Controlling play → +Tamas
```

### Hell Dimension (Redemption Arc)
```
Low Karma triggers Hell entry:
  → Special map with unique challenges
  → Earn Hell Shards to redeem karma
  → Time-limited (real-time timer)
  → Meditation system for karma recovery
```

### Trinity Gods (Strategic Layer)
```
Pre-match god selection adds strategic depth:
  Brahma → Focus generation (aggression sustain)
  Vishnu → Mobility (positioning advantage)
  Shiva → Raw power (burst damage)

Counter-play: God choice visible → opponent adapts strategy
```

---

## 11. MOBILE UX ARCHITECTURE

### Performance Targets
| Metric | iOS | Android | Windows |
|--------|-----|---------|---------|
| FPS | 60fps (iPhone 12+) | 60fps (SD 865+) | 120fps |
| Load time | < 5s cold start | < 5s cold start | < 3s |
| Memory | < 1.2 GB | < 1.0 GB | < 2.0 GB |
| Battery | 3hr gameplay | 3hr gameplay | N/A |
| Download | < 500 MB | < 500 MB | < 1 GB |

### Input Abstraction
```
UnifiedInputProvider
  ├── TouchInput (mobile)
  │   ├── Virtual joystick (movement)
  │   ├── Tap buttons (actions)
  │   └── Swipe gestures (dodge direction)
  │
  ├── KeyboardInput (desktop)
  │   ├── WASD (movement)
  │   ├── Mouse click (attack)
  │   ├── 1-4 keys (spells)
  │   └── Space (dodge)
  │
  └── GamepadInput (controller)
      ├── Left stick (movement)
      ├── Right trigger (attack)
      ├── Face buttons (abilities)
      └── Bumpers (dodge/shield)
```

### UI Design Principles
1. **One-thumb navigation** — Core actions reachable with right thumb
2. **3-second rule** — Any action should be 3 taps or less from main menu
3. **Progressive disclosure** — New players see simple UI, complexity unlocks
4. **Visual hierarchy** — Most important info (HP, stamina, focus) always visible
5. **Haptic feedback** — Impact feel on hit confirms (mobile vibration)

---

## 12. BUILD & DEPLOY PIPELINE

### Multi-Platform Build Matrix
```
┌──────────── BUILD PIPELINE ────────────────┐
│                                             │
│  Source: AUM-The-Epic (AUM_BODY branch)     │
│                                             │
│  ┌─── macOS Build Host ───┐                 │
│  │ iOS (arm64)            │→ TestFlight     │
│  │ macOS (x64/arm64)      │→ Dev testing    │
│  └────────────────────────┘                 │
│                                             │
│  ┌─── Windows Build Host ──┐                │
│  │ Android (arm64-v8a)     │→ Play Store    │
│  │ Windows (x64)           │→ Steam/Direct  │
│  └─────────────────────────┘                │
│                                             │
│  Source: AUM-Headless (AUM_MIND branch)     │
│                                             │
│  ┌─── Linux Build ─────────┐                │
│  │ Headless Server (x64)   │→ Hetzner VPS   │
│  └─────────────────────────┘                │
│                                             │
│  Nakama Backend:                            │
│  ┌─── Docker Deploy ───────┐                │
│  │ docker-compose up -d    │→ Singapore VPS  │
│  └─────────────────────────┘                │
└─────────────────────────────────────────────┘
```

### Deployment Workflow
```
1. Code change → AUM_BODY or AUM_MIND branch
2. /sync-headless → Sync shared code client ↔ server
3. Local playtest (Editor + Headless)
4. Build:
   - Client: Unity batch mode → platform binary
   - Server: Unity headless → Linux binary
5. Deploy server: scp → Hetzner → systemctl restart
6. Deploy client: Upload to TestFlight/Play Store/Steam
7. Verify: Tail logs 30s, check port 7777 UDP
```

---

## 13. TESTING INFRASTRUCTURE

### Test Matrix
| Test Type | Environment | Frequency |
|-----------|-------------|-----------|
| **Unit Tests** | Local Editor | Every commit |
| **Integration** | Singapore server | Every feature |
| **Playtest** | Singapore server | Daily |
| **Load Test** | Singapore server | Weekly |
| **Cross-Platform** | iOS + Android + Win | Per milestone |

### Singapore Dev Server (5.223.55.127)
```
Services:
  - Nakama (Docker): ports 7350-7352
  - Game Server (Headless): port 7777 UDP
  - Orchestrator: manages server instances

Monitoring:
  - MCP log tools (client + server)
  - Nakama console (port 7351)
  - systemctl status for game server
```

### Automated Playtest Pipeline (AutoDev)
```
/autodev "description"
  1. Investigate → Read logs, trace code
  2. Implement → Write fix/feature
  3. Verify → Build + launch playtest
  4. Screenshot → Capture game state
  5. Simulate input → Test gameplay
  6. Check logs → Verify no errors
  7. Commit → Atomic commit
  8. Push → To AUM_BODY/AUM_MIND
  9. Deploy → To Singapore dev server
```

---

## 14. SCALE ARCHITECTURE (1K-5K CCU)

### Horizontal Scaling Plan
```
Phase 1 (Launch): Single Nakama + 4 Game Servers
  Nakama: 1x (Singapore) — handles 5K sessions
  Game Servers: 4x Hetzner VPS — 250 matches each

Phase 2 (Growth): Multi-Region
  Nakama: 2x (Singapore + EU) — PostgreSQL replication
  Game Servers: 8x per region — 2000 matches total

Phase 3 (Scale): Kubernetes
  Nakama: K8s cluster with auto-scaling
  Game Servers: K8s pods with matchmaker-aware scheduling
```

### CCU Capacity Planning
| Component | Per Instance | 1K CCU | 5K CCU |
|-----------|-------------|--------|--------|
| Nakama | 5,000 sessions | 1 instance | 1 instance |
| Game Server | 50 matches (100 players) | 10 servers | 50 servers |
| PostgreSQL | 10K queries/sec | 1 instance | 1 instance (with read replicas) |
| Bandwidth | 2 KB/s per player | 2 MB/s | 10 MB/s |

---

## 15. FEATURE COMPLETENESS MAP

### Existing (Done)
- [x] Authentication (Google → Firebase → Nakama)
- [x] Avatar CRUD + 5 fighting styles
- [x] Combat Authority (Local/Hybrid/Server)
- [x] State Machine (20+ states)
- [x] Networking (LiteNetLib + prediction + reconciliation)
- [x] Economy (8 currencies per avatar)
- [x] Inventory + Store/Catalog
- [x] Matchmaking (property-based + bot fallback)
- [x] Karma/Guna/Hell/Meditation
- [x] Leaderboards
- [x] Social Presence + Chat
- [x] Tutorial Mode (LocalAuthority)
- [x] Training Mode
- [x] First Match (HybridAuthority)
- [x] MCP Tooling (autonomous development)
- [x] iOS Build (TestFlight live)

### To Build (Gap)
- [ ] Party System (Nakama-native rebuild)
- [ ] Friends System (full UI + Nakama integration)
- [ ] Profile System (public player cards)
- [ ] Match History (record + display)
- [ ] Bot AI (world-class rebuild)
- [ ] Ranked System (ELO, seasons, rewards)
- [ ] Daily Rewards / Battle Pass
- [ ] Tournament System
- [ ] Clan/Guild System
- [ ] Android Build (keystore resolution)
- [ ] Windows Build (Steam integration)
- [ ] Discord Integration (Social SDK)
- [ ] Push Notifications (FCM)
- [ ] Data Migration (PlayFab → Nakama for existing players)

---

## 16. MODULAR GAME MODE ARCHITECTURE (MMORPG-Style)

### Design Pattern
Every game mode is a self-contained plugin that registers with a central registry. Same pattern as ICombatAuthority — combat code never knows which authority it talks to; game code never knows which mode it's in.

### Layer 1: Game Mode Definition (ScriptableObject)
```csharp
[CreateAssetMenu(menuName = "AUM/Game Mode")]
public class GameModeDefinition : ScriptableObject
{
    public string modeId;                      // "arena_1v1", "raid_4player", "survival"
    public AuthorityType authorityType;         // Which ICombatAuthority implementation
    public int minPlayers, maxPlayers;
    public string sceneName;                    // Unity scene for this mode
    public string nakamaMatchHandler;           // Server-side match handler name
    public AssetReference[] requiredAssets;      // Addressable assets for this mode
    // Game-specific rules (timers, rounds, win conditions) configured here
}
```

### Layer 2: Game Mode Interface + Registry
```csharp
public interface IGameMode
{
    string ModeId { get; }
    GameModeDefinition Definition { get; }
    ICombatAuthority CreateAuthority();   // Each mode picks its authority
    void OnModeEnter();                   // Setup
    void OnModeTick(float deltaTime);     // Per-tick logic
    void OnModeExit();                    // Cleanup
}

// Modes register themselves at startup via assembly scanning
// New modes in separate ASMDEFs auto-register without touching core
```

### Layer 3: Assembly Definitions (Module Isolation)
```
Assets/Scripts/
├── AUM.Core.asmdef                      (ICombatAuthority, StateManager, shared types)
├── AUM.Networking.asmdef                (NetworkManager, PacketManager, SimulationManager)
├── AUM.Backend.asmdef                   (Nakama/, Data/)
├── AUM.Input.asmdef                     (InputManager, UnifiedInputProvider)
├── AUM.UI.asmdef                        (UI screens, managers)
├── AUM.Bots.asmdef                      (BotBrain, BotExecutor)
├── AUM.Analytics.asmdef                 (AUMLogger, analytics)
│
├── GameModes/
│   ├── AUM.GameModes.Core.asmdef        (IGameMode, GameModeDefinition, Registry)
│   ├── Arena/
│   │   └── AUM.GameModes.Arena.asmdef   (Current 1v1/duo/trio PvP)
│   ├── Tutorial/
│   │   └── AUM.GameModes.Tutorial.asmdef (Current tutorial mode)
│   ├── Training/
│   │   └── AUM.GameModes.Training.asmdef (Current training mode)
│   └── [Future modes as new ASMDEFs]
│       ├── Coop/AUM.GameModes.Coop.asmdef
│       ├── Dungeon/AUM.GameModes.Dungeon.asmdef
│       └── Survival/AUM.GameModes.Survival.asmdef
```

**Benefits:**
- Change Arena code → only Arena recompiles (~2s vs 15-30s full)
- Prototype Coop and Dungeon in parallel — zero merge conflicts
- Remove a mode = delete its ASMDEF folder, no core changes
- Each mode has its own authority, Nakama handler, and assets

### Layer 4: Nakama Match Handlers (Per-Mode Server Logic)
```
nakama-server/
├── main.go                              (registers all handlers)
├── handlers/
│   ├── arena_pvp.go                     (current 1v1/duo/trio)
│   ├── tutorial.go                      (tutorial match handler)
│   ├── training.go                      (training match handler)
│   └── [future handlers per mode]
```

Each handler implements `MatchInit`, `MatchLoop`, `MatchTerminate`. The client's `GameModeDefinition.nakamaMatchHandler` field routes to the correct handler.

### Layer 5: Addressable Content (DLC/Expansion Pattern)
```
Addressable Groups:
├── Core (always loaded: combat, UI, shared)     ~50 MB
├── Arena_PvP (arena maps, VFX)                  ~20 MB
├── Tutorial (tutorial assets)                    ~10 MB
├── [Future expansion groups]                    ~XX MB per mode
```

New modes ship as downloadable content. Players only download modes they play. Patches update individual groups without full app update.

---

## 17. DATA-DRIVEN BALANCE & CONFIGURATION

### ScriptableObject Balance Configs
All combat values externalized to ScriptableObjects for live tuning:

```
Assets/Data/Balance/
├── CombatBalanceConfig.asset          — Damage values, costs, cooldowns
├── ElementalConfig.asset              — Element cycle, interaction multipliers
├── AmukthaConfig.asset                — Fighting style stats
├── MukthaMukthaConfig.asset
├── MantraMukthaConfig.asset
├── YantramukhtaConfig.asset
├── PaniMukthaConfig.asset
├── GodBlessingConfig.asset            — Trinity god bonuses
└── [Per-mode configs]
    ├── ArenaConfig.asset              — Arena-specific rules
    ├── TutorialConfig.asset           — Tutorial-specific rules
    └── TrainingConfig.asset           — Training-specific rules
```

### Remote Balance Updates (Nakama Remote Config)
```
Pattern: Nakama storage → JSON balance overrides → Client applies on startup

Nakama storage (system-owned):
  collection: "remote_config"
  key: "balance_v1"
  value: { "amuktha_melee_damage": 100, "dodge_stamina_cost": 70, ... }

Client startup:
  1. Load local ScriptableObject defaults
  2. Fetch remote_config from Nakama
  3. Override any values that differ
  4. No app update needed for balance patches
```

**Existing foundation:** `ContentVersionManager.cs` + `NakamaRemoteConfig.cs` already handle remote config. Extend to cover balance data.

---

## 18. CONTENT PIPELINE & EXPANSION SYSTEM

### How Updates Ship
```
Balance Patch (no app update):
  → Tune SO in Editor → Push to Nakama remote_config
  → Clients pull new values on next launch

Content Patch (small app update):
  → New Addressable assets uploaded to CDN
  → Clients download on next launch, no full reinstall

New Game Mode (expansion):
  → New ASMDEF folder with mode code
  → New Addressable group with mode assets
  → New Nakama match handler
  → Ship as DLC or bundled update

Server Patch:
  → Build headless Linux binary → scp to Hetzner
  → systemctl restart → 30s log verification

Full Version Update:
  → New client build → App Store / Play Store / Steam
  → New server build → Hetzner
  → New Nakama RPCs → docker-compose restart
```

### Reusability Across Games
The ASMDEF module structure enables:
- `AUM.Core` (combat authority, state machine) = reusable package
- `AUM.Backend` (Nakama services) = reusable package
- `AUM.Input` (unified input) = reusable package
- Game-specific code lives only in `GameModes/{ModeName}/`

Future games import core packages as Git dependencies and build their own game modes on top.

---

## 19. INFRASTRUCTURE & AUTOMATION

### CI/CD Pipeline (GameCI + GitHub Actions)
```yaml
On push to AUM_BODY:
  1. Build client (Windows, Mac, Linux)
  2. Run unit tests
  3. Upload build artifacts

On push to AUM_MIND:
  1. Build headless server (Linux)
  2. Deploy to Singapore staging via SSH
  3. Tail logs 30s, verify clean startup

On merge to main:
  1. Full build matrix (iOS, Android, Windows)
  2. Deploy to production
```

### Analytics & Monitoring Stack
| Tool | Purpose | Cost |
|------|---------|------|
| **Metabase** | BI dashboards (win rates, retention, economy) | Free (open source) |
| **Prometheus + Grafana** | Real-time server monitoring, alerts | Free (open source) |
| **ELK Stack** | Centralized log aggregation, search | Free (open source) |

All deploy as Docker containers alongside Nakama on Singapore server.

### Future-Proofing
| Technology | Phase 1 (June 2026) | Future |
|------------|---------------------|--------|
| **Blockchain** | Data types use UUIDs, optional `blockchain_ref` field | Web3.unity by ChainSafe, Polygon |
| **VR/AR** | UnifiedInputProvider already abstracts input | OpenXR provider, no combat changes |
| **Localization** | Unity Localization package + string tables | AI-assisted translation |
| **Accessibility** | AccessibilityManager settings hub | Colorblind filters, input remapping |

---

*This blueprint is the single source of truth for AUM's June 2026 launch architecture.*
*Updated: February 22, 2026 — Body/Mind/Spirit v3.1 (Modular Architecture)*
