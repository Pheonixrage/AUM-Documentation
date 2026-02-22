# AUM Technology Stack Decisions

**Date:** February 22, 2026
**Context:** June 2026 global launch — iOS + Android + Windows

---

## Decision Record Format

Each decision includes: **Context** (why), **Decision** (what), **Alternatives** (what else), **Rationale** (why this one).

---

## 1. Game Engine — Unity 2022.3 LTS

| | |
|---|---|
| **Context** | Need cross-platform (iOS, Android, Windows) with mature multiplayer support |
| **Decision** | Unity 2022.3 LTS (already in use) |
| **Alternatives** | Unity 6 (too new, migration risk), Unreal (C++ slower iteration), Godot (less mobile tooling) |
| **Rationale** | LTS stability, existing codebase, cross-platform builds proven in production |

---

## 2. Backend — Nakama (Self-Hosted)

| | |
|---|---|
| **Context** | Need auth, economy, matchmaking, social, leaderboards — previously on PlayFab |
| **Decision** | Nakama 3.x self-hosted on Hetzner with Go runtime |
| **Alternatives** | PlayFab (being removed — vendor lock-in, pricing), Firebase RTDB (not designed for game loops), custom backend (build time) |
| **Rationale** | Open source, Go performance, built-in matchmaking/social/leaderboards, no vendor lock-in, self-hosted control |

---

## 3. Database — PostgreSQL 16

