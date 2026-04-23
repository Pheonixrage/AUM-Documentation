---
date: 2026-04-11
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
goal: Diagnose YantraMuktha Astra/Third Eye starvation and fix without regressing MukthaMuktha Astra behavior
status: code complete, NOT committed, needs playtest verify
related_bugs: BUG-03 (bots never cast Astra — YantraMuktha regression of the MukthaMuktha working case)
related_logs: DebugLogs/server_session_2026-04-11_11-27-09_port6006.log
---

# 2026-04-11 — YantraMuktha Astra Starvation

## Goal

User reported: "yantramuktha is spamming spells, not using Astra, not using Third Eye. why was MukthaMuktha able to use astra and why isn't yantramuktha using the astra". They played a ~3 minute 1v1 vs YantraMuktha bot and got zero bot Astra / zero bot Third Eye.

User also confirmed the earlier BUG-04 spell aim fix works: spells spawning properly.

## Evidence from log `server_session_2026-04-11_11-27-09_port6006.log`

Bot: YantraMuktha. Bot nickname `EditorPlayer2`. Human: `Hfhfhru` (Amuktha).

**Spell spawns:** 5 AIR spells over ~90 seconds.
**Bot Astra events:** 0.
**Bot Third_Eye events:** 0.
**Bot max focus seen in snapshots:** 73 (~2.9 segments). Never hit 100.

**EVENT distribution:**
```
147 WATCHDOG     (mostly failed_MeleeAttack_blacklisted)
 69 PHASE
 64 STALL_BREAK
 15 COMMIT_ENTER (Cast_Spell — the 5 spells)
 15 COMMIT_EXIT
  2 STRATEGY    (Pressure the whole match)
```

**Action histogram (from BOT snapshots):** only `Dodge`, `Idle`, `MeleeAttack`, `Reposition`. Zero `CastSpell`, zero `GodAbility`, zero `Astra` in the action stream — meaning the **tactician never picked** those actions. The 5 AIR spells that fired came from somewhere else (follow-up chain or WATCHDOG-forced branch).

## Why focus never reached 100

1. YantraMuktha's `BotPersonality.ForStyle` (line 167-185) sets `spellPreference = 0.9f`. Combined with `personality.aggression ≈ 0.5`, the P5 Spell branch fires at ~90% probability per tactical eval.
2. Each AIR cast consumes 1 focus segment (`FocusBarSegments: 1` in the AIR cast prefab).
3. Focus build-up for YantraMuktha is slow compared to MukthaMuktha — ranged volleys score once per 3-arrow shot, each volley counts as 1 hit (`Focus:VOLLEY ... COMPLETE — counting as single HIT`). Melee styles like MukthaMuktha score once per swing.
4. Net result: bot built to ~50–75 focus, cast a spell, dropped to 25–50, rebuilt, cast again. Never held 100 focus long enough to trigger the P4 Astra branch.
5. The `shouldSaveForAstra` rule was designed to prevent this, but its threshold was `FocusState.Near` = 3 segments (≥ 75 focus). Bot never reached 3 segments in practice, so the rule was dead code.

## Why Third Eye never fired

In `BotTactician.Evaluate`, the P7 default branch returns `MeleeAttack` as soon as `canMelee && r.isInAttackRange`. That's true almost every tick for a bot planted in range. The god-ability branch is **after** that early-return, so it was only reachable when `canMelee == false` (FSM animation blocking). In practice, that window was too short for the 20% chance to ever hit.

## Why MukthaMuktha worked but YantraMuktha didn't

MukthaMuktha has `spellPreference = 0.7f` (vs 0.9 for YantraMuktha) — lower cast rate. Plus melee axe swings build focus faster per second than ranged bow volleys. The net focus budget was positive, so MukthaMuktha occasionally reached 4 segments and fired Astra in log 09:56.

## Fixes

### Fix 1: `BotResourceEval.shouldSaveForAstra` — save starting at 2 segments

File: `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Tactics/BotResourceEval.cs`

