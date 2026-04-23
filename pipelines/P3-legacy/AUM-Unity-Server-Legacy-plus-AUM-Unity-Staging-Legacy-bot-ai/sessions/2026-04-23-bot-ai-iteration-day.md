---
date: 2026-04-23
scope: AUM-Unity-Server-Legacy
goal: Iterate bot AI quality via user playtests + generate human-derived presets for all 5 styles
status: complete — 16 presets generated, 7 commits, option 2 (live telemetry) handoff ready
pinned_commit_start: fa64b74
pinned_commit_end: 30a0183
---

# 2026-04-23 — Full-Day Bot AI Iteration

## Context

User played 22+ matches across 5 fighting styles × 3 god variations, reporting bot behavior issues after each playtest. Each report led to a targeted investigation → fix → re-test cycle.

By end of day: 16 human-derived presets covering full style/god matrix, 7 major bot-AI bug fixes committed, watchdog / action-cooldown / movement / Astra-aim all repaired.

## Playtest summary

Match sequence (16 matches with preset data):

| # | Time | Human | Bot | Human result | User feedback |
|---|------|-------|-----|--------------|---------------|
| 1 | 05:51 | Amuktha/Brahma | MukthaMuktha/Brahma | WIN | First preset pipeline validation |
| 2 | 10:09 | Amuktha/Brahma | MantraMuktha/Brahma | WIN | — |
| 3 | 10:28 | Amuktha/Shiva | MukthaMuktha/Vishnu | WIN | — |
| 4 | 10:32 | Amuktha/Vishnu | Amuktha/Vishnu | WIN | — |
| 5 | 10:44 | MukthaMuktha/Vishnu | Amuktha/Vishnu | WIN | — |
| 6 | 10:47 | MukthaMuktha/Shiva | YantraMuktha/Vishnu | WIN | "contested" |
| 7 | 10:51 | MukthaMuktha/Brahma | PaniMuktha/Shiva | WIN | — |
| 8 | 11:07 | MukthaMuktha/Shiva | PaniMuktha/Brahma | LOSS | "bot stuck and desynced" → post-action cooldown fix |
| 9 | 11:32 | MukthaMuktha/Shiva | Amuktha/Vishnu | LOSS | "stuck as if waiting to decide" → smooth-movement fix |
| 10 | 11:41 | MukthaMuktha/Shiva | Amuktha/Shiva | LOSS (bot WON) | "much better" ✓ confirmed fix working |
| 11 | 11:58 | MantraMuktha/Vishnu | YantraMuktha/Vishnu | WIN | "bot froze at low HP" → ranged-approach fix |
| 12 | 12:04 | MantraMuktha/Shiva | MukthaMuktha/Vishnu | WIN | — |
| 13 | 12:11 | MantraMuktha/Brahma | YantraMuktha/Brahma | LOSS (bot won 90% HP) | "bot invisible but playing" — visual desync |
| 14 | 12:18 | YantraMuktha/Brahma | YantraMuktha/Vishnu | WIN | — |
| 15 | 12:21 | YantraMuktha/Shiva | PaniMuktha/Vishnu | WIN | "bot cast earth without me in range" → spell-target-tracking fix |
| 16 | 12:25 | YantraMuktha/Vishnu | YantraMuktha/Shiva | WIN | — |
| 17 | 12:29 | PaniMuktha/Shiva | MantraMuktha/Brahma | LOSS (bot won 63% HP) | — |
| 18 | 12:35 | PaniMuktha/Brahma | YantraMuktha/Vishnu | WIN | — |
| 19 | 12:38 | PaniMuktha/Vishnu | MukthaMuktha/Shiva | WIN | — |
| 20 | 13:15 | PaniMuktha/Vishnu | YantraMuktha/Shiva | — | "Maheshwara astra beam didn't track me" → astra-aim fix |

## Bugs found + fixes shipped (in order)

### 1. Watchdog blacklist loop (commit `2c54855`)

**Symptom:** bot spent ~40% of match time unable to fire any action.

**Evidence:** In match 8 (11:07), watchdog fired 84× `failed_MeleeAttack_blacklisted`, 32× `zero_input_2s`, 9× `failed_CastSpell` in a single 157s match. Bot ran in circles between attempts.

