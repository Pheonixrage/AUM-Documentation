# AUM Technical Research Findings

**Date:** February 22, 2026
**Role:** Technical Co-Founder Research (no game design invention)
**Scope:** Architecture, infrastructure, tooling, scaling, and best practices

---

## 1. Modular Game Mode Architecture

### Research Question
How can AUM add new game modes (co-op, dungeon, raid, survival, open world) without touching core code, enabling parallel prototyping?

### Findings

**Unity ScriptableObject Architecture (Official)**
- Unity's recommended approach for modular, data-driven systems
- ScriptableObjects as configuration containers enable editor-driven mode creation
- No recompilation needed for parameter changes
- Source: [Unity Official — Create Modular Game Architecture with ScriptableObjects](https://unity.com/resources/create-modular-game-architecture-scriptableobjects-unity-6)

**Assembly Definitions (ASMDEFs)**
- Split compilation units for module isolation
- Change in one ASMDEF only recompiles that module (~2s vs 15-30s full)
- Enforces dependency direction (modules can't accidentally import each other)
- Source: [Unity Manual — Assembly Definitions](https://docs.unity3d.com/2020.1/Documentation/Manual/ScriptCompilationAssemblyDefinitionFiles.html)

**MMORPG Module Patterns**
- GW2 uses event-driven architecture where content modules register handlers
- FFXIV uses instanced content that loads/unloads independently
- Atavism engine provides modular MMORPG toolkit with plugin architecture
- Source: [Atavism Online — Modular MMORPG Architecture](https://atavismonline.com/)
- Source: [Unity MMORPG KIT — Extension Plugin System](https://github.com/suriyun-production/Unity-MMORPG-KIT-Extensions-And-Plugins)

**Reusable Unity Packages**
- Git-based package distribution for cross-project code sharing
- `AUM.Core`, `AUM.Backend`, `AUM.Input` as reusable packages for future games
- Source: [FreeCodeCamp — Build Reusable Modular Unity Packages](https://www.freecodecamp.org/news/build-reusable-modular-unity-packages-to-speed-up-development/)

### Recommendation
Plugin-based game mode system using IGameMode + GameModeDefinition (SO) + GameModeRegistry + per-mode ASMDEFs. Directly extends AUM's existing ICombatAuthority pattern to entire game modes.

---

## 2. Nakama Match Handler Architecture

### Research Question
How should per-mode server logic be structured in Nakama?

### Findings

**Nakama Authoritative Multiplayer**
- Match handlers implement `MatchInit`, `MatchLoop`, `MatchTerminate`
- Each handler is a self-contained match type with its own logic
- Client specifies handler name when creating/joining matches
- Server registers multiple handlers in `main.go`
- Source: [Heroic Labs — Match Handler API](https://heroiclabs.com/docs/nakama/server-framework/typescript-runtime/function-reference/match-handler/)
- Source: [Heroic Labs — Authoritative Multiplayer](https://heroiclabs.com/docs/nakama/concepts/multiplayer/authoritative/)

**Current AUM Implementation**
- 34+ Go RPCs in `nakama-server/main.go`
- Single match handler for all modes currently
- Extending to per-mode handlers is straightforward

### Recommendation
One Go file per game mode in `nakama-server/handlers/`. Client's `GameModeDefinition.nakamaMatchHandler` routes to correct handler. Adding a mode = adding a new handler file + registering in `main.go`.

---

## 3. Content Delivery & Addressable Assets

### Research Question
How to ship new content (modes, maps, cosmetics) without full app updates?

### Findings

**Unity Addressable Asset System**
- Asset groups load on-demand from local storage or remote CDN
- Per-mode asset groups enable DLC-style expansion delivery
- Patches update individual groups without full app reinstall
- Supports asset variant system for platform-specific content
- Source: [Wayline — Unity Addressables System Complete Guide](https://www.wayline.io/blog/unity-addressables-system-complete-guide)

**Remote Balance Updates**
- AUM already has `ContentVersionManager.cs` and `NakamaRemoteConfig.cs`
- Pattern: Load local SO defaults → fetch Nakama remote_config → override diffs
- Enables balance patches without app updates

### Recommendation
Addressable groups per game mode. Core group (~50MB) always loaded. Mode-specific groups downloaded on first play. Balance data via Nakama remote config for hot patches.

---

## 4. CI/CD for Unity Projects

### Research Question
What's the best free/low-cost CI/CD solution for Unity game builds?

### Findings

**GameCI (Free, Open Source, MIT License)**
- Purpose-built for Unity CI/CD on GitHub Actions
- Handles Unity license activation in CI environment
- Supports multi-platform builds (iOS, Android, Windows, Linux, macOS)
- Used by 1,000+ teams
- Integrates with GitHub Actions (free for public repos, 2,000 min/month for private)
- Source: [GameCI Documentation](https://game.ci/docs/gitlab/getting-started/)

**Alternatives Considered**
- CircleCI Unity: Works but requires paid plan for macOS builds
  - Source: [CircleCI Unity Guide](https://circleci.com/blog/cicd-for-unity-projects/)
- Jenkins: Self-hosted, free, but complex setup and maintenance
- Unity Cloud Build: Unity's solution, costs per-seat, limited customization

### Recommendation
GameCI + GitHub Actions. Free, open-source, well-documented, and directly integrates with AUM's existing GitHub workflow. iOS builds need macOS runner (self-hosted or GitHub paid).

---

## 5. Analytics & Monitoring (Open Source)

### Research Question
How to monitor server health, track game metrics, and build dashboards without vendor lock-in?

### Findings

**Metabase (Open Source BI)**
- SQL-based dashboarding, connects directly to PostgreSQL
- Can query Nakama's PostgreSQL for player data, match results, economy metrics
- Docker deployment, zero configuration for basic setup
- Source: [Metabase](https://www.metabase.com/)

**Prometheus + Grafana**
- Prometheus: Time-series metrics collection (CCU, match duration, server load)
- Grafana: Dashboards + alerting (Slack/Discord notifications on anomalies)
- Industry standard for real-time monitoring
- Source: [Prometheus](https://prometheus.io/)

**ELK Stack (Elasticsearch + Logstash + Kibana)**
- Centralized log aggregation and search
- Useful for searching across multiple game server instances
- Heavier resource footprint than Prometheus

### Recommendation
Start with Metabase (BI) + Prometheus + Grafana (monitoring). All deploy as Docker containers alongside Nakama. ELK is optional, add later if log search becomes critical.

---

## 6. Networking & Authority Patterns

### Research Question
How do other fighting games and competitive multiplayer games handle authority?

### Findings

**Unity Distributed Authority (New)**
- Unity's built-in distributed authority model for Netcode for GameObjects
- Allows dynamic ownership transfer between clients and server
- Not suitable for AUM — fighting games need single server authority
- Source: [Unity Distributed Authority](https://unity.com/products/distributed-authority)

**Network Topologies**
- Client-server (AUM's pattern): Best for competitive integrity
- Peer-to-peer: Lower latency but vulnerable to cheating
- Distributed: Good for co-op but complex for combat validation
- Source: [Netcode Network Topologies](https://docs.unity3d.com/Packages/com.unity.netcode.gameobjects@2.5/manual/terms-concepts/network-topologies.html)

**AUM's Current Architecture**
- LiteNetLib at 60Hz tick rate — already optimal for fighting games
- ICombatAuthority with 3 implementations — extensible for new modes
- Client prediction + server reconciliation — industry standard pattern

### Recommendation
AUM's current authority architecture is already well-designed. New game modes create new authority implementations as needed. No architectural change required — just extension points.

---

## 7. Scaling Architecture

### Research Question
How to scale from 1K to 5K to 50K CCU?

### Findings

**Monolith vs Microservices in Gaming**
- For <10K CCU, monolith (single server type) is simpler and faster to iterate
- Microservices add complexity — appropriate at 50K+ CCU
- Nakama itself is designed to handle 5K+ sessions per instance
- Source: [Ascendion — Monoliths vs Microservices in Gaming](https://ascendion.com/insights/monoliths-vs-microservices-in-gaming-architecture-striking-the-right-balance/)

**Authoritative MMO Data Models**
- Server-authoritative validation is mandatory for competitive games
- Horizontal scaling: multiple game server instances behind matchmaker
- Database: Read replicas for analytics, primary for writes
- Source: [HackerNoon — Authoritative MMO Data Models](https://hackernoon.com/authoritative-mmo-data-models-5dc4c1aa30fa)

**AUM's Scale Plan**
- Phase 1: 1 Nakama + 4 Game Servers (Singapore) → 1K CCU
- Phase 2: 2 Nakama + 8 Game Servers (SG + EU) → 5K CCU
- Phase 3: K8s cluster with auto-scaling → 50K+ CCU

### Recommendation
Stay monolith until 10K CCU. Nakama handles matchmaking/social, game servers handle combat. Horizontal scaling by adding more game server instances. PostgreSQL read replicas for analytics queries.

---

## 8. Blockchain Readiness

### Research Question
What's the minimal infrastructure to be blockchain-ready without committing to implementation?

### Findings

**ChainSafe Web3.unity (MIT License)**
- Free, open-source Unity SDK for blockchain integration
- Supports Ethereum, Polygon, and other EVM chains
- Polygon recommended for low gas fees (gaming use case)
- Source: [ChainSafe Web3.unity Documentation](https://docs.gaming.chainsafe.io/)

**Phase 1 Approach (Data Layer Only)**
- Use UUIDs for all item IDs (blockchain-compatible)
- Currency amounts support decimal precision
- Ownership records include optional `blockchain_ref` field
- No blockchain code at launch — data structures are future-proof

### Recommendation
No blockchain code for June 2026. Ensure data types are compatible (UUIDs, decimal currencies, optional blockchain reference fields). Implement Web3.unity when the founder designs the blockchain experience.

---

## 9. VR/AR Readiness

### Research Question
What's needed to support VR/AR in the future without changing combat code?

### Findings

**OpenXR 1.1 Standard**
- Industry standard for cross-platform XR development
- Unity XR Interaction Toolkit builds on OpenXR
- Source: [Unity XR Plugin Architecture](https://docs.unity3d.com/Manual/XRPluginArchitecture.html)
- Source: [XR/VR Development Guide 2026](https://theatlyx.com/blog/xr-vr-development-in-2026-the-complete-guide-to-trends-workflow-enterprise-adoption/)

**AUM's Current Architecture**
- `UnifiedInputProvider` already abstracts touch/keyboard/gamepad
- Adding XR input = new provider implementation
- `IGameMode` can specify input provider type per mode
- No combat code changes required

### Recommendation
No VR code for June 2026. Architecture already supports it — `UnifiedInputProvider` is the extension point. When VR mode is designed, create new `XRInputProvider` and `VRGameMode` ASMDEF.

---

## 10. Localization

### Research Question
What's the best approach for multi-language support in Unity?

### Findings

**Unity Localization Package**
- Official Unity package for string tables, asset localization
- Supports 100+ languages with pseudo-localization for testing
- Integration with TextMeshPro for font fallbacks
- AI-assisted translation tools (Phrase, LinguaForge) reduce manual translation effort

### Recommendation
Install Unity Localization package. Create string table directory. Build `AUMLocalizationManager.cs` for runtime language switching. Content and language selection is founder's domain.

---

## 11. Accessibility

### Research Question
What accessibility features are standard for competitive fighting games?

### Findings

**Street Fighter 6 Accessibility (Industry Benchmark)**
- Colorblind modes (Deuteranopia, Protanopia, Tritanopia)
- Adjustable text size
- Audio cues for visual effects
- Input remapping
- Single-hand play support via Modern Controls
- Proved accessibility doesn't reduce competitive integrity

### Recommendation
Build `AccessibilityManager.cs` as settings hub. Implement shader-based colorblind filter. Create `AccessibilityConfig.asset` (ScriptableObject) for configuration. All feature decisions by founder.

---

*Research conducted: February 22, 2026*
*All recommendations are technical infrastructure only — no game design concepts invented*
