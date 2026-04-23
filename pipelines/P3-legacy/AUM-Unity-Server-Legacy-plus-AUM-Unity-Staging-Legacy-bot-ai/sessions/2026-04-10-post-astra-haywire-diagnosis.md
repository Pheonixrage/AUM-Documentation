---
date: 2026-04-10
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
goal: Diagnose 3 bot AI bugs (spell offset, obstacle detection, post-Astra haywire) and commit a WIP checkpoint
status: diagnosis complete, plan drafted, no implementation started yet
related_bugs: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05, BUG-06
related_commits: c1470f9 (WIP checkpoint — architecture + aim/plant fixes)
related_logs: DebugLogs/server_session_2026-04-10_{11-55-36,13-36-13,14-07-54,15-06-09,16-27-10,17-44-01,17-49-30}_port6006.log
---

# 2026-04-10 — Post-Astra Haywire Diagnosis + 5-Phase Fix Plan

## Context

User reported three bot bugs after the 17:49 playtest:
1. Spell offset "using center at my player position" — wrong geometry for AOE spells.
2. Obstacle detection not working — bots get stuck.
3. Post-Astra haywire — after the human casts Astra, the bot goes confused until the human walks back into melee range.

Also queried the `BOT AI AUM` NotebookLM notebook for guidance grounded in research sources (Dave Mark utility AI, Craig Reynolds steering, Unreal GAS TargetData, "Modelling a Human-Like Bot in FPS" paper, For Honor GDC talks).

## Today's playtests — evidence summary

Seven session logs in `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/DebugLogs/`:

| Log | Styles tested | Focus HITs | Focus MISSes | Bot spells cast | Bot Astras | Crashes |
|---|---|---|---|---|---|---|
| 11:55:36 | Amuktha, YantraMuktha | 8 | 12 | 0 | 0 | 0 |
| 13:36:13 | Amuktha | 42 | 14 | 1 | 0 | 0 |
| 14:07:54 | Amuktha, MantraMuktha | 38 | 41 | 1 | 0 | 0 |
| 15:06:09 | Amuktha, PaniMuktha | 10 | 16 | 0 | 0 | 0 |
| 16:27:10 | Amuktha, MukthaMuktha | 1 | 0 | 0 | 0 | 0 |
| 17:44:01 | Amuktha, YantraMuktha | 34 | 6 | 0 | 0 | 0 |
| 17:49:30 | Amuktha, YantraMuktha | 73 | 58 | 1 | 0 | 0 |

Aggregate observations:
- **Zero runtime exceptions** across all 7 sessions. (The "1 exception" grep hit in each log is from the `Tracked Tags:` header listing "Exception" as a keyword, not actual errors.)
- **Bots almost never cast spells** — 3 spell cast events across 7 sessions. Only 1 actual `[COMBAT: AIR] Spell spawned` log, in the 17:49 session.
- **Zero bot Astras** across all sessions.
- Hit rate varies wildly — best 75 % (Amuktha melee, 13:36), worst 48 % (MantraMuktha mix, 14:07). YantraMuktha volleys in 17:49 = 32 hit / 47 miss = 40 %.

## Bug 1 — Spell offset wrong

**Investigation path:** Traced `abilityPos` from bot to server spawn.

- Bot sends `input.abilityPos = new Vector2(targetPos.x, targetPos.z)` in `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs:506` (spell cast) and `:521` (Astra).
- Server stores it verbatim: `player.abilityPos = new Vector3(input.abilityPos.x, 0, input.abilityPos.y)` in `PlayerManager.cs:904-1128`.
- Spell spawns at `player.abilityPos` directly: `ControllerBase.OnCastSpellUpdate:417 → SpellManager.InstantiateSelectedSpell(..., player.abilityPos, ...)`. The prefab `Instantiate(spellObj, spawnPos, _sourceTransform.rotation)` uses `spawnPos = abilityPos` as the spell's center.

**Contrast with human path:** `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/CastManager.cs:269-277`. Human's `abilityPos` comes from `currentSpell.castGameObject.transform.position`, where `castGameObject` is a **child of the caster** at `localPosition = (0, 0.2, maxRange)`, clamped to `[minRange, maxRange]` per spell config. So the human's `abilityPos` is always `caster.position + caster.forward × some_distance_in_that_range`. Never the target's position directly.

