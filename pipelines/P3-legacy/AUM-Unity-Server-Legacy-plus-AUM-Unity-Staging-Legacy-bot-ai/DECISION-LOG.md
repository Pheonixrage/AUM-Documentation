---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
append_only: true
last_updated: 2026-04-11
---

# Decision Log

**Append-only.** One entry per decision, newest at the bottom. Each entry is a single line or short paragraph with links to the session file where the decision was made and the commit (if any) where it landed.

Format:
```
YYYY-MM-DD — <decision> → <file/commit/lesson link>
```

---

## 2026-04-10

- **Adopted the 3-layer Utility AI + BT shim architecture** for the Legacy server bot. Strategy → Tactician → Executor. Retained the BT (`BotBT.cs` + `Custom Action Nodes/`) as a shim used by Tutorial mode and fallback paths. Origin design: `cross-pipeline/bot-ai-design-reference-from-april-8/2026-04-08-bot-ai-architecture.md`. Implementation: commit `c1470f9`. → `CURRENT-STATE.md`

- **PaniMuktha discus aim offset fix** — removed erroneous `-15°` in `BotExecutor.cs`, kept correct `+8°` matching the original BT `TargetWithinRange.cs:77`. → `BUGS-FIXED.md#FIXED-01`, commit `c1470f9`

- **Tried `playerStats.range / 2f` for melee attack range, reverted** — made bots plant even farther out. `playerStats.range` is the actual hit radius, not a tuning knob. → `LESSONS.md#1`, same commit `c1470f9`

- **Plant distance = `attackRange * 0.75f`**, strictly inside the fire zone. Previous `attackRange + 0.5f` created a dead zone where the fire gate could never satisfy. → `BUGS-FIXED.md#FIXED-02`, commit `c1470f9`

- **Whiff detection + LOS sidestep recovery DISABLED.** `attackDone` fires on projectile spawn for all ranged styles, so every ranged swing was logged as a false whiff → infinite sidestep → bots walked to corners. Entire pipeline commented out; fields/methods left as dead code. → `BUGS-FIXED.md#FIXED-03`, `LESSONS.md#2`, commit `c1470f9`

- **Pre-attack LOS raycast REMOVED** (hardcoded `hasLOS = true`). Humans don't LOS-check before swinging. → `BUGS-FIXED.md#FIXED-04`, `LESSONS.md#3`, commit `c1470f9`

- **Committed WIP checkpoint `c1470f9`** — 76 files, 7347 insertions, 170 deletions. This is the pinned state for all docs in this folder until a new checkpoint is recorded. → `GIT-STATE.md`

## 2026-04-11

- **Initialized this Obsidian folder** (`pipelines/P3-legacy/AUM-Unity-Server-Legacy-plus-AUM-Unity-Staging-Legacy-bot-ai/`) to track Legacy bot AI work across sessions. Everything here is scoped to the Legacy pipeline only. Cross-contamination with AUM-Headless (V2 server) or AUM-2.0 Production/Server is explicitly forbidden by the `README.md` rules.

- **Queried the `BOT AI AUM` NotebookLM notebook** for guidance on the three open bugs (spell aim offset, obstacle detection, post-Astra haywire). Response saved verbatim at `research/notebooklm-2026-04-10-response.md`. Architecture confirmed valid — do NOT switch to GOAP or HTN.

- **Phase 0 implemented** — Added `[BOT:` to `DebugLogTracker.trackedTags`. Bot telemetry will now reach session log files. → `sessions/2026-04-11-phase-0-and-2-implementation.md`, BUG-06 pending playtest verification.

- **Root cause of post-Astra haywire REVISED** — Yesterday's diagnosis blamed "enemy Astra → Survive → retreat" heuristic. `BotStrategy.ScoreSurvive` actually only triggers on the bot's OWN HP drop, not enemy-Astra. The real chain is: Shiva Astra ticks damage → bot HP drops below 30 % → strategy flips to Survive on next re-eval → `GetPhaseMovement` sets `IsRetreating=true` for the ranged bot → camera race between aim-hold ticks and non-aim ticks compounds retreat drift → bot physically walks northwest → volleys miss. → `sessions/2026-04-11-phase-0-and-2-implementation.md` section "Root cause revision".

