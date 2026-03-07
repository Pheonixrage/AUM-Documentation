# AUM Project Memory

## V2 ASMDEF Architecture (Assets/_AUM/Scripts/)
- 17 assemblies: Core, Combat, Networking, Input, Backend, Avatar, Bots, Economy, GameModes, Guna, Progression, Resources, UI, Social, Ranked, Platform, **Bridge**
- **AUM.Core is base** — NO other AUM assembly can be referenced by it
- Circular dep pattern: use `object` for cross-assembly fields, cast in consuming code
- See [asmdef-deps.md](asmdef-deps.md) for full dependency graph

## V1-V2 Bridge Architecture
- **AUM.Bridge** is `autoReferenced: true` (only V2 ASMDEF that is) — V1 Assembly-CSharp can see it
- `V1V2Bridge.cs` — static `object CombatAuthority` property, fires `OnCombatAuthoritySet` event
- `BridgeBootstrap.cs` — `[RuntimeInitializeOnLoadMethod(BeforeSceneLoad)]` subscribes to bridge events
- `V1AuthorityAdapter.cs` — reflection-based impl of V2 `AUM.ICombatAuthority` wrapping V1 authority
- **Two wiring points**: GameManager.CreateCombatAuthority() AND TutorialManager.Initialize()
- See [v2-bridge.md](v2-bridge.md) for detailed architecture

## Critical C# Gotcha: Boxed Enum Casts
- `(int)boxedEnumObject` THROWS InvalidCastException — use `Convert.ToInt32(boxedEnum)`
- Applies to ALL reflection-returned enum values

## Critical Unity Gotcha: Fake Null & ?.Operator
- Unity serialized fields (`public GameObject x`) can be "unassigned" — C# sees non-null, Unity throws `UnassignedReferenceException`
- `x?.Method()` does NOT catch this — `?.` checks C# null only
- **ALWAYS use `if (x != null)` for Unity objects** — Unity's overloaded `==` handles fake null
- Regression example: PaniMukthaController.CheckDiscus() — `leftDiscus?.SetActive()` crashed 10x/session

## Common V2 Compilation Issues
- **Duplicate types**: CombatStubs.cs and real files → CS0433
- **Missing ASMDEF refs**: unreferenced assembly → CS0246
- **Nakama GUID**: `69810832b544b46da9804f1af9373521`
- **TMPro GUID**: `6055be8ebefd69e48b49212b09b47b2f`
- **Cinemachine GUID**: `4307f53044263cf4b835bd812fc161a4`
- **LiteNetLib GUID**: `1fa0a8805029049dfa9e858d52572c02`

## Key Stub Files
- `Core/V1Stubs.cs` — 20+ V1 type stubs
- `Combat/Stubs/CombatStubs.cs` — Simulation, GameManager, PlayerManager, AUMLogger stubs
- `Input/InputEnums.cs` — ButtonType, ButtonPhase

## V2 Integration Progress (Feb 26)
- Phase 1 DONE: 16 ASMDEFs compile (Waves 1-7)
- Phase 2 DONE: Bridge live — V2 CombatBridge initializes at runtime
- Phase 3+ PENDING: Ability behaviors, HitFeel, UI, Bots, Core migration

## Debugging Tips
- MCP logs don't capture `[RuntimeInitializeOnLoadMethod]` — check Editor.log
- Editor.log accumulates — search from last `Begin MonoManager ReloadAssembly`
- Check `Library/ScriptAssemblies/AUM.*.dll` timestamps for compilation

## Important Commits
- `cfdd942a` — V2 .meta files (283 files)
- `06cb4519` — Tutorial bridge wiring + boxed enum fix
- `fa343c68` — Bridge assembly: V1AuthorityAdapter
- `93331a43` — Compilation fixes: stubs to Core
- `0d43c6fe` — V2 ASMDEF compilation fixes

## Environment
- V2 work on `v2` branch (~17 commits ahead of main)
