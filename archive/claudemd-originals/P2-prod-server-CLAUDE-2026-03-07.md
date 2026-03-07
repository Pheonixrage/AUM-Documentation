# AUM Server

**Repo:** `AUM-Unity-Server-Legacy` | **Branch:** `legacy-working-oct6` | **Unity 6 Headless (Linux IL2CPP)**

---

## Quick Reference

| Key | Value |
|-----|-------|
| Hetzner Helsinki | `65.109.133.129` (Production) / Hetzner ID: `115148857` |
| Singapore Dev | `5.223.55.127` (Dev/Staging) |
| SSH Access | **Key-only** — `ssh root@65.109.133.129` (no password, uses `~/.ssh/id_ed25519`) |
| Dev server | `/root/aum-server-dev/` port `6006` (systemd: `aum-dev-6006.service`) |
| Prod servers | `/root/aum-server-prod/` ports `7850-7909` (orchestrator-managed) |
| Orchestrator | `/root/orchestrator/` port `8080` / API key: `AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8` |
| Hetzner API Token | `S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY` |
| Root password | `AUM_Prod_2026_Kx9Mn!` (local/VNC console only, SSH password auth disabled) |
| PlayFab DEV | `15F2B7` / Secret: `JOAWWZ87KNU9KIXBTRG1PFXUHMGBSMQNSSMKKIR6F76GIIAFW3` / CloudScript rev 72 |
| PlayFab PROD | `158C02` / Secret: `3YET9HU3F5ZBZ5FUQ3DEUOZECKPFDP1FEND8TKKUY5466DESZH` / CloudScript rev 28 |
| Client repo | `c:\23rd Jan Reimport` / Branch: `legacy-working-oct29` |

---

## Architecture

```
CLIENT → UDP (LiteNetLib) → HEADLESS SERVER (this project)
                                ├── PlayerManager, BotManager, CombatManager, GameManager
                                ├── TestModeManager (direct connection, bypasses orchestrator)
                                └── 60Hz tick, server-authoritative
                            ↕
                       ORCHESTRATOR (orchestrator/orchestrator.py — Python, port 8080)
                            ├── POST /allocate — client requests server for match
                            ├── Pending match queue — groups by matchId
                            ├── Bot backfill — 15s timeout, fills remaining slots
                            └── Server spawning — ports 7850-7909
                            ↕
                       PLAYFAB (DEV: 15F2B7 / PROD: 158C02)
```

---

## Critical Files — DO NOT MODIFY Without Permission

