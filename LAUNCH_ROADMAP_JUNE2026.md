# AUM Launch Roadmap — June 2026

**Created:** February 22, 2026
**Timeline:** 17 weeks (Feb 22 → June 21, 2026)
**Scope:** Full Global Launch — iOS + Android + Windows
**Scale:** 1,000–5,000 CCU

---

## TIMELINE OVERVIEW

```
Feb 22 ─── Mar 8 ─── Mar 22 ─── Apr 5 ─── Apr 19 ─── May 3 ─── May 17 ─── Jun 7 ─── Jun 21
  │          │          │          │          │          │          │          │          │
  ▼          ▼          ▼          ▼          ▼          ▼          ▼          ▼          ▼
Phase 1    Phase 2    Phase 3    Phase 4    Phase 5    Phase 6    Phase 7    Phase 8    LAUNCH
Legacy     Bot AI     Social     Combat     Mobile     Mythology  Build      QA &       Go
Sync &     World-     Systems    Polish &   UX &       Content    Pipeline   Scale      Live
Foundation Class      Nakama     Netcode    Platform   & Balance  & CI/CD    Testing
```

---

## PHASE 1: LEGACY SYNC & FOUNDATION (Feb 22 – Mar 8)
**Duration:** 2 weeks
**Goal:** Port all production features, establish clean foundation

### 1A: Legacy Feature Audit & Port (Week 1)
| Task | Source | Target | Approach |
|------|--------|--------|----------|
| Party System logic | PlayFabPartyService (41KB) | NakamaPartyService | Rebuild on Nakama Groups API |
| Friends System logic | PlayFabSocialService (40KB) | NakamaFriendsService | Rebuild on Nakama Friends API |
| Profile System | Production ProfileScreen | NakamaPlayerData | Add public profile RPC |
| Match History | Production PlayFabStatsUpdater | New NakamaMatchHistory | New Go RPC + Unity service |
| PC Keyboard Controls | Production PCInput.cs | Already ported (InputManager) | Verify completeness |
| AcceptMatch Popup | Production scene-based | Already ported (MatchFoundPopup) | Verify working |
| iOS Build Pipeline | Production BuildScript.cs | Editor/BuildScript.cs | Port split-build logic |

### 1B: Nakama Backend Expansion (Week 2)
| RPC | Purpose | Go Handler |
|-----|---------|------------|
| `rpc_match_history_record` | Save match results with replay data | `match_history.go` |
| `rpc_match_history_query` | Retrieve match history with filters | `match_history.go` |
| `rpc_profile_public` | Public player card (stats, avatar, rank) | `profile.go` |
| `rpc_daily_login` | Login streak tracking + rewards | `daily_rewards.go` |

### 1C: Modular Architecture Foundation
| Task | Description | Files |
|------|-------------|-------|
| Create ASMDEF structure | Split 400+ files into ~10 modules | 10+ `.asmdef` files |
| IGameMode interface | Base interface for all game modes | `GameModes/Core/IGameMode.cs` |
| GameModeDefinition SO | Data-driven mode configuration | `GameModes/Core/GameModeDefinition.cs` |
| GameModeRegistry | Auto-discovers modes via assembly scanning | `GameModes/Core/GameModeRegistry.cs` |
| Extract Arena mode | Current PvP as first game mode plugin | `GameModes/Arena/` |
| Extract Tutorial mode | Current tutorial as game mode plugin | `GameModes/Tutorial/` |
| Extract Training mode | Current training as game mode plugin | `GameModes/Training/` |
| Balance ScriptableObjects | Externalize combat values from hardcoded consts | `Assets/Data/Balance/` |

### 1D: Foundation Cleanup
- [ ] Remove all PlayFab imports from remaining files
- [ ] Delete PlayFab SDK folder (Phase 8E)
- [ ] Verify all 17 Nakama services connect and function
- [ ] Run full integration test on Singapore server

