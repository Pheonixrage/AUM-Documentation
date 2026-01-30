# AUM Server Setup Documentation

**Comprehensive deployment and orchestration guides**

---

## Quick Links

### Primary Guides

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [**HETZNER-DEPLOYMENT.md**](./HETZNER-DEPLOYMENT.md) | Complete Hetzner server setup guide | First-time setup, troubleshooting, reference |
| [**ORCHESTRATOR-API-REFERENCE.md**](./ORCHESTRATOR-API-REFERENCE.md) | Quick API reference card | Client integration, testing |

---

## Quick Start

### For Developers

**Connect to Server:**
```yaml
# LocalTestingSettings.asset
localServerIP: 65.109.133.129
localServerPort: 7777
```

**Deploy New Mac Build:**
```bash
cd /Users/mac/Documents/GitHub/AUM-Headless/Build
tar -czf mac-build.tar.gz *
SSHPASS='brahman' sshpass -e scp mac-build.tar.gz root@65.109.133.129:/tmp/
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 << 'EOF'
systemctl stop aum-jan24
cd /opt/mac-build && rm -rf * && tar -xzf /tmp/mac-build.tar.gz
mv "23rd Mac build server.x86_64" Server.x86_64
mv "23rd Mac build server_Data" Server_Data
chmod +x Server.x86_64
systemctl start aum-jan24
EOF
```

**Test Orchestrator:**
```bash
curl -s http://65.109.133.129:8080/health \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" | jq
```

---

## Server Architecture

```
Hetzner VPS (65.109.133.129)
│
├── Direct Server (Port 7777)
│   └── /opt/mac-build/Server.x86_64
│       ├── Systemd managed (aum-jan24)
│       ├── Auto-restart on crash
│       └── Logs: /var/log/aum/mac-build.log
│
├── Orchestrator (Port 8080)
│   └── /opt/aum-orchestrator/orchestrator.py
│       ├── Flask HTTP API
│       ├── Spawns servers on 7800-7899
│       ├── Supports Mac/Windows builds
│       └── Logs: journalctl -u aum-orchestrator
│
└── Build Storage
    ├── /opt/mac-build/ (Deployed Jan 24, 2026)
    └── /opt/windows-build/ (Pending deployment)
```

---

## Documentation Index

### Setup & Deployment

1. **[HETZNER-DEPLOYMENT.md](./HETZNER-DEPLOYMENT.md)**
   - Full server overview
   - Directory structure
   - Deployment workflows (Mac/Windows)
   - Management commands
   - Monitoring & logs
   - Troubleshooting guide

2. **[ORCHESTRATOR-API-REFERENCE.md](./ORCHESTRATOR-API-REFERENCE.md)**
   - API endpoints (allocate, deallocate, list, health)
   - Request/response formats
   - Match types reference
   - C# client integration examples
   - Quick command reference

### Session Logs

- **[2026-01-24 Server Fixes](../sessions/2026-01-24-server-fixes-deployment.md)**
  - StateManager idempotent registration
  - Stamina regeneration trap fix
  - Focus logging improvements
  - Hetzner deployment process

### Change History

- **[CHANGELOG.md](../CHANGELOG.md)**
  - Jan 24: Server fixes + orchestrator updates
  - Historical changes across all projects

---

## Common Tasks

### Development Workflow

**1. Test Locally**
```bash
# Start local server
cd /Users/mac/Documents/GitHub/AUM-Headless/Build
./Server.x86_64 -batchmode -nographics -port 7777
```

**2. Build for Production**
```bash
# Unity Editor → File → Build Settings → Linux → Build
# Save to: AUM-Headless/Build/
```

**3. Deploy to Hetzner**
```bash
# Package
cd /Users/mac/Documents/GitHub/AUM-Headless/Build
tar -czf build.tar.gz *

# Upload
SSHPASS='brahman' sshpass -e scp build.tar.gz root@65.109.133.129:/tmp/

# Deploy
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
  'cd /opt/mac-build && systemctl stop aum-jan24 && rm -rf * && tar -xzf /tmp/build.tar.gz && systemctl start aum-jan24'
```

**4. Verify**
```bash
# Check service
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl status aum-jan24'

# Check logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -50 /var/log/aum/mac-build.log'
```

---

### Client Integration

**Direct Connection:**
```csharp
// LocalTestingSettings
localServerIP = "65.109.133.129";
localServerPort = 7777;
skipOrchestrator = true;

// Connect
NetworkManager.Connect("65.109.133.129:7777");
```

