---
date: 2026-04-22
pipeline: P3 — Legacy Live
repo: AUM-Unity-Staging-Legacy
branch: legacy-working-oct29
build: v0.1.44 (iOS build 4 / Android build 68)
topic: iOS TestFlight matchmaking failure — live device debugging
tags: [ios, testflight, matchmaking, playfab, serverallocator, debugging, devicectl]
status: resolved — rebuilt IPA confirmed working by user (2026-04-22)
---

# iOS TestFlight — "Find Match returns to menu after 5s"

## Symptom

TestFlight IPA uploaded Apr 13 wouldn't find matches. User taps **Find Match**,
spinner shows, and ~5 seconds later the app returns to the main menu with no
error popup.

## Wrong theory I chased first (and why)

My opening theory: **PROD PlayFab title `158C02` is missing matchmaking queues.**

How I got there: I ran `strings` on `IOS TEstflight build/Data/resources.assets`
and grep-filtered for `15F2B7|158C02|1A4AA8`. Only `158C02` came back.
I concluded the IPA was built for Production and that PROD queues must be
misconfigured.

**What I missed:** `AUMAuthConfig.asset` serializes all three title IDs
(development/staging/production). The binary layout of the ScriptableObject in
`resources.assets` only happened to render `158C02` as a standalone printable
line for `strings`. The Dev/Staging IDs were still in there, just not on clean
boundaries. `strings | grep '^ID$'` is not a reliable way to determine active
`buildMode` — you need either the runtime log or a proper asset-dump tool.

**Lesson:** When guessing which enum value serialized into a binary Unity
asset, don't trust `strings` unless you can grep for the enclosing structure,
and never ship a theory to the user based on it alone. Device logs are
authoritative; reach for them sooner.

## Right answer (from live device capture)

Three uncommitted local-dev flips got baked into the IPA during the 67-minute
window between the `v0.1.44 build 68` commit (Apr 12 23:30) and the Xcode
export (Apr 13 00:37):

| File | Field | Committed (HEAD) | In the built IPA |
|---|---|---|---|
| `Assets/Resources/AUMAuthConfig.asset` | `buildMode` | `2` (Production) | `0` (Development) |
| `Assets/Scenes/Initiate.unity` | AUMAuthManager `environment` | `2` (Production) | `0` (Development) |
| `Assets/Scenes/Initiate.unity` | ServerAllocator `connectionMode` | `0` (PlayFab) | `1` (Local) |

With `connectionMode=Local`, `ServerAllocator` points the client at
**`127.0.0.1:6006`** — the developer's PC loopback, which on a phone is
the phone itself. And because `buildMode=Development` (not `Production`),
the safety check at `ServerAllocator.cs:132-148` that would normally force
`ConnectionMode.PlayFab` in production builds never fires. The scene-serialized
`Local` leaked straight into the TestFlight IPA.

## Reproduction timeline (from device log)

```
08:57:15.478  [AUMAuth] BuildMode=Development → Environment=Development, AuthMode=FirebaseOpenId
08:57:15.481  [ServerAllocator] Build mode: Development, ConnectionMode: Local
08:57:15.482  [ServerAllocator]   Server: 127.0.0.1:6006
…user taps Find Match…
08:57:28.828  [MainEntrance] ★ Local MODE - Bypassing PlayFab matchmaking
08:57:28.829  [MainEntrance] ★ STARTING Local MATCH ★
08:57:28.838  [PreConnectManager] Starting pre-connect to 127.0.0.1:6006 (expectedHumans=2)
08:57:34.483  [PreConnectManager] Disconnected from server during pre-connect
08:57:34.483  [MainEntrance] Pre-connect failed: Disconnected during pre-connect
                             (auth=False, mode=Local) - returning to menu
```

28.828 → 34.483 = **5.655s** — matches the reported symptom exactly. It was a
TCP handshake timeout against a non-existent localhost server.

## Fix

Surgical revert of the two clobbered files:

```bash
git checkout HEAD -- Assets/Resources/AUMAuthConfig.asset Assets/Scenes/Initiate.unity
```

Then in Unity, reopen `Initiate.unity` (File → Revert) if it's currently open
so the in-memory editor state doesn't re-overwrite the revert on next save.
Rebuild → export Xcode → `fastlane ios beta`.

## Device-debug workflow for iOS 18+ (what worked)

`libimobiledevice` (`idevicesyslog`) **cannot see iOS 18 devices** on current
macOS — Apple moved to CoreDevice. `idevice_id -l` returns empty even when
the phone is paired and visible in Finder/Xcode.

The working path is Apple's `devicectl` with `--console`:

```bash
xcrun devicectl list devices               # confirm paired device
xcrun devicectl device process launch \
    --device <name-or-id> \
    --console \
    --terminate-existing \
    com.BrahmanStudios.Aum
```

`--console` attaches stdout/stderr of the app to the terminal — every Unity
`Debug.Log` streams live. Ctrl+C to stop.

**Prerequisite:** iPhone must be **unlocked** when you start the command.
`devicectl` mounts the developer disk image at launch, which fails with
`kAMDMobileImageMounterDeviceLocked` on a locked phone.

The reusable capture scripts from this session live at
`/tmp/aum-ios-debug/capture.sh` and `check-prod-queues.sh`. (These are in
/tmp and will evaporate on reboot — if they become useful regularly, promote
them to `scripts/ios-debug/` in the repo.)

## Preventive follow-ups (not yet done — user declined for now)

1. **Pre-build guard**: `IPreprocessBuildWithReport` that refuses iOS/Android
   builds when `AUMAuthConfig.buildMode != Production` (or fails closed unless
   a `AUM_ALLOW_DEV_BUILD=1` env var is set). Would have blocked the bad
   upload cold.

2. **Boot-time nag**: on `MainEntranceController.Awake`, if `buildMode` or
   `connectionMode` isn't the production pair, show a red on-screen toast
   (not just a `Debug.Log`). Silent misconfig is the whole reason this cost
   a day of tester confusion.

3. **Pre-commit/pre-build checklist macro** in `fastlane/Fastfile ios beta`:
   before `build_app`, print the contents of `AUMAuthConfig.asset` line 15
   and the ServerAllocator block from `Initiate.unity`, require an explicit
   `y/N` confirmation.

## Key file references

- [`Assets/Resources/AUMAuthConfig.asset`](Assets/Resources/AUMAuthConfig.asset) — `buildMode` field (line 15)
- [`Assets/Scenes/Initiate.unity`](Assets/Scenes/Initiate.unity) — AUMAuthManager `environment` (line 5542), ServerAllocator `connectionMode` (line 5576)
- [`Assets/Scripts/Network/ServerAllocator.cs`](Assets/Scripts/Network/ServerAllocator.cs) — ConnectionMode enum (line 43), production safety check (line 132)
- [`Assets/Scripts/Auth/AUMAuthConfig.cs`](Assets/Scripts/Auth/AUMAuthConfig.cs) — BuildMode enum (line 250)
- [`Assets/Scripts/Managers/MainEntranceController.cs`](Assets/Scripts/Managers/MainEntranceController.cs) — PlayFab-bypass branch (line 1080), OnPreConnectFailed (line 2375), OnPlayFabMatchFailed (line 2437)

## Enum reference (PlayFab matchmaking routing)

```
AUMAuthConfig.BuildMode:           Development=0, Staging=1, Production=2
ServerAllocator.ConnectionMode:    PlayFab=0, Local=1, Hetzner=2, LAN=3
```

Production-safe values for any shipped build: `buildMode=2`, `connectionMode=0`.
