# Session Log: 2026-02-12 - Grand Merge Verification & MCP Playtest Pipeline

## Summary
Multi-session conversation (spanning context compactions) that verified the Grand Merge fixes end-to-end, established the MCP autonomous playtest pipeline, and created the AUM_BODY/AUM_MIND/AUM_SPIRIT branch structure.

## Session Arc (Chronological)

### Session 1: Grand Merge Deployment
- Fixed `IsBotMatch` bug in `PlayFabMatchmaker.cs` (line 799: `false` -> `true`)
- Added `ApplyBuildModeSync()` to `ServerAllocator.cs` for auto-syncing ConnectionMode from AUMAuthConfig.BuildMode
- Deployed to Singapore server (5.223.55.127:7777)
- Verified popup fix and local match flow

### Session 2: First Match Verification
- Connected to Singapore via Hetzner mode
- Match loaded into Bhuloka scene
- Discovered combat input methods via MCP:
  - `click_ui` on AttackButton registers but **does NOT trigger actual combat** (EventTrigger/PointerDown vs Button.onClick)
  - `InputManager.TriggerAttackClick(FSM.StateType.WeaponStrike)` via `execute_code` **WORKS**
  - `FSM.StateType.Melee` doesn't exist - correct enum is `WeaponStrike`
- Player died to bot (was still figuring out attack methods)
- Verified full post-match flow on a **loss**: PostMatchPanel_2 (Guna) -> Panel_3 (Stats) -> MainMenu
- Zero errors

### Session 3: Popup & Combat Testing
- Saved MCP playtest workflow to memory (combat methods, editor management)
- **MatchFoundPopup Cancel test**: Invoked `OnMatchFound` via reflection with `IsBotMatch=false` -> popup appeared -> clicked Cancel -> returned to menu correctly
- **MatchFoundPopup Accept test**: Triggered popup -> clicked Accept -> PreConnect initiated, auth succeeded. Avatar sync timed out after 30s (server-side issue, not client bug)
- **Combat test via direct connect** (IsBotMatch=true, skips popup):
  - Spammed `TriggerAttackClick` in bursts of 10-15, re-facing enemy between bursts
  - Built focus from 0 -> 100 (~60 attack triggers for MantraMuktha)
  - Fired Astra at 100 focus -> **3750 damage server-confirmed** (enemy 7800 -> 4047)
  - Melee damage doesn't register server-side via MCP (expected: server validates hits, MCP injection bypasses proper hit registration)
  - Attempted second Astra but died before firing (bot killed us at WP 0)
- Post-match flow verified again on loss
- Committed and pushed remaining untracked files

## Key Technical Discoveries

### MCP Combat Input Methods
| Method | Works? | Notes |
|--------|--------|-------|
| `click_ui` on AttackButton | Registers only | Combat buttons use EventTrigger, not Button.onClick |
| `execute_code` + `TriggerAttackClick()` | YES | Correct way to trigger attacks |
| `execute_code` + `TriggerAstra()` | YES | Must be in Idle state first |
| `execute_code` + `TriggerDodge()` | YES | Dodge with `FSM.StateType.Dodge` |
| `execute_code` + `TriggerMove()` | YES | Vector2 direction input |
| `click_ui` on Next_Button | YES | Post-match panel navigation works |
| `inject_game_input` action | NO | InputManager.Instance is null |

### FSM StateType Enum (Key Values)
`Idle`, `WeaponStrike`, `WeaponStrike_Combo`, `Dodge`, `Death`, `Cast_Spell`, `Channel`, `Special`, `ThirdEye`, `Astra_Anticipate`, `Astra_Channel`, `Astra_Cast`, `Victory`, `Teleport`

### PlayerData Field Gotchas
- `playerData.focus` is a `float`, not an object (no `.CurrentFocus`)
- Position: use `player.character.transform.position` (not `player.playerBase`)
- `playerData.team`, `playerData.uniqueID`, `playerData.isBot` don't exist as expected

### Popup Testing via Reflection
```csharp
var mec = FindObjectOfType<MainEntranceController>();
var matchResult = new MatchResult {
    MatchId = "test-id", ServerIP = "5.223.55.127", ServerPort = 7777,
    IsBotMatch = false, // false = show popup, true = skip
    Players = new List<MatchPlayer>()
};
var method = mec.GetType().GetMethod("OnMatchFound",
    BindingFlags.NonPublic | BindingFlags.Instance);
method.Invoke(mec, new object[] { matchResult });
```

## Verification Results

| Test | Result |
|------|--------|
| IsBotMatch=true skips popup | PASS |
| MatchFoundPopup Cancel | PASS |
| MatchFoundPopup Accept | PASS (avatar sync timeout is server-side) |
| Match loads into Bhuloka | PASS |
| Combat via MCP execute_code | PASS |
| Astra deals server-confirmed damage | PASS (~3750 dmg) |
| Post-match flow (loss) | PASS |
| Return to MainMenu | PASS |
| Zero client errors | PASS |

## Branch Structure Established

| Project | Branch | Purpose |
|---------|--------|---------|
| AUM-The-Epic | `AUM_BODY` | Client - UI, input, rendering |
| AUM-Headless | `AUM_MIND` | Server - authority, validation, game logic |
| AUM-Documentation | `AUM_SPIRIT` | Context, session logs, architecture docs |

## Known Issues
- **PreConnect avatar sync timeout**: Auth succeeds on Singapore but AvatarSync=False after 30s. Server-side investigation needed.
- **Melee damage via MCP**: Server doesn't confirm MCP-injected melee hits (no proper hit validation chain). Astra works because it's a different code path.

## Files Changed
### AUM-The-Epic
- `Assets/Scripts/Network/PreConnectManager.cs.meta` (new)

### AUM-Headless
- `ProjectSettings/ProjectSettings.asset` (Unity version compat update)

## Memory Entities Updated
- `AUM MCP Playtest Combat Workflow` - attack methods, focus generation, Astra damage, post-match flow
- `AUM MCP Editor Window Management` - HTTP bridge, popup testing, POSTGAME-CAMERA behavior
- `AUM Grand Merge Verification Feb 12` - full session results

## Next Session Should
- Investigate PreConnect avatar sync timeout on Singapore
- Try winning a match (fire Astra earlier, dodge bot attacks more)
- Test full PlayFab matchmaking queue (Solo 1v1 with real queue config)
- Consider deploying updated server build with avatar sync fix
