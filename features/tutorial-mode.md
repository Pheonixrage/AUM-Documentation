# Tutorial Mode

## Overview

Offline tutorial system using `LocalAuthority` instead of `ServerAuthority`. Key difference: no server validation, player actions always succeed.

## Architecture

### Authority Difference

| Aspect | LocalAuthority (Tutorial) | ServerAuthority (Multiplayer) |
|--------|---------------------------|-------------------------------|
| Validation | None | Server validates all |
| Stamina | Bypassed in ControllerBase | Strictly enforced |
| State Sync | Local only | Server reconciles |
| Network | Not required | Required |

## Key Components

### TutorialManager
`Assets/Scripts/CombatAuthority/Tutorial/TutorialManager.cs`
- Manages tutorial flow
- Listens for quest events
- Calls `ResetPlayer()` on quest start

### LocalTutorialBotAI
`Assets/Scripts/CombatAuthority/Tutorial/LocalTutorialBotAI.cs`
- Simple AI for tutorial opponents
- Controlled behavior for teaching mechanics

### QuestIntegration
`Assets/Scripts/CombatAuthority/Integration/QuestIntegration.cs`
- Bridge between quest system and combat authority
- `NotifyQuestStarted(questId)` triggers player reset

## Quest System Integration

### QuestFace.cs Pattern
```csharp
// In QuestFace.BeginQuest()
protected void BeginQuest() {
    // Auto-notify to reset player stats
    QuestIntegration.NotifyQuestStarted(this.ID);
    // Continue with quest logic...
}
```

### Why ResetPlayer Matters
In multiplayer, server constantly sends fresh state → stamina resets automatically.
In tutorial, no server → must manually reset or player depletes stamina permanently.

## The Stamina Bug (Fixed 2026-01-05)

### Symptom
Player could dodge once, then never again in tutorial.

### Root Cause
- 28 of 32 quests didn't call `QuestIntegration.NotifyQuestStarted()`
- Without notification, `TutorialManager.OnQuestStarted()` never fired
- `ResetPlayer()` never called → stamina stayed at 0 after first use

### Log Evidence
```
ConsumeStamina SUCCESS | Before: 100 | After: 30   ← First dodge
TriggerDodge - Ability NOT ALLOWED in state: Idle   ← All subsequent blocked
```

### Fixes Applied
1. **ControllerBase.cs:352-360** - Bypass stamina check in tutorial (safety net)
2. **QuestFace.cs:31,137** - Auto-call `NotifyQuestStarted()` (root fix)

## Tutorial Quests

Located in `Assets/QuestSystem/Quests/`:

| Quest | Purpose |
|-------|---------|
| Tutorial1-6 | Basic mechanics |
| TutorialFocus | Focus/streak system |
| TutorialStaminabar | Resource management |
| TutorialElemental* | Elemental system |
| TutorialKillTheBot* | Combat practice |
| TutorialCastAstra | Ultimate abilities |
| FinalDialogue | Completion |

## Testing Tutorial Mode

1. Start game in Tutorial mode (not online)
2. Verify `LocalAuthority` is created (check logs)
3. Test stamina-consuming actions work repeatedly
4. Complete full quest chain

## Debugging Tips

### Check Authority Type
```csharp
Debug.Log($"Authority: {player.combatAuthority.GetType().Name}");
// Should be "LocalAuthority" in tutorial
```

### Force Reset (Debug)
If stuck, can manually call:
```csharp
TutorialManager.Instance.ResetPlayerForQuest();
```

## Key Files

| File | Purpose |
|------|---------|
| `CombatAuthority/Tutorial/TutorialManager.cs` | Tutorial controller |
| `CombatAuthority/Tutorial/LocalTutorialBotAI.cs` | Bot AI |
| `CombatAuthority/Authorities/LocalAuthority.cs` | No-validation authority |
| `CombatAuthority/Integration/QuestIntegration.cs` | Quest bridge |
| `QuestSystem/QuestFace.cs` | Base quest class |
