# AUM Build & Deploy Credentials Reference

**Last Updated:** 2026-02-21
**Maintained by:** Brahman Studios

---

## Build Workflow (Split Platform)

| Platform | Machine | Unity Version | Build Output | Upload Target |
|----------|---------|---------------|-------------|---------------|
| **iOS** | Mac (macOS) | 2022.3.62f2 | Xcode workspace → IPA | TestFlight / App Store |
| **Android** | Windows | 2022.3.x | AAB | Google Play Open Testing |

---

## Apple / iOS

### Developer Account
| Field | Value |
|-------|-------|
| Apple ID | `apple@brahmanstudios.com` |
| Team Name | Brahman Game Studios Private Limited |
| Team ID | `4HM345TPKH` |
| Account Type | Apple Developer Program (Organization) |
| Subscription | Annual (re-subscribed Feb 2026) |

### App Store Connect
| Field | Value |
|-------|-------|
| App Name | AUM - The Game |
| Bundle ID | `com.BrahmanStudios.Aum` |
| App Store Connect URL | https://appstoreconnect.apple.com/apps/6739957343 |
| TestFlight Public Link | https://testflight.apple.com/join/Cxp8RpgU |
| TestFlight Group | OpenBeta (118 testers) |

### iOS Versions (TestFlight History)
| Version | Build | Date | Status |
|---------|-------|------|--------|
| 0.1.23 | 1 | Feb 21, 2026 | Active (OpenBeta) |
| 0.1.26 | 0 | Oct 21, 2025 | Complete |
| 0.1.25 | 0 | Sep 30, 2025 | Complete |
| 0.1.24 | 1 | Aug 19, 2025 | Complete |
| 0.1.24 | 0 | Aug 15, 2025 | Complete |

### Signing Certificates (Mac Keychain)
| Certificate | Type | Account |
|-------------|------|---------|
| Apple Development: apple@brahmanstudios.com (3R83285TST) | Development | Team |
| Apple Development: pheonixrage_s@yahoo.co.in (2HT6WMV2T3) | Development | Personal |
| Apple Development: Sowmitri Reddy Maluchuru (3QL256433G) | Development | Personal |

**Note:** Distribution certificate is auto-managed by Xcode (Automatic Signing).

### iOS Build Pipeline (Mac)
```
Unity 2022.3 → Xcode workspace → Product > Archive → Distribute App → TestFlight
```
**Automation:**
```bash
cd "/Users/mac/Documents/AUM-2.0 Production/Client"
./deploy.sh ios          # Full: Unity build + archive + upload
./deploy.sh ios-upload   # Upload only (skip Unity build)
```

### PostBuildProcessor (Automatic)
The file `Assets/Editor/PostBuildProcessor.cs` auto-configures every iOS build:
- URL scheme `aum://oauth` for Google OAuth callback
- GIDClientID for Google Sign-In
- Development team `4HM345TPKH`
- NSAppTransportSecurity (allows HTTP for orchestrator)

### App Store Rejection Notes (Version 1.0)
Previous submission was rejected for:
1. **4.8.0 Design: Login Services** — Must add "Sign in with Apple" alongside Google Sign-In
2. **5.1.1 Legal: Privacy** — Need privacy policy URL and accurate data collection disclosure

These must be addressed before App Store release (not required for TestFlight).

---

## Google Play / Android

### Developer Account
| Field | Value |
|-------|-------|
| Account | Brahman Studios |
| Package Name | `com.BrahmanStudios.Aum` |
| Play Console URL | https://play.google.com/console (search "AUM") |
| Track | Open Testing (beta) |
| Play App Signing | Enabled (Google manages app signing key) |

### Android Versions (Play Store History)
| Version Name | Version Code | Date | Track |
|-------------|-------------|------|-------|
| 0.1.27 | 44 | (next upload) | Open Testing |
| 0.1.26 | 43 | Oct 21, 2025 | Open Testing |

**Stats (as of Feb 2026):** 91 installs, 3,743 active testers

### Keystores on Mac