**Before:**
```csharp
r.shouldSaveForAstra = r.focus == FocusState.Near  // 3 segments = 75 focus
    && cooldowns[5] <= 0f
    && state.targetWPPercent > 0.40f;
```

**After:**
```csharp
r.shouldSaveForAstra = r.focus >= FocusState.Some   // 2+ segments = 50+ focus
    && state.focusSegments >= 2
    && cooldowns[5] <= 0f
    && state.targetWPPercent > 0.40f;
```

Once the bot has 50 focus AND Astra is ready AND the target isn't about to die, it stops casting spells and lets melee build focus to 100. Astra fires on P4, cooldown starts, spell casting resumes.

### Fix 2: New P7a proactive god-ability branch

File: `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Tactics/BotTactician.cs`

**New block between P6 and P7:**
```csharp
// P7a: proactive god ability — 20% chance per eval
bool canGodProactive = state.god == TrinityGods.Brahma ? canBrahmaShield : canThirdEye;
if (canGodProactive && r.canAffordGodAbility)
{
    float proactiveGodChance = 0.20f;
    if (state.god == TrinityGods.Shiva && !player.IsThirdEyeActive() && !r.shouldSaveForAstra
        && Random.value < proactiveGodChance)
        return Pick(BotAction.GodAbility, "proactive_thirdeye");
    if (state.god == TrinityGods.Brahma && r.threat != BotResourceEval.ThreatState.None
        && Random.value < proactiveGodChance)
        return Pick(BotAction.GodAbility, "proactive_brahma_shield");
}
```

Places Third Eye / Brahma Shield ahead of the default melee early-return. 20% chance per eval means melee still wins 80% of the time (it's the focus engine), but god abilities actually cycle through over a match.

Shiva Third Eye is suppressed when `shouldSaveForAstra` is true (don't burn focus on Third Eye if we're holding for Astra). Brahma Shield only fires when a threat is present (pre-emptive shielding). Both are conservative.

## What this does NOT change

- The BUG-04 spell aim fix (maxRange=0 semantics) — unchanged, still works.
- Phase 0 telemetry, Phase 2 committed-state gate, ranged-never-retreat — all unchanged.
- Tutorial override: `BotBrain.OnUpdate` still forces `Strategy.Punish` for tutorial bots, and tactician still blocks Astra in tutorial.
- Melee remains the default focus engine. 80% of ticks in range still go to melee.
- MukthaMuktha / PaniMuktha / Amuktha / MantraMuktha behavior: unchanged, because their `spellPreference` values are lower (0.4–0.8) and the save-for-astra rule only kicks in when the bot actually reaches 2 segments.

## Files touched (2)

1. `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Tactics/BotResourceEval.cs` — `shouldSaveForAstra` threshold change (5 lines)
2. `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Tactics/BotTactician.cs` — new P7a block (18 lines)

## Pre-commit checklist

- [ ] Unity compiles
- [ ] Playtest vs YantraMuktha + Shiva bot. Expect: melee attacks, occasional AIR spells when focus is 1 segment, then focus hoard past 50 → melee only → reach 100 → Astra fires.
- [ ] Expect Third Eye to fire periodically (~every few exchanges).
- [ ] Playtest vs MukthaMuktha + Shiva bot. Expect: same as before (Astra still working, now with added Third Eye usage).
- [ ] Check DebugLogs/*.log for `EVENT: STRATEGY` events (should show more variety than just Pressure).
- [ ] Commit all of today's changes as one WIP when confirmed.

## Open concerns

- The 147 WATCHDOG recoveries in the log suggest the YantraMuktha bot's melee (bow shot) is failing execution often. Not addressed in this session — separate root cause (likely FSM blocking during Aiming state transitions). Filing as an observation, not a fix.
- The 64 STALL_BREAK events indicate the bot spent long stretches in passive actions (Idle/Reposition) which triggers the stall breaker. Related to the above — when the bot's chosen action gets rejected repeatedly, it stalls.
