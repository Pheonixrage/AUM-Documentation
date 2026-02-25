# Security Incident Report: Crypto Miner Attack on Helsinki Production Server

**Date:** February 25, 2026
**Severity:** High
**Status:** Resolved
**Affected Server:** Helsinki Production (`65.109.133.129`)

---

## Executive Summary

At 04:12 UTC on February 25, 2026, an automated attacker from a Hong Kong VPS (`154.51.63.183`) brute-forced the SSH root password (`brahman`) on the Helsinki production server and installed a Monero (XMR) crypto miner. The miner consumed 194% CPU and 2.4GB of 3.8GB RAM, causing game server OOM kills, stutter, and desync for production iOS/Play Store players. The attack was detected ~2 hours later, the miner was removed, and the server was fully hardened.

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| **04:12:18** | Attacker SSH login #1 from `154.51.63.183` (port 41448) |
| **04:12:22** | Attacker SSH login #2 (port 41456) — parallel session |
| **04:12:38** | Attacker SSH login #3 (port 51990) |
| **04:12:18-51** | Automated script installs XMRig miner (33 seconds total) |
| **~04:13** | Miner starts consuming 194% CPU + 2.4GB RAM |
| **~04:15+** | Game servers begin OOM-killed (exit code -9) |
| **~04:30+** | Players on iOS/Play Store start experiencing stutter and desync |
| **~05:48** | Investigation begins via SSH |
| **~05:55** | Crypto miner (`systemp`) discovered in process list |
| **~05:58** | Miner processes killed, services stopped and removed |
| **~06:00** | Root password changed, malicious files deleted |
| **~06:07** | fail2ban installed, SSH password auth disabled |
| **~06:11** | Hetzner rescue mode used to add Mac SSH key to authorized_keys |
| **~06:16** | Server rebooted with security updates applied |
| **~06:22** | Singapore server hardened (was clean, no compromise) |
| **~06:26** | All services restored and verified |

---

## Attacker Profile

| Detail | Value |
|--------|-------|
| **IP Address** | `154.51.63.183` |
| **Location** | Cheung Sha Wan, Hong Kong |
| **ISP** | UCloud Information Technology (HK) Limited |
| **ASN** | AS135377 |
| **Domain** | `ucloud.cn` (Chinese cloud hosting provider) |
| **Infrastructure Type** | Rented VPS — used as attack node, not the attacker's real location |
| **Attack Type** | Automated SSH brute-force + crypto miner deployment |
| **Dwell Time** | 33 seconds (fully scripted, no manual interaction) |

### Attack Sequence (Reconstructed from journalctl)

1. SSH brute-force of password `brahman` (dictionary word)
2. Install `msr-tools` package
3. Run `randomx_boost.sh` (CPU optimization for mining)
4. Run `enable_1gb_pages.sh` (memory page optimization)
5. Rename `xmrig` binary to `systemp` (disguise)
6. Install `free_proc.sh` (watchdog script) and `.config.json` (miner config)
7. Create `systemp.service` (systemd, auto-start, "System Proxy Service")
8. Create `observed.service` (systemd, watchdog to restart miner if killed)
9. Enable and start both services
10. Delete `~/.bash_history` to cover tracks

### Miner Configuration

| Setting | Value |
|---------|-------|
| Software | XMRig 6.25.0 |
| Cryptocurrency | Monero (XMR) |
| Pool | `xmr.kryptex.network:8029` (Kryptex) |
| Algorithm | RandomX (rx/0) |
| Threads | 2 |
| Hashrate | ~430 H/s |
| RAM Usage | 2.4GB (61% of server) |
| CPU Usage | 194% (nearly both cores) |

---

## Impact

| Area | Impact |
|------|--------|
| **Production Players** | ~2 hours of stutter, desync, and connection issues |
| **Game Servers** | OOM-killed repeatedly (exit code -9, 2.2GB+ RAM usage) |
| **Player Data** | **SAFE** — PlayFab is cloud-hosted, untouched |
| **Game Binaries** | **SAFE** — prod and dev binaries verified by timestamps |
| **Orchestrator** | **SAFE** — config untouched, still pointing to correct paths |
| **Source Code** | **SAFE** — not stored on production server |
| **Financial** | Minimal — attacker mined ~$0.50-1.00 of XMR in 2 hours |

