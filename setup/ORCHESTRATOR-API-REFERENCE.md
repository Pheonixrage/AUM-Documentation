# AUM Orchestrator API Reference

**Quick Reference Card for Match Server Allocation**

---

## Base Configuration

```
Endpoint: http://65.109.133.129:8080
API Key:  AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8
Header:   X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8
```

---

## Quick Commands

### Health Check
```bash
curl -X GET http://65.109.133.129:8080/health \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8"
```

**Response:**
```json
{
  "status": "ok",
  "active_servers": 2,
  "available_builds": ["mac", "windows"]
}
```

---

### Allocate Mac Build Server
```bash
curl -X POST http://65.109.133.129:8080/allocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{
    "matchType": "SOLO_1V1",
    "minPlayers": 1,
    "buildType": "mac"
  }'
```

**Response:**
```json
{
  "success": true,
  "ip": "65.109.133.129",
  "port": 7800,
  "matchId": "4f141059-91dd-41ef-9d20-4b7673730fd6",
  "buildType": "mac"
}
```

---

### Allocate Windows Build Server
```bash
curl -X POST http://65.109.133.129:8080/allocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{
    "matchType": "DUO_2V2",
    "minPlayers": 2,
    "buildType": "windows"
  }'
```

---

### List Active Servers
```bash
curl -X GET http://65.109.133.129:8080/servers \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8"
```

**Response:**
```json
{
  "servers": [
    {
      "port": 7800,
      "match_id": "4f141059-91dd-41ef-9d20-4b7673730fd6",
      "build_type": "mac",
      "match_type": "SOLO_1V1"
    }
  ],
  "count": 1
}
```

---

### Deallocate Server
```bash
curl -X POST http://65.109.133.129:8080/deallocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{"port": 7800}'
```

**Response:**
```json
{
  "success": true
}
```

---

## Match Types

| Match Type | Integer Value |
|------------|--------------|
| SOLO_1V1 | 1 |
| SOLO_1V2 | 2 |
| SOLO_1V5 | 4 |
| DUO_2V2 | 8 |
| DUO_2V4 | 16 |
| TRIO_3V3 | 32 |
| TRAINING | 64 |
| TUTORIAL | 128 |
| FIRST_MATCH | 256 |

---

## Build Types

| Build Type | Path | Status |
|------------|------|--------|
| mac | /opt/mac-build/ | ✅ Deployed |
| windows | /opt/windows-build/ | 📁 Ready for deployment |

---

## Port Allocation

- **Base Port:** 7800
- **Max Servers:** 100
- **Port Range:** 7800-7899
- **Direct Server:** 7777 (not orchestrated)

---

## Error Responses

### Unauthorized
```json
{
  "error": "Unauthorized"
}
```

### Invalid Build Type
```json
{
  "error": "Invalid buildType. Available: ['mac', 'windows']"
}
```

### Build Not Deployed
```json
{
  "error": "windows build not deployed yet at /opt/windows-build/Server.x86_64"
}
```

### No Available Ports
```json
{
  "error": "No available ports"
}
```

### Server Not Found
```json
{
  "error": "Server not found"
}
```

---

## C# Client Integration

### Request Model
```csharp
[Serializable]
public class AllocateRequest
{
    public string matchType;    // "SOLO_1V1", "DUO_2V2", etc.
    public int minPlayers;      // Minimum players to start match
    public string buildType;    // "mac" or "windows"
    public string matchId;      // Optional - auto-generated if null
}
```

### Response Model
```csharp
[Serializable]
public class AllocateResponse
{
    public bool success;
    public string ip;           // Server IP (65.109.133.129)
    public int port;            // Allocated port (7800-7899)
    public string matchId;      // Unique match identifier
    public string buildType;    // Which build is running
}
```

### Example Integration
```csharp
public class OrchestratorAPI
{
    private const string BASE_URL = "http://65.109.133.129:8080";
    private const string API_KEY = "AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8";

    public static async Task<AllocateResponse> AllocateServer(AllocateRequest request)
    {
        using (UnityWebRequest www = new UnityWebRequest($"{BASE_URL}/allocate", "POST"))
        {
            www.SetRequestHeader("X-API-Key", API_KEY);
            www.SetRequestHeader("Content-Type", "application/json");

            byte[] bodyRaw = Encoding.UTF8.GetBytes(JsonUtility.ToJson(request));
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();

            await www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                return JsonUtility.FromJson<AllocateResponse>(www.downloadHandler.text);
            }
            else
            {
                Debug.LogError($"Orchestrator error: {www.error}");
                return null;
            }
        }
    }

    public static async Task<bool> DeallocateServer(int port)
    {
        var data = JsonUtility.ToJson(new { port });

        using (UnityWebRequest www = new UnityWebRequest($"{BASE_URL}/deallocate", "POST"))
        {
            www.SetRequestHeader("X-API-Key", API_KEY);
            www.SetRequestHeader("Content-Type", "application/json");

            byte[] bodyRaw = Encoding.UTF8.GetBytes(data);
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();

            await www.SendWebRequest();

            return www.result == UnityWebRequest.Result.Success;
        }
    }
}
```

### Usage
```csharp
// Allocate server
var request = new AllocateRequest
{
    matchType = "SOLO_1V1",
    minPlayers = 1,
    buildType = "mac"
};

AllocateResponse response = await OrchestratorAPI.AllocateServer(request);

if (response != null && response.success)
{
    // Connect to server
    string serverAddress = $"{response.ip}:{response.port}";
    NetworkManager.ConnectToServer(serverAddress);
}

// After match ends
await OrchestratorAPI.DeallocateServer(response.port);
```

---

## Management Commands

### Restart Orchestrator
```bash
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl restart aum-orchestrator'
```

### Check Orchestrator Status
```bash
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'systemctl status aum-orchestrator'
```

### View Orchestrator Logs
```bash
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'journalctl -u aum-orchestrator -f'
```

### Kill All Spawned Servers
```bash
SSHPASS='brahman' sshpass -e ssh root@65.109.133.129 'pkill -f "port 78"'
```

---

## Testing

### Test Full Workflow
```bash
# 1. Check health
curl -s http://65.109.133.129:8080/health \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" | jq

# 2. Allocate server
RESPONSE=$(curl -s -X POST http://65.109.133.129:8080/allocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d '{"matchType": "SOLO_1V1", "minPlayers": 1, "buildType": "mac"}')

echo $RESPONSE | jq
PORT=$(echo $RESPONSE | jq -r '.port')

# 3. List servers
curl -s http://65.109.133.129:8080/servers \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" | jq

# 4. Deallocate
curl -s -X POST http://65.109.133.129:8080/deallocate \
  -H "X-API-Key: AUM_Orch_2025_K9xMnPqR7vTwYz3J5hL8" \
  -H "Content-Type: application/json" \
  -d "{\"port\": $PORT}" | jq
```

---

## Security Notes

⚠️ **This is a development/testing setup**

For production:
1. Move API key to environment variable
2. Add rate limiting
3. Add player authentication before allocation
4. Use HTTPS with TLS termination (nginx/caddy)
5. Restrict port 8080 to trusted IPs

---

**Last Updated:** January 24, 2026
**Maintained By:** Development Team
