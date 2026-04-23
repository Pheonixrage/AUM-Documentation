# AUM Social & Media Systems — Design Document

**Date:** March 30, 2026
**Status:** Research Complete — Future Implementation
**Pipelines:** All (P1 V2, P2 Production, P3 Legacy)

---

## Table of Contents

1. [Recommended Technology Stack](#1-recommended-technology-stack)
2. [Spectator System](#2-spectator-system)
3. [Replay & Recording System](#3-replay--recording-system)
4. [Voice & Text Chat](#4-voice--text-chat)
5. [Streaming & Social Watching](#5-streaming--social-watching)
6. [SDK Comparison Tables](#6-sdk-comparison-tables)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Cost Projections](#8-cost-projections)
9. [Sources](#9-sources)

---

## 1. Recommended Technology Stack

| System | Choice | Cost | Why |
|--------|--------|------|-----|
| **Voice + Text Chat** | Discord Social SDK | $0 forever | Free at all scales, Rich Presence, game invites, ToxMod moderation, no account required |
| **Voice (fallback)** | Vivox | $0 up to 5K PCU | AAA-proven (Fortnite, Valorant, LoL), native Unity package |
| **Lobby Chat (existing)** | PlayFab CloudScript | $0 | Already working via `SendLobbyChat` handler |
| **Quick-Chat (match)** | Custom enum over LiteNetLib | $0 | 1-byte message IDs, zero moderation needed |
| **Spectator Mode** | Custom on LiteNetLib (20Hz state stream) | $0 | Reuses existing 60Hz server architecture |
| **Replay System** | Hybrid keyframe + delta (.aumr format) | ~$20/mo storage | Server-side recording, immune to balance patches |
| **Cinematic Camera** | Cinemachine 3.x + Timeline | $0 | Unity built-in, free camera + follow + dolly |
| **Video Recording** | Cross Platform Replay Kit (Asset Store) | $25 one-time | iOS ReplayKit + Android MediaProjection unified |
| **Streaming** | Twitch Game Engine Plugin | $0 | Rich Presence, Twitch Drops for engagement |
| **Profanity Filter** | Custom word list + OpenAI Moderation API | $0 | Free tier covers English text moderation |

**Total incremental cost at launch: ~$25 one-time + ~$20/mo**

---

## 2. Spectator System

### How Top Fighting Games Do It

**Street Fighter 6 — Battle Hub:**
- Up to 100 players in shared social space with arcade cabinets
- Walk up to any cabinet to spectate with live inputs + frame data
- ~2-3 second delay, input replay model (deterministic)

**Tekken 8 — Lobby Spectating:**
- Must join lobby before match starts to spectate
- Server-side fixes were needed for multiple simultaneous spectating

**Valve (Dota 2 / CS2) — SourceTV/GOTV:**
- Relay proxy tree: master relay → regional relays → spectators
- Each relay serves up to 255 spectators, relays chain unlimited
- 2-minute delay for competitive integrity
- ~5-20 KB/s per spectator (game state, not video)

**Riot (League of Legends):**
- 3-minute enforced delay, lazy-loaded spectator servers
- HTTP chunks of replay data (~30 second chunks)
- Only loads spectator server when first spectator requests it

### Recommended Architecture for AUM

```
┌─────────────────────────────────────────────────┐
│                  GAME SERVER                     │
│  (Hetzner 65.109.133.129, 60Hz authoritative)   │
│                                                  │
│  Every tick: serialize GameState snapshot         │
│  → SpectatorBuffer (ring buffer, 30s)            │
│  → Push to spectator connections at 20Hz         │
└──────────────┬──────────────────────────────────┘
               │ UDP (state deltas, ~2 KB/s per spectator)
               ▼
┌─────────────────────────────────────────────────┐
│           SPECTATOR CLIENT (read-only)           │
│  iOS / Android / PC — same binary, spectator flag│
│                                                  │
│  - Receives CREATECHARACTER, AVATARSYNC, state   │
│  - No input sent to server                       │
│  - Free camera / follow camera / auto-director   │
│  - Interpolation between 20Hz snapshots          │
│  - HUD: health bars, names, timer, event feed    │
└─────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| Delay | 3-5 seconds | Anti-ghosting for fighting game |
| Data format | State snapshots (not input replay) | AUM is server-authoritative, not deterministic |
| Spectator tick rate | 20Hz (every 3rd tick) | 3x bandwidth savings, interpolation covers gaps |
| Max spectators (Phase 1) | 4 per match | Direct slots on game server, zero extra infra |
| Match discovery | Orchestrator `/live-matches` endpoint | Already tracks active matches |

### Bandwidth Estimates

| Data | Size/tick | At 20Hz |
|------|-----------|---------|
| 2 player positions (Vector3 x 2) | 24 bytes | 480 B/s |
| 2 player rotations (compressed) | 12 bytes | 240 B/s |
| 2 player states (FSM byte x 2) | 2 bytes | 40 B/s |
| Health/stamina/shield (6 vals x 2) | 24 bytes | 480 B/s |
| Animation params (4 floats x 2) | 32 bytes | 640 B/s |
| Combat events (hit/cast/dodge) | ~20 bytes avg | ~100 B/s |
| **Total per spectator** | | **~2 KB/s** |

Mobile-friendly: 2 KB/s = ~7 MB/hour on cellular.

### Scaling Tiers

| Tier | Spectators/Match | Architecture | Cost |
|------|-----------------|--------------|------|
| 1 (launch) | 1-8 | Direct slots on game server | $0 |
| 2 | 9-255 | Single relay proxy per match | ~$5/mo VPS |
| 3 | 256-65K | Relay proxy tree (Valve pattern) | Scale with demand |
| 4 | 65K+ | CDN + HTTP chunks (Riot pattern) | CDN pricing |

### Server Changes Required

- New connection type flag: `ConnectionType.SPECTATOR` in LiteNetLib handshake
- Spectators skip input processing, team assignment, spawn logic
- Send `SpectatorStatePacket` at 20Hz to spectator peers
- Spectators receive existing AVATARSYNC for avatar setup
- Add spectator count to match metadata in orchestrator

### Client Changes Required

- `SpectatorMode` flag in GameManager — disables PlayerInput, CastManager
- `SpectatorCamera` using Cinemachine TargetGroup (frames both players)
- Camera modes: Follow P1/P2, Side View, Free Cam, Auto-Director
- Entry: "Watch" button in lobby UI or friends list
- Spectator HUD: health bars, names, timer, event feed

---

## 3. Replay & Recording System

### Approach: Hybrid Keyframe + Delta (NOT input replay)

AUM is server-authoritative with non-deterministic simulation (float math differs across x86/ARM). Pure input replay would desync cross-platform. State-based recording is the correct approach.

**How Fortnite does it:** Records network replication data (same packets sent over wire). Checkpoints (full state) at regular intervals. Incremental changes between checkpoints. Compressed with Oodle. ~10MB per full BR match. Supports seeking via checkpoint system.

**How fighting games do it:** SF6/Tekken use pure input replay (deterministic). ~50-100KB per match. But requires perfect determinism which AUM doesn't have.

### .aumr Replay File Format

```
HEADER (32 bytes):
  [4] Magic: "AUMR"
  [2] Version: uint16
  [2] Flags: (hasKeyframes, compressed)
  [4] TotalTicks: uint32
  [4] TickRate: 60
  [2] PlayerCount
  [2] MatchType (Solo_1v1, Duo_2v2, etc.)
  [8] Timestamp (Unix ms)
  [4] GameVersion hash

PLAYER TABLE (variable, ~128 bytes per player):
  Per player:
    uniqueCode: uint32
    displayName: string (length-prefixed, max 32 chars)
    fightingStyle: uint8
    fighterClass: uint8 (Male/Female)
    god: uint8 (Brahma/Vishnu/Shiva)
    elementals: uint8[5]
    wearItems: uint16[6]

KEYFRAME TABLE (index for seeking):
  Per keyframe:
    tick: uint32
    fileOffset: uint32

TICK DATA (bulk of file):
  Per tick with changes:
    tick: uint32
    flags: uint8 (has_inputs, has_state_events, has_vfx_events)
    input_block: [player_mask: uint8, per-player: input_bitfield]
    event_block: [event_type: uint8, event_data: variable]

KEYFRAME DATA (full state, every 300 ticks = 5 seconds):
  Per keyframe:
    tick: uint32
    Per player: position(3xfloat), rotation(quat compressed),
                health(float16), stamina(float16), stateId(uint8),
                animHash(uint32), animTime(float16)
```

### File Size Estimates

| Match Type | Duration | Estimated Size |
|-----------|----------|---------------|
| 1v1 (3 min) | 10,800 ticks | ~80-130 KB |
| 1v5 FFA (3 min) | 10,800 ticks | ~300-500 KB |
| With compression | — | 40-60% of raw |

### Replay Playback Architecture

```
REPLAY PLAYBACK
├── ReplayController (loads .aumr, drives simulation from state data)
├── Cinemachine Brain (manages camera priorities)
│   ├── FreeLook Camera (user-controlled orbit)
│   ├── Player Follow Cameras (lock to each fighter)
│   ├── Side View Camera (classic fighting game angle)
│   └── Cinematic Dolly (keyframed camera paths)
├── Timeline Director
│   ├── Speed control (0.25x, 0.5x, 1x, 2x, 4x)
│   ├── Scrub bar (jump to any keyframe)
│   └── Frame stepping (critical for fighting games)
└── Export: Unity Recorder (editor) or native capture (builds)
```

### Auto-Highlight Detection

Event-based scoring from existing server state transitions:

| Event | Score | Source |
|-------|-------|--------|
| KO / Match Win | 100 | GameManager ENDMATCH |
| God Ability Kill (Astra) | 150 | CombatLogHandler |
| Low-Health Comeback (<10% HP win) | 200 | Health check at ENDMATCH |
| Multi-Kill (FFA) | 150 x count | Kill counter |
| Perfect Round (no damage) | 250 | Health unchanged check |
| Tamas Karma Steal (life steal) | 100 | MatchEndManager |

Rolling 8-second window scores events. Top segment auto-saved post-match.

### Video Recording (Native)

| Platform | API | Unity Integration |
|----------|-----|------------------|
| iOS | ReplayKit | Built-in `Apple.ReplayKit` (being deprecated) → use Cross Platform Replay Kit asset ($25) |
| Android | MediaProjection | Same cross-platform asset |
| PC | OS-level (ShadowPlay/Game Bar) | Zero integration needed |

### Replay Versioning

Replays are state-based (not input replay), so balance patches don't break them. Include `gameVersion` hash in header. On format-breaking changes, version field handles backward compatibility in parser. Worst case: "Export to video" before patches land.

### Storage Strategy

- Store locally on device by default
- Upload to PlayFab Entity Files (10MB limit per file — more than enough) or blob storage for sharing
- 500 replays at 200KB avg = 100MB cloud storage = ~$2/month
- Auto-delete after 30 days, players can "pin" to keep permanently

---

## 4. Voice & Text Chat

### Primary: Discord Social SDK

**Why Discord over Vivox:**

| Factor | Discord Social SDK | Vivox |
|--------|-------------------|-------|
| Cost | $0 forever | $0 up to 5K PCU, then $2K/5K bucket |
| Voice quality | Krisp AI (same as Discord app) | AAA-grade |
| Text chat | Included | Included |
| 3D spatial audio | No | Yes |
| Rich Presence | Yes (200M+ Discord users see "Playing AUM") | No |
| Game invites | Yes (join from Discord) | No |
| ToxMod moderation | Yes (free, Jan 2026+) | Premium add-on |
| Player account needed? | No | No |
| Maturity | ~1 year (GDC Mar 2025) | 15+ years, 150+ AAA titles |
| Early adopters | Rust, Splitgate, Tencent | Fortnite, Valorant, LoL |

AUM doesn't need spatial audio (1v1/team fighting game). The Rich Presence + game invites viral loop is worth more than spatial audio.

**Fallback: Vivox** if Discord SDK has stability issues or console support is needed.

### Channel Architecture

```
DISCORD CHANNELS (managed by AUM client):
├── Lobby Voice    (lobby_{lobbyId})     — all lobby members
├── Match Voice    (match_{matchId})     — active fighters
│   └── Team sub   (match_{matchId}_t1)  — for 2v2/3v3
├── Spectator      (match_{matchId}_spec)— spectator commentary
├── Party Voice    (party_{partyId})     — persistent across scenes
└── Global Text    (global_{region})     — social hub
```

### Quick-Chat System (Rocket League Pattern)

Pre-defined phrases, 1-byte enum ID over LiteNetLib. Zero moderation needed.

```
Categories:
  Respect:   "Namaste", "Well Played", "Good Fight", "GG"
  Taunt:     "Is That All?", "Try Harder", "Too Easy"
  Tactical:  "Attack Together", "Fall Back", "Need Help"
  Reactions: "Wow!", "Close One!", "Unlucky", "Nice Combo!"
  Post-Match: "Rematch?", "One More", "Good Game"

Packet: [PacketType.QUICKCHAT][uint8 phraseId]
Input:  D-pad (controller), number row (PC), radial menu (mobile)
```

Auto-translates across languages (each client has localization table). Can unlock custom phrases as cosmetic rewards (monetization potential).

### Profanity Filtering Pipeline

1. **Local word list** (instant, free) — catch obvious slurs
2. **OpenAI Moderation API** (free tier) — AI-based, covers hate/harassment/violence
3. **ToxMod** (via Discord SDK, free) — voice moderation when Discord integrated
4. Escalation: Add Azure Content Moderator ($1/1K calls) at scale

### Existing Lobby Chat (Preserved)

PlayFab CloudScript `SendLobbyChat` → host's `LobbyChatMessages` UserData → polled every 3s via `GetLobbyState`. Works fine for lobby. Discord SDK text channels supplement for real-time + global chat.

---

## 5. Streaming & Social Watching

### "Watch Friend" = Game State Streaming (NOT Video)

This IS the spectator system. Spectator relay streams game state (~2 KB/s). Friend's device has zero overhead (they're just playing normally). Spectator renders locally at full quality.

**This is how Dota 2, League, SF6, PUBG Mobile all do it.** Game state streaming, not video.

```
FRIEND PLAYING MATCH → Game Server → Spectator Relay
                                          │
                        ┌─────────────────┼──────────┐
                        ▼                 ▼          ▼
                    Friend 1          Friend 2    Friend 3
                   (watching)        (watching)  (watching)
```

Bandwidth: 2 KB/s vs 1-5 Mbps for video. 500-1000x more efficient.

### Twitch Integration

[Twitch Game Engine Plugin for Unity](https://dev.twitch.tv/docs/game-engine-plugins/unity-guide/) — free, officially maintained.

Features:
- **Twitch Drops:** Reward viewers with in-game items for watching AUM streams (massive engagement)
- **Enhanced Experiences SDK:** Send game metadata to Twitch (match score, player names)
- **Rich Presence:** Show "Playing AUM" on Twitch profile

Implementation: 2-4 weeks (account linking + webhook handler + item granting)

### Discord Rich Presence (Free Marketing)

Every AUM player's Discord shows:
- "Playing AUM — 1v1 Ranked Match"
- "In Lobby — Waiting for Players"
- "Spectating — SomeName vs OtherName"
- **"Join Match"** button for friends to click

200M+ Discord users potentially see AUM in their friend lists. Zero cost.

### Match Browser

Extend orchestrator with `GET /live-matches`:
```json
{
  "matches": [{
    "matchId": "abc123",
    "matchType": "Solo_1v1",
    "players": [{"name": "Player1", "style": "Amuktha"}, ...],
    "timeElapsed": 45,
    "spectatorCount": 3,
    "serverAddress": "65.109.133.129:7852"
  }]
}
```

Client UI: match list with player names/styles, "Watch" button. Mobile: swipe between matches. PC: grid view.

---

## 6. SDK Comparison Tables

### Voice Chat SDKs

| Factor | Discord Social SDK | Vivox | Agora | Photon Voice 2 | ODIN (4Players) |
|--------|-------------------|-------|-------|----------------|-----------------|
| **10K MAU** | $0 | $0 | ~$5,930/mo | $125-250/mo | $350/mo |
| **100K MAU** | $0 | $2,000/mo | ~$56,000/mo | Enterprise | $3,500/mo |
| **1M MAU** | $0 | $38,000/mo | ~$530,000/mo | Enterprise | $35,000/mo |
| **Billing** | Free | PCU buckets | Per-minute | CCU sub | Per 1K CU |
| **Free Tier** | Unlimited | 5K PCU | 10K min/mo | 20 CCU | None |
| **3D Spatial** | No | Yes | Yes | Manual | Yes |
| **Text Chat** | Yes | Yes | Separate | No | No |
| **Moderation** | ToxMod (free) | Basic free + premium | None | None | None |
| **Self-Hosted** | No | No | No | No | Yes |
| **Unity** | SDK + sample | Native package | SDK | Asset Store | SDK |
| **Latency** | ~40-80ms | ~40-80ms | ~50-100ms | ~50-100ms | ~50-100ms |
| **Platforms** | All + consoles | All + consoles | All + web | All + WebGL | All (no console) |

### Recording/Capture Solutions

| Solution | Platforms | Cost | Use Case |
|----------|----------|------|----------|
| Cross Platform Replay Kit | iOS + Android | $25 one-time | Player-facing recording |
| Unity Recorder | Editor only | Free | Marketing/trailers |
| ReplayKit (native) | iOS only | Free (being deprecated) | Basic iOS recording |
| MediaProjection | Android only | Free | Basic Android recording |
| OS-level (ShadowPlay/Game Bar) | PC | Free | Zero integration |

---

## 7. Implementation Roadmap

### Phase 1: Replay Data Recording (2-3 weeks)
- Server-side state recording in 60Hz tick loop
- .aumr binary format implementation
- Keyframes every 300 ticks (5 seconds)
- Store replay files on server at match end
- **Payoff:** Foundation for everything else — spectating, highlights, content creation

### Phase 2: Spectator System (2-3 weeks)
- `ConnectionType.SPECTATOR` in server handshake
- 20Hz reduced tick rate for spectator connections
- 3-5 second delay buffer
- Match discovery via orchestrator `/live-matches`
- Client `SpectatorMode` with Cinemachine cameras
- "Watch" button in lobby UI + friends list
- **Payoff:** "Watch friend" feature, community engagement

### Phase 3: Discord Social SDK Integration (2-3 weeks)
- Discord SDK Unity package integration
- Voice channels (lobby, match/team, spectator)
- Text chat alongside existing PlayFab lobby chat
- Rich Presence at all game states
- Game invite deep links
- Quick-chat preset system (2-3 days within this phase)
- **Payoff:** Voice comms, viral marketing via Discord, social glue

### Phase 4: Cinematic Tools + Streaming (2-3 weeks)
- Replay playback client with Cinemachine camera rig
- Timeline scrubbing, speed control, frame stepping
- Auto-highlight detection (event scoring)
- Platform-native video recording (Cross Platform Replay Kit)
- Twitch Game Engine Plugin + Drops
- **Payoff:** Content creation pipeline, esports broadcasts, Twitch engagement

### Phase 5: Social Sharing (1 week)
- Export replay clips to MP4 (via native capture of replay playback)
- Platform share sheets (iOS UIActivityViewController, Android Intent)
- Replay gallery (save/browse/share best moments)
- **Payoff:** TikTok/YouTube viral clips, player retention

**Total: ~10-12 weeks across all phases.**

---

## 8. Cost Projections

| Scale | Voice (Discord) | Spectator | Replay Storage | Streaming | Total |
|-------|----------------|-----------|---------------|-----------|-------|
| **Launch** | $0 | $0 (existing server) | ~$20/mo | $0 | **~$20/mo** |
| **10K MAU** | $0 | $0 | ~$20/mo | $0 | **~$20/mo** |
| **100K MAU** | $0 | ~$50/mo (relay) | ~$50/mo | $0 | **~$100/mo** |
| **1M MAU** | $0 | ~$200/mo (relay cluster) | ~$200/mo | $0 | **~$400/mo** |

**If using Vivox fallback instead of Discord:**

| Scale | Voice (Vivox) | Total with Vivox |
|-------|--------------|-----------------|
| 10K MAU | $0 (under 5K PCU) | ~$20/mo |
| 100K MAU | $2,000/mo | ~$2,100/mo |
| 1M MAU | $38,000/mo | ~$38,400/mo |

---

## 9. Sources

### Spectator Systems
- [SourceTV Relay Architecture (Valve Developer Wiki)](https://developer.valvesoftware.com/wiki/SourceTV)
- [SF6 Battle Hub Mode (Capcom)](https://www.streetfighter.com/6/en-us/mode/battlehub.html)
- [Tekken 8 Spectator Server Fix (Siliconera)](https://www.siliconera.com/tekken-8-servers-adjusted-for-spectator-mode/)
- [Riot LoL Determinism & Spectator (Riot Tech)](https://technology.riotgames.com/news/determinism-league-legends-unified-clock)
- [DotaTV Spectating (Liquipedia)](https://liquipedia.net/dota2/Spectating)
- [GGPO Spectator Architecture (GitHub)](https://github.com/pond3r/ggpo)
- [Snapshot Compression (Gaffer On Games)](https://gafferongames.com/post/snapshot_compression/)
- [Snapshot Interpolation (Gaffer On Games)](https://gafferongames.com/post/snapshot_interpolation/)
- [Fighting Game Networking (SuperCombo)](https://supercombo.gg/2021/10/13/archive-understanding-fighting-game-networking-by-mauve/)
- [Diarkis Fighting Game Infrastructure](https://www.diarkis.io/insights/building-real-time-fighting-games-with-diarkis-rollback-lockstep-and-scalable-infrastructure)

### Replay & Recording
- [Fortnite Replay System (Epic)](https://www.fortnite.com/news/fortnite-battle-royale-replay-system)
- [Fortnite Replay Decompressor (GitHub)](https://fortnitereplaydecompressor.readthedocs.io/en/latest/overview/)
- [Developing Your Own Replay System (Game Developer)](https://www.gamedeveloper.com/programming/developing-your-own-replay-system)
- [Implementing Replay in Unity (Game Developer)](https://www.gamedeveloper.com/programming/implementing-a-replay-system-in-unity-and-how-i-d-do-it-differently-next-time)
- [Overwatch Replay Technology (GDC Vault)](https://www.gdcvault.com/play/1024053/Replay-Technology-in-Overwatch-Kill)
- [Floating Point Determinism (Gaffer On Games)](https://gafferongames.com/post/floating_point_determinism/)
- [Slippi Desync Fighting (Project Slippi)](https://medium.com/project-slippi/fighting-desyncs-in-melee-replays-370a830bf88b)
- [Cinemachine + Timeline (Unity Docs)](https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/setup-timeline.html)
- [Cross Platform Replay Kit (Unity Asset Store)](https://assetstore.unity.com/packages/tools/integration/cross-platform-replay-kit-easy-screen-recording-on-ios-android-133662)

### Voice & Text Chat
- [Vivox Unity Integration](https://unity.com/products/vivox)
- [Vivox Pricing FAQ](https://support.unity.com/hc/en-us/articles/31045802890260-Vivox-Pricing-and-Billing-FAQ)
- [Discord Social SDK](https://discord.com/developers/social-sdk)
- [Discord Social SDK Unity Sample (GitHub)](https://github.com/discord/social-sdk-unity-sample)
- [Discord Social SDK Release Notes](https://discord.com/developers/docs/social-sdk/release_notes.html)
- [Discord Social SDK Announcement](https://discord.com/press-releases/announcing-discords-social-sdk-helping-power-your-games-social-experiences)
- [ToxMod + Discord Integration](https://www.modulate.ai/blog/game-on-safely-toxmod-now-powers-voice-moderation-via-discord-social-sdk)
- [Agora Pricing](https://www.agora.io/en/pricing/)
- [ODIN Voice SDK (4Players)](https://odin.4players.io/voice-chat/)
- [VoIP for Gaming 101 (Modulate)](https://www.modulate.ai/blog/voip-for-gaming-101-part-1)
- [Photon Voice 2 (Asset Store)](https://assetstore.unity.com/packages/tools/audio/photon-voice-2-130518)

### Streaming
- [Twitch Unity Plugin Guide](https://dev.twitch.tv/docs/game-engine-plugins/unity-guide/)
- [Twitch Enhanced Experiences SDK](https://dev.twitch.tv/docs/enhanced-experiences/e2-sdk-guide/)
- [Twitch Drops Campaign Guide](https://dev.twitch.tv/docs/drops/campaign-guide)
- [WebRTC Low-Latency Streaming (2026)](https://www.nanocosmos.net/blog/webrtc-latency/)

---

*Research conducted March 29-30, 2026. 6 parallel research agents, 12 web search queries, cross-referenced against AUM's existing LiteNetLib + PlayFab + Unity 6 stack.*
