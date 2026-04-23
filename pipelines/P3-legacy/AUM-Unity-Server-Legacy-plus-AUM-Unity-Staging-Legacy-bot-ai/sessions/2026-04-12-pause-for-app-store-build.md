---
date: 2026-04-12
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
goal: Pause bot AI work for App Store build. Resume instructions below.
status: paused — all code committed locally at fa64b74, no uncommitted changes
pinned_commit: fa64b74 (AUM-Unity-Server-Legacy, branch legacy-working-oct6)
next_action: user will provide movement/spacing direction using framework below, then resume coding
---

# 2026-04-12 — Pause for App Store Build

## State at pause

All bot AI code committed locally at `fa64b74` on branch `legacy-working-oct6`. Working tree clean (only untracked DebugLogs + MultiplayerManager.asset). NOT pushed to remote.

User is making an App Store build from the client repo (AUM-Unity-Staging-Legacy, branch legacy-working-oct29). Bot code lives on the server repo only — no client changes from the bot work.

## What's been done (Apr 10–11, two commits)

```
fa64b74 wip: Bot AI — spell AOE gate, Third Eye/Astra value rule, commit gate, telemetry
c1470f9 wip: Bot AI 3-layer Utility architecture + Apr 10 aim/plant fixes
```

### Fixes landed and working
1. PaniMuktha Brahma/Shiva discus aim offset (+8° matching original BT)
2. Plant distance = attackRange × 0.75 (inside the fire zone)
3. Whiff detection + LOS sidestep recovery disabled (false positives on all projectile styles)
4. Pre-attack LOS raycast removed (humans don't LOS-check)
5. Spell abilityPos matches human path: Fire/Water/Earth/Ether spawn at caster (maxRange=0), Air spawns 0-10m forward
6. CanSpellHitTarget rewritten with per-detection-type geometry (Circle/Cone/Box) mirroring the human's red-indicator glow logic
7. Committed-state gate in BotBrain.OnUpdate (skips eval during Cast_Spell, Astra, Special, Stun, Death, Victory)
8. Ranged bots never retreat (Survive strategy = stand and fire, not turn-and-sprint)
9. shouldSaveForAstra lowered from 3 segments → 2 segments (high-spellPreference styles can now reach Astra)
10. Proactive P7a god ability branch (20% chance Third Eye / Brahma Shield before default melee)
11. Third Eye / Astra value rule keyed on TARGET's HP (< 45% → Third Eye finisher, ≥ 45% → Astra)
12. [BOT: telemetry tag in DebugLogTracker + LogEvent unmuted

### Known open bugs
- **BUG-07** — Tactician never lets MukthaMuktha/PaniMuktha/YantraMuktha ranged specials win a round (axe throw, discus barrage, charged shot)
- **BUG-08 candidate** — YantraMuktha bow shot failing FSM execution gate frequently (147 WATCHDOG in one log)
- **THE BIG GAP** — Movement is a flat "approach or plant" with no spacing, no retreat-reengage rhythm, no comfort zone, no phase-driven behavior. All 7 personality rhythm fields are defined but not wired into the movement executor. This is what the user noticed: "no back and forth, no retreating, doesn't feel like a real player."

## What the user needs to provide when we resume

The movement layer needs explicit direction. I asked the user for input using one of 5 frameworks:

### Framework 1 — Describe specific moments
Give 2–3 beats of play you want the bot to handle. Not categories — actual moments.
> "When the human swings and misses, I want the bot to step in and punish."
> "After the bot lands a hit, it should back away 2–3m for 1 second."

### Framework 2 — Spacing dance per style
For each of the 5 styles, one-sentence ideal range + one-sentence rhythm.
> "MantraMuktha: Stay at 8–12m. Approach to 10m, cast, back off to 12m, wait, reapproach."
> "Amuktha: Stay at 3m. Close fast, 2-hit combo, dash back 5m, pause, re-engage."

### Framework 3 — Point at real gameplay
A recorded match where a human played the style the way you want the bot to play. I extract patterns from their position + action logs.

### Framework 4 — Define phases in your own words
What each combat rhythm phase should DO movement-wise:
> "Approach = walk toward target diagonally, 70% speed."
> "Exchange = attack 1–3 times, no movement."
> "Disengage = walk backward 4m at 80% speed."
> "Reset = hold at distance, face target, wait 1–2s."

### Framework 5 — Forbidden behaviors
What the bot should NEVER do:
> "Never stand still in melee range without swinging."
> "Never approach in a straight line at full speed."
> "Never spend more than 3 seconds without moving unless aiming."

**My recommendation: Framework 4 + Framework 5 together.** Most behavior per line of code, directly addresses the "attack, back off, reengage" ask.

## How to resume after App Store build

When context is cleared and we start fresh:

1. Say: **"Resume bot AI work from the pause. Check Obsidian."**
2. I will read:
   - `~/.claude/projects/.../memory/bot-ai-legacy.md` (auto-memory pointer)
   - `pipelines/P3-legacy/AUM-Unity-Server-Legacy-plus-AUM-Unity-Staging-Legacy-bot-ai/README.md`
   - `CURRENT-STATE.md`
   - `GIT-STATE.md` (pinned at fa64b74)
   - `LESSONS.md` (10 entries — the things I got wrong and must not repeat)
   - This session file
3. I will verify `git log --oneline -n 1` shows `fa64b74` in the server repo.
4. I will ask you: "Which framework for movement direction? Or paste your design."
5. We start coding the movement layer.

## Obsidian docs status

All session files, LESSONS (#1–#10), DECISION-LOG, BUGS-ACTIVE, BUGS-FIXED, GIT-STATE, CURRENT-STATE, README (with log-file locations table) are up to date as of this pause. 4 session files written during Apr 10–11:
- `2026-04-10-post-astra-haywire-diagnosis.md` (original 5-phase plan)
- `2026-04-11-phase-0-and-2-implementation.md` (committed-state gate + ranged never retreat)
- `2026-04-11-phase-1-spell-aim-fix.md` (abilityPos + telemetry + YantraMuktha starvation)
- `2026-04-11-aoe-check-and-thirdeye-value.md` (detection-type AOE check + Third Eye/Astra value)

Plus this file: `2026-04-12-pause-for-app-store-build.md`

## NotebookLM

The `BOT AI AUM` notebook (id `b099a943-5254-4cb9-bddc-955c80ddf7c0`) has research sources on utility AI, steering behaviors, Craig Reynolds, For Honor bots, FightingICE, Dark Souls AI. The full 2026-04-10 response is saved at `research/notebooklm-2026-04-10-response.md`. Use it for the movement/steering work.