- **Phase 2 implemented (code only, not playtest-verified)** — Two mechanisms:
  1. **Ranged bots never retreat** — `BotExecutor.GetPhaseMovement` Survive branch guards on `state.isRanged`. Ranged bots in Survive stay and fire, close to attack range if needed, never turn their back. Melee retreat behavior unchanged.
  2. **Committed-state gate** — Top of `BotBrain.OnUpdate` checks `BotExecutor.IsFullyBlocked(currentFsmState)` and bypasses the full tick pipeline if true. `ExecutePassthrough(dt)` sends minimal input (current facing, zero joystick, state resolution). `ResetTransientState()` drops `isAiming`, `isSpellAiming`, `isSpecialAiming`, shield holds, and follow-ups on commit entry and exit. New field `wasCommittedLastTick`. Telemetry events `[BOT:EVENT] COMMIT_ENTER` and `COMMIT_EXIT`.

  → `sessions/2026-04-11-phase-0-and-2-implementation.md`, BUG-01 code fix pending playtest verification.

- **NOT committed yet** — changes sit in the working tree on top of `c1470f9`. Next session should playtest first, then commit.

### Playtest verification (later the same day)

- **Phase 0 verified working** — Logs `server_session_2026-04-11_09-56-02` and `_10-04-04` both contain `[BOT:...]` snapshot lines. BUG-06 can move to `BUGS-FIXED.md`.

- **BUG-03 first bot Astra observed** — Log 09:56 shows bot entering `Astra_Channel` and `Astra_Cast` states twice in one match. First evidence of bot Astras in any recorded session. Likely enabled by the committed-state gate + transient reset clearing stale aim state that was blocking Astra builds. Not yet marked fixed — needs 2+ more playtest confirmations.

- **BUG-02 improved, not resolved** — Bot spell casts went from "1 across 7 sessions" yesterday to "2 in one match, 5 in another" today. Real progress. Still a gap before this feels natural.

- **BUG-01 post-Astra haywire NOT REPRODUCIBLE in today's matches** — Both matches had the bot's HP at 44–100 %, never dropping below 30 %, so `ScoreSurvive` never fired, so the retreat branch never ran. Yesterday's "ranged bots never retreat" fix is not yet proven. Needs a future match where bot HP actually drops into Survive territory.

- **BUG-04 spell abilityPos CONFIRMED WITH POSITIONAL MATH** — Three bot spell spawns analyzed in logs 09:56 and 10:04. Spell spawn coordinates matched the human player's position to within 0.1 m in every case, while the bot was 0.65 m to 3 m away. Conclusive proof that `BotExecutor.ExecuteAction.CastSpell0-3` was sending `new Vector2(targetPos.x, targetPos.z)` as `abilityPos`, and the human pipeline uses `caster.pos + caster.forward × clampedRange` via `CastManager.castGameObject.transform.position`.

- **BUG-04 fix implemented** — `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs` CastSpell branch now computes `worldCastPoint = botPos + flatDirToTarget × Clamp(distToTarget, minRange, maxRange)` and sends that as `abilityPos`. Matches the human's geometric pipeline exactly. Astras not touched (AstraManager doesn't use abilityPos). See `LESSONS.md #5`. → `sessions/2026-04-11-phase-1-spell-aim-fix.md`

- **Telemetry gap fixed** — `BotTelemetry.LogEvent` was gated on `verboseConsole` which `BotBrain.Start` sets to false. Removed the gate so `COMMIT_ENTER`, `COMMIT_EXIT`, `STRATEGY`, `PHASE`, `STALL_BREAK`, `WATCHDOG`, `HIT`, `WHIFF` events all reach the session log. `LogDecision` and `LogMovement` still gated (too noisy).

- **New bug filed: BUG-07** — Tactician priority order never lets MukthaMuktha/PaniMuktha/YantraMuktha ranged-specials (axe throw, discus barrage, charged shot) win a scoring round. They're only considered in the P7 "default_special" fallback after the P7 "default_melee_engine" early return, which fires whenever `canMelee && r.isInAttackRange`. Need to add a mid-range branch that lets these styles pick their special. Explains user-reported "bot is not using the special ability at all". → `BUGS-ACTIVE.md#BUG-07`

- **Still NOT committed** — working tree now has yesterday's Phase 0+2 PLUS today's Phase 1 spell aim + telemetry fix. Next session: playtest MukthaMuktha/Shiva bot, watch for spell spawns in FRONT of the bot (not on the human), commit as a single WIP if it looks good.

