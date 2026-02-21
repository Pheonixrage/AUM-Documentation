# Android Build & Release Guide

**Last Updated:** February 21, 2026
**App:** AUM | **Package:** `com.BrahmanStudios.Aum`
**Play Console:** Open Testing Track

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Keystore & Signing](#keystore--signing)
3. [Unity Build Settings](#unity-build-settings)
4. [Build Process](#build-process)
5. [Google Play Upload](#google-play-upload)
6. [Version History](#version-history)
7. [Troubleshooting](#troubleshooting)

---

## Quick Reference

| Key | Value |
|-----|-------|
| Package Name | `com.BrahmanStudios.Aum` |
| Current Version | `0.1.28` (Version Code `50`) |
| Min SDK | 23 (Android 6.0) |
| Target SDK | 34 (Android 14) |
| ABIs | ARM64 + ARMv7 |
| Split Binary | Enabled (required for Play Store) |
| Build Type | Android App Bundle (AAB) |

---

## Keystore & Signing

### Active Keystore (Google Play Upload Key)

| Property | Value |
|----------|-------|
| **File** | `C:\Keystore\AUM-google-upload.keystore` |
| **Password** | `brahman123` |
| **Alias** | `aum` |
| **Alias Password** | `brahman123` |
| **SHA1 Fingerprint** | `D5:7B:AD:56:79:BA:CB:E4:C7:0E:AC:DE:60:7B:D5:99:9E:81:41:A0` |
| **Format** | JKS |

### Mac Location

The same keystore was originally at `~/AUM.keystore` on the Mac. If building from Mac, use this file or copy `AUM-google-upload.keystore` to the Mac.

### All Files in C:\Keystore\

| File | Purpose | Status |
|------|---------|--------|
| `AUM-google-upload.keystore` | **ACTIVE** Google Play upload key | Use this one |
| `AUM.keystore` | Old keystore (same as AUM-google-upload, original copy from Downloads) | Backup |
| `AUM-upload.jks` | Created on Mac, WRONG fingerprint (F6:C5:0D...) | Do NOT use |
| `upload_certificate.pem` | Google's upload certificate (from Play Console) | Reference |
| `aum-upload-cert.pem` | Exported from AUM-upload.jks | Not needed |

### Verifying Keystore Fingerprint

```bash
# Check SHA1 fingerprint of a keystore
keytool -list -v -keystore "C:\Keystore\AUM-google-upload.keystore" -alias aum -storepass brahman123

# Expected output should include:
# SHA1: D5:7B:AD:56:79:BA:CB:E4:C7:0E:AC:DE:60:7B:D5:99:9E:81:41:A0
```

### Google Play App Signing

Google Play uses **App Signing by Google Play**:
- **Upload key** (you sign with): `AUM-google-upload.keystore` (SHA1: D5:7B:AD...)
- **App signing key** (Google re-signs): Managed by Google Play

The upload key fingerprint MUST match what's registered in Play Console under:
**Setup > App signing > Upload key certificate**

---

## Unity Build Settings

### Player Settings (Edit > Project Settings > Player)

| Setting | Value |
|---------|-------|
| Company Name | Brahman Studios |
| Product Name | Aum |
| Package Name (Android) | `com.BrahmanStudios.Aum` |
| Bundle Version | `0.1.28` |
| Bundle Version Code | `50` |
| Min API Level | 23 |
| Target API Level | 34 |
| Target Architectures | ARM64 + ARMv7 |
| Scripting Backend | IL2CPP |
| Split Application Binary | **Enabled** |

### Build Settings (File > Build Settings)

| Setting | Value |
|---------|-------|
| Platform | **Android** (must be switched!) |
| Build App Bundle | **Checked** (AAB, not APK) |
| Create symbols.zip | Optional (recommended for crash reports) |

### Keystore in Unity (Publishing Settings)

| Setting | Value |
|---------|-------|
| Custom Keystore | **Enabled** |
| Keystore Path | `C:/Keystore/AUM-google-upload.keystore` |
| Keystore Password | `brahman123` |
| Key Alias | `aum` |
| Key Password | `brahman123` |

---

## Build Process

### Prerequisites
- Unity 6 with Android Build Support module
- Android SDK (API 34)
- NDK (for IL2CPP)
- Correct keystore configured

### Step-by-Step

1. **Switch to Android platform**
   - File > Build Settings > Select Android > Switch Platform
   - Wait for reimport (can take several minutes)

2. **Verify settings**
   - Check package name is `com.BrahmanStudios.Aum` (NOT `AumTest`)
   - Check "Build App Bundle (Google Play)" is checked
   - Check "Split Application Binary" is enabled
   - Verify keystore path and credentials in Publishing Settings

3. **Increment version**
   - Edit > Project Settings > Player > Other Settings
   - Bump `Bundle Version` (e.g., `0.1.28` -> `0.1.29`)
   - Bump `Bundle Version Code` (must be HIGHER than any previously uploaded)
   - Current highest: **50**

4. **Build**
   - File > Build Settings > Build
   - Choose output filename (e.g., `AUM.aab`)
   - Wait for build to complete

5. **Verify output**
   - Base module should be ~187 MB (with Split Binary)
   - Total with asset packs ~1.3-1.4 GB
   - If base > 200 MB, ensure Split Application Binary is enabled

---

## Google Play Upload

### Play Console URL
https://play.google.com/console

### Upload Steps

1. Navigate to **Testing > Open testing** (or appropriate track)
2. Click **Create new release**
3. Drag and drop the `.aab` file
4. Wait for upload and processing
5. Fill in:
   - **Release name:** version string (e.g., `0.1.28`)
   - **Release notes:** Brief description of changes
6. Click **Review release**
7. Review warnings (Korea GRAC and debug symbols are OK)
8. Set **Roll-out percentage** (100% for testing)
9. Click **Save** then **Start rollout**
10. Go to **Publishing overview** > Click **Send changes for review**

### Post-Upload
- Google runs quick checks (~14 minutes)
- Review typically takes a few hours for open testing
- With managed publishing OFF, it goes live automatically on approval

---

## Version History

| Version Code | Bundle Version | Date | Notes |
|-------------|---------------|------|-------|
| 50 | 0.1.28 | Feb 21, 2026 | Party fixes, MatchHistory, host ready state, correct keystore |
| 43 | 0.1.26 | Previous | Previous open testing release |
| 16 | 0.1.23 | Earlier | Earlier release |

---

## Troubleshooting

### "Package name doesn't match" Error
**Cause:** Built with wrong platform active (e.g., Standalone instead of Android)
**Fix:** File > Build Settings > switch to Android platform, rebuild

### "Upload key fingerprint mismatch"
**Cause:** Signing with wrong keystore
**Fix:** Use `C:\Keystore\AUM-google-upload.keystore` (alias: `aum`). Verify with:
```bash
keytool -list -v -keystore "C:\Keystore\AUM-google-upload.keystore" -alias aum -storepass brahman123
```
Expected SHA1: `D5:7B:AD:56:79:BA:CB:E4:C7:0E:AC:DE:60:7B:D5:99:9E:81:41:A0`

### "Version code already used"
**Cause:** Google Play rejects version codes that have been previously uploaded (even if that upload was deleted)
**Fix:** Increment version code to a number higher than any ever uploaded. Current highest: **50**

### "Base module too large (>200 MB)"
**Cause:** Split Application Binary not enabled
**Fix:** Edit > Project Settings > Player > Publishing Settings > Enable "Split Application Binary"

### AAB size ~1.4 GB
This is normal for AUM. With Split Binary enabled:
- Base module: ~187 MB (under 200 MB limit)
- Asset packs: ~1.2 GB (delivered as install-time asset packs)
- Total install size: ~1.45 GB

### Build fails with IL2CPP errors
- Ensure Android NDK is installed via Unity Hub
- Check that target API level 34 SDK is installed
- Try: Edit > Preferences > External Tools > verify Android SDK/NDK paths
