# AUM Bot AI Design Document
## Comprehensive Game Mechanics + World-Class Bot AI Architecture

**Game:** AUM — Third-Person Multiplayer Arena Fighting Game
**Engine:** Unity 6 | **Netcode:** LiteNetLib UDP | **Tick Rate:** 60Hz Server-Authoritative
**Platforms:** iOS, Android, Windows (Steam)
**Developer:** Brahman Studios

---

# PART 1: COMPLETE GAME MECHANICS

## 1.1 Game Overview

AUM is a third-person multiplayer fighting game where players choose from 5 fighting styles and 3 gods, then battle in arena combat using melee attacks, elemental spells, unique character abilities, and god-powered ultimates. The game features both solo and team-based modes.

### Match Types & Player Counts

| Mode | Code | Total Players | Teams | Description |
|------|------|---------------|-------|-------------|
| Solo 1v1 | `Solo_1v1` | 2 | FFA | Duel |
| Solo 1v2 | `Solo_1v2` | 3 | FFA | Free-for-all |
| Solo 1v5 | `Solo_1v5` | 6 | FFA | Free-for-all battle royale |
| Duo 2v2 | `Duo_2v2` | 4 | 2 teams of 2 | Team duel |
| Duo 2v4 (2v2v2) | `Duo_2v4` | 6 | 3 teams of 2 | Three-way team battle |
| Trio 3v3 | `Trio_3v3` | 6 | 2 teams of 3 | Team battle |
| Tutorial | `Tutorial` | 2 | 1v1 | Training match |

### Win Conditions
- Reduce opponent's Willpower (health) to 0
- Last player/team standing wins
- Post-match: Karma selection (Sattva/Rajas/Tamas) affects progression

### Match Flow
```
NONE -> PREGAME -> TELEPORT -> MATCHRUNNING -> ENDMATCH -> POSTMATCH -> END
```

Post-match screens:
```
MatchVerdictScreen -> GunaScreen (karma selection) -> PostMatchPlayers -> MatchDetailScreen -> PlayerRewardScreen
```

---

## 1.2 The Five Fighting Styles

### AMUKTHA (Melee / Dash)
**Archetype:** Aggressive rushdown fighter. Close the gap, pressure with combos, dash to reposition.

| Stat | Value | Notes |
|------|-------|-------|
| Stamina | 10,000 | Standard |
| Armor | 7 | Mid-high |
| Movement Speed | 465 | Mid |
| Base Damage | 40 | Standard |
| Range | 3.5 units | Short (melee) |
| Max Willpower | 15,000 | Standard |
| Max Focus | 100 | 4 segments of 25 |

**Attack Speeds:**
- Melee: 1.5x | Melee Second: 1.5x
- Fire: 2.12x | Water: 1.875x | Air: 1.875x | Ether: 1.375x | Earth: 2.12x
- Special (Dash): 1.375x

**Unique Ability -- DASH:**
- 8-directional dash based on joystick input
- Min range: 3 units | Max range: MaxDashDistance + uniqueRange
- Directions map to dashVal 1-8: Forward, Forward-Right, Right, Back-Right, Back, Back-Left, Left, Forward-Left
- Fast repositioning tool -- can chase fleeing enemies or escape pressure
- No cooldown (focus cost only)

**Melee Combo:** Melee -> Melee_Second (2-hit chain). Impact detection at 50% animation completion. Can be chained continuously if input held.

**Shield (Brahma only):** Block incoming damage, shield attack for counter.

**Optimal Bot Behavior:** Close distance aggressively, circle-strafe at close range, use dash to gap-close or escape, pressure with melee combos, use spells at close range for guaranteed hits.

---

### MUKTHA MUKTHA (Melee / Axe)
**Archetype:** Heavy hitter. Deliberate, high-damage attacks. Axe throw for ranged option.

| Stat | Value | Notes |
|------|-------|-------|
| Stamina | 10,000 | Standard |
| Armor | 9 | Highest melee armor |
| Movement Speed | 455 | Slowest |
| Base Damage | 70 | HIGHEST base damage |
| Range | 4 units | Medium melee |
| Max Willpower | 15,000 | Standard |
| Max Focus | 100 | Standard |

**Attack Speeds:**
- Melee: 1.15x | Melee Second: 1.15x (SLOWEST melee)
- Fire: 2.12x | Water: 1.875x | Air: 1.875x | Ether: 1.375x | Earth: 2.12x
- Special (Axe Throw): 2.12x (fast projectile cast)

**Unique Ability -- AXE THROW:**
- State flow: Special_Aiming -> Special (throw) -> Axe_Callback (return)
- Brahma range scale: 35f | Shiva range scale: 50f
- Spawns projectile at ThrowSpawnPoint, travels to abilityPos
- Axe returns to thrower on callback
- Collision detection via SphereCast with castRadius

**Melee Combo:** Melee -> Melee_Second (2-hit chain). Slowest attack speed but highest damage per hit.

**Optimal Bot Behavior:** Deliberate approach, trade hits favorably (high damage + armor), use axe throw at mid-range, punish overcommits, don't chase -- let enemies come to you.

---

### MANTRA MUKTHA (Ranged / Teleport)
**Archetype:** Kiter. Hit-and-run with magic projectiles. Teleport to escape pressure.

| Stat | Value | Notes |
|------|-------|-------|
| Stamina | 10,000 | Standard |
| Armor | 4 | LOWEST armor |
| Movement Speed | 495 | Fast |
| Base Damage | 45 | Mid |
| Range | 16 units | LONGEST range |
| Max Willpower | 15,000 | Standard |
| Max Focus | 100 | Standard |

**Attack Speeds:**
- Melee: 1.5x | Melee Second: 2.0x
- Fire: 1.875x | Water: 1.375x | Air: 1.875x | Ether: 1.375x | Earth: 2.12x
- Special (Teleport): 3.0x (fastest special cast)

**Unique Ability -- TELEPORT:**
- Min range: 2 units | Max range: uniqueRange
- Instant position change to aimed location
- Fastest special ability cast speed (3.0x)
- Pre-teleport VFX plays on exit, teleport VFX on arrival
- Excellent escape tool and repositioning

**Ranged Attack -- MAGIC BALL:**
- Projectile type: MAGICBALL
- Spawns at RangedSpawnPoint, travels to MaxRangePoint
- Charged shot: 1.5x speed multiplier
- Quick shot: 1.0x speed
- Shiva Third Eye: adds shivaExplosionRadius for AoE on impact

**Aiming System:**
- State: Aiming -> charges during animation loop
- meleeChargingTime accumulates each frame
- Max charge: player.playerStats.maxHoldTime
- Release triggers Melee state (fires projectile)
- Combo variants: attackInt = 1 (normal) or 2 (from aiming)

**Optimal Bot Behavior:** Maintain 8-15m distance, kite melee opponents, teleport away when closed on, use charged shots for max damage, hit-and-run playstyle, never stay in melee range.

---

### PANI MUKTHA (Ranged / Discus)
**Archetype:** Zoner. Control space with discus throws. Maim (slow) enemies to maintain distance.

| Stat | Value | Notes |
|------|-------|-------|
| Stamina | 10,000 | Standard |
| Armor | 6 | Mid |
| Movement Speed | 475 | Mid |
| Base Damage | 45 | Mid |
| Range | 12 units | Long |
| Max Willpower | 15,000 | Standard |
| Max Focus | 100 | Standard |

**Attack Speeds:**
- Melee: 1.5x | Melee Second: 2.5x (fast secondary)
- Fire: 2.0x | Water: 2.5x | Air: 2.5x | Ether: 1.375x | Earth: 2.5x
- Special (Maim/Discus): 2.5x

**Dual Discus System:**
- rightDiscus: Always available (all gods)
- leftDiscus: Brahma only
- Holster system: Weapons store at Holster_Left/Right when unequipped
- Attack counter tracks which discus is active (1 = right, 2 = both for Brahma)