### Later the same day (2026-04-11 afternoon)

- **User playtested the spell aim fix and reported: "wtf it used ether and earth at my position"** — meaning my fix was broken for Fire/Water/Earth/Ether.

- **Root cause of the broken fix:** My `BotExecutor` CastSpell branch had `if (maxR > 0f) castDist = Mathf.Min(castDist, maxR);`. For Fire/Water/Earth/Ether all have `maxRange = 0` in their cast prefabs, so the guard skipped, and `castDist` stayed at `distToTarget` → `worldCastPoint = targetPos`. Reproducing the original bug for exactly those four spells. Air worked because maxR=10.

- **Real semantics of `maxRange = 0`:** The cast indicator's `localPosition.z` is clamped to `[minRange, maxRange]` on the HUMAN client. Both at 0 means the indicator stays on the caster's body, so `abilityPos = caster.position`. Four of five elementals are intentionally caster-centered because their spell implementations use `transform.position` directly: Fire (cone from forward), Water (moving projectile), Earth/Ether (sphere at spawn). Only Air has `maxRange = 10` because it's the one elemental the human can drag forward with vertical mouse.

- **Correct fix implemented** — Replaced the guard with unconditional `Mathf.Clamp(distToTarget, minR, maxR)`. When both are 0, `Clamp` returns 0, and the bot's `worldCastPoint` equals `botPos` — exact same as the human's cast indicator position for those spells. Air still works because `Clamp(dist, 0, 10)` gives a forward point. → `BotExecutor.cs` CastSpell branch, one block replaced.

- **LESSONS #7** added: `maxRange = 0` means "spawn at caster", NOT "no maximum". Bot arithmetic must match human arithmetic exactly, including edge cases around zeros.

- **AOE gating already correct** — `BotStateReader.CanSpellHitTarget` checks `if (dist > castDist) return false` where `castDist = spellDistance` (the AOE radius from the spawn point). So the tactician already refuses to cast when the target is outside the spell's effect sphere. No additional fix needed for "cast only when in range".

- **Still NOT committed** — working tree now carries the corrected spell fix + yesterday's Phase 0+2 changes. All in one file: `BotExecutor.cs` (+ yesterday's `BotBrain.cs`, `BotTelemetry.cs`, `DebugLogTracker.cs`).

### Later afternoon (YantraMuktha Astra starvation diagnosis)

- **User reported:** "yantramuktha keeps spamming [spells], why was MukthaMuktha able to use Astra and why isn't Yantramuktha? This one didn't even use Third Eye either". Compared to earlier 09:56 log where MukthaMuktha bot fired 2 full Astra cycles.

- **Root cause:** YantraMuktha's `BotPersonality.spellPreference = 0.9f` burns focus at ~90% of evals. Bot never accumulates past 2 segments (50 focus), Astra needs 4 (100 focus). `shouldSaveForAstra` was gated at 3 segments → dead code for YantraMuktha. Third Eye branch was after the default melee early-return → unreachable when bot is in melee range. See `sessions/2026-04-11-yantra-astra-starvation.md`.

- **Fix 1:** `BotResourceEval.shouldSaveForAstra` threshold lowered from 3 segments → 2 segments. When focus ≥ 50 AND Astra cooldown ready AND target HP > 40%, bot stops casting spells and melee-builds to 100. → `BotResourceEval.cs` line 94

- **Fix 2:** New P7a "proactive god ability" branch in `BotTactician.Evaluate`, placed BEFORE the default melee early-return. 20% chance per eval. Shiva → Third Eye if not already active and not hoarding for Astra. Brahma → Shield if threat is present. Melee still wins 80% of ticks. → `BotTactician.cs` new block at line 283

- **LESSONS #8 added** — "High `spellPreference` styles starve themselves of Astra focus."

- **No regressions intended** — MukthaMuktha / PaniMuktha / Amuktha / MantraMuktha still have lower `spellPreference` (0.4–0.8) so the save-for-astra rule only fires when they actually reach 2 segments. Tutorial bot override still in place. Melee still the focus engine.

- **Still NOT committed** — working tree now has all of today's afternoon changes. Next session: playtest YantraMuktha to confirm Astra + Third Eye both fire, then commit all of 2026-04-11 as one WIP.

