# AUM Bot AI — Critical Analysis: Edge Cases, Performance, Scalability

**Date:** April 8, 2026
**Purpose:** Honest assessment of risks, edge cases, and performance constraints before committing to implementation

---

## Verified Research Sources

| Source | Type | URL | Key Takeaway |
|--------|------|-----|-------------|
| **Game AI Pro 3 Ch.13** — Mike Lewis | Book chapter (free PDF) | [PDF](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter13_Choosing_Effective_Utility-Based_Considerations.pdf) | Utility considerations multiply together; any 0 score vetoes the action |
| **Dave Mark — GDC 2010** | GDC slides | [PDF](https://media.gdcvault.com/gdc10/slides/MarkDill_ImprovingAIUtilityTheory.pdf) | Response curves replace thresholds; personality = curve shapes |
| **For Honor — GDC Bot ML** | GDC Vault talk | [GDC Vault](https://gdcvault.com/play/1035522/Streamlining-Bot-Development-in-For) | 4 weeks per hero traditionally; hybrid RL+BT bots; stamina-aware |
| **For Honor — Data-Driven** | GDC Vault talk | [GDC Vault](https://www.gdcvault.com/play/1024580/Modify-Everything-Data-Driven-Dynamic) | Modifier system: data drives AI decisions, not code branches |
| **Guerrilla (Killzone) — MP Bots** | Academic paper | [PDF](https://www.guerrilla-games.com/media/News/Files/VUA07_Verweij_Hierarchically-Layered-MP-Bot_System.pdf) | Hierarchical layers for multi-mode bots; mode-specific AI code |
| **FightingICE Competition** | IEEE/Academic | [ResearchGate](https://www.researchgate.net/publication/261051410_Fighting_game_artificial_intelligence_competition_platform) | 0.2s information delay simulates human reaction; situation classification |
| **DRL Fighting Game** | IEEE CoG 2020 | [PDF](https://ieee-cog.org/2020/papers/paper_207.pdf) | Self-play RL for fighting game mastery |
| **DDA with IL+RL** | arXiv 2024 | [HTML](https://arxiv.org/html/2408.06818v1) | Player imitation + RL opponent = 7.0/10 satisfaction vs 6.6 baseline |
| **F.E.A.R. GOAP** — Jeff Orkin | GDC/Article | [Gamedeveloper](https://www.gamedeveloper.com/design/building-the-ai-of-f-e-a-r-with-goal-oriented-action-planning) | GOAP good for strategic planning; too slow for frame-by-frame combat |
| **GOAP vs Utility vs BT** | Comparison | [Tono](https://tonogameconsultants.com/game-ai-planning/) | Utility for real-time, GOAP for planning, BT for structure |
| **Utility AI Tutorial** | Tutorial | [Shaggy Dev](https://shaggydev.com/2023/04/19/utility-ai/) | Score × multiply considerations; weighted random from top actions |
| **Zero-Allocation Unity** | Technical | [Seba's Lab](https://www.sebaslab.com/zero-allocation-code-in-unity/) | Structs 50x faster; preallocate everything; no foreach on non-arrays |
| **Microsoft — Distributed AI** | Research paper | [PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/NOSSDAV2007.pdf) | Offloading AI computation; latency-tolerant bot architectures |
| **RL for FPS Bots** | Systematic review | [MDPI](https://www.mdpi.com/1999-4893/16/7/323) | Comprehensive review of RL approaches for FPS bot AI |
| **DDA Survey** | Academic | [arXiv](https://arxiv.org/pdf/2007.07220) | Explores flow state maintenance through difficulty adjustment |

---

## Critical Edge Cases We MUST Handle

### 1. Multi-Mode Consistency (1v1 vs 1v5 vs 2v2 vs 3v3)

**The problem:** The Killzone postmortem explicitly states that bot code for one game mode "cannot be reused or converted easily" to another mode. Each mode has different objectives.

**AUM-specific risks:**
```
1v1:  Bot must focus 100% on single opponent. No target switching.
      Risk: over-tuned for 1v1 feels robotic in group fights.

1v5 (FFA):  Bot must handle 5 threats simultaneously.
      Risk: target oscillation (switching every tick), mob behavior
      (all bots gang up on one player), ignoring flanking attacks.

2v2:  Bot must coordinate with teammate.
      Risk: both bots attack same target while ignoring the other
      team member. No team awareness.

3v3:  Six-player chaos.
      Risk: performance budget with 5 bots × utility scoring.
      Every bot evaluating every action every 150ms.
```

**What we must build:**
- **Mode-aware target selection** — different scoring weights per mode
- **Team awareness layer** — track what teammate is doing, don't duplicate
- **Threat assessment per-mode** — in FFA, threats come from all directions
- **Performance scaling** — reduce eval frequency as bot count increases

### 2. Resource State Desync

**The problem:** Bot reads `player.focus.CurrentFocus` and decides to cast a spell. Between the decision tick and the execution tick (8-14 ticks later = 130-230ms), the player might take damage that changes their state, or focus might decay.

**AUM-specific risks:**
```
Tick 100: Bot reads focus=25, decides CastSpell0
Tick 108: Bot executes CastSpell0
          BUT focus decayed to 22 between ticks (partial segment decay after 10s)
          Server rejects at OnSpellAnticipateUpdate → Idle
          Client sees: anticipation animation flicker → Idle

Result: Bot stutters. Looks glitchy. Player sees failed cast attempt.
```

**What we must build:**
- **Re-validate resources at execution time**, not just decision time
- **Cooldown buffer** — don't attempt action unless resource is above cost + safety margin
- **Graceful rejection handling** — if server rejects, don't retry immediately

### 3. Stuck States / Infinite Loops

**The problem:** Research on AI agents shows "Loop Drift" — when an agent misinterprets termination signals and enters endless loops. We've already seen this with our bots (stuck at obstacles, permanent Defensive mode, MantraMuktha at origin).

**AUM-specific risks:**
```
- Bot enters Special_Aiming but release never fires → stuck in aiming forever
- Bot tries to reach target behind obstacle → walks into wall forever
- Bot in Survival mode at 14% HP → never exits (HP doesn't regen)
- Two bots in Defensive mode facing each other → neither approaches → deadlock
- Bot's target dies → null target → exception → bot stops updating
```

**What we must build:**
- **Watchdog timer** — if bot produces identical input for N ticks, force reset
- **State timeout** — if in any FSM state for >5 seconds without progress, force Idle
- **Null target recovery** — always have a fallback (nearest enemy, center of arena)
- **Action attempt limit** — if action fails 3 times, blacklist it for N seconds

### 4. Performance Budget

**The hard numbers:**

```
Server tick rate: 60Hz → 16.67ms per tick
Max bots per match: 5 (in 1v5)
AI budget per tick: 7ms (per original design doc)
Budget per bot: 7ms / 5 = 1.4ms per bot per tick

What fits in 1.4ms:
  ✅ 20-30 utility curve evaluations (each ~0.01ms)
  ✅ 2-5 CapsuleCast obstacle checks (~0.01ms each)
  ✅ 1 strategy evaluation (~0.05ms)
  ✅ State reading (~0.1ms)
  ❌ NavMesh.CalculatePath (~0.1-0.3ms) — borderline
  ❌ Any memory allocation (GC stall risk)
  ❌ Deep MCTS/RL inference (10-100ms)
```

**Zero-allocation mandate** (from Seba's Lab research):
```
BANNED in bot AI hot path:
  ❌ new List<T>() — preallocate at Start()
  ❌ foreach on non-array — use for(int i=0; ...)
  ❌ LINQ (Any, Where, Select) — manual loops
  ❌ string concatenation — only in debug/telemetry
  ❌ Lambda captures — use static methods or cached delegates
  ❌ params keyword — fixed-size arrays

REQUIRED:
  ✅ Structs for ActionScore, GameState, CurveParams
  ✅ Pre-allocated arrays for action scoring (max 15 actions)
  ✅ Pre-allocated arrays for target scoring (max 6 targets)
  ✅ Cached curve parameters (don't recompute each tick)
  ✅ Telemetry only when enabled (compile-out or flag-guard)
```

### 5. Determinism and Replay Consistency

**The problem:** AUM uses server-authoritative architecture. Bot decisions happen server-side. But if we use `Random.Range()` for weighted random selection, the bot behavior is non-deterministic — can't reproduce bugs.

**What we should do:**
- **Seeded RNG per bot** — each bot gets its own `System.Random` with match-specific seed
- **Decision log** — telemetry captures enough state to reproduce any decision
- **Not critical for launch** but important for debugging

### 6. Dynamic Difficulty Without Revealing It

**The problem:** The DDA research shows that players rate adaptive opponents 7.0/10 vs static opponents 6.6/10. But if players NOTICE the adjustment, they feel cheated.

**AUM-specific approach:**
```
DON'T: Make bots obviously easier when player is losing
  ❌ Reduce bot damage at low player HP
  ❌ Make bots stop attacking when player is stunned
  ❌ Visible "mercy" moments

DO: Adjust through personality parameters (invisible)
  ✅ Increase reaction time by 50ms (player won't notice)
  ✅ Increase mistake chance by 5% (looks like real mistakes)
  ✅ Reduce combo depth by 1 hit (less pressure, not obvious)
  ✅ Shift strategy toward "Zone" instead of "Pressure" (natural variation)
```

---

## Performance Architecture (Critical for 5-Bot Matches)

```
TICK BUDGET: 16.67ms total
├── Physics/Movement:     5ms
├── Combat/Projectiles:   3ms  
├── Bot AI (all 5 bots):  7ms  ← OUR BUDGET
│   ├── Bot 1:  1.4ms
│   │   ├── State read:   0.10ms
│   │   ├── Strategy:     0.05ms  (only every 60-180 ticks)
│   │   ├── Tactics:      0.30ms  (only every 10-18 ticks)
│   │   ├── Execution:    0.15ms  (every tick)
│   │   ├── Obstacles:    0.05ms  (1-2 CapsuleCasts)
│   │   ├── Movement:     0.02ms
│   │   ├── Input build:  0.05ms
│   │   └── Telemetry:    0.02ms  (when enabled)
│   ├── Bot 2:  1.4ms
│   ├── Bot 3:  1.4ms
│   ├── Bot 4:  1.4ms
│   └── Bot 5:  1.4ms
└── Network/Snapshot:     1.67ms

KEY OPTIMIZATION: Not all layers run every tick!
  - Strategy: once per 1-3 seconds (60-180 ticks)
  - Tactics: once per 150-300ms (9-18 ticks)
  - Execution: every tick (movement, aim)
  - Obstacles: every tick but only 1-2 casts

Amortized cost per bot per tick: ~0.35ms
Peak cost (all layers evaluate): ~1.4ms (happens rarely)
```

### Struct-Based State (Zero Allocation)

```csharp
// ALL bot state in a single struct — no heap allocation
public struct BotGameState
{
    // Self
    public float wpPercent;      // 0-1
    public float staminaPercent; // 0-1
    public int focusPoints;      // 0-100
    public int focusSegments;    // 0-4
    public float distToTarget;
    public bool isMuted;
    public bool isStunned;
    
    // Target
    public float targetWPPercent;
    public float targetStamina;
    public int targetFocus;
    public bool targetAttacking;
    public bool targetVulnerable;
    public bool targetShielded;
    
    // Match
    public int aliveEnemies;
    public int aliveAllies;
    public float matchTimeRemaining;
}
// 72 bytes — fits in CPU cache line
// Read ONCE per tick, passed by ref to all layers
```

### Pre-Allocated Action Scoring

```csharp
// Fixed-size array, allocated once at bot Start()
private ActionScore[] actionScores = new ActionScore[15]; // max actions per style
private int actionCount;

public struct ActionScore  // 12 bytes, value type
{
    public byte actionId;
    public float score;
    public float randomWeight; // for weighted random selection
}

// Score all actions — zero allocation
public void ScoreActions(ref BotGameState state)
{
    actionCount = 0;
    // Each style populates its own actions
    styleCatalog.PopulateActions(ref state, actionScores, ref actionCount);
    
    // Sort by score (insertion sort — fast for <15 items, no allocation)
    InsertionSort(actionScores, actionCount);
}
```

---

## What Could Go Wrong (Honest Risk Assessment)

### Risk 1: Over-Engineering
**Probability: MEDIUM**
The 3-layer system with response curves is more complex than the current FSM. If curves aren't tuned well, the bot might behave WORSE than the current patched version.

**Mitigation:** Build incrementally. Get Layer 3 (execution) working first with simple hardcoded decisions. Then add Layer 2 (tactics). Then Layer 1 (strategy). Each layer is independently testable.

### Risk 2: Curve Tuning Hell
**Probability: HIGH**
With 15 actions × 8 considerations × 5 styles × 5 personalities = 3,000 curve parameters to potentially tune. This is a combinatorial explosion.

**Mitigation:** 
- Start with LINEAR curves everywhere (exponent = 1.0)
- Only switch to power/logistic curves where playtesting reveals problems
- Personality modifies 6 multipliers, not individual curves
- Use telemetry to identify which curves matter most

### Risk 3: Weighted Random Feels Random
**Probability: LOW-MEDIUM**
If the top 3 actions have similar scores, the weighted random selection might produce erratic behavior — dodge, then attack, then reposition, then dodge again.

**Mitigation:**
- Decision throttling (200ms minimum between action changes)
- Strategy inertia (2s minimum between strategy changes)
- Action commitment (once started, complete the action)

### Risk 4: Performance Regression
**Probability: LOW**
The utility scoring is ~20 multiplications per action × 15 actions = 300 operations. At ~0.001ms per multiplication, that's 0.3ms — within budget.

**Mitigation:**
- Profile with Unity Profiler from day 1
- Telemetry tracks eval time per bot
- LOD system: reduce eval frequency for distant bots

### Risk 5: Mode-Specific Bugs
**Probability: HIGH**
1v5 with 5 bots has never worked correctly even with the simple system. The new system introduces more complexity.

**Mitigation:**
- Test EVERY mode at each milestone
- Telemetry shows action distribution per mode per bot
- Mode-specific integration tests

---

## Updated Implementation Plan (with risk mitigations)

### Phase 1: Foundation + Execution (Week 1)
Build the execution layer first — extract and clean up input building from current Bot.cs. This is the lowest risk because it's mostly refactoring existing working code.

Deliverables:
- `ResponseCurve.cs` — simple math (4 curve types)
- `BotStateReader.cs` — struct-based state capture
- `BotExecutor.cs` — extracted from current Bot.cs input building
- `PersonalityVector.cs` — 6 floats with presets

**Test:** Bot can move and attack using hardcoded decisions. All 5 styles work. All modes (1v1, 1v5, 2v2, 3v3) don't crash.

### Phase 2: Tactical Layer (Week 2)
Build the utility scorer. This is the core innovation.

Deliverables:
- `ActionCatalog.cs` base + 5 style implementations
- `BotTactician.cs` — utility scoring with weighted random
- Wire into BotExecutor

**Test:** Bot makes sensible decisions in 1v1. Each style plays differently. Focus is validated before spell attempts. Astra is used when available.

### Phase 3: Strategic Layer + Multi-Mode (Week 3)
Add strategy selection, mode awareness, and team behavior.

Deliverables:
- `BotStrategy.cs` — strategy with inertia
- `EmotionalState.cs` — mood system
- Mode-specific target selection weights
- Team awareness (don't duplicate teammate's target)

**Test:** Bot behavior varies over the course of a match. 1v5 has reasonable target distribution. 2v2 bots don't both attack the same target.

### Phase 4: Polish + Safety (Week 4)
Add watchdog, decision throttling, mistake injection, and tune curves.

Deliverables:
- `BotWatchdog.cs` — stuck detection + recovery
- `DecisionThrottler.cs` — min time between changes
- `MistakeInjector.cs` — gaussian noise on decisions
- Curve tuning pass based on telemetry data

**Test:** Extended play sessions (10+ matches). No stuck states. No crashes. Bot feels competitive but beatable. Each personality is distinguishable.

---

## Architecture Diagram (Final)

```
┌──────────────────────────────────────────────────────────────────────┐
│                              BOT BRAIN                               │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    SHARED STATE (struct)                     │    │
│  │  BotGameState: WP, Stamina, Focus, Distance, Target, Mode  │    │
│  │  Read ONCE per tick. Passed by ref. Zero allocation.        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│           │                    │                    │                │
│  ┌────────▼───────┐  ┌───────▼────────┐  ┌───────▼────────┐       │
│  │  STRATEGY      │  │  TACTICS       │  │  EXECUTION     │       │
│  │  (1-3s eval)   │  │  (150-300ms)   │  │  (every tick)  │       │
│  │                │  │                │  │                │       │
│  │  Reads:        │  │  Reads:        │  │  Reads:        │       │
│  │  - Resources   │  │  - Strategy    │  │  - Chosen action│      │
│  │  - Match state │  │  - All actions │  │  - Target pos  │       │
│  │  - Emotion     │  │  - Curves      │  │  - Obstacles   │       │
│  │                │  │  - Personality  │  │                │       │
│  │  Outputs:      │  │                │  │  Outputs:      │       │
│  │  - Strategy    │  │  Outputs:      │  │  - KeyInput    │       │
│  │    (with 2s    │  │  - Best action │  │  - Camera rot  │       │
│  │     inertia)   │  │    (weighted   │  │  - Ability pos │       │
│  │                │  │     random)    │  │                │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│           │                    │                    │                │
│  ┌────────▼────────────────────▼────────────────────▼───────┐      │
│  │                    SAFETY SYSTEMS                         │      │
│  │  Watchdog: stuck detection + forced recovery              │      │
│  │  Throttler: min 200ms between action changes              │      │
│  │  Validator: re-check resources before execution           │      │
│  │  Watchdog: if same input 60+ ticks → force reposition    │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  PERSONALITY   │  │  STYLE CATALOG │  │  EMOTION       │         │
│  │  6 floats      │  │  Per-style     │  │  Confident     │         │
│  │  Modifies ALL  │  │  unique actions│  │  Focused       │         │
│  │  curves        │  │  + ranges      │  │  Anxious       │         │
│  │                │  │  + priorities  │  │  Desperate     │         │
│  │  Berserker     │  │                │  │  Tilted        │         │
│  │  Guardian      │  │  Amuktha       │  │                │         │
│  │  Trickster     │  │  MukthaMuktha  │  │  Modifies      │         │
│  │  Tactician     │  │  MantraMuktha  │  │  utility scores│         │
│  │  Wildcard      │  │  PaniMuktha    │  │  + reaction    │         │
│  │                │  │  YantraMuktha  │  │    time        │         │
│  └───────────────┘  └────────────────┘  └────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## The Honest Answer: Can We Build This?

**YES, but with caveats:**

1. **Week 1 is low risk** — it's mostly refactoring existing working code into cleaner structure
2. **Week 2 is the make-or-break** — the utility scorer either works or the whole approach fails. But the math is simple (multiply numbers together), and we have telemetry to debug
3. **Week 3 adds complexity** — multi-mode and team awareness are genuinely hard. Killzone developers said this code can't be easily reused across modes
4. **Week 4 is polish** — if weeks 1-3 work, this is just tuning

**The biggest risk is curve tuning** — but we start with simple linear curves and only add complexity where needed. The telemetry system (already built) is our safety net.

**What I will NOT do:**
- Promise the bot will feel perfect on first implementation
- Skip testing any mode (1v1, 1v5, 2v2, 3v3)
- Over-engineer with ML/RL (too complex, not enough training data)
- Ignore the performance budget (must stay under 1.4ms per bot)
