---
pipeline: all
type: reference
date: 2026-03-24
tags: [tools, mcp, skills, automation]
---

# AUM Tools Manifest

## MCP Servers (12)

| Server | Port | Purpose | Status |
|--------|------|---------|--------|
| unity | 6400 | Client log monitoring, runtime code exec, screenshots, input sim | ACTIVE |
| unity-headless | 6401 | Server log debugging, headless introspection | ACTIVE |
| playfab | - | Backend: currencies, inventory, matchmaking (Title 15F2B7) | ACTIVE |
| memory | - | Knowledge graph for persistent context | LOW USE |
| firebase | - | Google Auth, Crashlytics crash monitoring | LOW USE |
| sentry | - | Error tracking with AI root cause analysis (Seer) | LOW USE |
| hetzner | - | Cloud server provisioning and management | ACTIVE |
| ssh | - | Remote execution on Helsinki/Singapore servers | ACTIVE |
| github | - | PR management, issues, Actions, code search | ACTIVE |
| context7 | - | Live SDK documentation lookup (Unity, LiteNetLib, etc.) | ACTIVE |
| docker | - | Container management (Nakama on Singapore) | ACTIVE |
| playwright | - | Browser automation (admin panels) | LOW USE |

## Claude Computer Use (NEW - Mar 24, 2026)

Enabled for Pro/Max on macOS. Visual testing, UI verification, human-like game interaction.
Complements MCP tools: MCP = fast programmatic access, Computer Use = visual verification.

## Skills

### AUM-Specific
| Skill | Purpose |
|-------|---------|
| aum-dev | Auto-loads AUM context, architecture, MCP log tools |
| autodev | 10-phase autonomous development pipeline |
| aum-combat-check | Detect authority bypasses in combat code |
| aum-bot-patterns | Enforce bot AI patterns |
| aum-multiplayer-patterns | Enforce multiplayer correctness |
| fighting-game-netcode | Rollback, prediction, state sync patterns |

### General Development
| Skill | Purpose |
|-------|---------|
| debugging | Systematic 4-phase debugging framework |
| planning | Technical solution design |
| code-review | Code quality review protocol |
| unity-csharp-patterns | Unity C# best practices |
| problem-solving | 5 named problem-solving techniques |
| brainstorming | Creative exploration before implementation |

### GSD Framework
| Skill | Purpose |
|-------|---------|
| /gsd:progress | Check project progress, route to next action |
| /gsd:resume-work | Resume from previous session with context |
| /gsd:pause-work | Create handoff when stopping work |
| /gsd:plan-phase | Create detailed phase execution plan |
| /gsd:execute-phase | Execute plans with atomic commits |
| /gsd:quick | Quick task with GSD guarantees |

### Project Commands
| Command | Purpose |
|---------|---------|
| /session | Interactive session initializer |
| /start | Quick start session |
| /playtest | Analyze playtest session logs |
| /review | Review current changes |
| /debug-state | Debug FSM state issues |
| /sync-headless | Sync shared code client ↔ server |
| /test-combat | Run combat system validation |

## Agents (44+)

- **GSD Agents (11):** planner, executor, verifier, debugger, researcher, etc.
- **AUM-Specific (5):** bot-debugger, combat-reviewer, playtest-analyzer, sync-debugger, quick-explore
- **Unity Specialists (28+):** gameplay, graphics, shader, physics, animation, audio, mobile, multiplayer, VR, AR, UI, AI, security, data, monetization, localization, accessibility, etc.

---

*Last updated: March 24, 2026*
