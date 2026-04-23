---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
last_updated: 2026-04-11
---

# Active Bugs

Open bot AI bugs on the Legacy pipeline. When a bug is fixed, move the entry to `BUGS-FIXED.md` with commit hash + log evidence.

Severity codes: **CRIT** (makes bots unplayable) / **HIGH** (frequent / immersion-breaking) / **MED** (occasional) / **LOW** (cosmetic).

---

## BUG-01 — Post-player-Astra haywire drift  [HIGH]  [FIX IMPLEMENTED — needs playtest]

**Status (2026-04-11):** Fix implemented in the working tree on top of `c1470f9`, not yet committed, not yet playtest-verified. See `sessions/2026-04-11-phase-0-and-2-implementation.md`.

**Fix summary:**
- `BotExecutor.GetPhaseMovement` — ranged bots (state.isRanged == true) no longer retreat by turning their back. They plant and fire, closing to `attackRange * 0.75f` if out of range. Melee retreat unchanged.
- `BotBrain.OnUpdate` — committed-state gate added at the top. When `BotExecutor.IsFullyBlocked` returns true, the full tick pipeline is bypassed and `ExecutePassthrough(dt)` sends a minimal input. Transient state (`isAiming`, etc.) is reset on commit entry and exit.
- `BotExecutor` — new `ResetTransientState()` and `ExecutePassthrough(dt)` methods.

**How to verify:**
1. Playtest 1v1 vs a YantraMuktha or MantraMuktha bot.
2. Let the bot's HP drop via repeated hits (melee or Shiva Astra beam).
3. Observe: the bot should NOT drift away from you even when Strategy flips to Survive. It should stand and keep firing.
4. Check the session log for `[BOT:EVENT]` lines containing `COMMIT_ENTER` / `COMMIT_EXIT` when the bot uses its own long-committed abilities (spells, special, Astra). Those lines are the gate in action.

**If the fix works, move this entry to `BUGS-FIXED.md`.**

---



**Discovered:** 2026-04-10 playtest 17:49.
**Session file:** `sessions/2026-04-10-post-astra-haywire-diagnosis.md`
**Reproduction:** 1v1 vs YantraMuktha bot. Human casts Astra (e.g. Shiva beam). Bot enters a 5–10 second haywire state: drifts northwest, arrows miss every shot, camera facing oscillates. Recovers only when the human re-enters melee range.

**Log evidence** (`DebugLogs/server_session_2026-04-10_17-49-30_port6006.log`, lines ~4280–4500):
- Pre-Astra bot pos `(-6.91, -1.40)`, landing hits.
- Human starts Astra_Channel at `svrTick=7150`.
- Bot drifts: `(-10.91, -1.40)` → `(-11.32, -2.11)` → `(-12.23, 0.26)` → `(-12.41, 1.03)`.
- Volleys 40, 41, 42, 43, 44 all register as `MISS` — every arrow of every volley.
- Bot state cycles `Aiming` → `Idle` → `Aiming` repeatedly even after human's Astra_Cast ends at `svrTick=7300`.

**Root cause hypothesis (from code inspection, not yet proven):**
When human channels Astra, the bot's strategy layer flips to `Survive` (triggered by the "enemy channeling high-damage ability" heuristic in `BotStrategy.cs`). `BotExecutor.GetPhaseMovement` sets `IsRetreating=true` → returns `Vector2.up` (sprint forward while facing away). Simultaneously the tactician still picks `MeleeAttack` (ranged aim), which enters aim hold and overrides camera every frame to face the target. The two compete for `cameraRotation` — retreat sets facing-away, aim sets facing-target — and the arrows fire while the player's transform rotation lags both targets. Arrow forward ≠ actual target direction → 100% miss rate.

**Fix plan:** See session file "Phase 2 — Committed Action Gate" in `sessions/2026-04-10-post-astra-haywire-diagnosis.md`. Proposed approach:
1. Add `IsCommittedState` check at top of `BotBrain.OnUpdate` that bypasses tactical eval entirely during any committed FSM state (but this bug is about the human's Astra, not the bot's — needs variation).
2. Remove or soften the "enemy channeling Astra → retreat" heuristic in `BotStrategy.cs`. A ranged bot should keep firing, not retreat.
3. Ensure camera ownership is a single pipeline per tick: if aim is active, aim wins; retreat never overrides aim.

---

## BUG-02 — Bots almost never cast spells  [HIGH]