**Discus Path Mechanics (varies by god):**
- **Brahma:** Elliptical path -- Y-axis: range/2, X-axis: range/6, offset: (range/2 * -1) - 0.5. Discus flies in a curve.
- **Vishnu:** Direct straight throw to MaxRangePoint
- **Shiva:** Elliptical path + Third Eye variant with expanding explosion radius

**Unique Ability -- MAIM (Area Slow):**
- Effect: Applies Maim debuff (50% movement speed reduction)
- Radius: Maim_Range = player.playerStats.uniqueRange
- Duration: maimDuration
- Targets all enemies in radius
- Immunity: Third Eye active blocks Maim

**Optimal Bot Behavior:** Control mid-range (6-12m), zone with discus throws, use Maim when enemies cluster or approach, maintain distance from melee, exploit discus curve paths for angle attacks.

---

### YANTRAMUKTHA (Ranged / Bow)
**Archetype:** Sniper. Maximum range, charged shots, arrow spread. Impair enemies to slow approach.

| Stat | Value | Notes |
|------|-------|-------|
| Stamina | 10,000 | Standard |
| Armor | 5 | Low |
| Movement Speed | 485 | Mid-fast |
| Base Damage | 40 | Standard |
| Range | 16 units | LONGEST range (tied with MantraMuktha) |
| Max Willpower | 15,000 | Standard |
| Max Focus | 100 | Standard |

**Attack Speeds:**
- Melee: 1.5x | Melee Second: 1.875x
- All elementals: 1.375x (same for all)
- Special (Impair): 3.75x (FASTEST special ability)

**Arrow Mechanics (varies by god):**
- **Brahma:** Single arrow (index 0)
- **Shiva:** Single arrow (index 0)
- **Vishnu:** Triple arrow spread -- Left(-2), Center(0), Right(+2) offsets using MaxRangePoint.right
- Charged shot: 1.5x speed multiplier
- Quick shot: 1.0x speed

**Unique Ability -- IMPAIR (Movement Slow):**
- Effect: Applies Impair debuff (50% movement speed reduction)
- Fastest special ability cast (3.75x speed)
- Area effect with radius parameter
- Immunity: Third Eye active blocks Impair

**Optimal Bot Behavior:** Maximum distance (10-18m), retreat when closed on, use charged shots for damage, Impair approaching melee enemies, snipe from distance, reposition constantly.

---

## 1.3 The Three Gods (Trinity)

### BRAHMA (God Index 0)
**Theme:** Defense and control

**Bonuses:**
- Exclusive Shield mechanic (block + shield attack)
- Willpower Generation: +25% (1.25x faster health regen)
- Armor: +4
- Movement Speed: -25 penalty (slowest god)
- Unique Range: +5
- Melee Angle: 180 degrees (widest)
- Focus hit-streak starts at 3 (vs 1 for others)

**Shield Mechanics:**
- Activation: Press shield button -> Shield_Block state
- Block: Absorbs incoming damage, has integrity (hit counter)
- Shield Attack: Offensive counter from shield state
- Duration: Held while button pressed
- Cost: 1 focus segment (25 focus points)
- Shield integrity: Tracked by server, cracks appear at damage thresholds

**Impact Types vs Shield:**
- Amuktha Sword (Slice): 0.25x integrity damage
- MukthaMuktha Axe (ForceAndSlice): 0.75x integrity damage
- YantraMuktha Arrow (Pierce): 0.0x integrity damage (arrows bypass)
- PaniMuktha Discus (Slice): 0.25x integrity damage
- MantraMuktha Magic (Force): 0.5x integrity damage

**Astra -- BRAHMANDHA:**
- Spawns at world center (map centre position)
- 1 second delay before explosion
- Expanding AoE: starts at startRadius, expands to maxRadius
- Damage: astraDamage + (target.willPower x astraPercentDamage)
- Each player hit only once during expansion
- Cost: 4 focus segments (full bar)

---

### SHIVA (God Index 1)
**Theme:** Burst damage and dominance

**Bonuses:**
- Exclusive Third Eye mechanic
- Unique Range: +5
- No stat bonuses (pure offensive power through Third Eye)
- Damage multiplier: 1.2x on all attacks when god is Shiva

**Third Eye Mechanics:**
- Activation: Press Third Eye button -> Third_Eye_Anticipate -> Third_Eye state
- Duration: thirdEyeDuration (frame-counted, typically 6-10 seconds)
- Effects while active:
  - All damage dealt multiplied by thirdEyeDamageMultiplier (1.5x-2.0x)
  - IMMUNE to slows (AirSlow, Maim, Impair -- returns 1.0 movement)
  - IMMUNE to Stun (DoStun() cancelled if Third Eye active)
  - IMMUNE to Water Pushback (DoWaterPushback() returns false)
  - Melee AoE: Sword swing hits ALL players in melee range (360 degree coverage)
  - Projectile AoE: Ranged projectiles do AoE damage in thirdEyeAOERange radius
- Cost: Focus segments from CharacterData
- Condition: Cannot be muted, stunned, or already active

**Astra -- PASHUPATASTRA:**
- Spawns at PLAYER'S position (not world center)
- Expanding AoE sphere
- SphereCastAll detection in forward direction up to maxDistance
- Tick system: instant first frame, then dpsTick interval (0.5s)
- Lifetime: maxAstraLiftime (typically 5s)
- Damage: Same formula as Brahmastra

---

### VISHNU (God Index 2)
**Theme:** Speed and mobility

**Bonuses:**
- Movement Speed: +15 base, +30% multiplier (1.3x total)
- Armor Penalty: -2
- Unique Range: +5
- Stamina discount on dodge: 4,500 cost (vs 10,000 base -- 55% cheaper)
- No damage bonuses

**Speed Mechanics:**
- GetVishnuSpeedFactor(true) returns 1.3 (30% speed increase)
- Applied to all movement calculations
- Makes Vishnu the fastest god for any fighting style
- Combined with fast styles (MantraMuktha 495 + 30% = 643 effective) = very fast

**Arrow Spread (Yantramuktha + Vishnu):**
- Fires 3 arrows in spread pattern instead of 1
- Left/Center/Right offsets: 2f units apart
- More coverage but lower single-target damage

**Astra -- NARAYANASTRA:**
- Spawns at world center
- Weapon rain system (multiple projectiles from sky)
- AoE damage on impact zones
- Same damage formula

---

## 1.4 Elemental Spell System

### How Spells Work

Each character has 4-5 elemental spell slots. Spells cost focus segments to cast. The pipeline:

```
Player Input -> State: Spell_Anticipate -> Spell_Aiming (if aimed) -> Cast_Spell
-> SpellManager.InstantiateSelectedSpell() -> SpellProjectile spawns
-> Spell.Initialize() (burst damage) -> Spell.Process() (zone ticks)
-> Effects applied to hit players
```

### Spell Types

| Type | Behavior | Bot Consideration |
|------|----------|-------------------|
| INSTANT | Immediate effect at target location | Easy for bots -- just fire at target position |
| CHANNELING | Hold to charge, release to fire | Bot needs to hold input for charge time, then release |
| CHARGED | Build up power, release for bigger effect | Similar to channeling, longer hold = more damage |
| TRAPS | Place on ground, triggers when enemy enters | Bot should place at choke points or predicted paths |
| COATING | Apply buff/debuff effect | Bot should use before engaging or when allies nearby |
| SHIELD | Elemental shield protection | Bot should use reactively when threatened |

### Spell Subtypes
```csharp
SpellSubType: INSTANT, CHANNELING, CHARGED, TRAPS
SpellDamageMode: BurstOnly, ZoneOnly, EffectOnly, BurstAndZone, BurstAndEffect, ZoneAndEffect, BurstZoneAndEffect
```

### Elemental Effects

