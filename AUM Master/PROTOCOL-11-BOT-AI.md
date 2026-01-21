# PROTOCOL-11-BOT-AI.md
# Bot AI System - Behavior Tree Architecture

## Overview

The AUM bot system uses a **Behavior Tree** architecture to control server-side AI opponents. Bots run entirely on the server at a 60Hz tick rate (16.7ms per tick) and simulate player input through the same `KeyInput` structure used by real players.

**Key Files:**
- `Assets/Scripts/Bots/Bot.cs` - Main bot controller
- `Assets/Scripts/Bots/Behaviour Tree/BotBT.cs` - Behavior tree structure
- `Assets/Scripts/Managers/BotManager.cs` - Bot lifecycle management
- `Assets/Scripts/Bots/Behaviour Tree/*.cs` - Core tree classes
- `Assets/Scripts/Bots/Behaviour Tree/Custom Action Nodes/*.cs` - Action nodes

---

## 1. Bot State Machine

### 1.1 BotState Enum

```csharp
public enum BotState
{
    DISABLED,         // Bot does nothing (tutorial intro)
    MELEEACTION,      // Bot can only perform melee attacks
    SPELLMELEEACTION, // Bot can perform melee AND spells (no shields)
    FULL,             // Bot has full combat capabilities
}
```

### 1.2 State Transitions

```
Match Start Flow:
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  DISABLED ──────────────────┐                                  │
│      │                      │                                  │
│      │ (Tutorial only)      │ (Normal match: StartMatch())     │
│      ▼                      ▼                                  │
│  MELEEACTION ──────────► FULL                                  │
│      │                                                         │
│      ▼                                                         │
│  SPELLMELEEACTION                                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 State Capabilities Matrix

| BotState          | Movement | Melee | Spells | Shields | Target Acquisition |
|-------------------|----------|-------|--------|---------|-------------------|
| DISABLED          | ✗        | ✗     | ✗      | ✗       | ✗                 |
| MELEEACTION       | ✓        | ✓     | ✗      | ✗       | ✓                 |
| SPELLMELEEACTION  | ✓        | ✓     | ✓      | ✗       | ✓                 |
| FULL              | ✓        | ✓     | ✓      | ✓       | ✓                 |

---

## 2. Behavior Tree Architecture

### 2.1 Node States

```csharp
public enum NodeState
{
    RUNNING,   // Node is still executing (continue next tick)
    SUCCESS,   // Node completed successfully
    FAILURE    // Node failed to complete
}
```

### 2.2 Core Node Classes

#### Base Node (`Node.cs`)

```csharp
namespace BehaviourTree
{
    public class Node
    {
        protected NodeState state = NodeState.FAILURE;
        protected List<Node> children = new List<Node>();
        public Node parent;
        public Dictionary<string, object> sharedData = new Dictionary<string, object>();

        // Get/Set shared data (propagates up tree)
        public void SetData(string key, object value);
        public object GetData(string key);
        public bool ClearData(string key);

        // Traverse to root for shared data access
        public Node GetRootNode();

        // Override in subclasses
        public virtual NodeState Evaluate();
    }
}
```

#### Selector Node (`Selector.cs`)

A **Selector** (OR node) tries children in order and succeeds on first SUCCESS.

```csharp
public class Selector : Node
{
    public override NodeState Evaluate()
    {
        foreach (Node node in children)
        {
            switch (node.Evaluate())
            {
                case NodeState.FAILURE:
                    continue;              // Try next child
                case NodeState.SUCCESS:
                    return NodeState.SUCCESS;  // Stop, we succeeded
                case NodeState.RUNNING:
                    return NodeState.RUNNING;  // Wait for this child
            }
        }
        return NodeState.FAILURE;  // All children failed
    }
}
```

#### Sequence Node (`Sequence.cs`)

A **Sequence** (AND node) requires all children to succeed.

```csharp
public class Sequence : Node
{
    public override NodeState Evaluate()
    {
        bool isAnyChildRunning = false;
        foreach (Node node in children)
        {
            switch (node.Evaluate())
            {
                case NodeState.FAILURE:
                    return NodeState.FAILURE;  // Stop, sequence failed
                case NodeState.SUCCESS:
                    continue;                  // Try next child
                case NodeState.RUNNING:
                    isAnyChildRunning = true;
                    continue;
            }
        }
        return isAnyChildRunning ? NodeState.RUNNING : NodeState.SUCCESS;
    }
}
```

#### Tree Base (`Tree.cs`)

```csharp
public abstract class Tree : MonoBehaviour
{
    public Node root = null;