### Deliverables
- All production features available in upgraded project
- Nakama services verified end-to-end
- Clean codebase with zero PlayFab dependency
- Modular ASMDEF structure with 3 extracted game modes
- Singapore dev server fully operational

---

## PHASE 2: BOT AI — WORLD-CLASS REBUILD (Mar 8 – Mar 22)
**Duration:** 2 weeks
**Goal:** Bots indistinguishable from human players at network level

### 2A: Bot Intelligence Framework (Week 1)
| Module | Purpose | Files |
|--------|---------|-------|
| `BotBrain.cs` | Central decision engine | Enhance existing |
| `ThreatAssessment.cs` | Evaluate incoming danger | Enhance existing |
| `OpportunityDetector.cs` | Find attack windows | Enhance existing |
| `ResourceTracker.cs` | Predict resource availability | Enhance existing |
| `ElementalIntelligence.cs` | Spell selection + cycle awareness | Enhance existing |
| `PositioningAI.cs` | **NEW** — Zone control, spacing, retreats | Create |
| `ComboEngine.cs` | **NEW** — Multi-hit chain planning | Create |
| `AdaptiveAI.cs` | **NEW** — Learn opponent patterns mid-match | Create |

### 2B: Bot Behavior Implementation (Week 2)
| Behavior | Easy | Medium | Hard | Extreme |
|----------|------|--------|------|---------|
| Melee combos | 1-2 hits | 3-hit chains | Full combos + mix-ups | Frame-perfect |
| Dodging | Random | On hit-react | Animation read | I-frame perfect |
| Spells | Random element | Counter-element | Cycle combos | Optimal DPS |
| Shield | Never | Low HP only | Read enemy cast | Perfect timing |
| Focus use | Spam at 1 bar | Save for 2 bars | Strategic 3-bar | Optimal |
| Positioning | Stationary | Range maintain | Zone control | Perfect spacing |
| Third Eye | Never | Random | On burst incoming | Frame-perfect dodge |
| Astra | At 4 bars always | When enemy low | Combo finisher | Max damage setup |

### 2C: Personality System
```
PersonalityConfig:
  - Aggressive: Rush-down, constant pressure, risk-taker
  - Defensive: Counter-attacker, patience, punish mistakes
  - Balanced: Adaptive, reads opponent, switches styles
  - Chaotic: Unpredictable, random style switches, confusing
```

### 2D: Bot Testing & Tuning
- [ ] Bot vs Bot matches (all difficulty combinations)
- [ ] Bot vs Human (feel test — does it feel like fighting a person?)
- [ ] Network validation — bot inputs through same authority pipeline
- [ ] Performance test — 50 bot matches on single server

### Deliverables
- 4 difficulty levels with distinct feel
- 4 personality types
- Bots use same network pipeline as players
- All 5 fighting styles + 3 god selections covered

---

## PHASE 3: SOCIAL SYSTEMS ON NAKAMA (Mar 22 – Apr 5)
**Duration:** 2 weeks
**Goal:** Full social experience — party, friends, chat, presence

### 3A: Party System (Nakama Groups) (Week 1)
| Feature | Implementation | RPC/API |
|---------|---------------|---------|
| Create Party | `NakamaPartyService.CreateParty()` | Nakama Groups API |
| Invite Friend | `NakamaPartyService.InviteToParty()` | Nakama Notifications |
| Join/Leave | `NakamaPartyService.JoinParty()` | Nakama Groups API |
| Party Chat | `NakamaChatManager.JoinPartyChannel()` | Nakama Chat API |
| Ready State | Custom group metadata | Nakama Group Metadata |
| Party Matchmaking | `NakamaMatchmaker.FindMatch(partyProps)` | Matchmaker Properties |
| Elemental Sync | Party members see each other's loadout | WebSocket presence data |
| Host Controls | Leader can kick, set preferences | Group admin API |

