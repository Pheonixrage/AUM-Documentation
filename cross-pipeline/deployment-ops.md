---
pipeline: all
type: pattern
date: 2026-03-24
tags: [deployment, ssh, systemd, servers]
---

# Deployment Operations — Cross-Pipeline

## Server Access

| Server | IP | SSH | Pipelines |
|--------|----|-----|-----------|
| Helsinki | 65.109.133.129 | `ssh root@65.109.133.129` | P1 + P3 Live |
| Singapore | 5.223.55.127 | `ssh root@5.223.55.127` | P2 Staging + Nakama |

## MCP Tools for Operations

- `mcp__ssh__proc_exec` — Run commands on remote servers
- `mcp__hetzner__*` — Server provisioning and management
- `mcp__unity-headless__log_*` — Server log monitoring

## Build Targets

| Target | Platform | Build Type |
|--------|----------|------------|
| Client (macOS) | StandaloneOSX | Development/Release |
| Client (iOS) | iOS | IL2CPP |
| Client (Android) | Android | IL2CPP |
| Server (Linux) | Linux64 | Headless IL2CPP |

## Service Management

```bash
systemctl status aum-jan24    # Helsinki
systemctl restart aum-jan24   # Restart production
systemctl status aum-dev      # Singapore
```
