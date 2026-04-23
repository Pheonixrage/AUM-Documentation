---
date: 2026-04-10
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy
source: NotebookLM notebook "BOT AI AUM" (id b099a943-5254-4cb9-bddc-955c80ddf7c0)
query_turn: 1
notebook_sources: see below
---

# NotebookLM Response — 3-Bug Guidance (2026-04-10)

Verbatim response from the `BOT AI AUM` notebook on 2026-04-10, asked about the three bot bugs and the high-level architecture question.

## Query

I am building a bot AI for a multiplayer arena fighting game (Unity, server-authoritative 60Hz). I have three bugs to solve, and I need concrete architectural guidance grounded in the research sources you have access to. Please give me specific, actionable suggestions, citing the techniques or papers:

**BUG 1 — SPELL AOE OFFSET WRONG.** When my bot casts an AOE elemental spell (fire/water/earth ground zones), the spell is spawned with its center at the PLAYER TARGET position instead of where the spell mechanic actually places it. The spell system interprets 'abilityPos' differently for different spell types (some are center-at-cast-direction, some are origin+direction). What is the standard pattern for handling heterogeneous projectile/AOE aim vectors in a utility-AI bot? Should each ability have its own 'aim solver' that returns the correct KeyInput target position? Do you see similar patterns in any of the papers?

**BUG 2 — OBSTACLE AVOIDANCE IS BROKEN.** Currently I use a single CapsuleCast in the desired move direction with hysteresis. The bot gets stuck on corners, walks into pillars when pursuing, and can't path around concave obstacles. What is the recommended approach for short-range reactive obstacle avoidance in a combat bot that cannot use a NavMesh (arenas are small, open, with scattered blockers)? Is there a steering-behavior or potential-field approach that would work better? Any evidence in the sources of which approach works for combat bots specifically?

**BUG 3 — POST-ASTRA BOT GOES HAYWIRE.** After the bot casts its 'Astra' (a channeled ability that locks input for ~2 seconds), the bot goes into a confused state — wrong movement, wrong facing, sometimes repeatedly retrying the action — until the player walks back into melee range, after which it snaps back to normal. I suspect this is a state-machine issue where the tactician re-evaluates during the blocked-input window and accumulates stale decisions. What's the canonical pattern for handling 'committed actions' in a utility AI or behavior tree so the bot doesn't re-plan mid-execution? Any examples in the papers?

Please also give me a high-level diagnosis of whether my current architecture (layer 1: strategy, layer 2: tactician utility scoring, layer 3: executor) is the right shape, or if I should adopt something different like GOAP or HTN given the constraints.

Respond with concrete, referenced recommendations.

## Response (verbatim)

Based on the research sources and the specific mechanics of your game, your hybrid architecture is already on the right track. Here is the concrete, actionable guidance to solve your three bugs and validate your architectural approach.

### BUG 1: SPELL AOE OFFSET WRONG

**Diagnosis:** You are passing a single `abilityPos` directly from your target's root position, but different spells require different geometric solvers.

**Standard Pattern & Recommendation:**
Yes, each ability (or category of abilities) must have its own decoupled "Aim Solver" or "Target Data" generator. This is a canonical pattern seen in robust engines like Unreal's Gameplay Ability System (GAS), which separates the instigator's logic from the targeting logic using a specialized `Wait Target Data` task and `TargetData` payload structs [1, 2].

**Actionable Fix:**
1. **Abstract your targeting:** Create an `IAimSolver` interface with a `CalculateAbilityPos()` method.
2. **AoE Solver (Center of Mass):** For circular AoE spells, do not aim at a single player. Instead, query the environment for all enemies within the spell's maximum cast range. Calculate their "Center of Mass" (average position). If the AoE radius doesn't cover all of them at that point, iteratively drop the furthest enemy from the calculation until you find the optimal center that maximizes targets hit [3].
3. **Directional/Rectangular Solver:** For non-circular AoEs (like a wave or breath attack), the math is more complex. The solver must iterate through each enemy as a primary target and test various rotational orientations to see which angle maximizes secondary targets [3].
4. Your Utility AI should trigger the specific `AimSolver` to calculate and write the final `abilityPos` Vector3 to the bot's Blackboard **before** the Execution layer triggers the KeyInput.

### BUG 2: OBSTACLE AVOIDANCE IS BROKEN

**Diagnosis:** A single CapsuleCast is binary (hit or no hit) and lacks the peripheral context needed to slide around obstacles smoothly, leading to the bot getting stuck.

**Standard Pattern & Recommendation:**
For small, open combat arenas where NavMeshes are too rigid or expensive for micro-movements, the recommended approach is a **Raycast-based Steering Behavior** utilizing a "repel force" [4, 5], originally pioneered by Craig Reynolds [6]. Alternatively, Artificial Potential Fields (APF) are highly effective for reactive avoidance [7, 8].