---

## Remediation Actions Taken

### Immediate (During Incident)
- [x] Killed miner processes (PID 2321594, 2321647)
- [x] Stopped and disabled `systemp.service` and `observed.service`
- [x] Deleted malicious files: `/usr/local/bin/systemp`, `free_proc.sh`, `.config.json`
- [x] Removed systemd service files from `/etc/systemd/system/`
- [x] Changed root password from `brahman` to `AUM_Prod_2026_Kx9Mn!`

### Hardening (Post-Incident)

#### Helsinki (`65.109.133.129`)
- [x] Disabled SSH password authentication (`PasswordAuthentication no`)
- [x] Set `PermitRootLogin prohibit-password` (key-only)
- [x] Installed and configured fail2ban (3 attempts → 1 hour ban)
- [x] Added Mac SSH key to `authorized_keys`
- [x] Applied 72 pending security updates (including kernel)
- [x] Rebooted server
- [x] Disabled nginx (was auto-enabled by apt upgrade, conflicted with orchestrator port 8080)
- [x] Fixed dev server service path (`/root/aum-server/` → `/root/aum-server-dev/`)
- [x] Stopped crash-looping dev service (was at 168,699 restart count)

#### Singapore (`5.223.55.127`)
- [x] Verified clean — no compromise found
- [x] Installed and configured fail2ban
- [x] Disabled SSH password authentication
- [x] Fixed cloud-init override (`/etc/ssh/sshd_config.d/50-cloud-init.conf`)
- [x] Applied 69 pending security updates
- [ ] Pending: Reboot for kernel updates (game servers running)

---

## Root Cause

**Weak SSH password (`brahman`)** on a public-facing server with password authentication enabled. The server was under constant brute-force attack from dozens of IPs worldwide. The password was a common dictionary word, making it trivially crackable.

---

## Lessons Learned

1. **Never use dictionary passwords for SSH** — or better, disable password auth entirely
2. **SSH key-only authentication should be default** for all production servers
3. **fail2ban should be installed on day one** of any public server
4. **Security updates should be applied regularly** — 68+ pending updates is too many
5. **Monitor server resource usage** — a sudden spike in CPU/RAM should trigger alerts
6. **The attacker didn't target AUM specifically** — this was an automated botnet sweep. Any server with a weak password would have been hit.

---

## Current Server Security Status

### Helsinki Production (`65.109.133.129`)

| Setting | Value |
|---------|-------|
| SSH Auth | Key-only (password disabled) |
| PermitRootLogin | `prohibit-password` |
| fail2ban | Active, sshd jail (3 attempts → 1hr ban) |
| Security Updates | Applied (Feb 25, 2026) |
| Kernel | 6.8.0-100-generic (rebooted) |
| Root Password | `AUM_Prod_2026_Kx9Mn!` (only works on local console, not SSH) |

### Singapore Dev (`5.223.55.127`)

| Setting | Value |
|---------|-------|
| SSH Auth | Key-only (password disabled) |
| PermitRootLogin | `prohibit-password` |
| fail2ban | Active, sshd jail (3 attempts → 1hr ban) |
| Security Updates | Applied (Feb 25, 2026) |
| Kernel | Pending reboot for kernel update |

---

## Authorized SSH Keys (Both Servers)

| Key | Owner | Type |
|-----|-------|------|
| `ssh-rsa ...JJPOIQ==` | `PC_01@Mohan` | RSA (older PC) |
| `ssh-ed25519 ...HJVKQ` | `mohan@brahmanstudios.com` | Ed25519 (secondary) |
| `ssh-ed25519 ...EyTl` | `mohan@brahmanstudios.com` | Ed25519 (current Mac) |

---

*Report prepared: February 25, 2026*
*Investigators: Claude Code (Opus 4.6)*
