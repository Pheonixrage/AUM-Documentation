---
pipeline: P1
type: roadmap
version: 2.0
date: 2026-03-24
tags: [roadmap, launch, v2]
---

# AUM Unified Roadmap — August 2026 Launch

**Created:** March 24, 2026
**Timeline:** ~16 weeks (Mar 24 → mid-August 2026)
**Scale:** 1,000-5,000 CCU
**Platforms:** iOS + Android + Windows

## Reconciled From

- GSD `.planning/ROADMAP.md` (10 phases of V2 architecture — ALL COMPLETE)
- `LAUNCH_ROADMAP_JUNE2026.md` (8-phase vision plan)
- Archived: `archive/LAUNCH_ROADMAP_JUNE2026_v1.md`

## Key Discovery (Mar 24, 2026)

The `v2` branch already has **229 C# files across 17 modules** with 10 completed GSD phases:
- Avatar System (body/weapon separation, 5 weapon behaviors)
- Blessing System (24 abilities, BlessingManager)
- Elemental System (30 behaviors, GunaState, karma)
- Economy (stores, chests, missions, loka progression)
- Bot AI (4x4 difficulty/personality matrix, ELO)
- Mobile UX (performance, touch controls, combat HUD)
- Combat Polish (hit-feel, damage numbers, frame data)
- Build Pipeline (GameCI, K8s configs, monitoring)
- Social UI (64 Nakama stubs wired)
- Localization (5 languages, 238 entries)

**The path to launch is INTEGRATION and TESTING, not building from scratch.**

---

## Phase Overview

```
Mar 24 ── Apr 7 ── Apr 21 ── May 5 ── May 19 ── Jun 2 ── Jun 16 ── Jul 7 ── Aug 4
  │         │         │         │         │         │         │         │        │
  ▼         ▼         ▼         ▼         ▼         ▼         ▼         ▼        ▼
Phase 1   Phase 2   Phase 3   Phase 4   Phase 5   Phase 6   Phase 7   Phase 8  LAUNCH
V2        Nakama    Multi-    Combat    Social    Mobile    Build     QA &
Integr.   Deploy    player    Polish    Wiring    Platform  Pipeline  Launch
& Test    & Wire    Testing   & Tune    (Nakama)  Builds    CI/CD     Submit
```

---

## Phase 1: V2 Integration & Testing (2 weeks, Mar 25 - Apr 7)

**Goal:** Verify all V2 systems compile, wire to V1, and work end-to-end in Editor

### Tasks
- [ ] Verify v2 branch compiles clean in Unity 2022.3
- [ ] Test V1-V2 Bridge (V1AuthorityAdapter, BridgeBootstrap)
- [ ] Verify Avatar System: body/weapon separation works in-game
- [ ] Verify Blessing System: abilities fire correctly
- [ ] Verify Economy: stores, chests, missions functional
- [ ] Test all 5 weapon behaviors (Sword, Axe, Staff, Bow, Chakra)
- [ ] Run full tutorial flow with V2 systems active
- [ ] Fix any compilation errors or runtime crashes

### Success Criteria
1. V2 branch compiles with zero errors
2. Player can select body + weapon independently
3. All 5 weapon behaviors produce correct damage values
4. Tutorial completes without crashes

---

## Phase 2: Nakama Deployment & Wiring (2 weeks, Apr 7 - Apr 21)

**Goal:** Deploy Nakama to Singapore, wire 64 social stubs + economy RPCs

### Tasks
- [ ] Deploy Nakama + PostgreSQL on Singapore (Docker Compose)
- [ ] Wire 17 Nakama services (already coded in V2)
- [ ] Connect 64 social UI stubs to live Nakama APIs
- [ ] Migrate auth flow (Google OAuth → Nakama)
- [ ] Test currency/inventory CRUD operations
- [ ] Verify matchmaking queue on Nakama
- [ ] Load test with simulated connections

### Success Criteria
1. Nakama running on Singapore with PostgreSQL
2. Player can authenticate, see inventory, buy from store
3. Matchmaking finds opponent within 60 seconds
4. All 17 services respond correctly

---

## Phase 3: Multiplayer Testing (2 weeks, Apr 21 - May 5)

**Goal:** Two players complete a full match online with V2 combat

### Tasks
- [ ] Deploy headless server with V2 combat to Helsinki
- [ ] Connect two clients to server, complete 1v1 match
- [ ] Verify weapon behaviors work in multiplayer (server validates)
- [ ] Test elemental spells, shields, specials, astra online
- [ ] Verify hit-feel system (damage numbers, hit-stop) in multiplayer
- [ ] Test disconnect handling (remaining player wins)
- [ ] Verify state agreement (no persistent mismatches)
- [ ] Test bot fallback when no opponent found

### Success Criteria
1. Two players complete 1v1 without gameplay-breaking desync
2. All 5 weapon types work correctly in multiplayer
3. Disconnect → remaining player wins by default
4. Client-server state agreement throughout match

---

## Phase 4: Combat Polish & Tuning (2 weeks, May 5 - May 19)

**Goal:** Combat feels AAA — responsive, impactful, balanced

