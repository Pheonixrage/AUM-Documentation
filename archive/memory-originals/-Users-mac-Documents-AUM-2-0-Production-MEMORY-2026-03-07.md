# AUM 2.0 Production - Memory

## CRITICAL: Project Identity (DO NOT CONFUSE)
- **AUM-2.0 Production** = the LEGACY PRODUCTION codebase. NOT V2/experimental.
  - `Server/` = `AUM-Unity-Server-Legacy` repo, branch `legacy-working-oct6`
  - `Client/` = legacy client repo, branch `legacy-working-oct29`
  - This is the LIVE game that gets deployed to production servers
- **V2 experimental** (separate, NOT this project):
  - `AUM-The-Epic` at `/Users/mac/Documents/GitHub/AUM-The-Epic` = V2 Client
  - `AUM-Headless` at `/Users/mac/Documents/GitHub/AUM-Headless` = V2 Server
- NEVER call legacy work "V2" — it causes confusion. Call it "Elemental Mastery System" or "legacy enhancement".

## Elemental Mastery System (COMMITTED — Feb 28, 2026)
- Client commit: `42f7906f3` on `legacy-working-oct29` — 55 files, +9365/-311
- Server commit: `04b9d59` on `legacy-working-oct6` — 28 files, +2485/-111
- Plan file: `/Users/mac/.claude/plans/stateful-tumbling-ember.md`
- Session log: `AUM-Documentation/sessions/2026-02-28-elemental-mastery-system-implementation.md`
- Status: All 7 phases implemented, local commits done, NOT pushed to remote
- Testing: Elemental selection UI working, spell tree entry fixed, 5th slot auto-setup working
- Next: Import spell prefabs (.unitypackage), full match testing, PlayFab verification
- PlayFab: Dev title (15F2B7) only — NOT production (158C02)

## Server Security (Feb 25, 2026)
- Helsinki (`65.109.133.129`): SSH key-only, fail2ban, password auth disabled
- Singapore (`5.223.55.127`): SSH key-only, fail2ban, password auth disabled
- Root password (console only): `AUM_Prod_2026_Kx9Mn!`
- Hetzner API Token: `S5ndM58eyYAwHgkRJ3j2fuxWhQb0dmFi9K3RxOcPQdJOd2zytmDKh00Ph87CuxkY`
- Hetzner Server ID (Helsinki): `115148857`
- SSH key on this Mac (`~/.ssh/id_ed25519`) is authorized on both servers
- nginx is DISABLED on Helsinki (conflicts with orchestrator port 8080)
- After Helsinki reboot: must manually start orchestrator

## Helsinki Services
- Orchestrator: manual start (`nohup python3 orchestrator.py`), port 8080
- Dev server: `aum-dev-6006.service` (systemd), port 6006, path `/root/aum-server-dev/`
- Prod servers: orchestrator-managed, ports 7850-7909

## Singapore Services
- Nakama v2: Docker (`aum-nakama` + `aum-postgres`), ports 7350-7352, config at `/opt/nakama/`
- Legacy dev server: `aum-dev.service`, port 7777
- Legacy orchestrator: `aum-orchestrator.service`, port 8080
- Legacy prod service: DISABLED (migrating to Nakama)

## Key Lessons
- Use `expect` for SSH with password (sshpass not installed on Mac)
- Ubuntu 24.04 SSH service name is `ssh` not `sshd`
- `apt upgrade` can auto-enable disabled services (nginx got enabled after update)
- Hetzner rescue mode: enable via API → reboot → SSH with temp password → mount /dev/sda1 /mnt
- Always check `/etc/ssh/sshd_config.d/` for cloud-init overrides
- Dev service file had wrong path (`/root/aum-server/` vs `/root/aum-server-dev/`) — was causing crash loop

## Unity UI Setup Lessons (from Elemental Mastery)
- When Inspector arrays need expanding (e.g., selectIcons 4→5), write Editor scripts with `[MenuItem]`
- Editor scripts can: find components, read SerializedObject, duplicate GameObjects, calculate spacing
- `Screen.Entry()` has no try-catch — any exception in `EntrySet()` aborts ALL setup including listeners
- Use `if (i < array.Length)` bounds checks before accessing serialized arrays in loops
- Movement speed in legacy: use `player.movePenalty = SlowType.FIFTY` (NOT SetRunSpeedMultiplier)
- Prefab naming: `{ELEMENT}_{spellLevel}_{variant}` with fallback to `{ELEMENT}_0_{variant}`
- Unity MCP tools NOW configured for AUM-2.0 Production: port 6402, server name `unity-legacy`
  - Bridge: `Client/Assets/Editor/UnityMCPBridge.cs` (port 6402)
  - Node.js: `Client/unity-mcp-server/`
  - Config: `.mcp.json` at project root
  - MCP tools: `mcp__unity-legacy__*` (need Claude Code restart to pick up)
- `localScale = Vector3.one` when re-parenting UI elements prevents inherited scale issues

## Documentation
- Incident report: `AUM-Documentation/sessions/2026-02-25-security-incident-crypto-miner.md`
- Security guide: `AUM-Documentation/sessions/2026-02-25-server-security-guide.md`
- Elemental Mastery: `AUM-Documentation/sessions/2026-02-28-elemental-mastery-system-implementation.md`
- Server CLAUDE.md updated with security section
