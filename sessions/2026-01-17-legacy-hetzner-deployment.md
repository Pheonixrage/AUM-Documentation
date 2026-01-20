# Session Log: 2026-01-17 - Legacy Build Hetzner Deployment Plan

## Summary
Investigated deploying the October 2025 legacy build to Hetzner Linux server to restore a playable multiplayer state. Found that legacy projects are ready with TestModeManager bypass, needing only 2 null-check fixes.

## What Was Done
- Explored why legacy build failed on macOS (native DLL missing)
- Discovered legacy projects have everything needed for Hetzner deployment
- Found native Linux DLL exists: `Assets/Plugins/x86_64/libAUM-Server.so`
- Identified MKManager null-check fix needed (2 lines)
- Created comprehensive documentation

## Key Decisions
- **Use legacy projects on Hetzner** instead of current LiteNetLib projects for initial testing
- **Bypass MatchKeeper** using TestModeManager (already created)
- **Don't run legacy on macOS** - native DLL only works on Linux

## Files Changed
- None (planning only)

## Files Created
- `/Users/mac/Downloads/AUM-Project-Analysis/14-LOCAL-TESTING-CURRENT-BUILD.md`
- `/Users/mac/Downloads/AUM-Project-Analysis/15-SESSION-SUMMARY-JAN17-LEGACY-HETZNER.md`
- `/Users/mac/.claude/plans/fluttering-whistling-sifakis.md`

## Open Items
- Apply MKManager.cs null-check fix (2 lines)
- Build legacy server for Linux64
- Deploy to Hetzner
- Build legacy client with Hetzner IP
- Test multiplayer connection

## Required Fix Before Deployment
**File**: `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/MKManager.cs`

Add `if (mkSocket == null) return;` at start of:
- `DeInitialize()` (line 20)
- `SendMKMatchEnd()` (line 49)

## Next Session Should
1. Apply the 2-line MKManager fix
2. Build and deploy server to Hetzner
3. Build client and test connection
4. Verify multiplayer works end-to-end
5. Compare against current build to identify what broke

## Project State
- **Server branch**: `legacy-working-oct6` (commit `7147deb`)
- **Client branch**: `legacy-working-oct29` (commit `a4cfae155`)
- **Current projects**: AUM-Headless and AUM-The-Epic (LiteNetLib-based, also working)