### Later afternoon (AOE check + Third Eye/Astra value rule)

- **User request 1:** "Bots should always use spells only when they at least have the opponents in their AOE of the spell. There is a red indicator that spawns when the players are in the AOE — maybe use that or at least some check." → I located the human's exact red-indicator math in `CastManager.EnemyGlowOnDetection` (three detection types: Circle / Cone / Box) and replicated it in `BotStateReader.CanSpellHitTarget`. Per-element verification table recorded in session file. → `sessions/2026-04-11-aoe-check-and-thirdeye-value.md`, `LESSONS.md #10`

- **User request 2:** "Third Eye usage should be valued based on opponent health — low HP opponent = Third Eye, otherwise Astra because it does more damage" and "yea the third eye and astra thing is about the enemy's hp, not the bot's". → New helper `ShouldPreferThirdEyeOverAstra(ref state, player, r, canThirdEye)` in `BotTactician.cs`, returns true when Shiva + canThirdEye + !active + `targetWPPercent < 0.45f`. Called from P3 Execute and P4 Astra Strategy — Third Eye wins first, Astra is the fallback when god/cooldown/active blocks it. → `LESSONS.md #9`

- **Files touched in this sub-session (2):** `BotStateReader.cs` (CanSpellHitTarget rewrite, ~70 lines), `BotTactician.cs` (helper + 2 call sites)

- **Per-element AOE semantics locked in** (from cast prefabs verified 2026-04-11):
  - AIR: Circle, radius 3, maxRange 10 → effective reach 13m forward
  - FIRE: Cone, radius 8.75, angle 155 Brahma / 45 Vishnu, spawn at caster
  - WATER: Box, length 10, half-width 2.4 (width 4.8), spawn at caster
  - EARTH: Circle, radius 9, spawn at caster
  - ETHER: Circle, radius 9, spawn at caster

- **Committed as `fa64b74`** — user requested "just commit till here locally only" after the AOE check + Third Eye/Astra value rule landed. 7 files, 358 insertions, 39 deletions. All 2026-04-11 changes rolled into one WIP checkpoint on top of `c1470f9`: Phase 0 (telemetry tag + LogEvent unmute), Phase 2 (committed-state gate + ranged-never-retreat), BUG-04 spell `abilityPos` fix with `maxRange=0` correction, `shouldSaveForAstra` lowered to 2 segments, P7a proactive god ability branch, detection-aware `CanSpellHitTarget` (Circle/Cone/Box), Third Eye/Astra value rule keyed on target HP. Pinned checkpoint in `GIT-STATE.md` updated.

## 2026-04-14 — Gameplay Analysis Pipeline (Phase 1-5)

- **Phases 1+2 implemented (prior session)** — HumanBehaviorRecorder.cs (`#if UNITY_EDITOR`), DESYNC-SVR wp+targetDist enhancement, `[HBR:` tag in DebugLogTracker, Python analyzer `tools/aum_gameplay_analyzer.py`. All server-side, zero client impact. → `sessions/2026-04-14-gameplay-analysis-pipeline.md`

- **Phase 3 implemented** — `BotPersonality.FromPresetJson()` loads human-derived preset JSON, overrides personality fields + outputs MovementProfile. `HumanDerivedPreset` serializable class for `JsonUtility`. `BotBrain.TryLoadPreset()` searches `ServerData/BotPresets/{Style}_*.json`, picks random preset if multiple exist. → `BotPersonality.cs`, `BotBrain.cs`

- **Phase 4 implemented** — `MovementProfile` struct in `BotMovement.cs` with per-style defaults (5 styles). 4 new movement methods: `GetExchangeMovement()` (micro-strafe during combat), `GetRetreatMovement()` (ranged=sidestep, melee=sprint), `GetOrbitMovement()` (maintain comfort distance), `GetPhaseSpeedMult()` (joystick magnitude per phase). `BotExecutor.GetPhaseMovement()` rewritten: preserves BUG-01 Survive override exactly, then switches on `BotCombatRhythm.CombatPhase` with speed mult from MovementProfile. `Bot.cs` updated for new constructor signature. → `BotMovement.cs`, `BotExecutor.cs`, `Bot.cs`

