# AUM Deployment Workflow
**Generated:** January 25, 2026

---

## Current Status

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT STATUS                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   [✓] STEP 1: Develop & Fix             ────────── COMPLETE                    │
│       • Stamina sync added to SimulationResult packet                          │
│       • Animation IndexOutOfRange fixed (MukthaMuktha, Amuktha)                │
│       • 30 client files + 12 server files modified                             │
│                                                                                 │
│   [✓] STEP 2: Commit Changes            ────────── COMPLETE                    │
│       • CLIENT: 45bc7c47 "Jan 25 2026: Stamina sync, animation fixes"         │
│       • SERVER: 7b19179 "Jan 25 2026: Server stamina sync, bot fixes"          │
│                                                                                 │
│   [✓] STEP 3: Push to Origin            ────────── COMPLETE                    │
│       • CLIENT: Pushed to origin/feature/authoritative-architecture            │
│       • SERVER: Pushed to origin/feature/authoritative-architecture            │
│                                                                                 │
│   [ ] STEP 4: Build iOS                 ────────── PENDING                     │
│       • Unity → iOS build                                                       │
│       • Xcode archive → IPA                                                     │
│                                                                                 │
│   [ ] STEP 5: Test on Device            ────────── PENDING                     │
│       • Install on iPhone                                                       │
│       • Playtest all match types                                               │
│                                                                                 │
│   [ ] STEP 6: Merge to Main             ────────── PENDING (after testing)     │
│       • PR from feature → main                                                  │
│       • Squash/merge commits                                                    │
│                                                                                 │
│   [ ] STEP 7: Deploy Server             ────────── PENDING (after merge)       │
│       • SSH to Hetzner                                                          │
│       • Update server binary                                                    │
│       • Restart systemd service                                                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Full Deployment Pipeline

```
═══════════════════════════════════════════════════════════════════════════════════
                              DEVELOPMENT PHASE
═══════════════════════════════════════════════════════════════════════════════════

    ┌─────────────────┐
    │   Write Code    │
    │   Fix Bugs      │
    │   Test Locally  │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   git add .     │
    │   git commit    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   git push      │
    │   origin/feature│
    └────────┬────────┘
             │
═══════════════════════════════════════════════════════════════════════════════════
                                BUILD PHASE
═══════════════════════════════════════════════════════════════════════════════════
             │
             ▼
    ┌─────────────────┐         ┌─────────────────┐
    │   Unity Build   │────────►│   Xcode Build   │
    │   iOS Target    │         │   Archive       │
    │                 │         │   Sign & Export │
    └─────────────────┘         └────────┬────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │   Install on    │
                                │   Test Device   │
                                │   (iPhone)      │
                                └────────┬────────┘
                                         │
═══════════════════════════════════════════════════════════════════════════════════
                               TESTING PHASE
═══════════════════════════════════════════════════════════════════════════════════
                                         │
                                         ▼
                                ┌─────────────────┐
                                │   Playtest      │
                                │   • Tutorial    │
                                │   • Solo 1v1    │
                                │   • Multiplayer │
                                └────────┬────────┘
                                         │
                            ┌────────────┴────────────┐
                            │                         │
                            ▼                         ▼
                    ┌─────────────┐           ┌─────────────┐
                    │   FAILED    │           │   PASSED    │
                    │   ──────    │           │   ──────    │
                    │   Return to │           │   Continue  │
                    │   Dev Phase │           │   to Merge  │
                    └──────┬──────┘           └──────┬──────┘
                           │                         │
                           ▼                         │
                    ┌─────────────┐                  │
                    │ Check Logs: │                  │
                    │ log_errors  │                  │
                    │ log_tail    │                  │
                    └─────────────┘                  │
                                                     │
═══════════════════════════════════════════════════════════════════════════════════
                               MERGE PHASE
═══════════════════════════════════════════════════════════════════════════════════
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Create PR      │
                                            │  feature → main │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Review &       │
                                            │  Approve PR     │
                                            └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Merge to main  │
                                            │  (both repos)   │
                                            └────────┬────────┘
                                                     │
═══════════════════════════════════════════════════════════════════════════════════
                              DEPLOYMENT PHASE
═══════════════════════════════════════════════════════════════════════════════════
                                                     │
                    ┌────────────────────────────────┴────────────────────────────┐
                    │                                                             │
                    ▼                                                             ▼
        ┌─────────────────────┐                                   ┌─────────────────────┐
        │   CLIENT DEPLOY     │                                   │   SERVER DEPLOY     │
        │   ═══════════════   │                                   │   ═══════════════   │
        │                     │                                   │                     │
        │   TestFlight        │                                   │   SSH Hetzner       │
        │   ───────────       │                                   │   ───────────       │
        │   Upload IPA        │                                   │   git pull          │
        │   External testers  │                                   │   ./build.sh        │
        │                     │                                   │   systemctl restart │
        │   App Store         │                                   │                     │
        │   ─────────         │                                   │   Verify:           │
        │   Submit for review │                                   │   • Server running  │
        │   Release           │                                   │   • Logs clean      │
        │                     │                                   │   • Connections OK  │
        └─────────────────────┘                                   └─────────────────────┘
```

