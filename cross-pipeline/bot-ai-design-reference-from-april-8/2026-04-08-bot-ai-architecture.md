# AUM Bot AI Architecture — Design Document

**Date:** April 8, 2026
**Status:** Research Complete — Ready for Implementation Planning
**Goal:** Replace patched FSM bot with proper multi-layered Utility AI

---

## Research Sources

### Books & Foundational Work
- **Dave Mark — "Behavioral Mathematics for Game AI"** (2009) — The foundational text on Utility AI with response curves. Defines how to convert game state into smooth utility scores instead of brittle thresholds.
  - [Book Review](https://www.gbgames.com/2017/02/13/book-review-behavioral-mathematics-for-game-ai-by-dave-mark/)
  - [Barnes & Noble](https://www.barnesandnoble.com/w/behavioral-mathematics-for-game-ai-dave-mark/1118850221)
- **Game AI Pro 3, Chapter 13 — "Choosing Effective Utility-Based Considerations"** by Mike Lewis
  - [PDF (free)](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter13_Choosing_Effective_Utility-Based_Considerations.pdf)
- **Game AI Pro 2, Chapter 30 — "Modular Tactical Influence Maps"** by Dave Mark
  - [PDF (free)](https://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf)

### GDC Talks (Verified on GDC Vault)
- **"Streamlining Bot Development in For Honor with ML Automation"** — Ubisoft Montreal
  - [GDC Vault](https://gdcvault.com/play/1035522/Streamlining-Bot-Development-in-For)
  - Key: For Honor bots traditionally took 4 weeks per hero. They combined RL with behavior trees for hybrid bots.
- **"Modify Everything! Data-Driven Dynamic Gameplay Effects on For Honor"** — Ubisoft
  - [GDC Vault](https://www.gdcvault.com/play/1024580/Modify-Everything-Data-Driven-Dynamic)
  - Key: Data-driven modifier system affects AI decision-making, damage, speed, area effects.
- **"Back to the Future! Working with Deterministic Simulation in For Honor"**
  - [GDC Vault](https://www.gdcvault.com/play/1026322/Back-to-the-Future-Working)
- **"Improving AI Decision Modeling Through Utility Theory"** — Dave Mark & Kevin Dill (GDC 2010)
  - [GDC Vault Slides PDF](https://media.gdcvault.com/gdc10/slides/MarkDill_ImprovingAIUtilityTheory.pdf)
- **"Building the AI of F.E.A.R. with Goal Oriented Action Planning"** — Jeff Orkin (GOAP origin)
  - [Gamedeveloper.com](https://www.gamedeveloper.com/design/building-the-ai-of-f-e-a-r-with-goal-oriented-action-planning)

### Academic Papers (FightingICE Competition)
- **"Creating Pro-Level AI for Real-Time Fighting Game with Deep Reinforcement Learning"**
  - [ResearchGate](https://www.researchgate.net/publication/332301037_Creating_Pro-Level_AI_for_Real-Time_Fighting_Game_with_Deep_Reinforcement_Learning)
- **"Fighting game artificial intelligence competition platform"** — Ritsumeiken University
  - [ResearchGate](https://www.researchgate.net/publication/261051410_Fighting_game_artificial_intelligence_competition_platform)
- **"DareFightingICE Competition"** (IEEE CoG)
  - [arXiv](https://arxiv.org/abs/2203.01556)
- **"Mastering Fighting Game Using Deep Reinforcement Learning With Self-play"**
  - [IEEE CoG 2020 PDF](https://ieee-cog.org/2020/papers/paper_207.pdf)
- **FighterZero — Deep Learning for FightingICE**
  - [GitHub](https://github.com/MatejVitek/FighterZero)

### Dark Souls / Elden Ring AI Analysis
- **"The AI of Dark Souls"** — Tommy Thompson (AI and Games)
  - [AI and Games](https://www.aiandgames.com/p/the-ai-of-dark-souls)
  - Key: Weighted random state transitions, per-attack cooldowns, phase-based behavior shifts at HP thresholds.
- **"How Elden Ring Gets Away With Input Reading"**
  - [Game Rant](https://gamerant.com/elden-ring-input-reading-animations-boss-battles/)
  - Key: Animation reading, not input reading. Enemies respond to player animation states, not button presses.

### Architecture Comparisons
- **"Game AI Planning: GOAP, Utility, and Behavior Trees"** — Tono Game Consultants
  - [Article](https://tonogameconsultants.com/game-ai-planning/)
- **"GOBT: A Synergistic Approach Using Goal-Oriented and Utility-Based Planning in Behavior Trees"** — Journal of Multimedia Information System
  - [Paper](https://www.jmis.org/archive/view_article?pid=jmis-10-4-321)
- **"An Introduction to Utility AI"** — The Shaggy Dev
  - [Tutorial](https://shaggydev.com/2023/04/19/utility-ai/)
- **Utility System — Wikipedia**
  - [Wikipedia](https://en.wikipedia.org/wiki/Utility_system)

---

## Why the Current System Is Wrong

```
CURRENT (Patched FSM):                      WHAT WE NEED (Utility AI):

  if (hp < 15%) → SURVIVAL                    Every action gets a SCORE
  if (hp < 30%) → DEFENSIVE                   Score = curve(resource) × curve(threat) × personality
  if (targetLow) → OFFENSIVE                  Top 3 scores → weighted random pick
  else → POSITIONAL                            No cliffs. No oscillation. Smooth behavior.
       ↓                                              ↓
  Priority 1: Survival                         All actions compete EQUALLY
  Priority 2: Threat                           Resources modify scores, not gates
  Priority 3: Opportunity                      Personality = different curve shapes
  Priority 4: Resource                         Style = different action catalog
  Priority 5: Elemental                        Emotional state = score modifier
  Priority 6: Position
  Priority 7: Default

PROBLEMS:                                    BENEFITS:
❌ Cliff-edge behavior changes               ✅ Smooth transitions
❌ Oscillation at thresholds                  ✅ No oscillation (curves are continuous)
❌ Personality = hardcoded branches           ✅ Personality = 6 numbers
❌ Style + personality tangled together       ✅ Style = action catalog (separate)
❌ Same code for all styles                   ✅ Each style has unique actions
❌ Can't tune without code changes            ✅ Tune by editing numbers, not code
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BOT BRAIN                                │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   LAYER 1    │   │   LAYER 2    │   │   LAYER 3    │       │
│  │  STRATEGIC   │──▶│  TACTICAL    │──▶│  EXECUTION   │       │
│  │  (1-3 sec)   │   │ (150-300ms)  │   │ (every tick) │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│        │                   │                   │                │
│   "What am I         "What action        "How do I             │
│    trying to do?"     right now?"         perform it?"          │
│                                                                 │
│  Strategies:          Score ALL legal     - Aim direction       │
│  - Pressure           actions through     - Movement path       │
│  - Zone               response curves     - Reaction delay      │
│  - Punish             Pick from top 3     - Animation timing    │
│  - Survive            via weighted        - Obstacle avoid      │
│  - Execute            random                                    │
│  - BuildResource                                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              SHARED STATE (read-only)                │       │
│  │  Resources: WP, Stamina, Focus                       │       │
│  │  Distance, Target state, Own state                   │       │
│  │  Emotional state, Match timer                        │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐                           │
│  │ PERSONALITY  │   │   STYLE      │                           │
│  │ (6 floats)   │   │  ACTION      │                           │
│  │ Modifies     │   │  CATALOG     │                           │
│  │ all curves   │   │ (per style)  │                           │
│  └──────────────┘   └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## How Response Curves Work (The Core Innovation)

Instead of: `if (stamina < 30) don't dodge`
We use: `dodge_score *= staminaCurve(stamina / maxStamina)`

```
CURVE EXAMPLES:

Aggressive Bot (Berserker)              Cautious Bot (Guardian)
Stamina Spend Willingness               Stamina Spend Willingness

1.0 ┤ ████████████████████             1.0 ┤                  ██
    │ █████████████████                    │                ██
    │ ██████████████                       │             ███
0.5 ┤ ████████████                    0.5 ┤          ███
    │ ██████████                           │       ███
    │ ████████                             │    ███
0.0 ┤ ██████                          0.0 ┤ ███
    └──────────────────                    └──────────────────
    0%    50%    100%                      0%    50%    100%
         Stamina %                              Stamina %

    x^0.3 (nearly flat)                    x^2.5 (steep curve)
    "I'll dodge even at low stamina"       "Only dodge if nearly full"


SAME CODE, different curve exponent. That's it.
```

---

## Action Scoring Example

When the bot evaluates "Should I cast Earth spell?":

```
earth_spell_score =
    base_value(0.5)                                    // Earth spell is decent
  × strategy_fit(currentStrategy == Pressure ? 1.2     // Good fit for pressure
                 : currentStrategy == Zone ? 0.6        // Bad fit for zoning
                 : 1.0)                                 // Neutral otherwise
  × focus_curve(currentFocus / 25)                     // SMOOTH: low focus = low score
  × stamina_safety(currentStamina / maxStamina)        // Don't cast if can't dodge after
  × distance_fit(idealRange=3m, current=4m → 0.9)     // Close to ideal range
  × cooldown_ready(earthCooldown == 0 ? 1.0 : 0.0)    // Hard gate: on cooldown = 0
  × personality.aggression^0.5                          // Aggressive = cast more
  × emotional_mod(Confident ? 1.1 : Anxious ? 0.7)    // Mood affects willingness
  × target_vulnerability(stunned ? 1.5 : shielded ? 0.3)

= 0.5 × 1.2 × 0.95 × 0.8 × 0.9 × 1.0 × 0.87 × 1.1 × 1.5
= 0.59

Compare with ALL other actions:
  melee_attack_score = 0.72     ← WINNER (but not always picked)
  dodge_score = 0.31
  earth_spell_score = 0.59
  reposition_score = 0.25
  special_ability_score = 0.44
  astra_score = 0.0             (not enough focus)

Pick from top 3 via WEIGHTED RANDOM:
  melee (72%) → 52% chance
  earth (59%) → 31% chance
  special (44%) → 17% chance
```

---

## Personality System (Separate from Style)

```
PERSONALITY VECTOR (6 floats, 0 to 1):

                    ┌─────────────────────────────────────────┐
                    │         PERSONALITY PRESETS              │
                    ├─────────┬──────┬──────┬──────┬──────────┤
                    │Berserker│Guard │Trick │Tact  │Wildcard  │
┌───────────────────┼─────────┼──────┼──────┼──────┼──────────┤
│ aggression        │   0.9   │ 0.2  │ 0.6  │ 0.4  │   0.5   │
│ risk_tolerance    │   0.9   │ 0.2  │ 0.6  │ 0.3  │   0.5   │
│ patience          │   0.1   │ 0.9  │ 0.4  │ 0.7  │   0.5   │
│ adaptability      │   0.3   │ 0.5  │ 0.9  │ 0.7  │   0.5   │
│ resource_greed    │   0.1   │ 0.8  │ 0.4  │ 0.6  │   0.5   │
│ combo_preference  │   0.8   │ 0.3  │ 0.5  │ 0.7  │   0.5   │
└───────────────────┴─────────┴──────┴──────┴──────┴──────────┘

These 6 numbers modify EVERY curve in the system.
Adding a new personality = changing 6 numbers. No code changes.

5 styles × 5 personalities = 25 unique bot behaviors
```

---

## Style Action Catalogs (Each Style Is Unique)

```
AMUKTHA (Sword + Dash)                 MANTRAMUKTHA (Staff + Teleport)
├── MeleeCombo (1-3 hits)              ├── RangedAttack (projectile)
├── DashStrike (gap close)             ├── TeleportEscape (flee)
├── DashEscape (flee)                  ├── TeleportFlank (reposition)
├── DodgeCancel (defensive)            ├── SpellBarrage (multi-elemental)
├── ElementalBurst (close AoE)         ├── ElementalZone (area denial)
├── ElementalShield                    ├── ElementalShield
├── ThirdEye / Astra                   ├── ThirdEye / Astra
└── Taunt (personality-driven)         └── Kite (maintain distance)

MUKTHAMUKTHA (Axe + Throw)             PANIMUKTHA (Discus + Maim)
├── HeavyStrike (high damage)          ├── DiscusThrow (mid-range)
├── AxeThrow (ranged poke)             ├── MaimDebuff (slow enemy)
├── AxeRecall                          ├── HitAndRun (throw + retreat)
├── StaggerCombo (break guard)         ├── DiscusBarrage (multi-throw)
├── ElementalBurst (close AoE)         ├── ElementalBurst
├── ElementalShield                    ├── ElementalShield
├── ThirdEye / Astra                   ├── ThirdEye / Astra
└── TradeBlows (tank + counter)        └── SpacingControl (kite)

YANTRAMUKTHA (Bow + Impair)
├── ArrowShot (long range)
├── ChargedShot (high damage)
├── ImpairShot (debuff)
├── KiteRetreat (shoot + back)
├── ElementalSnipe (ranged spell)
├── ElementalShield
├── ThirdEye / Astra
└── TrapZone (area denial)
```

---

## Emotional State System

```
                    ┌───────────┐
              ┌────▶│ CONFIDENT │◀────┐
              │     │ HP > 70%  │     │
              │     │ +20% aggr │     │
              │     └─────┬─────┘     │
              │           │           │
         ┌────┴────┐      │     ┌─────┴────┐
         │ FOCUSED │◀─────┘────▶│ ANXIOUS  │
         │ HP ~50% │            │ HP < 40% │
         │ Optimal │            │ +30% def │
         │ play    │            │ +15% rxn │
         └────┬────┘            └─────┬────┘
              │                       │
              │     ┌───────────┐     │
              └────▶│ DESPERATE │◀────┘
                    │ HP < 25%  │
                    │ YOLO or   │
                    │ TURTLE    │
                    │(personality│
                    │ decides)  │
                    └─────┬─────┘
                          │
                    ┌─────┴─────┐
                    │  TILTED   │
                    │ 3+ hits   │
                    │ no answer │
                    │ WORSE     │
                    │ decisions │
                    │ (5s reset)│
                    └───────────┘
```

---

## Resource-Driven Decision Flow

```
RESOURCES ARE CONTINUOUS SIGNALS, NOT GATES:

WILLPOWER (Health) ─────────────────────────────────────────
100% ████████████████████████████████████████████████
 75% ████████████████████████████████████
 50% ████████████████████████   ← Strategy shifts toward "Survive"
 25% ████████████████            ← Emotional state → Desperate
  0% ████████                    ← Dead

STAMINA ────────────────────────────────────────────────────
100% ████████████████████████████████████████████████
 70% █████████████████████████████████  ← Can dodge (cost: 70)
 45% ██████████████████████             ← Can dodge (Vishnu only)
 30% █████████████████                  ← Utility curves say "don't commit"
  0% ████████                           ← Pure defense, wait for regen

FOCUS ──────────────────────────────────────────────────────
100  ████████████████████████████████████████████████ ← ASTRA! (4 bars)
 75  ████████████████████████████████████   ← Third Eye (3 bars)
 50  ████████████████████████               ← 2 spells available
 25  ████████████████                       ← 1 spell/shield available
  0  ████████                               ← Must melee to build focus

THE KEY: Focus is EARNED by hitting. This means:
  → Bots MUST be aggressive to build Focus
  → Spending Focus on spells is an INVESTMENT (hit to earn, spend to damage)
  → Saving Focus for Astra is a STRATEGIC CHOICE (personality.resource_greed)
  → Guardian personality hoards Focus → always has Astra ready
  → Berserker personality spends Focus → constant spell pressure
```

---

## Implementation Plan — File Structure

```
Assets/Scripts/Bots/
├── Core/
│   ├── BotBrain.cs              # Main coordinator (replaces Bot.cs decision loop)
│   │                            # Orchestrates 3 layers, holds state
│   ├── BotStateReader.cs        # Reads all game state into a clean struct
│   │                            # WP, Stamina, Focus, distance, target state, etc.
│   └── BotExecutor.cs           # Converts decisions to KeyInput
│                                # Handles aim, movement, reaction delay, animation
│
├── Strategy/
│   ├── BotStrategy.cs           # Layer 1: Strategic brain (1-3s eval)
│   │                            # Picks: Pressure/Zone/Punish/Survive/Execute/Build
│   └── StrategyScorer.cs        # Scores each strategy via resource curves
│
├── Tactics/
│   ├── BotTactician.cs          # Layer 2: Action selection (150-300ms eval)
│   │                            # Scores all legal actions, weighted random pick
│   ├── ActionCatalog.cs         # Base class for per-style action lists
│   └── ResponseCurve.cs         # Math: curve evaluation (power, logistic, linear)
│
├── Styles/                      # Per-style action catalogs
│   ├── AmukthaActions.cs        # Sword: dash, melee chain, dodge-cancel
│   ├── MukthaMukthaActions.cs   # Axe: heavy strikes, axe throw, stagger
│   ├── MantraMukthaActions.cs   # Staff: teleport, spell zone, kite
│   ├── PaniMukthaActions.cs     # Discus: throw, maim, spacing
│   └── YantraMukthaActions.cs   # Bow: snipe, charged shot, impair
│
├── Personality/
│   ├── PersonalityVector.cs     # 6-float vector + curve modifiers
│   ├── EmotionalState.cs        # Confident/Focused/Anxious/Desperate/Tilted
│   └── PersonalityPresets.cs    # Berserker, Guardian, Trickster, Tactician, Wildcard
│
├── Navigation/
│   ├── BotObstacleDetector.cs   # CapsuleCast obstacle avoidance (ALREADY BUILT)
│   └── BotMovementExecutor.cs   # Converts tactical position goals to joystick input
│
├── Humanization/
│   ├── BotReactionTimer.cs      # Reaction delays (ALREADY BUILT)
│   ├── DecisionThrottler.cs     # Min 200ms between action changes
│   └── MistakeInjector.cs       # Gaussian noise on decisions + execution
│
└── Debug/
    ├── BotTelemetry.cs          # Structured logging (ALREADY BUILT, enhance)
    └── BotDebugOverlay.cs       # Visual debug in editor (optional)
```

---

## Can I Actually Build This?

**YES — here's why:**

### What Already Works (Keep)
- `BotObstacleDetector.cs` — CapsuleCast obstacle avoidance ✅
- `BotReactionTimer.cs` — Reaction delays with fatigue/momentum ✅
- `BotTelemetry.cs` — Structured logging ✅
- `BotManager.cs` — Bot lifecycle, tick loop ✅
- Server combat infrastructure — KeyInput, FSM states, PlayerManager ✅
- All 5 fighting style implementations on server ✅

### What Gets Built New (in order)
1. `ResponseCurve.cs` — Simple math class (~50 lines)
2. `PersonalityVector.cs` — 6 floats + curve lookup (~80 lines)
3. `BotStateReader.cs` — Reads game state into struct (~100 lines)
4. `ActionCatalog.cs` + 5 style files — Per-style action definitions (~150 lines each)
5. `BotTactician.cs` — Utility scorer, scores actions (~200 lines)
6. `BotStrategy.cs` — Strategy selection with inertia (~150 lines)
7. `BotExecutor.cs` — Input building (extract from current Bot.cs) (~300 lines)
8. `BotBrain.cs` — Orchestrator replacing Bot.cs (~200 lines)
9. `EmotionalState.cs` — Mood tracking (~80 lines)

### Total: ~1,500 lines across 15 files
vs current: 1,600 lines in 1 monolithic file

### Build Order (Incremental — testable at each step)

```
WEEK 1: Foundation
  ├── ResponseCurve.cs + PersonalityVector.cs + BotStateReader.cs
  ├── Test: verify curves produce expected outputs
  └── MILESTONE: Math layer works

WEEK 2: Action System
  ├── ActionCatalog.cs + all 5 style files
  ├── BotTactician.cs (utility scorer)
  ├── Test: verify action scoring produces sensible rankings
  └── MILESTONE: Bot picks actions correctly (no execution yet)

WEEK 3: Execution + Integration
  ├── BotExecutor.cs (extract from current Bot.cs)
  ├── BotBrain.cs (orchestrator)
  ├── BotStrategy.cs
  ├── Wire into BotManager.cs
  ├── Test: full playtest, each style, each personality
  └── MILESTONE: Bot plays a complete match

WEEK 4: Polish
  ├── EmotionalState.cs
  ├── DecisionThrottler.cs + MistakeInjector.cs
  ├── Tune curves per style × personality
  ├── Test: 1v1, 1v5, 2v2, 3v3 across all modes
  └── MILESTONE: Bot feels human and competitive
```

---

## Key Difference from Current Approach

```
CURRENT:                                    NEW:
"Bot is in DEFENSIVE mode                  "Bot scores all 12 actions.
 so it can only dodge/retreat"              Dodge scores 0.8 because stamina is high
                                            and threat is incoming.
                                            Melee scores 0.6 because target is close.
                                            Retreat scores 0.4 because HP is ok.
                                            → Picks dodge (65%), melee (25%),
                                              retreat (10%) via weighted random"

CURRENT:                                    NEW:
"Amuktha and MukthaMuktha                  "Amuktha has DashStrike action.
 both do the same MeleeAttack"              MukthaMuktha has HeavyStrike action.
                                            Different damage, range, recovery.
                                            Each scored through SAME curves
                                            but with DIFFERENT base values."

CURRENT:                                    NEW:
"if (focus >= 25) → can cast spell"         "spell_score *= focusCurve(focus/25)
                                             where focusCurve = x^1.5
                                             So at focus=20, score *= 0.72
                                             At focus=10, score *= 0.25
                                             At focus=5, score *= 0.04
                                             → Naturally deprioritizes when low"
```

---

*This document will be updated as implementation progresses.*
