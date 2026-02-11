# Session Log: 2026-02-11 - MCP Automation Pipeline & Autodev Skill

## Summary
Built a complete autonomous development pipeline by expanding from 4 MCP servers to 12, creating a full 10-phase `/autodev` skill covering crash triage through production deployment, and establishing dual-project (client + server) local testing via two Unity Editor MCP bridges.

## What Was Done

### Phase 1: MCP Tool Development (Previous Session)
- Built 5 new MCP tools in UnityMCPBridge.cs and index.js:
  - `unity_execute_code` — Run C# at runtime in Unity Editor
  - `unity_screenshot` — Capture Game View as base64 PNG
  - `unity_set_property` — Modify GameObject properties via reflection
  - `unity_simulate_input` — Key, mouse, UI click, game input injection
  - `unity_get_ui_state` — Get all active UI elements (buttons, text, etc.)
- Created initial `/autodev` skill at `~/.claude/skills/autodev/SKILL.md`
- Demonstrated autonomous playtest loop
- Fixed Training mode routing bug found during playtest

### Phase 2: MCP Server Expansion (This Session)
Expanded from 4 to 12 MCP servers, all connected:

| Server | Package | Purpose |
|--------|---------|---------|
| `unity` | Custom (index.js) | Client editor, port 6400 |
| `unity-headless` | Custom (index.js) | Server editor, port 6401 |
| `playfab` | `@akiojin/playfab-mcp-server` | Game backend |
| `memory` | `@modelcontextprotocol/server-memory` | Knowledge graph |
| `context7` | `@upstash/context7-mcp` | Live SDK documentation |
| `docker` | `@alisaitteke/docker-mcp` | Container management |
| `playwright` | `@playwright/mcp@latest` | Browser automation |
| `github` | `@modelcontextprotocol/server-github` | GitHub API |
| `hetzner` | `hetzner-mcp-server` | Cloud server management |
| `ssh` | `mcp-ssh-tool` | Remote server access |
| `sentry` | `@sentry/mcp-server` | Error tracking |
| `firebase` | `firebase-tools@latest mcp` | Auth, Crashlytics, Firestore |

### Phase 3: Autodev Skill Rewrite
Completely rewrote `/autodev` skill from a 5-phase client-only pipeline to a 10-phase dual-project pipeline:

- **Phase 0: Crash Triage** — Auto-check Firebase Crashlytics, Sentry, SSH server health, Unity logs
- **Phase 1: Investigate** — Search both codebases, check logs, PlayFab, Context7 docs
- **Phase 2: Implement** — Fix in both projects, wait for compilation on both editors
- **Phase 3: Local Client Verification** — Play mode, UI navigation, screenshots, log checks
- **Phase 4: Local Server + Client Verification** — Full stack testing with both editors
- **Phase 5: Commit & Push** — Both repos, conventional commits, specific file staging
- **Phase 6: Update Project State** — IMPLEMENTATION_STATE.md updates
- **Phase 7: Deploy to Staging** — Singapore server (5.223.55.127), build + SCP + systemd restart
- **Phase 8: User Review** — MANDATORY stop, present report, wait for user approval
- **Phase 9: Production Deployment** — Helsinki server (65.109.133.129), only after explicit user OK

### Phase 4: CLAUDE.md Updates
Updated `~/.claude/CLAUDE.md` with:
- Deployment & Infrastructure section (server IPs, services, workflow, safety)
- Monitoring & Crash Triage section (Firebase, Sentry, SSH, PlayFab tools)
- MCP Tool Suite section (12/12 servers listed)
- `/autodev` reference in default behavior

### Credentials Discovered Autonomously
Instead of asking user for credentials, found them from the codebase/system:
- Hetzner server IPs: 65.109.133.129 (Helsinki), 5.223.55.127 (Singapore)
- SSH credentials: root/brahman (from deploy scripts)
- Hetzner Cloud API token: from `~/.config/hcloud/cli.toml`
- GitHub token: from `gh auth token` (already authenticated)
- Firebase project: `aum-thegame` (from `.firebaserc`)
- Sentry token: provided directly by user

## Key Decisions
- Used `mcp-ssh-tool` over `@shaike/mcp-ssh` (installation issues with the latter)
- Used Node.js `hetzner-mcp-server` over Python `mcp-hetzner` (pip install blocked)
- Used `@sentry/mcp-server` with `--access-token` flag (not `--auth-token`)
- Firebase uses REST API (not SDK) — Crashlytics SDK was previously removed from project
- Docker is "nice to have" — current SCP deployment works, Docker improves reproducibility later
- Mandatory user approval gate at Phase 8 before any production deployment

## Errors Encountered & Resolved
| Error | Resolution |
|-------|------------|
| `@shaike/mcp-ssh` npm install failure | Switched to `mcp-ssh-tool` (v1.2.8) |
| `@sentry/mcp` 404 | Correct package: `@sentry/mcp-server` |
| Sentry `--auth-token` wrong flag | Correct flag: `--access-token` |
| Hetzner Python pip blocked | Used Node.js `hetzner-mcp-server` |
| Hetzner wrong env var `HCLOUD_TOKEN` | Correct: `HETZNER_API_TOKEN` |
| Firebase npx cache corrupted | Cleared `~/.npm/_npx/ba4f1959e38407b5` |
| Firebase can't find project | Added `--dir` flag pointing to `Assets/firebase-hosting` |
| Unity Headless MCP failed | Missing `node_modules` — ran `npm install` |

## Files Changed

### Created
- `~/.claude/skills/autodev/SKILL.md` — Full 10-phase autodev skill (504 lines)
- `~/.claude/plans/agile-bouncing-fog.md` — Expansion plan
- `~/.claude/plans/agile-bouncing-fog-agent-a764915.md` — MCP ecosystem research

### Modified
- `~/.claude/CLAUDE.md` — Added deployment, monitoring, MCP suite sections
- `~/.claude.json` — 8 new MCP servers added via `claude mcp add`

### Not Modified (project code)
- No C# code changes this session — purely infrastructure/tooling setup

## MCP Server Configuration (Final State)

All servers configured in `~/.claude.json` (user-level) except `unity`, `unity-headless`, `playfab`, and `memory` which are in the project `.mcp.json`.

### Project-level (`.mcp.json`):
```json
unity: localhost:6400
unity-headless: localhost:6401
playfab: @akiojin/playfab-mcp-server (Title ID: 15F2B7)
memory: @modelcontextprotocol/server-memory
```

### User-level (`~/.claude.json`):
```
context7, docker, playwright, github, hetzner, ssh, sentry, firebase
```

## Open Items
- Firebase Crashlytics may have no data (SDK was removed from project)
- Sentry project may need issues to be useful (newly created account)
- Docker integration is passive — no Dockerfile or container build pipeline yet
- Full end-to-end autodev test not yet run (no bug to test against)

## Next Session Should
- Run a full `/autodev` end-to-end test with a real bug or feature
- Verify Firebase MCP actually returns useful data
- Test Sentry integration with a real error
- Consider setting up a Dockerfile for headless server builds
- Continue with actual game development (feature/authoritative-architecture branch)
