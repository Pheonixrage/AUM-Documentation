# AUM Legacy Server Deployment Experiment

**Date:** January 19, 2026
**Duration:** ~3 hours
**Status:** SUCCESS - Server running, awaiting client test

---

## 1. INTENT & MOTIVATION

### Problem Statement
The current AUM-Epic (client) and AUM-Headless (server) projects are experiencing "glitchy" multiplayer behavior. Rather than debugging the complex new architecture, the decision was made to restore a known-working state using the legacy October 2025 builds.

### Goal
Deploy the legacy AUM server to Hetzner VPS and configure a legacy client to connect directly, bypassing the old MatchKeeper/WebSocket orchestration infrastructure.

### Success Criteria
1. Server runs on Hetzner (65.109.133.129:6006) without crashing
2. Server waits for human player connection (doesn't auto-end match)
3. Client can connect and authenticate
4. Gameplay functions correctly

---

## 2. ARCHITECTURE OVERVIEW

### Legacy System (October 2025)
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Game Client   │────▶│   MatchKeeper    │────▶│   Game Server   │
│  (Unity Build)  │     │   (WebSocket)    │     │  (Unity Headless)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
        │    Session UUID       │    avatarList          │
        └───────────────────────┴────────────────────────┘
```

### Test Mode Bypass (Our Solution)
```
┌─────────────────┐                              ┌─────────────────┐
│   Game Client   │─────── Direct UDP ──────────▶│   Game Server   │
│ + TestModeClient│      65.109.133.129:6006     │ + TestModeManager│
└─────────────────┘                              └─────────────────┘
        │                                                │
        │         Matching Session UUIDs                 │
        │    3d46e7bc-914e-fca2-c3ae-1ae23d72aa34       │
        └────────────────────────────────────────────────┘
```

---

## 3. PROJECT LOCATIONS

| Project | Path | Purpose |
|---------|------|---------|
| Legacy Client | `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy/` | Unity client build |
| Legacy Server | `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/` | Unity headless server |
| Server Deploy | `/Users/mac/Documents/GitHub/server legacy/` | Built server binary |
| Hetzner Server | `root@65.109.133.129:/root/server/` | Production deployment |

---

## 4. TIMELINE OF CHANGES

### Phase 1: Initial Setup (~17:00 UTC)

#### 4.1 TestModeManager.cs (Server)
**File:** `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/TestModeManager.cs`

**Purpose:** Bypass MatchKeeper orchestration, populate avatarList directly

```csharp
// Session ID constants for deterministic matching
public const string PLAYER_1_SESSION = "test-player-1-session";
public const string BOT_1_SESSION = "test-bot-1-session";

public static void Initialize(int port, MatchType matchType, bool includeBot, bool isFirstMatch)
{
    // Create test avatars directly in avatarList
    AddTestAvatar(1, "TestPlayer1", PLAYER_1_SESSION, 0,
                  FightingStyles.Amuktha, TrinityGods.Brahma, false, 0);

    if (includeBot)
    {
        AddTestAvatar(2, "TestBot", BOT_1_SESSION, 1,
                      FightingStyles.MukthaMuktha, TrinityGods.Shiva, true, 1);
    }

    // Initialize server socket on specified port
    NetworkManager.Instance.InitializeServer(port);
}

// MD5 hash creates deterministic GUID from string
private static Guid StringToGuid(string input)
{
    using (MD5 md5 = MD5.Create())
    {
        byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(input));
        return new Guid(hash);
    }
}
```

#### 4.2 TestModeClient.cs (Client)
**File:** `AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/TestModeClient.cs`

**Purpose:** Configure client for direct server connection

```csharp
public class TestModeClient : MonoBehaviour
{
    public static string serverIP = "65.109.133.129";
    public static int serverPort = 6006;

    public static void SetupForTestMode()
    {
        // Generate matching session UUID
        Guid sessionGuid = StringToGuid("test-player-1-session");
        SessionManager.sessionUUID = sessionGuid.ToString();

        // Setup match_Avatars array (prevents null reference)
        SetupMatchAvatars();

        // Set local player ID
        SessionManager.localPlayerID = 1;
    }

    private static void SetupMatchAvatars()
    {
        SessionManager.match_Avatars = new SessionManager.Avatar[2];
        SessionManager.match_Avatars[0] = new SessionManager.Avatar
        {
            playerID = 1,
            playerName = "TestPlayer1",
            sessionID = StringToGuid("test-player-1-session").ToString(),
            // ... other fields
        };
        SessionManager.match_Avatars[1] = new SessionManager.Avatar
        {
            playerID = 2,
            playerName = "TestBot",
            isBot = true,
            // ... other fields
        };
    }
}
```

---

### Phase 2: First Bug Fixes (~17:15 UTC)

#### 4.3 MKManager.cs - Null Reference Fix
**File:** `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/MKManager.cs`

**Problem:** `NullReferenceException` when match ended because MKManager wasn't initialized in test mode

**Fix:**
```csharp
public static void SendMKMatchEnd()
{
    // In test mode, MKManager is not initialized - skip reporting
    if (mkSocket == null)
    {
        Debug.Log("[MKManager] Skipping match end report (test mode - no MatchKeeper connection)");
        return;
    }

    // ... rest of original code
}
```

#### 4.4 BotManager.cs - Premature Match End Fix
**File:** `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/BotManager.cs`

**Problem:** `CheckBotQuickComplete()` ended match immediately because no human players were in activePlayerList

**Fix:**
```csharp
// Line 13: New tracking flag
[HideInInspector] public bool humanPlayerEverConnected = false;

