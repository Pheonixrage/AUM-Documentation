---
date: 2026-04-22
status: PLANNING — not yet implemented
pipeline: P3 — Legacy Live (AUM-Unity-Staging-Legacy + AUM-Unity-Server-Legacy)
branch: legacy-working-oct29
risk: MEDIUM (gameplay-adjacent, but client-only and gated by phases)
related: [[bot-ai-legacy]]
---

# Object Pooling Plan — Spell Effects + Impact VFX

## TL;DR

Replace per-cast `Instantiate()`/`Destroy()` with `UnityEngine.Pool.ObjectPool<T>` for spell projectiles, melee/projectile impact VFX, and status-effect indicators. Goal: eliminate GC spikes and FPS drops during combat. **Astras explicitly excluded** (work fine, low frequency). Plan is the result of a 4-agent deep dive + direct verification of all critical files (2026-04-22 session).

## Why now

- Spells cause confirmed FPS drops in combat (user-reported)
- `ParticleManager` already uses `ObjectPool<T>` successfully — proven template
- Unity 6.0.60f1 has `UnityEngine.Pool.ObjectPool<T>` available
- Network layer is server-authoritative (WORLDSNAPSHOT) — pooling is invisible to packet layer

---

## Scope (locked)

| System | Pool? | Reason |
|---|---|---|
| Spell projectiles (FIRE/WATER/AIR/EARTH/ETHER) | ✅ YES | [SpellManager.cs:138](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/SpellManager.cs) — single Instantiate point |
| Melee impact VFX (3 gods × 5 styles) | ✅ YES | [PlayerBase.cs:736-780](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Player/PlayerBase.cs) + 3 callsites in [Projectile.cs:156,171,184](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/Projectile.cs) |
| Projectile impact VFX | ✅ YES | Shares `impactScriptableObjects` pool |
| Status effect indicators (Mute, Fire, Air_Slow, Impair, Maim) | ✅ YES | [ImpactEffectController.cs:137](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ImpactEffectController.cs) |
| **Astras (Brahma/Vishnu/Shiva)** | ❌ NO | **User instruction: work fine, exclude** |
| DiscusProjectile (PaniMuktha) | ❌ NO | 4 Initialize variants + return-to-thrower path — too risky |
| Shield cracks | ❌ NO | Already SetActive-pooled |
| PlayParticle weapon trails | ❌ NO | Already instantiated once + reused |
| MatchScreen spawn particles | ⚠️ FIX SEPARATELY | Leaks 6 GameObjects/match (no Destroy) — one-line fix, not pool work |

---

## The 8 Verified Blockers (must fix or pool will break)

All verified by reading the actual files on 2026-04-22.

| # | File:Line | Issue | Fix |
|---|---|---|---|
| 1 | [ProjectileScript.cs:25-28](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ProjectileScript.cs) | `Start()` only fires once per pool create — `moving` stays false on reuse | Move `moving = true` to `OnEnable()` or public `Initialize()` |
| 2 | [ProjectileScript.cs:67](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ProjectileScript.cs) | `Destroy(gameObject, destroy_delay)` — uncancellable, will destroy pooled objects | Replace with `StartCoroutine(DelayedRelease(delay))` storing handle |
| 3 | [ProjectileScript.cs:17](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ProjectileScript.cs) | `AlreadyHitObjects` list never cleared on reuse | `AlreadyHitObjects.Clear()` in `Initialize()` |
| 4 | [ProjectileScript.cs:47](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ProjectileScript.cs) | `SphereCollider.radius +=` accumulates across reuses | Cache initial radius in `Awake()`, restore in `Initialize()` |
| 5 | [Projectile.cs:19](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/Projectile.cs) | `bool hit` flag never resets | Reset `hit = false` in `Initialize()` |
| 6 | [Projectile.cs:90,157,172,185,205,220,233](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/Projectile.cs) | 7 orphan `StartCoroutine(DestroyCoroutine())` calls — coroutine ends with `Destroy(gameObject)` at [line 124](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/Projectile.cs) | `StopAllCoroutines()` + `CancelInvoke()` on pool return; replace inner Destroy with `pool.Release()` |
| 7 | [SpellManager.cs:147-148](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/SpellManager.cs) | `DestroySpellEffect` NPEs on pooled-but-stale entity | Null-check `entity.entityObject` AND `projectileScript` |
| 8 | [Projectile.cs:158,173,186](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/Projectile.cs) + [PlayerBase.cs:753](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Player/PlayerBase.cs) | `SetParent()` after scheduling Destroy — race if player destroyed first | Pool to `[VFXPool]` parent transform, not player |

### Edge cases (not blockers but flagged)

- **ETHER prefab `PlayOnAwake = 1` AudioSource** — Awake doesn't fire on Get → silent re-cast. Fix: explicit `audioSource.Play()` in Initialize().
- **`ParticleController.Awake()` clears particles** — only fires once per pool create. Latent bug today. Fix: move clear into `Initialize()`.

