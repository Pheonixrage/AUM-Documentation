---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
last_updated: 2026-04-11
append_only: true
---

# Lessons — "We tried X and it was wrong because Y"

**Append-only.** If a lesson turns out to be incomplete or wrong, add a new entry that references the old one. Never edit or delete old entries. The "why we didn't do X" knowledge is often more valuable than "what we did".

Each entry is short: rule, why, how to apply.

---

## #1 — `playerStats.range` IS the hit radius, not a range-for-aiming. Do NOT divide it.

**Date:** 2026-04-10
**Context:** Bot planted at max range and whiffed every swing. I guessed that `playerStats.range` was a "maximum effective range" that needed to be halved for a "plant in the sweet spot" distance, mirroring the old BT's `TargetWithinRange.cs` which used `localBot.playerStats.range / 2f`.

**What I tried:** Changed `GetEffectiveAttackRange` in `BotStateReader.cs` to return `playerStats.range / 2f` for melee.

**Why it was wrong:** `playerStats.range` is the **actual hit radius** used by `GetPlayersInRange()` in the melee hit check (see `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Player/Characters/Amuktha/Amuktha.cs:14` and `MukthaMuktha.cs:20`). It's not a "maximum approach distance". The old BT's `/2f` was a **planting heuristic** applied to movement, not to the hit check. When I halved the fire gate, the bot stopped trying to fire until the target was very close, and the plant threshold was also derived from the same value so it planted even closer — net result: bot stood ~2 m away from a target whose melee hit radius was 3.5 m, waiting for a condition that the tactician evaluated incorrectly. It was strictly worse than before.

**Correct fix:** Two separate values.
- **Fire gate** (`attackRange` in `BotStateReader`): FULL `playerStats.range`. This is the real hit radius; the fire check `distToTarget <= attackRange` must be true at the actual swing distance.
- **Plant distance** (in `BotExecutor.GetPhaseMovement`): `attackRange * 0.75f`. Strictly inside the fire zone so the plant threshold always overlaps the fire threshold. For Amuktha: plant at 2.6 m, fire at 3.5 m, overlap 0.9 m.

See checkpoint commit `c1470f9` for the current fix.

**How to apply:** Before changing any "range" constant in the bot code, **grep every use of `playerStats.range`** across `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/` to see what the game engine itself treats the value as. If it's used as a radius in `GetPlayersInRange`, it's a hit radius, don't halve it.

**Related session:** `sessions/2026-04-10-post-astra-haywire-diagnosis.md` (same day, different bug, same file edited).

---

## #2 — Whiff detection via `attackDone` is broken for all ranged/projectile styles. Do not re-enable the old pipeline as-is.

**Date:** 2026-04-10
**Context:** I had built a "whiff tracker" in `BotBrain.cs` that snapshotted focus/streak when an attack started and compared when the attack finished (via `player.character.attackDone`). After 2 consecutive whiffs it triggered "LOS recovery" — a perpendicular sidestep to clear a supposed line-of-sight block.

**What I tried:** Ship it as written.

**Why it was wrong:** `attackDone` is set to `true` **on projectile spawn**, not on projectile hit. For PaniMuktha (`PaniMuktha.OnAttackUpdate:84`), MantraMuktha, YantraMuktha, MukthaMuktha axe throw — `attackDone = true` the moment the projectile leaves the caster. But the whiff check runs immediately: streak hasn't changed (projectile in flight), focus hasn't changed → the checker concludes WHIFF. Every ranged swing registered as a false whiff. After two false whiffs the LOS recovery fired, the bot sidestepped perpendicular for 1.5 s, exited recovery, attacked again, false-whiffed again → infinite loop. Result: bot walked to the nearest arena corner and stood there.

**Correct fix:** Disabled the whiff pipeline entirely (checkpoint `c1470f9`). Left the fields and methods in place as dead code for future redesign, but removed the calls and the LOS recovery movement/camera branches. Bots now attack like humans — swing, resolve, re-evaluate next tick. If they miss, they miss.