#### FIRE
- **Damage Mode:** BurstAndZone + EffectOnly
- **Effect:** FireBurn DoT (damage over time)
  - Continues dealing damage after leaving the zone
  - DoT PAUSES while inside source spell zone (prevents infinite refresh)
  - Resumes when player exits zone
- **Parameters:** effectDuration, effectDamage, effectTickInterval
- **Bot Strategy:** Fire at enemy position for burst + zone control. Fire DoT is excellent for area denial -- cast at choke points or where enemies will run through. Lead targets for zone placement.

#### WATER
- **Damage Mode:** BurstAndZone (moving)
- **Effect:** Water Pushback
  - PUSHES targets in spell direction
  - Transitions target to Water_Pushback state (blocks all input)
  - On spell destruction -> Pushback_Land state
  - Movement speed of push: water.moveSpeed
  - IMMUNE if: Third Eye active OR shield blocks
- **Bot Strategy:** Use to push enemies into hazards or away from allies. Excellent defensive tool -- push approaching melee away. Can push off edges or into walls for positional advantage.

#### AIR
- **Damage Mode:** BurstAndZone
- **Effect:** AirSlow (50% movement speed reduction)
  - Duration: effectDuration with tick damage
  - Significantly hampers enemy mobility
  - IMMUNE if: Third Eye active
- **Bot Strategy:** Use to slow approaching melee enemies. Cast at enemy's predicted path. Excellent setup for follow-up attacks -- slowed enemy is easy to hit with projectiles or combos.

#### EARTH
- **Damage Mode:** BurstOnly (NO zone ticks -- instant only)
- **Effect:** EarthStun
  - Forces target into StateType.Stun immediately
  - Blocks ALL input during stun
  - Only applies on burst hit (entering zone), not zone ticks
  - IMMUNE if: Third Eye active
- **Bot Strategy:** THE most valuable offensive spell. Stun enables free follow-up damage. Cast when enemy is in range for guaranteed burst hit. Prioritize Earth over other spells when setting up kills.

#### ETHER
- **Damage Mode:** BurstAndZone
- **Effect:** EtherMute
  - Blocks ALL spell casting for duration
  - AllowSpellCasting() returns false when muted
  - Prevents: spells, shields, special abilities, god abilities
  - NO immunity from Third Eye
- **Bot Strategy:** Use against spell-heavy opponents. Cast to prevent enemy from shielding or using abilities. Excellent counter to Brahma shield users -- mute then attack. Also good pre-engagement to disable enemy options.

### Spell Detection & AoE

**How AoE works server-side:**
- `spellDistance`: Radius in units for area detection
- `spellAngle`: Cone angle (divided by 2 for half-angle check)
- Detection: `GetPlayersInSpellRange(float distance)` uses ContactPoint distance check
- Angle filter: `TargetWithinAngle(target, angle)` uses Vector3.Angle()
- Typical AoE distances: 20-40 units radius
- Typical cone angles: 60-180 degrees

**Zone Ticks:**
- After initial burst, zone continues dealing damage
- Tick interval: `spellTickInterval` (0.5-2.0s typically)
- DPSCounter tracks timing
- Fire zones pause DoT inside (anti-cheese mechanic)

### Elemental Shield

- Activation: `playerBase.ActivateElementalShield(byte buttonIndex)`
- Duration: 10 seconds (hardcoded)
- Max hit count: BaseShieldIntegrity (configurable via BalanceOverrideProvider)
- Blocks physical and elemental attacks (with pass-through fractions)
- Each element has different effectiveness against different attack types

**Shield vs Physical Attacks (integrity damage):**
- Pierce (Yantramuktha arrow): 0.0x -- arrows bypass shields
- Slice (Amuktha/PaniMuktha): 0.25x
- Force (MantraMuktha): 0.5x
- ForceAndSlice (MukthaMuktha axe): 0.75x

**Shield vs Weapon Types (damage pass-through):**
- Bow Basic vs Fire shield: 100% pass-through
- Bow Basic vs Water/Air shield: 50% pass-through
- Bow Basic vs Earth/Ether shield: 0% (fully blocked)
- Sword vs Fire/Water shield: 50% pass-through
- Sword vs Air/Earth/Ether shield: 0% (fully blocked)
- Axe vs Fire/Water/Air shield: 50% pass-through
- Axe vs Earth/Ether shield: 0% (fully blocked)

**Astra vs Shield:** Bypasses shields entirely (full damage)

---

## 1.5 Melee Combat System

### Hit Detection Pipeline

```
Player presses attack -> StateType.Melee -> Animation plays
-> At 50% animation: PostMeleeAttack(attackTick) called
-> Rollback server to attackTick: GameManager.RollbackState()
-> GetPlayersInRange(player.playerStats.range)
-> TargetWithinAngle(target, player.playerStats.meleeAngle)
-> Apply damage if within angle
-> Forward state: GameManager.ForwardState()
```

### Range & Angle by Style

| Style | Range | Damage | Attack Speed |
|-------|-------|--------|-------------|
| Amuktha | 3.5 | 40 | 1.5x (fast) |
| MukthaMuktha | 4.0 | 70 | 1.15x (slow) |
| MantraMuktha | 16.0* | 45 | 1.5x |
| PaniMuktha | 12.0* | 45 | 1.5x |
| Yantramuktha | 16.0* | 40 | 1.5x |

*Ranged styles use projectiles at full range; melee range is close-quarters only

### Melee Combo System
- Melee -> Melee_Second: 2-hit chain
- Input during first attack animation triggers second attack
- Both hits use same range/angle detection
- MukthaMuktha also has Axe_Callback state for axe return

### Damage Calculation

```
baseDamage = player.playerStats.damage
x GetShivaDamageFactor()         [1.2x if god is Shiva, else 1.0x]
x thirdEyeDamageMultiplier      [1.5-2.0x if Third Eye active]
x chargeShotDamageMultiplier    [1.5x if charged attack]
x ShieldBlockMultiplier         [reduced if target is shielding]
x BotToHumanMultiplier          [if bot attacking human]
x TutorialDamageMultiplier      [if tutorial mode]
x FirstMatchDamageMultiplier    [if first match]

Final: targetPlayer.playerData.willPower -= finalDamage
```

---

## 1.6 Projectile System

### Projectile Types

| Type | Style | Behavior |
|------|-------|----------|
| ARROW | Yantramuktha | Straight-line, SphereCast hit detection |
| MAGICBALL | MantraMuktha | Straight-line, SphereCast hit detection |
| DISCUSS | PaniMuktha | Varies by god (straight/elliptical), SphereCast |

### Projectile Properties
- `projectileSpeed`: Base movement speed (30-50 units/s typical)
- `chargeSpeed`: Multiplier when fully charged (1.5-2.0x)
- `projectileRadius`: SphereCast radius for hit detection (0.5-2.0 units)
- `projectileDestination`: Set from player.abilityPos (where player aimed)
- `isCharged`: Boolean -- held to max charge time
- Movement: `Vector3.MoveTowards()` at projectileSpeed each frame

### Hit Detection (Projectile)
```
Each frame:
  Physics.SphereCast(position, radius, direction, out hit, distance)
  -> Check collider tag == "Player"
  -> Verify: not self, not dead, not same team
  -> Apply damage on first hit
  -> Destroy projectile or mark as hit
```

### PaniMuktha Discus Paths

**Brahma:** Elliptical orbit path
- Y-axis: range/2f | X-axis: range/6f | Offset: (range/2 * -1) - 0.5f
- Discus follows curved path around target area
- Catchable after move_counter > 8 or obstacle detected

**Vishnu:** Direct straight throw
- Single target destination
- No curve, travels straight to MaxRangePoint

**Shiva:** Elliptical + Third Eye expansion
- When Third Eye active: uses thirdEyeProjectile mesh
- Expanding explosion radius on impact