    public void Setup()
    {
        root = SetupTree();
    }

    public abstract Node SetupTree();
}
```

### 2.3 Shared Data Keys

The behavior tree communicates through shared data stored at the root node:

| Key                     | Type      | Description                                |
|-------------------------|-----------|-------------------------------------------|
| `LocalBot`              | `Player`  | Reference to the bot's Player instance     |
| `target`                | `Player`  | Current target player                      |
| `InputVector`           | `Vector2` | Movement joystick input                    |
| `CameraAngle`           | `float`   | Y-axis rotation for facing direction       |
| `Melee`                 | `int`     | Flag to trigger melee attack (value = 1)   |
| `SelectedElemental`     | `int`     | Index of elemental to cast (0-3)           |
| `SelectedElementalShield` | `int`   | Index of elemental shield to raise (0-3)   |

---

## 3. Complete Behavior Tree Structure

### 3.1 Tree Definition (`BotBT.cs`)

```csharp
public class BotBT : BehaviourTree.Tree
{
    public override Node SetupTree()
    {
        Node root = new Selector(new List<Node>
        {
            // Priority 1: Check if bot is dead (early exit)
            new IsBotDead(),

            // Priority 2: Defensive spell when damaged
            new Sequence(new List<Node>
            {
                new IsBotStateSpells(),      // Can cast spells?
                new CheckPlayerDamaged(),    // Took significant damage?
                new CastDefenseSpell()       // Raise shield
            }),

            // Priority 3: Switch targets periodically
            new Sequence(new List<Node>
            {
                new HasTargetReachedTimeThreshold(),  // Time to switch?
                new CheckPlayerDamaged(),             // (condition check)
                new SetRandomTarget()                 // Pick new target
            }),

            // Priority 4: Cast offensive spells
            new Sequence(new List<Node>
            {
                new IsBotStateSpells(),      // Can cast spells?
                new TargetWithinRange(),     // Target in spell range?
                new CastSpell()              // Cast random elemental
            }),

            // Priority 5: Melee attack
            new Sequence(new List<Node>
            {
                new IsBotStateMelee(),       // Can melee?
                new TargetWithinRange(),     // Target in range?
                new Attack()                 // Perform melee attack
            }),

            // Priority 6: Movement (always runs if enabled)
            new Sequence(new List<Node>
            {
                new IsBotStateEnabled(),     // Bot not disabled?
                new Selector(new List<Node>
                {
                    new Sequence(new List<Node>
                    {
                        new IsTargetNull(),      // No target?
                        new GetNearestEnemy()    // Find one
                    }),
                    new Node(NodeState.SUCCESS)  // Have target, continue
                }),
                new MoveToTarget()           // Move toward target
            })
        });
        return root;
    }
}
```

### 3.2 Visual Tree Diagram

```
ROOT (Selector - OR)
├── [1] IsBotDead
│       └─ SUCCESS if dead → stops all behavior
│       └─ FAILURE if alive → continue to next
│
├── [2] Defense Sequence (AND)
│   ├── IsBotStateSpells
│   ├── CheckPlayerDamaged (damage >= 2500)
│   └── CastDefenseSpell
│
├── [3] Target Switch Sequence (AND)
│   ├── HasTargetReachedTimeThreshold (5-10 sec)
│   ├── CheckPlayerDamaged
│   └── SetRandomTarget
│
├── [4] Spell Cast Sequence (AND)
│   ├── IsBotStateSpells
│   ├── TargetWithinRange
│   └── CastSpell (10 sec cooldown)
│
├── [5] Melee Attack Sequence (AND)
│   ├── IsBotStateMelee
│   ├── TargetWithinRange
│   └── Attack (1.8 sec rate)
│
└── [6] Movement Sequence (AND)
    ├── IsBotStateEnabled
    ├── Target Acquisition (Selector)
    │   ├── Sequence: IsTargetNull → GetNearestEnemy
    │   └── Node(SUCCESS) - fallback
    └── MoveToTarget
