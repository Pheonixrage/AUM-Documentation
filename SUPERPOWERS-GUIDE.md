# Superpowers & Commands Guide

**Simple explanations for designers**
*Your AI coding assistant just got superpowers!*

---

## What Are Superpowers?

Superpowers are **smart behaviors** that make Claude work like a senior developer instead of just guessing at solutions. They activate automatically when relevant.

Think of them as "good habits" that Claude follows.

---

## The Superpowers (What Each Does)

### 1. Systematic Debugging
**The most important one!**

| Without It | With It |
|------------|---------|
| Claude guesses randomly | Claude follows a 4-step process |
| Might fix symptoms, not cause | Finds the ROOT cause |
| Takes many attempts | Usually fixes on first try |

**The 4 Steps:**
1. **Investigate** - What's actually happening?
2. **Trace** - Where does it go wrong?
3. **Fix** - Minimal change to fix root cause
4. **Verify** - Confirm it's actually fixed

**How to trigger:** Just say "debug" or "fix this bug"

---

### 2. Brainstorming
**Use before starting any new feature**

| Without It | With It |
|------------|---------|
| Jumps straight to coding | Thinks through the problem first |
| Might miss edge cases | Considers all scenarios |
| May need rewrites | Gets it right the first time |

**What it does:**
- Explores different approaches
- Identifies potential problems early
- Creates a clear plan before coding

**How to trigger:** Say "let's brainstorm" or "plan this feature"

---

### 3. Writing Plans
**For complex, multi-step work**

| Without It | With It |
|------------|---------|
| Works on random parts | Organized step-by-step plan |
| Loses track of progress | Clear checklist to follow |
| Might forget steps | Nothing gets missed |

**Best for:**
- Big features (multiple files)
- Refactoring
- Bug fixes that touch many areas

**How to trigger:** Say "write a plan for this"

---

### 4. Executing Plans
**Runs plans in organized batches**

| Without It | With It |
|------------|---------|
| Does everything at once | Works in manageable chunks |
| Hard to review changes | Easy to check each step |
| Risky if something breaks | Can stop and fix issues |

**How to trigger:** Say "execute the plan" after writing one

---

### 5. Test-Driven Development (TDD)
**Write tests alongside code**

| Without It | With It |
|------------|---------|
| Code might have hidden bugs | Bugs caught immediately |
| "It works on my machine" | Verified to work correctly |
| Scary to change later | Safe to modify |

**The cycle:**
1. **Red** - Write a failing test
2. **Green** - Write code to pass
3. **Refactor** - Clean up

**How to trigger:** Say "use TDD" or "write tests first"

---

### 6. Verification Before Completion
**Double-checks work before saying "done"**

| Without It | With It |
|------------|---------|
| "Done!" (but actually broken) | Actually verified working |
| You find bugs later | Bugs caught before you test |

**What it checks:**
- Does the code compile?
- Do tests pass?
- Does it actually solve the problem?

**How to trigger:** Automatic when Claude finishes tasks

---

### 7. Code Review (Requesting & Receiving)
**Get feedback on code quality**

**Requesting Review:**
- Prepares code for review
- Highlights important changes
- Explains what was done

**Receiving Review:**
- Accepts feedback gracefully
- Makes suggested improvements
- Explains any disagreements

**How to trigger:** Say "review this code" or "what do you think of this?"

---

### 8. Parallel Agents
**Do multiple things at once**

| Without It | With It |
|------------|---------|
| One thing at a time | Multiple tasks simultaneously |
| Slow for big jobs | Fast exploration |

**Good for:**
- Searching large codebases
- Checking multiple files
- Running independent tasks

**How to trigger:** Say "search in parallel" or "explore the codebase"

---

### 9. Git Worktrees
**Work on multiple branches safely**

**What it does:**
- Keeps different features separate
- No need to stash/switch constantly
- Clean workspace per task

**How to trigger:** Say "set up a worktree" or "work on separate branch"

---

## Your Custom Commands

These are shortcuts you can type anytime:

