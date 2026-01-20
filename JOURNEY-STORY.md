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

## Chapter 6: The Road Ahead

### Republic Day Target: January 26, 2026

| Day | Date | Task |
|-----|------|------|
| 1 | Jan 19 | Documentation |
| 2 | Jan 20 | PC Input Fixes |
| 3 | Jan 21 | Main Menu UI Wiring |
| 4 | Jan 22 | Addressables Fix |
| 5 | Jan 23 | Android Build |
| 6 | Jan 24 | Play Store Submit |
| 7 | Jan 25 | Buffer |
| 8 | **Jan 26** | **REPUBLIC DAY LAUNCH** |

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
Hours of Debugging:          ~6+
"It's working!" moments:     2
"Why isn't it working?!":    47+
Firewalls discovered:        2 (one too many)
DLLs incompatible:           1 (that was enough)
Session UUIDs matched:       FINALLY
```

---

*"In the chaos of networking bugs, we found not just a connection, but a path forward."*

*Last Updated: January 20, 2026*
