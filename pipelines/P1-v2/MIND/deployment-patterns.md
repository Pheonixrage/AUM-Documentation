---
pipeline: P1
project: AUM-MIND
type: pattern
date: 2026-03-24
tags: [deployment, servers, systemd]
---

# Deployment Patterns — AUM MIND

## Servers

| Server | IP | Role | Service |
|--------|----|------|---------|
| Helsinki | 65.109.133.129 | Production (P1+P3) | aum-jan24.service |
| Singapore | 5.223.55.127 | Dev/Staging + Nakama | aum-dev.service :7777 |

## Deploy Process

1. Build headless server (Unity → Linux64 IL2CPP)
2. `scp` build to server at `/opt/mac-build/` (Helsinki) or `/root/aum-server-prod/` (Singapore)
3. `systemctl restart aum-jan24` (or `aum-dev`)
4. Verify via MCP: `mcp__unity-headless__log_tail`

## Logs

- Server logs: `/var/log/aum/mac-build.log`
- MCP access: `mcp__unity-headless__log_errors`, `log_tail`, `log_search`
