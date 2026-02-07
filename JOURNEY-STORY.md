# AUM: The Journey Story

**The Impossible Wire-Up and Beyond**

---

## Chapter 1: The Foundation (2021-2025)

### Dheeraj's Vision

In April 2021, **Dheeraj Chintaluri** laid the first stone of what would become AUM. Starting with LiteNetLib for networking, he built the entire server architecture from scratch.

**Key Milestones:**
- **April 2021:** Initial networking protocols (LiteNetLib)
- **January 2022:** FSM state machine implementation
- **November 2022:** MatchKeeper integration
- **January 2023:** Fixed-point decimal arithmetic for determinism
- **October 2025:** Elemental spell and shield interactions

By October 2025, AUM was a **working multiplayer fighting game** with:
- 5 unique fighting styles
- 3 Trinity Gods with special abilities
- Server-authoritative combat
- 60Hz tick-based netcode
- Mobile and PC support

**The Gold Standard:** October 6, 2025 (server) and October 29, 2025 (client)

---

## Chapter 2: The Glitch Situation (Late 2025)

### The Upgrade That Wasn't

The team attempted to modernize the codebase:
- **AUM-The-Epic:** New client with ICombatAuthority pattern
- **AUM-Headless:** Refactored server with rollback netcode

But something went wrong. The new architecture was:
- Complex to debug
- Producing glitchy multiplayer
- Harder to work with than the original

**The Decision:**

> "Let's restore a KNOWN-WORKING state from October 2025"

---

## Chapter 3: The Pivot (January 2026)

### Return to Legacy

Instead of fighting the new code, the strategy became:
1. **Keep** the working legacy gameplay
2. **Add** PlayFab integration on top
3. **Cherry-pick** useful patterns from upgraded projects

**The Repos:**
- `AUM-Unity-Staging-Legacy` @ `legacy-working-oct29`
- `AUM-Unity-Server-Legacy` @ `legacy-working-oct6`

---

## Chapter 4: The Impossible Wire-Up (January 16-19, 2026)

### Mac to Windows to Victory

**Day 1: The Mac Attempt**
```
Build server on Mac ✓
Deploy to Hetzner ✓
Server running ✓
Client on Mac... DLL MISMATCH (ARM64 vs x86_64)
```

The native LiteNetLib DLL was x86_64 only. Mac ARM64 couldn't run it.

**Solution:** Move everything to Windows.

**Day 2: The Windows Pivot**
```
Transfer project to Windows ✓
Open in Unity 6 ✓
Client connects... DISCONNECT!
```

UDP packets weren't reaching the server. tcpdump showed nothing arriving.

**The Revelation:** Hetzner has TWO firewalls:
1. UFW (OS-level) - was open
2. **Hetzner Cloud Firewall** - was BLOCKING UDP 6006!

Added the rule in Hetzner Console.

**The Moment:**

> "hey check now its fucking working!!!"

---

## Chapter 5: Current Victory (January 19-20, 2026)

### What's Working

| System | Status |
|--------|--------|
| Server Connection | Direct UDP to Hetzner |
| Authentication | Session UUID matching via MD5 |
| Match Flow | NONE → POSTMATCH complete |
| Combat (All fighters) | Working |
| PC Input | Camera, dodge, aiming fixed |
| PlayFab Auth | Firebase → PlayFab |

### The TestMode Bypass

The genius solution: Both client and server generate the same UUID from the same string using MD5. No MatchKeeper needed.

```
"test-player-1-session" → MD5 → 3d46e7bc-914e-fca2-c3ae-1ae23d72aa34
```

---

## Chapter 6: The LEGENDARY Elemental Fix (February 7, 2026)

### The Problem

Elemental buttons (1-4) weren't working like the Attack button. Expected behavior: HOLD = enter aiming state, RELEASE = cast spell. But only Fire elemental worked - other elements (ETHER, EARTH) spawned Fire spells!

### The Hunt

```
First clue: CastManager logs showed spellIndex=0 (FIRE) for all spells
Second clue: matchAvatar.elementalSelected had correct values (96=ETHER, 128=EARTH)
Third clue: Two data sources for elementals...
```

**The Revelation:**
- `InterfaceManager.Instance.Player_elementals` → STALE (set to FIRE defaults)
- `player.m_elementals` → AUTHORITATIVE (from matchAvatar.elementalSelected)

CastManager was using the wrong source!

### The Double Fix

**Client Side (CastManager.cs):**
```csharp
// BEFORE (WRONG):
Elemental[] elementals = InterfaceManager.Instance.Player_elementals;

// AFTER (CORRECT):
Elemental[] elementals = player.m_elementals;
```

**Server Side (PlayerManager.cs - ProcessAvatarUpload):**
```csharp
// Server wasn't updating player.elementals from AVATARUPLOAD!
player.elementals = new Elemental[elementalCount];
for (int i = 0; i < elementalCount; i++)
    player.elementals[i] = new Elemental(data.elementalSelected[i]);

// Reinitialize CastManager with correct elementals
player.character.castManager = player.pGameObject.AddComponent<CastManager>()
    .Instantiate(player.elementals, player);
```

### Bonus Fixes

1. **Shield Cast on Drag Down** - Wait for drag direction in BEGINDRAG before entering aiming
2. **Focus Timing** - Use target fill amount instead of animated DOTween value
3. **SpecialAbility Button** - Same pattern fix as elemental buttons

### The Commit

```
[LEGENDARY] fix: Elemental/SpecialAbility controls fully working
[LEGENDARY] fix: Server elemental sync from AVATARUPLOAD
```

> "hey cool this is working now... this will be the same for all fighting styles right?"

---

## Chapter 7: The Road Ahead

### Post-Launch Development

| Date | Milestone | Status |
|------|-----------|--------|
| Jan 26 | Republic Day Target | ✓ Achieved |
| Feb 7 | LEGENDARY Elemental Fix | ✓ Complete |
| TBD | Addressables CDN | Pending |
| TBD | PlayFab Matchmaking | In Progress |

---

## The Lessons Learned

### 1. Scene Serialization Overrides Code
Unity scene values override code defaults. Always force values in `Start()` if needed.

### 2. Two Firewalls, Two Problems
Cloud providers often have their own firewall layer above the OS firewall.

### 3. Execution Order Matters
Use `[DefaultExecutionOrder]` and `Awake()` to control initialization order.

### 4. Don't Fight Working Code
Sometimes the old way is the right way. Legacy doesn't mean broken.

---

## The Credits

```
Hours of Debugging:          ~10+
"It's working!" moments:     4
"Why isn't it working?!":    100+
Firewalls discovered:        2 (one too many)
DLLs incompatible:           1 (that was enough)
Session UUIDs matched:       FINALLY
LEGENDARY commits:           2 (Feb 7, 2026)
Elemental data sources:      2 (one too many)
```

---

*"In the chaos of networking bugs, we found not just a connection, but a path forward."*

*"When your elementals all cast Fire, check if you're reading from the past or the present."*

*Last Updated: February 7, 2026*