### `/start`
**Quick session startup**

```
What it does:
1. Loads project context
2. Shows available tools
3. Gets you ready to work

When to use: Beginning of every session
```

---

### `/session`
**Full interactive setup**

```
What it does:
1. Asks what you're working on
2. Loads relevant context
3. Sets up for your specific task

When to use: When you want guided setup
```

---

### `/playtest`
**Analyze game session logs**

```
What it does:
1. Pulls logs from client AND server
2. Finds all errors
3. Creates prioritized report
4. Suggests fixes

When to use: After testing the game
```

---

### `/review`
**Check code before committing**

```
What it does:
1. Scans all changed files
2. Finds dangerous patterns
3. Reports violations
4. Suggests fixes

When to use: Before git commit
```

---

## Your Custom Agents

These activate automatically when you mention related topics:

### Combat Reviewer
**Catches multiplayer-breaking code mistakes**

```
Triggers: "combat", "damage", "authority", "check code"

Finds:
- Direct playerData changes (BAD)
- Hardcoded values (BAD)
- Missing safety checks (BAD)

Example: "Check if my combat changes are safe"
```

---

### Sync Debugger
**Finds why client and server disagree**

```
Triggers: "desync", "mismatch", "client-server", "networking"

Does:
- Compares client vs server logs
- Finds first point of disagreement
- Identifies root cause

Example: "Why is the player position different on client and server?"
```

---

### Quick Explore
**Fast codebase search**

```
Triggers: "find", "where is", "search", "look for"

Does:
- Searches across all files
- Returns file:line references
- Quick and lightweight

Example: "Where is dodge implemented?"
```

---

### Playtest Analyzer
**Full game session analysis**

```
Triggers: "playtest", "session logs", "what went wrong"

Does:
- Analyzes both client and server
- Groups errors by severity
- Creates actionable report

Example: "Analyze the last playtest"
```

---

### Bot Debugger
**Diagnoses AI behavior issues**

```
Triggers: "bot", "AI", "stuck", "not attacking"

Does:
- Traces bot decision-making
- Finds where logic fails
- Suggests fixes

Example: "The bot isn't using abilities"
```

---

## AUM-Specific Skills

These know AUM's rules and catch mistakes:

### AUM Combat Check
```
Automatically activates when editing combat code

Enforces:
- All damage through Authority
- All costs from AbilityCosts.cs
- No direct playerData changes
```

### AUM Multiplayer Patterns
```
Automatically activates for networking code

Enforces:
- Server authority for combat
- Correct input flow
- State machine safety
```

### AUM Bot Patterns
```
Automatically activates for bot code

Enforces:
- Bots only generate input
- No direct state manipulation
- Proper difficulty handling
```

---

## Cheat Sheet: What To Say

| I want to... | Say this... |
|--------------|-------------|
| Fix a bug | "Debug why X isn't working" |
| Plan a feature | "Let's brainstorm how to add X" |
| Make a big change | "Write a plan for X" |
| Check my code | "/review" |
| Analyze playtest | "/playtest" |
| Find something | "Where is X implemented?" |
| Fix desync | "Debug the client-server mismatch" |
| Fix bot | "Why isn't the bot doing X?" |
| Start working | "/start" |

---

## Pro Tips

### 1. Be Specific
```
Instead of: "Fix the combat"
Say: "Debug why fire spell doesn't damage enemies"
```

### 2. Mention the Context
```
"This only happens in multiplayer, not tutorial"
"After the dodge, the player position is wrong"
```

### 3. Use Commands Before Big Work
```
/start → /review → make changes → /review again
```

### 4. Trust the Process
When Claude uses systematic-debugging, let it complete all 4 steps. Don't rush!

---

## Remember

- **You don't need to memorize commands** - just describe what you need
- **Superpowers activate automatically** - Claude uses them when relevant
- **If something seems wrong**, say "use systematic debugging"
- **Commands start with /** - like `/start`, `/review`, `/playtest`

---

*Questions? Just ask Claude: "How do I use [feature]?"*
