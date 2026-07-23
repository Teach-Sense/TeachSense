# TeachSense Integration Documentation

Complete integration guide for developers building with TeachSense backend API.

## Quick Navigation

### Core Documentation

- **[OVERVIEW](./integration/OVERVIEW.md)** - Architecture overview and quick start
- **[API_ENDPOINTS](./integration/API_ENDPOINTS.md)** - Complete REST API reference
- **[WEBSOCKET](./integration/WEBSOCKET.md)** - Real-time WebSocket integration
- **[HARDWARE](./integration/HARDWARE.md)** - Hardware device integration guide
- **[AUTHENTICATION](./integration/AUTHENTICATION.md)** - JWT authentication flow
- **[ERROR_HANDLING](./integration/ERROR_HANDLING.md)** - Error codes and responses

---

## Getting Started

### 1. Authentication

All API calls require JWT token. Get one by logging in:

```bash
curl -X POST https://teachsense.onrender.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

See [AUTHENTICATION.md](./integration/AUTHENTICATION.md) for details.

### 2. REST API

Create a session and manage lecture data:

```bash
# Create session
curl -X POST https://teachsense.onrender.com/api/sessions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Lecture"}'

# List sessions
curl https://teachsense.onrender.com/api/sessions/ \
  -H "Authorization: Bearer <token>"
```

See [API_ENDPOINTS.md](./integration/API_ENDPOINTS.md) for full reference.

### 3. WebSocket Real-Time

Subscribe to live updates:

```javascript
const ws = new WebSocket(
  'wss://teachsense.onrender.com/ws/sessions/1/?token=<token>'
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

See [WEBSOCKET.md](./integration/WEBSOCKET.md) for details.

### 4. Hardware Integration

Connect audio devices:

```bash
# Register device
curl -X POST https://teachsense.onrender.com/api/devices/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Classroom Mic",
    "type":"audio_input",
    "protocol":"websocket"
  }'
```

See [HARDWARE.md](./integration/HARDWARE.md) for full details.

---

## API Base URL

```
https://teachsense.onrender.com/api
```

## WebSocket Base URL

```
wss://teachsense.onrender.com/ws
```

## Interactive Docs

- **Swagger UI**: https://teachsense.onrender.com/docs/
- **OpenAPI Schema**: https://teachsense.onrender.com/api/schema/
- **Health Check**: https://teachsense.onrender.com/api/health/

---

## Common Code Examples

### Frontend: React

```javascript
import { useEffect, useState } from 'react';

function LectureViewer({ sessionId }) {
  const [transcript, setTranscript] = useState('');
  const [token, setToken] = useState(localStorage.getItem('authToken'));

  useEffect(() => {
    const ws = new WebSocket(
      `wss://teachsense.onrender.com/ws/sessions/${sessionId}/?token=${token}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'transcript.update') {
        setTranscript(prev => prev + ' ' + data.transcript_segment);
      }
    };

    ws.onerror = (error) => console.error('WebSocket error:', error);

    return () => ws.close();
  }, [sessionId, token]);

  return <div className="transcript">{transcript}</div>;
}
```

### Backend: Python

```python
import requests
import asyncio
import websockets
import json

class TeachSenseClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.token = None
        self.authenticate(email, password)

    def authenticate(self, email, password):
        response = requests.post(
            f'{self.base_url}/api/auth/login/',
            json={'email': email, 'password': password}
        )
        self.token = response.json()['access']

    def create_session(self, title):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.post(
            f'{self.base_url}/api/sessions/',
            headers=headers,
            json={'title': title}
        )
        return response.json()

    async def connect_websocket(self, session_id):
        ws_url = f'wss://teachsense.onrender.com/ws/sessions/{session_id}/?token={self.token}'
        async with websockets.connect(ws_url) as websocket:
            async for message in websocket:
                data = json.loads(message)
                print(f'Received: {data}')

# Usage
client = TeachSenseClient(
    'https://teachsense.onrender.com',
    'user@example.com',
    'password123'
)
session = client.create_session('My Lecture')
asyncio.run(client.connect_websocket(session['id']))
```

### Hardware: Arduino with WiFi

```cpp
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

WiFiClient wifiClient;
WebSocketsClient webSocket;
String deviceToken = "device_token_xyz123";

void setup() {
  WiFi.begin(ssid, password);
  
  webSocket.setAuthorization("Bearer", deviceToken);
  webSocket.beginSSL("teachsense.onrender.com", 443, "/ws/devices/audio_01/");
  webSocket.onEvent(webSocketEvent);
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      {
        StaticJsonDocument<256> doc;
        doc["type"] = "handshake";
        doc["device_type"] = "audio_input";
        doc["timestamp"] = getTimestamp();
        
        String msg;
        serializeJson(doc, msg);
        webSocket.sendTXT(msg);
      }
      break;
    
    case WStype_TEXT:
      {
        StaticJsonDocument<256> doc;
        deserializeJson(doc, payload);
        handleMessage(doc);
      }
      break;
  }
}

void sendAudioFrame(uint8_t* audioData, size_t length) {
  StaticJsonDocument<512> doc;
  doc["type"] = "audio_frame";
  doc["device_id"] = 15;
  doc["timestamp"] = getTimestamp();
  doc["data_base64"] = base64Encode(audioData, length);
  
  String msg;
  serializeJson(doc, msg);
  webSocket.sendTXT(msg);
}
```

---

## Feature Support Matrix

| Feature | REST | WebSocket | Hardware |
|---------|------|-----------|----------|
| Sessions | ✅ | ✅ | - |
| Transcripts | ✅ | ✅ | ✅ |
| Questions | ✅ | ✅ | - |
| Responses | ✅ | ✅ | - |
| Devices | ✅ | ✅ | ✅ |
| Analytics | ✅ | ✅ | - |
| Dashboards | ✅ | ✅ | - |

---

## Troubleshooting

### Can't Connect to WebSocket
- Verify token hasn't expired: use `/api/auth/refresh/`
- Check URL format: `wss://` not `ws://`
- Verify session ID exists and you have access
- Check browser console for CORS errors

### API Returns 401 Unauthorized
- Ensure token is in `Authorization: Bearer <token>` header
- Token may have expired (24-hour expiry)
- Use `/api/auth/refresh/` to get new token

### Hardware Device Won't Register
- Verify device key is correct
- Check device is on same network
- Review device registration logs
- Try device restart

---

## Performance Limits

- **Rate Limit**: 100 requests/minute per user
- **WebSocket Message Size**: 16KB maximum
- **File Upload Size**: 500MB maximum
- **Concurrent Connections**: Unlimited per user
- **Response Time**: <500ms p95

---

## Support & Resources

- **Documentation**: This file and linked guides
- **API Schema**: https://teachsense.onrender.com/api/schema/
- **Interactive UI**: https://teachsense.onrender.com/docs/
- **Status**: https://teachsense.onrender.com/api/health/
- **Issues**: Contact development team

---

## Versioning

- API Version: 1.0
- Schema Version: 2024-05-23
- Last Updated: May 2026

---

*For backend developers integrating with TeachSense. For questions, see `/api/docs/` endpoint.*