```

---

## 4. Action Node Implementations

### 4.1 State Check Nodes

#### IsBotDead

Returns SUCCESS if bot is dead (stops all behavior), FAILURE otherwise.

```csharp
public class IsBotDead : Node
{
    public override NodeState Evaluate()
    {
        Player localBot = (Player)GetRootNode().GetData("LocalBot");
        if (localBot == null || localBot.IsDead())
        {
            return NodeState.SUCCESS;  // Stop processing
        }
        return NodeState.FAILURE;  // Continue to next selector child
    }
}
```

#### IsBotStateEnabled

```csharp
public class IsBotStateEnabled : Node
{
    public override NodeState Evaluate()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        if (localPlayer.bot.botState == BotState.DISABLED)
            return NodeState.FAILURE;
        return NodeState.SUCCESS;
    }
}
```

#### IsBotStateMelee

```csharp
public class IsBotStateMelee : Node
{
    public override NodeState Evaluate()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        return localPlayer.bot.botState switch
        {
            BotState.MELEEACTION or
            BotState.SPELLMELEEACTION or
            BotState.FULL => NodeState.SUCCESS,
            _ => NodeState.FAILURE,
        };
    }
}
```

#### IsBotStateSpells

```csharp
public class IsBotStateSpells : Node
{
    public override NodeState Evaluate()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        return localPlayer.bot.botState switch
        {
            BotState.SPELLMELEEACTION or
            BotState.FULL => NodeState.SUCCESS,
            _ => NodeState.FAILURE,
        };
    }
}
```

### 4.2 Target Acquisition Nodes

#### IsTargetNull

```csharp
public class IsTargetNull : Node
{
    public override NodeState Evaluate()
    {
        state = ((Player)GetRootNode().GetData("target") == null)
            ? NodeState.SUCCESS
            : NodeState.FAILURE;
        return state;
    }
}
```

#### GetNearestEnemy

Finds the closest living enemy player.

```csharp
public class GetNearestEnemy : Node
{
    Player GetNearestPlayer()
    {
        Player nearestPlayer = null;
        float minDist = Mathf.Infinity;
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");

        foreach (Player targetPlayer in PlayerManager.playerList.Values)
        {
            // Skip self, dead players, teammates
            if (localPlayer == targetPlayer) continue;
            if (targetPlayer.IsDead()) continue;
            if (targetPlayer.team == localPlayer.team) continue;

            float dist = Vector3.Distance(
                localPlayer.pGameObject.transform.position,
                targetPlayer.pGameObject.transform.position
            );
            if (dist < minDist)
            {
                nearestPlayer = targetPlayer;
                minDist = dist;
            }
        }
        return nearestPlayer;
    }

    public override NodeState Evaluate()
    {
        Player target = GetNearestPlayer();
        GetRootNode().SetData("target", target);
        return (target != null) ? NodeState.SUCCESS : NodeState.FAILURE;
    }
}
```

#### SetRandomTarget

Switches to a different valid target with bias toward human players.

```csharp
public class SetRandomTarget : Node
{
    public override NodeState Evaluate()
    {
        List<Player> availablePlayers = GetAvailablePlayers();
        if (availablePlayers.Count == 0)
            return NodeState.FAILURE;

        Player newTarget = availablePlayers[Random.Range(0, availablePlayers.Count)];
        parent.parent.SetData("target", newTarget);
        return NodeState.SUCCESS;
    }

    List<Player> GetAvailablePlayers()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        Player currentTarget = (Player)GetRootNode().GetData("target");
        List<Player> filtered = new();

        // Get non-bot players for priority targeting
        List<Player> nonBotPlayers = PlayerManager.playerList.Values
            .Where(p => !p.IsBot && !p.IsDead() &&
                       p != localPlayer && !p.IsInTeam(localPlayer.team))
            .ToList();