**Discovered:** 2026-04-10 playtest analysis across 7 logs.
**Reproduction:** Any 1v1 or FFA match with bots. Bots cast a total of **1 spell across 7 full playtests today**.

**Log evidence:** Counts per session:
```
11:55  0 bot spells cast
13:36  1 bot spells (spell cast but never spawned per [COMBAT:] log)
14:07  1 bot spells
15:06  0 bot spells
16:27  0 bot spells
17:44  0 bot spells
17:49  1 bot spells (the one actual [COMBAT: AIR] Spell spawned log of the day)
```

**Root cause hypothesis:**
- **Tactician gating** — `BotTactician.PickBestSpellSlot` checks focus cost, element cooldown, spell range (`minRange`/`maxRange`/`effectAngle`). If any gate fails, spell is dropped from consideration. Likely too strict.
- **`abilityPos` bug** — even when a spell fires, it uses literal target coords instead of the human-style `caster.position + forward × clamp(dist, minRange, maxRange)`, so the spawn is wrong and visually the bot doesn't appear to cast anything. See BUG-04.
- **Focus accumulation** — bots may not build focus fast enough to hit the ≥1 segment minimum. Need to log `player.focus.CurrentFocus` per tick per bot to verify.

**Fix plan:** Instrument first. Add `[BOT:CAST]` telemetry emitting `tried spell X slot Y, gate failed because Z` whenever the tactician rejects a candidate spell. Run a playtest, read the rejections.

---

## BUG-03 — Bots never cast Astra  [HIGH]

**Discovered:** 2026-04-10 playtest analysis.
**Reproduction:** Any match. Zero bot Astra events in all 7 sessions today.

**Root cause hypothesis:** Astra needs 4 focus segments. Bots need ~30+ uninterrupted seconds to build that up without being killed or resetting focus on each miss. Tactician may also not be scoring Astra highly enough to win the utility competition against cheaper actions.

**Fix plan:**
1. Add telemetry: log every time tactician evaluates Astra (score value + gate pass/fail).
2. Check if `BotResourceEval.hasAstraFocus` ever returns true for any bot mid-match.
3. If the problem is tactician scoring, rebalance the Astra utility curve in `BotTactician.PickBestAction`.

---

## BUG-04 — Spell `abilityPos` computed incorrectly for bots  [MED]  [FIX IMPLEMENTED — needs playtest]

**Status (2026-04-11):** Confirmed with positional math from 2026-04-11 playtest logs. Fix implemented in `BotExecutor.cs` CastSpell branch. Not committed yet, not playtest-verified. See `sessions/2026-04-11-phase-1-spell-aim-fix.md`.

**Evidence from today's logs:**
| Log | Bot pos | Human pos | Spell spawn | Spell-to-human |
|---|---|---|---|---|
| 09:56 spell #1 | (-9.43, 5.35) | (-10.02, 5.08) | (-10.02, 5.08) | 0.00 m |
| 10:04 spell #1 | (8.63, 15.42) | (9.27, 17.25) | (9.35, 17.21) | 0.09 m |
| 10:04 spell #2 | (-2.65, -13.41) | (-1.82, -16.27) | (-1.82, -16.27) | 0.00 m |

**Fix (implemented):** Replaced `spellAimTargetPos = new Vector2(targetPos.x, targetPos.z)` with a computation that mirrors the human's `castGameObject` world point:
```csharp
float castDist = Mathf.Clamp(state.distToTarget, minR, maxR);
Vector3 flatDir = (targetPos - botPos).WithY(0).normalized;
Vector3 worldCastPoint = botPos + flatDir * castDist;
spellAimTargetPos = new Vector2(worldCastPoint.x, worldCastPoint.z);
```

After fix, bot-cast spells should spawn at a point between the bot and the human, matching human-cast spells exactly.

**How to verify:** Playtest vs a MukthaMuktha bot. Let it cast an AIR or FIRE spell. Watch for the spell VFX to appear in FRONT of the bot, not on top of your player.

**See:** `LESSONS.md #5` for the full semantic explanation of `abilityPos`.

---

## BUG-05 — Obstacle detection brittle: stuck on corners / walks into pillars  [MED]

**Discovered:** 2026-04-10 during session diagnosis + code inspection.
**Reproduction:** Any arena with concave corners or pillars. Bot approaches target along a line, hits geometry, tries 5 hardcoded joystick alternatives (add-lateral / pure-lateral / opposite-lateral / diagonal-back / back), often returns `Vector2.zero` → freeze. Watchdog eventually kicks in but with delay.

