# AUM Project Memory

## CRITICAL: Project Confusion Warning
- **Elemental Mastery Progression work** is on `/Users/mac/Documents/AUM-2.0 Production/` (Client + Server subdirs)
- This is NOT the legacy staging repos (`AUM-Unity-Staging-Legacy` / `AUM-Unity-Server-Legacy`)
- See [project-paths.md](project-paths.md) for details

## Unity Scene File Grep Gotcha
**`grep "ClassName"` in `.unity` files returns 0 even if the component is attached.** Unity stores component references by script GUID/fileID, not class name. To check if a component is in a scene, search for its script asset GUID or check via the Editor Inspector.

## Editor Script Scenes (AUM-2.0 Production Client)
| Script | Scene to open first |
|--------|-------------------|
| `AUM > Wire SpellDetailPanel` | **MainMenu** — SpellDescriptionParent lives in GnanaMargPanel.prefab |
| `AUM > Setup 5th HUD Elemental Button` | **Map_Hell** — wires in-match HUD buttons |
| `AUM > Fix Air Tree SpellIndex` | **MainMenu** |
| `AUM > Import Elemental VFX` | any |
| `AUM > Populate Elemental Spell Configs` | any |

## Git: Stale Rebase State Cleanup
If `git status` shows "currently editing a commit while rebasing" but `git-rebase-todo` is empty and no conflicts exist, the rebase is done but the state directory wasn't cleaned up. Fix: `git rebase --quit`

## Git LFS Pre-Push Hook
Both AUM-2.0 repos have LFS pre-push hooks that block all pushes when `git-lfs` isn't installed on the Mac. The hook message itself says to delete it. Safe to remove: `rm .git/hooks/pre-push`

## Elemental Mastery Status (AUM-2.0 Production) — PHASES 1-8 COMPLETE

### Phase Summary
| Phase | What | Status |
|-------|------|--------|
| 1 | VFX prefab import editor script (6 unitypackages) | Code done, needs Unity run |
| 2 | Config population — 150 spell configs (5 elem × 10 types × 3 levels) | Code done, needs Unity run |
| 3 | SpellDetailPanel wiring, DOTween flash, levelText bug fix | Complete |
| 4 | Spell spawn pipeline — PrefabManager, SpellManager cache, CastManager loadout | Complete |
| 5 | Match HUD wiring — SpellIndex from loadout, state callbacks, ShieldManager | Complete |
| 6 | Review pass — rangeType in AVATARUPLOAD confirmed, null-guard warnings | Complete |
| 7 | UI Testing & Bug Fixes — skill tree, Air fix, controls restored | Complete |
| 8 | Runtime fixes — default loadout gen, button visibility, dupe prevention, slot unlock | Complete |
| 9 | **Full playtest PASS** — all spell types route+spawn correctly with new prefabs | **Verified Mar 4** |
| 10 | **VFX prefab loading fix** — SpellManager loads type-specific VFX (FIRE_4_0 etc.) instead of invisible _0_0 | **Fixed Mar 5** |

### Git Log (latest first)
```
9f7c272ae feat: Sadhana Main Screen UI — ornate loadout slots, unlock popup, back navigation
0639b1204 fix: Hide elemental buttons during prematch, increase mouse sensitivity, add E5 cancel
7fe8e7985 feat: Rewrite SetupFifthHUDSlot editor script with hardcoded arc positions
0382be053 fix: Use name-based lookup for ELEMENTAL5 AttackType in SpellManager
e040f5b19 fix: Move AttackType.ELEMENTAL5 to end of enum to preserve serialized values
```

### Remaining Work (Not Code — run in Unity Editor)
- **AUM > Import Elemental VFX** — imports 6 unitypackages
- **AUM > Populate Elemental Spell Configs** — creates 150 SpellConfig assets
- **AUM > Fix Air Tree SpellIndex** — fixes Air tree scene data, SAVE SCENE after (MainMenu)
- **AUM > Wire SpellDetailPanel** — already wired (confirmed Mar 7), re-run only if refs break
- **AUM > Setup 5th HUD Elemental Button** — creates EA5, positions all 5, SAVE SCENE after (Map_Hell)
- Build server on Windows + deploy to Singapore (5.223.55.127)
- Playtest end-to-end flow (in-match with server)

