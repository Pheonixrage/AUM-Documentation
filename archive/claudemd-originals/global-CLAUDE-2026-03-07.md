# Global Claude Code Workflow (AUM Development)

## Primary Projects

| Project | Path | Purpose |
|---------|------|---------|
| **AUM-The-Epic** | `/Users/mac/Documents/GitHub/AUM-The-Epic` | Unity Client |
| **AUM-Headless** | `/Users/mac/Documents/GitHub/AUM-Headless` | Unity Server |
| **AUM-Documentation** | `/Users/mac/Documents/GitHub/AUM-Documentation` | Context & Logs |

---

## GSD Workflow (Always Active)

### Starting a Session
```
/gsd:progress          # Check current state
/gsd:resume-work       # If continuing previous work
```

### Before Implementation
| Task Type | Command |
|-----------|---------|
| Multi-file feature | `/gsd:plan-phase` first |
| Single-file fix | `/gsd:quick` |
| Bug investigation | `/gsd:debug` |

### During Work
- One task at a time
- Atomic commits per task
- Verify before marking complete

### Ending a Session
```
/gsd:pause-work        # Save state for next session
```

---

## Context Management

### Monitor Usage
```
/context               # Check current usage %
/context-check         # Get full health report
```

### Actions by Usage Level
| Usage | Action |
|-------|--------|
| 50% | Consider `/compact` soon |
| 60% | Use `/gsd:pause-work`, then `/compact` |
| 70%+ | `/gsd:pause-work`, then `/clear`, then `/gsd:resume-work` |

### Context Rot Warning Signs
- Ignoring earlier instructions
- Repeating same mistakes
- Forgetting project rules
- Missing validation checks

---

## AUM-Specific Workflows

### After Playtests
Always check logs when returning from testing:
1. `mcp__unity__log_errors` - Client errors
2. `mcp__unity-headless__log_errors` - Server errors
3. `mcp__unity__log_tail` - Recent client activity

### Cross-Project Changes
When modifying shared code:
1. Make change in AUM-The-Epic
2. Run `/sync-headless` to sync to AUM-Headless
3. Test both projects

### Autonomous Development
Use `/autodev <description>` for fully hands-off: investigate → implement → playtest-verify → commit → push → deploy.

### Session Logs
Save session summaries to: `AUM-Documentation/sessions/YYYY-MM-DD-{topic}.md`

---

## Deployment & Infrastructure

### Server Infrastructure
| Server | IP | Purpose | Service |
|--------|----|---------|---------|
| Helsinki (Production) | `65.109.133.129` | Live matches | `aum-jan24.service` |
| Singapore (Dev) | `5.223.55.127` | Staging/test | `aum-dev.service` |

### Deployment Workflow
1. Build headless server from AUM-Headless
2. Deploy via SSH: `scp` build → restart `systemd` service
3. Tail logs for 30s to verify clean startup
4. Check port 7777 (UDP) is listening

### Deployment Safety
- Check active players before restarting production
- Never deploy without passing local playtest verification
- Always have rollback plan (previous build at `/opt/mac-build.bak/`)

---

## Monitoring & Crash Triage

### Tools
| Source | MCP Tool | What It Checks |
|--------|----------|----------------|
| Unity Client | `mcp__unity__log_errors` | Editor/runtime errors |
| Unity Server | `mcp__unity-headless__log_errors` | Headless server errors |
| Firebase | `mcp__firebase__*` | Crashlytics, Auth, Firestore |
| Sentry | `mcp__sentry__*` | Error tracking, AI root cause |
| Production | `mcp__ssh__direct_exec` | Remote server logs/status |
| PlayFab | `mcp__playfab__*` | Backend data, catalog, users |

### Monitoring Workflow
When checking production health:
1. SSH to server → `systemctl status aum-jan24`
2. Check server logs → `tail -50 /var/log/aum/mac-build.log`
3. Check Firebase Crashlytics for mobile crashes
4. Check PlayFab for backend issues

---

## MCP Tool Suite

### Currently Configured (12/12 Connected)
| Server | Purpose |
|--------|---------|
| `unity` | Unity Editor client (port 6400) |
| `unity-headless` | Unity headless server (port 6401) |
| `playfab` | PlayFab backend management |
| `memory` | Knowledge graph persistence |
| `firebase` | Crashlytics, Auth, Firestore |
| `sentry` | Error tracking, AI root cause analysis |
| `hetzner` | Hetzner Cloud server provisioning/management |
| `ssh` | SSH to any server (per-request credentials) |
| `github` | GitHub API (PR, issues, Actions) |
| `context7` | Live SDK documentation |
| `docker` | Container management |
| `playwright` | Browser automation |

---

## Project Documentation

**Always read the project's CLAUDE.md first** - it contains:
- Project-specific rules and constraints
- DO NOT MODIFY lists
- Architecture documentation
- Recent fixes and known issues

The project CLAUDE.md at `/Users/mac/Documents/GitHub/AUM-The-Epic/CLAUDE.md` is the **single source of truth** for AUM.

---

## Default Behavior

- Use TodoWrite for multi-step tasks
- Commit atomically per completed task
- Verify before marking complete
- Never guess - ask if unclear
- Check project CLAUDE.md for project-specific rules
- Use MCP log tools after playtests
- Use `/autodev` for autonomous development pipeline
