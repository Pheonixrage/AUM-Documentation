---
kind: design-reference
last_updated: 2026-04-11
---

# Bot AI Design Reference (April 8, 2026)

Two design documents from 2026-04-08 describing a 3-layer hybrid bot architecture (Strategy → Utility Tactician → BT Executor).

## Scope — read this carefully

These documents describe a **design**, not a specific codebase. The design was used as inspiration by **two separate Unity projects**, which built their own independent implementations with different file trees:

| Unity project | Implementation path | Notes |
|---|---|---|
| `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy` (Legacy pipeline) | `Assets/Scripts/Bots/{Core,Tactics,Strategy,Styles,Personality,Humanization}/` | Branch `legacy-working-oct6`. Working state tracked in `pipelines/P3-legacy/AUM-Unity-Server-Legacy-plus-AUM-Unity-Staging-Legacy-bot-ai/` |
| `/Users/mac/Documents/GitHub/AUM-Headless` (V2 pipeline server) | `Assets/Scripts/Bots/Bot/{Core,Intelligence,Personality,Difficulty,Data}/` + `Assets/Scripts/Bots/Training/` | Branch `AUM_MIND`. No Obsidian tracking yet — create under `pipelines/P1-v2/` if/when we work on V2 bots. |

**These are two different codebases with different file names, different module structures, and different bugs.** A fix in one does NOT automatically apply to the other. The design documents here are the only thing they share.

**NOT related to these design docs:**
- `/Users/mac/Documents/AUM-2.0 Production/Server/Assets/Scripts/Bots/` — still runs the pre-April-8 pure Behaviour Tree. Read-only reference only.
- `/Users/mac/Documents/AUM-2.0 Production/Client/` and `/Users/mac/Documents/GitHub/AUM-The-Epic/` — clients have no bot code.

## Files in this folder

- [`2026-04-08-bot-ai-architecture.md`](2026-04-08-bot-ai-architecture.md) — the main design document. Research sources (Dave Mark Utility AI, For Honor GDC talks, FightingICE papers, Dark Souls AI analysis, NavMesh discussions), the 3-layer diagram, folder structure proposal, style-specific considerations.
- [`2026-04-08-bot-ai-critical-analysis.md`](2026-04-08-bot-ai-critical-analysis.md) — edge cases, performance constraints, scalability concerns, open questions. Companion to the architecture doc.

## Rules for editing

- **Treat these as design reference, not current state.** If implementation in Legacy or V2 diverges from the design, update the **implementation's Obsidian folder** (e.g. `pipelines/P3-legacy/AUM-Unity-Server-Legacy-plus-AUM-Unity-Staging-Legacy-bot-ai/CURRENT-STATE.md`), NOT these files.
- **Do not patch the design docs with legacy-specific or V2-specific fixes.** Those belong in the pipeline folders. These files describe the original 2026-04-08 design as authored; they're historical.
- **Amendments** to the design (if the architectural approach itself evolves) get a new file dated accordingly, e.g. `2026-05-01-bot-ai-architecture-revision.md`, left next to the originals. Cross-reference in both.

## Original location

These files used to live at `sessions/2026-04-08-bot-ai-architecture.md` and `sessions/2026-04-08-bot-ai-critical-analysis.md`. Breadcrumb stubs remain at those paths redirecting here.