### Sadhana Main Screen (committed 9f7c272ae)
- **SadhanaMainScreenSetup.cs**: Editor script builds entire UI hierarchy with ornate sprites
- **SadhanaMainController.cs**: Runtime controller — slot display, unlock popup, element switching
- **SadhanaUIAnimations.cs**: DOTween animations for popup, pulse, feedback
- **Loadout slots**: 5 ornate frames (`_65` sprite), white color, 70x70 element icons, lock overlays
- **Null singleton handling**: Creates default `ElementalProgressionState` if null on Initialize
- **Back navigation**: Uses existing scene Back button (persistent ScreenController.Back listener)

## CRITICAL LESSON: Controls Architecture
**NEVER destructively modify control files. Only add elemental behavior additively.**

### PC Control Map (PCInput.cs)
| Key/Input | Action | Handler |
|-----------|--------|---------|
| LMB (cursor locked) | Melee attack | Update() — `else if (Cursor.lockState == Locked)` |
| LMB (aiming) | Cast aimed spell | Update() — aimingAbility block |
| RMB (aiming) | Cancel aiming | Update() — aimingAbility block |
| Mouse delta | Camera rotation | Update() — always active |
| 1-5 | Elemental (hold=aim, tap=quick) | HandleElementalKey() — hold-based detection |
| Q | Special ability aim | HandleKeyboardInput() |
| E | Third Eye / Shield | HandleKeyboardInput() + HandleEKeyHold() |
| R | God ability (Astra) | HandleKeyboardInput() |
| Space | Dodge / Cancel aiming | HandleKeyboardInput() |

### Elemental Type Routing (PlayerInput.cs)
| Method | Routes |
|--------|--------|
| HandleElementalTap | Shield→DefenseCast, Coating→toggle, Instant/Channel→quickcast, Charged→phase-dep, Trap→close:instant/long:reticle |
| HandleElementalHeld | Shield/Coating→none, Instant/Channel→aim, Charged→aim if ready, TrapLong→aim |
| HandleElementalRelease | Fire if in Spell_Aiming |
| HandleElementalDrag | Mobile touch aim with dead zone |
| HandleElementalEndDrag | Confirm cast from drag |

### ControllerBase.IsAbilityAllowed
- Handles UNIQUE, THIRDEYE, DODGE explicitly with stamina/focus checks
- Default `return true` — ATTACK and ELEMENTAL types pass through (validated elsewhere)
- **NEVER change default to `return false`** — blocks basic attacks

## Key Patterns
- SpellType encoding: `(int)category * 2 + (int)range` — PrefabManager.EncodeSpellType()
- Elemental bit-packing: `(element << 5 | spellType)` — Elemental.cs
- Server SpellManager uses Dictionary<int, SpellObject> on-demand cache (not flat array)
- CastManager reads ElementalLoadout.Current for type/range/level per slot
- Server/Client enum mismatch: Client WeaponCoating=0, Server INSTANT=0 — mapped in server EncodeSpellType()
- Prefab fallback chain: `{ELEM}_{type}_{level}` → `{ELEM}_{type}_0` → `{ELEM}_0_0`
- AVATARUPLOAD carries loadoutSpellTypes + loadoutRanges + loadoutLevels arrays
- **ClickCatcher safety**: SpellDetailPanel has OnDestroy/OnDisable to clean up full-screen overlay
- **VFX prefab difference**: `_0_0` = invisible entity (0 ParticleSystems), `_4_0` etc = full VFX (24+ ParticleSystems)
- **SpawnSpellEffect**: Skips pool particles (`ParticleManager.GetFromPool`) when prefab has built-in ParticleSystem VFX

