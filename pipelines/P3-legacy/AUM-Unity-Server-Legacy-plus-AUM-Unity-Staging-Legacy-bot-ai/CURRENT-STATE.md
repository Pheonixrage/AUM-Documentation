---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
last_updated: 2026-04-23
pinned_commit: 30a0183
uncommitted_on_top: no — all changes committed locally, NOT pushed
---

# Current State

As of commit `30a0183`. Seven 2026-04-23 commits on top of `fa64b74` (checkpoint before this session).

## Summary

**16 human-derived presets deployed** covering all 5 fighting styles × 3 god variations. Bot AI has had 6 major bug-fix commits this session — watchdog, post-action cooldown, movement jitter, low-HP freeze, spell target tracking, astra beam aim.

## Architecture in place

Same 3-layer Utility AI + BT shim as before. Gameplay Analysis Pipeline still active:

```
PLAY → LOG (HBR) → ANALYZE (Python) → CONVERT (Python) → LOAD (BotBrain) → TEST → ITERATE
```

**Currently:** pipeline runs locally in Editor, manually triggered.
**Next stage:** live production ingestion (see `sessions/2026-04-23-option-2-live-telemetry-handoff.md`).

## What works (verified in 2026-04-23 playtests)

- Bot spawning + AVATARSYNC pipeline across all 5 styles
- Melee combat: Amuktha, MukthaMuktha bots land hits consistently
- Ranged combat: YantraMuktha, MantraMuktha, PaniMuktha bots fire arrows/discs/staff shots
- Preset loading via `BotBrain.TryLoadPreset` — auto-picks `{Style}_{God}_*.json`, falls back to `{Style}_*.json`
- Strategy layer adapts: bots cycled through Punish, Zone, BuildResource, Execute, Pressure, Survive in single matches
- Combat rhythm working: Approach → Engage → Exchange → Disengage → Reset
- Phase-driven movement smooth (no more duty-cycle jitter during approach)
- Watchdog quiet (zero blacklist events in last 10 matches)
- Shiva Maheshwara astra beam now tracks target during cast
- Spells track moving target during aim-hold (no longer cast at stale position)
- Ranged bots approach to firing range even at critical HP (no more freeze)

## Preset inventory (16 files in ServerData/BotPresets/)

```
Amuktha_Brahma_v1      Amuktha_Brahma_v2      Amuktha_Shiva_v1      Amuktha_Vishnu_v1
MukthaMuktha_Brahma    MukthaMuktha_Shiva     MukthaMuktha_Vishnu
MantraMuktha_Brahma    MantraMuktha_Shiva     MantraMuktha_Vishnu
PaniMuktha_Brahma      PaniMuktha_Shiva       PaniMuktha_Vishnu
YantraMuktha_Brahma    YantraMuktha_Shiva     YantraMuktha_Vishnu
```

All derived from user playtests; all players dominated matches, so presets encode "expert vs weak bot" patterns. Option 2 (live telemetry) will regenerate these from real PvP data.

## What was fixed this session (7 commits)

See `sessions/2026-04-23-bot-ai-iteration-day.md` for full detail.

| Commit | Problem | Fix |
|--------|---------|-----|
| `2c54855` | Watchdog blacklisting 84×/match | Fixed failure detection (mid-animation ≠ failure); MIN_FAILED_EVALS 3→5, BLACKLIST 3s→1s |
| `be25952` | Shield_Block stuck 7s, Aiming 2.4s | Per-action post-fire cooldown (500ms/2s Shield) |
| `d7b722a` | Compile error from `be25952` | Correct BotAction enum names |
| `bd19f8b` | Jerky chase movement (lurch 5-7m per 800ms) | Out-of-range ignores duty cycle; duty cycle only during Reset phase |
| `6cf227e` | Ranged bot frozen at low HP + spells cast at stale target | Kamikaze approach for ranged; recompute spellAimTargetPos every tick during aim |
| `30a0183` | Shiva Maheshwara beam fires in fixed direction during cast | Split movement/camera gating: camera tracks target during Astra states |

## What's still broken (deferred to future sessions)

1. **Visual desync** (`BUG-08` new) — user reported "bot invisible but playing" in matches 13 + 19. Logs show zero rollbacks, zero teleports. Likely client-side Unity rendering/animator issue. Needs live observation to debug.
2. **Stuck behind obstacles** (`BUG-05`) — BotObstacleDetector too simple (single CapsuleCast + 5 hardcoded fallbacks). Requires nav mesh or multi-ray whiskers.
3. **Possible focus constraint bypass** (`BUG-09` new) — user reported bots casting without enough focus. Code gates exist (CheckFocusSegments + hasAstraFocus); snapshots showing "focus=0 in Astra state" are likely post-consumption. No provable bypass, but flagged for reproduction.
4. **Bot doesn't dodge incoming attacks reactively** — known from prior sessions, not addressed this session.
5. **Bot rarely uses Specials** — BUG-07 from vault, deferred again.
6. **Astras still low frequency** — existing `shouldSaveForAstra` is correct per combat-reviewer agent review, but bots rarely reach 100 focus in the first place. Deeper tactician work needed.

## Next session path

User committed to **Option 2: live telemetry** over continued preset iteration. See
`sessions/2026-04-23-option-2-live-telemetry-handoff.md` for the full plan.

## Environment

- Unity 6 (6000.0.60f1) on server
- Playtest setup: Editor play mode, port 6006
- Logs rotating to `DebugLogs/server_session_YYYY-MM-DD_HH-MM-SS_port6006.log`
- HBR `#if UNITY_EDITOR` — still Editor-only; unlocking for production is Phase 1 of Option 2

## Paths

- Server: `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy`
- Client: `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy`
- Branch: `legacy-working-oct6` (server) / `legacy-working-oct29` (client)
- Pipeline tools: `tools/aum_gameplay_analyzer.py`, `tools/profile_to_config.py`
- Presets: `ServerData/BotPresets/`
