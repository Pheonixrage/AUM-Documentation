# AUM Claude Code Workflow Guide

**For Designers & Non-Programmers**
*Last Updated: January 12, 2026*

---

## Quick Reference Card

### Starting Your Day
```
Open Terminal
cd to your project folder
Type: claude
Type: /start
```

### Common Commands (Just Type These!)

| What You Want | What to Type |
|--------------|--------------|
| Start a session | `/start` |
| Full session setup | `/session` |
| Analyze playtest | `/playtest` |
| Review code changes | `/review` |
| Get help | `/help` |

### Magic Words That Trigger Helpers

Just mention these in your request and Claude will use the right tools:

| Say This | Claude Uses |
|----------|-------------|
| "debug this" | systematic-debugging skill |
| "check the combat code" | combat-reviewer agent |
| "why is there desync" | sync-debugger agent |
| "analyze the playtest" | playtest-analyzer agent |
| "bot is stuck" | bot-debugger agent |
| "find where X is" | quick-explore agent |
| "plan this feature" | brainstorming skill |

---

## Your Daily Workflow

### Morning Start
1. Open Terminal
2. Navigate to project:
   ```
   cd ~/Documents/GitHub/AUM-Headless
   ```
   (or AUM-The-Epic for client)
3. Start Claude Code:
   ```
   claude
   ```
4. Type `/start` to initialize

### Working on a Bug

Just describe the problem naturally:

> "The dodge isn't working - the player doesn't move when they dodge"

Claude will:
1. Automatically use **systematic-debugging** skill
2. Search for relevant code
3. Analyze the issue
4. Propose a fix
5. Ask for your approval before changing anything

### After a Playtest

1. Type `/playtest`
2. Claude will automatically:
   - Pull logs from both client and server
   - Find all errors
   - Create a prioritized report
   - Suggest fixes

### Before Committing Code

1. Type `/review`
2. Claude will check all changed files for:
   - Combat authority violations (dangerous!)
   - Hardcoded values (should use constants)
   - Missing safety checks
3. Get a clean report before committing

---

## Understanding the Agents

Think of agents as specialized assistants. You don't need to call them directly - Claude will use them automatically when needed.

### combat-reviewer
**When it activates:** You're looking at combat-related code

**What it does:** Checks for "anti-patterns" - code mistakes that would cause multiplayer bugs

**Example trigger:** "Check if this damage code is correct"

### sync-debugger
**When it activates:** You mention desync, networking issues, or client-server problems

**What it does:** Compares client and server logs to find where things went wrong

**Example trigger:** "The client and server aren't matching up"

### quick-explore
**When it activates:** You want to find something in the codebase

**What it does:** Fast search across all code files

**Example trigger:** "Where is the dodge handled?"

### playtest-analyzer
**When it activates:** You run `/playtest` or mention "playtest"

**What it does:** Full analysis of recent game session logs

**Example trigger:** "What went wrong in the last playtest?"

### bot-debugger
**When it activates:** You mention bot problems

**What it does:** Analyzes bot AI decision-making

**Example trigger:** "The bot isn't attacking"

---

## Understanding the Skills

Skills are knowledge packages that help Claude work smarter. They activate automatically.

### systematic-debugging (Most Important!)
**Prevents:** Random guessing at fixes

**What it does:** Forces a 4-step process:
1. Find the root cause
2. Understand why it happens
3. Create the minimal fix
4. Verify the fix works

**Tip:** If Claude starts guessing, say "use systematic debugging"

### test-driven-development
**When to use:** Building new features

**What it does:** Ensures tests are written alongside code

### brainstorming
**When to use:** Planning a new feature

**How to trigger:** Say "let's brainstorm" or "plan this feature"

### writing-plans
**When to use:** Complex multi-step work

**How to trigger:** Say "write a plan for this"

---

## Tips for Best Results

### Be Specific
```
Instead of: "Fix the combat"
Say: "The fire spell isn't doing damage to the enemy"
```

### Give Context
```
Instead of: "It's broken"
Say: "After the last update, bots stopped dodging attacks"
```

### Mention the Mode
```
"This only happens in multiplayer, not tutorial mode"
```

### Reference Files if You Know Them
```
"I think the issue is in PlayerManager.cs"
```

---

## When Things Go Wrong

### Claude Seems Confused
Say: "Let's start fresh. Here's what I need: [describe clearly]"

### Claude Keeps Guessing Wrong
Say: "Stop guessing. Use systematic debugging to find the root cause."

### Claude Changed Too Much
Say: "Undo that. Make a smaller, more focused change."

### Session Gets Slow
Type: `/compact`
This clears old conversation but keeps important context.

---

## Quick Fixes

### "Command not found: claude"
Run in Terminal:
```
npm install -g @anthropic-ai/claude-code
```

### "MCP server not connecting"
Make sure Unity is running with the MCP package.

### "Skills not working"
Say: "List my available skills" to verify they're loaded.

---

## Optional: GitHub Integration

This lets Claude create Pull Requests and manage Issues directly.

### Setup (One Time)
1. Go to https://github.com/settings/tokens
2. Create a new token with "repo" access
3. Run:
   ```
   cd ~/Documents/GitHub/AUM-Documentation/setup
   ./github-mcp-setup.sh YOUR_TOKEN_HERE
   ```
4. Restart Claude Code

### Using It
Just say things like:
- "Create a PR for these changes"
- "What issues are open?"
- "Close issue #123"

---

## Folder Structure (Reference)

```
~/.claude/
  skills/           <- Installed skills (auto-loads)
    brainstorming/
    systematic-debugging/
    aum-combat-check/
    aum-multiplayer-patterns/
    aum-bot-patterns/
    ...

  agents/           <- Custom agents (auto-loads)
    combat-reviewer.md
    sync-debugger.md
    quick-explore.md
    playtest-analyzer.md
    bot-debugger.md

  superpowers-repo/ <- Superpowers source
  settings.json     <- Global settings
```

```
AUM-Headless/.claude/
  commands/         <- Custom commands
    start.md        <- /start
    session.md      <- /session
    playtest.md     <- /playtest
    review.md       <- /review

  rules/            <- Always-active rules
    aum-architecture.md
    game-design.md
    session-management.md

  settings.json     <- Project settings
```

---

## Getting Help

- Type `/help` in Claude Code
- Check this guide
- Ask Claude: "How do I [do something]?"

---

*Remember: Claude is here to help YOU. If something isn't working the way you expect, just describe what you want in plain language!*