**Root cause:** `actionSucceeded` flag was `false` whenever the action didn't fire THIS tick. But animation in progress, distance gating, and tick-level debounce all correctly prevent re-firing — yet were counted as "failure". 3 failures in 50ms of ticks → action blacklisted for 3 seconds.

**Fix:**
- `actionSucceeded` now also true when bot is mid-animation (`IsFullyBlocked(currentState)`)
- Failure counter only increments on TACTICAL EVAL ticks (every 6-10 ticks), not every tick
- MIN_FAILED_EVALS 3 → 5, BLACKLIST_DURATION 3s → 1s
- `zero_input_2s` only counts when bot SHOULD be moving (target out of attack range + not blocked by animation)

### 2. Post-action cooldown missing (commits `be25952`, `d7b722a`)

**Symptom:** bot stuck in Shield_Block for 7.2 seconds continuous, Aiming for 2.4 seconds.

**Evidence:** Match 8 position trace — bot planted at `(6.84, 9.63)` for 300 ticks cycling Aiming → Shield → Aiming → Shield without moving.

**Root cause:** tactician re-evaluates every 100-170ms. When it picks the same action (MeleeAttack, Shield) while the previous animation is still playing, bot re-enters the animation state before it visually completes. Net effect: bot looks frozen.

**Fix:** per-action post-fire cooldown. After an action fires, same action locked out for:
- 500ms for MeleeAttack/CastSpell/SpecialAbility/Dodge
- 2000ms for ElementalShield/GodAbility (Brahma Shield was worst offender)

When tactician picks a cooldown'd action, BotBrain forces Reposition → bot must move/strafe for 500ms before re-attacking.

