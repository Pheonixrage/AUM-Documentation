# AUM Server Security & Access Guide

**Last Updated:** February 25, 2026
**Applies To:** Helsinki Production + Singapore Dev

---

## Server Inventory

| Server | IP | Location | Purpose | Hetzner ID |
|--------|----|----------|---------|------------|
| **Helsinki** | `65.109.133.129` | Helsinki, Finland | Production (live iOS/Play Store) | `115148857` |
| **Singapore** | `5.223.55.127` | Singapore | Dev/Staging | — |

---

## How to SSH In

### From This Mac (Authorized)

```bash
# Helsinki Production
ssh root@65.109.133.129

# Singapore Dev
ssh root@5.223.55.127
```

No password needed. Your SSH key at `~/.ssh/id_ed25519` authenticates automatically.

### From a New Machine

You MUST add the new machine's SSH public key to the server first:

```bash
# Step 1: On the NEW machine, get its public key
cat ~/.ssh/id_ed25519.pub
# (If no key exists: ssh-keygen -t ed25519 -C "your@email.com")

# Step 2: From an ALREADY authorized machine, add the new key
ssh root@65.109.133.129 "echo 'PASTE_THE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
ssh root@5.223.55.127 "echo 'PASTE_THE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
```

### If Locked Out (Emergency Access)

**Option 1: Hetzner Cloud Console (VNC)**
1. Go to https://console.hetzner.cloud
2. Login with Hetzner account
3. Select server → "Console" tab
4. Login with: `root` / `AUM_Prod_2026_Kx9Mn!`
5. Fix authorized_keys or unban your IP

**Option 2: Hetzner Rescue Mode (via API)**
```bash
# Hetzner API Token: S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY

# Enable rescue mode (returns temporary root password)
curl -s -X POST \
  -H "Authorization: Bearer S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY" \
  -H "Content-Type: application/json" \
  -d '{"type": "linux64"}' \
  "https://api.hetzner.cloud/v1/servers/115148857/actions/enable_rescue"

# Reboot into rescue
curl -s -X POST \
  -H "Authorization: Bearer S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY" \
  "https://api.hetzner.cloud/v1/servers/115148857/actions/reset"

# Wait 30s, then SSH with the temp password from step 1
ssh root@65.109.133.129

# Mount disk, fix authorized_keys
mount /dev/sda1 /mnt
echo 'NEW_KEY_HERE' >> /mnt/root/.ssh/authorized_keys
umount /mnt

# Disable rescue mode and reboot to normal
curl -s -X POST \
  -H "Authorization: Bearer S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY" \
  "https://api.hetzner.cloud/v1/servers/115148857/actions/disable_rescue"

curl -s -X POST \
  -H "Authorization: Bearer S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY" \
  "https://api.hetzner.cloud/v1/servers/115148857/actions/reset"
```

**Option 3: From another authorized machine, unban your IP**
```bash
ssh root@65.109.133.129 "fail2ban-client set sshd unbanip YOUR_BANNED_IP"
```

---

## Credentials & Tokens

| Credential | Value | Notes |
|------------|-------|-------|
| Helsinki root password | `AUM_Prod_2026_Kx9Mn!` | Only works on local/VNC console (SSH password auth is disabled) |
| Singapore root password | (original, unchanged) | SSH password auth is disabled |
| Hetzner API Token | `S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY` | Helsinki server management |
| Hetzner Helsinki Server ID | `115148857` | For API calls |
| PlayFab DEV Title | `15F2B7` | Secret: `JOAWWZ87KNU9KIXBTRG1PFXUHMGBSMQNSSMKKIR6F76GIIAFW3` |
| PlayFab PROD Title | `158C02` | Secret: `3YET9HU3F5ZBZ5FUQ3DEUOZECKPFDP1FEND8TKKUY5466DESZH` |
| Orchestrator API Key | `AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8` | For `/allocate` endpoint |

---

## Security Configuration

### SSH (`/etc/ssh/sshd_config`)

Both servers:
```
PermitRootLogin prohibit-password
PasswordAuthentication no
```

- Root can ONLY login with SSH keys
- Password authentication is completely disabled
- Singapore also has override fixed in `/etc/ssh/sshd_config.d/50-cloud-init.conf`

### fail2ban (`/etc/fail2ban/jail.local`)

Both servers:
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3        # 3 failed attempts
bantime = 3600      # 1 hour ban
findtime = 600      # within 10 minute window
```

**Useful fail2ban commands:**
```bash
# Check status
fail2ban-client status sshd

# Unban an IP
fail2ban-client set sshd unbanip 1.2.3.4

# Ban an IP manually
fail2ban-client set sshd banip 1.2.3.4

# Check all banned IPs
fail2ban-client get sshd banned
```

### Firewall (UFW) — Helsinki

```
22/tcp          SSH
80/tcp          HTTP (currently unused, nginx disabled)
443/tcp         HTTPS (currently unused, nginx disabled)
6006/udp+tcp    Dev game server
7850:7909/udp   Production game server pool
8080/tcp        Orchestrator API
8081/tcp        Orchestrator direct (backup)
```

---

## Service Architecture — Helsinki

```
CLIENT (iOS/Android/PC)
  │
  ├── POST https://65.109.133.129:8080/allocate
  │   └── Orchestrator (Python Flask, port 8080)
  │       ├── Groups players by matchId
  │       ├── 15s timeout → backfill bots
  │       └── Spawns game server on port 7850-7909
  │
  └── UDP connection to game server (port 7850-7909)
      └── Server.x86_64 (Unity IL2CPP headless)
          ├── 60Hz tick, server-authoritative
          └── Match lifecycle managed by orchestrator

