---
date: 2026-04-23
scope: AUM-Unity-Server-Legacy + PlayFab CloudScript + Python tooling
goal: Handoff document for Option 2 — live telemetry → automated bot preset pipeline
status: planning only, not started
---

# Option 2 Handoff: Live Telemetry + Automated Bot Preset Pipeline

## Why this exists

The user has played ~22 matches to generate 16 human-derived bot presets for 5 styles × 3 gods. The presets work but have one fundamental flaw:

> The user dominated almost every match (8 of 9 in Phase 1 data, similar in Phase 2). Presets encode "expert player crushes weak bot" patterns. The resulting bots will be mirrors of that behavior — aggressive and dominant but calibrated for dumb opponents, not peer humans.

User's decision (quoted): *"for the live telemetry and player tracking and using the players matches online, i think we should only check for player vs player matches and see if there are at least a minimum [number], then we can take only those matches to kind of use to build our bots behaviour etc"*

**Goal:** ingest real human-vs-human PvP matches from production, process them through the existing analyzer pipeline, generate better presets weekly, auto-deploy.

## User's requirements (from 2026-04-23 chat)

1. **Human-vs-human only** — no human-vs-bot matches in training data
2. **Minimum threshold filter** — only ingest matches with N+ humans (probably 2 for 1v1, or 4+ for team modes)
3. **Cost-optimized** — don't blow the PlayFab budget on telemetry
4. **Weekly updates** — automated preset regeneration on a cadence

## Current state (what's already done)

The data-collection side is largely built — Phase 1+2 of the existing pipeline. What needs extending:

### Already exists ✅
- `HumanBehaviorRecorder.cs` — captures structured events (`#if UNITY_EDITOR` only today)
- `[HBR:SNAPSHOT]`, `[HBR:MELEE]`, `[HBR:DODGE]`, etc. — 12+ event types
- `[HBR:MATCH_CONTEXT]` — startTime, matchType, humans/bots count, players list
- `[HBR:SUMMARY]` — match-end aggregate stats
- `tools/aum_gameplay_analyzer.py` — parses HBR logs → Gameplay Profile JSON
- `tools/profile_to_config.py` — Gameplay Profile → HumanDerivedPreset JSON
- `BotBrain.TryLoadPreset` — reads `ServerData/BotPresets/{Style}_{God}_*.json` at bot spawn
- `BotPersonality.FromPresetJson` — applies preset values to BotPersonality + MovementProfile

### Needs to be built 🚧
- Remove `#if UNITY_EDITOR` gate from HBR so it runs in production server builds
- Configurable opt-in/opt-out flag (default OFF, enable per-match or per-player)
- Compact binary serialization (current logs are ~10MB per match — need to shrink)
- PlayFab CloudScript endpoint to ingest event batches
- Storage strategy (TitleData has size limits — need external storage)
- Aggregation job (weekly cron on Helsinki or GitHub Action)
- Preset generation + deployment (git commit or live CDN push)
- Dashboard / health monitoring

## Proposed architecture

```
┌─────────────┐  1. Match plays   ┌──────────────┐
│ Production  │ ────────────────▶│   HBR on     │
│   Server    │                    │   server     │
│  (Helsinki) │                    └──────┬───────┘
└─────────────┘                           │
                                          │  2. Compact binary
                                          │     batch (5-10kb)
                                          ▼
                                 ┌──────────────┐
                                 │  CloudScript │
                                 │    ingest    │
                                 └──────┬───────┘
                                        │  3. Write to external store
                                        ▼
                            ┌───────────────────────┐
                            │  S3 / Cloudflare R2   │
                            │  /matches/YYYY-MM-DD/ │
                            │   {matchId}.bin       │
                            └──────────┬────────────┘
                                       │
                                       │  4. Weekly aggregation
                                       ▼
                              ┌──────────────────┐
                              │   GitHub Action  │
                              │  or Helsinki cron│
                              │                  │
                              │  - fetch week's  │
                              │    matches       │
                              │  - filter PvP    │
                              │  - run analyzer  │
                              │  - run mapper    │
                              │  - commit preset │
                              └──────────┬───────┘
                                         │  5. Deploy
                                         ▼
                                ┌────────────────┐
                                │ ServerData/    │
                                │   BotPresets/  │
                                │ auto-deployed  │
                                └────────────────┘
```