        foreach (Player player in PlayerManager.playerList.Values)
        {
            // Skip invalid targets
            if (player == currentTarget || player.IsDead() ||
                player == localPlayer || player.IsInTeam(localPlayer.team))
                continue;

            // 30% chance to prefer human players
            if (nonBotPlayers.Count > 0 && Random.value < 0.3f)
            {
                filtered.Add(nonBotPlayers[Random.Range(0, nonBotPlayers.Count)]);
                continue;
            }

            filtered.Add(player);
        }
        return filtered;
    }
}
```

#### HasTargetReachedTimeThreshold

Triggers target switching after 5-10 seconds.

```csharp
public class HasTargetReachedTimeThreshold : Node
{
    float timer = 0f;
    float maxTimeThreshold = Random.Range(5f, 10f);

    public override NodeState Evaluate()
    {
        if ((Player)GetRootNode().GetData("target") == null)
            return NodeState.FAILURE;

        if (timer >= maxTimeThreshold)
        {
            timer = 0f;
            maxTimeThreshold = Random.Range(5f, 10f);  // Randomize next threshold
            return NodeState.SUCCESS;
        }

        timer += GameManager.Instance.BotManager.botTickRate;
        return NodeState.FAILURE;
    }
}
```

### 4.3 Combat Nodes

#### CheckPlayerDamaged

Detects if bot took significant damage (2500+ in one check).

```csharp
public class CheckPlayerDamaged : Node
{
    float currentStamina;
    float maxDamageThreshold = 2500f;

    public override NodeState Evaluate()
    {
        if (!PlayerReachedDamageThreshold())
            return NodeState.FAILURE;
        return NodeState.SUCCESS;
    }

    bool PlayerReachedDamageThreshold()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        if (Mathf.Abs(currentStamina - localPlayer.playerData.stamina) >= maxDamageThreshold)
        {
            currentStamina = localPlayer.playerData.stamina;
            return true;
        }
        return false;
    }
}
```

#### TargetWithinRange

Checks if target is within attack range and faces them.

```csharp
public class TargetWithinRange : Node
{
    float lookLerpSpeed = 25f;
    float rangeTimer = 0f;
    float maxRangedTime = 5f;
    float currentRange = 1f;

    public override NodeState Evaluate()
    {
        Player localBot = (Player)GetRootNode().GetData("LocalBot");
        currentRange = localBot.playerStats.range / 2f;

        // Ranged fighters vary their range every 5 seconds
        if (localBot.IsRanged())
        {
            if (rangeTimer > maxRangedTime)
            {
                rangeTimer = 0;
                currentRange = Random.Range(
                    localBot.playerStats.range / 4f,
                    localBot.playerStats.range / 2f
                );
            }
            else
            {
                rangeTimer += GameManager.Instance.BotManager.botTickRate;
            }
        }

        Player target = (Player)GetRootNode().GetData("target");
        if (target == null) return NodeState.FAILURE;
        if (target.IsDead())
        {
            GetRootNode().SetData("target", null);
            return NodeState.FAILURE;
        }
        if (!IsTargetWithinRange(target, currentRange))
            return NodeState.FAILURE;

        // Face target and stop moving
        Move(Vector2.zero);
        return NodeState.SUCCESS;
    }

    void Move(Vector2 inputVector)
    {
        Player target = (Player)GetRootNode().GetData("target");
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        Node rootNode = GetRootNode();

        Quaternion lookRotation = Quaternion.LookRotation(
            target.pGameObject.transform.position - localPlayer.pGameObject.transform.position
        );
        Quaternion finalRotation = Quaternion.Slerp(
            localPlayer.pGameObject.transform.rotation,
            lookRotation,
            lookLerpSpeed * GameManager.Instance.BotManager.botTickRate
        );

        rootNode.SetData("InputVector", inputVector);
        float eulerAngle = finalRotation.eulerAngles.y;

        // PaniMuktha angle offset for elliptical discus
        if (localPlayer.fightingStyle == FightingStyles.PaniMuktha &&
            localPlayer.selectedGod != TrinityGods.Vishnu)
        {
            eulerAngle += 8;  // 8 degree offset
        }

        rootNode.SetData("CameraAngle", eulerAngle);
    }
}
```

#### Attack

Performs melee attacks with cooldown.

```csharp
public class Attack : Node
{
    bool isAttacking = false;
    float attackTime = 0f;
    float atkRate = 1.8f;  // Base attack rate in seconds

