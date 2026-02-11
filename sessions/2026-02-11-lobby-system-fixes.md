# Session Log: 2026-02-11 - Lobby System Fixes & Social Features Debugging

## Summary
Continuation session: Fixed compilation errors from PlayFab social services, deployed CloudScript, and debugged lobby creation flow end-to-end. Lobby creation now properly transitions to lobby room UI.

## What Was Done

### Compilation Fixes
- Fixed 10 compilation errors across PlayFabLobbyService, PlayFabPartyService, PlayFabMatchmaker
- Key fixes: `avatar.trinityGod` → `avatar.godSelected`, `JoinLobbyRequest` namespace ambiguity, `CurrentPlayers.Count` → `CurrentPlayers` (uint not collection), `LobbyNotFound` → `LobbyDoesNotExist`
- Added `using System.Linq` to PlayFabMatchmaker

### CloudScript Deployment
- Merged 7 new social handlers with existing 17 handlers
- Deployed to PlayFab as Revision 51 (24 total handlers)
- New: GenerateFriendCode, SearchByFriendCode, SendFriendRequest, ClearFriendRequest, GetFriendsEnrichmentData, SendInvite, ClearProcessedInvites

### Lobby Creation Flow (Main Bug)
- **Root cause 1**: `ChangeNumber` check (`0 <= 0`) blocked first `GetLobbyState` poll after creation → `InLobby()` never called → UI never transitioned
- **Root cause 2**: `LobbyData` constructor skipped players with empty `friendID` → empty player list
- **Root cause 3**: `OnLobbyLeft()` never stopped polling coroutine → infinite rate-limit spam on PlayFab (hundreds of throttled requests)
- **Fix**: Added `forceNextPoll` flag, used `playerCount` instead of `maxPlayers`, stop polling on leave

### Lobby Robustness
- Added `isCreatingLobby` guard to prevent double lobby creation
- Added polling backoff: 5s base, +5s per consecutive error, 30s max, auto-stop after 10 errors
- Added stale lobby auto-cleanup in FindLobbies (leave orphaned lobbies owned by player)
- Added `OnApplicationQuit`/`OnDestroy` handlers to leave lobby on exit
- Added host name to SearchData for lobby browser display (was showing entity ID)
- Added immediate `GetLobbyState()` on join flows for instant UI transition

### Profile & UI Fixes
- Fixed blank friend ID on profile screen (new players had no SocialInfo key)
- Fixed lobby toggle hidden on Karma Marga (was gated behind `wins > 0`)

### MCP Autonomous Dev Tools
- Committed MCP bridge tools: `unity_execute_code`, `unity_screenshot`, `unity_simulate_input`, `unity_get_ui_state`

### Training Mode
- Committed `StartLocalMatch()` and `IsOfflineMode()` for Training mode to bypass matchmaker

## Key Decisions
- Lobby polling: 5s base interval with exponential backoff (was 3s flat, caused rate limiting)
- Stale lobbies: Auto-cleanup on browse via FindLobbies, plus leave on app quit
- UseConnections=false means PlayFab can't detect disconnects; explicit LeaveLobby required

## Files Changed
- `Assets/Scripts/PlayFab/PlayFabLobbyService.cs` - Major: forceNextPoll, polling backoff, stale cleanup, app quit handler, host name in SearchData
- `Assets/Scripts/Managers/LobbyManager.cs` - Major: DoCreateLobby with guards, immediate GetLobbyState, stop polling on leave, LobbyData constructor fix
- `Assets/Scripts/PlayFab/PlayFabDataBridge.cs` - Handle missing SocialInfo for new players
- `Assets/Scripts/UI/Managers/KarmaMargManager.cs` - Remove wins>0 gate on lobby toggle
- `Assets/Scripts/Managers/MainEntranceController.cs` - Training mode local match
- `Assets/Scripts/Managers/GameManager.cs` - IsOfflineMode() helper
- `Assets/Editor/UnityMCPServer/UnityMCPBridge.cs` - MCP autonomous dev tools
- `unity-mcp-server/index.js` - MCP server tool handlers
- `IMPLEMENTATION_STATE.md` - Updated with all progress

## Commits Pushed
| Hash | Description |
|------|-------------|
| 42563391 | chore: Add meta files for social services and update font assets |
| 9b08b749 | fix: Lobby creation flow, polling backoff, stale cleanup, UI transitions |
| 129074b3 | feat: Training mode local match bypass - no server needed |
| 5843e927 | feat(mcp): Autonomous dev tools - screenshot, execute, input, UI state |
| 66e2b6dc | fix: Resolve 10 compilation errors in PlayFab social services |

## Open Items
- Lobby join flow needs testing (join from browser, join from invite)
- Friends list and party features not yet functional (skeletons only)
- Discord SDK not yet integrated (scaffolded only)
- CloudScript `http.request` can't reach Hetzner orchestrator from PlayFab servers
- Stale lobbies from earlier testing will auto-expire via PlayFab TTL (~2hr)

## Next Session Should
- Test lobby join flow end-to-end
- Test friend code generation on first login
- Begin implementing friends list UI with PlayFabFriendsService
- Consider switching to `UseConnections=true` for automatic lobby cleanup on disconnect