## Design decisions needed (not yet made)

### 1. Event batching / serialization
**Options:**
- (a) JSON lines, gzipped — human-readable, ~30% size reduction vs raw text
- (b) MessagePack binary — 70-80% smaller, harder to inspect
- (c) Custom binary protocol — smallest, custom tools needed

**Recommendation:** MessagePack. Good balance, decent tooling.

**Size budget:** current HBR log = ~10MB per 3-minute match. Target: 100KB batched and compressed (~100× reduction). Drop all SNAPSHOT events (we can derive position from DESYNC-SVR sparse sampling), keep only event-driven data (attacks, dodges, damage, state transitions, summary).

### 2. Storage backend
**Options:**
- (a) PlayFab TitleData — existing, but limited (10MB per key, slow writes)
- (b) Cloudflare R2 — free tier generous, already configured (see `AUM-Unity-Staging-Legacy/CLAUDE.md` R2 account details)
- (c) S3 — standard but costs add up

**Recommendation:** R2. Already configured for the project. Bucket: `aum-telemetry` (new). Cost: near zero for weekly analysis volume.

### 3. Ingestion path
**Options:**
- (a) CloudScript `ingestMatchTelemetry` handler — simple but rate-limited
- (b) Dedicated endpoint on orchestrator (port 8080) — adds load
- (c) Server writes directly to R2 via signed URLs — needs AWS SDK on server

**Recommendation:** CloudScript, batched every match end. Write R2 from CloudScript via HTTP upload with signed URL.

### 4. Filter: what counts as a "PvP match"?
**Criteria:**
- `matchType` is SOLO_1V1, DUO_2V2, DUO_2V4, or TRIO_3V3
- All participants are humans (0 bots)
- Match duration > 30s (discard quitters)
- Both players alive at match start (discard leavers)
- PlayFab MMR delta between players < 500 (filter smurf stomps)

### 5. Opt-in / privacy
Players need to consent to gameplay recording. Options:
- First-launch checkbox (default off) — loses most data
- ToS update — automatic opt-in, requires legal review
- Per-match opt-out — too friction

**Recommendation:** ToS update with a setting to disable. Anonymize all player IDs before storing. Only store mechanic data (positions, actions, timings) — no chat, no names.

### 6. Aggregation cadence
- Daily: too expensive, noisy data
- Weekly: sweet spot (enough data, still fresh)
- Monthly: presets go stale

**Recommendation:** Weekly. Fire at low-traffic time (Monday 4am UTC).

### 7. Preset versioning + A/B testing
When a new preset is auto-generated, should it:
- Replace the old one immediately? (risk: regression)
- Run A/B (50% of bots use old, 50% use new)? (safer, needs dashboard)
- Stage for manual review? (slower, but safest)

**Recommendation:** Auto-replace with a rollback mechanism. Keep previous 4 weeks of presets in git, can `git revert` if a bad preset ships. Track "bot win rate per preset" in CloudScript to alert if a preset shifts badly.

## Implementation phases (suggested)

### Phase 1: Unlock HBR for production builds (2-4 hours)
- Remove `#if UNITY_EDITOR` gate from HBR
- Add opt-in settings flag (default off, CLI-overridable)
- Test with release build: confirm zero overhead when disabled, minimal when enabled
- Compact the SNAPSHOT frequency — every 30 ticks is fine for Editor debug, but for production maybe every 120 ticks (2s intervals)

