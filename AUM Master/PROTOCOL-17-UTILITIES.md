# PROTOCOL-17-UTILITIES.md
# Utility Systems and Helper Classes

## Overview

This document covers utility systems that provide foundational functionality across the AUM codebase, including fixed-point arithmetic, file handling, network compensation, and engine configuration.

**Key Files:**
- `Assets/Scripts/Utilities/FInt.cs` - Fixed-point integer arithmetic
- `Assets/Scripts/Utilities/FileHandler.cs` - JSON and file I/O operations
- `Assets/Scripts/Network/JitterCompensator.cs` - Network latency adjustment
- `Assets/Scripts/Utilities/Settings.cs` - Engine configuration

---

## 1. FInt (Fixed-Point Integer)

### 1.1 Overview

`FInt` is a fixed-point number implementation used for deterministic calculations across client and server. This ensures identical results regardless of floating-point hardware differences.

```csharp
[Serializable]
public struct FInt
{
    public long RawValue;
    public const int SHIFT_AMOUNT = 12;  // 4096 precision levels
    public const long One = 1 << SHIFT_AMOUNT;  // 4096
}
```

### 1.2 Core Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `SHIFT_AMOUNT` | 12 | Bit shift for fixed-point conversion |
| `One` | 4096 (1 << 12) | Represents 1.0 in fixed-point |

### 1.3 Constructors

```csharp
// From integer
public FInt(int StartingRawValue, bool UseMultiple)
{
    RawValue = (long)StartingRawValue;
    if (UseMultiple)
        RawValue = (long)StartingRawValue * (long)One;
}

// From long
public FInt(long StartingRawValue, bool UseMultiple)
{
    RawValue = StartingRawValue;
    if (UseMultiple)
        RawValue = StartingRawValue * One;
}
```

### 1.4 Static Factory Methods

```csharp
// Create from integer (recommended)
public static FInt Create(int StartingRawValue, bool UseMultiple)
{
    FInt fInt;
    fInt.RawValue = (long)StartingRawValue;
    if (UseMultiple)
        fInt.RawValue = (long)StartingRawValue * (long)One;
    return fInt;
}

// Create from long
public static FInt Create(long StartingRawValue, bool UseMultiple)
{
    FInt fInt;
    fInt.RawValue = StartingRawValue;
    if (UseMultiple)
        fInt.RawValue = StartingRawValue * One;
    return fInt;
}

// Create from double (with precision loss warning)
public static FInt Create(double DoubleValue)
{
    FInt fInt;
    DoubleValue *= One;
    fInt.RawValue = (long)Math.Round(DoubleValue);
    return fInt;
}
```

### 1.5 Arithmetic Operators

#### Addition & Subtraction
```csharp
public static FInt operator +(FInt one, FInt other)
{
    FInt fInt;
    fInt.RawValue = one.RawValue + other.RawValue;
    return fInt;
}

public static FInt operator -(FInt one, FInt other)
{
    FInt fInt;
    fInt.RawValue = one.RawValue - other.RawValue;
    return fInt;
}
```

#### Multiplication
```csharp
public static FInt operator *(FInt one, FInt other)
{
    FInt fInt;
    fInt.RawValue = (one.RawValue * other.RawValue) >> SHIFT_AMOUNT;
    return fInt;
}

public static FInt operator *(FInt one, int multi)
{
    return one * (FInt)multi;
}

public static FInt operator *(int multi, FInt one)
{
    return one * (FInt)multi;
}
```

#### Division
```csharp
public static FInt operator /(FInt one, FInt other)
{
    FInt fInt;
    fInt.RawValue = (one.RawValue << SHIFT_AMOUNT) / other.RawValue;
    return fInt;
}

public static FInt operator /(FInt one, int divisor)
{
    return one / (FInt)divisor;
}

public static FInt operator /(int divisor, FInt one)
{
    return (FInt)divisor / one;
}
```