---

## Build Commands Reference

### iOS Client Build

```bash
# 1. Unity Build (from terminal or Unity)
/Applications/Unity/Hub/Editor/2022.3.*/Unity.app/Contents/MacOS/Unity \
  -batchmode \
  -projectPath /Users/mac/Documents/GitHub/AUM-The-Epic \
  -buildTarget iOS \
  -executeMethod AUMBuildScript.BuildiOS \
  -quit

# 2. Open Xcode Project
open /Users/mac/Documents/GitHub/AUM-The-Epic/Builds/iOS/Unity-iPhone.xcodeproj

# 3. In Xcode:
#    - Select "Any iOS Device (arm64)"
#    - Product → Archive
#    - Distribute App → Ad Hoc / Development
#    - Export IPA
```

### Headless Server Build

```bash
# 1. Build Linux Headless
/Applications/Unity/Hub/Editor/2022.3.*/Unity.app/Contents/MacOS/Unity \
  -batchmode \
  -projectPath /Users/mac/Documents/GitHub/AUM-Headless \
  -buildTarget Linux64 \
  -nographics \
  -executeMethod HeadlessBuildScript.BuildServer \
  -quit

# 2. Deploy to Hetzner
scp Builds/Server/AUM-Server root@65.109.133.129:/opt/aum/

# 3. On Server
ssh root@65.109.133.129
cd /opt/aum
systemctl stop aum-server
mv AUM-Server AUM-Server.backup
mv AUM-Server.new AUM-Server
chmod +x AUM-Server
systemctl start aum-server
journalctl -u aum-server -f  # Watch logs
```

---

## Git Commands Reference

### Commit & Push (Current Workflow)

```bash
# Already completed for this session:
git add <files>
git commit -m "message"
git push origin feature/authoritative-architecture
```

### Merge to Main (After Testing)

```bash
# Option A: Fast-forward merge (if linear history)
git checkout main
git merge feature/authoritative-architecture
git push origin main

# Option B: Squash merge (cleaner history)
git checkout main
git merge --squash feature/authoritative-architecture
git commit -m "Merge feature/authoritative-architecture: Stamina sync, animation fixes"
git push origin main

# Option C: GitHub PR (recommended for team)
gh pr create --base main --head feature/authoritative-architecture \
  --title "Jan 25 2026: Stamina sync, animation fixes" \
  --body "Merges authoritative architecture improvements"
```

### Rollback Commands (If Needed)

```bash
# Revert last commit (keeps changes)
git reset --soft HEAD~1

# Revert last commit (discards changes)
git reset --hard HEAD~1

# Revert specific commit
git revert <commit-hash>

# Force push (DANGER - only for feature branches)
git push --force origin feature/authoritative-architecture
```

---

## Verification Checklist

### Pre-Merge Testing

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TESTING CHECKLIST                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Tutorial Mode (LocalAuthority)                                                │
│   [ ] Quest 1-5 complete without freezing                                       │
│   [ ] Dodge works after stamina spent                                           │
│   [ ] Bot responds to combat                                                    │
│                                                                                 │
│   Solo 1v1 (HybridAuthority)                                                    │
│   [ ] Match starts without errors                                               │
│   [ ] Stamina syncs correctly (watch [STAMINA-SYNC] logs)                      │
│   [ ] No animation exceptions (watch logs)                                      │
│   [ ] Combat feels responsive                                                   │
│   [ ] Focus gains properly from hits                                            │
│                                                                                 │
│   Multiplayer (ServerAuthority) - if available                                  │
│   [ ] Connection successful                                                     │
│   [ ] State sync correct                                                        │
│   [ ] No excessive position mismatches                                          │
│                                                                                 │
│   Performance                                                                   │
│   [ ] No memory leaks (check profiler)                                         │
│   [ ] Stable frame rate (60 FPS target)                                        │
│   [ ] No excessive log spam                                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: What Changed Today

| Repository | Commit | Key Changes |
|------------|--------|-------------|
| **CLIENT** | 45bc7c47 | Stamina in SimulationResult, Animation index fix |
| **HEADLESS** | 7b19179 | Stamina in SimulationResult (server side) |

### Files Changed (Summary)

**CLIENT (30 files):**
- Network: Packet.cs (stamina field)
- Managers: SimulationManager.cs (stamina sync), PlayerManager.cs
- Characters: MukthaMukthaEnemy.cs, AmukthaEnemy.cs (meleeAnimIndex fix)
- Authority: BaseAuthority.cs, HybridAuthority.cs, ServerAuthority.cs

**HEADLESS (12 files):**
- Network: Packet.cs (stamina field)
- Player: PlayerManager.cs (stamina in SimulationResult)
- Bots: BotDecisionManager.cs
- State: StateManager.cs
