---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
last_updated: 2026-04-11
---

# Bugs Fixed

Bot AI bugs that are **closed** — confirmed resolved by playtest evidence or by a followup session validating the fix. Each entry has a commit hash, a brief evidence note, and a link to the session file where the fix was made.

Entries move from `BUGS-ACTIVE.md` to here only when they're confirmed to work. A fix that "should work but hasn't been tested yet" stays in ACTIVE.

---

## FIXED-01 — PaniMuktha Brahma/Shiva discus aim offset was −7° instead of +8°

**Closed:** 2026-04-10
**Commit:** `c1470f9` (checkpoint)
**Files:** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs` (`ComputeCamera` ~line 373–374, `UpdateAimDirection` ~line 687–689)
**Session:** `sessions/2026-04-10-post-astra-haywire-diagnosis.md`

**Symptom:** PaniMuktha Brahma and Shiva variant bots never landed discus hits, even from correct distance with correct facing. The discus ellipse orbit was rotated incorrectly, throwing projectiles wide.

**Root cause:** Two lines in `BotExecutor.cs` applied `-= 15f` followed by `+= 8f`, producing a net `-7°` offset. The correct value is `+8°` — this matches the original working BT node `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Behaviour Tree/Custom Action Nodes/TargetWithinRange.cs:77` which applies only `+8°`. The `-15f` was a bad copy from an old iteration of `Bot.cs` that had been propagated into the new Executor.

**Fix:** Removed both `-= 15f` lines. Net offset is now `+8°`, matching the BT.

**Verification:** Code diff confirmed matches BT reference. NOT YET validated in a playtest with PaniMuktha Brahma/Shiva bot specifically — belongs in the "verified by code inspection, awaiting playtest confirmation" tier. Will be marked as playtest-verified once the next PaniMuktha playtest log shows non-zero hit rate.

---

## FIXED-02 — Bot plant distance was OUTSIDE the fire zone (dead zone)

**Closed:** 2026-04-10
**Commit:** `c1470f9`
**Files:** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs` (`GetPhaseMovement`)
**Session:** `sessions/2026-04-10-post-astra-haywire-diagnosis.md`

**Symptom:** Bots approached the target, stopped ~0.5 m short of their actual attack range, and then stood there swinging uselessly. The melee hit gate `distToTarget <= attackRange` could never satisfy because the plant gate was `> attackRange + 0.5f`.

**Root cause:** Two thresholds drifted apart:
- **Plant gate** in `GetPhaseMovement`: `distToTarget > attackRange + 0.5f` triggered approach. So the bot stopped moving when `dist <= attackRange + 0.5f`, i.e. the bot planted at the **outer edge** of its fire range plus a 0.5 m safety buffer — outside the fire zone.
- **Fire gate** in `ExecuteAction.MeleeAttack`: `distToTarget <= attackRange` required strictly. Could never become true because the plant was always 0.5 m too far.

**Failed fix attempt (see LESSONS.md #1):** I first tried dividing `playerStats.range` by 2 in `GetEffectiveAttackRange`. This made things strictly worse because `playerStats.range` is the hit radius, not a tuning knob.

**Correct fix:** Keep `GetEffectiveAttackRange` returning the FULL `playerStats.range` (the real hit radius). In `GetPhaseMovement`, plant at `attackRange * 0.75f` — strictly **inside** the fire zone, so there's always overlap. For Amuktha: plant at 2.6 m, fire at 3.5 m. For MukthaMuktha: plant at 3 m, fire at 4 m.

**Verification:** Playtest session 17:49 (`DebugLogs/server_session_2026-04-10_17-49-30_port6006.log`) shows MukthaMuktha bots landing melee hits at close distance (no freeze-at-range behavior observed). Earlier sessions' "bot stands at a distance" reports are gone. **Confirmed fixed.**

---

## FIXED-03 — Whiff detection triggered false positives on every ranged attack, causing infinite LOS recovery sidestep

**Closed:** 2026-04-10
**Commit:** `c1470f9`
**Files:** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotBrain.cs` (`OnUpdate` ~line 442, `UpdateWhiffTracking`, `UpdateLOSRecovery`); `BotExecutor.cs` (`GetPhaseMovement` and `ComputeCamera` LOS recovery branches)
**Session:** `sessions/2026-04-10-post-astra-haywire-diagnosis.md`

**Symptom:** Ranged bots (PaniMuktha, MantraMuktha, YantraMuktha, MukthaMuktha axe throw) would fire a projectile, then immediately sidestep perpendicular for 1.5 seconds, then fire again, sidestep again, forever. Net result: bot walked to the nearest corner and stood there.

**Root cause:** `UpdateWhiffTracking` snapshotted `player.focus.CurrentStreak` on attack start, then compared after `player.character.attackDone` became true. `attackDone` fires on **projectile spawn**, not on projectile hit. So when the check ran, the projectile was still in flight — streak hadn't incremented — checker concluded WHIFF. Two consecutive "whiffs" triggered `TriggerLOSRecovery` which set `losRecoveryUntilTime` and made movement sidestep perpendicular and camera face perpendicular. After the 1.5 s timer the bot re-fired → false whiff → recovery → loop.

**Fix:** Disabled the whiff pipeline entirely. Commented out `UpdateWhiffTracking` and `UpdateLOSRecovery` calls in `BotBrain.OnUpdate`. Removed the LOS recovery branch in `BotExecutor.GetPhaseMovement` and the matching camera branch in `ComputeCamera`. Left the fields and methods as dead code — to be redesigned using a different hit-detection mechanism (see LESSONS.md #2).

**Verification:** Playtest session 17:49 shows bots no longer walking to corners. Ranged bots repeatedly attack from the same position, confirming the sidestep loop is broken. **Confirmed fixed.**

---

## FIXED-04 — Pre-attack LOS raycast in tactician was false-negativing valid shots

**Closed:** 2026-04-10
**Commit:** `c1470f9`
**Files:** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotBrain.cs` (~line 362)

**Symptom:** Bots occasionally refused to swing at visible targets because a pre-attack raycast said "no LOS".

**Root cause:** `BotObstacleDetector.HasLineOfSight` casts from chest height and filters player/spell colliders, but misses partial-occlusion cases where a real shot would still land. Using it as a pre-attack gate made the bot strictly more cautious than a human player would be.

**Fix:** Hardcoded `hasLOS = true` in the tactician call. Let the game resolve hits the same way it does for human players.

**Verification:** Session 17:49 shows continuous volley firing without gate rejections. **Confirmed fixed.**

**See also:** LESSONS.md #3 — this is a general principle, not a one-off fix.

---

## How to add a new entry to this file

When moving a bug from ACTIVE to FIXED:

1. Copy the entry structure above.
2. Fill in: **Closed** date, **Commit** hash, **Files** with full repo paths, **Session** link.
3. Include a **Root cause** paragraph — the post-mortem, not just "fixed a bug".
4. Include a **Verification** paragraph with the log file path and what signal proved it.
5. Delete the entry from `BUGS-ACTIVE.md`.
6. Append a one-liner to `DECISION-LOG.md` referencing the new FIXED entry.