## AUTODEV RULE: ALWAYS Use Emulated Clicks for Navigation (MANDATORY)
**NEVER call game methods programmatically to switch screens or navigate.** Always use emulated UI button clicks via MCP.
- Finding a button → `.GetComponent<Button>()` → `button.onClick.Invoke()` or use MCP click simulation
- This applies to ALL screen transitions, login, navigation, element selection, etc.
- Programmatic calls bypass event listeners, animations, and state management — causing desynced UI
- The ONLY exception is editor-time setup scripts (SadhanaMainScreenSetup etc.)

## UI Testing Workflow (MCP Click Simulation)

### MCP Unity Bridge Ports
| Project | Port | Unity Version |
|---------|------|---------------|
| AUM-2.0 Production Client | **6402** | Unity 6000.0.60f1 |
| AUM-2.0 Production Server | **6401** | Unity 6000.0.60f1 |

### AUTODEV RULE: ALWAYS Start Server Before Client for Combat Testing (MANDATORY)
**Start server play mode FIRST, wait for it to be ready, THEN start client.** The client needs a running server to connect to for bot/PvP matches. Server on port 6401, client on port 6402.

### AUTODEV RULE: Never Use DisplayDialog in Editor Scripts
**`EditorUtility.DisplayDialog()` blocks the Unity main thread** — MCP bridge cannot execute ANY command until user manually clicks OK.
- **NEVER write `EditorUtility.DisplayDialog`** — use `Debug.Log` / `Debug.LogError` instead.
- **Before running any editor script via MCP**, grep for `DisplayDialog` and remove first.
- If dialog blocking: use Swift CGWindowList to detect (260x352 unnamed window on PID), then try `NSRunningApplication.activate` + CGEvent Return key.

### AUTODEV RULE: ALWAYS Use ScreenCapture for Screenshots (MANDATORY)
**The MCP `/screenshot` endpoint captures a low-res thumbnail of the editor view. ALWAYS use `ScreenCapture.CaptureScreenshot` instead for proper game rendering.**

**Pattern for every screenshot:**
```csharp
// Captures ALL cameras + UI Canvas overlays at 2x resolution
UnityEngine.ScreenCapture.CaptureScreenshot("/tmp/screenshot.png", 2);
```
- Wait 1-2 seconds after capture call for file to be written
- Read the file at `/tmp/screenshot.png` to view the result
- **NEVER rely on MCP `/screenshot` endpoint** — it misses UI, is low-res, and may show wrong camera
- Use incrementing filenames (`/tmp/screen_01.png`, `/tmp/screen_02.png`) to avoid overwrite issues
- After taking screenshot, ALWAYS `Read` the file to visually inspect it

### AUTODEV RULE: ALWAYS Activate Unity BEFORE Any MCP Command (MANDATORY, NO PERMISSION NEEDED)
**Two-step focus: (1) macOS app activate, (2) Unity GameView focus. Do BOTH before EVERY MCP call. Never ask permission.**

**Step 1 — macOS activate** (run via Bash, before any curl to MCP):
```bash
open -a "/Applications/Unity/Hub/Editor/6000.0.60f1/Unity.app" && sleep 0.5
```

**Step 2 — GameView focus** (prepend to every execute_code call):
```csharp
var asm = typeof(UnityEditor.EditorWindow).Assembly;
var gvType = asm.GetType("UnityEditor.GameView");
var gv = UnityEditor.EditorWindow.GetWindow(gvType);
gv.maximized = true; gv.Focus();
```

**Combined pattern for every MCP call:**
```bash
# Step 1: macOS activate
open -a "/Applications/Unity/Hub/Editor/6000.0.60f1/Unity.app" && sleep 0.5
# Step 2: MCP call with GameView focus prepended
curl -s -X POST http://localhost:6402/execute -H 'Content-Type: application/json' -d '{"code":"<focus gate + actual code>"}'
```
- After scene switches, play mode changes, recompiles: ALWAYS re-activate + re-focus
- **Never skip this. Never ask user.** Just do it every single time.