#### Modulo
```csharp
public static FInt operator %(FInt one, FInt other)
{
    FInt fInt;
    fInt.RawValue = one.RawValue % other.RawValue;
    return fInt;
}

public static FInt operator %(FInt one, int divisor)
{
    return one % (FInt)divisor;
}

public static FInt operator %(int divisor, FInt one)
{
    return (FInt)divisor % one;
}
```

### 1.6 Comparison Operators

```csharp
public static bool operator ==(FInt one, FInt other)
{
    return one.RawValue == other.RawValue;
}

public static bool operator !=(FInt one, FInt other)
{
    return one.RawValue != other.RawValue;
}

public static bool operator >=(FInt one, FInt other)
{
    return one.RawValue >= other.RawValue;
}

public static bool operator <=(FInt one, FInt other)
{
    return one.RawValue <= other.RawValue;
}

public static bool operator >(FInt one, FInt other)
{
    return one.RawValue > other.RawValue;
}

public static bool operator <(FInt one, FInt other)
{
    return one.RawValue < other.RawValue;
}
```

### 1.7 Type Conversions

#### To FInt
```csharp
public static explicit operator FInt(int src)
{
    return FInt.Create(src, true);
}

public static explicit operator FInt(long src)
{
    return FInt.Create(src, true);
}

public static explicit operator FInt(ulong src)
{
    FInt fInt;
    fInt.RawValue = (long)src << SHIFT_AMOUNT;
    return fInt;
}
```

#### From FInt
```csharp
public static explicit operator int(FInt src)
{
    return (int)(src.RawValue >> SHIFT_AMOUNT);
}

public static explicit operator long(FInt src)
{
    return src.RawValue >> SHIFT_AMOUNT;
}

public static explicit operator float(FInt src)
{
    return (float)src.RawValue / (float)One;
}

public static explicit operator double(FInt src)
{
    return (double)src.RawValue / (double)One;
}
```

### 1.8 Utility Methods

```csharp
public int ToInt()
{
    return (int)(RawValue >> SHIFT_AMOUNT);
}

public override bool Equals(object obj)
{
    if (obj is FInt)
        return ((FInt)obj).RawValue == RawValue;
    else
        return false;
}

public override int GetHashCode()
{
    return RawValue.GetHashCode();
}

public override string ToString()
{
    return ((double)this).ToString();
}
```

### 1.9 Usage Example

```csharp
// Creating FInt values
FInt speed = FInt.Create(5, true);      // 5.0
FInt multiplier = FInt.Create(1.5);     // 1.5 (from double)

// Arithmetic
FInt result = speed * multiplier;       // 7.5

// Comparison
if (result > FInt.Create(7, true))
{
    // result > 7.0
}

// Conversion back to float for Unity
float unitySpeed = (float)result;       // 7.5f
```

---

## 2. FileHandler

### 2.1 Overview

`FileHandler` provides JSON serialization and file I/O utilities for persistent data storage.

```csharp
public static class FileHandler
{
    // File operations
    public static void SaveToJSON<T>(T toSave, string filename);
    public static T ReadFromJSON<T>(string filename);
    public static void DeleteFile(string filename);
    public static bool FileExists(string filename);
    public static bool FolderExists(string foldername);
    public static void CreateFolder(string path);
}
```

### 2.2 JSON Serialization

#### Save to JSON
```csharp
public static void SaveToJSON<T>(T toSave, string filename)
{
    Debug.Log(GetPath(filename));
    string content = JsonUtility.ToJson(toSave);
    WriteFile(GetPath(filename), content);
}
```

#### Read from JSON
```csharp
public static T ReadFromJSON<T>(string filename)
{
    string content = ReadFile(GetPath(filename));
    if (string.IsNullOrEmpty(content) || content == "{}")
    {
        return default(T);
    }
    return JsonUtility.FromJson<T>(content);
}
```

### 2.3 File Operations

#### Path Resolution
```csharp
private static string GetPath(string filename)
{
    return Application.persistentDataPath + "/" + filename;
}
```

