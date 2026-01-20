# AUM Glossary

**Terms and definitions specific to the AUM project.**

---

## A

### Addressables
Unity's asset management system for loading assets at runtime. Currently having issues loading character cosmetics in legacy project.

### Amuktha
Close-range fighting style. Has Melee and Melee_Second states. Special ability: Dash.

### Aiming State
State used by ranged fighters (MantraMuktha, PaniMuktha, Yantramuktha) when holding the attack button before releasing a ranged attack.

### Astra
Ultimate ability system. Charged by building Focus meter through combat.

---

## B

### BotManager
Server-side component managing AI bot behavior and decision-making.

### Brahma
Trinity God option. Provides shield abilities and +3 focus streak start.

### ButtonHelper
Static class managing button event queue. Used for input processing.

### ButtonPhase
Enum for button states: PRESS, RELEASE, TAP, HELD, DRAG, BEGINDRAG, ENDDRAG, CANCELED.

---

## C

### CamTouchField
UI component handling camera rotation via touch on mobile. Has platform guard to not interfere with PCInput on desktop.

### CREATECHARACTER (0x1401)
Packet type for player authentication. Client sends session UUID, server responds with spawn position.

### ControllerBase
Base class for all character controllers. Defines 20+ states for the FSM.

---

## D

### Deterministic GUID
UUID generated from MD5 hash of a string. Used for session authentication without central server.

### Dheeraj (Chintaluri)
Original developer who wrote 100% of the server code and core client architecture.

---

## E

### ENDGAMEDATA (0x1407)
Packet sent when match ends. Contains winner info, stats, rewards.

### Elemental System
Fire > Wind > Earth > Water > Fire. 1.5x damage when advantaged, 0.75x when disadvantaged.

---

## F

### FSM (Finite State Machine)
State management system controlling character behavior. Core of gameplay logic.

### Focus
Combat resource built by landing hits. When full, enables Astra (ultimate) ability.

### FixedUpdate
Unity callback running at fixed intervals (60Hz in AUM). All networked game logic runs here.

---

## G

### GameManager
Central component managing match state machine (NONE → END).

### Gold Standard
October 2025 codebase that was working in production. Server: Oct 6, Client: Oct 29.

---

## H

### Hetzner
Cloud VPS provider hosting the game server. IP: 65.109.133.129.

---

## I

### InterfaceManager
Singleton holding global data like sessionUUID, match_Avatars, localPlayerID.

### IsBlockingInput()
StateManager method checking if current state blocks new input. Always check before state transitions.

---

## L

### Legacy Projects
October 2025 codebase being used as the production base. Repositories with "Legacy" in name.

### LiteNetLib
UDP networking library used for client-server communication. Native DLL (x86_64).

---

## M

### MantraMuktha
Ranged fighting style. Uses Aiming state. Special ability: Teleport.

### MatchKeeper
WebSocket-based match orchestration system. Bypassed in test mode for direct connection.

### MATCHRUNNING
Match state when combat is active. Players can fight, use abilities, etc.

### Match_Avatar
Data structure defining a player in a match: uniqueID, teamID, fightingStyle, godSelected, etc.

### Melee_Second
Second melee attack state. Only exists for close-range fighters (Amuktha, MukthaMuktha).

### MukthaMuktha
Close-range fighting style. Has Melee and Melee_Second states. Special ability: Axe throw/recall.

---

## N

### NetworkManager
Component handling UDP communication via LiteNetLib native DLL.

---

## P

### Packet.cs
File containing all network packet structure definitions.

### PaniMuktha
Ranged fighting style. Uses Aiming state. Special ability: Discus throw.

### PCInput
Component handling PC-specific input (mouse movement, keyboard).

### PlayFab
Backend service for player data, currencies, inventory, leaderboards. Title ID: 15F2B7.

### PlayerInput
Component processing player input from various sources (mobile, PC, controller).

### PlayerManager
Server-side component managing player processing, input handling, and state updates.

### POSTMATCH
Match state after combat ends. Shows results, calculates rewards.

### PREGAME
Match state before combat. 5-second countdown timer.

---

## S

### Session UUID
Unique identifier for a player session. Generated via MD5 hash in test mode.

### Shiva
Trinity God option. Provides Third Eye immunity and +20% damage.

### SimulationManager
Client-side component handling prediction and state reconciliation.

### Stamina
Combat resource for dodging. Max 100, dodge costs 70, regenerates at 15/sec.

### StateManager
Core FSM controller. Manages state transitions and blocking.

### StateType
Enum of all possible character states: Idle, Walking, Attacking, Dodging, etc.

---

## T

### TELEPORT
Match state when players are spawning at their positions.

### TestModeClient
Client component for direct server connection, bypassing MatchKeeper.

### TestModeManager
Server component for test mode, handling direct connections without WebSocket orchestration.

### Tick
Single update of game simulation. AUM runs at 60 ticks/second (60Hz).

### Trinity Gods
Three ultimate ability types: Brahma, Vishnu, Shiva. Each provides different buffs.

---

## V

### Vishnu
Trinity God option. Provides +30% movement speed and stamina discount.

---

## W

### Willpower
Health/HP resource. When depleted, player is defeated.

### WORLDSNAPSHOT (0x1403)
Packet containing all player states. Sent by server at 60Hz.

---

## Y

### Yantramuktha
Ranged fighting style. Uses Aiming state. Special ability: Arrow special.

---

*Last Updated: January 20, 2026*