**Orchestrator Allocation:**
```csharp
var request = new AllocateRequest {
    matchType = "SOLO_1V1",
    minPlayers = 1,
    buildType = "mac"
};

var response = await OrchestratorAPI.AllocateServer(request);
NetworkManager.Connect($"{response.ip}:{response.port}");

// After match
await OrchestratorAPI.DeallocateServer(response.port);
```

---

### Monitoring

**Server Health:**
```bash
# Check all services
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
  'systemctl status aum-jan24 aum-orchestrator'

# Check ports
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
  'netstat -tulnp | grep -E "777|8080"'

# Active servers
curl -s http://65.109.133.129:8080/servers \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" | jq
```

**Logs:**
```bash
# Direct server
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'tail -f /var/log/aum/mac-build.log'

# Orchestrator
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-orchestrator -f'
```

---

## Troubleshooting Quick Reference

### Server Won't Start
```bash
# Check logs
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-jan24 -n 50'

# Verify executable
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ls -la /opt/mac-build/Server.x86_64'

# Try manual start
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 \
  'cd /opt/mac-build && ./Server.x86_64 -batchmode -nographics -port 7777'
```

### Port Conflict
```bash
# Find process using port
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'lsof -i :7777'

# Kill it
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'kill <PID>'
```

### Client Can't Connect
```bash
# Test port
nc -u -v 65.109.133.129 7777

# Check firewall
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'ufw status'
```

See [HETZNER-DEPLOYMENT.md](./HETZNER-DEPLOYMENT.md#troubleshooting) for detailed troubleshooting.

---

## Server Specifications

**Hetzner VPS:**
- **Provider:** Hetzner Cloud
- **Location:** Helsinki (hel1)
- **IP:** 65.109.133.129
- **RAM:** 4GB
- **OS:** Ubuntu 22.04 LTS
- **CPU:** Shared vCPU

**Services:**
- Direct Server: Systemd (aum-jan24)
- Orchestrator: Systemd (aum-orchestrator)
- Auto-restart: Enabled (10s delay)

---

## Build History

### Mac Build (Current - Jan 24, 2026)

| Property | Value |
|----------|-------|
| Unity Version | 2022.3.62f2 |
| Platform | Linux64 (Dedicated Server) |
| Scripting Backend | IL2CPP |
| Compiled On | macOS |
| Size | 117MB (compressed) |
| Path | /opt/mac-build/ |

**Key Fixes:**
- StateManager idempotent registration
- Stamina regeneration trap elimination
- Focus logging improvements

### Windows Build (Pending)

| Property | Value |
|----------|-------|
| Unity Version | 2022.3.x |
| Platform | Linux64 (Dedicated Server) |
| Scripting Backend | IL2CPP |
| Compiled On | Windows |
| Path | /opt/windows-build/ |

---

## Security

⚠️ **Development Setup - Not Production Ready**

**Current:**
- API Key in plaintext
- No rate limiting
- HTTP (not HTTPS)
- Root user access

**For Production:**
1. Environment variables for secrets
2. Rate limiting on orchestrator
3. HTTPS/TLS termination
4. Player authentication
5. Firewall IP whitelisting
6. Non-root service users
7. Log rotation
8. Monitoring alerts

---

## Support

### Getting Help

1. **Check logs first:** See [Monitoring & Logs](./HETZNER-DEPLOYMENT.md#monitoring--logs)
2. **Review troubleshooting:** See [Troubleshooting Guide](./HETZNER-DEPLOYMENT.md#troubleshooting)
3. **Session logs:** Check `sessions/` directory for historical issues
4. **CHANGELOG:** See recent changes that may affect deployment

### Updating Documentation

When deploying changes:
1. Update build metadata in [HETZNER-DEPLOYMENT.md](./HETZNER-DEPLOYMENT.md#build-metadata)
2. Add entry to [CHANGELOG.md](../CHANGELOG.md)
3. Create session log in `sessions/YYYY-MM-DD-description.md`
4. Update this README if workflow changes

---

## Related Documentation

### Project Documentation
- [AUM-The-Epic/.claude/](../../AUM-The-Epic/.claude/) - Client architecture & rules
- [AUM-Headless/](../../AUM-Headless/) - Server codebase
- [IMPLEMENTATION_STATE.md](../../AUM-The-Epic/IMPLEMENTATION_STATE.md) - Current work status

### External Resources
- [Unity Dedicated Server Docs](https://docs.unity3d.com/Manual/dedicated-server.html)
- [LiteNetLib Documentation](https://github.com/RevenantX/LiteNetLib)
- [Hetzner Cloud Docs](https://docs.hetzner.com/cloud/)

---

**Last Updated:** January 24, 2026
**Maintainer:** Development Team