**Paths by Platform:**
| Platform | Path |
|----------|------|
| Windows | `C:/Users/{User}/AppData/LocalLow/{Company}/{Product}/` |
| macOS | `~/Library/Application Support/{Company}/{Product}/` |
| Linux | `~/.config/unity3d/{Company}/{Product}/` |
| Android | `/data/data/{package}/files/` |
| iOS | `/var/mobile/Containers/Data/Application/{GUID}/Documents/` |

#### Write File
```csharp
private static void WriteFile(string path, string content)
{
    FileStream fileStream = new FileStream(path, FileMode.Create);
    using (StreamWriter writer = new StreamWriter(fileStream))
    {
        writer.Write(content);
    }
}
```

#### Read File
```csharp
private static string ReadFile(string path)
{
    if (File.Exists(path))
    {
        using (StreamReader reader = new StreamReader(path))
        {
            string content = reader.ReadToEnd();
            return content;
        }
    }
    return "";
}
```

### 2.4 File Management

```csharp
// Delete a file
public static void DeleteFile(string filename)
{
    File.Delete(GetPath(filename));
}

// Check if file exists
public static bool FileExists(string filename)
{
    return File.Exists(GetPath(filename));
}

// Check if folder exists
public static bool FolderExists(string foldername)
{
    return Directory.Exists(Application.persistentDataPath + "/" + foldername);
}

// Create folder
public static void CreateFolder(string path)
{
    Directory.CreateDirectory(path);
}
```

### 2.5 Usage Example

```csharp
// Define a serializable data class
[Serializable]
public class PlayerSettings
{
    public float musicVolume = 1.0f;
    public float sfxVolume = 1.0f;
    public int graphicsQuality = 2;
    public bool invertY = false;
}

// Save settings
PlayerSettings settings = new PlayerSettings();
settings.musicVolume = 0.8f;
FileHandler.SaveToJSON(settings, "player_settings.json");

// Load settings
PlayerSettings loaded = FileHandler.ReadFromJSON<PlayerSettings>("player_settings.json");
if (loaded != null)
{
    Debug.Log($"Music Volume: {loaded.musicVolume}");
}

// Check and delete
if (FileHandler.FileExists("player_settings.json"))
{
    FileHandler.DeleteFile("player_settings.json");
}
```

---

## 3. JitterCompensator

### 3.1 Overview

`JitterCompensator` provides network latency adjustment factors to smooth out gameplay across varying network conditions.

```csharp
public static class JitterCompensator
{
    public static float GetFactor(int value, int min, int max);
}
```

### 3.2 Implementation

```csharp
public static class JitterCompensator
{
    public static float GetFactor(int value, int min, int max)
    {
        if (value >= max)
            return 0.95f;      // High ping: speed up slightly
        else if (value <= min)
            return 1.05f;      // Low ping: slow down slightly
        else
            return 1f;         // Normal range: no adjustment
    }
}
```

### 3.3 Compensation Logic

| Network Condition | Ping Range | Factor | Effect |
|-------------------|------------|--------|--------|
| High Latency | `>= max` | 0.95 | Speed up 5% to catch up |
| Low Latency | `<= min` | 1.05 | Slow down 5% to not get ahead |
| Normal | `min < ping < max` | 1.0 | No adjustment |

### 3.4 Usage Context

The jitter compensator is typically used with:
- **Simulation timing** - Adjust client-side prediction speed
- **Animation speed** - Sync animations with server state
- **Movement interpolation** - Smooth position updates

```csharp
// Example usage in movement system
int currentPing = NetworkManager.Instance.GetPing();
int minPing = 20;   // Good connection
int maxPing = 150;  // Poor connection

float factor = JitterCompensator.GetFactor(currentPing, minPing, maxPing);

// Apply to movement
Vector3 movement = inputDirection * moveSpeed * factor * Time.deltaTime;
transform.position += movement;
```

### 3.5 Design Rationale

The symmetric adjustment (±5%) creates a buffer zone:

```
Ping Timeline:
│
│  0ms ─────── 20ms ─────────────────── 150ms ─────── ∞
│       [SLOW +5%]    [NORMAL 100%]     [FAST -5%]
│
│  Purpose: Keep all clients within similar simulation frame
```