### Volley System (Yantramuktha Vishnu)
- 3-arrow spread for Vishnu: Left(-2), Center(0), Right(+2) offsets
- StartVolley(arrowCount) returns volleyId
- Each arrow resolves with OnVolleyArrowResolved(volleyId, hit)
- When ALL arrows resolved: counts as single hit/miss for focus

### Bot Aiming Considerations

**abilityPos** is the key field -- it determines WHERE spells and projectiles go:
- Server reads `player.abilityPos` for spell spawn location
- For AoE spells: center of AoE is at abilityPos
- For projectiles: destination is abilityPos
- Bots must set abilityPos to enemy's predicted position (not current position)

**Leading targets:** For projectiles traveling at projectileSpeed, bots need to:
1. Calculate target's velocity vector
2. Estimate travel time: distance / projectileSpeed
3. Set abilityPos to: targetPosition + (targetVelocity * travelTime)
4. Add slight randomization for human-like imperfection

---

## 1.7 Dodge System

### Mechanics
- State: StateType.Dodge
- Cost: base stamina (10,000 default, 4,500 for Vishnu -- 55% cheaper)
- Movement: `Vector3.MoveTowards()` to abilityPos at dodgeSpeed (35 units/s)
- Completion: When distance <= 0.1f
- Cooldown: Sets staminaCooldown = 2.0s on completion
- **NO invincibility frames** -- damage can still be taken during dodge
- Dodge provides positional displacement only

### What Dodge Can Cancel
- Can cancel most states except Death
- State machine prevents input during dodge animation
- Dodge blocks all other input (BlockAll flag)

### Bot Dodge Strategy
Since there are no i-frames, dodging is purely about repositioning:
- Dodge SIDEWAYS to avoid straight-line projectiles
- Dodge BACKWARD to create distance from melee
- Dodge TOWARD to close gap on fleeing ranged enemy
- Time dodge to avoid AoE zones (dodge out of Fire/Water area)

---

## 1.8 Special Abilities (Per Style)

### Amuktha -- DASH
- 8-directional movement burst
- Min 3 units, max MaxDashDistance + uniqueRange
- No cooldown (focus cost only)
- Use: Gap close, escape, reposition

### MukthaMuktha -- AXE THROW
- Ranged projectile from melee character
- States: Special_Aiming -> Special (throw) -> Axe_Callback (return)
- Brahma: range 35f | Shiva: range 50f
- SphereCast hit detection
- Axe must return before next throw

### MantraMuktha -- TELEPORT
- Instant position change
- Min 2 units, max uniqueRange
- Fastest special cast (3.0x speed)
- Use: Escape melee pressure, reposition to sniping spot

### PaniMuktha -- MAIM (Area Slow)
- AoE debuff: 50% movement speed for maimDuration
- Radius: Maim_Range = uniqueRange
- Affects all enemies in radius
- Third Eye immune
- Use: Slow approaching enemies, enable follow-up attacks

### YantraMuktha -- IMPAIR (Movement Slow)
- Area debuff: 50% movement speed for impairDuration
- Fastest special ability (3.75x speed)
- Third Eye immune
- Use: Slow enemies to enable sniping, kite melee fighters

---

## 1.9 Status Effects

