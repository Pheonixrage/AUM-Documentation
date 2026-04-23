---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
last_updated: 2026-04-11
---

# Git State — Checkpoint Reference

This file is a snapshot of the git state at the moment these docs were written. It lets a fresh session know **what code is committed vs what's still in the working tree**, which matters because reading a file on disk doesn't tell you whether that file is actually safe in git.

## Pinned commit (server — AUM-Unity-Server-Legacy, branch `legacy-working-oct6`)

**`fa64b74`** — `wip: Bot AI — spell AOE gate, Third Eye/Astra value rule, commit gate, telemetry`

Committed **2026-04-11 afternoon** on top of `c1470f9`. Contains all of the 2026-04-11 changes rolled into one WIP:

- **Phase 0** — `[BOT:` added to `DebugLogTracker.trackedTags`; `BotTelemetry.LogEvent` unmuted.
- **Phase 2** — committed-state gate in `BotBrain.OnUpdate` + `ResetTransientState()` + `ExecutePassthrough(dt)` in `BotExecutor`; ranged bots never retreat (Survive branch).
- **BUG-04** — `BotExecutor.CastSpell` computes `abilityPos = botPos + flatDir × Clamp(dist, minR, maxR)` matching the human path exactly; Fire/Water/Earth/Ether (maxR=0) spawn at caster, Air (maxR=10) spawns 0–10m forward.
- **BUG-10** — `BotStateReader.CanSpellHitTarget` rewritten to mirror the human client's per-detection-type red-indicator logic (Circle / Cone / Box).
- **BUG-03 improvement** — `BotResourceEval.shouldSaveForAstra` lowered from 3-segment to 2-segment threshold so high-spellPreference styles can actually reach Astra.
- **P7a proactive god ability** — new branch in `BotTactician` before default melee; 20% chance Third Eye (Shiva) / Shield (Brahma) per eval.
- **Third Eye / Astra value rule** — new `ShouldPreferThirdEyeOverAstra` helper. Keyed on TARGET's HP: < 45% → Third Eye finisher, ≥ 45% → Astra (big damage where it matters).

7 files, 358 insertions, 39 deletions.

### Previous checkpoint

**`c1470f9`** — `wip: Bot AI 3-layer Utility architecture + Apr 10 aim/plant fixes`

Committed **2026-04-10 evening**. Contains the full 3-layer architecture (Core/, Tactics/, Strategy/, Styles/, Personality/, Humanization/), legacy BT shim, Apr 10 fixes (PaniMuktha aim offset, plant distance, whiff detection disable), and Manager + Player hooks. 76 files, 7347 insertions, 170 deletions.

## Recent commit history (server, last 16)

```
fa64b74 wip: Bot AI — spell AOE gate, Third Eye/Astra value rule, commit gate, telemetry  ← THIS checkpoint
c1470f9 wip: Bot AI 3-layer Utility architecture + Apr 10 aim/plant fixes
af09e93 fix: Yantramuktha Brahma 3-arrow volley counts as single attack for focus
21cbd28 sync: CloudScript DEV rev 149, PROD rev 76 — per-avatar leaderboard via TitleData
3408d69 fix: Rewrite Shiva Astra — instant ticking beam, no focus from astras
7e6337c feat: Balance hot-update system via PlayFab TitleData
1da3108 fix: orchestrator — team modes start immediately, bot backfill for all partial matches
6d049af fix: 2v2 team collision in orchestrator — guard FFA-only check in _merge_player_data
4e66d41 fix: Server timing — targetFrameRate 200, realtimeSinceStartup, iteration caps
4423679 fix: Cast_Spell deadlock — auto-transition to Idle
5c8c2ce fix: Bot behavior tree state conflict — prevent simultaneous melee+spell
bc71f10 feat: Ether spell balance + bot mute fix
b271395 fix: Replace InvokeRepeating with Update() accumulators for Unity 6 compatibility
9d454df chore: Update Map_Hell scene (Unity 6 scene data refresh)
5dab322 fix: Karma selection no longer skipped for teammates in team games
345d8c1 fix: LAN idle timeout + bot slot re-keying + Windows build support
```

## Client branch (AUM-Unity-Staging-Legacy, branch `legacy-working-oct29`)

Latest: `5a44cf29e fix: iOS build support — DISABLESTEAMWORKS defines + build prep`

Client repo has uncommitted changes (AUMAuthConfig.asset, Initiate.unity, ProjectSettings) — **none of them related to bot AI**. The client has no bot code; bots are entirely server-side. Client branch state is noted here only so a fresh session isn't surprised by the `M` markers.

## Other AUM repos — for context only, not pinned

- **AUM-Headless** (V2 server, branch `AUM_MIND`) — latest `e6557c9 fix: Sync headless state renames + MantraMuktha aim-to-attack fixes`. Has its own separate bot architecture under `Assets/Scripts/Bots/Bot/{Core,Intelligence,Personality,Difficulty,Data}/`. **NOT related to this checkpoint.**
- **AUM-2.0 Production/Server** (branch `elemental-progression`) — runs the old BT. Not tracked here except as read-only reference.

## What's NOT in the checkpoint commit (intentional)

- `DebugLogs/*.log` (7 files from 2026-04-10) — runtime artifacts, large, not code.
- `ProjectSettings/MultiplayerManager.asset` — unrelated Unity 6 migration leftover.

If a future session finds either of these dirty, they can be ignored with respect to bot AI work.

## How to re-verify this state

```bash
cd /Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy
git log --oneline -n 2           # should show fa64b74, c1470f9
git status --short               # should be clean except DebugLogs + MultiplayerManager
```

If `fa64b74` is no longer at HEAD, **this doc is stale**. Check `DECISION-LOG.md` for newer commits and update this file.