    public override NodeState Evaluate()
    {
        Player target = (Player)GetRootNode().GetData("target");
        if (target.IsDead())
        {
            GetRootNode().SetData("target", null);
            return NodeState.FAILURE;
        }
        AttackFunction();
        return NodeState.RUNNING;
    }

    float GetAttackRate()
    {
        Player target = (Player)GetRootNode().GetData("target");
        // Attack twice as fast against bots or when no real players alive
        if (target.IsBot || !GameManager.Instance.BotManager.hasAliveRealPlayers)
            return atkRate / 2;  // 0.9 seconds
        return atkRate;  // 1.8 seconds
    }

    void AttackFunction()
    {
        if (isAttacking)
        {
            if (Mathf.Abs(Time.time - attackTime) >= GetAttackRate())
            {
                isAttacking = false;
                attackTime = Time.time;
            }
        }
        else
        {
            GetRootNode().SetData("Melee", 1);  // Trigger melee
            isAttacking = true;
            attackTime = Time.time;
        }
    }
}
```

### 4.4 Spell Casting Nodes

#### CastSpell

Casts offensive spells with cooldown.

```csharp
public class CastSpell : Node
{
    float maxWaitTime = 10f;  // 10 second cooldown
    float currentTime = 0f;

    public override NodeState Evaluate()
    {
        currentTime += GameManager.Instance.BotManager.botTickRate;

        if (IsPlayerAvailableToCast())
        {
            if (currentTime > maxWaitTime)
            {
                currentTime = 0f;
                if (SelectAvailableElemental())
                    return NodeState.SUCCESS;
            }
        }
        return NodeState.FAILURE;
    }

    bool SelectAvailableElemental()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        int elementalIndex = Random.Range(0, localPlayer.elementals.Length);
        Elemental castElemental = localPlayer.elementals[elementalIndex];

        // Check focus segments for spell cost
        if (localPlayer.focus.CheckFocusSegments(castElemental.spellCastAttributes.FocusBarSegments))
        {
            GetRootNode().SetData("SelectedElemental", elementalIndex);
            return true;
        }
        return false;
    }

    bool IsPlayerAvailableToCast()
    {
        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        return localPlayer.character.stateManager.GetState() != StateType.Stun &&
               localPlayer.character.AllowSpellCasting();
    }
}
```

#### CastDefenseSpell

Raises elemental shield when damaged.

```csharp
public class CastDefenseSpell : Node
{
    public override NodeState Evaluate()
    {
        // Only use shields against real players
        if (!GameManager.Instance.BotManager.hasAliveRealPlayers)
            return NodeState.FAILURE;

        Player localPlayer = (Player)GetRootNode().GetData("LocalBot");
        int elementalIndex = Random.Range(0, localPlayer.elementals.Length);

        // Shields cost 2 focus segments
        if (localPlayer.focus.CheckFocusSegments(2))
        {
            GetRootNode().SetData("SelectedElementalShield", elementalIndex);
            return NodeState.SUCCESS;
        }
        return NodeState.FAILURE;
    }
}
```

### 4.5 Movement Node

#### MoveToTarget

Moves toward current target.

```csharp
public class MoveToTarget : Node
{
    float lookLerpSpeed = 12f;

    public override NodeState Evaluate()
    {
        Player target = (Player)GetRootNode().GetData("target");
        Move(Vector2.up);  // Always move forward
        return NodeState.RUNNING;
    }

    void Move(Vector2 inputVector)
    {
        Player target = (Player)GetRootNode().GetData("target");
        if (target == null) return;

        Node rootNode = GetRootNode();
        Player localPlayer = (Player)rootNode.GetData("LocalBot");

        Quaternion lookRotation = Quaternion.LookRotation(
            target.pGameObject.transform.position - localPlayer.pGameObject.transform.position
        );
        Quaternion finalRotation = Quaternion.Slerp(
            localPlayer.pGameObject.transform.rotation,
            lookRotation,
            lookLerpSpeed * GameManager.Instance.BotManager.botTickRate
        );

        rootNode.SetData("InputVector", inputVector);
        rootNode.SetData("CameraAngle", finalRotation.eulerAngles.y);
    }
}
```

---

## 5. Bot Manager

### 5.1 BotManager Class

```csharp
public class BotManager : MonoBehaviour
{
    public List<Bot> bots = new();
    public float botTickRate = 0.0167f;  // ~60Hz (16.7ms)
    public bool hasAliveRealPlayers = false;

