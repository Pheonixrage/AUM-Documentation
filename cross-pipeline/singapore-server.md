# Singapore Server — 5.223.55.127

**Purpose:** P2 Staging (Elemental Progression) + P1 Nakama
**Provider:** Hetzner Cloud (Singapore region)

---

## Access

| Key | Value |
|-----|-------|
| IP | `5.223.55.127` |
| SSH | `ssh root@5.223.55.127` |
| SSH Key | `~/.ssh/id_ed25519` (key-only, password auth disabled) |
| Security | fail2ban enabled (3 failed SSH = 1hr ban) |

---

## Services

| Service | Port | Protocol | Purpose | Command |
|---------|------|----------|---------|---------|
| `aum-dev.service` | 7777 | UDP | P2 elemental progression game server | `systemctl restart aum-dev` |
| `aum-orchestrator.service` | 8080 | TCP | P2 orchestrator (Python) | `systemctl restart aum-orchestrator` |
| Nakama (Docker) | 7350-7352 | TCP/UDP | P1 V2 infrastructure | **NEVER TOUCH** |
| MIND V2 (Docker) | 7800 | UDP | P1 V2 test server (Mar 25 deploy) | Docker managed |

---

## PlayFab Credentials (Staging Title)

| Key | Value |
|-----|-------|
| Title ID | `1A4AA8` |
| Secret Key | `PQZKY3G1Q8SNM5U8QZCSJBSN3GHHZK8K44FCN9SSZFQST46DWJ` |
| CloudScript | Rev 7 (61 handlers, Singapore orchestrator) |
| Catalog Items | 305 (copied from DEV Mar 7) |
| Matchmaking Queues | 7 |
| Virtual Currencies | 8 |
| Title Data Keys | 17 |

---

## Directories

| Path | Contents |
|------|----------|
| `/root/aum-server-dev/` | P2 game server binary + Server_Data |
| `/root/orchestrator/` | Orchestrator Python service |
| `/root/orchestrator/logs/orchestrator.log` | Orchestrator logs |

---

## Firewall Rules (ufw)

| Port | Protocol | Purpose |
|------|----------|---------|
| 22 | TCP | SSH |
| 6006 | UDP | Legacy dev (unused) |
| 7350-7352 | TCP/UDP | Nakama |
| 7777 | UDP | P2 game server |
| 7800 | UDP | MIND V2 test |
| 8080 | TCP | Orchestrator API |

---

## Common Commands

```bash
# Check service status
systemctl status aum-dev
systemctl status aum-orchestrator

# Restart services
systemctl restart aum-dev
systemctl restart aum-orchestrator

# View logs
journalctl -u aum-dev -f
journalctl -u aum-orchestrator -f
tail -f /root/orchestrator/logs/orchestrator.log

# Server launch args (aum-dev.service)
# -playfabTitleId 1A4AA8 -port 7777
```

---

## Client Config (P2 — AUMAuthConfig.asset)

- `buildMode: 1` = Staging (1A4AA8)
- `orchestratorUrl: http://5.223.55.127:8080`
- Branch: `elemental-progression`

---

## Safety Notes

- **NEVER touch Nakama** (P1 infrastructure, Docker ports 7350-7352)
- This is **staging only** — not production. Production is Helsinki (`65.109.133.129`)
- Server was security-hardened Feb 25, 2026 (crypto miner incident, verified clean)

---

*Last updated: April 8, 2026*
