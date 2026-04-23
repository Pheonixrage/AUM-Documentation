---
date: 2026-04-11
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
goal: (1) Bot spell AOE check must mirror the human's "red indicator" detection logic exactly. (2) Third Eye vs Astra decision keyed on TARGET's HP — low HP = Third Eye, healthy = Astra.
status: code complete, NOT committed, needs playtest verify
related_bugs: BUG-04 gate tightening + new rule from user conversation
related_logs: DebugLogs/server_session_2026-04-11_11-27-09_port6006.log (the YantraMuktha session where the need was noticed)
---

# 2026-04-11 — Spell AOE Check + Third Eye/Astra Value Rule

## User requests (verbatim paraphrase)

1. "bots should always use spells only when they at least have the opponents in their AOE of the spell when they are planning to use it. There is a red indicator that spawns when the players are in the AOE of their attacks or spells — maybe we can use that or at least some sort of check before using the spell. Even if they miss it's fine, but they shouldn't use the spell when the opponents are not in the AOE at all — that is some wrong behaviour."

2. "Third Eye usage should be valued upon whether to use it or use the Astra based on the opponent's health. If the opponents have low health, they can go for Third Eye. Otherwise it's wise to actually use the Astra itself because it does more damage."

3. "yea the third eye and astra thing is about the enemy's hp, not the bot's."

## Part 1 — Spell AOE check

### The human's red-indicator logic

Found in `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/CastManager.cs:318-390`. The `EnemyGlowOnDetection` function dispatches on `detectionType` and uses one of three geometric checks. Each elemental's cast prefab specifies which detection type it uses:

| Element | detectionType | spellDistance | effectAngle | maxRange |
|---|---|---|---|---|
| AIR | 0 Circle | 3 | — | 10 |
| FIRE | 1 Cone | 8.75 | 155 Brahma / 45 Vishnu | 0 |
| WATER | 2 Box | 10 | — | 0 |
| EARTH | 0 Circle | 9 | — | 0 |
| ETHER | 0 Circle | 9 | — | 0 |

Read from `Assets/Resources/CastPrefabs/<Element>/<ELEMENT>_0_0.prefab`.

The human's check per type (with `indicatorPos = castGameObject.transform.position`):
- **Circle**: `dist(target, indicatorPos) ≤ spellDistance[god]`
- **Cone**: distance ≤ radius AND target within `effectAngle[god]` of player forward
- **Box**: target inside rectangle at player position extending `spellDistance` forward, half-width 2.4 (CastManager `width = 4.8`)

And `indicatorPos = caster.pos + caster.forward × Clamp(localZ, minRange, maxRange)`.

### What I had

`BotStateReader.CanSpellHitTarget` used a flat `dist(bot, target) ≤ spellDistance` for every element. Three bugs at once:

1. **Too strict for Air.** Air can reach 13m (maxRange 10 + radius 3), but the flat check rejected anything past 3m.
2. **Wrong for Water.** Water uses box detection. A target 8m forward + 4m laterally passes `dist ≤ 10` (distance ≈ 9m) but fails the actual box check.
3. **Approximately right for Fire/Earth/Ether by accident.** Those spells spawn at caster and use `spellDistance` as reach, so the flat check roughly worked — but Fire's cone angle was ignored.

### What I did

Rewrote `CanSpellHitTarget` to:
1. Compute `spawnPoint = botPos + flatDirToTarget × Clamp(dist, minR, maxR)` — the same formula `BotExecutor.CastSpell` uses when it fires, so the gate evaluates what will actually happen.
2. Switch on `attrs.detectionType`:
   - **Circle**: `Vector3.Distance(spawnPoint, targetPos) ≤ spellRadius`
   - **Cone**: distance check AND `Vector3.Angle(flatDir, toTargetFromSpawn) ≤ angle / 2`
   - **Box**: project `target - spawnPoint` onto `flatDir` and perpendicular right axis, require `0 ≤ forwardDot ≤ spellRadius` AND `|rightDot| ≤ 2.4`
3. Reject if `spellRadius ≤ 0` (unsafe to evaluate).

Verification example per element, target 5m directly in front of bot:
- **AIR**: spawn = bot + dir × 5 = at target. dist(spawn, target) = 0 ≤ 3. PASS ✓
- **FIRE**: spawn = bot (maxR=0). dist(spawn, target) = 5 ≤ 8.75. angle = 0 ≤ 155/2 or 45/2. PASS ✓
- **WATER**: spawn = bot. forwardDot = 5 in [0, 10]. rightDot ≈ 0 in [-2.4, 2.4]. PASS ✓
- **EARTH**: spawn = bot. dist(spawn, target) = 5 ≤ 9. PASS ✓
- **ETHER**: same as Earth. PASS ✓