    // Initialize bots from avatar list
    public void InitializeBots()
    {
        foreach (var playerData in PlayerManager.avatarList)
        {
            if (playerData.Value.IsBot == 0) continue;  // Skip real players

            Player botPlayer = PlayerManager.AuthenticatePlayer(
                new UDPServerSocket.Peer(),
                new Guid(playerData.Value.sessionUUID).ToString()
            );
            if (botPlayer != null)
            {
                Bot bot = botPlayer.pGameObject.AddComponent<Bot>();
                bots.Add(bot);
            }
        }

        if (bots.Count != 0)
        {
            InvokeRepeating(nameof(BotTick), 0, botTickRate);
        }
    }

    // Enable full bot behavior at match start
    public void StartMatch()
    {
        foreach (Bot bot in bots)
        {
            if (GameManager.Instance.matchType != MatchType.TUTORIAL)
                bot.botState = BotState.FULL;
        }
    }

    // Fixed timestep tick
    void BotTick()
    {
        foreach (Bot bot in bots)
        {
            bot.OnUpdate();
        }

        if (MatchState.Instance.state == MatchState.MatchStates.MATCH)
            CheckBotQuickComplete();
    }
}
```

### 5.2 Bot Quick Complete

When all real players disconnect, the match auto-completes:

```csharp
void CheckBotQuickComplete()
{
    var activePlayerList = PlayerManager.playerList.Values
        .Where(p => !p.IsBot && p.active).ToList();
    var alivePlayerList = PlayerManager.playerList.Values
        .Where(p => !p.IsBot && !p.IsDead()).ToList();

    hasAliveRealPlayers = (alivePlayerList.Count != 0);

    if (activePlayerList.Count == 0 && !matchEnded)
    {
        // First Match/Tutorial: Forfeit
        if (GameManager.Instance.IsFirstMatch ||
            GameManager.Instance.matchType == MatchType.TUTORIAL)
        {
            GameManager.Instance.EndGame(true);
            matchEnded = true;
            return;
        }

        // Normal match: Pick random bot winner, kill rest
        var botList = PlayerManager.playerList.Values
            .Where(p => p.IsBot && !p.IsDead()).ToList();

        if (botList.Count > 0)
        {
            Player winner = botList[Random.Range(0, botList.Count)];
            foreach (Bot bot in bots)
            {
                if (bot.player != winner && !bot.player.IsDead())
                {
                    bot.player.playerData.stamina = 0;
                    bot.player.playerData.willPower = 0;
                    bot.player.character.playerBase.CheckDeath();
                }
            }
        }

        matchEnded = true;
    }
}
```

### 5.3 First Match Damage Multipliers

```csharp
public float GetFirstMatchDamageMultiplier(Player sourcePlayer, Player targetPlayer)
{
    if (sourcePlayer.IsBot)
        return 0.2f;  // Bots deal 20% damage
    else
        return 3.0f;  // Players deal 300% damage (easy mode)
}
```

---

## 6. Bot Class - Input Processing

### 6.1 Bot Initialization

```csharp
public class Bot : MonoBehaviour
{
    public Player player;
    public PlayerBase playerBase;
    public BotBT botBT;
    public BotState botState = BotState.DISABLED;

    UInt32 botTick;

    void Start()
    {
        playerBase = GetComponent<PlayerBase>();
        player = playerBase.character.player;
        player.bot = this;

        // Setup behavior tree
        botBT = playerBase.gameObject.AddComponent<BotBT>();
        botBT.Setup();
        botBT.root.SetData("LocalBot", player);
    }