**How to apply:** If you want to re-introduce hit detection for bots in the future, **don't use `attackDone`**. Options:
1. Hook into the actual damage application (in `PlayerBase.DoDamage` / `DoSpellDamage` / `DoAstraDamage`) and correlate back to the originating bot by source player.
2. Use a delayed check (1–2 seconds after swing start) that polls `player.focus.CurrentStreak` — by then the projectile has either landed or expired.
3. Query projectile entities in `EntityManager` and wait for their `Destroy` + hit-result callback.

Under no circumstances should "2 consecutive missed attacks → retreat" become a movement rule again. Bots should attack like humans.

**Related session:** `sessions/2026-04-10-post-astra-haywire-diagnosis.md`.

---

## #3 — Pre-attack line-of-sight raycast is unnecessary and does more harm than good.

**Date:** 2026-04-10
**Context:** I had added a `hasLineOfSight` raycast inside `BotBrain.OnUpdate` that ran one raycast per tactical eval from bot to target. The tactician used it to gate whether attacks were allowed.

**What I tried:** Ship it as a safety net against "bot attacks through a wall".

**Why it was wrong:** Human players don't LOS-check before swinging — they just swing and the game's collision/damage system resolves the rest. If a human tries to fire an arrow through a pillar, they fire, the arrow hits the pillar, it explodes, that's that. A bot that pre-checks LOS is strictly more conservative than a human and will refuse to fire in edge cases where a human would actually land the hit (e.g. partial occlusion, low-hanging geometry, hitbox overhang). Also: the raycast from `BotObstacleDetector.HasLineOfSight` is imperfect (uses a chest-height ray with player-collider filtering), so it returns false negatives.

**Correct fix:** Hardcoded `hasLOS = true` in the tactician call. Let the game resolve hits. The raycast method is still defined in `BotObstacleDetector.cs` as dead code for possible future use.

**How to apply:** If a bot appears to fire through walls in the future, that's a **damage system** bug, not a bot AI bug. Fix it in `Spell.cs`, `Projectile.cs`, or the melee `GetPlayersInRange` check — NOT by adding a pre-attack filter in the tactician.

---

## #9 — Third Eye vs Astra decision is keyed on the TARGET's HP, not the bot's. Low target HP → Third Eye. Healthy target → Astra.

**Date:** 2026-04-11
**Context:** User rule: "if the opponents have low health they can go for Third Eye otherwise it's wise to actually use Astra itself because it does more damage". And: "yea the third eye and astra thing is about the enemy's hp, not the bot's".