---

## Architecture (from final plan)

```
VFXPoolManager (singleton on GameManager, scene-scoped — NOT DontDestroyOnLoad)
├── projectilePools     : Dictionary<Elementals, ObjectPool<ProjectileScript>>     (5 pools)
├── impactPools         : Dictionary<ImpactKey, ObjectPool<GameObject>>            (3 gods × 5 styles = 15)
├── statusEffectPools   : Dictionary<ImpactIndicatorType, ObjectPool<GameObject>>  (~7 effects)
└── poolRoot            : Transform (holds inactive instances)

Capacity:
  Projectiles:    defaultCapacity=8,  maxSize=20  per element
  Impacts:        defaultCapacity=6,  maxSize=15  per god
  Status effects: defaultCapacity=4,  maxSize=10  per type

Warmup: piggyback on existing SpellManager.WarmupSpellShaders() — pre-warm 4-6 instances
        during loading screen alongside shader compilation
```

### Detach-on-release pattern (solves the 1–5s coroutine wait)

```
On hit:
  1. Pool.Get() → fresh projectile
  2. Hit detected
  3. Spawn impact VFX (pooled separately)
  4. Detach all child ParticleSystems to a "fading VFX" collector
  5. Projectile released to pool IMMEDIATELY (clean state)
  6. Detached particles fade naturally → auto-destroyed when IsAlive() = false
  7. VFXQueue's existing MAX_ACTIVE_VFX=10 cap applies
```

### Universal `OnGetFromPool` reset checklist

```csharp
StopAllCoroutines();            // kills orphan DestroyCoroutines
CancelInvoke();                  // kills FixedTimestep InvokeRepeating
transform.SetParent(poolRoot, false);
transform.localScale = cachedInitialScale;
moving = true;
hit = false;
AlreadyHitObjects.Clear();
sphereCollider.radius = cachedInitialRadius;
sphereCollider.center = cachedInitialCenter;
foreach (var ps in childParticleSystems) ps.Clear(true);
foreach (var tr in childTrails) tr.Clear();           // NOT trail.time *= x
audioSource?.Stop();
audioSource.time = 0f;
if (playOnAwake) audioSource?.Play();
transform.DOKill();
Initialize();
```

---

## Phased Rollout (each phase = its own commit, easy revert)

| Phase | What | Risk | Time | GC win |
|---|---|---|---|---|
| **P1** | Melee impact VFX pooling | LOW | 1 day | ~40% |
| **P2** | Status effect indicator pooling | LOW | 0.5 day | ~10% |
| **P3** | Spell projectile pooling (`ProjectileScript`) | MEDIUM | 1.5 days | ~35% |
| **P4** | Advanced projectile pooling (`Projectile.cs`) | MEDIUM | 1 day | ~15% |
| **Quick** | MatchScreen leak fix (separate, not pool work) | TRIVIAL | 15 min | leak fix |

**Each phase shipped as ONE atomic commit with clear message** — see Revert Strategy.

---

## Test Plan

### Approach: **One playtest per phase, decide go/no-go**

Per user instruction: "we will test this once and then if its not working out we want to be able to revert safely."

### Per-phase test checklist

For each phase before deciding go/no-go:

1. **Solo bot match (Solo_1v2)** — 5 minutes, all elementals + special abilities used
2. **Visual regression check:**
   - Impact VFX appear correctly (no missing effects, no double-spawn)
   - Spell projectiles travel + impact correctly
   - Status indicators (Mute, Fire DoT, Slow) render correctly
   - No "ghost" particles from previous reuse
   - No stuck/invisible projectiles
3. **Performance check** (the whole point):
   - Open Profiler, watch GC.Alloc per frame
   - Compare baseline (pre-pool) vs post-pool — should see significant drop
   - Watch FPS in busy combat (3+ projectiles + impacts on screen)
4. **Network sanity:**
   - Check `mcp__unity__log_errors` — no NPEs from `DestroySpellEffect`
   - Check `mcp__unity-headless__log_errors` — server-side unaffected
5. **Edge case probes:**
   - Cast spell, immediately disconnect → no leaked GameObjects
   - Match end → all pooled objects cleaned up (scene unload)
   - Rapid fire (Yantramuktha) → pool capacity holds, no exhaustion

### Pass criteria (go to next phase)

- All visual checks pass
- GC spikes measurably reduced
- Zero new errors in client/server logs
- Match completes normally end-to-end

### Fail criteria (revert)

ANY of:
- Visible visual glitches (ghost particles, missing impacts, stuck projectiles)
- New NPE/exception spam in logs
- Match-breaking bug (cant complete match)
- No measurable performance improvement
- Bot AI breaks (combat detection relies on entity lifecycle)

---

## Revert Strategy (CRITICAL)

### Strategy: Atomic phase commits + git revert

Each phase is **one commit** with a clear conventional message. Reverting is `git revert <hash>` — clean, no merge conflicts, no manual undo.