**Actionable Fix:**
Instead of one CapsuleCast, use a multi-ray "whisker" approach.
1. Cast 3 to 5 rays from the bot: one directly forward, and others angled at ±30° and ±60° [4].
2. When a peripheral ray hits an obstacle, calculate the distance to the hit.
3. Generate a `repelForce` vector that points away from the obstacle's normal [4, 5]. The intensity of this force should scale inversely with the distance to the obstacle.
4. Add this `repelForce` to the bot's desired movement vector. This naturally "steers" the bot to slide around convex corners and pillars rather than walking directly into them and dead-stopping.

### BUG 3: POST-ASTRA BOT GOES HAYWIRE

**Diagnosis:** Your BT's Executor layer is losing synchronization with the game's Finite State Machine (FSM). The FSM locks inputs during the 2-second Astra channel, but your Utility tactician is still evaluating and queuing new BT actions.

**Standard Pattern & Recommendation:**
The canonical pattern for "committed actions" in a Behavior Tree is the **Running** status, combined with strict FSM input blocking [9, 10].

**Actionable Fix:**
1. **Return RUNNING:** When the BT executes the `ExecuteAstra` leaf node, the node must return the `Running` status (not `Success`) for the entire 2-second duration of the channel [9, 11]. Because the node is `Running`, the BT will not attempt to select or execute a new branch on subsequent ticks [12].
2. **Listen to the FSM:** The leaf node should monitor the game's actual FSM. According to AUM's design document, `Cast_Spell` and `Astra` states have `BlockFlags` that prevent entering other states [10]. The BT node should only return `Success` once the FSM broadcasts that the Astra state is complete and input is unlocked.
3. **Pause Utility Scoring:** Add a "Decorator" (conditional node) at the root of your tree or tactician that checks `IsBlockingInput()`. If the bot is locked in an animation, bypass the utility scoring completely until the bot is free to act again.

### High-Level Architecture Diagnosis

**Is your 3-layer architecture (Strategic -> Utility -> BT Executor) correct?**
**Yes, absolutely.** This hybrid approach represents the "gold standard" for creating intelligent, adaptive NPCs in modern Unity combat games [13].

- **Utility AI** acts as the "brain" to handle the nuanced, analog decisions of **what** to do (e.g., "Is it more valuable to heal or attack right now?") [14, 15].
- **Behavior Trees** handle the **how** — executing the moment-to-moment sequences in a structured, visual, and easy-to-debug way [15, 16].

**Should you use GOAP or HTN instead?**
**No, stay away from them for this specific project.** While GOAP is famous for games like *F.E.A.R.* [17], the sources strongly warn that for small teams, GOAP "hungers for hapless AI engineers... chances are you'd get stuck in AI development hell" [18]. Hierarchical Task Networks (HTN) face similar issues; developers often find they become "unmanageable" for complex action-melee combat due to the sheer explosion of branches and task decomposition [19, 20].

Your current architecture perfectly balances the dynamic adaptability of Utility AI with the authoring ease of Behavior Trees [13, 21]. Stick with it, implement the `Running` state locks, decouple your aim solvers, and add raycast steering, and your bots will feel incredibly human.

## Notebook sources cited (tags [1]–[21])

NotebookLM cited numbered references [1]–[21]. The source list in the notebook includes (at the time of query):
- "Fortnite Lobbies Can Now Have Up to 92% Bots" — VICE
- "Kiting in RTS games using influence maps" — ResearchGate (PDF)
- "Modelling a Human-Like Bot in a First Person Shooter Game" — ResearchGate (PDF)
- "2022 IEEE Conference on Games (CoG) Program"
- "3.5 PREDICTING PHYSICS" — Dept of Computer Science (PDF)
- "A Comprehensive Review of Multi-Agent Reinforcement Learning in Video Games" — arXiv (PDF)
- "A Game AI Approach to Autonomous..." (cut off in list query)
- plus additional sources not enumerated in the list preview

For the full source list, run:
```bash
~/.local/bin/notebooklm source list
```

## Conversation metadata

- **Conversation ID:** `57586ab6-5ca8-4436-a2bb-f9d2f34536ce`
- **Notebook ID:** `b099a943-5254-4cb9-bddc-955c80ddf7c0`
- **Turn:** 1 (fresh conversation)

To continue this conversation in a future session without creating a new one, use:
```bash
~/.local/bin/notebooklm use b099a943-5254-4cb9-bddc-955c80ddf7c0
~/.local/bin/notebooklm ask "<followup question>"
```