### Phase 2: Ingestion endpoint (6-8 hours)
- CloudScript `ingestMatchTelemetry(matchData)` — accepts MessagePack batch, validates, writes to R2
- Server-side MessagePack serializer for the HBR event log
- Signed R2 upload URLs
- Rate limiting (don't accept >1 batch per match per player)

### Phase 3: R2 bucket + lifecycle (2 hours)
- Create `aum-telemetry` bucket in R2
- Lifecycle rule: delete raw matches after 90 days (aggregate presets are the long-term artifact)
- Access keys for aggregation job

### Phase 4: Aggregation job (6-10 hours)
- GitHub Action triggered weekly via cron
- Pulls last 7 days of matches from R2
- Filters by PvP criteria (see Decision 4)
- Runs `aum_gameplay_analyzer.py` on aggregated data per style/god combo
- Runs `profile_to_config.py`
- Commits new presets to `legacy-working-oct6` branch
- Triggers deploy (existing Hetzner deploy pipeline)

### Phase 5: Dashboard + monitoring (4-8 hours)
- Simple web page (maybe on brahmanstudios.com) showing:
  - Matches ingested per week
  - Presets updated per style/god
  - Bot win rates per preset (from CloudScript query)
  - Alerts if a new preset shifts win rate > 15%

### Phase 6: Privacy + ToS (coordination w/ legal)
- Add data recording disclosure to ToS
- Add in-app setting "Opt out of gameplay telemetry"
- Anonymization layer in ingestion (hash player IDs before R2)

**Total estimated effort: 2-3 weeks of focused work.**

## Cost estimate (back-of-envelope)

Assuming 1000 matches/day at steady state:
- R2 storage: 1000 × 100KB × 90 days = 9GB in cold storage → ~$0.15/mo
- R2 egress: weekly aggregation pulls 7 × 1000 × 100KB = 700MB/week → negligible
- CloudScript: 1000 invocations/day × 30 days = 30k/mo → within free tier
- GitHub Action: weekly 30-min run → within free tier for public repo, $0.48/mo for private

**Total monthly cost: <$2.** Well within acceptable budget.

## Open questions for user

1. Confirm R2 is acceptable (vs PlayFab TitleData)?
2. Opt-in flow: ToS update vs explicit checkbox — which is acceptable to your team?
3. Is a weekly preset update frequent enough, or do you want daily?
4. MMR filtering threshold — what's "reasonable skill match" in AUM?
5. Do you want per-style/god presets (current) or per-style-only (god-agnostic averaging)?
6. Legal/privacy review needed before starting, or can we start technical work in parallel?

## Files that will be touched

### Server (AUM-Unity-Server-Legacy)
- `Assets/Scripts/Debug/HumanBehaviorRecorder.cs` — remove `#if UNITY_EDITOR`, add production path
- `Assets/Scripts/Managers/GameManager.cs` — add runtime flag
- `Assets/Scripts/Network/TelemetryIngester.cs` — NEW — MessagePack batch builder + CloudScript call
- `Assets/Scripts/Managers/SettingsManager.cs` — opt-out flag plumbing

### Client (AUM-Unity-Staging-Legacy)
- Settings UI — opt-out toggle
- First-launch ToS acknowledgment if needed

### CloudScript
- `ingestMatchTelemetry` handler — validate, sign R2 upload URL, return upload response

### Infrastructure
- R2 bucket + IAM policies
- GitHub Action workflow file
- Aggregation script (extends existing `aum_gameplay_analyzer.py`)

### Python tooling
- `tools/batch_ingest.py` — NEW — fetch from R2, filter, feed analyzer
- `tools/telemetry_dashboard.py` — NEW (optional Phase 5)

## Prerequisites to validate before starting

- [ ] Confirm R2 still accessible (check credentials in AUM-Unity-Staging-Legacy CLAUDE.md)
- [ ] Confirm PlayFab CloudScript rev number + available free handler slots (current rev ~149 per CLAUDE.md)
- [ ] Verify GitHub Action runs as expected on server repo
- [ ] Draft ToS language for data recording disclosure (legal review)
- [ ] Confirm current HBR log volume per match (baseline for size optimization)

## Why Option 2 and not Option 1

Option 1 (iterate on solo-vs-bot presets) was completed today. 16 presets shipped. The data quality ceiling is the problem — you can't learn "expert play against peer humans" from "winning against weak bots". Option 2 breaks that ceiling by aggregating thousands of real PvP matches.

## Success criteria

- [ ] Preset regeneration runs automatically weekly without manual intervention
- [ ] Bot win rate across all preset styles stays within 40-55% (not too easy, not too hard)
- [ ] Presets derived from live data produce "feel" comments from testers: "bots play like real humans"
- [ ] Storage cost < $5/mo
- [ ] Zero production performance regression (HBR overhead < 0.5ms per tick)
- [ ] ToS compliant, opt-out functional

## Ready to start when

User green-lights Phase 1 in a future session. Carry this doc forward.