**The reasoning (user's words paraphrased):** Astra is the big-damage, long-cooldown ability. If the target is already close to dying, Astra's damage is wasted — melee or Third Eye + a chain finishes them for free. Save Astra for when the damage actually matters: against a healthy target where taking a big chunk of HP off them is meaningful.

**What I got wrong at first:** I kept thinking "when should the BOT use Third Eye" in terms of bot resources (focus budget, cooldown timers). User clarified: the decision variable is the OPPONENT's HP, not ours.

**The rule, fully:**
- `targetWPPercent < 0.45f` AND god == Shiva AND Third Eye available → **Third Eye** (it's "good enough" to finish)
- `targetWPPercent >= 0.45f` AND Astra ready → **Astra** (big damage, max value against a healthy target)
- Not Shiva (Brahma/Vishnu) → Astra as kill confirm (no Third Eye option)
- Third Eye on cooldown / already active → Astra fallback

**Implementation:** New helper `ShouldPreferThirdEyeOverAstra(ref state, player, r, canThirdEye)` in `BotTactician.cs`. Used in two places:
1. **P3 Execute** (targetLow or vulnerable): Call helper first. If true → fire Third Eye. If false → fall through to Astra kill confirm.
2. **P4 Astra Strategy** sub-branch (target < 45% HP): Same check. If prefer Third Eye → fire it. Otherwise → Astra kill confirm. The `>= 45% HP` proactive branch still fires Astra normally.

**What this does NOT change:**
- Kamikaze branch in P1 (HP critical, bot's own HP < 15%, aggression > 0.6) still fires Astra because the bot is dying anyway — last-chance damage matters more than "saving" an ability the bot might not live to use again.
- P7a proactive Third Eye (20% chance per eval) still fires as a general buff-before-melee cycle. That's independent of the kill-confirm logic.
- Brahma Shield and Vishnu don't have Third Eye → unaffected, they always use Astra for kill confirms.

**Open future tuning:** 0.45 HP threshold is a guess. If playtests show Third Eye firing too often (target at 40% is "low enough to not Astra") the threshold can drop to 0.35 or 0.30. Record observations in session files.

**Related:** `sessions/2026-04-11-aoe-check-and-thirdeye-value.md`, LESSONS #8 (save-for-astra threshold), `BotTactician.cs` P3/P4/helper.

---

## #10 — Spell AOE check must use the same geometry the human client uses — not a one-size-fits-all `dist ≤ spellDistance`.

**Date:** 2026-04-11
**Context:** User rule: "bots should only use spells when they have the opponents in the AOE of the spell they are planning to use it. There is a red indicator that spawns when players are in the AOE of their spells — maybe we can use that or at least some check before using the spell. Even if they miss it's fine, but they shouldn't use the spell when the opponents are not in the AOE at all."

**What I had:** `BotStateReader.CanSpellHitTarget` used a flat `dist(bot, target) ≤ spellDistance` check for every spell. This was wrong two ways at once:
1. **Too strict for Air.** Air has `maxRange = 10` (indicator can be placed up to 10m forward) + `spellDistance = 3` (sphere radius around indicator). Max effective reach = 13m. But the flat check rejected anything past `spellDistance = 3` even though Air can reach 13m. Result: bot refused to cast Air at targets between 3 and 13m.
2. **Approximately right for Earth/Ether/Fire/Water by accident.** Those spells have `maxRange = 0` so spawn at the caster, and their `spellDistance` IS effectively the reach around the caster. The flat check worked for these, but only because the indicator is centered on the caster — not by design.
3. **Wrong for Water.** Water has `detectionType = Box` (4.8m wide × spellDistance long), not Circle. A target 8m forward and 4m laterally from the bot would pass a distance check but fail the actual box detection.

**What the human client does** (from `CastManager.cs:318-390`, the `EnemyGlowOnDetection` system that produces the "red indicator" glow the user mentioned):

Per detection type, with `indicatorPos = castGameObject.transform.position`:
- **Circle** (Air/Earth/Ether): `dist(target, indicatorPos) ≤ spellDistance[god]`
- **Cone** (Fire): `dist(target, indicatorPos) ≤ spellDistance[god]` AND `TargetWithinAngle(player.playerObject, target, effectAngle[god])` — angle measured from player forward
- **Box** (Water): target inside a box starting at the player's position, extending `spellDistance[god]` forward, half-width 2.4 (CastManager `width = 4.8` / 2)

And `indicatorPos = caster.position + caster.forward × Clamp(localZ, minRange, maxRange)` where `localZ` is the indicator's forward offset — 0 for caster-centered spells, up to `maxRange` for Air.

**What I landed:** Rewrote `CanSpellHitTarget` to:
1. Compute `spawnPoint = botPos + flatDirToTarget × Clamp(dist, minR, maxR)` — the exact same formula `BotExecutor.CastSpell` uses when it fires the cast (so the check matches what actually happens).
2. Switch on `attrs.detectionType`:
   - **Circle**: `Vector3.Distance(spawnPoint, targetPos) ≤ spellRadius`
   - **Cone**: distance check AND angle cone check against `flatDir` (the bot's cast-forward at cast time, which equals the direction to target since bot rotates camera to face target before releasing)
   - **Box**: project `target - spawnPoint` onto forward/right axes, check `0 ≤ forwardDot ≤ spellRadius` AND `|rightDot| ≤ 2.4`
3. If the spell has no valid `spellDistance`, reject (unsafe to cast).

This means the bot's spell gate now uses the EXACT same math the human's red glow uses. If a human would see the red indicator light up on the opponent, the bot will attempt the cast. If not, the bot won't.

**Per-element verified behavior table** (attributes read from cast prefabs in `Assets/Resources/CastPrefabs/`):

| Element | detectionType | spellDistance | effectAngle | maxRange | Gate semantic |
|---|---|---|---|---|---|
| AIR | Circle | 3 | — | 10 | Sphere radius 3 around indicator (0-10m forward). Reach up to 13m from bot. |
| FIRE | Cone | 8.75 | 155 Brahma / 45 Vishnu | 0 | Cone at bot, length 8.75, wide (Brahma) or narrow (Vishnu). |
| WATER | Box | 10 | — | 0 | Box at bot, 10m long × 4.8m wide. |
| EARTH | Circle | 9 | — | 0 | Sphere radius 9 at bot. |
| ETHER | Circle | 9 | — | 0 | Sphere radius 9 at bot. |

**How to apply in future:** Never write a "catch-all" spell gate. If the game has per-element geometry (cone, box, moving projectile), mirror each one. Read the client's detection code as the source of truth — whatever the player sees as "in range" is what the bot should evaluate as hittable.

**Related:** LESSONS #7 (maxRange=0 semantics), `sessions/2026-04-11-aoe-check-and-thirdeye-value.md`.

---

## #8 — High `spellPreference` styles starve themselves of Astra focus. Saving for Astra must start at 2 segments, not 3.

**Date:** 2026-04-11
**Context:** User played a YantraMuktha bot for 2+ minutes. Focus peaked at 73 (2 segments), Astra never fired, Third Eye never fired. User compared: "why was MukthaMuktha able to use astra [earlier] and why isn't yantramuktha using the astra".

**What I found:**
1. YantraMuktha's `BotPersonality.spellPreference = 0.9f`. At the P5 Elemental Spell branch, `spellChance = 0.9 + (aggression - 0.5) * 0.2 ≈ 0.9`. So 90% of tactical evals with focus available → cast a spell.
2. Each AIR cast costs 1 focus segment (25 focus). Bot hit 2 segments, cast, dropped to 1, built to 2, cast, loop forever. Never reached 4 segments.
3. `shouldSaveForAstra` only triggered at `FocusState.Near` (3 segments = 75 focus). Since the bot never reached 3 segments in practice, the save-for-astra rule never fired. Dead code for YantraMuktha.
4. Third Eye (Shiva God Ability) never ran either. The tactician's `if (canMelee && r.isInAttackRange) return MeleeAttack` at P7 shadowed the god-ability branch entirely. Bot was always in melee range → always chose melee → god-ability branch was unreachable.

**Why MukthaMuktha worked but YantraMuktha didn't:** MukthaMuktha `spellPreference = 0.7f`, lower cast rate, plus axe melee builds focus faster per tick than ranged bow shots (melee hit = higher combo streak = more focus/hit). The two effects together let MukthaMuktha occasionally reach 4 segments and fire Astra. YantraMuktha couldn't.

**What I tried:** Two surgical fixes in one session, preserving all current behavior.

1. **`BotResourceEval.shouldSaveForAstra` threshold lowered** from 3 segments → 2 segments (`FocusState.Some`). When a bot hits 50 focus AND Astra cooldown is ready AND target HP > 40%, it STOPS casting spells and starts melee-only focus building. Once it reaches 100 focus, the P4 Astra branch fires and the bot casts Astra. After Astra's refractory cooldown, spell casting resumes normally.

2. **New P7a god-ability branch** before the default melee branch. `proactiveGodChance = 0.20f` per eval. Shiva → Third Eye if not already active and not hoarding for Astra. Brahma → Shield if a threat is imminent. Still leaves 80% of ticks for melee (which is the focus engine).

**Why it matters:** The "Astra must be earned" rule is a good design principle — Astra should be rare, Astra should be meaningful. But it only works if the bot can actually reach 4 segments. Before this fix, high-spellPreference styles were mathematically incapable of reaching Astra. Saving earlier is the only way to break the spell-starvation loop.

**How to apply in future:**
- When adding a new personality preset, verify the focus budget: `(attacksPerSecond × focusPerHit) > (spellsPerSecond × spellCost)` should hold at steady state, or the bot can never build toward Astra.
- When tuning `spellPreference`, think of it as a "spell vs save" dial. 0.9 means "spells always", which is only OK if focus generation per hit is VERY high.
- Third Eye and Brahma Shield belong in a tier BEFORE the default melee, not after. They're strategic buffs, not fallbacks.

**Related:** `sessions/2026-04-11-yantra-astra-starvation.md` (session file).

---

## #7 — `maxRange = 0` in a spell cast prefab means "spawn at caster", NOT "no maximum / unlimited".

**Date:** 2026-04-11
**Context:** After LESSON #5 (spell `abilityPos` = `caster.pos + forward × clampedRange`), I shipped a fix to `BotExecutor.ExecuteAction.CastSpell` that computed `castDist = Mathf.Clamp(distToTarget, minR, maxR)`. To handle "spells without a maximum", I added a guard `if (maxR > 0f) castDist = Mathf.Min(castDist, maxR);`. User playtested, reported "wtf it used ether and earth at my position" — the fix didn't work for those spells.

**What went wrong:** Four of five elementals have `maxRange: 0` in their cast prefab:

| Element | minRange | maxRange |
|---|---|---|
| AIR | 0 | 10 |
| FIRE | 0 | 0 |
| WATER | 0 | 0 |
| EARTH | 0 | 0 |
| ETHER | 0 | 0 |

I read `maxRange = 0` as "no max defined, treat as unlimited" — that is **wrong**. It is literal design intent: "the cast indicator stays at `localPosition = (0, 0.2, 0)` relative to the caster, i.e. on the caster's body". The human's `CastManager.Update` clamps `castGameObject.transform.localPosition.z` into `[minRange, maxRange]` each frame; with both values 0, the Z stays at 0, and `castPosition = caster.position`.

So for Fire/Water/Earth/Ether, the HUMAN's `abilityPos` is ALWAYS the caster's own position. Those spells are caster-centered: Fire is a cone from `transform.forward`, Water is a moving projectile from `transform.forward`, Earth is a sphere at `transform.position`, Ether is a sphere at `transform.position`. Only AIR uses `transform.position` as a forward-placed AOE (because maxRange > 0 lets the player drag the indicator forward).

My buggy guard `if (maxR > 0f) castDist = Mathf.Min(castDist, maxR);` did this:
```
maxR == 0 (Fire/Water/Earth/Ether):
  guard → false, skip
  castDist stays at state.distToTarget (the distance to the enemy)
  worldCastPoint = botPos + dir * distToTarget = enemy position
  → spell spawns on the enemy, wrong.
```

Reproducing EXACTLY the old broken behavior for those four spells. Air worked because `maxR == 10` passed the guard.

**Correct fix:** drop the guard. Use unconditional `Mathf.Clamp(dist, minR, maxR)`. When both are 0, clamp returns 0, and the spell spawns at the bot — matching the human.

```csharp
float minR = Mathf.Max(0f, el.spellCastAttributes.minRange);
float maxR = Mathf.Max(0f, el.spellCastAttributes.maxRange);
float castDist = Mathf.Clamp(state.distToTarget, minR, maxR);
Vector3 worldCastPoint = botPos + flatDirToTarget * castDist;
```

**How to apply:** Never interpret a numeric config value as "unset / unlimited" without reading the consumer code first. For a clamp target, 0 is a valid lower bound and always means "clamp to 0". If the game designer wanted "no max", the field would be `float.MaxValue` or a sentinel negative value. Every clamp should be unconditional unless the consumer documentation explicitly says otherwise.

**Related:** `LESSONS.md #5` (the parent lesson — abilityPos semantics). `sessions/2026-04-11-phase-1-spell-aim-fix.md` has the first broken attempt; this LESSON closes the loop.

**Bot behavior rule:** The bot must behave **identically** to the human. Any special case ("maxR > 0") that exists in the bot but not in the human's clamp is a bug waiting to bite. Match the human's arithmetic exactly, down to the handling of zeros and edge cases.

---

## #6 — There are FOUR bot log sources. Always name which one you checked before claiming telemetry is "broken".

**Date:** 2026-04-11
**Context:** I reported "telemetry is broken, LogEvent events aren't reaching the logs" in the 2026-04-11 Phase 1 session. User corrected me: "the telemetry fix was already there, check properly". They were showing a Unity Console screenshot with `[BOT:EditorPlayer2]` match summary lines clearly present.

**What I did wrong:** I used the phrase "telemetry is broken" as if it meant ONE thing. It doesn't. There are four distinct log sources (see `README.md` for the full table) and four distinct emitter paths in `BotTelemetry.cs`:
- `LogSnapshot` — unconditional `Debug.Log`, always reaches any log
- `LogMatchSummary` — unconditional `Debug.Log`, always reaches any log
- `LogEvent` — gated on `verboseConsole` (was `false` before my fix)
- `LogDecision` / `LogMovement` — gated on `verboseConsole` (still gated, too noisy to unmute)

The user could see `LogMatchSummary` + `LogSnapshot` lines (unconditional) and reasonably concluded "bot telemetry is working". I had grepped for `EVENT:` / `COMMIT_` / `STRATEGY` specifically and concluded "all telemetry is broken". Both were correct about different things; my framing was the problem.

**Why it was wrong:** "Telemetry" is a category, not a single thing. If I say "bot telemetry is broken" without specifying WHICH emitter path and WHICH log file, I'm making an unfalsifiable claim. The user can always point to one working part and say I'm wrong.

**Correct framing:** Whenever I claim a telemetry gap, I must answer three questions before the claim leaves my mouth:
1. **Which emitter path?** `LogSnapshot` / `LogEvent` / `LogDecision` / `LogMovement` / `LogMatchSummary`.
2. **Which log sink?** `DebugLogs/server_session_*.log` / `Logs/{guid}-S.log` / `~/Library/Logs/Unity/Editor.log` / Unity Console in-editor view.
3. **What gate is blocking it?** `trackedTags` filter / `verboseConsole` flag / `enabled` flag / `csvEnabled` flag / project-scope mismatch (Editor.log tied to another project).

Example of correct framing: "`BotTelemetry.LogEvent` is gated on `verboseConsole == true`, but `BotBrain.Start` sets it to `false`. So `COMMIT_ENTER` / `STRATEGY` / `PHASE` / `STALL_BREAK` events never reach `DebugLogs/server_session_*.log`. `LogSnapshot` and `LogMatchSummary` bypass the gate and DO reach the log."

**How to apply:** Before the next "telemetry is missing" diagnosis, write this checklist and fill it in:
- [ ] Which emitter method?
- [ ] Which log file (with full path)?
- [ ] Which gate (`trackedTags` / `verboseConsole` / `enabled` / other)?
- [ ] If Unity Editor Console is the source of truth, say so — it's not a file Claude can read from disk.

**Related session:** `sessions/2026-04-11-phase-1-spell-aim-fix.md` — session where I made the mistake.

---

## #5 — `abilityPos` for spells is `caster.pos + caster.forward × clampedRange`, NOT the target's world position.

**Date:** 2026-04-11
**Context:** User reported that bot-cast AOE spells (Air / Fire / Earth / Ether) were spawning at their player position instead of "around the bot". I diagnosed the bot was sending `input.abilityPos = new Vector2(targetPos.x, targetPos.z)` — literal target world coordinates. Initially I assumed that was a safe default since AOE spells only care about where the damage zone lands, and landing it on the target gives maximum coverage. That's the trap.

**What I could have tried:** Keep sending `targetPos` because "the AOE catches the target anyway".

**Why it would have been wrong:** `abilityPos` is NOT a semantic "where should the AOE land" field. It's a raw world-space spawn coordinate that the spell prefab uses as its transform position. For the HUMAN pipeline:

1. Client creates a `castGameObject` child of the caster with `localPosition = (0, 0.2, maxRange)`.
2. `AdjustCastPosition` clamps the local z between `minRange` and `maxRange` as the human drags to adjust cast distance.
3. World position = `caster.transform.position + caster.forward × clampedLocalZ`.
4. That world position is serialized as `abilityPos` and sent to the server.
5. Server: `ControllerBase.OnCastSpellUpdate` calls `SpellManager.InstantiateSelectedSpell(currentSpellIndex, player.abilityPos, player.pGameObject.transform)`.
6. `SpellManager` does `Instantiate(spellPrefab, spawnPos, _sourceTransform.rotation)` — the spell prefab is instantiated AT `abilityPos` with the caster's rotation.

Key implications:
- The spell prefab's transform.position is set to `abilityPos`. Any AOE visual, particle system, collider, or damage trigger child of the prefab inherits this world point as its origin.
- For directional spells (like a cone of Fire breathing forward from a single point), the spawn point must be in front of the caster or the spell visually appears "from a weird place".
- Spell VFX prefabs are authored assuming they originate from the forward cast indicator, not from an arbitrary world point at the target's feet.
- Game-design intent: a human casting Air/Fire/Earth/Ether is directing the spell forward, not pinpoint-targeting the enemy.

When the bot sent `targetPos` verbatim, the spell's damage zone still caught the target (because `Spell.GetPlayersInSpellRange` uses distance from the spell's own `transform.position`, wherever that is), but:
- The VFX appeared on top of the human instead of between the bot and the human.
- The bot's animation was "casting at empty space" — looked broken.
- The spell's directional design was silently broken — a Fire breath cone authored to come FROM the caster now spawned directly on the target, so the cone pointed backward.
- Inconsistent with the "bot plays like a human" rule.

**Correct behavior:** `abilityPos = bot.position + botToTargetDirection × Clamp(distToTarget, minRange, maxRange)`. This matches the human pipeline exactly: a point along the bot's forward cast line, distance clamped to the spell's design range. The AOE still catches the target whenever `distToTarget ≤ castDist` (which `CanSpellHitTarget` already verifies before the tactician picks the spell).

**How to apply:** When writing any new bot code that needs to set `abilityPos`, first answer: "what coordinate does the server's spell/ability spawn code interpret this as?" Look at the server-side consumer (`ControllerBase.OnCastSpellUpdate`, `SpellManager.InstantiateSelectedSpell`, or the per-style special handlers in `Characters/*.cs`). If it's passed as a spawn origin to `Instantiate`, the bot must compute the same world point the human's `castGameObject` would generate. If it's passed as a destination (teleport target, dash destination, axe landing point), literal target coords MAY be OK depending on the mechanic.

The three categories to watch for:
- **Spawn origin** (most elementals): compute `caster.pos + forward × clampedRange`.
- **Destination** (teleport, dash): literal target coords with arena bounds clamp.
- **Aim direction** (charged shot, discus barrage, Astras that don't use `abilityPos`): usually not through `abilityPos` at all — the spell reads `caster.forward` directly. Bot just needs to rotate camera, don't touch `abilityPos`.

**Related session:** `sessions/2026-04-11-phase-1-spell-aim-fix.md` — full positional math proof from logs `DebugLogs/server_session_2026-04-11_09-56-02_port6006.log` and `_10-04-04_port6006.log`.

---

## #4 — Committing a WIP snapshot is cheap and saves hours.

**Date:** 2026-04-10
**Context:** Before today's session I had ~1500 lines of uncommitted bot architecture refactor floating in the working tree across 76 files. Any crash, merge, or `git checkout` mistake would have lost all of it.

**What I should have done sooner:** Committed a WIP checkpoint at the end of EACH session, even if the code wasn't "done".

**How to apply:** At the end of any bot session where I've added or modified more than ~100 lines, commit a WIP snapshot. Use the message format `wip: Bot AI <scope>`. Record the commit hash in `DECISION-LOG.md` + `GIT-STATE.md`.
