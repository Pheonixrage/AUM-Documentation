---
type: dashboard
date: 2026-03-24
---

# AUM Knowledge Vault

## Current Status

- **Phase:** Integration & Testing (V2 systems built, wiring to production)
- **Branches:** BODY `v2` | MIND `AUM_MIND` | SPIRIT `AUM_SPIRIT`
- **Launch Target:** August 2026
- **V2 Progress:** 229 C# files across 17 modules built

## Quick Links

- [[ROADMAP]] — Unified launch roadmap
- [[ARCHITECTURE_BLUEPRINT]] — V2 architecture (1155 lines)
- [[TOOLS_MANIFEST]] — All dev tools reference
- [[GLOSSARY]] — Game terminology
- [[TECH_STACK_DECISIONS]] — Backend choices

## Pipelines

- [[pipelines/P1-v2/_index|P1 — AUM V2]] (Active Development)
- [[pipelines/P2-production/_index|P2 — Production]] (Live on iOS/Android)
- [[pipelines/P3-legacy/_index|P3 — Legacy]] (Being migrated)

## Pattern Docs

### BODY (Client)
- [[pipelines/P1-v2/BODY/combat-patterns|Combat Patterns]] — Authority, damage flow, elementals
- [[pipelines/P1-v2/BODY/state-machine-patterns|State Machine]] — FSM, callbacks, mismatch
- [[pipelines/P1-v2/BODY/networking-patterns|Networking]] — Prediction, reconciliation, ticks

### MIND (Server)
- [[pipelines/P1-v2/MIND/server-authority-patterns|Server Authority]] — Validation, bots, match lifecycle
- [[pipelines/P1-v2/MIND/deployment-patterns|Deployment]] — Helsinki/Singapore, systemd

### Cross-Pipeline
- [[cross-pipeline/deployment-ops|Deployment Ops]] — SSH, builds, service management

## Servers

| Server | IP | Service |
|--------|----|---------|
| Helsinki | 65.109.133.129 | Production (P1+P3) |
| Singapore | 5.223.55.127 | Dev/Staging (Nakama) |

## Recent Sessions

<!-- Update with latest session links -->

---

*Last updated: March 24, 2026*