DEV SERVER (direct connect, bypasses orchestrator)
  └── UDP to port 6006 → /root/aum-server-dev/Server.x86_64
      └── systemd service: aum-dev-6006.service
```

### Services (systemd)

| Service | Purpose | Status |
|---------|---------|--------|
| `aum-dev-6006.service` | Dev server on port 6006 | Enabled, auto-start |
| `fail2ban.service` | Brute-force protection | Enabled, auto-start |
| `nginx.service` | Reverse proxy (SSL) | **Disabled** — conflicts with orchestrator on 8080 |
| `ssh.service` | SSH server | Enabled, key-only auth |

### Orchestrator

The orchestrator runs as a foreground process (not a systemd service):
```bash
# Start orchestrator (from SSH or after reboot)
cd /root/orchestrator && nohup python3 orchestrator.py > /root/orchestrator/logs/orchestrator.log 2>&1 &

# Check health
curl http://65.109.133.129:8080/health

# View logs
tail -f /root/orchestrator/logs/orchestrator.log

# Stop
pkill -f orchestrator.py
```

**After server reboot, you must manually start the orchestrator.**

---

## Deployment Procedures

### Deploy Orchestrator (Python only — no Unity build needed)

```bash
# From local machine
scp /Users/mac/Documents/AUM-2.0\ Production/Server/orchestrator/orchestrator.py root@65.109.133.129:/root/orchestrator/

# SSH in and restart
ssh root@65.109.133.129
pkill -f orchestrator.py
cd /root/orchestrator && nohup python3 orchestrator.py > /root/orchestrator/logs/orchestrator.log 2>&1 &
curl http://localhost:8080/health
```

### Deploy Game Server (Requires Unity IL2CPP Build)

```bash
# ALL files must be deployed together
scp Server.x86_64 GameAssembly.so UnityPlayer.so root@65.109.133.129:/root/aum-server-prod/
scp -r Server_Data root@65.109.133.129:/root/aum-server-prod/

# For dev server
scp Server.x86_64 GameAssembly.so UnityPlayer.so root@65.109.133.129:/root/aum-server-dev/
scp -r Server_Data root@65.109.133.129:/root/aum-server-dev/

# Restart dev server after deploy
ssh root@65.109.133.129 "systemctl restart aum-dev-6006.service"
```

### Promote Dev to Prod

```bash
ssh root@65.109.133.129 "cp /root/aum-server-dev/* /root/aum-server-prod/ && cp -r /root/aum-server-dev/Server_Data /root/aum-server-prod/"
```

---

## Server Directories — Helsinki

```
/root/
├── aum-server-dev/           # Dev game server binary + data
│   ├── Server.x86_64
│   ├── GameAssembly.so
│   ├── UnityPlayer.so
│   ├── Server_Data/
│   └── logs/
│       └── dev-6006.log
├── aum-server-prod/          # Production game server binary + data
│   ├── Server.x86_64
│   ├── GameAssembly.so
│   ├── UnityPlayer.so
│   └── Server_Data/
├── orchestrator/
│   ├── orchestrator.py       # Flask app (port 8080)
│   └── logs/
│       └── orchestrator.log
└── .ssh/
    └── authorized_keys       # 3 SSH keys (PC_01, ed25519 secondary, Mac current)
```

---

## Monitoring & Health Checks

```bash
# Quick health check (run from local)
ssh root@65.109.133.129 "echo '--- Load ---' && cat /proc/loadavg && echo '--- Memory ---' && free -m | grep Mem && echo '--- Orchestrator ---' && curl -s http://localhost:8080/health && echo && echo '--- Game Servers ---' && ps aux | grep Server.x86 | grep -v grep | wc -l && echo '--- fail2ban ---' && fail2ban-client status sshd | grep banned"

# Check for suspicious processes
ssh root@65.109.133.129 "ps aux --sort=-%cpu | head -10"

# Check recent logins
ssh root@65.109.133.129 "last -10"

# Check failed login attempts
ssh root@65.109.133.129 "lastb | head -20"
```

---

## Routine Maintenance

### Apply Security Updates (Monthly)

```bash
ssh root@65.109.133.129 "apt-get update && apt-get upgrade -y"
ssh root@5.223.55.127 "apt-get update && apt-get upgrade -y"
# Reboot if kernel updated (check: needs-restarting or /var/run/reboot-required)
```

### Rotate SSH Keys (If Compromised)

```bash
# Generate new key on local machine
ssh-keygen -t ed25519 -C "mohan@brahmanstudios.com" -f ~/.ssh/id_ed25519_new

# Add new key via existing access
ssh root@65.109.133.129 "echo 'NEW_PUBLIC_KEY' >> ~/.ssh/authorized_keys"

# After verifying new key works, remove old key
ssh root@65.109.133.129 "sed -i '/OLD_KEY_FINGERPRINT/d' ~/.ssh/authorized_keys"
```

### After Server Reboot Checklist

1. SSH in: `ssh root@65.109.133.129`
2. Start orchestrator: `cd /root/orchestrator && nohup python3 orchestrator.py > logs/orchestrator.log 2>&1 &`
3. Verify health: `curl http://localhost:8080/health`
4. Check dev server: `systemctl status aum-dev-6006.service`
5. Check fail2ban: `fail2ban-client status sshd`
6. Check firewall: `ufw status`

---

*Guide created: February 25, 2026*
*Following security incident — see `2026-02-25-security-incident-crypto-miner.md` for full details*