- **Phase 5 implemented** — `DifficultyScaler.cs` static `Scale()` method. Lerps reaction time (3x→1x), aim accuracy (35%→baseline), mistake chance (40%→baseline), attack rate (2.5x→1x), spell cooldown (2x→1x), aggressiveness (0.2→baseline), hesitation (0.9→baseline), approach speed (0.5x→baseline), chase persistence (0.1→baseline). `BotBrain.botDifficulty` static field (default 0.75). Applied after preset loading in `Start()`. → `DifficultyScaler.cs`, `BotBrain.cs`

- **Phase 6 tool** — `tools/profile_to_config.py` maps Gameplay Profile JSON to HumanDerivedPreset JSON. Converts spacing→comfort zone, rhythm→attack timing, abilities→spellPreference, phases→rhythm multipliers+movement profile, resources→reaction time. Style defaults hardcoded to match C# code.

- **NOT committed** — All Phase 3-5 changes in working tree on top of `fa64b74`. 8 modified + 3 new untracked files. Next: playtest to verify phase-driven movement works, then commit.

## 2026-04-23 — Full day of bot iteration + 16 presets + 7 fix commits

- **Watchdog rewrite** (`2c54855`) — old watchdog counted "didn't fire this tick" as "action failed". Fired 84× blacklist events in a single 157s match. Fixed: failure only counted on tactical eval ticks, animation-in-progress counted as success, MIN_FAILED_EVALS 3→5, BLACKLIST 3s→1s. → `sessions/2026-04-23-bot-ai-iteration-day.md#1`

- **Post-action cooldown** (`be25952` + compile fix `d7b722a`) — Shield_Block stuck 7.2s, Aiming stuck 2.4s because tactician re-picked same action while animation was still playing. Added per-action cooldown: 500ms for most, 2000ms for Shield. Fixed compile error from using non-existent BotAction.CastSpell / BotAction.Shield — correct enum is CastSpell0/1/2/3 + ElementalShield/GodAbility. → `sessions/2026-04-23-bot-ai-iteration-day.md#2`

- **Smooth movement** (`bd19f8b`) — duty-cycle caused 5-7m lurches every 400ms. Out-of-range now always closes; duty cycle only applies to Reset phase. User confirmed "this is much better now". → `sessions/2026-04-23-bot-ai-iteration-day.md#3`

- **Ranged low-HP approach + spell target tracking** (`6cf227e`) — two fixes in one commit. (a) Ranged bot at <15% HP and out of range now approaches to firing range (was frozen because kamikaze branch returned Vector2.zero for all ranged). (b) Spell aim-hold recomputes spellAimTargetPos every tick using current target position (was locked at aim-entry). Plus 9 new human-derived presets. → `sessions/2026-04-23-bot-ai-iteration-day.md#4-5`

- **Shiva astra beam tracking** (`30a0183`) — Maheshwara astra fired in world +Z direction because camera computation was gated by IsFullyBlocked. Split gating: movement stays blocked during Astra_Cast/Channel/Anticipate, but camera continues tracking target. User reported "bot stays still during astra instead of aiming at me". → `sessions/2026-04-23-bot-ai-iteration-day.md#6`

- **Rejected fixes** (by combat-reviewer sub-agent) — TWO proposed fixes were killed before implementation:
  1. "Astra hoarding rule" — redundant with existing `BotResourceEval.shouldSaveForAstra` (focus≥50, target HP>40%, astra ready). Adding a second gate would risk stall.
  2. "Cancel spell if target leaves AOE mid-aim" — would waste the 500ms action cooldown, create visible bot indecision, and conflict with the intentional aim-commit design. Better fix: track target during aim (what I ended up implementing).

- **16 presets total** in `ServerData/BotPresets/` — full 5 styles × 3 gods matrix complete. All derived from user playtests where user dominated 8/9 matches. Encode "expert vs weak bot" patterns; will be regenerated from live PvP when Option 2 live telemetry is built. → `sessions/2026-04-23-option-2-live-telemetry-handoff.md`

- **Direction decided** — user chose Option 2 (live telemetry pipeline) over Option 1 (continued solo-vs-bot iteration) as the next major effort. Full plan written to `sessions/2026-04-23-option-2-live-telemetry-handoff.md`. ~2-3 weeks of focused work. Target: weekly automated preset regeneration from real PvP matches, <$5/mo infra cost.