    public void OnUpdate()
    {
        if (botBT.root != null)
        {
            botBT.root.Evaluate();  // Run behavior tree
            ProcessBotState();       // Convert to input
            botTick++;
        }
    }
}
```

### 6.2 Converting Tree Output to KeyInput

```csharp
private void ProcessBotState()
{
    KeyInput botKeyInput = new();

    // Movement (if not disabled)
    if (botState != BotState.DISABLED)
    {
        object joystickAxisObj = botBT.root.GetData("InputVector");
        Vector2 joystickAxis = joystickAxisObj == null ? Vector2.zero : (Vector2)joystickAxisObj;
        // Pack into single byte: upper 4 bits = X, lower 4 bits = Y
        botKeyInput.JoystickAxis = (byte)((((int)joystickAxis.x & 0xF) << 4) |
                                          ((int)joystickAxis.y & 0xF));
    }

    // Teleport state handling
    if (MatchState.Instance.GetMatchState() == MatchState.MatchStates.TELEPORT && !teleportDone)
    {
        player.character.stateManager.ChangeState(FSM.StateType.Teleport);
        teleportDone = true;
    }

    // Camera angle
    object cameraAngle = botBT.root.GetData("CameraAngle");
    botKeyInput.cameraRotation = cameraAngle == null ? 0f : (float)cameraAngle;

    // Melee attack
    if (botBT.root.GetData("Melee") != null)
    {
        botKeyInput.meleeAbility = (byte)EventState.PROGRESS;
        botBT.root.ClearData("Melee");
    }

    // Elemental spell casting
    if (botBT.root.GetData("SelectedElemental") != null)
    {
        int selectedElemental = (int)botBT.root.GetData("SelectedElemental");
        switch (selectedElemental)
        {
            case 0: botKeyInput.elementalAbility1 = (byte)EventState.PROGRESS; break;
            case 1: botKeyInput.elementalAbility2 = (byte)EventState.PROGRESS; break;
            case 2: botKeyInput.elementalAbility3 = (byte)EventState.PROGRESS; break;
            case 3: botKeyInput.elementalAbility4 = (byte)EventState.PROGRESS; break;
        }
        botKeyInput.abilityPos = new Vector2(
            player.character.playerBase.ContactPoint.transform.position.x,
            player.character.playerBase.ContactPoint.transform.position.z
        );
        botBT.root.ClearData("SelectedElemental");
    }

    // Elemental shield
    if (botBT.root.GetData("SelectedElementalShield") != null)
    {
        int selectedElemental = (int)botBT.root.GetData("SelectedElementalShield");
        switch (selectedElemental)
        {
            case 0: botKeyInput.elementalAbility1 = (byte)EventState.SHIELDUP; break;
            case 1: botKeyInput.elementalAbility2 = (byte)EventState.SHIELDUP; break;
            case 2: botKeyInput.elementalAbility3 = (byte)EventState.SHIELDUP; break;
            case 3: botKeyInput.elementalAbility4 = (byte)EventState.SHIELDUP; break;
        }
        botBT.root.ClearData("SelectedElementalShield");
    }

    // Tick info
    botKeyInput.serverTick = GameManager.serverTick;
    botKeyInput.tick = botTick;

    // State recovery
    if (player.character.stateManager.GetState() == FSM.StateType.Pushback_Land &&
        player.character.pushBackInit && player.character.pushBackDone)
    {
        botKeyInput.state = FSM.StateType.Idle;
    }
    else if (player.character.stateManager.GetState() == FSM.StateType.Cast_Spell &&
             player.character.spellCastDone)
    {
        botKeyInput.state = FSM.StateType.Idle;
    }
    else
    {
        botKeyInput.state = player.character.stateManager.GetState();
    }

    // Process input through normal player input pipeline
    PlayerManager.ProcessPlayerInputTick(player, botKeyInput);
    player.inputs.lastProcInput = botKeyInput;
}
```

---

## 7. Karma System (Post-Match)

Bots participate in the karma voting system after matches:

```csharp
public void SendKarmaPlayersState(uint[] karmaPlayers, int karmaPlayerCount)
{
    for (int i = 0; i < karmaPlayerCount; i++)
    {
        StartCoroutine(SendKarmaChoice(
            karmaPlayers[i],
            Random.Range(
                MatchState.Instance.postMatchReadyTime + 3f,
                MatchState.Instance.postMatchReadyTime + 8f
            )
        ));
    }
}