Target 15m away (out of Air reach but inside Water's box length):
- **AIR**: spawn = bot + dir × 10. dist(spawn, target) = 5 > 3. REJECT ✓
- **FIRE**: spawn = bot. dist = 15 > 8.75. REJECT ✓
- **WATER**: spawn = bot. forwardDot = 15 > 10. REJECT ✓
- **EARTH/ETHER**: dist = 15 > 9. REJECT ✓

Target 5m away + 4m laterally (fails Water box but passes circle check):
- **WATER**: forwardDot = 5 in [0, 10], rightDot = 4 > 2.4. REJECT ✓ (old code would have incorrectly allowed)

### File touched

`/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotStateReader.cs` — `CanSpellHitTarget` completely replaced (about 70 lines). No other function affected.

## Part 2 — Third Eye / Astra value rule

### The rule

Per user: decision variable is TARGET's HP.

- `targetWPPercent < 0.45f` AND Shiva AND Third Eye available → **Third Eye** (save Astra for bigger fish)
- `targetWPPercent >= 0.45f` → **Astra** (healthy target, Astra damage has max value)

Reasoning: Astra is the big-damage, long-cooldown ultimate. Spending it on a 20% HP target wastes most of the damage. Third Eye + a melee chain finishes the kill cheaply and keeps Astra banked.

### Implementation

New helper at `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Tactics/BotTactician.cs`:

```csharp
private static bool ShouldPreferThirdEyeOverAstra(
    ref BotStateReader.BotGameState state,
    Player player,
    BotResourceEval r,
    bool canThirdEye)
{
    if (state.god != TrinityGods.Shiva) return false;
    if (!canThirdEye || !r.canAffordGodAbility) return false;
    if (player.IsThirdEyeActive()) return false;
    return state.targetWPPercent < 0.45f;
}
```

Called from two places in `Evaluate`:

1. **P3 Execute** — when target is low HP / vulnerable / huge advantage:
   ```csharp
   if (ShouldPreferThirdEyeOverAstra(ref state, player, r, canThirdEye))
       return Pick(BotAction.GodAbility, "execute_thirdeye_finisher");
   if (canAstra && ...) return Pick(BotAction.Astra, "execute_astra_kill");
   ```

2. **P4 Astra Strategy** — when target is 30-45% HP (kill confirm range):
   ```csharp
   if (state.targetWPPercent < 0.45f)
   {
       if (ShouldPreferThirdEyeOverAstra(...))
           return Pick(BotAction.GodAbility, "astra_branch_thirdeye_finisher");
       return Pick(BotAction.Astra, "astra_killconfirm");
   }
   ```

### What this does NOT change

- **P1 Kamikaze Survive**: bot's own HP critical + aggression > 0.6 → still fires Astra. Bot is dying, last-chance damage matters more than banking Astra.
- **P7a Proactive God Ability**: 20% chance per eval for Third Eye / Brahma Shield cycling. Independent of the kill-confirm value question. Still fires as a general buff-before-melee.
- **Brahma / Vishnu gods**: no Third Eye option, so the helper returns false → always use Astra for kill confirms. Unchanged.

## Files touched (2)

1. `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotStateReader.cs` — `CanSpellHitTarget` rewrite
2. `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Tactics/BotTactician.cs` — new helper + P3 and P4 updates

## Pre-commit checklist

- [ ] Unity compiles (no missing `CastDetectionType` reference — it's in `Assets/Scripts/Enum.cs`, same assembly)
- [ ] Playtest vs YantraMuktha + Shiva bot
- [ ] Expect: bot casts Air when you're in its 13m reach, doesn't cast Earth/Ether when you're past 9m, Fire only when you're in front (within cone), Water only when you're in the forward box
- [ ] When you drop below 45% HP, bot should fire Third Eye instead of Astra
- [ ] When you're at full HP and bot has 100 focus + HP advantage, bot should fire Astra proactively
- [ ] Commit all of 2026-04-11's changes as one WIP when confirmed (spell aim fix, LogEvent unmute, save-for-astra, proactive god, AOE check, Third Eye rule)

## Open observations

- The YantraMuktha 147-watchdog loop from log `11:27:09` is still unresolved. Separate root cause (FSM Aiming transition). Not fixing here — filed in BUGS-ACTIVE as BUG-08 candidate.
- The `P4 astra_killconfirm` branch previously fired Astra aggressively on <45% HP. It's now gated behind `ShouldPreferThirdEyeOverAstra`. This means Shiva bots will naturally hoard Astra longer (until target ≥ 45% HP + the bot has full focus). Should surface in playtests as more Astra usage against full-HP humans.

## Lessons filed

- **LESSONS #9** — Third Eye vs Astra decision keys on TARGET's HP, not bot's.
- **LESSONS #10** — Spell AOE check must mirror per-detection-type geometry, not use a flat distance.
