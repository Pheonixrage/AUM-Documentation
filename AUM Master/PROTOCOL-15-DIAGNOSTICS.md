# PROTOCOL-15-DIAGNOSTICS.md
# Diagnostics, Logging, and Telemetry Systems

## Overview

This document covers the server-side diagnostic and logging systems used for debugging, combat telemetry, and post-match analysis.

**Key Files:**
- `Assets/Scripts/Network/ClientLog.cs` - Client-sent debug logs
- `Assets/Scripts/Debug/DebugLogTracker.cs` - Filtered debug log capture
- `Assets/Scripts/Diagnostics/AUMFileLogger.cs` - Full session logging
- `Assets/Scripts/Network/Utils.cs` - Combat logging utilities

---

## 1. ClientLog System

### 1.1 Overview

`ClientLog` processes debug information sent from clients to the server, enabling server-side logging of client-side issues.

```csharp
public class ClientLog
{
    public static void HandleClientLog(UDPServerSocket.Peer peer, byte[] packet);

    public enum ClientLogType
    {
        SIMULATIONFAIL = 0,   // Position mismatch
        STATEMISMATCH = 1,    // State desync
        CHANGESTATE = 2       // State transition log
    }
}
```

### 1.2 Log Types

#### SIMULATIONFAIL (Position Desync)

Logged when client position doesn't match server simulation.

```csharp
case ClientLogType.SIMULATIONFAIL:
    Packet.SimulationFailLog logPacket = Serializer.Deserialize<Packet.SimulationFailLog>(packet);
    Utils.WriteLogFile(GameManager.Instance.MatchUUID.ToString(), Utils.LogSource.CLIENT,
        "[" + player.nickName + "][" + logPacket.frameNumber +
        "][FAIL] Simulation:[(" + logPacket.curX + "," + logPacket.curY + ")]-" +
        "[(" + logPacket.realX + "," + logPacket.realY + ")][" +
        ((FSM.StateType)logPacket.state).ToString() +
        "][P:" + ((SlowType)(logPacket.movePenalty & 0x3)).ToString() +
        ",B:" + ((WillPowerBuffType)(logPacket.movePenalty >> 2)).ToString() + "]");
    break;
```

**Output Example:**
```
[PlayerName][12345][FAIL] Simulation:[(10.5,20.3)]-[(10.8,20.1)][Idle][P:None,B:None]
```

#### STATEMISMATCH (State Desync)

Logged when client state doesn't match server expectation.

```csharp
case ClientLogType.STATEMISMATCH:
    Packet.StateMismatchLog logPacket = Serializer.Deserialize<Packet.StateMismatchLog>(packet);
    Utils.WriteLogFile(GameManager.Instance.MatchUUID.ToString(), Utils.LogSource.CLIENT,
        "[" + player.nickName + "][" + logPacket.frameNumber +
        "][FAIL] State: GOT:" + ((FSM.StateType)logPacket.realState).ToString() +
        " FOR:" + ((FSM.StateType)logPacket.curState).ToString());
    break;
```

**Output Example:**
```
[PlayerName][12345][FAIL] State: GOT:Melee FOR:Idle
```

#### CHANGESTATE (State Transition)

Logs all state changes for debugging.

```csharp
case ClientLogType.CHANGESTATE:
    Packet.StateChangeLog logPacket = Serializer.Deserialize<Packet.StateChangeLog>(packet);
    Utils.WriteLogFile(GameManager.Instance.MatchUUID.ToString(), Utils.LogSource.CLIENT,
        "[" + player.nickName + "][" + logPacket.frameNumber +
        "][" + ((FSM.StateType)logPacket.curState).ToString() + "->" +
        ((FSM.StateType)logPacket.newState).ToString() + "]");
    break;
```

**Output Example:**
```
[PlayerName][12345][Idle->Melee]
```

---

## 2. DebugLogTracker

### 2.1 Overview

`DebugLogTracker` is a persistent debug log capture system that filters for specific tags and saves to session files.

```csharp
public class DebugLogTracker : MonoBehaviour
{
    private static DebugLogTracker _instance;
    public static DebugLogTracker Instance => _instance;

    public List<string> trackedTags;  // Tags to filter for
    public int maxLogLines = 1000;    // Memory buffer limit
    public float autoSaveInterval = 30f;  // Save interval (seconds)
}
```

### 2.2 Tracked Tags

```csharp
public List<string> trackedTags = new List<string>
{
    "[MatchState]",
    "[TestMode]",
    "[GameManager]",
    "[PlayerManager]",
    "[BotManager]",
    "NullReferenceException",
    "Exception",
    "Error",
    "BroadcastPlayers",
    "Sending to",
    "AuthenticatePlayer",
    "Waiting for human"
};
```

### 2.3 Log Entry Structure

```csharp
[Serializable]
public class LogEntry
{
    public string timestamp;   // HH:mm:ss.fff
    public string type;        // Log/Warning/Error/Exception
    public string message;     // Log content
    public string stackTrace;  // Stack trace (errors only)
}
```

