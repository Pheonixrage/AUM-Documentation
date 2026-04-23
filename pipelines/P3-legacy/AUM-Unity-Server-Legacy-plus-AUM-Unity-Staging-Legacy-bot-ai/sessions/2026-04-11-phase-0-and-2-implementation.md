---
date: 2026-04-11
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
goal: Implement Phase 0 (telemetry unblock) and Phase 2 (committed-state gate + ranged never-retreat)
status: code complete, NOT yet playtest-verified, NOT committed
related_bugs: BUG-01 (post-Astra haywire), BUG-06 ([BOT: tracked tag)
pinned_commit_before: c1470f9
pinned_commit_after: (pending — not committed yet)
---

# 2026-04-11 — Phase 0 + Phase 2 Implementation

## Goals

Implement the two highest-ROI items from the 5-phase fix plan drafted in `sessions/2026-04-10-post-astra-haywire-diagnosis.md`:

- **Phase 0** — Unblock bot telemetry by adding `[BOT:` to `DebugLogTracker.trackedTags`. Prerequisite for diagnosing BUG-02 and BUG-03 next session.
- **Phase 2** — Fix the post-player-Astra haywire (BUG-01) via two mechanisms:
  1. Committed-state gate at the top of `BotBrain.OnUpdate` so tactical eval doesn't run while the bot's own FSM is in a blocked state.
  2. "Ranged bots never retreat" — because on camera-ownership analysis (below) the retreat path was the real cause of the post-Astra drift, not the committed-state race.

## Root cause revision (correction to yesterday's hypothesis)

Yesterday's session file hypothesised an "enemy channeling Astra → Survive strategy → retreat" chain. That's partially wrong in an important way, which a full read of `BotStrategy.cs` revealed today.

`BotStrategy.ScoreSurvive` **does not** include any enemy-Astra signal. `Survive` only gets a high score when the **bot's own** HP drops below 30 %, with an additional massive boost below 15 %. So the "enemy is channeling Astra → retreat" step never runs directly.

What probably actually happens (needs [BOT: logs to confirm, but structurally plausible):
1. Human casts Shiva Astra — a ticking beam spell.
2. Beam damages the bot for several ticks while the human is in `Astra_Channel` + `Astra_Cast` states.
3. Bot's HP drops below 30 %.
4. On the next strategy re-eval (1.5–3 s cadence), `ScoreSurvive` wins.
5. `BotExecutor.GetPhaseMovement` sees `strategy == Survive` → sets `IsRetreating = true` → returns `Vector2.up`.
6. Camera race (see below) kicks in, bot drifts northwest, arrows miss.
7. User walks into melee range → bot's HP recovers or distance shrinks enough for strategy to re-evaluate → retreat clears → haywire ends.

## The camera ownership race — detailed trace

In `BotExecutor.Execute` each tick:

| Line | Action |
|---|---|
| 199–203 | `ComputeMovement` returns `Vector2.up` (retreat). `ComputeCamera` returns a small Slerp step from current rotation toward `-direction` (away from target). |
| 206 | `input.cameraRotation = cameraAngle;` — stores the "partially away" angle. |
| 208 | `input.JoystickAxis = EncodeJoystick(Vector2.up);` — forward in the (soon-to-be) new rotation. |
| 239–250 | If `isAiming` is true (aim hold, 200–500 ms) → `UpdateAimDirection` OVERWRITES `input.cameraRotation` with the target-facing angle. |

Server (`PlayerManager.cs:1165–1175`):
1. `transform.rotation = Quaternion.AngleAxis(input.cameraRotation, Vector3.up);` — snaps rotation.
2. `CharacterController.Move((transform.right * jx + transform.forward * jy).normalized * speed * dt);` — moves using the **new** rotation.

**On aim ticks** (say, 20–30 % of all ticks during a volley sequence):
- `isAiming = true` → cameraRotation overwritten to target. Server snaps rotation to target. Joystick `(0, 1)` → moves forward in new rotation → moves **toward** target. OK.

**On non-aim ticks** (the other 70–80 %):
- `isAiming = false` → line 206 stores the retreat lerp. Server snaps rotation to the lerp output (slightly more "away" than previous tick). Joystick `(0, 1)` → moves forward in the "slightly away" rotation → moves **partially away** from target.

Over ~30 non-aim ticks in a 2-second Astra window, the bot's physical position drifts ~3–5 m away from the target, and its rotation drifts noticeably toward "facing away". Each aim tick snaps rotation back and lets the bot fire — **but the bot has physically moved** northwest during the non-aim ticks, so the arrow's spawn point and target direction no longer match the trajectory the game's collision system was expecting. Most arrows miss.

That's the haywire. It's not an FSM desync; it's the `IsRetreating=true` + `Vector2.up` combination being toxic for any style that has an aim-hold cycle.

**Also:** Even if the bot isn't in aim hold, `ComputeCamera` reads `player.pGameObject.transform.rotation` as the Slerp start point. Because the server's snap is the full rotation (not a lerp), the "start point" on each tick already incorporates the retreat step from the previous tick. Retreat **compounds** tick-over-tick instead of lerping toward a fixed target. The bot physically turns away faster than the `lookLerpSpeed * 1.5f * dt` constant would suggest.

## The fix — ranged bots never retreat

Per NotebookLM's earlier response: "A retreating ranged bot is a dead ranged bot."

**[BotExecutor.cs:409–447](../../../../../AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs#L409-L447)** (`GetPhaseMovement`):

- New branch: if `state.isRanged && strategy == Survive`, the bot stays in place and keeps firing. If out of attack range it closes to `attackRange * 0.75f` (same plant threshold as the normal fight path). Never returns `Vector2.up` for ranged in Survive.
- Kamikaze branch (HP < 15 %): ranged bots plant and fire, don't "close and kamikaze".
- Melee retains the old turn-and-sprint-forward retreat because there's no aim-hold cycle to pollute.

## Phase 2 — Committed-state gate (cleaner infrastructure)

Even though it doesn't directly fix today's haywire (the bot isn't in a committed state during the human's Astra), the gate is still valuable:

1. It prevents the symmetric bug when the BOT itself casts a long-committed ability in the future.
2. It cleans up `isAiming`, `isSpellAiming`, `isSpecialAiming`, shield hold, and follow-up state on entry and exit, so no ghosts can persist.
3. It reduces wasted tick budget.

**[BotBrain.cs:238–289](../../../../../AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotBrain.cs#L238-L289)** — top of `OnUpdate`:

- New field `wasCommittedLastTick` tracks the previous tick's committed status.
- Each tick reads `currentFsmState = player.character.stateManager.GetState()` and checks `BotExecutor.IsFullyBlocked(currentFsmState)`.
- **Commit entry** (`!wasCommittedLastTick && isCommittedNow`): log `COMMIT_ENTER`, call `executor.ResetTransientState()`.
- **During commit**: call `executor.ExecutePassthrough(dt)` and `return` — no cooldown tick, no strategy eval, no tactics eval, no one-shot actions. Just send a minimal input so the server's `ResolveState` can transition the bot back to Idle when the committed animation finishes.
- **Commit exit** (`wasCommittedLastTick && !isCommittedNow`): log `COMMIT_EXIT`, call `ResetTransientState()` again (belt and braces), and force the next tactics eval timer to fire by setting `tacticsEvalTimer = tacticsEvalInterval`. Don't let a pre-commit decision carry over.

**[BotExecutor.cs:106–153](../../../../../AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs#L106-L153)** — two new methods:

- `ResetTransientState()`: drops `isAiming`, `aimHoldTimer`, `isSpellAiming`, `spellAimSlot`, `spellAimTimer`, `isSpecialAiming`, `specialAimTimer`, `holdingShield`, `shieldHoldTimer`, `QueuedFollowUp`, `FollowUpTimer`, `actionFired`.
- `ExecutePassthrough(float dt)`: minimal tick path — current facing, zero joystick, state resolution, send packet. Used while committed.

## Phase 0 — `[BOT:` tag in DebugLogTracker

**[DebugLogTracker.cs:30](../../../../../AUM-Unity-Server-Legacy/Assets/Scripts/Debug/DebugLogTracker.cs#L30)** — one-line addition to `trackedTags`:

```csharp
"[BotManager]",
"[BOT:",          // NEW — captures all BotTelemetry events
"[ControllerBase]",
```

`BotTelemetry.cs` emits events via `Debug.Log($"[BOT:{tag}] {message}")`, which Unity forwards to `HandleLog`. The filter uses `logString.Contains(tag)`, so `[BOT:` (with colon) matches `[BOT:DECISION]`, `[BOT:SNAPSHOT]`, `[BOT:EVENT]`, `[BOT:STALL_BREAK]`, `[BOT:COMMIT_ENTER]`, `[BOT:COMMIT_EXIT]`, etc.

Next playtest session's `DebugLogs/*.log` will finally contain bot telemetry, which unblocks diagnostics for:
- BUG-02 (bots almost never cast spells) — we'll see the tactician's `DECISION` reasons.
- BUG-03 (bots never cast Astra) — we'll see if `hasAstraFocus` ever becomes true and whether Astra is even considered.
- BUG-05 (obstacle detection) — we'll see `WATCHDOG` events.

## Files touched (3)

- `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Debug/DebugLogTracker.cs` — 1 line added to `trackedTags`
- `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotBrain.cs` — `wasCommittedLastTick` field + committed-state gate block in `OnUpdate`
- `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs` — `ResetTransientState()` + `ExecutePassthrough()` methods + ranged-never-retreat guard in `GetPhaseMovement`

No file was created. No new scripts were added. All changes are additive except the `GetPhaseMovement` Survive branch which got restructured.

## Pre-commit checklist

- [ ] Verify the code compiles in Unity Editor (open the server project, let Unity refresh).
- [ ] Run a quick 1v1 playtest vs a YantraMuktha bot, cast Shiva Astra on it, watch the log for `[BOT:COMMIT_ENTER]` / `[BOT:COMMIT_EXIT]` events (if the bot's HP actually drops into Astra_Channel or similar — won't trigger normally since the BOT doesn't enter committed states from being hit).
- [ ] Primary verification: the bot should no longer drift northwest while the user channels Astra. Volleys after Astra should land at ~pre-Astra rates.
- [ ] If OK, commit as `fix: Bot AI — ranged bots never retreat + committed-state gate + telemetry tag`.

## What this session does NOT fix

- **BUG-02** (bots barely cast spells). Phase 1 (Aim Solvers) is the real fix, not started yet.
- **BUG-03** (no bot Astras). Needs telemetry to diagnose. Phase 0 unblocks that diagnostic.
- **BUG-04** (spell `abilityPos` geometry). Same as BUG-02 — waits on Phase 1.
- **BUG-05** (obstacle detection). Phase 3, not started.

## Tomorrow's session should

1. Playtest the current changes. Read the log, verify `[BOT:` events are captured.
2. Confirm BUG-01 fix in practice. If bot still drifts during Astra, re-open the bug with new log evidence.
3. Start Phase 1 (Aim Solvers). This is where bug 2/3/4 get unblocked.

## Lessons filed this session

(none — nothing surprising happened; the plan from yesterday held up)
