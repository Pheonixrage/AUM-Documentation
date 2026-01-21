# AUM Protocol Documentation: PlayFab Integration

**Version:** 1.0
**Last Updated:** January 21, 2026
**Protocol Layer:** HTTPS (PlayFab REST API)
**Repo:** `AUM-Unity-Staging-Legacy`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Service Inventory](#3-service-inventory)
4. [PlayFabManager](#4-playfabmanager)
5. [PlayFabDataBridge](#5-playfabdatabridge)
6. [PlayFabPlayerData](#6-playfabplayerdata)
7. [PlayFabMatchmaker](#7-playfabmatchmaker)
8. [PlayFabLeaderboard](#8-playfableaderboard)
9. [PlayFabCurrencyService](#9-playfabcurrencyservice)
10. [PlayFabAvatarCurrencyService](#10-playfabavatarcurrencyservice)
11. [PlayFabKarmaManager](#11-playfabkarmamanager)
12. [PlayFabStoreService](#12-playfabstoreservice)
13. [PlayFabInventoryService](#13-playfabinventoryservice)
14. [PlayFabItemMapper](#14-playfabitemmapper)
15. [PlayFabItemData](#15-playfabitemdata)
16. [PlayFabOpenIdAuth](#16-playfabopenidauth)
17. [Data Classes](#17-data-classes)
18. [CloudScript Functions](#18-cloudscript-functions)
19. [Currency System](#19-currency-system)
20. [Error Handling](#20-error-handling)

---

## 1. Overview

PlayFab serves as the backend-as-a-service (BaaS) for AUM, handling:

- **Authentication** - OpenID Connect via Firebase
- **Player Data** - Stats, avatars, settings, progress
- **Currency** - 8 virtual currencies (per-avatar)
- **Inventory** - Items, equipment, purchases
- **Matchmaking** - Queue-based with bot fallback
- **Leaderboards** - Rating, wins, kills
- **CloudScript** - Server-authoritative game logic

### Connection Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PlayFab Integration Flow                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Firebase Auth          PlayFab API            Game Client                  │
│       │                      │                      │                        │
│       │  1. ID Token         │                      │                        │
│       │ ─────────────────────┼──────────────────────>                        │
│       │                      │                      │                        │
│       │                      │  2. OpenID Login     │                        │
│       │                      │ <────────────────────│                        │
│       │                      │                      │                        │
│       │                      │  3. Session Token    │                        │
│       │                      │ ────────────────────>│                        │
│       │                      │                      │                        │
│       │                      │  4. Load Player Data │                        │
│       │                      │ <────────────────────│                        │
│       │                      │                      │                        │
│       │                      │  5. Avatars/Stats    │                        │
│       │                      │ ────────────────────>│                        │
│       │                      │                      │                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture

### Service Hierarchy

```
PlayFabManager (Orchestrator)
├── AUMAuthManager (Authentication)
│   └── PlayFabOpenIdAuth (Firebase → PlayFab)
├── PlayFabDataBridge (Unified Data Manager)
│   ├── Avatars
│   ├── PlayerStats
│   ├── Settings
│   ├── Progress
│   └── Currencies
├── PlayFabPlayerData (Legacy Data Handler)
├── PlayFabMatchmaker (Queue + Bot Fallback)
├── PlayFabLeaderboard (Statistics)
├── PlayFabCurrencyService (Conversion)
├── PlayFabAvatarCurrencyService (Per-Avatar)
├── PlayFabKarmaManager (Lives/Guna/Hell)
├── PlayFabStoreService (Catalog)
├── PlayFabInventoryService (Items)
└── PlayFabItemMapper (Item Encoding)
```

### Singleton Pattern

All services use Unity singleton pattern:

```csharp
public static ServiceName Instance { get; private set; }

private void Awake()
{
    if (Instance == null)
    {
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
    else
    {
        Destroy(gameObject);
    }
}
```

---

## 3. Service Inventory

| Service | File | Lines | Purpose |
|---------|------|-------|---------|
| PlayFabManager | `PlayFabManager.cs` | 304 | Main orchestrator |
| PlayFabDataBridge | `PlayFabDataBridge.cs` | 1961 | Unified data management |
| PlayFabPlayerData | `PlayFabPlayerData.cs` | 525 | Legacy player data |
| PlayFabMatchmaker | `PlayFabMatchmaker.cs` | 921 | Matchmaking with bot fallback |
| PlayFabLeaderboard | `PlayFabLeaderboard.cs` | 249 | Leaderboard operations |
| PlayFabCurrencyService | `PlayFabCurrencyService.cs` | 257 | Currency conversion |
| PlayFabAvatarCurrencyService | `PlayFabAvatarCurrencyService.cs` | 747 | Per-avatar currencies |
| PlayFabKarmaManager | `PlayFabKarmaManager.cs` | 706 | Karma/Guna/Hell system |
| PlayFabStoreService | `PlayFabStoreService.cs` | 428 | Catalog management |
| PlayFabInventoryService | `PlayFabInventoryService.cs` | 554 | Inventory management |
| PlayFabItemMapper | `PlayFabItemMapper.cs` | 259 | Item code encoding |
| PlayFabItemData | `PlayFabItemData.cs` | 218 | Item data class |
| PlayFabOpenIdAuth | `PlayFabOpenIdAuth.cs` | 235 | Firebase authentication |

**Total: 13 Services, 7,364 Lines**

---

## 4. PlayFabManager

**File:** `Assets/Scripts/PlayFab/PlayFabManager.cs`
**Lines:** 304
**Purpose:** Main orchestrator for PlayFab systems

### Class Definition

```csharp
[RequireComponent(typeof(PlayFabPlayerData))]
[RequireComponent(typeof(PlayFabLeaderboard))]
public class PlayFabManager : MonoBehaviour
{
    public static PlayFabManager Instance { get; private set; }

    // Events
    public event Action OnReady;
    public event Action<string> OnError;

    // Components
    public PlayFabPlayerData PlayerData { get; private set; }
    public PlayFabLeaderboard Leaderboard { get; private set; }
    public PlayFabMatchmaker Matchmaker { get; private set; }

    // State
    public bool IsReady { get; private set; }
    public bool IsLoggedIn => authManager?.IsLoggedIn ?? false;

    private AUMAuthManager authManager;
}
```

### Public Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `Login()` | - | void | Trigger login via auth manager |
| `Logout()` | - | void | Trigger logout |
| `GetPlayFabId()` | - | string | Get current PlayFab ID |
| `GetDisplayName()` | - | string | Get display name |
| `ReportMatchResults()` | bool won, int kills, int deaths, float damage, int ratingChange | void | Update stats after match |
| `ConnectToGameServer()` | MatchResult match | void | Connect to allocated server |
| `FindMatch()` | MatchType matchType | void | Start matchmaking |
| `CancelMatchmaking()` | - | void | Cancel current search |

### Lifecycle

```
Awake()
  └── InitializeComponents()
       ├── GetComponent<PlayFabPlayerData>()
       └── GetComponent<PlayFabLeaderboard>()

Start()
  ├── FindAuthManager()
  │    └── Subscribe to auth events
  └── FindMatchmaker()

OnLoginSuccess()
  └── (Data handled by PlayFabDataBridge)

OnDataLoaded()
  ├── IsReady = true
  └── OnReady?.Invoke()
```

---

## 5. PlayFabDataBridge

**File:** `Assets/Scripts/PlayFab/PlayFabDataBridge.cs`
**Lines:** 1961
**Purpose:** Unified single source of truth for all player data

### Class Definition

```csharp
public class PlayFabDataBridge : MonoBehaviour
{
    public static PlayFabDataBridge Instance { get; private set; }

    // Events
    public static event Action OnAllDataLoaded;
    public static event Action<bool> OnPlayerTypeDetected;  // true = new player
    public static event Action<string> OnDataLoadFailed;

    // State
    public string PlayFabId { get; private set; }
    public bool IsNewPlayer { get; private set; }
    public bool TutorialCompleted { get; private set; }

    // Loading flags
    private bool currenciesLoaded = false;
    private bool userDataLoaded = false;
    private bool inventoryLoaded = false;
}
```

### Data Loading Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `InitializeAfterLogin()` | string playFabId, bool newlyCreated | Initialize after PlayFab login |
| `LoadPlayerData()` | - | Public entry point for data loading |
| `LoadAllPlayerData()` | - | Load currencies, user data, inventory |

### Data Categories Loaded

```csharp
// Keys fetched from PlayFab UserData
var request = new GetUserDataRequest
{
    Keys = new List<string>
    {
        "PlayerStats",      // Wins, losses, guna, karma
        "Avatars",          // All avatar data
        "ActiveAvatarId",   // Currently active avatar
        "Settings",         // User preferences
        "Progress",         // Tutorial progress
        "SocialInfo",       // Profile, friends
        "MeditationInfo",   // Meditation state
        "TutorialCompleted" // Tutorial flag
    }
};
```

### Avatar Management

```csharp
// Save avatar with fetch-and-merge for safety
public void SaveAvatar(
    AUM.AvatarInfo avatar,
    bool setAsActive = true,
    Action onSuccess = null,
    Action<string> onError = null)

// Switch active avatar
public void SetActiveAvatar(
    Guid avatarId,
    Action onSuccess = null,
    Action<string> onError = null)

// Soft delete (preserves data for recovery)
public void DeleteAvatar(
    Guid avatarId,
    Action onSuccess = null,
    Action<string> onError = null)
```

### Tutorial Tracking

```csharp
// Mark tutorial complete
public void MarkTutorialComplete(
    Action onSuccess = null,
    Action<string> onError = null)

// Reset for testing
public void ResetTutorialCompletion(Action onSuccess = null)
```

### Currency Methods

```csharp
// Add currency
public void AddCurrency(
    string currencyCode,
    int amount,
    Action<int> onComplete = null)

// Subtract currency
public void SubtractCurrency(
    string currencyCode,
    int amount,
    Action<int> onComplete = null)

// Refresh from PlayFab
public void RefreshCurrencies(Action onComplete = null)
```

---

## 6. PlayFabPlayerData

**File:** `Assets/Scripts/PlayFab/PlayFabPlayerData.cs`
**Lines:** 525
**Purpose:** Legacy player data handler (being replaced by PlayFabDataBridge)

### Class Definition

```csharp
public class PlayFabPlayerData : MonoBehaviour
{
    public static PlayFabPlayerData Instance { get; private set; }

    // Events
    public event Action<PFPlayerGameData> OnDataLoaded;
    public event Action OnDataSaved;
    public event Action<string> OnError;

    // Data
    public PFPlayerGameData CurrentData { get; private set; }
    public bool HasAvatar => CurrentData?.Avatar?.IsCompleted ?? false;
    public bool IsDataLoaded { get; private set; } = false;
}
```

### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `LoadPlayerData()` | - | void (async) | Load all player data |
| `SaveAllData()` | - | void | Save all data to PlayFab |
| `SaveData()` | string key, object data | void | Save specific field |
| `SaveAvatarData()` | PFAvatarData, callbacks | void | Save avatar data |
| `ApplyLoadedDataToInterfaceManager()` | - | void | Sync to game state |
| `HasCompletedAvatar()` | - | bool | Check avatar completion |
| `UpdateMatchResults()` | PFMatchResult | void | Update stats after match |
| `GetCurrency()` | Action<int> callback | void | Get currency balance |
| `AddCurrency()` | int amount, callback | void | Add virtual currency |
| `SaveLoadout()` | int style, int god, int[] elementals, etc. | void | Save loadout |
| `GetLoadout()` | - | PFPlayerLoadout | Get current loadout |

---

## 7. PlayFabMatchmaker

**File:** `Assets/Scripts/PlayFab/PlayFabMatchmaker.cs`
**Lines:** 921
**Purpose:** Matchmaking with bot fallback

### Queue Configuration

```csharp
private static readonly Dictionary<MatchType, string> QueueMap = new Dictionary<MatchType, string>
{
    { MatchType.Solo_1v1, "queue_solo_1v1" },
    { MatchType.Solo_1v2, "queue_solo_1v2" },
    { MatchType.Solo_1v5, "queue_solo_1v5" },
    { MatchType.Duo_2v2, "queue_duo_2v2" },
    { MatchType.Duo_2v4, "queue_duo_2v2v2" },
    { MatchType.Trio_3v3, "queue_trio_3v3" },
    { MatchType.Tutorial, "queue_tutorial" }
};
```

### Settings

```csharp
[Header("Bot Backfill Settings")]
[SerializeField] private float botBackfillTimeout = 10f;
[SerializeField] private bool enableBotBackfill = true;

[Header("Polling Settings")]
[SerializeField] private float pollInterval = 3f;
[SerializeField] private int maxPollAttempts = 40;  // 40 * 3s = 2 min max
```

### Events

```csharp
public event Action<MatchResult> OnMatchFound;
public event Action<string> OnMatchFailed;
public event Action OnMatchCancelled;
public event Action<float> OnSearchTimeUpdate;
```

### State

```csharp
public bool IsSearching { get; private set; }
private string currentTicketId;
private string currentQueue;
private float searchStartTime;
private bool botMatchRequested = false;
private int pollAttempts = 0;
```

### Public Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `FindMatch()` | MatchType matchType | void | Start matchmaking |
| `CancelMatch()` | - | void | Cancel current search |
| `RequestBotMatchDirectly()` | MatchType matchType | void | Skip queue, request bot |

### Matchmaking Flow

```
FindMatch(matchType)
│
├─► Local Server Mode?
│   └── AllocateServerDirect() → OnMatchFound
│
└─► PlayFab Matchmaking
    │
    ├── CreateMatchmakingTicket()
    │   └── PollMatchmakingStatus()
    │       │
    │       ├── Status: "Matched"
    │       │   └── GetMatchDetailsCoroutine()
    │       │       └── RequestServerAllocationCoroutine()
    │       │           └── OnMatchFound
    │       │
    │       ├── Status: "WaitingForPlayers"
    │       │   └── Continue polling...
    │       │
    │       ├── Timeout (10s default)
    │       │   └── CancelTicketAndRequestBotMatch()
    │       │       └── RequestBotMatchCoroutine()
    │       │           └── CloudScript: "RequestBotMatch"
    │       │               └── OnMatchFound
    │       │
    │       └── Status: "Canceled"
    │           └── OnMatchCancelled
    │
    └── Error
        └── OnMatchFailed
```

### Ticket Status Values

| Status | Action |
|--------|--------|
| `Matched` | Get match details, allocate server |
| `WaitingForPlayers` | Continue polling |
| `WaitingForMatch` | Continue polling |
| `Canceled` | Exit polling |

---

## 8. PlayFabLeaderboard

**File:** `Assets/Scripts/PlayFab/PlayFabLeaderboard.cs`
**Lines:** 249
**Purpose:** Leaderboard operations

### Leaderboard Names

```csharp
public const string LEADERBOARD_RATING = "Rating";
public const string LEADERBOARD_WINS = "TotalWins";
public const string LEADERBOARD_KILLS = "TotalKills";
```

### Events

```csharp
public event Action<List<LeaderboardEntry>> OnLeaderboardLoaded;
public event Action<LeaderboardEntry> OnPlayerRankLoaded;
public event Action<string> OnError;
```

### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `UpdateLeaderboard()` | string name, int score | Update single leaderboard |
| `UpdateLeaderboards()` | Dictionary<string, int> scores | Update multiple leaderboards |
| `GetLeaderboard()` | string name, int maxResults=10 | Get top players |
| `GetLeaderboardAroundPlayer()` | string name, int maxResults=10 | Get centered around player |
| `GetFriendsLeaderboard()` | string name, int maxResults=10 | Get friends only |
| `GetPlayerRank()` | string name | Get current player's rank |

---

## 9. PlayFabCurrencyService

**File:** `Assets/Scripts/PlayFab/PlayFabCurrencyService.cs`
**Lines:** 257
**Purpose:** Currency conversion between tiers

### Conversion Rates

```csharp
public const int BRONZE_TO_SILVER_RATE = 1000;  // 1000 Bronze = 1 Silver
public const int SILVER_TO_GOLD_RATE = 100;     // 100 Silver = 1 Gold
```

### Events

```csharp
public event Action<bool, string> OnConversionComplete;
```

### Methods

```csharp
// Main conversion method
public async Task<CurrencyConversionResult> ConvertCurrencyAsync(
    RewardType fromCurrency,
    RewardType toCurrency,
    int sourceAmount)

// Refresh balances
public async Task RefreshCurrenciesAsync()
```

### Currency Codes

```csharp
private string GetCurrencyCode(RewardType type)
{
    return type switch
    {
        RewardType.Bronze => "BZ",
        RewardType.Silver => "SV",
        RewardType.Gold => "GD",
        _ => "BZ"
    };
}
```

---

## 10. PlayFabAvatarCurrencyService

**File:** `Assets/Scripts/PlayFab/PlayFabAvatarCurrencyService.cs`
**Lines:** 747
**Purpose:** Per-avatar currency management (currencies tied to avatars, not players)

### Events

```csharp
public static event Action<AvatarCurrencies> OnCurrenciesLoaded;
public static event Action<string, int, int> OnCurrencyChanged;  // code, old, new
public static event Action<string> OnAvatarEnteredHell;
public static event Action<string> OnAvatarLeftHell;
```

### State

```csharp
public AvatarCurrencies CurrentCurrencies { get; private set; }
public string CurrentAvatarId { get; private set; }
```

### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `LoadAvatarCurrencies()` | callbacks | Load active avatar's currencies |
| `LoadAvatarCurrencies()` | string avatarId, callbacks | Load specific avatar's currencies |
| `AddCurrency()` | string code, int amount, callbacks | Add currency |
| `SubtractCurrency()` | string code, int amount, callbacks | Subtract currency |
| `PurchaseItem()` | string itemId, string code, int price, callbacks | Server-validated purchase |
| `ProcessMatchEnd()` | bool won, int bronzeReward, callback | Handle match rewards |
| `AddLife()` | int amount=1, callbacks | Add life (exits hell if applicable) |
| `HasEnoughCurrency()` | string code, int amount | Check balance (local) |
| `GetCurrencyBalance()` | string code | Get balance (local) |

### CloudScript Functions Used

```csharp
// Load currencies
FunctionName = "getAvatarCurrencies"
FunctionParameter = new { avatarId = avatarId }

// Add currency
FunctionName = "addAvatarCurrency"
FunctionParameter = new { avatarId, currencyCode, amount }

// Subtract currency
FunctionName = "subtractAvatarCurrency"
FunctionParameter = new { avatarId, currencyCode, amount }

// Purchase
FunctionName = "purchaseWithAvatarCurrency"
FunctionParameter = new { avatarId, itemId, currencyCode, price }

// Match end
FunctionName = "processAvatarMatchEnd"
FunctionParameter = new { avatarId, won, bronzeReward }

// Add life
FunctionName = "addAvatarLife"
FunctionParameter = new { avatarId, amount }
```

---

## 11. PlayFabKarmaManager

**File:** `Assets/Scripts/PlayFab/PlayFabKarmaManager.cs`
**Lines:** 706
**Purpose:** Lives, Karma, Guna, and Hell systems

### Events

```csharp
public static event Action<int> OnLivesChanged;
public static event Action<KarmaGunaState> OnGunaUpdated;
public static event Action<KarmaHellStatus> OnHellStatusChanged;
public static event Action<KarmaMatchEndResult> OnMatchProcessed;
public static event Action<string> OnError;
```

### Properties

```csharp
public int CurrentLives { get; private set; } = 3;
public bool IsInHell { get; private set; } = false;
public float HellTimeRemaining { get; private set; } = 0;
public KarmaGunaState CurrentGuna { get; private set; }
public KarmaStateData CurrentKarma { get; private set; }
public bool IsInitialized { get; private set; } = false;
```

### Constants

```csharp
private const string LIVES_CURRENCY_CODE = "LV";
private const int DEFAULT_LIVES = 3;
```

### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `Initialize()` | callbacks | Initialize karma system |
| `InitializeNewPlayer()` | callbacks | Set up new player (3 lives) |
| `LoadKarmaState()` | callbacks | Load full karma state |
| `LoadLives()` | callbacks | Load just lives |
| `ProcessMatchEnd()` | bool won, string matchType, float timeAlive, float matchDuration, string karmaAction, string karmaReceived, string opponentId, callbacks | Full match processing |
| `ModifyLives()` | int change, string reason, callbacks | Change lives |
| `CheckHellStatus()` | callback | Check hell state |
| `UseHellShard()` | callbacks | Reduce hell time by 50% |
| `CompleteMeditation()` | string type, callbacks | Complete meditation |

### CloudScript Functions

```csharp
// Initialize new player
"initializeNewPlayer"

// Get full karma state
"getKarmaState"

// Process match end
"processMatchEnd"
FunctionParameter = new {
    won,
    matchType,
    timeAlive,
    matchDuration,
    karmaAction,      // "sattva", "rajas", "tamas"
    karmaReceived,
    opponentPlayFabId
}

// Modify lives
"modifyLives"
FunctionParameter = new { change, reason }

// Check hell status
"checkHellStatus"

// Use hell shard
"useHellShard"

// Complete meditation
"completeMeditation"
FunctionParameter = new { type }  // "bhakti" or "gnana"
```

### Karma System

```
Karma Actions (Winner's Choice):
├── Sattva - Grant mercy (increases Sattva guna)
├── Rajas - Steal bronze (increases Rajas guna)
└── Tamas - Punish (increases Tamas guna)

Guna Percentages:
├── Sattva: Default 33.33%
├── Rajas: Default 33.33%
└── Tamas: Default 33.34%

Hell System:
├── Triggered when lives = 0
├── Time-based (hellTimeSeconds)
├── Hell Shards reduce time by 50%
└── Lives restored on exit
```

---

## 12. PlayFabStoreService

**File:** `Assets/Scripts/PlayFab/PlayFabStoreService.cs`
**Lines:** 428
**Purpose:** Catalog management and purchases

### State

```csharp
private List<PlayFabStoreItem> _catalogItems = new List<PlayFabStoreItem>();
private bool _isCatalogLoaded = false;
private string _catalogVersion = "Main";

public bool IsCatalogLoaded => _isCatalogLoaded;
public IReadOnlyList<PlayFabStoreItem> CatalogItems => _catalogItems.AsReadOnly();
```

### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `LoadCatalogAsync()` | bool forceRefresh=false | Task<bool> | Load catalog |
| `GetAllItemsAsync()` | - | Task<List<PlayFabStoreItem>> | Get all items |
| `GetItemsForAvatarAsync()` | FightingStyles, FighterClass | Task<List<PlayFabStoreItem>> | Get filtered items |
| `GetItemsByTypeAsync()` | style, class, ItemType | Task<List<PlayFabStoreItem>> | Get by type |
| `GetFeaturedItemsAsync()` | style, class | Task<List<PlayFabStoreItem>> | Get featured items |
| `GetItemById()` | string itemId | PlayFabStoreItem | Get specific item |
| `GetItemByCode()` | uint itemCode | PlayFabStoreItem | Get by item code |
| `PurchaseItemAsync()` | string itemId, string currencyCode, int price | Task<PurchaseResult> | Purchase item |
| `PurchaseItemAsync()` | string itemId, RewardType, int price | Task<PurchaseResult> | Purchase (enum) |
| `ClearCache()` | - | void | Clear catalog cache |

### Currency Conversion

```csharp
public static string RewardTypeToCurrencyCode(RewardType rewardType)
{
    return rewardType switch
    {
        RewardType.Bronze => "BZ",
        RewardType.Silver => "SV",
        RewardType.Gold => "GD",
        _ => "BZ"
    };
}

public static string CurrencyIntToCode(int currencyType)
{
    return currencyType switch
    {
        1 => "BZ",  // Bronze
        2 => "SV",  // Silver
        3 => "GD",  // Gold
        _ => "BZ"
    };
}
```

---

## 13. PlayFabInventoryService

**File:** `Assets/Scripts/PlayFab/PlayFabInventoryService.cs`
**Lines:** 554
**Purpose:** Inventory management with default items and SET expansion

### State

```csharp
private List<InventoryItemData> _inventoryItems = new List<InventoryItemData>();
private bool _isInventoryLoaded = false;

public bool IsInventoryLoaded => _isInventoryLoaded;
public IReadOnlyList<InventoryItemData> InventoryItems => _inventoryItems.AsReadOnly();
```

### Events

```csharp
public event Action OnInventoryUpdated;
public event Action<InventoryItemData> OnItemAdded;
```

### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `SyncInventoryAsync()` | - | Task<bool> | Full sync (defaults + PlayFab) |
| `AddPurchasedItems()` | List<ItemInstance> | void | Add purchased items |
| `AddPurchasedItem()` | uint itemCode, bool isSet | void | Add single item |
| `OwnsItem()` | uint itemCode | bool | Check ownership |
| `OwnsItemById()` | string itemId | bool | Check by ID |
| `ClearCache()` | - | void | Clear inventory |
| `RefreshAsync()` | - | Task | Refresh from PlayFab |

### Sync Flow

```
SyncInventoryAsync()
│
├── 1. Clear local cache
│
├── 2. AddDefaultItems()
│   ├── Add ID=1 items for each slot (Head, Torso, Hands, Pants, Legs, Weapons)
│   └── Add currently equipped non-default items
│
├── 3. Fetch PlayFab inventory
│   └── ProcessPlayFabInventory()
│       └── For each item:
│           ├── Is SET? → ExpandSetToInventory()
│           │            ├── Generate Head piece
│           │            ├── Generate Torso piece
│           │            ├── Generate Hands piece
│           │            ├── Generate Pants piece
│           │            └── Generate Legs piece
│           └── Individual → AddSingleItemToInventory()
│
└── 4. Update currencies & notify
```

### SET Expansion

```csharp
private void ExpandSetToInventory(uint setItemCode, string itemInstanceId)
{
    var setDetails = new WearItem(setItemCode);
    var style = setDetails.FightingStyle;
    var fighterClass = setDetails.FighterClass;
    var itemIdentifier = setDetails.ItemIdentifier;

    var pieceTypes = new[] {
        ItemType.Head,
        ItemType.Torso,
        ItemType.Hands,
        ItemType.Pants,
        ItemType.Legs
    };

    foreach (var pieceType in pieceTypes)
    {
        uint pieceCode = WearItem.GetItemCode(style, fighterClass, pieceType, itemIdentifier);
        string pieceInstanceId = $"{itemInstanceId}_{pieceType}";
        AddSingleItemToInventory(pieceCode, pieceInstanceId, true);
    }
}
```

---

## 14. PlayFabItemMapper

**File:** `Assets/Scripts/PlayFab/PlayFabItemMapper.cs`
**Lines:** 259
**Purpose:** Convert PlayFab CustomData ↔ WearItem itemCode encoding

### Static Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `ParseCustomData()` | string json | PlayFabItemData | Parse CustomData JSON |
| `GetItemCode()` | PlayFabItemData | uint | Get itemCode from data |
| `GetItemCodeFromJson()` | string json | uint | Get itemCode from JSON |
| `EncodeItemCode()` | FightingStyles, FighterClass, ItemType, uint identifier | uint | Encode to itemCode |
| `DecodeItemCode()` | uint itemCode | tuple | Decode from itemCode |
| `ValidateItemCode()` | uint itemCode | bool | Validate itemCode |
| `ParseFightingStyle()` | string styleName | FightingStyles | Parse style string |
| `ParseFighterClass()` | string gender | FighterClass | Parse gender string |
| `ParseItemType()` | string slotType, bool isWeapon, bool isSet | ItemType | Parse item type |
| `GetTierIdentifier()` | string setName, string tier | uint | Get tier ID |
| `GetAddressableKeys()` | uint itemCode, ObjectType | string[] | Get Addressable keys |
| `DebugItemCode()` | uint itemCode, string context | void | Debug logging |
| `DebugItemData()` | PlayFabItemData, string context | void | Debug logging |

### Style Parsing

```csharp
public static FightingStyles ParseFightingStyle(string styleName)
{
    return styleName.ToLower() switch
    {
        "amuktha" => FightingStyles.Amuktha,
        "mantramuktha" => FightingStyles.MantraMuktha,
        "mukthamuktha" => FightingStyles.MukthaMuktha,
        "panimuktha" => FightingStyles.PaniMuktha,
        "yantramuktha" => FightingStyles.YantraMuktha,
        _ => FightingStyles.Amuktha
    };
}
```

### Tier Identifiers

```csharp
public static uint GetTierIdentifier(string setName, string tier)
{
    return (set, t) switch
    {
        ("aranya", "bronze") => 1,
        ("aranya", "silver") => 2,
        ("aranya", "gold") => 3,
        ("lohitha", "bronze") => 4,
        ("lohitha", "silver") => 5,
        ("lohitha", "gold") => 6,
        _ => 1
    };
}
```

---

## 15. PlayFabItemData

**File:** `Assets/Scripts/PlayFab/PlayFabItemData.cs`
**Lines:** 218
**Purpose:** Data class for parsed PlayFab catalog item CustomData

### Fields

```csharp
[Serializable]
public class PlayFabItemData
{
    // Armor fields
    public string setName;       // "aranya" or "lohitha"
    public string fightingStyle; // "Amuktha", "MantraMuktha", etc.
    public string gender;        // "m" or "f"
    public string slotType;      // "head", "torso", "hands", "pants", "legs"
    public string tier;          // "bronze", "silver", "gold"

    // Weapon fields
    public string weaponType;    // "sword", "staff", "axe", "bow", "disc"
    public string material;      // "wood_steel" or "steel_gold"
    public bool isDefault;       // Default weapon?
    public bool grantOnCreate;   // Grant on avatar creation?

    // Bundle/Set fields
    public bool isBundle;        // Is this a bundle?
    public int discountPercent;  // Discount for bundles

    // Encoded itemCode
    public uint itemCode;        // Pre-calculated itemCode
    public uint itemCodeOld;     // Migration reference
}
```

### Helper Properties

```csharp
public bool IsArmor => !string.IsNullOrEmpty(slotType) &&
                       string.IsNullOrEmpty(weaponType) &&
                       !isBundle;

public bool IsWeapon => !string.IsNullOrEmpty(weaponType);

public bool IsSet => isBundle || slotType == "set";
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `GetFightingStyle()` | FightingStyles | Parse fighting style |
| `GetFighterClass()` | FighterClass | Parse gender to class |
| `GetItemType()` | ItemType | Parse slot to item type |
| `GetItemIdentifier()` | uint | Get tier-based identifier |
| `CalculateItemCode()` | uint | Calculate from fields |
| `GetValidItemCode()` | uint | Get stored or calculated |

### Weapon Type → Fighting Style

```csharp
// For weapons, derive style from weapon type
weaponType?.ToLower() switch
{
    "sword" => FightingStyles.Amuktha,
    "staff" => FightingStyles.MantraMuktha,
    "axe" => FightingStyles.MukthaMuktha,
    "bow" => FightingStyles.PaniMuktha,
    "disc" => FightingStyles.YantraMuktha,
    _ => FightingStyles.Amuktha
};
```

---

## 16. PlayFabOpenIdAuth

**File:** `Assets/Scripts/Auth/PlayFabOpenIdAuth.cs`
**Lines:** 235
**Purpose:** Firebase → PlayFab authentication via OpenID Connect

### Properties

```csharp
private string connectionId = "Firebase";  // OpenID Connection ID in PlayFab
```

### Methods

```csharp
public void Initialize(AUMAuthConfig config)
{
    connectionId = config.openIdConnectionId;
}

public void LoginWithOpenIdConnect(
    string idToken,
    Action<LoginResult> onSuccess,
    Action<PlayFabError> onError)
```

### Login Request

```csharp
var request = new LoginWithOpenIdConnectRequest
{
    ConnectionId = connectionId,   // "Firebase"
    IdToken = idToken,             // Firebase ID token
    CreateAccount = true           // Auto-create if new
};

PlayFabClientAPI.LoginWithOpenIdConnect(request, onSuccess, onError);
```

### JWT Debugging

The service includes comprehensive JWT debugging to diagnose authentication issues:

```csharp
// Decodes and logs JWT claims
private void DecodeAndLogJWT(string jwt)
{
    // Header: {"alg":"RS256","typ":"JWT"}
    // Payload: {"iss":"...", "aud":"...", "sub":"...", "email":"...", etc.}
    // Key claims logged:
    // - iss (Issuer)
    // - aud (Audience) ← CRITICAL: Must match PlayFab Client ID
    // - sub (Subject/User ID)
    // - email
    // - exp (Expires)
    // - iat (Issued At)
}
```

### Common Errors

| Error | Hint |
|-------|------|
| `InvalidIdentityProviderId` | OpenID Connection not found in PlayFab |
| `Audience` mismatch | JWT 'aud' doesn't match PlayFab Client ID |

---

## 17. Data Classes

### PlayFabPlayerStats

```csharp
[Serializable]
public class PlayFabPlayerStats
{
    public int lives;
    public int guna;
    public int wins;
    public int losses;
    public int sattva;
    public int rajas;
    public int tamas;
    public int hellTime;
    public int maxHellTime;
}
```

### PlayFabAvatarData

```csharp
[Serializable]
public class PlayFabAvatarData
{
    public string uniqueID;
    public string nickName;
    public byte fightingStyle;
    public byte fighterClass;
    public byte godSelected;
    public byte weaponVariant;
    public byte lastActive;
    public byte isCompleted;
    public byte[] elementalSelected;
    public uint[] wearItemCodes;

    // Soft delete fields
    public byte isDeleted = 0;
    public string deletedAt = "";

    // Per-avatar currencies
    public AvatarCurrencyData currencies;
}
```

### AvatarCurrencyData

```csharp
[Serializable]
public class AvatarCurrencyData
{
    public int bronze = 500;      // Starting bronze
    public int silver = 0;
    public int gold = 0;
    public int lives = 3;         // Starting lives
    public int timeShards = 0;
    public int hellShards = 0;
    public int bhaktiTokens = 0;
    public int gnanaTokens = 0;
}
```

### PlayFabUserSettings

```csharp
[Serializable]
public class PlayFabUserSettings
{
    public float musicVolume = 1f;
    public float sfxVolume = 1f;
    public int graphicsQuality = 2;
    public bool vibration = true;
}
```

### PlayFabProgress

```csharp
[Serializable]
public class PlayFabProgress
{
    public int tutorialStep;
    public bool hasCompletedTutorial;
    public int lastMatchType;
}
```

### PlayFabSocialInfo

```csharp
[Serializable]
public class PlayFabSocialInfo
{
    public string profileName;
    public string friendId;
    public int profileImageID;
}
```

### PlayFabMeditationInfo

```csharp
[Serializable]
public class PlayFabMeditationInfo
{
    public int meditationState;
    public int bhaktiTimerRemaining;
    public int bhaktiTimerTotal;
    public int gnanaTimerRemaining;
    public int gnanaTimerTotal;
    public int timeShards;
}
```

### PFPlayerGameData

```csharp
[Serializable]
public class PFPlayerGameData
{
    public PFPlayerStats Stats = new PFPlayerStats();
    public PFPlayerLoadout Loadout = new PFPlayerLoadout();
    public PFPlayerInventory Inventory = new PFPlayerInventory();
    public PFPlayerSettings Settings = new PFPlayerSettings();
    public PFPlayerProgress Progress = new PFPlayerProgress();
    public PFAvatarData Avatar;
}
```

### PFPlayerStats

```csharp
[Serializable]
public class PFPlayerStats
{
    public int TotalMatches;
    public int Wins;
    public int Losses;
    public int TotalKills;
    public int TotalDeaths;
    public float TotalDamageDealt;
    public int Rating = 1000;
    public int CurrentWinStreak;
    public int BestWinStreak;
    public int[] MatchesPerStyle = new int[5];
    public int[] WinsPerStyle = new int[5];
}
```

### PFPlayerLoadout

```csharp
[Serializable]
public class PFPlayerLoadout
{
    public int SelectedFightingStyle;
    public int SelectedGod;
    public int[] SelectedElementals = new int[4];
    public int WeaponSkin;
    public int CharacterSkin;
}
```

### PFPlayerInventory

```csharp
[Serializable]
public class PFPlayerInventory
{
    public List<string> OwnedSkins = new List<string>();
    public List<string> OwnedEmotes = new List<string>();
    public List<string> OwnedBanners = new List<string>();
    public List<string> OwnedWeaponSkins = new List<string>();
}
```

### PFPlayerSettings

```csharp
[Serializable]
public class PFPlayerSettings
{
    public float MusicVolume = 1f;
    public float SFXVolume = 1f;
    public float Sensitivity = 1f;
    public bool VibrationEnabled = true;
    public int GraphicsQuality = 2;
}
```

### PFPlayerProgress

```csharp
[Serializable]
public class PFPlayerProgress
{
    public int Level = 1;
    public int Experience;
    public int TutorialStep;
    public bool TutorialCompleted;
    public long LastLoginTimestamp;
    public int ConsecutiveLoginDays;
}
```

### PFMatchResult

```csharp
[Serializable]
public class PFMatchResult
{
    public bool Won;
    public int Kills;
    public int Deaths;
    public float DamageDealt;
    public int RatingChange;
    public string MatchType;
}
```

### PFAvatarData (Legacy)

```csharp
[Serializable]
public class PFAvatarData
{
    public int FightingStyle;
    public int FighterClass;
    public int WeaponVariant;
    public int GodSelected;
    public int[] Elementals;
    public string NickName;
    public string CreatedAt;
    public bool IsCompleted;
}
```

### MatchResult

```csharp
[Serializable]
public class MatchResult
{
    public string MatchId;
    public string ServerIP;
    public int ServerPort;
    public bool IsBotMatch;
    public List<MatchPlayer> Players;
}
```

### MatchPlayer

```csharp
[Serializable]
public class MatchPlayer
{
    public string PlayFabId;
    public string TeamId;
    public bool IsBot;
}
```

### LeaderboardEntry

```csharp
[Serializable]
public class LeaderboardEntry
{
    public int Rank;
    public string PlayFabId;
    public string DisplayName;
    public int Score;
}
```

### CurrencyConversionResult

```csharp
public class CurrencyConversionResult
{
    public bool Success;
    public string ErrorMessage;
    public int SourceAmount;
    public int GainAmount;
    public RewardType FromCurrency;
    public RewardType ToCurrency;
}
```

### PurchaseResult

```csharp
public class PurchaseResult
{
    public bool Success;
    public string ItemId;
    public string ErrorMessage;
    public List<ItemInstance> Items;
}
```

### PlayFabStoreItem

```csharp
[Serializable]
public class PlayFabStoreItem
{
    // PlayFab identifiers
    public string ItemId;
    public string ItemClass;
    public string DisplayName;
    public string Description;
    public List<string> Tags;

    // Parsed CustomData
    public PlayFabItemData ParsedData;

    // Encoded itemCode
    public uint ItemCode;

    // Prices
    public uint BronzePrice;
    public uint SilverPrice;
    public uint GoldPrice;

    // Decoded properties
    public FightingStyles FightingStyle;
    public FighterClass FighterClass;
    public ItemType ItemType;
    public uint ItemIdentifier;

    // UI state
    public bool IsFeatured;
    public bool IsOwned;
    public AddressableIcon IconData;
}
```

### InventoryItemData

```csharp
[Serializable]
public class InventoryItemData
{
    public string ItemId;
    public string ItemInstanceId;
    public uint ItemCode;
    public FightingStyles FightingStyle;
    public FighterClass FighterClass;
    public ItemType ItemType;
    public uint ItemIdentifier;
    public bool IsNew;
    public PlayFabItemData ParsedData;
}
```

### Karma Data Classes

```csharp
[Serializable]
public class KarmaFullState
{
    public KarmaStateData karma;
    public KarmaGunaState guna;
    public KarmaHellStateData hell;
    public int lives;
    public KarmaCurrencyBalances currencies;
}

[Serializable]
public class KarmaStateData
{
    public float accumulatedKarma;
    public int totalMatchesPlayed;
    public int sattvicStreak;
    public int rajasicStreak;
    public int tamasicStreak;
    public string lastAction;
}

[Serializable]
public class KarmaGunaState
{
    public float sattva = 33.33f;
    public float rajas = 33.33f;
    public float tamas = 33.34f;
    public string dominant = "none";
    public int totalActions;
    public int switchCount;
    public int nextSwitchThreshold = 1;
}

[Serializable]
public class KarmaHellStateData
{
    public bool inHell;
    public float hellTimeSeconds;
    public string entryTime;
    public string exitTime;
    public int totalHellVisits;
}

[Serializable]
public class KarmaHellStatus
{
    public bool inHell;
    public float remainingSeconds;
    public string exitTime;
    public bool justExited;
    public int livesRestored;
    public int lives;
}

[Serializable]
public class KarmaCurrencyBalances
{
    public int BZ;  // Bronze
    public int SV;  // Silver
    public int GD;  // Gold
    public int TS;  // Time Shards
    public int HS;  // Hell Shards
    public int BT;  // Bhakti Tokens
    public int GT;  // Gnana Tokens
    public int LV;  // Lives
}

[Serializable]
public class KarmaMatchEndResult
{
    public bool success;
    public string error;
    public int bronzeEarned;
    public int timeShardsEarned;
    public int stolenBronze;
    public bool hellShardEarned;
    public int livesChange;
    public float baselineKarma;
    public float postMatchKarma;
    public float totalKarma;
    public bool gunaUpdated;
    public bool enteredHell;
    public string newDominantGuna;
    public KarmaGunaPercentages gunaPercentages;
    public int currentLives;
    public float accumulatedKarma;
}

[Serializable]
public class KarmaGunaPercentages
{
    public float sattva;
    public float rajas;
    public float tamas;
}

[Serializable]
public class KarmaModifyLivesResult
{
    public bool success;
    public int previousLives;
    public int currentLives;
    public int change;
    public bool enteredHell;
}

[Serializable]
public class KarmaHellShardResult
{
    public bool success;
    public string error;
    public float previousRemaining;
    public float reduction;
    public float newRemaining;
    public bool exited;
    public int livesRestored;
}

[Serializable]
public class KarmaMeditationResult
{
    public bool success;
    public string tokenGranted;
    public int lifeRestored;
    public int currentLives;
}
```

### Avatar Currency Service Response Types

```csharp
[Serializable]
public class AvatarCurrencies
{
    public int bronze = 500;
    public int silver = 0;
    public int gold = 0;
    public int lives = 3;
    public int timeShards = 0;
    public int hellShards = 0;
    public int bhaktiTokens = 0;
    public int gnanaTokens = 0;
}

[Serializable]
public class MatchEndResult
{
    public bool won;
    public bool enteredHell;
    public AvatarCurrencies currencies;
}

[Serializable]
public class GetCurrenciesResponse
{
    public bool success;
    public string error;
    public string avatarId;
    public string nickName;
    public AvatarCurrencies currencies;
}

[Serializable]
public class CurrencyChangeResponse
{
    public bool success;
    public string error;
    public string avatarId;
    public string currencyCode;
    public int oldBalance;
    public int newBalance;
    public AvatarCurrencies allCurrencies;
}

[Serializable]
public class PurchaseResponse
{
    public bool success;
    public string error;
    public string avatarId;
    public string itemId;
    public string currencyCode;
    public int price;
    public int oldBalance;
    public int newBalance;
    public AvatarCurrencies allCurrencies;
}

[Serializable]
public class MatchEndResponse
{
    public bool success;
    public string avatarId;
    public string nickName;
    public bool won;
    public bool enteredHell;
    public AvatarCurrencies currencies;
}

[Serializable]
public class AddLifeResponse
{
    public bool success;
    public string error;
    public string avatarId;
    public int oldLives;
    public int newLives;
    public bool leftHell;
    public AvatarCurrencies allCurrencies;
}
```

---

## 18. CloudScript Functions

### Avatar Currency Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getAvatarCurrencies` | avatarId | GetCurrenciesResponse | Get avatar's currencies |
| `addAvatarCurrency` | avatarId, currencyCode, amount | CurrencyChangeResponse | Add currency |
| `subtractAvatarCurrency` | avatarId, currencyCode, amount | CurrencyChangeResponse | Subtract currency |
| `purchaseWithAvatarCurrency` | avatarId, itemId, currencyCode, price | PurchaseResponse | Server-validated purchase |
| `processAvatarMatchEnd` | avatarId, won, bronzeReward | MatchEndResponse | Process match rewards |
| `addAvatarLife` | avatarId, amount | AddLifeResponse | Add life |

### Karma Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `initializeNewPlayer` | - | - | Set up new player (3 lives) |
| `getKarmaState` | - | KarmaFullState | Get full karma state |
| `processMatchEnd` | won, matchType, timeAlive, matchDuration, karmaAction, karmaReceived, opponentPlayFabId | KarmaMatchEndResult | Full match processing |
| `modifyLives` | change, reason | KarmaModifyLivesResult | Change lives |
| `checkHellStatus` | - | KarmaHellStatus | Check hell state |
| `useHellShard` | - | KarmaHellShardResult | Reduce hell time |
| `completeMeditation` | type | KarmaMeditationResult | Complete meditation |

### Matchmaking Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `RequestBotMatch` | matchType | serverIP, serverPort, matchId | Request bot match |
| `RequestGameServer` | matchId, matchType, playerIds | serverIP, serverPort | Request server allocation |

---

## 19. Currency System

### Currency Codes

| Code | Name | Default | Description |
|------|------|---------|-------------|
| `BZ` | Bronze | 500 | Primary currency (earned in matches) |
| `SV` | Silver | 0 | Premium currency (converted from Bronze) |
| `GD` | Gold | 0 | Super premium (converted from Silver) |
| `LV` | Lives | 3 | Game lives (lose 1 per match loss) |
| `TS` | Time Shards | 0 | Meditation currency |
| `HS` | Hell Shards | 0 | Reduce hell time |
| `BT` | Bhakti Tokens | 0 | Meditation reward |
| `GT` | Gnana Tokens | 0 | Meditation reward |

### Conversion Rates

```
1000 Bronze (BZ) → 1 Silver (SV)
100 Silver (SV) → 1 Gold (GD)
```

### Per-Avatar Currency

Currencies are stored per-avatar, not per-player. When switching avatars:

1. Save current avatar's currencies
2. Load new avatar's currencies
3. Update `InterfaceManager.playerRewards`

---

## 20. Error Handling

### Common PlayFab Errors

| Error Code | Description | Handling |
|------------|-------------|----------|
| `InvalidIdentityProviderId` | OpenID Connection not found | Check PlayFab dashboard |
| `InvalidTitleId` | Invalid PlayFab Title ID | Verify PlayFabSettings |
| `NotAuthenticated` | Not logged in | Trigger re-login |
| `AccountBanned` | Account is banned | Show ban message |
| `InsufficientFunds` | Not enough currency | Show error, refresh balance |
| `ItemNotFound` | Invalid item ID | Refresh catalog |

### Error Callback Pattern

```csharp
PlayFabClientAPI.SomeMethod(request,
    result =>
    {
        Debug.Log("[Service] Success");
        onSuccess?.Invoke(result);
    },
    error =>
    {
        Debug.LogError($"[Service] Error: {error.ErrorMessage}");
        Debug.LogError($"[Service] Code: {error.Error}");
        Debug.LogError($"[Service] HTTP: {error.HttpCode}");

        if (error.ErrorDetails != null)
        {
            foreach (var detail in error.ErrorDetails)
            {
                Debug.LogError($"[Service] Detail: {detail.Key} = {string.Join(", ", detail.Value)}");
            }
        }

        onError?.Invoke(error.ErrorMessage);
    });
```

---

## Cross-Reference

- **Protocol Overview:** [PROTOCOL-1-OVERVIEW.md](./PROTOCOL-1-OVERVIEW.md)
- **WSS Packets:** [PROTOCOL-2-WSS-PACKETS.md](./PROTOCOL-2-WSS-PACKETS.md)
- **UDP Packets:** [PROTOCOL-3-UDP-PACKETS.md](./PROTOCOL-3-UDP-PACKETS.md)
- **MatchKeeper:** [PROTOCOL-4-MATCHKEEPER.md](./PROTOCOL-4-MATCHKEEPER.md)
- **State Machines:** [PROTOCOL-6-STATE-MACHINES.md](./PROTOCOL-6-STATE-MACHINES.md)
- **Game Data:** [PROTOCOL-7-GAME-DATA.md](./PROTOCOL-7-GAME-DATA.md)
- **Characters:** [PROTOCOL-8-CHARACTERS.md](./PROTOCOL-8-CHARACTERS.md)
- **Spells:** [PROTOCOL-9-SPELLS.md](./PROTOCOL-9-SPELLS.md)
- **Enums:** [PROTOCOL-10-ENUMS.md](./PROTOCOL-10-ENUMS.md)
- **Index:** [PROTOCOL-INDEX.md](./PROTOCOL-INDEX.md)

---

*Document generated from AUM-Unity-Staging-Legacy codebase*
*Total data classes: 45+*
*Total CloudScript functions: 15+*
*Total service methods: 80+*