**Evidence (code):** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/BotObstacleDetector.cs:148-174`. Single `CapsuleCast` in the desired direction. Binary hit / no-hit. 5 fallback alternatives hardcoded. No steering gradient, no peripheral awareness, no slide-along-wall behavior.

**Fix plan:** Phase 3 from session file. Multi-ray whisker steering (5 rays at -60°/-30°/0°/+30°/+60° around desired direction) + Craig Reynolds repel force. NotebookLM recommends this pattern from the "Modelling a Human-Like Bot in FPS" paper already loaded in the `BOT AI AUM` notebook.

---

## BUG-06 — `[BOT:` telemetry tag not in DebugLogTracker trackedTags  [LOW]  [FIX IMPLEMENTED — needs playtest]

**Status (2026-04-11):** Fix implemented in the working tree on top of `c1470f9`, not yet committed.
`[BOT:` added to `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Debug/DebugLogTracker.cs` line 30.
Move to `BUGS-FIXED.md` once a playtest session log contains `[BOT:...]` lines.

---

### Original entry (kept for history)

**Discovered:** 2026-04-10 when trying to read bot decisions from the session logs.
**Reproduction:** Any bot session. The `BotTelemetry.cs` class emits `[BOT:` prefixed events (STALL_BREAK, WATCHDOG, REJECTED, HIT, WHIFF, LOS_RECOVERY, etc.), but none of them reach the session log file because `[BOT:` is missing from `DebugLogTracker.trackedTags`.

**Evidence (log header):** Every session log's `Tracked Tags:` line enumerates `[MatchState], [TestMode], [GameManager], [PlayerManager], [BotManager], [ControllerBase], [Amuktha], ...` — but not `[BOT:`.

**Fix:** One-line addition to `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Debug/DebugLogTracker.cs`. Prerequisite for diagnosing BUG-02 and BUG-03.

**Priority:** Do this FIRST in the next session, before any other fix. It's the instrumentation the other fixes depend on.

---

## BUG-07 — Ranged-damage specials never win a scoring round (MukthaMuktha axe throw, PaniMuktha discus barrage, YantraMuktha charged shot)  [MED]

**Discovered:** 2026-04-11 from user report "bot is not using the special ability at all" after playing vs MukthaMuktha bot.
**Reproduction:** 1v1 vs any ranged-damage-special style (MukthaMuktha, PaniMuktha, YantraMuktha). Across both 2026-04-11 playtest logs: zero `Special_Anticipate` or `Special` bot states. User plays exclusively vs MukthaMuktha and never sees the bot throw its axe.

**Root cause (from code inspection of `BotTactician.Evaluate` ~line 260–314):**

```
P5: Spell windows — runs if good spell + focus
P6: Positioning — if !isInAttackRange:
      - Amuktha dash     → gap-close special
      - MantraMuktha tp  → gap-close special
      - all others       → Reposition
P7: Default (in range) → MeleeAttack (early return)
P7b: "default_special" → only runs if P7 melee gate failed
      (requires canSpecialDamage + hasSpecialFocus + random chance)
```

MukthaMuktha is **not** in the P6 gap-close list, so when out of range → `Reposition`. In range → P7 melee always wins → axe throw never scored. The `P7b: default_special` branch runs after P7's early return `if (canMelee && r.isInAttackRange) return Pick(MeleeAttack, ...)`, so it's only reached when melee cooldown is active. Which means axe throw only fires in the rare window where melee is recovering AND `Random.value < ScoreSpecialChance` (30 % max).

Same pattern breaks PaniMuktha discus barrage and YantraMuktha charged shot.

**Impact:** Styles lose their core combat identity. A MukthaMuktha that never throws its axe is just a clunky melee unit with a slow recovery.

**Fix plan (proposed, not implemented):**

1. Introduce a new priority slot `P5b: Ranged-special` that runs between spell windows (P5) and positioning (P6). Scores each style's own special as a ranged option when `distToTarget > attackRange * 0.5f && distToTarget < specialReach`.
2. Add the style-specific "ranged special sweet spot" distances (axe throw best at 5–15 m, discus barrage at 4–10 m, charged shot at 8–20 m).
3. Random chance at ~40 % per eval so it's not spammed but shows up regularly.
4. Tutorial override: block Astra + ranged specials so the user can learn mechanics.

**Priority:** Medium. The bot is playable without this, but it's what the user specifically noticed — the bot's identity per style is flat. Fix in Phase 5 (bot behavior polish) after the current Phase 1/2 stabilize in playtest.