| File | Password | Alias | SHA1 | Status |
|------|----------|-------|------|--------|
| `~/AUM-upload.jks` | `brahman123` | `aum-upload` | `F6:C5:0D:06:00:9E:D9:DD:99:F6:3F:DD:B3:E8:DB:B1:07:5F:0C:23` | Created Feb 12, 2026 — NOT registered with Google Play |
| `~/Documents/Google Keys/AUM.keystore` | Unknown | Unknown | Unknown | Old key — password forgotten |
| `~/Downloads/AUM_2.0.keystore` | Unknown | Unknown | Unknown | Old key — password forgotten |
| `~/Downloads/AUM.keystore` | Unknown | Unknown | Unknown | Old key — password forgotten |

### Upload Key Status
Google Play expects upload key with fingerprint `D5:7B:AD:...` (from the Feb 2026 reset).
The `AUM-upload.jks` created on Mac has a DIFFERENT fingerprint (`F6:C5:0D:...`).

**Resolution needed:** Either:
1. Find the keystore matching `D5:7B:AD:...` (check Windows machine)
2. Reset upload key again: Play Console → Setup → App signing → Request upload key reset
   - Export PEM from `AUM-upload.jks`: `keytool -export -rfc -keystore AUM-upload.jks -alias aum-upload -file upload_cert.pem`
   - Upload the PEM to Google
   - Wait 2-3 days for Google to process

### Windows Keystore Location
When found/configured: `C:\Keystore\AUM-upload.jks` (or whichever matches Google's expected fingerprint)

### Android Build Pipeline (Windows)
```
Unity 2022.3 → Build Settings → Android → Build App Bundle → AAB
```
Upload via Play Console web UI or:
```bash
fastlane android beta
```

---

## Shared Configuration

### Project Locations
| Machine | Path |
|---------|------|
| Mac | `/Users/mac/Documents/AUM-2.0 Production/Client/` |
| Windows | (same repo, pulled via git) |

### Git Repository
| Field | Value |
|-------|-------|
| Remote | `https://github.com/Pheonixrage/Unity6-Legacy.git` |
| Branch | `legacy-working-oct29` |
| Latest Commit | `2a5059928` — Split-build pipeline |

### ProjectSettings.asset (Shared)
| Setting | Value |
|---------|-------|
| Product Name | Aum |
| Bundle Version | 0.1.27 |
| iPhone Bundle ID | `com.BrahmanStudios.Aum` |
| Android Bundle ID | `com.BrahmanStudios.Aum` |
| Android Version Code | 44 |
| Android Min SDK | 23 |
| Android Target SDK | 34 |
| insecureHttpOption | 1 (Always Allowed) |

### Fastlane (Installed on Mac)
| File | Purpose |
|------|---------|
| `fastlane/Fastfile` | iOS beta/release + Android beta/prod lanes |
| `fastlane/Appfile` | App identifiers, team ID |
| `deploy.sh` | Mac-only automation (iOS) |
| `Assets/Editor/BuildScript.cs` | Unity CLI build methods (both platforms) |

### Firebase
| Field | Value |
|-------|-------|
| Project | AUM (Firebase Console) |
| iOS Client ID | Set via `GoogleService-Info.plist` |
| Android Client ID | Set via `google-services.json` |
| Services | Auth (Google Sign-In), Crashlytics, FCM Push |

### AndroidManifest.xml
- Package: `com.BrahmanStudios.AumTest` (template — overridden by Unity's Player Settings at build time)
- Main Activity: `com.google.firebase.MessagingUnityPlayerActivity`
- Deep link: `aum://oauth` for OAuth callback

---

## Important Notes

1. **Never commit keystore files to git** — they contain private keys
2. **insecureHttpOption must stay at 1** — the matchmaking orchestrator uses HTTP
3. **PostBuildProcessor.cs handles iOS config automatically** — no manual Info.plist edits needed
4. **TestFlight builds expire after 90 days** — upload new builds regularly
5. **Android version code must always increment** — next upload must be ≥44
6. **The "Aum Test" vs "Aum" naming**: Legacy AndroidManifest says AumTest, but Player Settings override to Aum at build time
