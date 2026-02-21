# Session Log: 2026-02-21 — Build & Deploy Pipeline (iOS + Android)

## Summary
Set up the split-build pipeline for AUM: Mac builds iOS (TestFlight), Windows builds Android (Play Store). Successfully uploaded iOS build to TestFlight with 118 testers on OpenBeta. Android blocked by upload key mismatch.

## What Was Done

### iOS (Complete)
- Fixed disk space issue (32GB freed from Xcode caches, Unity cache, system caches)
- Archived Xcode project (Any iOS Device arm64)
- Uploaded to App Store Connect (version 0.1.23, build 1)
- Resolved "Missing Compliance" (no custom encryption)
- Added build to OpenBeta external testing group
- Public TestFlight link active: https://testflight.apple.com/join/Cxp8RpgU

### Android (Blocked)
- Discovered upload key mismatch: `AUM-upload.jks` (F6:C5:0D) doesn't match Google's expected key (D5:7B:AD)
- Found 5 keystore files on Mac, 4 have forgotten passwords
- Need to either find correct keystore or reset upload key with Google

### Build Pipeline Setup
- Created `deploy.sh` (Mac = iOS only automation)
- Created `fastlane/Fastfile` (iOS + Android lanes)
- Created `fastlane/Appfile` (identifiers, team config)
- Created `Assets/Editor/BuildScript.cs` (Unity CLI builds)
- Committed as `2a5059928` — "Split-build pipeline"

### Cleanup
- Reverted all Unity 6 Gradle template changes (mainTemplate, settingsTemplate, AndroidManifest, launcherTemplate)
- Reverted ~200 Unity 6 reimport artifacts (lightmap metas, Firebase metas)
- Removed backup gradle files and Unity 6 temp files
- Kept useful ProjectSettings changes (product name, bundle ID, version)

## Key Decisions
- Split builds by platform: Mac=iOS, Windows=Android (Unity 6 Gradle incompatibility with legacy templates)
- Keystore paths in ProjectSettings reverted to Windows paths (shared repo)
- iOS version 0.1.23 (from pre-existing Xcode build) — Android will be 0.1.27

## Files Changed
- `ProjectSettings/ProjectSettings.asset` — product name, version, bundle IDs
- `deploy.sh` — new, iOS automation
- `fastlane/Fastfile` — new, upload lanes
- `fastlane/Appfile` — new, identifiers
- `Assets/Editor/BuildScript.cs` — new, CLI build methods
- `AUM-Documentation/setup/BUILD-DEPLOY-CREDENTIALS.md` — new, full credentials reference

## Open Items
- **Android upload key mismatch** — need correct keystore or key reset (2-3 day wait)
- **App Store rejection issues** — need Sign in with Apple + privacy policy for App Store release
- **Version sync** — iOS at 0.1.23, Android will be 0.1.27 (next Unity rebuild will sync)

## Next Session Should
- Resolve Android upload key (find correct keystore on Windows or reset via Play Console)
- Build and upload Android AAB once key is sorted
- Consider adding `ITSAppUsesNonExemptEncryption = NO` to Info.plist via PostBuildProcessor to skip compliance question on future uploads
- Plan Sign in with Apple implementation for App Store approval