Compile fix `d7b722a`: used correct enum names `CastSpell0/1/2/3` and `ElementalShield`/`GodAbility` (was `CastSpell` / `Shield` which don't exist).

### 3. Jerky movement during approach (commit `bd19f8b`)

**Symptom:** "keeps getting stuck as if waiting to make a decision"

**Evidence:** Match 9 bot trace — lurched 5-7m forward in 800ms windows, then frozen for 800ms, over and over.

**Root cause:** duty-cycle logic rolled "move vs plant" every 400ms window. For Amuktha exchangeSpeedMult=0.1, 90% of windows were plant → bot moves 40ms full-speed then plants 360ms. Joystick byte oscillates sharp-on/off.

**Fix:** Out-of-range always closes (duty cycle ignored). Duty cycle only applies to Reset phase (where chilling at comfort distance is the intent).

User confirmed: "this is much better now" ✓

### 4. Ranged bot freezes at low HP (commit `6cf227e`)

**Symptom:** "bot stopped moving once it was on low health... only when i entered it started attacking again"

**Evidence:** Match 11 — YantraMuktha bot at 6% HP planted at `(0.3, 6.9)` for 11+ seconds while user was 25-30m away (out of bow range).

**Root cause:** kamikaze branch returned `Vector2.zero` for ALL ranged bots regardless of distance. Melee bots got `Vector2.up` (sprint-in), ranged bots got freeze.

**Fix:** ranged bot at HP critical + out of range → `GetApproachMovement` (humanized approach with hesitation to prevent overshoot). Ranged bot at HP critical + in range → plant and fire.

### 5. Spell casts at stale target position (commit `6cf227e`)

**Symptom:** "earth spells etc were always used without even me in range"

**Evidence:** Bot picks spell slot at eval time (CanSpellHitTarget check passes), enters Spell_Aiming for 250-500ms, then fires at cached abilityPos. User had moved 1-3m during the aim.

**Fix:** recompute spellAimTargetPos EVERY TICK during the aim-hold using current target position (clamped by spell's minRange/maxRange). Bot visibly aims at moving target; spell commits at whatever position target is at cast time.

### 6. Shiva Maheshwara astra fires in fixed direction (commit `30a0183`)

**Symptom:** "bot uses the shivas astra... its just staying still, but it should aim the beam at the player"

**Evidence:** Match 20 — YantraMuktha/Shiva bot in Astra_Cast for ~5 seconds, camera locked at 0° regardless of user's movement from 5m→14m.

**Root cause:** `BotExecutor.Execute` gated BOTH movement AND camera computation on `!IsFullyBlocked(currentState)`. Astra_Cast is blocked (correctly — body can't walk). Camera was collateral damage — stayed at default 0 → beam fired at world +Z.

**Fix:** split movement/camera gating.
- Astra_Cast/Channel/Anticipate: movement=0 but camera STILL tracks target via ComputeCamera
- Other blocked states (Stun, Cast_Spell, Water_Pushback): preserve current facing, no tracking
- Non-blocked: normal compute both

## Reviewer-driven rejection of bad fixes

Three proposed fixes were sent through sub-agent (combat-reviewer) review. Two were rejected as counterproductive:

### Rejected: Astra hoarding rule

Proposed: new "if losing badly, save focus for Astra" gate. Reviewer correctly noted `BotResourceEval.shouldSaveForAstra` **already does this exactly** — focus ≥ 50 segments, target HP > 40%, astra ready. Adding a second gate would risk stall conditions. **Deleted before implementation.**

### Rejected: Cancel spell if target leaves AOE during aim

Proposed: during Spell_Aiming, re-check `CanSpellHitTarget` and cancel cast if target moved out. Reviewer flagged three problems:
1. `MarkActionFired` already burned the 500ms cooldown — canceling wastes it
2. "Aim then don't fire" looks like a visible bug to the player
3. The aim-hold design is INTENTIONAL — bot commits to a prediction, same risk as humans

Better fix: track target during aim (what I ended up implementing — Bug #5 above). **Cancel approach never implemented.**

### Approved with refinement: Low-HP ranged bot fix

Reviewer approved `GetApproachMovement` use, noted built-in hesitation prevents "bot sprints into melee at 6% HP and dies instantly". Implemented as approved.

## Presets generated (16 total, complete matrix)

```
Amuktha_Brahma_v2     Amuktha_Shiva_v1      Amuktha_Vishnu_v1
MukthaMuktha_Brahma   MukthaMuktha_Shiva    MukthaMuktha_Vishnu
MantraMuktha_Brahma   MantraMuktha_Shiva    MantraMuktha_Vishnu
PaniMuktha_Brahma     PaniMuktha_Shiva      PaniMuktha_Vishnu
YantraMuktha_Brahma   YantraMuktha_Shiva    YantraMuktha_Vishnu
```

**Data quality:** user dominated 8 of 9 style-preset matches. Presets encode "skilled player winning against weak bots" patterns. Will re-derive from live PvP telemetry when Option 2 is built.

## Deferred / not fixed this session

### Bug A: client-visual desync (bot invisible but playing server-side)
User reported in matches 13 + match 19. Logs show zero rollback events, zero position teleports. Likely client-side Unity rendering/animator stall. Needs live observation.

### Bug C: stuck behind obstacles, doesn't reposition
Known BUG-05 in `BUGS-ACTIVE.md`. `BotObstacleDetector` is too simple (single CapsuleCast + 5 hardcoded fallbacks). Proper fix requires multi-ray whisker steering or nav mesh. Out of scope today.

### Bug E: bot casts spells/astra without enough focus
Investigated — no definitive evidence. `CheckFocusSegments` gate exists for spells, `hasAstraFocus` exists for astra. Snapshots showing "Astra_Channel focus=0" are post-consumption readings (100 spent → 0, same tick as state transition). Possible but unconfirmed race condition; deferred until reproducible case.

## Commits (7 this session)

```
30a0183  fix(bot): Shiva astra beam tracks target during cast
6cf227e  fix(bot): ranged low-HP approach + stale spell target tracking
bd19f8b  fix(bot): smooth movement — out-of-range bot always closes, no duty cycle
d7b722a  fix(bot): use correct BotAction enum names in cooldown logic
be25952  fix(bot): post-action cooldown prevents long-animation state sticks
f288f1a  data: 3 Amuktha presets (Brahma/Shiva/Vishnu) from 2026-04-23 matches
2c54855  fix(bot): rewrite watchdog — action-in-progress no longer counts as failure
```

Plus 6cf227e added 9 MantraMuktha/YantraMuktha/PaniMuktha presets in one commit.

## Next session

User decided to move to **Option 2: live telemetry system** — see handoff doc at
`sessions/2026-04-23-option-2-live-telemetry-handoff.md`.
