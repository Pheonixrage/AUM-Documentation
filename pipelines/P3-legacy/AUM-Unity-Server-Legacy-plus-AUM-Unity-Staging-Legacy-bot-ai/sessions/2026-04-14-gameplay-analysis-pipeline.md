---
date: 2026-04-14
scope: AUM-Unity-Server-Legacy
goal: Build gameplay analysis → bot behavior pipeline
status: in_progress — Phase 1-5 code complete, needs playtest + commit
pinned_commit: NOT YET COMMITTED — 8 modified + 3 new files, working tree dirty on top of fa64b74
next_action: Playtest to verify phase-driven movement, then commit all phases as WIP
---

# 2026-04-14 — Gameplay Analysis Pipeline Implementation

## What was done this session

### Phase 1: Enhanced Server Logging (COMPLETE)

1. **DESYNC-SVR enhanced** — `GameManager.cs` line ~788: added `wp={willPower}/{maxWP}` and `targetDist={nearestEnemyDist}` to existing DESYNC-SVR snapshots. Computes nearest enemy distance inline. NOT guarded (lightweight, always useful).

2. **HumanBehaviorRecorder.cs** — NEW file at `Assets/Scripts/Debug/HumanBehaviorRecorder.cs`. Entire file inside `#if UNITY_EDITOR`. Singleton on GameManager. Emits:
   - `[HBR:SNAPSHOT]` every 30 ticks: position, state, wp, stamina, focus, target, targetDist, moveVec, facing
   - `[HBR:MELEE]`, `[HBR:DODGE]`, `[HBR:SPELL]`, `[HBR:SPECIAL]`, `[HBR:ASTRA]`, `[HBR:GOD_ABILITY]`, `[HBR:ELEMENTAL_SHIELD]` on action events
   - `[HBR:STATE_CHANGE]` on FSM transitions
   - `[HBR:DAMAGE_TAKEN]` from WP delta detection
   - `[HBR:SUMMARY]` at match end with full statistics
   - Burst tracking, attack distance tracking, focus peak tracking built in

3. **DebugLogTracker.cs** — Added `"[HBR:"` to trackedTags array (line ~45)

4. **GameManager.cs** — Added `#if UNITY_EDITOR` guarded:
   - `public bool enableHBR = false;` field with Inspector tooltip
   - HBR component initialization in `Start()` (after balance provider, before test mode)
   - `HumanBehaviorRecorder.Instance.OnMatchEnd()` call in `EndGame()`

5. **PlayerManager.cs** — Added `#if UNITY_EDITOR` guarded hook after `RecordStateAtTick()` (line ~1236):
   ```csharp
   if (HumanBehaviorRecorder.Instance != null && HumanBehaviorRecorder.Instance.enabled && !player.IsBot)
       HumanBehaviorRecorder.Instance.OnPlayerInput(player, input, GameManager.serverTick);
   ```

### Phase 2: Python Analysis Pipeline (COMPLETE)

6. **tools/aum_gameplay_analyzer.py** — NEW file (~550 lines). Full Python analyzer that:
   - Parses BOTH legacy format (`[MELEE:`, `[DESYNC-SVR]`, `[Focus:`) AND new `[HBR:]` format
   - Backward compatible — works with existing 13 logs immediately
   - Computes: SpacingProfile, AttackRhythm, AbilityUsage, PhaseDetection, ResourceManagement
   - Burst detection with 1.5s gap threshold
   - Auto-detects APPROACH/EXCHANGE/DISENGAGE/RESET phases from position + action data
   - Multi-session aggregation via `--logs` accepting multiple files
   - Outputs JSON Gameplay Profile with confidence score
   - **TESTED** against `server_session_2026-04-11_14-44-03_port6006.log` — correctly identified:
     - Hfhfhru (HUMAN, Amuktha) vs EditorPlayer2 (BOT, MantraMuktha)
     - Engagement distance: 2.15m
     - Burst sizes: [4, 1, 7, 12, 23, 5, 3, 3, 3]
     - Avg gap: 13.1s between bursts
     - Hit rate: 92.5%
     - Phase cycle: 11.7s (APPROACH 2.2s → EXCHANGE 4.5s → DISENGAGE 1.7s → RESET 3.4s)
     - Resource pattern: "hoarder" (focus peaked at 100)

### Phase 3: Profile → Bot Configuration (COMPLETE — session 2)

- `tools/profile_to_config.py` — maps Gameplay Profile JSON to HumanDerivedPreset JSON. Per-style defaults hardcoded. Converts spacing→comfort zone, rhythm→attack timing, abilities→spellPreference, phases→rhythm mults + movement profile, resources→reaction time.
- `BotPersonality.cs` — added `FromPresetJson(string json, BotPersonality, out MovementProfile)`. `HumanDerivedPreset` serializable class. Overrides only non-zero fields from JSON.
- `BotBrain.cs` — added `TryLoadPreset()` — searches `ServerData/BotPresets/{Style}_*.json`, picks random if multiple exist. Called after `ForStyle()` but before subsystem init.

### Phase 4: Movement Layer Wiring (COMPLETE — session 2)