### Tasks
- [ ] Tune hit-feel system (HitStopController, HitFeelManager configs)
- [ ] Calibrate damage numbers (14 types, pooled display)
- [ ] Configure combat camera profiles (4 profiles exist)
- [ ] Test haptic feedback on mobile
- [ ] Tune frame data (cancel windows, startup/active/recovery)
- [ ] Balance weapon damage values across all 5 styles
- [ ] Test adaptive netcode (dynamic buffer + reconciliation)
- [ ] Apply remote balance overrides via Nakama

### Success Criteria
1. Hits feel impactful (visual + audio + haptic feedback)
2. No input delay >100ms perceived
3. All 5 weapons feel distinct but balanced
4. Smooth gameplay on 100ms+ latency connections

---

## Phase 5: Social Systems Wiring (2 weeks, May 19 - Jun 2)

**Goal:** Friends, party, lobby, chat all functional on Nakama

### Tasks
- [ ] Wire friends system (request, accept, search by code)
- [ ] Wire party system (create, invite, ready up, queue together)
- [ ] Wire lobby system (create, browse, join, spectate)
- [ ] Wire chat (match, party, global channels)
- [ ] Test ranked ELO system end-to-end
- [ ] Verify leaderboards display correctly
- [ ] Test player profiles and match history

### Success Criteria
1. Send friend request → accept → appears in friends list
2. Create party → invite friend → both queue → matched together
3. Leaderboard shows global rankings with player position
4. Chat messages delivered in <1 second

---

## Phase 6: Mobile Platform & Builds (2 weeks, Jun 2 - Jun 16)

**Goal:** 60fps on mobile, platform builds ready for store testing

### Tasks
- [ ] Profile on target iOS and Android devices
- [ ] Apply DeviceDetector + QualityController optimizations
- [ ] Test FloatingJoystick + AbilityButtonHandler touch controls
- [ ] Verify PlatformInputRouter switches correctly
- [ ] Build iOS → TestFlight internal testing
- [ ] Build Android → Play Store internal testing
- [ ] Build Windows → Steam dev build
- [ ] Test SteamManager + SteamAchievements integration

### Success Criteria
1. 60fps on iPhone 12+ and equivalent Android
2. Touch controls responsive and intuitive
3. TestFlight build installs and plays correctly
4. Play Store internal testing build works

---

## Phase 7: Build Pipeline & CI/CD (1 week, Jun 16 - Jun 23)

**Goal:** Automated builds and deployment — no manual SSH

### Tasks
- [ ] Activate GameCI GitHub Actions (V2 configs exist)
- [ ] Configure automated client builds (iOS, Android, Windows)
- [ ] Configure automated headless server build
- [ ] Set up automated Hetzner deployment on push
- [ ] Verify Prometheus/Grafana monitoring dashboards
- [ ] Configure Sentry + Crashlytics error reporting
- [ ] Test CDN Addressables delivery (R2 + fallback)

### Success Criteria
1. Push to main → automated build → success/failure notification
2. Server deployment without manual SSH
3. Error dashboard shows real-time issues
4. CDN delivers assets correctly

---

## Phase 8: QA & Launch (3 weeks, Jun 23 - Aug 4)

**Goal:** Cross-platform testing, store submission, soft launch

### Week 1: QA
- [ ] Run 40 automated cross-platform checks (V2 QA exists)
- [ ] Execute 44-test matrix across platforms
- [ ] Run k6 load test (1K CCU target)
- [ ] Verify veteran migration RPC
- [ ] Test colorblind accessibility (3 filters exist)
- [ ] Verify 5-language localization (238 entries)

### Week 2: Store Submission
- [ ] App Store submission (privacy policy, screenshots, descriptions)
- [ ] Google Play submission
- [ ] Steam store page setup
- [ ] Security audit (network policies exist)

### Week 3: Soft Launch
- [ ] Limited release (TestFlight + Play Store beta)
- [ ] Monitor error rates, crash-free rate
- [ ] Collect player feedback
- [ ] Hot-fix cycle
- [ ] Public launch decision

### Success Criteria
1. <1% crash rate across platforms
2. 1K CCU sustained without degradation
3. Store approval received
4. Positive beta feedback

---

## Progress Tracker

| Phase | Name | Duration | Target | Status |
|-------|------|----------|--------|--------|
| (V2 Build) | 10 GSD phases of architecture | - | Done | COMPLETE |
| 1 | V2 Integration & Testing | 2 weeks | Apr 7 | NEXT |
| 2 | Nakama Deploy & Wiring | 2 weeks | Apr 21 | Pending |
| 3 | Multiplayer Testing | 2 weeks | May 5 | Pending |
| 4 | Combat Polish & Tuning | 2 weeks | May 19 | Pending |
| 5 | Social Systems Wiring | 2 weeks | Jun 2 | Pending |
| 6 | Mobile Platform Builds | 2 weeks | Jun 16 | Pending |
| 7 | Build Pipeline & CI/CD | 1 week | Jun 23 | Pending |
| 8 | QA & Launch | 3+ weeks | Aug 4 | Pending |

**Total: ~16 weeks → Soft Launch July, Public August 2026**

---

*Roadmap created: March 24, 2026*
*Replaces: LAUNCH_ROADMAP_JUNE2026.md (archived)*