### Boot Sequence
1. Enter play mode
2. **Focus + Maximize Game View** (REQUIRED — otherwise clicks don't register):
   ```csharp
   var asm = typeof(UnityEditor.EditorWindow).Assembly;
   var gvType = asm.GetType("UnityEditor.GameView");
   var gv = UnityEditor.EditorWindow.GetWindow(gvType);
   gv.maximized = true; gv.Focus();
   ```
3. Skip cinematic: `GameObject.Find("CinematicScreen").GetComponent<CinematicScreen>().SkipCinematic()`
4. Click `LoginButton` to log in (was `GoogleSignIn_Btn` in legacy)
5. Navigate: `Gnana` → `SadhanaButton` → element wheel → `ElementBttn`

### Element Selection
- Use `rotator.SelectElementalNoLerp(rotator.GetSpellIndex(element))` then click `ElementBttn`
- Fire=AGNI, Water=JALA, Air=VAYU, Ether=AKASHA, Earth=PRITHVI

## Legacy Migration Status (Mar 3, 2026)

### Pipeline
- **Data:** 139 players, 288 avatars → `LegacyMigration_0..9` chunks in Title Internal Data
- **Client:** `PlayFabDataBridge.CheckLegacyMigration()` → fires every login, sends email to CloudScript
- **CloudScript:** `claimLegacyAccount` — fast returns via LegacyMigrated/LegacyChecked flags
- **Commit:** `3325f610a` on `legacy-working-oct29` (2.0 Production Client)
- **Remote:** `https://github.com/Pheonixrage/Unity-Origin.git` (updated from Unity6-Legacy)

### Deployment Status
| Env | Chunks | CloudScript | Client |
|-----|--------|-------------|--------|
| DEV (15F2B7) | Uploaded | Rev 138 | Needs build |
| PROD (158C02) | Pending | Pending | Needs build |

### PROD Deployment Steps
1. `python3 upload_to_playfab.py --env prod` (migration chunks)
2. Deploy CloudScript to PROD title
3. Remove `#if UNITY_EDITOR` test email override
4. Build + release new client

### Key Details
- **Karma:** BASELINE=1 (migration), BASELINE=33 (live). Per-avatar sattva/rajas/tamas/guna.
- **Names:** AN_ key format. Legacy player keeps name, new player gets `_2` suffix.
- **Merge:** Existing players get legacy avatars appended (dedup by uniqueID), Math.max currencies.
- **Flags:** `LegacyMigrated` (restored), `LegacyChecked` (scanned, even if no data).

### Known Issue: Match Connection (Deferred)
- PvP ID FIX incorrectly remaps localPlayerID when bot CREATECHAR arrives first
- PREGAME stuck at 15s in real PvP matches
- Investigated, fixes prototyped but reverted — pre-existing, unrelated to migration

## Sadhana UI Design & Implementation
- **Full design doc:** [sadhana-ui-design.md](sadhana-ui-design.md) — FTUE flow, visual specs, sprite assets, code state
- **Autodev workflow:** [autodev-mcp-workflow.md](autodev-mcp-workflow.md) — MCP rules, timings, compile cycles, null patterns
- **PureRef designs:** `/Users/mac/Desktop/PureRef_SkillTree_Flows/individual_images/` (212 images)
- **12 files created** (~4500+ lines) — all working, editor scripts run from MainMenu scene
- **CRITICAL:** Never create plain boxes. Use existing sprites. Always inspect old UI properties fully (color, material, preserveAspect, size).
- **Remaining:** Training flow, upgrade flow, equip/unequip wiring to skill tree, scene save

## Environment
- VFX RAR: `/Users/mac/Downloads/prefabs/` (6 unitypackages)
- Design doc: memory/design-doc-spells.md
- PureRef designs: `/Users/mac/Desktop/PureRef_SkillTree_Flows/individual_images/` (212 images)
