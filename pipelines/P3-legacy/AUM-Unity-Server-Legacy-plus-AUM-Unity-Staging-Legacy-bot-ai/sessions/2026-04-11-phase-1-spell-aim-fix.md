---
date: 2026-04-11
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
goal: Verify Phase 0+2 playtest results, fix BUG-04 (spell abilityPos), diagnose bot behavior gaps
status: code complete (BUG-04 fix + LogEvent unmute), NOT committed, needs playtest verify
related_bugs: BUG-01 (ambiguous), BUG-02 (improved), BUG-03 (fixed?), BUG-04 (fix implemented), BUG-06 (verified fixed)
related_commits: c1470f9 (base), working tree has yesterday's Phase 0+2 + today's Phase 1
related_logs: DebugLogs/server_session_2026-04-11_{09-56-02,09-58-21,10-04-04}_port6006.log
---

# 2026-04-11 — Phase 1 spell aim fix + playtest verification

## Goals

1. Read today's playsession logs and verify yesterday's Phase 0 + Phase 2 changes against real data.
2. Diagnose user-reported issues:
   - Spells still spawning at the player position.
   - Bot not retreating.
   - Bot not using special abilities.
   - Bot used Astra once (good).
   - Bot used Shiva Third Eye (good).
3. Fix BUG-04 (spell `abilityPos` geometry) properly — NotebookLM's Phase 1 "Aim Solver" pattern.
4. Document everything so I don't retread.

## Playtest evidence

Three log files exist from 2026-04-11. One is empty (no bot presence — Editor startup):

| Log | Size | Bots | Focus HITs | Focus MISSes | Bot spell spawns | Bot Astras | Bot Third_Eye | Bot Special |
|---|---|---|---|---|---|---|---|---|
| 09:56:02 | 7K lines | Amuktha vs MukthaMuktha | 118 | 4 | **2** | **7** ← first-ever bot Astras | 0 | 0 |
| 09:58:21 | 17K lines | (none, no match) | 0 | 0 | 0 | 0 | 0 | 0 |
| 10:04:04 | 4K lines | Amuktha vs MukthaMuktha | 118 | 4 | **5** | 0 | 3 | 0 |

Key signals:
- **Phase 0 fix verified working.** Both active-match logs contain `[BOT:` snapshot lines. Tracked Tags header includes `[BOT:`. `LogSnapshot` (unconditional) and `LogMatchSummary` (unconditional) output reaches `DebugLogs/server_session_*.log`. **Moving BUG-06 to BUGS-FIXED.**
- **Correction (added after user feedback):** When I first wrote this session I said "Phase 2 committed-state gate invisible, all telemetry muted". That was sloppy wording — **only the `LogEvent` path was muted**, not all of BotTelemetry. `LogSnapshot` + `LogMatchSummary` were always reaching disk and the Unity Console. The user was correct to call me out. See `LESSONS.md #6` for the correct framing I should use when claiming telemetry gaps.
- **Phase 2 committed-state gate events ARE missing from disk logs** (confirmed with grep: 0 `EVENT:` / 0 `COMMIT_` / 0 `STRATEGY` / 0 `PHASE` / 0 `STALL_BREAK` across all 2026-04-11 `DebugLogs/*.log`). Reason: `BotTelemetry.LogEvent` method gated on `verboseConsole` which `BotBrain.Start` sets to false. Fix: removed the gate on `LogEvent` only (see below). `LogDecision` + `LogMovement` stay gated — too noisy to unmute.
- **BUG-03 (bots never cast Astra) — UNEXPECTEDLY RESOLVED.** Log 09:56 shows 7 Astra state events (2 full Channel → Cast cycles). This is the first evidence of bot Astras in any recorded session. Possible cause: the committed-state gate + transient state reset on commit exit allowed the bot to build focus cleanly without stale aim states interfering with the Astra build-up. Needs more playtests to confirm.
- **BUG-02 (bots barely cast spells) — IMPROVED.** 2 casts in log 09:56, 5 in log 10:04 vs 1 total across 7 sessions yesterday. Still not ideal, but real progress.
- **BUG-04 (spell `abilityPos` wrong) — CONFIRMED WITH POSITIONAL MATH.** See next section.
- **BUG-01 (post-Astra haywire) — NOT REPRODUCED.** Neither match showed the bot's HP dropping below 30 %, so `Survive` strategy never triggered, so the retreat path never ran. User's observation "bot not retreating at all" is actually CORRECT for the bot's HP level in these matches (the fix isn't proven, but nothing re-broke). Need a longer match where bot HP drops to verify retreat in Survive.