**Conclusion:** Bot and human use two different geometric rules. When they match (target is between minRange and maxRange along the bot's facing), bot spells happen to land. When the target is outside the spell's design range, the bot sends an out-of-range position and the spell spawns somewhere the mechanic wasn't built for. Mispositioned damage zones, broken VFX, miss.

**Fix:** Introduce `IAimSolver` interface with per-element solvers (see plan below). Filed as **BUG-04** in `BUGS-ACTIVE.md`.

## Bug 2 — Obstacle detection broken

**Investigation path:** Read `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/BotObstacleDetector.cs` end to end.

- `AdjustMovement` is a binary single `CapsuleCast` in the desired direction. If blocked → tries 5 hardcoded joystick alternatives (`add-lateral`, `pure-lateral`, `opposite-lateral`, `diagonal-back`, `back`). If none clear → returns `Vector2.zero` (freeze).
- No peripheral awareness (no side rays). No steering gradient (binary pass/fail). No slide-along-wall behavior.
- `IsDirectionClear` uses `LOOKAHEAD = 3.0f` and ignores player colliders. That's fine, but the single-ray limitation means a pillar directly on the approach line traps the bot.

**Failure mode:** Bot approaches enemy past a pillar. CapsuleCast hits pillar forward → pick `pure-lateral` → next tick the lateral vector also hits the pillar (slightly different angle) → pick `opposite-lateral` → back-and-forth jitter. Hysteresis field `_cachedStrafeDir` exists but only kicks in after a direction is chosen, so the first few ticks after each collision still flip.

**Fix:** Multi-ray whiskers (5 rays at −60°/−30°/0°/+30°/+60°) with Craig Reynolds repel force. NotebookLM confirms this is the recommended pattern from the "Modelling a Human-Like Bot in FPS" paper in the notebook's sources. Filed as **BUG-05**.

## Bug 3 — Post-Astra haywire

**Investigation path:** Cross-referenced `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/DebugLogs/server_session_2026-04-10_17-49-30_port6006.log` lines ~4270–4500 with `BotExecutor.ComputeCamera`, `GetPhaseMovement`, and `BotStrategy.cs`.

**What the log shows:**

```
17:51:30.093  [DESYNC-SVR] svrTick=7150  Hfhfhru        state=Astra_Channel  focus=0    pos=(-9.24,-12.15)
17:51:30.093  [DESYNC-SVR] svrTick=7150  EditorPlayer2  state=Aiming         focus=15   pos=(-6.91,-1.40)
17:51:30.924  [DESYNC-SVR] svrTick=7200  Hfhfhru        state=Astra_Channel  focus=10
17:51:30.924  [DESYNC-SVR] svrTick=7200  EditorPlayer2  state=Aiming         focus=16   pos=(-10.91,-1.40)  ← drifted 4m west
17:51:31.757  [DESYNC-SVR] svrTick=7250  Hfhfhru        state=Astra_Channel  focus=20
17:51:31.757  [DESYNC-SVR] svrTick=7250  EditorPlayer2  state=Melee          focus=17   pos=(-10.91,-1.40)
17:51:32.595  [DESYNC-SVR] svrTick=7300  Hfhfhru        state=Astra_Cast     focus=20
17:51:32.595  [DESYNC-SVR] svrTick=7300  EditorPlayer2  state=Aiming         focus=17   pos=(-10.91,-1.40)
17:51:33.429  [DESYNC-SVR] svrTick=7350  Hfhfhru        state=Idle           focus=20
17:51:33.429  [DESYNC-SVR] svrTick=7350  EditorPlayer2  state=Idle           focus=17   ← human Astra done
17:51:34.262  [DESYNC-SVR] svrTick=7400  EditorPlayer2  state=Aiming                    pos=(-10.91,-1.40)
17:51:35.928  [DESYNC-SVR] svrTick=7500  EditorPlayer2  state=Aiming                    pos=(-11.32,-2.11)  ← drifting NW
17:51:36.762  [DESYNC-SVR] svrTick=7550  EditorPlayer2  state=Idle                      pos=(-12.23, 0.26)
17:51:37.595  [DESYNC-SVR] svrTick=7600  EditorPlayer2  state=Aiming                    pos=(-12.41, 1.03)

Volleys during this window: #38, #39, #40, #41, #42, #43, #44 — every arrow of every volley reported as MISS.
```

**Root cause hypothesis (from code, not proven in a debugger):**

1. Human enters `Astra_Channel` at svrTick 7150.
2. Bot's strategy layer likely flips to `Survive` due to a "enemy channeling high-damage ability" heuristic in `BotStrategy.cs`. (Need to confirm by instrumentation — no `[BOT:` logs reach the session file; see BUG-06.)
3. `BotExecutor.GetPhaseMovement` sees `strategy == Survive` and the bot's own HP is above 15 %, so it sets `IsRetreating = true` and returns `Vector2.up` (sprint forward).
4. `ComputeCamera` sees `IsRetreating = true` and lerps camera to face **away** from the target (`lookLerpSpeed * 1.5f * dt`).
5. Simultaneously, the tactician is still picking `MeleeAttack` (ranged aim hold). The aim hold override in `BotExecutor.UpdateAimDirection` runs every tick inside the aim block and tries to point the camera at the target.
6. The two signals compete for `cameraRotation`. Retreat wins when movement runs first that tick; aim wins when the aim block runs. Result: camera oscillates, and because `player.pGameObject.transform.rotation` is lerped it lags behind the oscillation.
7. Arrows fire when aim hold timer expires. But the player's actual rotation at fire time is somewhere between "facing away" and "facing target" — arrow direction ≠ target direction → 100 % miss.
8. Bot drifts northwest because retreat movement is always `Vector2.up` = forward in the bot's current facing, and facing is lerping toward "away from target".
9. When human walks back into melee range, distance shrinks below the Survive threshold → `IsRetreating` flips back to false → camera stops oscillating → normal firing resumes. That's why the user sees it "snap back" when they approach.

**Fix:** Two changes, documented in the plan below. Filed as **BUG-01**.

## The 5-Phase Fix Plan (from NotebookLM response + code inspection)

Grounded in the NotebookLM response saved at `research/notebooklm-2026-04-10-response.md`. High-level: keep the 3-layer architecture (NotebookLM explicitly warns against GOAP/HTN for combat bots on small teams — "AI development hell"), refine within it.

### Phase 0 — Instrument first (BUG-06, one-line fix, BLOCKS all diagnostics)

Add `[BOT:` to `trackedTags` in `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Debug/DebugLogTracker.cs`. Without this, `BotTelemetry.cs` emits events that never reach the session log file, so I'm blind during playtest analysis. Do this BEFORE any other fix.

### Phase 1 — Aim Solvers (BUG-04, ~100 lines)

- New interface `IAimSolver` at `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Aim/IAimSolver.cs`.
- `HumanEquivalentAimSolver`: returns `self.pos + flatDirToTarget × Clamp(distToTarget, minRange, maxRange)`. Applies to all spells by default.
- `CenterOfMassAimSolver`: for radial AOE in team / FFA, iteratively drops the furthest enemy until all remaining fit inside `spellDistance`.
- `DirectionalAimSolver`: for cones/walls if any exist.
- `SelfAimSolver`: for self-centered defensive spells.
- Build a `Dictionary<Elementals, IAimSolver>` in `BotTactician` constructor. Wire in from `BotExecutor.ExecuteAction` at lines 506 and 521.

### Phase 2 — Committed Action Gate (BUG-01, ~40 lines, HIGHEST ROI)

The post-Astra haywire is two overlapping problems:
- The bot re-plans every tick during the human's Astra channel — it shouldn't. Planning during a scripted event produces noise.
- Camera ownership fights between retreat and aim — exactly one pipeline owns camera per tick.

Fix:
1. In `BotBrain.OnUpdate`, at the top, check `IsCommittedState(currentState)`. If true, skip tactical eval entirely and call `executor.ExecutePassthrough(dt)`. `IsCommittedState` returns true for `Astra_Channel`, `Astra_Anticipate`, `Astra_Cast`, `Cast_Spell`, `Spell_Anticipate`, `Special`, `Special_Anticipate`, `Stun`, `Death`, `Victory`. (Note: this gates on the BOT's own state, which doesn't actually address the haywire. It's preparation for future fixes where the bot uses these abilities.)
2. The actual haywire fix: **remove or de-escalate the "enemy is channeling Astra → retreat" heuristic** in `BotStrategy.cs`. A ranged bot should keep pressure on, not retreat. Only flip to `Survive` if the bot's OWN HP is critical, not because of the enemy's channel.
3. Resolve the camera ownership race: if `isAiming` or `isSpellAiming` or `isSpecialAiming` is true, the aim block wins camera unconditionally. Move the retreat camera branch to run ONLY when no aim is active. Put it behind an explicit `if (!IsMidAim) { ... }` guard.
4. When a committed state clears, reset transient bot state: `isAiming`, `isSpellAiming`, `isSpecialAiming`, stall counter, combat-rhythm phase.

### Phase 3 — Steering Obstacle Avoidance (BUG-05, larger rewrite)

Replace `BotObstacleDetector.AdjustMovement` with 5 whisker rays (−60°, −30°, 0°, +30°, +60°) using Craig Reynolds repel force blending. Each ray contributes a weighted repel vector; the blended result is re-projected onto the joystick axis. Keep the existing hysteresis for concave dead-ends.

NotebookLM recommends this pattern and cites the "Modelling a Human-Like Bot in FPS" paper and Reynolds' 1999 steering behaviors. See `research/notebooklm-2026-04-10-response.md`.

### Phase 4 — Hit probability gate (accuracy polish)

Before firing a ranged shot, do a SphereCast along the aim direction and check the first hit. If it's not the target's PlayerBase, don't fire — reposition. This is NOT target leading (which user explicitly forbade). It's a "don't waste arrows on walls" gate.

Would have prevented the 25 wasted arrows in volleys 40–44 during the post-Astra haywire window.

### Phase 5 — Telemetry loop

- Phase 0 already adds `[BOT:` to tracked tags.
- Every `IAimSolver.Solve()` call logs `spell, target, computed abilityPos, direction`.
- Every tactician eval logs top 3 candidates + their scores.
- Every committed-state enter/exit logs the transition.

## Execution order for the next session

1. **Phase 0 first** — 1 line, unlocks everything else.
2. **Phase 2 next** — highest ROI, fixes today's reported bug, ~40 lines.
3. **Phase 1** — larger, but sets up the pattern we'll use forever.
4. Playtest. Diagnose with `[BOT:` logs now visible.
5. **Phase 3** — steering whiskers.
6. **Phase 4** — hit-probability polish.

**Do NOT start code changes in this session.** This session ends at the doc + commit checkpoint. Next session starts from Phase 0.

## Commits in this session

- `c1470f9` — `wip: Bot AI 3-layer Utility architecture + Apr 10 aim/plant fixes`. Committed as a safety checkpoint at the end of the session. Contains the full in-progress architecture plus today's PaniMuktha aim offset, plant distance, whiff disable, LOS raycast removal fixes. 76 files changed, 7347 insertions, 170 deletions.

## Bugs closed in this session

- **FIXED-01** PaniMuktha discus `+8°` offset restored.
- **FIXED-02** Plant distance moved inside fire zone.
- **FIXED-03** Whiff-triggered LOS recovery disabled.
- **FIXED-04** Pre-attack LOS raycast removed.

## Bugs filed in this session

- **BUG-01** post-Astra haywire drift (HIGH).
- **BUG-02** bots almost never cast spells (HIGH).
- **BUG-03** bots never cast Astra (HIGH).
- **BUG-04** spell `abilityPos` computed incorrectly (MED, blocks BUG-02 verification).
- **BUG-05** obstacle detection brittle (MED).
- **BUG-06** `[BOT:` telemetry tag missing from DebugLogTracker (LOW, but blocks diagnostics).

## Lessons filed

- **LESSON #1** `playerStats.range` IS the hit radius, don't divide it.
- **LESSON #2** `attackDone` fires on projectile spawn, not hit — don't use it for whiff detection.
- **LESSON #3** Pre-attack LOS raycast is harmful — let the game resolve hits.
- **LESSON #4** Commit WIP snapshots at end of every session.

## References

- NotebookLM response — `research/notebooklm-2026-04-10-response.md`
- Checkpoint commit — `c1470f9` (AUM-Unity-Server-Legacy, branch `legacy-working-oct6`)
- Session log for haywire diagnosis — `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/DebugLogs/server_session_2026-04-10_17-49-30_port6006.log`