IEnumerator SendKarmaChoice(UInt32 karmaPlayerUID, float delay)
{
    yield return new WaitForSeconds(delay);

    foreach (KarmaPlayer karmaPlayer in player.karmaPlayers)
    {
        if (karmaPlayer.player.uniqueCode == karmaPlayerUID)
        {
            // Random karma choice
            karmaPlayer.karma = (Karma)Random.Range(0, Enum.GetNames(typeof(Karma)).Length);

            Packet.PlayerKarma packet = new()
            {
                givingPlayer = player.uniqueCode,
                packetType = (UInt16)Packet.PacketTypeOUT.PLAYERKARMA,
                receivingPlayer = karmaPlayerUID,
                karma = (byte)karmaPlayer.karma
            };

            GameManager.Instance.BroadcastPlayers(
                Serializer.Serialize<Packet.PlayerKarma>(packet),
                null, true
            );
            break;
        }
    }
}
```

---

## 8. Bot Timing Constants

| Constant                | Value       | Description                              |
|-------------------------|-------------|------------------------------------------|
| `botTickRate`           | 0.0167f     | 60Hz tick rate (16.7ms)                  |
| `atkRate`               | 1.8f        | Base melee attack cooldown (seconds)     |
| `atkRate` (vs bots)     | 0.9f        | Melee cooldown when fighting bots        |
| `maxWaitTime` (spell)   | 10f         | Spell casting cooldown (seconds)         |
| `maxDamageThreshold`    | 2500f       | Damage threshold for defense trigger     |
| `maxTimeThreshold`      | 5-10f       | Random target switch time                |
| `maxRangedTime`         | 5f          | Range variation timer for ranged bots    |
| `lookLerpSpeed` (move)  | 12f         | Rotation smoothing when moving           |
| `lookLerpSpeed` (range) | 25f         | Rotation smoothing when in range         |
| Shield cost             | 2 segments  | Focus cost for elemental shields         |

---

## 9. Fighting Style Considerations

### 9.1 Range Calculation

```csharp
// Base range from player stats
currentRange = localBot.playerStats.range / 2f;

// Ranged fighters (MantraMuktha, PaniMuktha, YantraMuktha)
// vary their attack range every 5 seconds
if (localBot.IsRanged())
{
    currentRange = Random.Range(
        localBot.playerStats.range / 4f,  // Min: 25% range
        localBot.playerStats.range / 2f   // Max: 50% range
    );
}
```

### 9.2 PaniMuktha Angle Offset

```csharp
// PaniMuktha uses elliptical discus attack
// Requires 8-degree angle offset (except Vishnu god selection)
if (localPlayer.fightingStyle == FightingStyles.PaniMuktha &&
    localPlayer.selectedGod != TrinityGods.Vishnu)
{
    eulerAngle += 8;
}
```

---

## 10. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `Bot.cs` | 176 | Main bot controller, input processing |
| `BotBT.cs` | 56 | Behavior tree structure definition |
| `BotManager.cs` | 173 | Bot lifecycle, tick management |
| `Node.cs` | 97 | Base behavior tree node |
| `Selector.cs` | 37 | OR composite node |
| `Sequence.cs` | 43 | AND composite node |
| `Tree.cs` | 28 | Abstract tree base class |
| `Attack.cs` | 50 | Melee attack action |
| `CastSpell.cs` | 51 | Offensive spell action |
| `CastDefenseSpell.cs` | 31 | Shield raise action |
| `CheckBotState.cs` | 40 | State check nodes (3 in file) |
| `CheckPlayerDamaged.cs` | 31 | Damage threshold check |
| `GetNearestEnemy.cs` | 45 | Target acquisition |
| `HasTargetReachedTimeThreshold.cs` | 34 | Target switch timer |
| `IsBotDead.cs` | 24 | Death check |
| `IsTargetNull.cs` | 12 | Null target check |
| `MoveToTarget.cs` | 32 | Movement action |
| `SetRandomTarget.cs` | 82 | Random target selection |
| `TargetWithinRange.cs` | 81 | Range check and facing |

**Total Bot System: ~1,023 lines of code**

---

*Last Updated: January 21, 2026*
*Protocol Version: 11.0*