| | |
|---|---|
| **Context** | Nakama requires PostgreSQL; need to store player data, economy, karma state |
| **Decision** | PostgreSQL 16 via Nakama's Docker Compose |
| **Alternatives** | CockroachDB (distributed SQL — overkill at 5K CCU), MongoDB (Nakama doesn't support) |
| **Rationale** | Nakama's native database, ACID transactions for economy, proven at scale, read replicas when needed |

---

## 4. Networking — LiteNetLib (UDP)

| | |
|---|---|
| **Context** | Fighting game needs low-latency, tick-based networking at 60Hz |
| **Decision** | LiteNetLib 1.3.1 (already in use) |
| **Alternatives** | Unity Netcode for GameObjects (higher latency, less control), Photon (vendor lock-in, cost), ENet (less C# support) |
| **Rationale** | Direct UDP control, reliable/unreliable channels, proven in AUM production, no per-CCU cost |

---

## 5. Hosting — Hetzner Cloud VPS

| | |
|---|---|
| **Context** | Need affordable, performant game server hosting in Asia-Pacific |
| **Decision** | Hetzner VPS (Singapore for dev/staging, Helsinki for production) |
| **Alternatives** | AWS GameLift (expensive, complex), GCP (similar cost), DigitalOcean (no Singapore) |
| **Rationale** | Best price/performance ratio, Singapore location for Asia-Pacific, simple VPS model, existing relationship |

---

## 6. CI/CD — GameCI + GitHub Actions

| | |
|---|---|
| **Context** | Need automated builds for 3 platforms + headless server, free/low-cost |
| **Decision** | GameCI (open source) on GitHub Actions |
| **Alternatives** | Unity Cloud Build (per-seat cost, limited), CircleCI (paid macOS), Jenkins (complex self-hosted) |
| **Rationale** | Free, open-source (MIT), purpose-built for Unity, 1000+ teams using it, integrates with existing GitHub repos |

---

## 7. Analytics — Metabase + Prometheus + Grafana

| | |
|---|---|
| **Context** | Need BI dashboards for game metrics and real-time server monitoring |
| **Decision** | Metabase for BI, Prometheus + Grafana for monitoring |
| **Alternatives** | Unity Analytics (limited), Mixpanel (expensive at scale), GameAnalytics (already scaffolded, limited BI) |
| **Rationale** | All open source, Docker deployable alongside Nakama, Metabase queries PostgreSQL directly, Grafana industry standard |

---

## 8. Modular Architecture — ASMDEFs + IGameMode + ScriptableObjects

| | |
|---|---|
| **Context** | Need to add game modes (co-op, dungeon, survival) without touching core code |
| **Decision** | Assembly Definitions for module isolation + IGameMode interface + GameModeDefinition ScriptableObjects |
| **Alternatives** | Monolithic (current — blocks parallel work), Unity ECS (too different from existing MonoBehaviour code), Addressable scenes only (not enough isolation) |
| **Rationale** | Builds on existing ICombatAuthority pattern, ~2s recompile per module vs 15-30s, enables parallel prototyping, MMORPG-style expansion model |

---

## 9. Content Delivery — Unity Addressables

| | |
|---|---|
| **Context** | Need to ship new content (modes, maps, cosmetics) without full app updates |
| **Decision** | Unity Addressables with per-mode asset groups |
| **Alternatives** | Asset Bundles (legacy, less feature-rich), Custom CDN (build everything from scratch) |
| **Rationale** | Official Unity solution, supports remote CDN hosting, per-group patching, platform variants, already used in production Unity games |

---

## 10. Balance System — ScriptableObjects + Nakama Remote Config

| | |
|---|---|
| **Context** | Currently combat values are hardcoded constants — balance patches require code changes |
| **Decision** | ScriptableObject configs as local defaults + Nakama remote_config for live overrides |
| **Alternatives** | JSON files (less Unity-integrated), Nakama-only (no offline defaults), Code constants (current — inflexible) |
| **Rationale** | SO = editor-friendly tuning, remote config = hot patches without app update, existing `NakamaRemoteConfig.cs` partially implements this |

---

## 11. Authentication — Google OAuth → Firebase → Nakama

| | |
|---|---|
| **Context** | Need secure authentication that works across platforms |
| **Decision** | Google OAuth (step 1) → Firebase Auth (token) → Nakama AuthenticateCustom (session) |
| **Alternatives** | Direct Nakama auth (limited social login), Firebase only (no game backend), Apple only (Android exclusion) |
| **Rationale** | Google covers most users, Firebase handles token management, Nakama gets custom token for session — already implemented and working |

---

## 12. Crash Reporting — Firebase Crashlytics

| | |
|---|---|
| **Context** | Need mobile crash reporting with stack traces and device info |
| **Decision** | Firebase Crashlytics (already integrated) |
| **Alternatives** | Sentry (also integrated — for server-side), BugSnag (paid), Unity Cloud Diagnostics (limited) |
| **Rationale** | Free, excellent mobile coverage, real-time alerts, already set up |

---

## 13. Blockchain (Future) — ChainSafe Web3.unity + Polygon

| | |
|---|---|
| **Context** | Founder wants blockchain readiness for cosmetic NFTs and game economy |
| **Decision** | Data layer preparation now; ChainSafe Web3.unity + Polygon when designed |
| **Alternatives** | Solana (faster but less Unity tooling), Ethereum L1 (gas too expensive for gaming), Immutable X (NFT-focused but less flexible) |
| **Rationale** | ChainSafe is MIT licensed and Unity-native, Polygon has low gas fees ideal for gaming, no code at launch — just future-proof data types |

---

## 14. VR/AR (Future) — OpenXR + Unity XR Interaction Toolkit

| | |
|---|---|
| **Context** | Founder's long-term vision includes VR combat modes |
| **Decision** | No VR code at launch; architecture already supports it via UnifiedInputProvider |
| **Alternatives** | Build VR now (premature), Oculus SDK only (platform lock-in), Custom XR (reinventing wheel) |
| **Rationale** | OpenXR is the industry standard, Unity XR Toolkit builds on it, adding XR = new input provider + new game mode ASMDEF — no combat code changes |

---

## 15. Localization — Unity Localization Package

| | |
|---|---|
| **Context** | Global launch requires multi-language support |
| **Decision** | Unity Localization package with string tables |
| **Alternatives** | I2 Localization (third-party, paid), Custom system (maintenance burden), Phrase/Lokalise (SaaS cost) |
| **Rationale** | Official Unity solution, free, integrates with TextMeshPro, supports asset localization (not just strings), AI-assisted translation tools available |

---

## Stack Summary

| Layer | Technology | License | Cost |
|-------|-----------|---------|------|
| Engine | Unity 2022.3 LTS | Unity License | Per-seat |
| Backend | Nakama 3.x (Go) | Apache 2.0 | Free (self-hosted) |
| Database | PostgreSQL 16 | PostgreSQL License | Free |
| Networking | LiteNetLib 1.3.1 | MIT | Free |
| Hosting | Hetzner Cloud VPS | N/A | ~$40-80/mo |
| CI/CD | GameCI + GitHub Actions | MIT + GitHub TOS | Free tier |
| Analytics | Metabase | AGPL-3.0 | Free |
| Monitoring | Prometheus + Grafana | Apache 2.0 | Free |
| Crash Reporting | Firebase Crashlytics | Google TOS | Free |
| Content | Unity Addressables | Unity License | Free |
| Auth | Firebase Auth | Google TOS | Free tier |
| Localization | Unity Localization | Unity License | Free |

**Total recurring cost:** ~$40-80/month (hosting only) at launch scale

---

*All decisions reversible. No vendor lock-in on critical path.*
*Updated: February 22, 2026*