### 3B: Friends System (Week 1-2)
| Feature | Implementation | RPC/API |
|---------|---------------|---------|
| Send Request | `NakamaFriendsService.SendRequest()` | Nakama Friends API |
| Accept/Decline | `NakamaFriendsService.AcceptRequest()` | Nakama Friends API |
| Friend Code | `NakamaFriendsService.SearchByCode()` | `rpc_search_friend_code` |
| Friend List | `NakamaFriendsService.GetFriends()` | Nakama Friends API |
| Online Status | `NakamaSocialManager.TrackPresence()` | Nakama Presence |
| Friend Stats | `NakamaFriendsService.GetFriendStats()` | `rpc_friend_enrichment` |
| Direct Message | `NakamaChatManager.OpenDM()` | Nakama Chat API |
| Block Player | `NakamaFriendsService.BlockPlayer()` | Nakama Friends API |

### 3C: Profile System (Week 2)
| Feature | Implementation |
|---------|---------------|
| Public Profile Card | Avatar preview, stats, rank, god preference |
| Name System | Unique names via `rpc_name_registry` |
| Avatar Showcase | Selected avatar with equipped cosmetics |
| Career Stats | Win rate, total matches, favorite style |
| Match History | Last 20 matches with results |

### 3D: Social UI Verification
- [ ] All friend screens (Add, List, Stats, Request)
- [ ] Party screens (Create, Invite, Ready, Leave)
- [ ] Chat UI (Party channel, DM)
- [ ] Profile screen (View own, view friend's)

### Deliverables
- Full party flow: create → invite → ready → match
- Full friend flow: request → accept → chat → view profile
- Real-time presence (online, in-match, idle)
- All social UI screens functional

---

## PHASE 4: COMBAT POLISH & NETCODE TUNING (Apr 5 – Apr 19)
**Duration:** 2 weeks
**Goal:** Frame-perfect feel, zero perceived input lag, esports-ready

### 4A: Hit Feel & Impact (Week 1)
| Improvement | Current | Target |
|-------------|---------|--------|
| Hit-stop | None | 3-frame freeze on heavy hits |
| Screen shake | Basic | Layered: light/medium/heavy |
| Hit VFX | Placeholder | Elemental-specific impact particles |
| Hit SFX | Basic | Layer: impact + element + damage-level |
| Damage numbers | Static | Animated pop with crit/element colors |
| Haptic (mobile) | None | Per-hit vibration patterns |

### 4B: Netcode Tuning (Week 1-2)
| System | Current | Target |
|--------|---------|--------|
| Input buffer | Fixed size | Adaptive (latency-aware) |
| Reconciliation speed | 150-250ms | Tunable per connection quality |
| Prediction confidence | Simple compare | Weighted by recent accuracy |
| Position smoothing | Linear lerp | Cubic interpolation |
| Mismatch handling | Snap + log | Graceful blend with analytics |

### 4C: State Machine Polish (Week 2)
| Improvement | Description |
|-------------|-------------|
| Cancel windows | Define which states can cancel into what |
| Buffer inputs | Queue next action during current animation |
| Priority system | When two states conflict, clear winner |
| Recovery frames | Balance advantage on hit/block/whiff |

### 4D: Combat Balance
| Check | Method |
|-------|--------|
| Damage values | Spreadsheet simulation, all matchups |
| Elemental cycle | Every element vs every element tested |
| God balance | Win rates per god across all styles |
| Stamina economy | Dodge spam prevention verified |
| Focus economy | Hit-streak rewards feel meaningful |

### Deliverables
- Every hit feels impactful (visual + audio + haptic)
- < 100ms perceived input latency on 4G connections
- All 25 style × god matchups balanced within 55/45
- Cancel/buffer system for responsive controls

---

## PHASE 5: MOBILE UX & PLATFORM OPTIMIZATION (Apr 19 – May 3)
**Duration:** 2 weeks
**Goal:** Brawl Stars-level mobile UX, smooth multi-platform experience

### 5A: Mobile Performance (Week 1)
| Target | Metric | Action |
|--------|--------|--------|
| 60 FPS | iPhone 12+, SD 865+ | Profile → optimize hot paths |
| < 1 GB RAM | All mobile | Asset streaming, texture compression |
| < 500 MB download | All mobile | Addressable assets, on-demand download |
| < 5s load | Cold start | Preload optimization, splash screen |
| 3hr battery | Continuous play | GPU/CPU throttling, thermal management |

### 5B: Touch Controls Polish (Week 1)
| Control | Improvement |
|---------|-------------|
| Virtual joystick | Dead zone tuning, thumb tracking |
| Action buttons | Size/placement optimization per device |
| Swipe dodge | Direction detection accuracy |
| Spell selection | One-tap element wheel |
| Target lock | Auto-aim assist for mobile |

### 5C: Platform-Specific (Week 2)
| Platform | Work |
|----------|------|
| iOS | App Store compliance (Sign in with Apple, privacy policy) |
| Android | Keystore resolution, Play Store listing |
| Windows | Keyboard/mouse bindings, ultrawide support, Steam SDK |

### 5D: UI/UX Polish
| Screen | Improvement |
|--------|-------------|
| Main Menu | 3-tap flow to any feature |
| Character Select | Preview animations, stat comparison |
| Matchmaking | Clear queue status, cancel button |
| Post-Match | Stats summary, progression reward animation |
| Settings | Per-platform control remapping |

### Deliverables
- 60 FPS on target mobile devices
- Touch controls feel natural and responsive
- All three platforms buildable and deployable
- UI passes usability test (5 new users complete onboarding)

---

## PHASE 6: MYTHOLOGY CONTENT & BALANCE (May 3 – May 17)
**Duration:** 2 weeks
**Goal:** Karma/Guna/Trinity become the game's soul, not just mechanics

### 6A: Karma System Deep Integration (Week 1)
| Feature | Implementation |
|---------|---------------|
| Karma-based matchmaking | Sattvic/Rajasic/Tamasic pools |
| Karma display | Visual indicator on player card |
| Karma rewards | Bonus currency for high karma |
| Karma penalties | Queue delays for low karma |
| Anti-rage-quit | Karma loss for disconnect |

### 6B: Guna Progression System (Week 1)
| Feature | Implementation |
|---------|---------------|
| Guna balance display | Triangle meter (Sattva/Rajas/Tamas) |
| Guna-affected abilities | Scaling bonuses based on dominant guna |
| Guna shift feedback | Post-match guna change notification |
| Guna-themed cosmetics | Unlock cosmetics aligned with dominant guna |

### 6C: Content Pipeline (Week 2)
| Content | Count | Status |
|---------|-------|--------|
| Fighting styles | 5 | Done (Amuktha, MantraMuktha, MukthaMuktha, PaniMuktha, Yantramuktha) |
| Trinity Gods | 3 | Done (Brahma, Vishnu, Shiva) |
| Elements | 5 | Done (Fire, Water, Earth, Air, Ether) |
| Maps | 2+ | Bhuloka (main), need 1-2 more |
| Match modes | 9 | Need verification of all modes |
| Cosmetics | TBD | Per-character cosmetic sets |

### 6D: Ranked System
| Feature | Implementation |
|---------|---------------|
| ELO rating | Nakama leaderboard + custom RPC |
| Rank tiers | Bronze → Silver → Gold → Diamond → Legend |
| Season system | Monthly seasons with rank rewards |
| Placement matches | 10 matches to calibrate initial rank |
| Rank display | Badge on player card and match loading |

### Deliverables
- Karma affects every social interaction
- Guna visible and meaningful in gameplay
- Ranked system with seasonal progression
- At least 2 competitive maps

---

## PHASE 7: BUILD PIPELINE, CI/CD & INFRASTRUCTURE (May 17 – Jun 7)
**Duration:** 3 weeks
**Goal:** One-click builds, automated testing, monitoring, live ops infrastructure

### 7A: Build Automation (Week 1)
| Platform | Build System | Distribution |
|----------|-------------|-------------|
| iOS | Unity batch → Xcode → Archive | TestFlight → App Store |
| Android | Unity batch → Gradle → APK/AAB | Play Store |
| Windows | Unity batch → exe | Steam / Direct |
| Server | Unity headless → Linux binary | Hetzner VPS |

### 7B: CI/CD Pipeline — GameCI + GitHub Actions (Week 1-2)
```yaml
# .github/workflows/build-client.yml
On push to AUM_BODY:
  1. GameCI Unity build (all platforms)
  2. Run unit tests (Unity Test Framework)
  3. Upload build artifacts to GitHub Releases
  4. Notify Discord channel

# .github/workflows/build-server.yml
On push to AUM_MIND:
  1. Build headless server (Linux x64)
  2. Deploy to Singapore staging via SSH
  3. Tail logs 30s, verify clean startup
  4. Notify Discord channel

# .github/workflows/deploy-production.yml
On merge to main:
  1. Full build matrix (iOS, Android, Windows)
  2. Security scan
  3. Deploy to production (manual approval gate)
```

### 7C: Analytics & Monitoring Stack (Week 2)
| Tool | Purpose | Deployment |
|------|---------|------------|
| **Metabase** | BI dashboards (win rates, retention, economy) | Docker on Singapore VPS |
| **Prometheus** | Metrics collection (server health, CCU, match duration) | Docker on Singapore VPS |
| **Grafana** | Real-time dashboards, alerting | Docker on Singapore VPS |

New Nakama RPC: `rpc_analytics_event` — Records match events for Metabase queries.

### 7D: Server Infrastructure (Week 2-3)
| Component | Dev (Singapore) | Production (Multi-Region) |
|-----------|-----------------|---------------------------|
| Nakama | 1 instance | 2 instances (SG + EU) |
| Game Servers | 4 instances | 10+ per region |
| PostgreSQL | 1 instance | Primary + read replica |
| Orchestrator | 1 instance | Per-region |
| Monitoring | MCP + logs | Grafana + Prometheus + alerts |
| Analytics | Metabase | Metabase + custom dashboards |

### 7E: Data Migration (Week 3)
| Task | Approach |
|------|----------|
| Existing players | `rpc_data_migration` — PlayFab → Nakama one-time |
| Avatar data | JSON export → Nakama storage import |
| Currency balances | Verify → atomic transfer |
| Friend relationships | Map PlayFab IDs → Nakama user IDs |

### 7F: Localization & Accessibility Infrastructure (Week 3)
| System | Implementation |
|--------|---------------|
| Unity Localization | Package install + string table directory |
| AUMLocalizationManager | Runtime language switching |
| AccessibilityManager | Settings hub (colorblind, text size, input remapping) |
| Remote config integration | Language/accessibility settings via Nakama |

### Deliverables
- All platforms build from single command via GameCI
- CI/CD pipeline with staging → production flow
- Metabase + Grafana monitoring live
- Multi-region server infrastructure ready
- Data migration path for existing players
- Localization and accessibility infrastructure scaffolded

---

## PHASE 8: QA & SCALE TESTING (Jun 7 – Jun 21)
**Duration:** 2 weeks
**Goal:** Production-ready, battle-tested, launch-confident

### 8A: Load Testing (Week 1)
| Test | Target | Method |
|------|--------|--------|
| 100 CCU | Baseline | Bot clients on Singapore |
| 500 CCU | Regional | Multi-instance bot swarm |
| 1,000 CCU | Launch day | Full infrastructure test |
| 5,000 CCU | Peak scenario | Stress test with auto-scaling |

### 8B: Cross-Platform QA (Week 1)
| Platform | Device | Test Matrix |
|----------|--------|-------------|
| iOS | iPhone 12, 14, 15 Pro | Full gameplay + social |
| Android | Pixel 7, Samsung S23, budget devices | Full gameplay + social |
| Windows | Laptop + Desktop | Full gameplay + social |
| Cross-play | iOS vs Android vs Win | Matchmaking + gameplay |

### 8C: Security Audit (Week 2)
| Check | Method |
|-------|--------|
| Client hack prevention | Verify all damage server-validated |
| Packet manipulation | Fuzz test network packets |
| Economy exploits | Verify currency operations atomic |
| Auth security | Token refresh, session hijack prevention |
| DDOS resilience | Rate limiting, connection throttling |

### 8D: Launch Checklist (Week 2)
- [ ] App Store approved (iOS)
- [ ] Play Store approved (Android)
- [ ] Steam page live (Windows)
- [ ] Production servers provisioned (multi-region)
- [ ] Monitoring & alerting configured
- [ ] Rollback plan documented
- [ ] Customer support pipeline ready
- [ ] Marketing assets prepared
- [ ] Analytics dashboards live
- [ ] Community Discord ready

### Deliverables
- 5K CCU load test passed
- Cross-platform verified on target devices
- Security audit passed
- All stores approved and ready

---

## MILESTONE CHECKPOINTS

| Date | Milestone | Success Criteria |
|------|-----------|-----------------|
| **Mar 8** | Foundation Complete | All legacy features ported, Nakama clean |
| **Mar 22** | Bot AI Complete | 4 difficulties, indistinguishable from human |
| **Apr 5** | Social Complete | Party + Friends + Chat + Profile working |
| **Apr 19** | Combat Polished | Frame-perfect feel, balanced matchups |
| **May 3** | Mobile Ready | 60 FPS on target devices, touch controls polished |
| **May 17** | Content Complete | Ranked system, maps, all modes verified |
| **Jun 7** | Pipeline Ready | CI/CD, multi-region, data migration done |
| **Jun 21** | LAUNCH | All stores approved, 5K CCU tested, go live |

---

## RISK REGISTER

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Android keystore unresolved | Can't launch Android | Escalate to Google Play support, prepare key reset |
| Nakama scale limits | Can't hit 5K CCU | Load test early (Phase 1), plan horizontal scaling |
| Bot AI takes longer | Delayed Phase 2 | Start with 2 difficulties, add 2 more later |
| App Store rejection | Delayed iOS launch | Submit early, address feedback quickly |
| Combat balance issues | Poor player retention | Continuous balance patches, community feedback |
| Cross-platform desync | Different gameplay per platform | Use fixed timestep, test all platforms together |

---

## RESOURCE ALLOCATION

### Development Focus per Phase
```
Phase 1 ████████ Foundation     (BODY 60%, MIND 20%, SPIRIT 10%, NAKAMA 10%)
Phase 2 ████████ Bot AI         (MIND 70%, BODY 10%, SPIRIT 10%, NAKAMA 10%)
Phase 3 ████████ Social         (BODY 40%, NAKAMA 40%, SPIRIT 10%, MIND 10%)
Phase 4 ████████ Combat Polish  (BODY 50%, MIND 30%, SPIRIT 10%, NAKAMA 10%)
Phase 5 ████████ Mobile UX      (BODY 70%, MIND 10%, SPIRIT 10%, NAKAMA 10%)
Phase 6 ████████ Mythology      (BODY 30%, MIND 20%, NAKAMA 30%, SPIRIT 20%)
Phase 7 ████████ Pipeline       (MIND 30%, NAKAMA 30%, BODY 20%, SPIRIT 20%)
Phase 8 ████████ QA & Scale     (ALL 25% each)
```

---

## NIGHTLY SESSION PLAN (Feb 22)

### Tonight's Priority
Since we're reviewing the blueprint + roadmap first, the execution order after approval:

1. **Set up GSD** for Phase 1 with this roadmap
2. **Start Phase 1A** — Party system Nakama rebuild
3. **Start Phase 1B** — Match history + Profile Go RPCs
4. **Use /autodev** for implementation + testing
5. **Document learnings** to Spirit after each feature

---

*This roadmap is a living document. Updated at each milestone checkpoint.*
*Stored in Spirit (AUM-Documentation) as the canonical plan.*
