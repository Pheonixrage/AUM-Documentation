# Hetzner Server Deployment Guide

**Last Updated:** January 24, 2026
**Server:** 65.109.133.129 (Ubuntu 4GB VPS - Hel1)

---

## Table of Contents

1. [Server Overview](#server-overview)
2. [Directory Structure](#directory-structure)
3. [Deployed Servers](#deployed-servers)
4. [Match Orchestrator](#match-orchestrator)
5. [Deployment Workflow](#deployment-workflow)
6. [Management Commands](#management-commands)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)

---

## Server Overview

### Connection Details
```
Host: 65.109.133.129
User: root
Password: brahman
SSH: ssh root@65.109.133.129
```

### Installed Services
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| aum-jan24 | 7777 | Direct Mac build server | Active (systemd) |
| aum-orchestrator | 8080 | Match allocation API | Active (systemd) |

### Firewall Ports
- **7777** (UDP) - Direct server connection
- **7800-7899** (UDP) - Orchestrated match servers
- **8080** (TCP) - Orchestrator HTTP API

---

## Directory Structure

```
/opt/
├── mac-build/                  # Mac-compiled Linux server
│   ├── Server.x86_64          # Main executable
│   ├── GameAssembly.so        # IL2CPP compiled game code
│   ├── UnityPlayer.so         # Unity runtime
│   ├── Server_Data/           # Game data (scenes, assets, etc.)
│   └── Server_BackUpThisFolder_ButDontShipItWithYourGame/
│
├── windows-build/              # Windows-compiled Linux server
│   ├── Server.x86_64          # (Deploy from Windows workspace)
│   ├── GameAssembly.so
│   ├── UnityPlayer.so
│   ├── Server_Data/
│   └── Server_BackUpThisFolder_ButDontShipItWithYourGame/
│
└── aum-orchestrator/
    ├── orchestrator.py        # Match allocation service
    └── logs/                  # Orchestrator logs

/var/log/aum/
├── mac-build.log              # Direct server logs
└── orchestrator.log           # Orchestrator logs (also in journal)

/etc/systemd/system/
├── aum-jan24.service          # Mac build systemd service
└── aum-orchestrator.service   # Orchestrator systemd service
```

---

## Deployed Servers

### Mac Build Server (Jan 24, 2026)

**Build Info:**
- Compiled from: AUM-Headless on macOS
- Unity Version: 2022.3.62f2
- Target Platform: Linux64 (Dedicated Server)
- Build Date: January 24, 2026
- Fixes Included:
  - StateManager idempotent registration
  - Stamina regeneration trap fix
  - Focus logging improvements
  - Defensive state checks

**Systemd Service:**
```ini
[Unit]
Description=AUM Mac Build Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mac-build
ExecStart=/opt/mac-build/Server.x86_64 -batchmode -nographics -port 7777 -matchtype 1 -minplayers 1 -logfile /var/log/aum/mac-build.log
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Direct Connection:**
- IP: `65.109.133.129`
- Port: `7777` (UDP)
- Match Type: Solo_1v1 (ServerAuthority)
- Min Players: 1

### Windows Build Server (Pending Deployment)

**Deployment Steps:**
1. Build from Windows workspace (AUM-Headless)
2. Target: Linux64 (Dedicated Server)
3. Package: `tar -czf windows-build.tar.gz Server.x86_64 Server_Data/ Server_BackUpThisFolder_ButDontShipItWithYourGame/ GameAssembly.so UnityPlayer.so`
4. Upload: `scp windows-build.tar.gz root@65.109.133.129:/tmp/`
5. Extract: `ssh root@65.109.133.129 'cd /opt/windows-build && tar -xzf /tmp/windows-build.tar.gz'`
6. Set permissions: `chmod +x /opt/windows-build/Server.x86_64`

**NOTE:** Both "Mac build" and "Windows build" are **Linux executables** (.x86_64). The names refer to the development environment used for compilation, not the target platform.

---

## Match Orchestrator

### Overview
The orchestrator is a Flask-based HTTP API that dynamically spawns and manages game server instances on demand.

### API Details

**Base URL:** `http://65.109.133.129:8080`
**API Key:** `AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8`
**Required Header:** `X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8`

### Endpoints

#### 1. Health Check
```bash
GET /health

# Example
curl -X GET http://65.109.133.129:8080/health \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8"

# Response
{
  "status": "ok",
  "active_servers": 0,
  "available_builds": ["mac", "windows"]
}
```

#### 2. Allocate Server
```bash
POST /allocate

# Request Body
{
  "matchType": "SOLO_1V1",      // See Match Types below
  "minPlayers": 1,              // Minimum players to start
  "buildType": "mac",           // "mac" or "windows"
  "matchId": "uuid-optional"    // Optional, auto-generated if omitted
}

# Example - Allocate Mac Build
curl -X POST http://65.109.133.129:8080/allocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{
    "matchType": "SOLO_1V1",
    "minPlayers": 1,
    "buildType": "mac"
  }'

# Response
{
  "success": true,
  "ip": "65.109.133.129",
  "port": 7800,
  "matchId": "4f141059-91dd-41ef-9d20-4b7673730fd6",
  "buildType": "mac"
}

# Example - Allocate Windows Build
curl -X POST http://65.109.133.129:8080/allocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{
    "matchType": "DUO_2V2",
    "minPlayers": 2,
    "buildType": "windows"
  }'
```

#### 3. Deallocate Server
```bash
POST /deallocate

# Request Body
{
  "port": 7800
}

# Example
curl -X POST http://65.109.133.129:8080/deallocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{"port": 7800}'

# Response
{
  "success": true
}
```

#### 4. List Active Servers
```bash
GET /servers

# Example
curl -X GET http://65.109.133.129:8080/servers \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8"

# Response
{
  "servers": [
    {
      "port": 7800,
      "match_id": "4f141059-91dd-41ef-9d20-4b7673730fd6",
      "build_type": "mac",
      "match_type": "SOLO_1V1"
    },
    {
      "port": 7801,
      "match_id": "abc123-def456",
      "build_type": "windows",
      "match_type": "DUO_2V2"
    }
  ],
  "count": 2
}
```

### Match Types

| Match Type | Integer | Description |
|------------|---------|-------------|
| SOLO_1V1 | 1 | 1 player vs 1 bot |
| SOLO_1V2 | 2 | 1 player vs 2 bots |
| SOLO_1V5 | 4 | 1 player vs 5 bots |
| DUO_2V2 | 8 | 2 players vs 2 bots |
| DUO_2V4 | 16 | 2 players vs 4 bots |
| TRIO_3V3 | 32 | 3 players vs 3 bots |
| TRAINING | 64 | Training mode |
| TUTORIAL | 128 | Tutorial mode |
| FIRST_MATCH | 256 | First match experience |

### Port Allocation

- **Base Port:** 7800
- **Max Servers:** 100
- **Port Range:** 7800-7899
- Ports are allocated sequentially and reused when servers are deallocated

### Error Responses

```json
// Unauthorized
{
  "error": "Unauthorized"
}

// Invalid build type
{
  "error": "Invalid buildType. Available: ['mac', 'windows']"
}

// Build not deployed
{
  "error": "windows build not deployed yet at /opt/windows-build/Server.x86_64"
}

// No available ports
{
  "error": "No available ports"
}

// Server not found (deallocate)
{
  "error": "Server not found"
}
```

---

## Deployment Workflow

### Mac Build Deployment

**From Mac Development Machine:**

1. **Build Server**
   ```bash
   cd /Users/mac/Documents/GitHub/AUM-Headless
   # Unity Editor → File → Build Settings → Linux → Build
   # Or use batch mode build command
   ```

2. **Package Build**
   ```bash
   cd /Users/mac/Documents/GitHub/AUM-Headless/Build
   tar -czf mac-build.tar.gz \
     "23rd Mac build server.x86_64" \
     "23rd Mac build server_Data" \
     "23rd Mac build server_BackUpThisFolder_ButDontShipItWithYourGame" \
     GameAssembly.so \
     UnityPlayer.so
   ```

3. **Upload to Hetzner**
   ```bash
   SSHPASS='brahman' sshpass -e scp mac-build.tar.gz root@65.109.133.129:/tmp/
   ```

4. **Deploy on Server**
   ```bash
   SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 << 'EOF'
   systemctl stop aum-jan24
   cd /opt/mac-build
   rm -rf *
   tar -xzf /tmp/mac-build.tar.gz
   mv "23rd Mac build server.x86_64" Server.x86_64
   mv "23rd Mac build server_Data" Server_Data
   mv "23rd Mac build server_BackUpThisFolder_ButDontShipItWithYourGame" Server_BackUpThisFolder_ButDontShipItWithYourGame
   chmod +x Server.x86_64
   systemctl start aum-jan24
   EOF
   ```

5. **Verify Deployment**
   ```bash
   SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
     'systemctl status aum-jan24 && netstat -tulnp | grep 7777'
   ```

### Windows Build Deployment

**From Windows Development Machine:**

1. **Build Server**
   ```cmd
   cd C:\path\to\AUM-Headless
   # Unity Editor → File → Build Settings → Linux → Build
   ```

2. **Package Build** (use WSL or Git Bash)
   ```bash
   cd /path/to/AUM-Headless/Build
   tar -czf windows-build.tar.gz \
     Server.x86_64 \
     Server_Data \
     Server_BackUpThisFolder_ButDontShipItWithYourGame \
     GameAssembly.so \
     UnityPlayer.so
   ```

3. **Upload to Hetzner**
   ```bash
   scp windows-build.tar.gz root@65.109.133.129:/tmp/
   # Password: brahman
   ```

4. **Deploy on Server**
   ```bash
   ssh root@65.109.133.129
   cd /opt/windows-build
   tar -xzf /tmp/windows-build.tar.gz
   chmod +x Server.x86_64
   exit
   ```

5. **Verify Orchestrator Detects It**
   ```bash
   curl -X GET http://65.109.133.129:8080/health \
     -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8"
   # Should show "available_builds": ["mac", "windows"]
   ```

---

## Management Commands

### Server Control

```bash
# Start Mac build server
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl start aum-jan24'

# Stop Mac build server
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl stop aum-jan24'

# Restart Mac build server
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl restart aum-jan24'

# Check Mac build server status
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl status aum-jan24'

# View Mac build server logs (live)
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -f /var/log/aum/mac-build.log'
```

### Orchestrator Control

```bash
# Start orchestrator
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl start aum-orchestrator'

# Stop orchestrator
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl stop aum-orchestrator'

# Restart orchestrator
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl restart aum-orchestrator'

# Check orchestrator status
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl status aum-orchestrator'

# View orchestrator logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-orchestrator -f'
```

### Kill All Orchestrated Servers

```bash
# Kill all spawned servers (not the direct server on 7777)
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'pkill -f "port 78"'
```

### Check Active Servers

```bash
# List all running servers
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ps aux | grep Server.x86_64 | grep -v grep'

# Check listening ports
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'netstat -tulnp | grep -E "777|780"'
```

---

## Monitoring & Logs

### Direct Server Logs

```bash
# View last 100 lines
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -100 /var/log/aum/mac-build.log'

# Follow live logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -f /var/log/aum/mac-build.log'

# Search for errors
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'grep -i error /var/log/aum/mac-build.log'

# Search for specific player
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'grep "PlayerName" /var/log/aum/mac-build.log'
```

### Orchestrator Logs

```bash
# View systemd journal logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-orchestrator -n 100'

# Follow live orchestrator logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-orchestrator -f'

# View orchestrator log file
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -100 /opt/aum-orchestrator/orchestrator.log'
```

### System Health

```bash
# Check CPU/Memory usage
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'top -b -n 1 | head -20'

# Check disk space
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'df -h'

# Check network connections
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ss -tunap | grep Server'
```

---

## Troubleshooting

### Server Won't Start

**Symptom:** `systemctl status aum-jan24` shows failed

**Check:**
```bash
# View detailed error
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-jan24 -n 50'

# Verify executable exists and has execute permission
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ls -la /opt/mac-build/Server.x86_64'

# Try running manually to see error
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
  'cd /opt/mac-build && ./Server.x86_64 -batchmode -nographics -port 7777'
```

**Common Fixes:**
- Missing execute permission: `chmod +x /opt/mac-build/Server.x86_64`
- Port already in use: Check for zombie processes with `ps aux | grep Server.x86_64`
- Missing libraries: Check error log for "cannot open shared object file"

### Port Already in Use

**Symptom:** Server starts but doesn't listen on port

**Check:**
```bash
# Find what's using the port
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'lsof -i :7777'

# Kill the process
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'kill <PID>'
```

### Orchestrator Not Spawning Servers

**Symptom:** `/allocate` returns error 503

**Check:**
```bash
# Verify build exists
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ls -la /opt/mac-build/Server.x86_64'

# Check orchestrator logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-orchestrator -n 50'

# Test manual spawn
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
  '/opt/mac-build/Server.x86_64 -batchmode -nographics -port 7800 -matchtype 1 -minplayers 1'
```

### Client Can't Connect

**Symptom:** Client times out connecting to server

**Check:**
```bash
# Verify server is listening
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'netstat -tulnp | grep 7777'

# Test connectivity from local machine
nc -u -v 65.109.133.129 7777

# Check firewall
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ufw status'
```

**Common Fixes:**
- Server not bound to 0.0.0.0: Check server startup logs
- Firewall blocking: `ufw allow 7777/udp`
- Client using wrong IP/port: Verify [LocalTestingSettings.asset](file:///Users/mac/Documents/GitHub/AUM-The-Epic/Assets/Resources/LocalTestingSettings.asset)

### Out of Ports

**Symptom:** `/allocate` returns "No available ports"

**Fix:**
```bash
# List all active servers
curl -X GET http://65.109.133.129:8080/servers \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8"

# Deallocate old servers
curl -X POST http://65.109.133.129:8080/deallocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{"port": 7800}'
```

### Server Crash Loop

**Symptom:** Server keeps restarting (systemd RestartSec=10)

**Check:**
```bash
# View crash logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-jan24 -n 200'

# Disable auto-restart temporarily
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl stop aum-jan24'
```

**Common Causes:**
- Corrupted build: Redeploy
- Missing dependencies: Check for library errors in logs
- Configuration error: Verify command line arguments in service file

---

## Client Configuration

### LocalTestingSettings.asset

For connecting to Hetzner server from Unity client:

```yaml
enableLocalTesting: 1
localServerIP: 65.109.133.129
localServerPort: 7777          # Direct server (or orchestrator-assigned port)
skipOrchestrator: 1             # 1 for direct, 0 for orchestrator
verboseLogging: 1
exportLogs: 1
```

### Orchestrator Integration

If using orchestrator allocation from client code:

```csharp
// Example: Request server allocation
var request = new AllocateRequest {
    matchType = "SOLO_1V1",
    minPlayers = 1,
    buildType = "mac"
};

var response = await OrchestratorAPI.AllocateServer(request);
// response.ip = "65.109.133.129"
// response.port = 7800 (example)
// Connect client to response.ip:response.port
```

---

## Security Notes

### Current Setup
⚠️ **WARNING:** This is a development/testing setup. For production:

1. **API Key:** Change `AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8` to environment variable
2. **Firewall:** Restrict orchestrator port 8080 to trusted IPs
3. **HTTPS:** Add TLS termination (nginx/caddy) for orchestrator
4. **Rate Limiting:** Add rate limits to prevent abuse
5. **Authentication:** Add player authentication before allocation

### Recommended Production Setup
```
Client → CloudFlare → Load Balancer → Orchestrator (HTTPS) → Game Servers
```

---

## Build Metadata

### Mac Build (Jan 24, 2026)

| Property | Value |
|----------|-------|
| Build Date | January 24, 2026 |
| Unity Version | 2022.3.62f2 |
| Scripting Backend | IL2CPP |
| Target Platform | Linux64 (Dedicated Server) |
| Compiled On | macOS |
| Deployment Path | `/opt/mac-build/` |
| Git Commit | (Check AUM-Headless repo) |

**Changes in This Build:**
- StateManager: Idempotent state registration (fixes duplicate Add exception)
- PlayerBase: Fixed stamina cooldown trap (-1f → 2f)
- PlayerManager: Removed negative cooldown check blocking regen
- Player.cs: Added focus consumption debug logging

### Windows Build (Pending)

| Property | Value |
|----------|-------|
| Build Date | TBD |
| Unity Version | 2022.3.x |
| Scripting Backend | IL2CPP |
| Target Platform | Linux64 (Dedicated Server) |
| Compiled On | Windows |
| Deployment Path | `/opt/windows-build/` |
| Git Commit | TBD |

---

## Quick Reference

### One-Liner Commands

```bash
# Check everything
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl status aum-jan24 aum-orchestrator && netstat -tulnp | grep -E "777|8080"'

# Restart everything
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl restart aum-jan24 aum-orchestrator'

# View all logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -50 /var/log/aum/mac-build.log && journalctl -u aum-orchestrator -n 50'

# Health check
curl -s http://65.109.133.129:8080/health -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" | jq
```

---

## Related Documentation

- [AUM-Headless Build Instructions](../AUM-Headless/README.md)
- [Networking Architecture](./../AUM-The-Epic/.claude/rules/networking.md)
- [Server Authority Guide](./../AUM-The-Epic/.claude/rules/combat-system.md)
- [Session Log: Jan 24 Fixes](../sessions/2026-01-24-server-fixes.md)

---

**Maintained By:** Development Team
**Contact:** (Add contact info)
**Last Review:** January 24, 2026