`StateManager.cs` (FSM, must match client), `PlayerManager.cs` (Dheeraj's patterns), `Packet.cs` (network protocol), `BotManager.cs` (bot AI state machine)

---

## Orchestrator (`orchestrator/orchestrator.py`)

| Setting | Value |
|---------|-------|
| Endpoints | `POST /allocate`, `GET /health` |
| Server binary | `/root/aum-server-prod/Server.x86_64` |
| Port pool | 7850-7909 (UDP) |
| Bot backfill timeout | 15 seconds |

**Bot backfill:** `_get_bot_teams_for_match()` reads occupied teams from players_data, uses TEAM_CONFIGS dict, assigns bots to unoccupied slots only. BOT_NAMES: 100 Indian human-like names.

**Match flow:** Client `/allocate` with matchId → orchestrator groups by matchId → all minPlayers arrive = start immediately, else 15s timeout → backfill bots → start server with `-port` arg.

**MATCH_CONFIGS (CRITICAL):** Two config dicts — `TEAM_CONFIGS` (bot team assignment) and `MATCH_CONFIGS` (UniqueID assignment). Both must have entries for ALL match types. Client sends `Duo_2v4` (uppercased to `DUO_2V4`), NOT `DUO_2V2V2`. Missing key → `max_per_team` defaults to 1 → FFA path → teammates share UniqueIDs → server rejects connections.

### Deploy orchestrator (Python — NO Unity build needed)
```bash
scp orchestrator/orchestrator.py root@65.109.133.129:/root/orchestrator/
ssh root@65.109.133.129 "pkill -f orchestrator.py; cd /root/orchestrator && nohup python3 orchestrator.py > logs/orchestrator.log 2>&1 &"
```

**After server reboot:** Orchestrator must be manually restarted (not a systemd service).

---

## Server Deployment

### Required files (ALL mandatory, deploy together)
| File | Purpose |
|------|---------|
| `Server.x86_64` | Launcher stub (useless alone) |
| `GameAssembly.so` | IL2CPP compiled game code (~30-80MB) |
| `UnityPlayer.so` | Unity engine runtime (~20-40MB) |
| `Server_Data/` | Assets, configs |

```bash
# DEV deploy
scp Server.x86_64 GameAssembly.so UnityPlayer.so root@65.109.133.129:/root/aum-server-dev/
scp -r Server_Data root@65.109.133.129:/root/aum-server-dev/

# PROD deploy
scp Server.x86_64 GameAssembly.so UnityPlayer.so root@65.109.133.129:/root/aum-server-prod/
scp -r Server_Data root@65.109.133.129:/root/aum-server-prod/

# Promote dev→prod
ssh root@65.109.133.129 "cp /root/aum-server-dev/* /root/aum-server-prod/ && cp -r /root/aum-server-dev/Server_Data /root/aum-server-prod/"

# Verify
ssh root@65.109.133.129 "ls -lh /root/aum-server-dev/*.so /root/aum-server-dev/Server.x86_64"
```

### Firewall (BOTH required)
1. **UFW:** `sudo ufw allow 6006/udp && sudo ufw allow 7850:7909/udp && sudo ufw allow 8080/tcp`
2. **Hetzner Cloud Firewall:** Add UDP 6006, UDP 7850-7909, TCP 8080 inbound rules

### Useful commands
```bash
tail -f /root/orchestrator/logs/orchestrator.log  # Orchestrator logs
ps aux | grep -E "AUM|orchestrator"               # Check processes
netstat -tulpn | grep -E "6006|8080|785"          # Check ports
pkill -f AUM-Server                               # Kill all server instances
systemctl status aum-dev-6006.service             # Dev server status
fail2ban-client status sshd                       # Check banned IPs
fail2ban-client set sshd unbanip 1.2.3.4          # Unban an IP
```

---

## Server Security (Updated Feb 25, 2026)

**SSH:** Key-only authentication. Password login is disabled on both servers.
**fail2ban:** Active on both servers. 3 failed SSH attempts = 1 hour ban.
**nginx:** Disabled on Helsinki (was conflicting with orchestrator port 8080).

See `AUM-Documentation/sessions/2026-02-25-server-security-guide.md` for full security guide, emergency access procedures, and Hetzner rescue mode instructions.

---

## Recent Fixes

| Date | Fix | Files |
|------|-----|-------|
| **Feb 25** | **SECURITY INCIDENT** — Crypto miner removed, SSH hardened (key-only), fail2ban installed, 72 updates applied, dev service path fixed. See incident report. | sshd_config, jail.local, aum-dev-6006.service |
| **Feb 16** | **DUO_2V4 MATCH_CONFIGS** — added missing key (client sends Duo_2v4, not DUO_2V2V2), was causing duplicate UniqueIDs → match rejection | orchestrator.py |
| **Feb 15** | Orchestrator FFA bot team collision — reads occupied teams, assigns to free slots | orchestrator.py |
| **Feb 15** | Bot names unified — 100 Indian names (BOT_NAMES constant) | orchestrator.py |
| **Feb 12** | Debug log port in filename, PaniMuktha debug tags | DebugLogTracker.cs |
| **Feb 7** | **Server elemental sync from AVATARUPLOAD** — ProcessAvatarUpload updates player.elementals + reinits CastManager | PlayerManager.cs |

---

## Elemental System (CRITICAL)

AVATARUPLOAD processing in `PlayerManager.cs`: update `player.elementals` array (not just avatarList), then reinitialize `player.character.castManager`.
Spell bit packing: `(int)elementalType << 5 | spellType`. FIRE=0, WATER=1, AIR=2, ETHER=3, EARTH=4.

---

## Key Packets

| Packet | Code | Direction | Purpose |
|--------|------|-----------|---------|
| CREATECHARACTER | 0x1401 | C→S | Auth + spawn |
| WORLDSNAPSHOT | 0x1403 | S→C | All player states (60Hz) |
| PLAYERINPUT | 0x1404 | C→S | Input commands |
| ENDGAMEDATA | 0x1407 | S→C | Match results |
| AVATARUPLOAD | 0x140C | C→S | Avatar data (elementals, god, focus) |

---

## CloudScript Handlers (DEV rev 72, PROD rev 28)

| Handler | Purpose |
|---------|---------|
| `processAvatarMatchEnd` | Match end rewards/penalties (currencies, lives, Tamas self-deduction via `receivedKarma`, rajas steal) |
| `syncAvatarToVC` | Background currency sync (app quit/pause) |
| `purchaseWithAvatarCurrency` | Store purchase, tags itemCode in CustomData |
| `backfillInventoryItemCodes` | Tags old inventory items with itemCode |
| `checkAndRegisterAvatarName` | Global avatar name uniqueness (Title Internal Data registry) |
| `unregisterAvatarName` | Remove name from registry on avatar deletion |
| `GenerateFriendCode` | Social: create unique friend code |
| `SearchByFriendCode` | Social: find player by friend code |
| `SendFriendRequest` / `ClearFriendRequest` | Social: friend requests |
| `GetFriendsEnrichmentData` | Social: friend details |
| `SendInvite` / `ClearProcessedInvites` | Social: game invites |

**Name Registry:** Title Internal Data key `AvatarNameRegistry` — JSON `{lowercaseName: "playFabId_avatarGuid"}`. Atomic check+register prevents race conditions.

---

*Last Updated: February 25, 2026 (Security hardening — SSH key-only, fail2ban, crypto miner incident cleanup)*
