# AUM Claude Code - Quick Reference

**Print this or keep it open!**

---

## Start Your Session

```bash
cd ~/Documents/GitHub/AUM-Headless   # or AUM-The-Epic
claude
/start
```

---

## Commands

| Command | What It Does |
|---------|--------------|
| `/start` | Quick session start |
| `/session` | Full interactive setup |
| `/playtest` | Analyze recent playtest |
| `/review` | Check code for problems |
| `/compact` | Clear conversation, keep context |
| `/help` | Get help |

---

## Magic Phrases

| Say This... | Claude Will... |
|-------------|----------------|
| "debug this" | Use systematic 4-step debugging |
| "check combat code" | Scan for authority violations |
| "analyze desync" | Compare client/server logs |
| "playtest report" | Full session analysis |
| "bot isn't working" | Debug bot AI |
| "find [something]" | Search codebase |
| "plan this" | Create implementation plan |

---

## Agents (Auto-Activate)

| Agent | Trigger Words |
|-------|---------------|
| combat-reviewer | "combat", "damage", "authority" |
| sync-debugger | "desync", "mismatch", "client-server" |
| quick-explore | "find", "where is", "search" |
| playtest-analyzer | "playtest", "session", "logs" |
| bot-debugger | "bot", "AI", "stuck" |

---

## If Claude Gets Stuck

1. **Too much guessing:** "Use systematic debugging"
2. **Confused:** "Let's start over. I need [clear description]"
3. **Changed too much:** "Undo. Make smaller change"
4. **Slow:** Type `/compact`

---

## Combat Code Rules (FYI)

**NEVER:** `player.playerData.stamina -= X`
**ALWAYS:** `authority.ConsumeStamina(playerId, X)`

**NEVER:** Hardcode `25f` or `70f`
**ALWAYS:** Use `AbilityCosts.ELEMENTAL_SPELL`

---

## Projects

| Project | Path | Port |
|---------|------|------|
| Headless (Server) | `AUM-Headless` | 6401 |
| Epic (Client) | `AUM-The-Epic` | 6400 |
| Docs | `AUM-Documentation` | - |

---

## Help

- In Claude: `/help`
- Full guide: `AUM-Documentation/WORKFLOW-GUIDE.md`
- Just ask Claude!