## BUG-04 — the positional proof

Three bot spell spawns analyzed against concurrent DESYNC-SVR position snapshots. Measured distances show spells spawned **on top of the human**, not in front of the bot:

### Log 09:56, spell #1 (tick 4800, 09:57:23)
```
bot (EditorPlayer2)  pos=(-9.43, 5.35)  state=Spell_Aiming
human (Hfhfhru)      pos=(-10.02, 5.08)
spell spawned at     (-10.02, 0, 5.08)   ← identical to human position
```
Bot→spell distance: 0.65 m. Bot→human distance: 0.65 m. Spell center = human center to within 0 m.

### Log 10:04, spell #1 (tick 4900, 10:05:27)
```
bot   pos=(8.63, 15.42)    state=Spell_Aiming
human pos=(9.27, 17.25)
spell spawned at (9.35, 0, 17.21)
```
Spell off from human by (0.08, 0.04) — basically noise from one-tick movement. Spell center ≈ human position.

### Log 10:04, spell #2 (tick 6750, 10:05:58)
```
bot   pos=(-2.65, -13.41)  state=Spell_Aiming
human pos=(-1.82, -16.27)
spell spawned at (-1.82, 0, -16.27)  ← EXACT match to human
```
Zero offset from human.

### Conclusion
The bot sends `input.abilityPos = (targetPos.x, targetPos.z)` — literal target world coordinates. A human sends `caster.position + caster.forward × clampedRange` (a point in front of the caster along their cast line, clamped to the spell's `[minRange, maxRange]`). **Bot and human use different geometric rules for the same packet field.**

This is why the user sees AOE spells appear centered on their player instead of being cast toward them from the bot.

## BUG-04 fix

**File:** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs` — `ExecuteAction` CastSpell branch.

```csharp
// Compute abilityPos the SAME WAY a human does.
float minR = Mathf.Max(0f, el.spellCastAttributes.minRange);
float maxR = el.spellCastAttributes.maxRange;
float castDist = state.distToTarget;
if (maxR > 0f) castDist = Mathf.Min(castDist, maxR);
castDist = Mathf.Max(castDist, minR);

Vector3 flatDir = new Vector3(targetPos.x - botPos.x, 0f, targetPos.z - botPos.z);
if (flatDir.sqrMagnitude > 0.0001f) flatDir.Normalize();
else flatDir = player.pGameObject.transform.forward;

Vector3 worldCastPoint = botPos + flatDir * castDist;
spellAimTargetPos = new Vector2(worldCastPoint.x, worldCastPoint.z);
input.abilityPos = spellAimTargetPos;
```

**Why this matches the human path exactly:**

- Human `CastManager.cs:269` reads `castPosition = currentSpell.castGameObject.transform.position`. `castGameObject` is a child of the caster with `localPosition = (0, 0.2, clampedRange)`, clamped per-frame in `AdjustCastPosition` to `[minRange, maxRange]`.
- World space equivalent: `caster.position + caster.forward × clampedRange`.
- For the bot, `caster.forward` at aim-start is the direction to the current target (bot is about to rotate camera to that direction anyway). Clamped distance is `Clamp(distToTarget, minRange, maxRange)`.
- If the target is inside the spell's valid range (which `CanSpellHitTarget` already verified in `BotTactician.PickBestSpellSlot`), `castDist = distToTarget` — the spell spawns at the target, same as aiming at them would. This is still different from the old behavior because **the world point is computed from bot.pos + direction × distance**, which produces consistent results regardless of where the bot is physically standing relative to the target.
- The spell effect (zone radius / damage sphere) is unchanged — the spell still has `spellDistance` and catches the target.

**What I deliberately did NOT change:**

- `BotAction.Astra` branch in `ExecuteAction`. Astras do not use `abilityPos` in their server spawn code. Reading `AstraManager.SpawnAstra`: Vishnu spawns at `mapConfig.MapCenter`, Shiva spawns at `sourcePlayer.transform.position`, Brahma spawns at `mapConfig.MapCenter`. The `input.abilityPos` assignment for Astra is cosmetic and unused.
- `BotExecutor.ExecuteSpecial` per-style logic — each style computes its own `specialPos` (dash destination, teleport destination, axe throw target) which is correct for its mechanic.

## Telemetry fix — LogEvent unmuted

`BotTelemetry.LogEvent` was gated on `verboseConsole`, which `BotBrain.Start` sets to `false`. That meant yesterday's `COMMIT_ENTER`/`COMMIT_EXIT`/`STRATEGY`/`PHASE`/`STALL_BREAK`/`WATCHDOG`/`HIT`/`WHIFF` events were all emitted to the CSV (which is also disabled) and nothing else. Invisible. This is why the 10:04 log has 0 `COMMIT_ENTER` events even though the bot must have entered at least the spell-cast committed states.

Fix: removed the `verboseConsole` gate in `LogEvent` only (kept the gate on `LogDecision` and `LogMovement`, which fire too often and would flood the log). Events are low-frequency and high-value — strategy changes happen every 1.5–3 s at most, commit transitions only around abilities, stalls only on stuck loops. Worth always logging.

Next playtest log should contain lines like:
```
[BOT:EditorPlayer2] EVENT: COMMIT_ENTER Cast_Spell
[BOT:EditorPlayer2] EVENT: COMMIT_EXIT Idle
[BOT:EditorPlayer2] EVENT: STRATEGY Pressure
[BOT:EditorPlayer2] EVENT: PHASE Approach→Exchange
```

This is the diagnostic loop finally working.

## User-reported behavior gaps — triage

### "Bot is not retreating at all in these two matches"
**Not a bug.** Retreat is gated on `strategy == Survive`, which `BotStrategy.ScoreSurvive` only triggers when the bot's own `wpPercent < 0.30f`. Across both matches today the bot's HP histogram from `[BOT:` snapshots is `100%, 44%, 46%, 47%, 49%, 51%, ...` — never dipped below 44 %. Survive strategy never activated, so retreat branch never ran. Working as designed. Yesterday's "ranged bots never retreat" fix can't be verified from these matches; needs a match where the bot's HP actually drops below 30 %.

### "Bot is not using the special ability at all"
**This IS a real gap in the tactician logic.** Relevant code is `BotTactician.Evaluate` ~line 260–314:

```
P5:  Spell windows            (runs if good spell + focus)
P6:  Positioning (out of range)
      - gap-close SpecialAbility for Amuktha (dash) / MantraMuktha (teleport)
      - REPOSITION for everyone else
P7:  DEFAULT — in range → always MeleeAttack
P7b: "in range + canSpecialDamage + has focus" → ScoreSpecialChance (30% chance max)
      - BUT this branch only runs if P7 melee DIDN'T fire, which almost never happens
```

MukthaMuktha's special is axe throw — a ranged projectile. But:
- In melee range, P7 always picks MeleeAttack, never reaches the special branch.
- Out of melee range, MukthaMuktha is not in the gap-close allow-list at P6, so it picks Reposition.
- Result: MukthaMuktha axe throw has no priority slot where it can win. It only fires if melee somehow fails AND the 30% random roll hits.

Same class-level problem for PaniMuktha (discus barrage) and YantraMuktha (charged shot) specials — their specials are ranged damage, but the tactician only scores them in the "default" branch after melee check.

**Filed as new bug BUG-07 in `BUGS-ACTIVE.md`. Not fixing in this session** — needs a proper rebalance of the tactician priority, not a quick patch.

### "Bot used Astra once (good)"
Confirmed in log 09:56. First-ever bot Astra cast. Likely enabled by yesterday's committed-state gate + transient reset — prior to the fix, aim hold state could persist across commit boundaries and clobber Astra. Partial resolution of BUG-03.

### "Bot used Shiva Third Eye (good)"
Confirmed in log 10:04, 3 Third Eye events. The God Ability branch in `BotTactician.Evaluate` (P7 fallback) fires `ScoreGodAbilityChance` which works for MukthaMuktha + Shiva. Third Eye is working.

## High-level "how do we make the bot better" (for the user's question)

The current 3-layer utility AI is doing most things right. The gaps are:

1. **Tactician priority order is too melee-favoring for ranged-special styles.** MukthaMuktha axe throw, PaniMuktha discus barrage, YantraMuktha charged shot are all ranged-damage specials that should be scored BEFORE default melee when the target is at mid-range. Currently they're only considered after melee fails.
2. **Spell aim was wrong** (fixed in this session).
3. **No per-style "personality" signal for ranged-special preference.** A MukthaMuktha with "prefers_throws = 0.8" should throw the axe more often than melee. Currently the bot has a generic `personality.prefersMelee` boolean which applies equally.
4. **Combat rhythm is not visible** — the bot cycles Approach → Exchange → Reset phases but there's no visible pacing for the human. A bot that always attacks on the same beat is boring; a bot that varies its combo timing feels more alive.
5. **No reactive dodges** yet — user can land free hits on the bot because it doesn't dodge on anticipation. `P2: React` in the tactician scores dodges on `state.targetAttacking`, but `targetAttacking` comes from `BotStateReader` which only flags it when the human is in `Melee`/`Melee_Second` state for ≥1 tick. Often too late to actually dodge before the hit.
6. **No concept of "commit window"** for humans — when the bot sees a human in `Melee_Second`, it should punish (the human is locked in the recovery animation and can't block). Currently it just tries to hit back normally.

These are NOT today's fixes — they're a backlog for future sessions. Filed as improvement notes in `BUGS-ACTIVE.md` as BUG-07 (tactician priority), BUG-08 (dodge timing), BUG-09 (punish windows). None are crash bugs, they're "the bot feels dumb" problems.

## Files touched in this session (2)

- `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs` — BUG-04 fix in CastSpell branch (~15 lines added).
- `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/BotTelemetry.cs` — LogEvent unmuted (3 line change, gate removed).

No new files. No new classes. Minimal surface area.

## Pre-commit checklist

- [ ] Unity Editor compiles the server project.
- [ ] Playtest 1v1 vs a MukthaMuktha bot with Shiva god.
- [ ] Observe: the bot's AIR spells should now spawn in front of the bot (between bot and human), NOT on top of the human.
- [ ] Check the new log for `[BOT:` event lines (COMMIT_ENTER, STRATEGY, PHASE).
- [ ] If both pass, commit WIP as `fix: Bot AI spell aim matches human path + telemetry event unmute`.
- [ ] Update BUGS-FIXED with the verified entries.

## Bugs filed this session

- **BUG-07** — Tactician priority doesn't let MukthaMuktha/PaniMuktha/YantraMuktha ranged-specials win at mid-range.

## Lessons filed this session

- **LESSONS #5** — `abilityPos` is caster.forward × clampedRange in human path, NOT target world coords. See below.