// Lines 80-88: Track human connection
public void CheckBotQuickComplete()
{
    // Track if a human player has ever connected
    if (activePlayerList.Count > 0)
    {
        humanPlayerEverConnected = true;
    }

    // Only trigger quick complete if a human was connected and then left
    if (activePlayerList.Count == 0 && !matchEnded && humanPlayerEverConnected)
    {
        GameManager.Instance.EndGame(winnerIndex, loserIndex, EndReason.PLAYER_LEFT);
    }
}
```

---

### Phase 3: Port Configuration (~17:25 UTC)

#### 4.5 GameManager.cs - Hardcoded Port
**File:** `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/GameManager.cs`

**Problem:** Unity scene serialization was overriding the port value to 7777 instead of 6006

**Fix:**
```csharp
// Lines 94-101: Hardcode port to avoid scene override
if (useTestMode)
{
    Debug.Log("[GameManager] Using TEST MODE - bypassing MatchKeeper");
    // Hardcode port 6006 to avoid scene serialization override
    TestModeManager.Initialize(6006, testMatchType, true, testIsFirstMatch);
    TestModeManager.LogSessionIds();
}
```

---

### Phase 4: Match State Fix (~17:40 UTC)

#### 4.6 GameManager.cs - StartMatchTeleport Bypass
**File:** `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/GameManager.cs`

**Problem:** During TELEPORT→MATCH transition, `StartMatchTeleport()` called `EndGame()` because `playerList.Count != GetMatchMaxPlayers()` (only bot was connected, expecting 2 players)

**Root Cause Analysis:**
```
Match State Flow: NONE → PREMATCH → TELEPORT → MATCH
                                      ↓
                          StartMatchTeleport() checks player count
                                      ↓
                          Only 1 player (bot) ≠ 2 expected
                                      ↓
                          EndGame() called prematurely
```

**Fix:**
```csharp
// Lines 166-200: Test mode bypass
public void StartMatchTeleport()
{
    // In test mode, skip player count validation - wait for human to connect
    if (useTestMode)
    {
        foreach(Player player in PlayerManager.playerList.Values)
        {
            player.playerData.willPower = player.playerStats.willPower;
            player.playerData.stamina = player.playerStats.stamina;
        }
        return; // Skip validation, let match proceed
    }

    // Original validation code (for production with MatchKeeper)
    if (playerList.Count != GetMatchMaxPlayers())
    {
        EndGame(0, 0, EndReason.PLAYER_LEFT);
        return;
    }
    // ... rest of teleport logic
}
```

#### 4.7 GameManager.cs - CheckMatchEndCondition Guard
**File:** `AUM-Unity-Server-Legacy/Assets/Scripts/Managers/GameManager.cs`

**Additional safety:**
```csharp
// Lines 462-466
public void CheckMatchEndCondition()
{
    // In test mode, don't end match until a human has connected at least once
    if (useTestMode && BotManager != null && !BotManager.humanPlayerEverConnected)
    {
        return;
    }

    // ... win condition checks
}
```

---

## 5. DEPLOYMENT PROCESS

### 5.1 Build Server (Unity)
```
1. Open Unity project: AUM-Unity-Server-Legacy
2. File → Build Settings
3. Target Platform: Linux
4. Architecture: x86_64
5. Server Build: Checked
6. Build to: /Users/mac/Documents/GitHub/server legacy/
```

### 5.2 Deploy to Hetzner
```bash
# Create tarball
cd "/Users/mac/Documents/GitHub"
tar -czvf server-legacy.tar.gz "server legacy"

# Upload to server
sshpass -p 'brahman' scp server-legacy.tar.gz root@65.109.133.129:/root/

# Extract on server
sshpass -p 'brahman' ssh root@65.109.133.129 "cd /root && rm -rf server && tar -xzvf server-legacy.tar.gz && mv 'server legacy' server"
```

### 5.3 Start Server
```bash
# Kill any existing server
sshpass -p 'brahman' ssh root@65.109.133.129 "pkill -f 'server legacy' || true"