- `BotMovement.cs` — added `MovementProfile` struct with `DefaultForStyle()` for all 5 styles. 4 new methods: `GetExchangeMovement()` (70% plant, 30% half-speed strafe), `GetRetreatMovement()` (ranged=strafe+backpedal, melee=sprint), `GetOrbitMovement()` (lateral orbit with distance correction), `GetPhaseSpeedMult()` (returns per-phase multiplier from profile).
- `BotExecutor.cs` — `GetPhaseMovement()` rewritten: preserves BUG-01 Survive override (ranged never retreat), then switches on `BotCombatRhythm.CombatPhase` with speed mult from MovementProfile. Approach closes to plant distance, Engage commits at full speed, Exchange micro-adjusts or re-closes, Disengage retreats if profile allows, Reset orbits or strafes.
- `Bot.cs` — updated constructor call for new `BotMovement(personality, movementProfile)` signature.

### Phase 5: Difficulty Scaling (COMPLETE — session 2)

- `DifficultyScaler.cs` — NEW file. Static `Scale()` method lerps: reaction time 3x→1x, aim accuracy 35%→baseline, mistake chance 40%→baseline, attack rate 2.5x→1x, spell cooldown 2x→1x, aggressiveness 0.2→baseline, hesitation 0.9→baseline, approach speed 0.5x→baseline, chase persistence 0.1→baseline.
- `BotBrain.cs` — `public static float botDifficulty = 0.75f` (configurable via CLI). Applied after preset loading in `Start()`.

### What's NOT done yet (remaining tasks)

**Phase 6: The Complete Loop (0/1 tasks)**
- Play 15 matches (3 per style), run analyzer, generate presets, test against human-derived bots
- This is a MANUAL process, not code

## Files modified (uncommitted — on top of fa64b74)

| File | Status | Guard |
|------|--------|-------|
| `Assets/Scripts/Debug/HumanBehaviorRecorder.cs` | NEW | `#if UNITY_EDITOR` |
| `Assets/Scripts/Debug/DebugLogTracker.cs` | MODIFIED (1 line) | None |
| `Assets/Scripts/Managers/GameManager.cs` | MODIFIED (~20 lines) | Partial `#if UNITY_EDITOR` |
| `Assets/Scripts/Player/PlayerManager.cs` | MODIFIED (4 lines) | `#if UNITY_EDITOR` |
| `Assets/Scripts/Bots/BotMovement.cs` | MODIFIED (~150 lines added) | None — ships in server builds |
| `Assets/Scripts/Bots/BotPersonality.cs` | MODIFIED (~100 lines added) | None — ships in server builds |
| `Assets/Scripts/Bots/Core/BotBrain.cs` | MODIFIED (~50 lines added) | None — ships in server builds |
| `Assets/Scripts/Bots/Core/BotExecutor.cs` | MODIFIED (~70 lines rewritten) | None — ships in server builds |
| `Assets/Scripts/Bots/Bot.cs` | MODIFIED (2 lines) | None |
| `Assets/Scripts/Bots/DifficultyScaler.cs` | NEW | None — ships in server builds |
| `tools/aum_gameplay_analyzer.py` | NEW | N/A (Python) |
| `tools/profile_to_config.py` | NEW | N/A (Python) |

## How to resume

1. Read this session file
2. Read the plan at `/Users/mac/.claude/plans/reflective-sniffing-fiddle.md`
3. Check `git diff --stat` on AUM-Unity-Server-Legacy to verify uncommitted changes
4. Continue with Phase 3 tasks: MovementProfile struct in BotMovement.cs, then GetPhaseMovement wiring in BotExecutor.cs, then preset loading, then DifficultyScaler, then profile_to_config.py
5. After all code is done, commit and playtest

## Key files to read for context

- `BotMovement.cs` (151 lines) — needs MovementProfile + 4 new methods
- `BotExecutor.cs` (~901 lines) — `GetPhaseMovement()` method needs rewrite
- `BotPersonality.cs` (231 lines) — needs `FromPresetJson()` + MovementProfile defaults
- `BotBrain.cs` (830 lines) — needs preset loading in `Start()`
- `BotCombatRhythm.cs` (223 lines) — defines the 5 combat phases the movement should respond to

## Per-style MovementProfile defaults (from the plan)

| Style | Approach | Exchange | Disengage | Reset | Retreat? |
|-------|----------|----------|-----------|-------|----------|
| Amuktha | 1.0 rush | 0.1 plant | 0.0 never | 0.0 stand | No |
| MukthaMuktha | 0.9 | 0.2 adjust | 0.5 back off | 0.4 strafe | On heavy hit |
| MantraMuktha | 0.7 cautious | 0.0 plant | 0.8 retreat | 0.6 orbit | At <40% HP |
| PaniMuktha | 0.8 | 0.3 strafe | 0.6 back off | 0.5 orbit | At <30% HP |
| YantraMuktha | 0.6 hesitant | 0.0 plant | 1.0 full retreat | 0.7 wide orbit | At <40% HP |

## DifficultyScaler parameter table (from the plan)

| Parameter | At 0.0 (easy) | At 0.5 (casual) | At 1.0 (human) |
|-----------|---------------|-----------------|-----------------|
| Reaction time mult | 3.0x | ~1.5x | 0.8x |
| Aim accuracy | 35% | 65% | human baseline |
| Mistake chance | 40% | 15% | human baseline |
| Attack rate mult | 2.5x slower | ~1.5x | 1.0x |
| Aggression | 0.2 | lerp | human value |
| Hesitation | 0.9 | lerp | human value |
| Approach speed | 0.5x | lerp | human value |
| Resource greed | 0.1 (wastes) | lerp | human value |