---

## 4. Settings

### 4.1 Overview

`Settings` is a simple MonoBehaviour that configures engine-level settings on startup.

```csharp
public class Settings : MonoBehaviour
{
    void Start()
    {
        Application.targetFrameRate = 60;
    }
}
```

### 4.2 Frame Rate Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `targetFrameRate` | 60 | Matches 60Hz network tick rate |

### 4.3 Why 60 FPS?

The 60 FPS target is critical for AUM's networking:

1. **Network Tick Alignment** - Server runs at 60Hz, client should match
2. **Deterministic Simulation** - Fixed timestep requires consistent frame rate
3. **Input Sampling** - 60 samples/second provides responsive input
4. **Battery/Performance** - Prevents excessive frame rates on mobile

### 4.4 Placement

The `Settings` component should be attached to a persistent GameObject that exists before any gameplay begins, typically:
- On the same object as `GameManager`
- On a dedicated "Bootstrap" object
- In the main menu scene

---

## 5. Additional Utilities

### 5.1 EnumNamedArrayAttribute (Editor Utility)

Used for displaying arrays with enum names in the Unity Inspector.

```csharp
public class EnumNamedArrayAttribute : PropertyAttribute
{
    public string[] names;

    public EnumNamedArrayAttribute(Type namesEnumType)
    {
        names = Enum.GetNames(namesEnumType);
    }
}
```

**Usage:**
```csharp
public enum Elements { Fire, Water, Air, Earth, Ether }

// In MonoBehaviour
[EnumNamedArray(typeof(Elements))]
public float[] elementDamageMultipliers = new float[5];

// In Inspector, shows:
// Element 0: Fire    [1.0]
// Element 1: Water   [1.0]
// Element 2: Air     [1.0]
// Element 3: Earth   [1.0]
// Element 4: Ether   [1.0]
```

---

## 6. Utility Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          UTILITY SYSTEM FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Game Startup                                                           │
│       │                                                                 │
│       ▼                                                                 │
│  Settings.Start()                                                       │
│  ├── Application.targetFrameRate = 60                                   │
│  │                                                                      │
│  │                                                                      │
│  Network Frame Loop                                                     │
│       │                                                                 │
│       ▼                                                                 │
│  JitterCompensator.GetFactor()                                          │
│  ├── Adjusts timing based on ping                                       │
│  │                                                                      │
│  │                                                                      │
│  Deterministic Calculations                                             │
│       │                                                                 │
│       ▼                                                                 │
│  FInt Operations                                                        │
│  ├── Fixed-point math for server/client sync                            │
│  │                                                                      │
│  │                                                                      │
│  Persistent Storage                                                     │
│       │                                                                 │
│       ▼                                                                 │
│  FileHandler                                                            │
│  ├── SaveToJSON() - Write settings/data                                 │
│  └── ReadFromJSON() - Load settings/data                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `FInt.cs` | 317 | Fixed-point integer arithmetic |
| `FileHandler.cs` | 96 | JSON and file I/O utilities |
| `JitterCompensator.cs` | 18 | Network latency compensation |
| `Settings.cs` | 19 | Engine configuration |

**Total: ~450 lines of code**

---

## 8. Best Practices

### FInt Usage
- Use for all deterministic calculations that must match between client/server
- Convert to/from float only at display/Unity API boundaries
- Avoid double precision - use `Create(int, true)` when possible

### FileHandler Usage
- Always wrap in try-catch for file operations
- Check `FileExists()` before `ReadFromJSON()`
- Use consistent filenames across save/load operations

### JitterCompensator Usage
- Tune min/max values based on target audience network conditions
- Apply consistently to all time-dependent calculations
- Monitor for oscillation if values swing rapidly

### Settings Usage
- Set frame rate before any gameplay logic initializes
- Consider platform-specific frame rate targets (mobile: 30fps option)
- Match network tick rate for optimal synchronization

---

*Last Updated: January 21, 2026*
*Protocol Version: 17.0*