### 2.4 Initialization

```csharp
void Awake()
{
    // Singleton pattern
    if (_instance != null && _instance != this)
    {
        Destroy(gameObject);
        return;
    }
    _instance = this;
    DontDestroyOnLoad(gameObject);

    // Create log folder: {ProjectRoot}/DebugLogs/
    logFolderPath = Path.Combine(Application.dataPath, "..", "DebugLogs");
    if (!Directory.Exists(logFolderPath))
    {
        Directory.CreateDirectory(logFolderPath);
    }

    // Session file: server_session_2026-01-21_14-30-00.log
    string sessionTime = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
    currentSessionFile = Path.Combine(logFolderPath, $"server_session_{sessionTime}.log");

    // Subscribe to Unity log callback
    Application.logMessageReceived += HandleLog;

    // Write session header
    WriteToFile($"=== SERVER DEBUG SESSION STARTED: {DateTime.Now} ===\n");
    WriteToFile($"Unity Version: {Application.unityVersion}\n");
    WriteToFile($"Platform: {Application.platform}\n");
    WriteToFile($"Tracked Tags: {string.Join(", ", trackedTags)}\n");
    WriteToFile("====================================================\n\n");
}
```

### 2.5 Log Filtering

```csharp
void HandleLog(string logString, string stackTrace, LogType type)
{
    // Check if log matches any tracked tag
    bool shouldTrack = false;
    foreach (var tag in trackedTags)
    {
        if (logString.Contains(tag) || (type == LogType.Error || type == LogType.Exception))
        {
            shouldTrack = true;
            break;
        }
    }

    if (!shouldTrack) return;

    var entry = new LogEntry
    {
        timestamp = DateTime.Now.ToString("HH:mm:ss.fff"),
        type = type.ToString(),
        message = logString,
        stackTrace = (type == LogType.Error || type == LogType.Exception) ? stackTrace : ""
    };

    logEntries.Add(entry);

    // Trim old entries
    while (logEntries.Count > maxLogLines)
    {
        logEntries.RemoveAt(0);
    }

    // Format and buffer
    string logLine = $"[{entry.timestamp}] [{entry.type}] {entry.message}";
    if (!string.IsNullOrEmpty(entry.stackTrace))
    {
        logLine += $"\n  Stack: {entry.stackTrace.Split('\n')[0]}";
    }
    logLine += "\n";

    logBuffer.Append(logLine);

    // Immediate write for errors
    if (type == LogType.Error || type == LogType.Exception)
    {
        SaveToFile();
    }
}
```

### 2.6 Utility Methods

```csharp
// Get current session log path
public string GetCurrentLogPath() => currentSessionFile;

// Get log folder path
public string GetLogFolderPath() => logFolderPath;

// Write a summary block
public void WriteSummary(string title, string content)
{
    string summary = $"\n### {title} - {DateTime.Now:HH:mm:ss} ###\n{content}\n###\n\n";
    WriteToFile(summary);
}

// Write a marker for analysis
public void WriteMarker(string markerName)
{
    WriteToFile($"\n========== MARKER: {markerName} - {DateTime.Now:HH:mm:ss} ==========\n\n");
}
```

---

## 3. AUMFileLogger

### 3.1 Overview

`AUMFileLogger` captures ALL Unity logs to a persistent file for complete session history.

```csharp
public class AUMFileLogger : MonoBehaviour
{
    private string logFilePath;     // {ProjectRoot}/AUM_Server_Log.txt
    private StreamWriter logWriter;
}
```

### 3.2 Initialization

```csharp
void Awake()
{
    DontDestroyOnLoad(gameObject);

    // Path: {ProjectRoot}/AUM_Server_Log.txt
    logFilePath = Path.Combine(Directory.GetCurrentDirectory(), "AUM_Server_Log.txt");

    // Clear previous log on startup
    try
    {
        if (File.Exists(logFilePath))
        {
            File.Delete(logFilePath);
        }
        logWriter = new StreamWriter(logFilePath, true);
        logWriter.AutoFlush = true;

        Debug.Log($"[AUMFileLogger] Persistent server logging started at: {logFilePath}");
        logWriter.WriteLine($"--- AUM Server Session Started: {DateTime.Now} ---");
    }
    catch (Exception ex)
    {
        Debug.LogError($"[AUMFileLogger] Failed to initialize server logger: {ex.Message}");
    }
}
```

### 3.3 Log Capture

```csharp
void OnEnable()
{
    Application.logMessageReceived += HandleLog;
}

void OnDisable()
{
    Application.logMessageReceived -= HandleLog;
    if (logWriter != null)
    {
        logWriter.Close();
    }
}

void HandleLog(string logString, string stackTrace, LogType type)
{
    if (logWriter == null) return;

    string timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
    string logEntry = $"[{timestamp}] [{type}] {logString}";

    logWriter.WriteLine(logEntry);

    // Include stack trace for errors
    if (type == LogType.Error || type == LogType.Exception)
    {
        logWriter.WriteLine(stackTrace);
    }
}
```

---