```
git log --oneline (planned commits)
  feat(perf): P4 - pool advanced projectiles (Projectile.cs)
  feat(perf): P3 - pool spell projectiles (ProjectileScript) + 8 blocker fixes
  feat(perf): P2 - pool status effect indicators
  feat(perf): P1 - pool melee impact VFX + add VFXPoolManager
  fix(perf): MatchScreen spawn particle leak  (separate, keep regardless)
```

### Revert protocol if a phase fails

```bash
# Identify the bad commit
git log --oneline -10

# Revert it (creates an inverse commit, preserves history)
git revert <hash>

# Push (DO NOT force push)
git push origin legacy-working-oct29
```

### What CANNOT be reverted easily (and what we do about it)

- **Refactor of `ProjectileScript.Start() → OnEnable()`** is bundled with P3. If we revert P3, this is undone. ✓ Safe.
- **`ParticleController.Awake() → Initialize()` move** — if we touch this, bundle it inside the same phase commit, not a separate cleanup commit. Keeps revert atomic.
- **Field caching of initial collider radius** — bundled with P3. Reverts cleanly.

### Safety net commit before starting

Before P1, create an annotated tag:

```bash
git tag -a pre-pooling-2026-04-22 -m "Snapshot before object pooling rollout"
git push origin pre-pooling-2026-04-22
```

Worst case: `git reset --hard pre-pooling-2026-04-22` (DESTRUCTIVE — last resort, requires user confirmation per safety rules).

### Files NOT touched (safe by exclusion)

These are in `DO NOT MODIFY` list per CLAUDE.md — pooling avoids them entirely:
- `NetworkManager.cs` ✓ (no changes needed — packets unchanged)
- `Packet.cs` ✓
- `StateManager.cs` ✓
- Animation timing ✓
- 60Hz tick rate ✓

---

## Failure Log (fill in IF/WHEN issues found during testing)

> **Template — leave empty until something fails.** This is for future reference so we don't repeat mistakes if we ever try pooling again.

### Phase 1 (Melee impacts)

- **Date tested:**
- **Outcome:** ☐ Pass ☐ Fail
- **What failed:**
- **Root cause (if known):**
- **Symptoms observed:**
- **Reverted commit:**
- **Lesson learned:**

### Phase 2 (Status effects)

- **Date tested:**
- **Outcome:** ☐ Pass ☐ Fail
- **What failed:**
- **Root cause (if known):**
- **Symptoms observed:**
- **Reverted commit:**
- **Lesson learned:**

### Phase 3 (Spell projectiles)

- **Date tested:**
- **Outcome:** ☐ Pass ☐ Fail
- **What failed:**
- **Root cause (if known):**
- **Symptoms observed:**
- **Reverted commit:**
- **Lesson learned:**

### Phase 4 (Advanced projectiles)

- **Date tested:**
- **Outcome:** ☐ Pass ☐ Fail
- **What failed:**
- **Root cause (if known):**
- **Symptoms observed:**
- **Reverted commit:**
- **Lesson learned:**

---

## Things We're Confident About

- Architecture mirrors working `ParticleManager` (proven in production)
- Server-authoritative network layer is fully insulated
- Pool sizing covers worst-case 6-player burst
- All 8 blockers are real and the fixes are mechanical

## Things That Need Real Playtest

- AIR projectile 5s delayed-destroy + detach-particles pattern
- ETHER `PlayOnAwake` audio compensation
- 60Hz server tick + same-frame pool reuse edge case
- Visual quality of "snap-cut vs detach-and-fade" particle handling

## Reference Files (deep-dive completed)

| File | Verified | Notes |
|---|---|---|
| [SpellManager.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/SpellManager.cs) | ✅ read directly | Single Instantiate at :138 |
| [ProjectileScript.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ProjectileScript.cs) | ✅ read directly | 4 of 8 blockers live here |
| [Projectile.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/Projectile.cs) | ✅ read directly | Orphan coroutines + hit flag |
| [ImpactEffectController.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Entities/ImpactEffectController.cs) | ✅ read directly | Status effect spawning hub |
| [PlayerBase.cs:736-780](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Player/PlayerBase.cs) | ✅ via agent | `CreateMeleeImpactEffect()` |
| [ParticleManager.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/ParticleManager.cs) | ✅ via agent | Reference pool implementation |
| [VFXQueue.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Utils/VFXQueue.cs) | ✅ via agent | Existing MAX_ACTIVE_VFX=10 cap |
| [EntityManager.cs](../../AUM-Unity-Staging-Legacy/Assets/Scripts/Managers/EntityManager.cs) | ✅ via agent | Network entity lifecycle |

---

## Status Log

- **2026-04-22:** Plan created. 4-agent investigation complete. Direct file verification done. Awaiting user go-ahead to start P1.
- **(next entry):** _Will be filled when implementation begins or revert decision made._