| Effect | Element/Source | Duration | Mechanic | Third Eye Immune? |
|--------|---------------|----------|----------|-------------------|
| FireBurn | Fire spells | effectDuration | DoT (damage per tick), pauses in source zone | No |
| AirSlow | Air spells | effectDuration | 50% movement speed | Yes |
| EarthStun | Earth spells | effectDuration | Blocks ALL input, forced Stun state | Yes |
| EtherMute | Ether spells | effectDuration | Blocks ALL spell casting | **No** (even Third Eye can't prevent mute) |
| Impair | Yantramuktha special | impairDuration | 50% movement speed | Yes |
| Maim | PaniMuktha special | maimDuration | 50% movement speed | Yes |
| ThirdEye | Shiva god ability | thirdEyeDuration | Damage buff + immunities | N/A (is the buff) |

### Effect Application
- `character.AddEffect(effect, skipShield)`: Adds to player's effects list
- If effect type already active: refreshes duration
- If player has elemental shield: shield absorbs (unless bypassed)
- EarthStun also forces StateType.Stun immediately

---

## 1.10 Focus System (Spell Resource)

### How Focus Works
- Max: 100 points (4 segments of 25)
- Gained by: Landing hits (streak-based), getting hit (+1)
- Lost by: Casting spells (cost in segments)
- Miss: Resets streak to 1 (Brahma: resets to 3)

### Focus Costs
- Standard spell: 1-2 segments (25-50 focus)
- Elemental shield: 2 segments (50 focus)
- Astra ultimate: 4 segments (100 focus -- full bar)
- Special ability: Varies by style

### Bot Resource Management
- **Aggressive bots:** Spend focus freely, always casting
- **Defensive bots:** Save focus for shields and escapes
- **Smart bots:** Save 4 segments when enemy is low HP for Astra finish
- **Build focus:** Melee attacks build focus via hit streaks

---

## 1.11 Damage System Summary

### Willpower as Health
- `playerData.willPower`: Current health pool
- `playerStats.willPower`: Max health (15,000 for all styles)
- Death at willPower <= 0
- Respawn restores to max

### Damage Modifiers Stack

| Modifier | Value | Condition |
|----------|-------|-----------|
| Shiva God | x1.2 | God = Shiva (always active) |
| Third Eye | x1.5-2.0 | Shiva Third Eye effect active |
| Charged Shot | x1.5 | Attack held to max charge |
| Shield Block | varies | Target has active elemental shield |
| Bot vs Human | varies | First match damage reduction |
| Tutorial | varies | Tutorial mode damage scaling |

### Knockback/Pushback
- Water spells ONLY
- Uses CharacterController.Move() in spell direction
- State: Water_Pushback (blocks all input)
- Speed: water.moveSpeed
- Duration: While in water spell collider
- Immune: Third Eye OR shield blocks

---

## 1.12 State Machine (Complete FSM)

### All States

| State | Category | Description |
|-------|----------|-------------|
| Idle | Neutral | Default -- can take any action |
| Melee | Combat | First melee attack |
| Melee_Second | Combat | Combo second hit |
| Aiming | Combat | Ranged weapon aimed (pre-fire) |
| Cast_Spell | Combat | Spell actively casting |
| Spell_Aiming | Combat | Spell being aimed (pre-cast) |
| Spell_Anticipate | Combat | Spell pre-cast animation |
| Channel | Combat | Charging spell |
| Shield_Block | Defense | Brahma shield blocking |
| Shield_Attack | Defense | Brahma shield counter-attack |
| Cast_Shield | Defense | Elemental shield active |
| Dodge | Defense | Dodge roll movement |
| Special | Ability | Unique ability executing |
| Special_Aiming | Ability | Aiming unique ability |
| Special_Anticipate | Ability | Pre-ability animation |
| Third_Eye | God | Shiva buff active |
| Third_Eye_Anticipate | God | Pre-Third Eye animation |
| Astra_Anticipate | God | Pre-ultimate animation |
| Astra_Channel | God | Ultimate channeling |
| Astra_Cast | God | Ultimate active |
| Stun | CC | Stunned -- no input |
| Water_Pushback | CC | Being pushed by water |
| Pushback_Land | CC | Landing after pushback |
| Jump | Movement | In the air |
| Vulnerable | Transition | Teleport vulnerability window |
| Death | Terminal | Dead |
| Teleport | Transition | Map start teleport |
| Victory | Terminal | Match won |

### Key State Checks for Bot AI
```
IsDead()                    -> In Death state
AllowSpellCasting()         -> Not muted, not in blocking state
IsBlockingInput(flag)       -> Specific state prevents this action
IsThirdEyeActive()         -> Shiva Third Eye buff running
IsImpairable()             -> Can be affected by movement debuffs
IsMuted()                  -> Ether mute effect active
```

---

## 1.13 Server Architecture for Bots

### Bot Execution Loop
```
Every 0.0167s (60Hz):
  BotManager.BotTick()
    -> For each bot:
      -> bot.OnUpdate()
        -> botBT.root.Evaluate()           [Run decision tree]
        -> ProcessBotState()                [Convert to KeyInput]
        -> PlayerManager.ProcessPlayerInputTick()  [Execute input]
    -> CheckBotQuickComplete()              [End match if humans gone]
```

### KeyInput Packet (What Bots Control)
```csharp
KeyInput {
    byte JoystickAxis;          // Movement (packed x,y nibbles)
    float cameraRotation;       // Facing angle (Euler Y)
    byte meleeAbility;          // Melee/ranged attack
    byte elementalAbility1-4;   // Spell slots 1-4
    byte specialAbility;        // Unique ability
    byte abilityEx;             // God ability (shield/ThirdEye)
    byte dodgeAbility;          // Dodge
    byte astraAbility;          // Ultimate
    Vector2 abilityPos;         // Target position for spells/projectiles
    UInt32 tick;                // Tick counter
    FSM.StateType state;        // Current state
}
```

### EventState Values (Input Commands)
```
NONE = 0           // No input
START = 1          // Begin aiming/holding
PROGRESS = 2       // Execute ability
PROGRESS_CONTINUOUS = 3  // Hold to repeat
AIMING = 4         // Active aiming mode
SHIELDUP = 5       // Shield/elemental shield up
CHANNELING = 6     // Spell charging
DONE = 7           // Release/stop
```

### What Each Input Byte Does

**meleeAbility:**
- PROGRESS (2) -> Attack (melee or ranged fire)
- AIMING (4) -> Start ranged aim state
- PROGRESS_CONTINUOUS (3) -> Hold for multi-hit

**elementalAbility[1-4]:**
- CHANNELING (6) -> Start spell channel
- AIMING (4) -> Start spell aim
- PROGRESS (2) -> Execute spell directly
- SHIELDUP (5) -> Activate elemental shield

**specialAbility:**
- START (1) -> Begin unique ability
- AIMING (4) -> Aim special
- DONE (7) -> Cancel aiming

**abilityEx (God Ability):**
- Brahma: START (1) = Shield Attack, AIMING (4) = Shield Block
- Shiva: PROGRESS (2) = Third Eye

**dodgeAbility:**
- START (1) -> Enter dodge state
- PROGRESS (2) -> Execute dodge

**astraAbility:**
- CHANNELING (6) -> Begin ultimate charge (requires 4 focus segments)

---

# PART 2: CURRENT BOT AI (What Exists Today)

## 2.1 Current Architecture

Bots use a flat Behavior Tree with Selector (priority) nodes. The tree evaluates every tick at 60Hz.

### Decision Tree (Current -- Priority Order)
```
Root (Selector -- first success wins)
|-- 1. IsBotDead -> Exit immediately
|-- 2. Sequence: Defensive Shield
|  |-- IsBotStateSpells() -> spell mode available?
|  |-- CheckPlayerDamaged(2500) -> took 2500+ damage?
|  +-- CastDefenseSpell() -> cast random shield
|-- 3. Sequence: Change Target
|  |-- HasTargetReachedTimeThreshold(5-10s) -> time to switch?
|  +-- SetRandomTarget() -> pick new random enemy
|-- 4. Sequence: Cast Spell
|  |-- IsBotStateSpells() -> spell mode available?
|  |-- TargetWithinRange() -> enemy in range?
|  |-- CheckForSpell() -> random spell every 10s
|  +-- CastSpell() -> execute spell
|-- 5. Sequence: Melee Attack
|  |-- IsBotStateMelee() -> melee mode available?
|  |-- TargetWithinRange() -> enemy in range?
|  +-- Attack() -> melee every 1.8s (0.9s vs bots)
+-- 6. Sequence: Movement
   |-- IsBotStateEnabled() -> bot active?
   |-- GetNearestEnemy() -> find closest enemy
   +-- MoveToTarget() -> walk toward enemy (Vector2.up, always forward)
```

### Bot States
```csharp
enum BotState {
  DISABLED = 0,           // No actions (tutorial)
  MELEEACTION = 1,        // Melee only
  SPELLMELEEACTION = 2,   // Spell + melee
  FULL = 3                // Everything
}
```

## 2.2 Current Bot Behaviors -- What They Do

### Movement
- **Always move forward** toward target using Vector2.up (straight line)
- Smooth Slerp rotation to face target (12f lerp speed)
- **NO strafing, NO circling, NO retreating** (except when muted: Vector2.down)
- Special case: PaniMuktha gets +8 degree offset with non-Vishnu god

### Melee Attacks
- Fixed interval: 1.8s vs humans, 0.9s vs bots
- Single hit only -- no combos exploited
- Just sets "Melee" = 1 in shared data
- No timing based on enemy state

### Spell Casting
- Wait 10-15 seconds between casts (random)
- Randomly select from available elementals (try up to 5 times)
- Skip SHIELD-type slots during offense
- Check focus availability before casting
- **No intelligent spell selection** -- random picks

### Defensive Shield
- Trigger: Took >= 2,500 damage spike
- Search for SHIELD-type slot, fallback to random
- Requires 2+ focus segments
- **Only reactive** -- never proactive shielding

### Target Selection
- Primary: Nearest enemy (distance-based)
- Switch every 5-10s (random timer)
- 30% chance to prefer real players over bots
- **No HP-based targeting, no tactical assessment**

## 2.3 Current Bot Behaviors -- What They DON'T Do

| Missing Behavior | Impact |
|------------------|--------|
| **Never dodge** | Bots stand and take hits -- instantly looks like AI |
| **Never use god abilities** | Brahma shield, Shiva Third Eye never activated |
| **Never use Astra** | Full focus bar wasted -- ultimate never cast |
| **Never use special abilities** | No dash/teleport/axe throw/maim/impair |
| **No strafing or positioning** | Walk in straight line, stop, attack |
| **No retreat** | Never back away from danger (except mute) |
| **No combo chaining** | Single melee hits only |
| **Random spell selection** | No tactical spell choice based on situation |
| **No opponent awareness** | Don't react to enemy attacks or states |
| **No HP awareness** | Don't play differently at low/high health |
| **No focus management** | Don't save focus for important abilities |
| **No team coordination** | In 2v2/3v3, bots act independently |
| **All styles identical** | Same behavior tree for all 5 fighting styles |
| **Same difficulty always** | No easy/medium/hard tiers |
| **Instant reactions** | 0ms response time -- obviously artificial |
| **Predictable patterns** | Walk -> stop -> attack -> occasional spell -> repeat |
| **No projectile leading** | Spells/projectiles aimed at current position, not predicted |
| **No AoE placement** | Spells cast randomly, not at strategic locations |

---

# PART 3: WORLD-CLASS BOT AI DESIGN

## 3.1 Architecture: Hybrid Utility-BT (Three Layers)

Replaces the flat priority BT with a three-layer system inspired by For Honor's bot AI (Ubisoft, GDC 2025), Killzone 2 (Guerrilla Games), and Game AI Pro recommendations.

### Layer 1: STRATEGIC (Evaluates every 1-2 seconds)
**Purpose:** High-level decisions -- WHO to fight, WHERE to be, WHAT role to play

Decisions:
- **Target Selection:** Based on weighted factors (HP, distance, threat level, teammate focus, isolation)
- **Positioning Goal:** Where does the bot want to be? (comfort zone for fighting style)
- **Team Role:** In 2v2/3v3 -- engager, supporter, or flanker
- **Strategy Mode:** Aggressive (pushing), defensive (retreating), neutral (spacing)

### Layer 2: TACTICAL (Evaluates every 0.25-0.5 seconds, after reaction delay)
**Purpose:** Combat decisions -- WHAT action to take right now

This is the Utility Scorer. Every possible action gets a score from 0.0 to 1.0:

| Action | Score Factors |
|--------|---------------|
| Melee Attack | In range? Target vulnerable? Own HP? Aggression weight? |
| Cast Fire | Target stationary? Zone control value? Focus available? |
| Cast Water | Target near edge? Need pushback? Defensive value? |
| Cast Air | Target approaching? Need slow? Setup value? |
| Cast Earth | Target in range for stun? Kill potential? Highest priority spell |
| Cast Ether | Target spell-heavy? Need to mute? Counter value? |
| Elemental Shield | Under attack? Expect damage? Focus available? |
| Dodge | Enemy attacking? Projectile incoming? HP low? |
| Special Ability | Style-specific value assessment |
| God Ability | Brahma shield timing, Shiva Third Eye value, Vishnu passive |
| Astra Ultimate | 4 focus available? Target low HP? Team fight value? |
| Approach | Too far from comfort zone? Target fleeing? |
| Retreat | Too close? HP low? Retreat threshold? |
| Circle-Strafe | In comfort zone? Want unpredictability? |
| Switch Target | Current target too tanky? Teammate needs help? |

**Score Formula:**
```
finalScore = baseScore * personalityWeight * situationalMultiplier * (1 - mistakeNoise)
```

Where `mistakeNoise` = random 0.0 to `mistakeChance` -- occasionally picks suboptimal action.

### Layer 3: EXECUTION (Every tick, 60Hz)
**Purpose:** HOW to mechanically perform the chosen action

Uses the existing BT infrastructure to generate KeyInput packets. This layer handles:
- Movement interpolation (smooth strafing, approach angles)
- Aim position calculation (lead targets for projectiles)
- Input state management (hold/release timing for channeled spells)
- FSM compliance (don't send inputs that current state blocks)

---

## 3.2 Personality System (5 Fighting Style Profiles)

Each bot has a BotPersonality that biases the Utility Scorer:

### Amuktha Profile -- "The Rusher"
```
Archetype: Aggressive rushdown
Comfort Zone: 2-5m (close range)
Aggressiveness: 0.85
Defensiveness: 0.3
Spell Preference: 0.4 (prefers melee over spells)
Reposition Frequency: 0.7 (circles often at close range)
Reaction Time Base: 180ms (+/- 80ms)
Mistake Chance: 0.08
Pressure Threshold: 40% HP (gets more aggressive below this)
Retreat Threshold: 15% HP (rarely retreats)
```

**Behavioral Patterns:**
- Dash to close distance aggressively
- Circle-strafe at close range (constant movement)
- Pressure with melee combos, interrupt with Earth stun
- Use Fire for area denial behind target (cut off escape)
- Dodge sideways when attacked (reposition, not retreat)
- Third Eye (Shiva) activates before engaging
- Save Astra for finishing blows
- In teams: always the engager

### MukthaMuktha Profile -- "The Brawler"
```
Archetype: Heavy trader
Comfort Zone: 3-6m (mid-close)
Aggressiveness: 0.7
Defensiveness: 0.5
Spell Preference: 0.5 (balanced)
Reposition Frequency: 0.4 (more stationary)
Reaction Time Base: 250ms (+/- 100ms)
Mistake Chance: 0.10
Pressure Threshold: 50% HP
Retreat Threshold: 20% HP
```

**Behavioral Patterns:**
- Deliberate approach (not rushing)
- Trade hits favorably (high damage + armor)
- Axe throw at mid-range for poke damage
- Use Earth stun for guaranteed axe + melee follow-up
- Shield (Brahma) against ranged poke
- Don't chase -- control space and punish approaches
- Wait for enemy to commit, then counter
- In teams: off-tank, protect ranged teammates

### MantraMuktha Profile -- "The Ghost"
```
Archetype: Hit-and-run kiter
Comfort Zone: 8-15m (far)
Aggressiveness: 0.4
Defensiveness: 0.7
Spell Preference: 0.8 (heavily prefers spells and projectiles)
Reposition Frequency: 0.9 (constantly repositioning)
Reaction Time Base: 200ms (+/- 60ms)
Mistake Chance: 0.06
Pressure Threshold: 60% HP (plays safe early)
Retreat Threshold: 30% HP
```

**Behavioral Patterns:**
- NEVER stay in melee range -- teleport away immediately
- Charged magic ball shots from max range
- Air slow on approaching melee, then kite backward
- Ether mute on enemy Brahma (disable their shield)
- Teleport to escape -- always have escape route planned
- Earth stun only at safe distance (don't get caught in melee while casting)
- In teams: always supporter or flanker, never engager
- Focus on different target than teammate's engager

### PaniMuktha Profile -- "The Controller"
```
Archetype: Space controller / zoner
Comfort Zone: 6-12m (mid)
Aggressiveness: 0.5
Defensiveness: 0.6
Spell Preference: 0.7
Reposition Frequency: 0.6
Reaction Time Base: 220ms (+/- 70ms)
Mistake Chance: 0.08
Pressure Threshold: 45% HP
Retreat Threshold: 25% HP
```

**Behavioral Patterns:**
- Control mid-range with discus throws (Brahma: curved path for angle attacks)
- Maim approaching enemies (50% slow, setup for team)
- Water pushback to reset distance when pressured
- Place Fire/Earth at choke points for area denial
- Maintain distance from melee, close distance on ranged
- In teams: supporter, controls zone between engager and enemy

### Yantramuktha Profile -- "The Sniper"
```
Archetype: Maximum range threat
Comfort Zone: 10-18m (maximum distance)
Aggressiveness: 0.3
Defensiveness: 0.8
Spell Preference: 0.9 (almost always ranged)
Reposition Frequency: 0.8 (repositions to maintain range)
Reaction Time Base: 200ms (+/- 60ms)
Mistake Chance: 0.05
Pressure Threshold: 50% HP
Retreat Threshold: 30% HP
```

**Behavioral Patterns:**
- Maximize distance at all times
- Charged arrow shots for damage (Vishnu: 3-arrow spread for coverage)
- Impair on any approaching enemy (slow their advance)
- Retreat instantly when melee closes distance
- Lead targets with projectiles (account for travel time)
- Earth stun on close enemies for escape window
- In teams: always furthest back, focus fire on team target
- Switch to whoever teammate is fighting

---

## 3.3 Reaction Time System

**THE single most important change for human-like behavior.**

### How It Works
1. Bot PERCEIVES a threat (enemy attack animation, projectile, spell)
2. Perception starts a reaction timer
3. Timer = reactionTimeBase + Random(-variance, +variance) milliseconds
4. Bot can only RESPOND (dodge, shield, counter) after timer expires

### Reaction Time by Difficulty

| Difficulty | Base | Variance | Effective Range | Human Equivalent |
|------------|------|----------|-----------------|------------------|
| Easy | 400ms | +/-150ms | 250-550ms | Casual player |
| Medium | 250ms | +/-100ms | 150-350ms | Average player |
| Hard | 150ms | +/-50ms | 100-200ms | Expert player |

### What Triggers Reactions
- Enemy enters melee range -> potential dodge/block
- Enemy starts attack animation -> dodge or counter timing
- Projectile fired at bot -> sidestep or shield
- Spell AoE spawning at bot's position -> move out
- Teammate taking damage -> peel consideration
- Own HP dropping below threshold -> mode shift

---

## 3.4 Movement Humanization

### Replace Vector2.up with Context-Aware Movement

**Current:** Always move straight at target -> stop -> attack -> repeat
**New:** Dynamic movement based on distance, style, and situation

### Movement Modes

**Approach (outside comfort zone):**
- Move toward target with slight angle offset (not straight line)
- Angle offset: random 10-30 degrees, changes every 2-4s
- Creates natural-looking approach path
- Speed: full movement speed

**Retreat (inside comfort zone for ranged, or HP below threshold):**
- Move away from nearest threat
- Angle away at 150-170 degrees (not perfectly backwards)
- Ranged styles: always retreat when melee enters comfort zone
- Speed: full movement speed

**Circle-Strafe (inside comfort zone):**
- Orbit target at comfort distance
- Direction: random left/right, changes every 2-4s
- Speed: 70-100% movement speed (slight variation)
- Creates unpredictable lateral movement

**Jitter (micro-movements):**
- Small random direction changes every 0.5-1.0s
- Magnitude: 10-20% of input range
- Simulates the constant small adjustments real players make
- Applied on top of primary movement mode

### Style-Specific Movement

| Style | Primary Mode | On Pressure | On Low HP |
|-------|-------------|-------------|-----------|
| Amuktha | Approach + Strafe close | Strafe faster | Dash escape |
| MukthaMuktha | Slow approach | Hold ground | Shield or retreat |
| MantraMuktha | Kite at max range | Teleport escape | Full retreat |
| PaniMuktha | Maintain mid-range | Maim + retreat | Dodge backward |
| Yantramuktha | Maximize distance | Impair + retreat | Full retreat |

---

## 3.5 Intelligent Spell Selection

### Replace Random with Weighted Situational Choice

### Fire (Area Denial + DoT)
**High value when:**
- Target is stationary (casting, stunned, blocking) -> guaranteed zone hit
- Choke point nearby -> deny escape routes
- Multiple enemies clustered -> AoE value
- Team fight -> zone control

**Low value when:**
- Target is mobile and far -> will dodge zone
- Focus is low (save for Earth stun or shield)

### Water (Pushback + Displacement)
**High value when:**
- Melee enemy in close range -> push away for breathing room
- Target near own teammate -> push away from ally
- Need to reset engagement

**Low value when:**
- Target has Third Eye (immune to pushback)
- Target has elemental shield (blocks pushback)
- Target is already far away

### Air (Slow + Tick Damage)
**High value when:**
- Target approaching (melee closing in) -> slow their advance
- Setting up follow-up attack -> slowed target easier to hit
- Team fight -> slow key threat for teammate

**Low value when:**
- Target has Third Eye (immune to slow)
- Target is already slowed

### Earth (STUN -- Highest Priority Offensive)
**High value when:**
- Target in range for guaranteed burst hit -> free stun
- Setting up kill combo -> stun + follow-up damage
- Enemy about to cast dangerous spell -> interrupt
- Enemy channeling Astra -> cancel it
- Enemy low HP -> stun + finish

**Low value when:**
- Target has Third Eye (immune to stun)
- Target too far for burst hit (Earth only does burst, no zone)

### Ether (Mute -- Anti-Spell)
**High value when:**
- Target is Brahma god -> disable their shield
- Target is about to cast spells -> silence them
- Counter-play against spell-heavy enemy

**Low value when:**
- Target is already muted
- Target is melee-focused (mute less impactful)

---

## 3.6 Projectile Aiming & Leading Targets

### Lead Targeting Algorithm
```
1. targetPosition = enemy.transform.position
2. targetVelocity = (enemy.position - enemy.lastPosition) / deltaTime
3. distanceToTarget = Vector3.Distance(bot.position, targetPosition)
4. travelTime = distanceToTarget / projectileSpeed
5. predictedPosition = targetPosition + (targetVelocity * travelTime)
6. abilityPos = predictedPosition
```

### Humanization of Aim
- Add random offset: aimOffset = Random(-accuracy, +accuracy)
- Easy bots: large offset (+/-3.0 units, miss frequently)
- Medium bots: moderate offset (+/-1.5 units)
- Hard bots: small offset (+/-0.5 units, accurate)
- Accuracy degrades with distance (natural falloff)
- Accuracy degrades under pressure (HP low, being attacked)

### AoE Spell Placement
For AoE spells (Fire, Water, Air, Earth, Ether), bots should:
1. If target is stationary -> cast at current position
2. If target is moving -> cast slightly ahead of them (they walk into zone)
3. If target is approaching -> cast between bot and target (forces them through)
4. For area denial -> cast at choke points or escape routes
5. For team fights -> cast at enemy cluster center

---

## 3.7 Difficulty Scaling

### Three Tiers (Scale Execution, Not Capability)

All difficulty levels have access to ALL abilities. The difference is HOW WELL they execute.

| Aspect | Easy | Medium | Hard |
|--------|------|--------|------|
| Reaction time | 400ms +/-150ms | 250ms +/-100ms | 150ms +/-50ms |
| Mistake chance | 25% | 12% | 3% |
| Spell selection | Slightly biased random | Situationally weighted | Near-optimal |
| Dodge frequency | Rare (low utility weight) | Regular | Reads attack windups |
| Aim accuracy | +/-3.0 unit offset | +/-1.5 unit offset | +/-0.5 unit offset |
| Target lead | No prediction | Basic prediction | Advanced prediction |
| Combo awareness | Single hits | Basic chains | Optimized sequences |
| Focus management | Wasteful (cast whenever) | Moderate (save some) | Efficient (save for key moments) |
| Target switching | Random timer | HP-based | Tactical assessment |
| God ability usage | Never | Sometimes | Strategic |
| Astra usage | Never | When full focus | Kill-confirming |
| Team coordination | None | Basic focus fire | Full blackboard |

### Why This Approach Works (For Honor Model)
Easy bots CAN dodge -- they just react 400ms late (human-like slow reactions). They don't look "stupid" -- they look like a new player who hasn't learned timing. Hard bots react at 150ms -- they look like an experienced player who reads your patterns. This is more natural than removing abilities.

---

## 3.8 Match Adaptation (In-Match Learning)

### Track Per-Opponent Patterns
During the match, bots track:

| Tracked Pattern | Response Adaptation |
|-----------------|---------------------|
| Opponent dodges after every melee | Delay follow-up, bait dodge then attack |
| Opponent always attacks from left | Dodge right preemptively |
| Opponent uses same spell repeatedly | Pre-dodge that spell's AoE area |
| Opponent never blocks | Be more aggressive |
| Opponent blocks frequently | Use Earth stun or Ether mute first |
| Opponent is passive (waiting) | Approach cautiously, use spells to force action |

### Match Momentum
- **Winning:** Play slightly looser (entertaining for viewer), more aggressive
- **Losing:** Play tighter, more defensive, look for openings
- **Even:** Standard personality-driven play

### Fatigue Simulation
- Over match duration, reaction times increase 5-15%
- After taking a big hit: briefly more defensive (2-3 seconds)
- After landing a kill: briefly more aggressive (3-5 seconds)
- After dying: come back slightly more cautious

---

## 3.9 Team Coordination (2v2, 3v3)

### Team Blackboard (Shared Data)
All team bots read/write to a shared blackboard:

```
TeamBlackboard {
    focusTarget: Player           // Agreed kill target
    roles: {playerId: Role}       // Engager/Supporter/Flanker
    needsPeeling: Player          // Teammate under pressure
    focusTargetHP: float          // Track focus target health
    teamHealthAverage: float      // Overall team health
    enemyHealthLowest: Player     // Weakest enemy
}
```

### Role Assignment
Based on fighting style:

| Role | Assigned To | Behavior |
|------|-------------|----------|
| Engager | Amuktha, MukthaMuktha | Close distance, initiate fights, draw attention |
| Supporter | PaniMuktha, MantraMuktha | Maintain range, support engager, zone control |
| Flanker | Yantramuktha (or 2nd melee) | Attack from angle, focus fire, finish low targets |

### Team Behaviors

**Focus Fire:**
- Team agrees on one target (lowest HP or most isolated)
- All bots prioritize that target
- Switch when target dies or escapes
- This alone makes team bots feel 10x smarter

**Peeling:**
- If teammate is below 30% HP AND being attacked
- Nearby bot switches to intercept the attacker
- Uses CC spells (Earth stun, Water pushback) to protect teammate
- Ranged bots prioritize long-range support (slow/mute attacker)

**Positioning:**
- Engagers: Close to enemies, between enemies and supporters
- Supporters: Behind engager, maintaining comfort range
- Flankers: Offset position, approaching from side/behind

---

## 3.10 Implementation Phases

### Phase 1: Core Systems (HIGHEST IMPACT)
1. BotPersonality class with 5 style presets
2. BotMovement -- replace Vector2.up with context-aware movement (strafe/retreat/approach/jitter)
3. BotReactionTimer -- perception delay before responses
4. BotUtilityScorer -- score all actions, pick highest
5. Missing action nodes: ExecuteDodge, ExecuteSpecialAbility, ExecuteGodAbility, ExecuteAstra, ExecuteReposition
6. Restructure BotBT to use utility scorer output

**Expected result:** Bots that strafe, dodge, use all abilities, and play differently per style.

### Phase 2: Combat Intelligence (HIGH IMPACT)
1. Intelligent spell selection (weighted by situation, not random)
2. Opponent state awareness (react to enemy states)
3. Projectile lead targeting (aim at predicted position)
4. AoE spell placement (zone denial, interception)
5. Attack timing variance (not fixed 1.8s)
6. Focus/resource management (save for key moments)
7. God ability usage (Brahma shield, Shiva Third Eye, Astra)

**Expected result:** Bots that make smart combat decisions and hit their spells.

### Phase 3: Depth & Difficulty (MEDIUM-HIGH IMPACT)
1. Three difficulty tiers (Easy/Medium/Hard)
2. Match adaptation (track opponent patterns)
3. Intentional mistakes system (human-like errors)
4. Fatigue/tilt simulation
5. Combo optimization per style
6. Advanced positioning (use map geometry)

**Expected result:** Bots that feel like real players at different skill levels.

### Phase 4: Team Mode (HIGH IMPACT for team modes)
1. Team blackboard implementation
2. Role assignment per style
3. Focus fire coordination
4. Peeling behavior
5. Positioning relative to teammates
6. Zone control in 3v3

**Expected result:** Team bots that coordinate like a real squad.

---

## 3.11 Key Design Principles

1. **Difficulty = execution quality, not capability removal.** Easy bots dodge late. Hard bots dodge on time. Don't remove abilities at lower difficulties.

2. **Personality > raw intelligence.** A "dumb" aggressive Amuktha that plays its rushdown style correctly is more fun than a "smart" bot that plays generically. Each style must FEEL different.

3. **Reaction time is king.** The #1 factor separating bots from humans. 200-400ms delay with variance. Current bots react at 0ms -- instantly detectable.

4. **Comfort zones per style.** Ranged bots maintaining distance looks intelligent. Melee bots rushing in looks correct. This alone differentiates styles massively.

5. **Imperfection is a feature.** Bots should occasionally overcommit, dodge the wrong way, waste focus on bad spells. Real players make these mistakes. Perfect play looks robotic.

6. **Movement sells the illusion.** A bot that strafes, circles, and jitters looks human even with simple decision-making. Static bots look artificial even with perfect decisions.

7. **Spacing is the meta.** In real fighting games, most of the skill is in positioning (footsies). Bots that maintain correct distance for their style automatically look skilled.

8. **Earth stun is the high-value play.** Smart bots should prioritize Earth spells for stun then follow-up damage combos. This is what skilled players do.

9. **Team coordination multiplies perception.** A team of bots that focus-fire the same target looks dramatically more intelligent than individually smart bots acting independently.

10. **Adaptation creates the illusion of intelligence.** A bot that changes behavior after being hit the same way twice looks like it's "learning" -- even simple pattern tracking creates this effect.

---

# PART 4: REFERENCE DATA

## 4.1 All Server Bot Files

| File | Purpose | Lines |
|------|---------|-------|
| BotManager.cs | Orchestrates all bots, tick loop | ~230 |
| Bot.cs | Individual bot controller | ~192 |
| BotBT.cs | Behavior tree root definition | ~56 |
| Attack.cs | Melee attack node | ~80 |
| CastSpell.cs | Offensive spell cast node | ~90 |
| CastDefenseSpell.cs | Defensive shield node | ~70 |
| GetNearestEnemy.cs | Nearest enemy targeting | ~40 |
| SetRandomTarget.cs | Random target selection | ~60 |
| TargetWithinRange.cs | Range check node | ~50 |
| MoveToTarget.cs | Movement toward target | ~40 |
| HasTargetReachedTimeThreshold.cs | Target switch timer | ~30 |
| IsBotDead.cs | Death check node | ~15 |
| CheckPlayerDamaged.cs | Damage threshold check | ~30 |

## 4.2 Combat Value Quick Reference

| Parameter | Value |
|-----------|-------|
| Max Willpower (all styles) | 15,000 |
| Max Focus | 100 (4 segments of 25) |
| Max Stamina | 10,000 |
| Dodge Cost (base) | 10,000 stamina |
| Dodge Cost (Vishnu) | 4,500 stamina |
| Dodge Speed | 35 units/s |
| Dodge Cooldown | 2.0s |
| Shiva Damage Multiplier | 1.2x (passive) |
| Third Eye Damage Multiplier | 1.5-2.0x (while active) |
| Charged Shot Multiplier | 1.5x |
| Vishnu Speed Boost | 30% (1.3x) |
| Brahma Willpower Regen | 1.25x |
| Brahma Armor Bonus | +4 |
| Brahma Speed Penalty | -25 |
| Shield Duration | 10 seconds |
| Astra Cost | 4 focus segments (100 focus) |
| Bot Melee Rate (vs human) | 1.8s |
| Bot Melee Rate (vs bot) | 0.9s |
| Bot Spell Rate | 10-15s |
| Bot Target Switch | 5-10s |
| Bot Shield Trigger | 2,500 damage spike |
| Movement Speed Scaling | moveSpeed * 0.014f |
| Projectile Speed (typical) | 30-50 units/s |
| Projectile Radius | 0.5-2.0 units |
| Spell AoE Radius (typical) | 20-40 units |
| Spell Cone Angle (typical) | 60-180 degrees |
| Zone Tick Interval | 0.5-2.0s |

## 4.3 State Machine Quick Reference

**Can Bot Act?**
- Idle -> YES (any action)
- Melee/Melee_Second -> NO (wait for animation)
- Cast_Spell -> NO (wait for cast)
- Stun -> NO (wait for recovery)
- Dodge -> NO (wait for movement)
- Death -> NO (respawn)
- All others -> Check IsBlockingInput()

**Can Bot Cast Spell?**
- AllowSpellCasting() must return true
- Not muted (no EFFECT_ETHERMUTE)
- Not in: Cast_Spell, Spell_Anticipate, Melee, Melee_Second
- Has enough focus segments

**Can Bot Dodge?**
- Has enough stamina
- Not dead
- Not already dodging
- Most states can be cancelled into dodge

## 4.4 Research Sources

- Game AI Pro Chapter 10: Building Utility Decisions into Your Existing Behavior Tree (Bill Merrill)
- GDC 2025: Streamlining Bot Development in For Honor (Ubisoft Montreal)
- Guerrilla Games: Hierarchically-Layered Multiplayer Bot System (Killzone 2)
- Personality Parameters: Flexibly and Extensibly Providing a Variety of AI Opponents (Game Developer)
- AI Blackboard Architecture for Tactical Game AI
- Squad Coordination in Days Gone (Game AI Pro Online Edition 2021)
- Building the AI of F.E.A.R. with Goal-Oriented Action Planning
- Dave Mark GDC 2013: Architecture Tricks for Managing Behaviors
- Adaptive AI for Fighting Games (Stanford CS229)
- Human-like Bots for Tactical Shooters (arXiv 2501.00078)
- Difficulty Scaling of Game AI (ResearchGate)

---

*Document version: 1.0 -- April 5, 2026*
*Compiled from server/client codebase analysis of AUM-Unity-Staging-Legacy and AUM-Unity-Server-Legacy*
*For use with NotebookLM and AI research tools*