## 4. Utils (Combat Logging)

### 4.1 Overview

`Utils` provides combat logging utilities for tracking damage, blocks, and shield interactions.

```csharp
class Utils
{
    public static int GetSize(Type target);
    public static void SendLogData(Player, CombatLogType, Player, DamageType, EffectType, float, float);
    public static void WriteLogFile(string, LogSource, string);

    public enum CombatLogType { ... }
    public enum LogSource { ... }
}
```

### 4.2 CombatLogType Enum

```csharp
public enum CombatLogType
{
    RECEIVE,       // Damage received
    BLOCK,         // Attack blocked by shield
    DEATH,         // Player died
    SHIELD_BREAK,  // Shield destroyed
    NULLIFY,       // Spell nullified (counter-element)
    MITIGATE,      // Damage reduced (same element)
    VULNERABLE,    // Damage increased (weak element)
}
```

### 4.3 LogSource Enum

```csharp
public enum LogSource
{
    CLIENT,   // Client-side log
    SERVER    // Server-side log
}
```

### 4.4 SendLogData (Combat Telemetry)

```csharp
public static void SendLogData(
    Player sendPlayer,
    CombatLogType combatLogType,
    Player sourcePlayer,
    DamageType damageType,
    Effects.EffectType effectType,
    float damage = 0f,
    float shieldHealth = 0f)  // Only when damage applied to shield
{
    Packet.LogData logDataPacket = new Packet.LogData
    {
        packetType = (UInt16)Packet.PacketTypeOUT.LOGDATA,
        targetPlayer = sendPlayer.uniqueCode,
        playerStamina = (UInt16)sendPlayer.playerData.stamina,
        sourcePlayer = (sourcePlayer != null) ? sourcePlayer.uniqueCode : 0,
        DamageType = (byte)damageType,
        EffectType = (byte)effectType,
        LogType = (byte)combatLogType,
        damage = damage,
        shieldHealth = shieldHealth
    };
    GameManager.Instance.BroadcastPlayers(
        Serializer.Serialize<Packet.LogData>(logDataPacket), null, true);
}
```

### 4.5 WriteLogFile (File Logging)

```csharp
public static void WriteLogFile(string LogFile, LogSource logType, string writeData)
{
    // Path: ./Logs/{MatchUUID}-S.log (Server) or ./Logs/{MatchUUID}-C.log (Client)
    using StreamWriter sw = new StreamWriter(
        "./Logs/" + LogFile + (logType == LogSource.SERVER ? "-S" : "-C") + ".log",
        true);
    sw.WriteLine(writeData);
    sw.Flush();
    sw.Close();
}
```

### 4.6 GetSize (Packet Size)

```csharp
public static int GetSize(Type target)
{
    return Marshal.SizeOf(target);
}
```

---

## 5. Log File Locations

| Logger | Location | Persistence | Content |
|--------|----------|-------------|---------|
| **AUMFileLogger** | `{ProjectRoot}/AUM_Server_Log.txt` | Session | ALL logs |
| **DebugLogTracker** | `{ProjectRoot}/DebugLogs/server_session_{timestamp}.log` | Permanent | Filtered logs |
| **Utils.WriteLogFile** | `./Logs/{MatchUUID}-S.log` | Per-match | Combat logs |
| **ClientLog** | `./Logs/{MatchUUID}-C.log` | Per-match | Client debug |

---

## 6. Log Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SERVER LOGGING FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Unity Debug.Log()                                                      │
│       │                                                                 │
│       ├───────────────────┬─────────────────────────────────┐           │
│       ▼                   ▼                                 ▼           │
│  AUMFileLogger      DebugLogTracker                   Console           │
│  (ALL logs)         (Filtered by tags)                                  │
│       │                   │                                             │
│       ▼                   ▼                                             │
│  AUM_Server_Log.txt  server_session_{ts}.log                            │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Combat Event (Damage/Block/Death)                                      │
│       │                                                                 │
│       ▼                                                                 │
│  Utils.SendLogData()                                                    │
│       │                                                                 │
│       ├─────────────────────────────────┐                               │
│       ▼                                 ▼                               │
│  Packet.LogData                   ./Logs/{UUID}-S.log                   │
│  (Broadcast to clients)           (Server combat log)                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Client Debug Packet (Simulation fail, State mismatch)                  │
│       │                                                                 │
│       ▼                                                                 │
│  ClientLog.HandleClientLog()                                            │
│       │                                                                 │
│       ▼                                                                 │
│  Utils.WriteLogFile()                                                   │
│       │                                                                 │
│       ▼                                                                 │
│  ./Logs/{UUID}-C.log                                                    │
│  (Client debug log)                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `ClientLog.cs` | 39 | Client debug packet handling |
| `DebugLogTracker.cs` | 204 | Filtered debug log capture |
| `AUMFileLogger.cs` | 66 | Full session logging |
| `Utils.cs` | 57 | Combat logging utilities |

**Total: ~366 lines of code**

---

*Last Updated: January 21, 2026*
*Protocol Version: 15.0*
