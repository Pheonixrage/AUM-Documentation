---
type: index
date: 2026-03-07
---

# AUM Knowledge Vault — Index

## Three Pipelines

| Pipeline | Client | Server | Status |
|----------|--------|--------|--------|
| **P1 — V2** (AUM BODY/MIND/SPIRIT) | AUM-The-Epic [v2] | AUM-Headless [AUM_MIND] | Active development |
| **P2 — Production** | AUM-2.0 Production/Client [elemental-progression] | AUM-2.0 Production/Server | Elemental Mastery phases 1-10 ✓ |
| **P3 — Legacy Live** | AUM-Unity-Staging-Legacy [legacy-working-oct29] | AUM-Unity-Server-Legacy | Live on iOS + Android |

## Servers

| Server | IP | Pipelines | Service |
|--------|----|-----------|---------|
| Helsinki | `65.109.133.129` | P1 + P3 Live | `aum-jan24.service` |
| Singapore | `5.223.55.127` | P2 Staging | `aum-dev.service` :7777 |

---

## Vault Structure

```
pipelines/
├── P1-v2/
│   ├── _index.md          ← P1 dashboard
│   ├── BODY/              ← AUM-The-Epic patterns + sessions
│   ├── MIND/              ← AUM-Headless patterns + sessions
│   └── SPIRIT/            ← Architecture decisions
│
├── P2-production/
│   ├── _index.md          ← P2 dashboard
│   ├── client/            ← Elemental patterns + sessions
│   └── server/            ← Singapore ops + sessions
│
└── P3-legacy/
    ├── _index.md          ← P3 dashboard
    ├── client/            ← Legacy client patterns + sessions
    └── server/            ← Helsinki/Singapore ops

cross-pipeline/            ← Patterns used across pipelines
├── playfab-cloudscript.md
├── matchmaking-patterns.md
└── server-deployment-ops.md

sessions/                  ← All session logs (existing, tag with pipeline frontmatter)
archive/                   ← CLAUDE.md + MEMORY.md originals (Mar 7, 2026)
```

---

## Quick Links

- [P1 Dashboard](pipelines/P1-v2/_index.md)
- [P2 Dashboard](pipelines/P2-production/_index.md)
- [P3 Dashboard](pipelines/P3-legacy/_index.md)
- [Architecture Blueprint](ARCHITECTURE_BLUEPRINT.md)
- [Unified Roadmap](ROADMAP.md)
- [Tools Manifest](TOOLS_MANIFEST.md)
- [Home Dashboard](HOME.md)
- [Session Logs](sessions/)
- [Archive](archive/)

---

## Note Format

New session logs: `sessions/YYYY-MM-DD-{topic}.md`

Frontmatter for every new note:
```yaml
---
pipeline: P2
project: 2.0-production-client
date: 2026-03-07
tags: [elemental, VFX, spells]
---
```

*Last updated: Mar 24, 2026*