# Start new server
sshpass -p 'brahman' ssh root@65.109.133.129 "cd /root/server && chmod +x 'server legacy.x86_64' && nohup './server legacy.x86_64' -logFile /root/server.log -batchmode -nographics > /dev/null 2>&1 &"
```

### 5.4 Verify Server
```bash
# Check process
sshpass -p 'brahman' ssh root@65.109.133.129 "ps aux | grep legacy"

# Check logs
sshpass -p 'brahman' ssh root@65.109.133.129 "tail -50 /root/server.log"
```

---

## 6. FINAL SERVER STATE

### Server Logs (Success)
```
[GameManager] Using TEST MODE - bypassing MatchKeeper
[TestMode] Initializing test match - Port:6006 Type:SOLO_1V1 Bot:True FirstMatch:False
Server Socket has been intiialized Port:6006
[TestMode] Added avatar: TestPlayer1 (ID:1, Team:0, Bot:False, Session:3d46e7bc-914e-fca2-c3ae-1ae23d72aa34)
[TestMode] Added avatar: TestBot (ID:2, Team:1, Bot:True, Session:d69717f4-e785-49f3-f80b-823fb889dd45)
[TestMode] Match ready - waiting for client connections
[2][TestBot] - Logged in as MukthaMuktha (Shiva) Team: 1 Bot:True
Bot functionality initialized for TestBot [MukthaMuktha]
```

### Connection Details
| Parameter | Value |
|-----------|-------|
| Server IP | 65.109.133.129 |
| Server Port | 6006 |
| Protocol | UDP (LiteNetLib) |
| Player 1 Session | 3d46e7bc-914e-fca2-c3ae-1ae23d72aa34 |
| Bot Session | d69717f4-e785-49f3-f80b-823fb889dd45 |

---

## 7. CLIENT CONFIGURATION

### TestModeClient Settings
```csharp
public static string serverIP = "65.109.133.129";
public static int serverPort = 6006;
```

### Build Client (Unity)
```
1. Open Unity project: AUM-Unity-Staging-Legacy
2. Ensure TestModeClient.cs has correct IP/port
3. File → Build Settings
4. Target Platform: Windows (for testing on Windows PC)
5. Build and run
```

### Known Client Issue
Mac cannot run the legacy client due to ARM64/x86_64 native DLL mismatch in LiteNetLib. Testing must be done from Windows PC.

---

## 8. RESULTS SUMMARY

### Achieved
| Goal | Status |
|------|--------|
| Server runs on Hetzner | ✅ Running on 65.109.133.129:6006 |
| Server waits for human | ✅ No premature EndGame |
| Bot initializes correctly | ✅ MukthaMuktha + Shiva ready |
| Session IDs match | ✅ Deterministic MD5 GUIDs |

### Pending
| Task | Status |
|------|--------|
| Client connection test | ⏳ Needs Windows PC |
| Gameplay verification | ⏳ After client connects |
| Addressables loading | ⚠️ May need client-side fixes |

---

## 9. LESSONS LEARNED

### 1. Scene Serialization Overrides Code
Unity scene values can override script defaults. When debugging "why isn't my value being used", check the scene inspector.

### 2. Match State Machine Complexity
The legacy code has multiple places that can trigger `EndGame()`:
- BotManager.CheckBotQuickComplete()
- GameManager.StartMatchTeleport()
- GameManager.CheckMatchEndCondition()
- MKManager.SendMKMatchEnd()

Each needed a test mode bypass.

### 3. Session UUID Matching is Critical
Client and server must use identical session UUIDs. Using MD5 hash of deterministic strings ensures matching.

### 4. Iterative vs Holistic Debugging
Initial iterative approach (fix one error → find next) was frustrating. A comprehensive code flow analysis would have identified all issues upfront:
```
Client Connect → Server Auth → Match State → Teleport → Match Start
                                    ↓
                              Multiple EndGame() triggers
```

---

## 10. FILES MODIFIED

### Server (AUM-Unity-Server-Legacy)
| File | Changes |
|------|---------|
| GameManager.cs | Test mode init, port hardcode, StartMatchTeleport bypass, CheckMatchEndCondition guard |
| BotManager.cs | humanPlayerEverConnected tracking |
| MKManager.cs | Null check for test mode |
| TestModeManager.cs | New file - test match setup |

### Client (AUM-Unity-Staging-Legacy)
| File | Changes |
|------|---------|
| TestModeClient.cs | New file - direct connection setup |
| SessionManager.cs | skipWebSocket flag integration |

---

## 11. NEXT STEPS

1. **Build Windows Client**
   - Open AUM-Unity-Staging-Legacy in Unity
   - Build for Windows Standalone
   - Transfer to Windows PC

2. **Test Connection**
   - Run client on Windows
   - Verify authentication packet sent
   - Check server logs for player connection

3. **Verify Gameplay**
   - Test combat against bot
   - Verify damage registration
   - Check state synchronization

4. **Document Results**
   - Update this document with test results
   - Note any additional fixes needed

---

*Document generated: January 19, 2026*
*Server Status: RUNNING (65.109.133.129:6006)*
