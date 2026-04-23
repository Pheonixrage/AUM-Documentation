---
scope: AUM-Unity-Server-Legacy + AUM-Unity-Staging-Legacy (Legacy pipeline, full game)
server_repo: /Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy
server_branch: legacy-working-oct6
client_repo: /Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy
client_branch: legacy-working-oct29
bots_live_on: server (no bot code on client)
NOT_applicable_to:
  - AUM-Headless (V2 server, has its own separate bot architecture under Assets/Scripts/Bots/Bot/)
  - AUM-The-Epic (V2 client)
  - AUM-2.0 Production/Server (still runs the old behaviour tree, read-only reference)
  - AUM-2.0 Production/Client
last_updated: 2026-04-11
---

# Bot AI — Legacy Pipeline

Everything in this folder applies to the **Legacy pipeline only** — i.e. the game that's live on the App Store / Play Store today, running on the Helsinki server (`65.109.133.129`).

Two Unity projects make up the full game and must be kept in sync:

| Role | Folder | Branch |
|---|---|---|
| Server (bots live here) | `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy` | `legacy-working-oct6` |
| Client (no bot code) | `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy` | `legacy-working-oct29` |

Bot AI runs entirely server-side. The client only sees bots as "other players" arriving via the normal UDP packet stream. Any client-side change that affects bots (shield swipe thresholds, input processing, etc.) is tracked in the legacy client's own CLAUDE.md, not here.

## What this folder is

A durable memory system for bot AI work on the Legacy pipeline. It survives context compaction because every file lives in the Obsidian vault (`AUM-Documentation`), not in a conversation. When I start a new session I read this folder first, so I never re-diagnose the same bug twice.

## Where to start reading

Read in this order:

1. **[CURRENT-STATE.md](CURRENT-STATE.md)** — what works and what's broken right now. Read first, always.
2. **[GIT-STATE.md](GIT-STATE.md)** — the commit checkpoint this doc is pinned to. Tells you what's in git vs what's still in the working tree.
3. **[BUGS-ACTIVE.md](BUGS-ACTIVE.md)** — known open bugs.
4. **[LESSONS.md](LESSONS.md)** — "we tried X and it was wrong because Y." This is the regression-prevention file. Read before proposing any change.
5. **[DECISION-LOG.md](DECISION-LOG.md)** — append-only one-liners for every decision, with links to the session files.
6. **[BUGS-FIXED.md](BUGS-FIXED.md)** — closed bugs with commit hash and evidence.
7. **sessions/** — one file per work session, newest at the top.
8. **research/** — NotebookLM answers, papers, external references.

## Rules for editing this folder

- **Never rewrite history.** `DECISION-LOG.md` and `LESSONS.md` are append-only. If a prior decision was wrong, the fix is a new entry that references the old one. Nothing gets deleted.
- **Every code reference includes the full repo path.** Not just `BotExecutor.cs:521` — write `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Assets/Scripts/Bots/Core/BotExecutor.cs:521`. `BotExecutor.cs` exists in all three pipelines; the path disambiguates.
- **Never cross-contaminate with AUM-Headless or AUM-2.0 Production.** The 3-layer architecture here was inspired by the design document in `cross-pipeline/bot-ai-design-reference-from-april-8/`, but the actual code in `AUM-Unity-Server-Legacy` and `AUM-Headless` is **separate implementations** with different file trees. A fix in one does NOT automatically apply to the other.
- **Session files cap at ~200 lines.** If a session runs longer, start a new one and link.
- **Log dumps stay in `DebugLogs/` in the repo.** Reference paths, don't copy contents.

## Log file locations (READ THIS before grepping for bot telemetry)

There are FOUR distinct log sources. I (Claude) have confused them before. **Every claim about "the bot didn't log X" must specify which source was checked.**

| # | Path | Contents | Coverage |
|---|---|---|---|
| 1 | `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/DebugLogs/server_session_YYYY-MM-DD_HH-MM-SS_port6006.log` | Filtered subset of every `Debug.Log` that matches one of `DebugLogTracker.trackedTags`. Primary diagnostic source. Per-match file. | Only tags in `trackedTags`. As of 2026-04-11, includes `[BOT:` |
| 2 | `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/Logs/{guid}-S.log` and `{guid}-C.log` | Per-match state transition dumps (JITTER / DESYNC tracking, state change events). Raw engine data, **NO bot telemetry**, useful only for state-machine desync debugging. | State transitions only |
| 3 | `~/Library/Logs/Unity/Editor.log` | Current Unity Editor session log. **Tied to whichever project Unity Hub opened LAST.** If the Editor last opened `AUM-The-Epic` or any other project, this file has nothing to do with `AUM-Unity-Server-Legacy`. Always check `head -20` for the `-projectpath` argument before using this file as evidence. | Full editor stdout, but project-scoped to whatever Unity is running |
| 4 | **Unity Editor Console (in-editor view)** | Live full `Debug.Log` stream, including tags NOT in `trackedTags`. **Only accessible via screenshot or MCP — Claude cannot read it from disk.** | Everything Unity logs at runtime |

**If `DebugLogs/*.log` doesn't have a tag you expect**, the cause is EITHER:
- The tag isn't in `DebugLogTracker.trackedTags`, OR
- The `Debug.Log` call is gated by a `verboseConsole` / `enabled` / other flag in the emitting code.

`LogSnapshot` and `LogMatchSummary` in `BotTelemetry.cs` are **unconditional** — they always print. `LogEvent`, `LogDecision`, `LogMovement` are **gated on `verboseConsole`** which `BotBrain.Start` sets to `false`. (Fix for `LogEvent` landed 2026-04-11 — removed the gate because events are low-frequency high-value.)

**Lesson from 2026-04-11 session #3:** I conflated "bot telemetry" with "LogEvent telemetry" and reported "telemetry broken" when only one of four paths was actually broken. Always enumerate WHICH telemetry method, WHICH log file, and WHICH gate before claiming a telemetry gap.

## Cross-references

- **Design reference (both implementations drew from this):** `cross-pipeline/bot-ai-design-reference-from-april-8/`
- **V2 bot work (AUM-Headless + AUM-The-Epic):** does not exist yet in the vault. When it does, it will live in `pipelines/P1-v2/AUM-Headless-plus-AUM-The-Epic-bot-ai/`.
- **AUM-2.0 Production server bots:** read-only reference. Still runs the old behaviour tree (`/Users/mac/Documents/AUM-2.0 Production/Server/Assets/Scripts/Bots/Behaviour Tree/`). Not modified, cited only for comparison.
- **Legacy server CLAUDE.md:** `/Users/mac/Documents/GitHub/AUM-Unity-Server-Legacy/CLAUDE.md` — canonical project state.
- **Legacy client CLAUDE.md:** `/Users/mac/Documents/GitHub/AUM-Unity-Staging-Legacy/CLAUDE.md` — canonical client state.
