# TeachSense WebSocket Integration Guide

## Overview

WebSocket connections enable real-time bidirectional communication between frontend clients and the backend. TeachSense uses Django Channels with Redis for scalable, reliable real-time updates.

## Connection Details

### Base URL
```
wss://teachsense.up.railway.app/ws/
```

### Supported Endpoints

1. **Session Consumer** - Real-time lecture updates
   ```
   wss://teachsense.up.railway.app/ws/sessions/<session_id>/
   ```

2. **Dashboard Consumer** - Live metrics and dashboard updates
   ```
   wss://teachsense.up.railway.app/ws/dashboard/
   ```

---

## Session Consumer

### Purpose
Handles real-time updates for active lecture sessions including:
- Transcript updates
- Question submissions and answers
- Student responses and feedback
- Session state changes

### Connection

**JavaScript/Web:**
```javascript
const sessionId = 1;
const token = localStorage.getItem('authToken');

const ws = new WebSocket(
  `wss://teachsense.up.railway.app/ws/sessions/${sessionId}/?token=${token}`
);

ws.onopen = (event) => {
  console.log('WebSocket connected');
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('WebSocket disconnected');
};
```

**Python:**
```python
import asyncio
import websockets
import json

async def connect_to_session(session_id, token):
    uri = f"wss://teachsense.up.railway.app/ws/sessions/{session_id}/?token={token}"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
```

### Message Format

All WebSocket messages use JSON format:

```json
{
  "type": "message_type",
  "data": {
    "field": "value"
  },
  "timestamp": "2024-05-23T10:00:00Z"
}
```

### Outgoing Messages (Client → Server)

#### 1. Transcript Update
**Event:** New transcript segment from audio processing

```json
{
  "type": "transcript_update",
  "data": {
    "segment": "Today we'll discuss advanced topics",
    "timestamp": "2024-05-23T10:05:00Z",
    "speaker": "lecturer",
    "confidence": 0.95
  }
}
```

#### 2. Question Update
**Event:** Lecturer answers a question

```json
{
  "type": "question_update",
  "data": {
    "question_id": 5,
    "answer": "The answer is...",
    "timestamp": "2024-05-23T10:10:00Z"
  }
}
```

#### 3. Response Feedback
**Event:** Lecturer provides feedback on student response

```json
{
  "type": "response_feedback",
  "data": {
    "response_id": 10,
    "feedback": "Excellent work!",
    "score": 9,
    "timestamp": "2024-05-23T10:15:00Z"
  }
}
```

#### 4. Heartbeat
**Event:** Keep-alive ping (auto-sent every 30 seconds)

```json
{
  "type": "ping",
  "timestamp": "2024-05-23T10:20:00Z"
}
```

### Incoming Messages (Server → Client)

#### Group Broadcast: Transcript.Update
Receives when lecturer's transcript is processed

```json
{
  "type": "transcript.update",
  "action": "new_segment",
  "transcript_segment": "Today we'll discuss advanced topics",
  "timestamp": "2024-05-23T10:05:00Z",
  "speaker": "lecturer"
}
```

#### Group Broadcast: Question.Updated
Receives when question is answered

```json
{
  "type": "question.updated",
  "question_id": 5,
  "action": "answered",
  "answer": "The answer is...",
  "answered_at": "2024-05-23T10:10:00Z"
}
```

#### Group Broadcast: Response.Feedback
Receives when feedback is provided

```json
{
  "type": "response.feedback",
  "response_id": 10,
  "feedback": "Excellent work!",
  "score": 9,
  "feedback_time": "2024-05-23T10:15:00Z"
}
```

#### System Message: Error
Receives on error

```json
{
  "type": "error",
  "message": "Invalid message format",
  "code": "INVALID_FORMAT"
}
```

#### Heartbeat Response: Pong
Auto-response to ping

```json
{
  "type": "pong",
  "timestamp": "2024-05-23T10:20:00Z"
}
```

---

## Dashboard Consumer

### Purpose
Provides real-time metrics and aggregated data for dashboard displays:
- Participant engagement scores
- Session metrics
- System health indicators
- Live participant list updates

### Connection

```javascript
const token = localStorage.getItem('authToken');

const dashboardWs = new WebSocket(
  `wss://teachsense.up.railway.app/ws/dashboard/?token=${token}`
);

dashboardWs.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  updateDashboard(data);
});
```

### Message Format

#### Incoming Messages (Server → Client)

##### Metrics Update
Sent every 5 seconds with latest metrics

```json
{
  "type": "metrics.update",
  "data": {
    "current_sessions": 3,
    "active_participants": 85,
    "avg_engagement": 7.8,
    "questions_pending": 4,
    "responses_submitted": 42,
    "system_health": {
      "database": "healthy",
      "cache": "healthy",
      "queue": "healthy"
    }
  },
  "timestamp": "2024-05-23T10:25:00Z"
}
```

##### Sessions Update
Sent when session list changes

```json
{
  "type": "sessions.update",
  "action": "session_started",
  "session": {
    "id": 1,
    "title": "Advanced Python",
    "status": "ongoing",
    "participant_count": 25,
    "started_at": "2024-05-23T10:00:00Z"
  }
}
```

##### Participant Update
Sent when participant joins/leaves

```json
{
  "type": "participants.update",
  "action": "joined",
  "participant": {
    "id": 123,
    "name": "John Doe",
    "role": "student",
    "joined_at": "2024-05-23T10:05:00Z",
    "engagement_score": 8.5
  }
}
```

#### Outgoing Messages (Client → Server)

##### Subscribe to Metrics
Request metric updates for specific session

```json
{
  "type": "subscribe_metrics",
  "data": {
    "session_id": 1
  }
}
```

##### Unsubscribe from Metrics
Stop receiving updates

```json
{
  "type": "unsubscribe_metrics",
  "data": {
    "session_id": 1
  }
}
```

---

## Authentication

### Token-Based

WebSocket connections require JWT token as query parameter:

```
wss://teachsense.up.railway.app/ws/sessions/1/?token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Important:** Token must be:
- Valid JWT
- Not expired
- Issued by the same backend

### Token Refresh

If token expires while connected:
1. Frontend detects token expiration
2. Obtains new token via REST API
3. Reconnects with new token

```javascript
async function reconnectWithNewToken() {
  const newToken = await refreshToken();
  ws = new WebSocket(
    `wss://teachsense.up.railway.app/ws/sessions/${sessionId}/?token=${newToken}`
  );
}
```

---

## Error Handling

### Connection Errors

```javascript
ws.addEventListener('error', (event) => {
  if (event.reason === '401') {
    // Token expired - refresh and reconnect
    refreshAndReconnect();
  } else if (event.reason === '403') {
    // Permission denied
    showError('You do not have access to this session');
  } else if (event.reason === '404') {
    // Session not found
    showError('Session not found');
  }
});
```

### Message Format Errors

Backend responds with:
```json
{
  "type": "error",
  "message": "Invalid JSON format",
  "code": "INVALID_JSON",
  "timestamp": "2024-05-23T10:30:00Z"
}
```

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `INVALID_JSON` | Message not valid JSON | Check message format |
| `INVALID_TYPE` | Unknown message type | Use valid message type |
| `UNAUTHORIZED` | Not authenticated | Provide valid token |
| `PERMISSION_DENIED` | No access to resource | Check permissions |
| `RATE_LIMITED` | Too many messages | Reduce message frequency |
| `SERVER_ERROR` | Backend error | Retry after delay |

---

## Connection Management

### Automatic Reconnection

```javascript
class WebSocketManager {
  constructor(url, maxRetries = 5) {
    this.url = url;
    this.maxRetries = maxRetries;
    this.retryCount = 0;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.addEventListener('close', () => {
      if (this.retryCount < this.maxRetries) {
        setTimeout(() => {
          this.retryCount++;
          console.log(`Reconnecting... (attempt ${this.retryCount})`);
          this.connect();
        }, 1000 * this.retryCount); // Exponential backoff
      }
    });

    this.ws.addEventListener('open', () => {
      this.retryCount = 0; // Reset counter on successful connection
    });
  }
}
```

### Heartbeat (Ping/Pong)

Backend sends ping every 30 seconds. Frontend automatically responds with pong:

```javascript
ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'ping') {
    ws.send(JSON.stringify({
      type: 'pong',
      timestamp: new Date().toISOString()
    }));
  }
});
```

### Graceful Disconnect

```javascript
function disconnect() {
  if (ws.readyState === WebSocket.OPEN) {
    ws.close(1000, 'Normal closure');
  }
}
```

---

## Performance Optimization

### Message Batching
Combine multiple updates into single message:

```javascript
let messageQueue = [];
let batchTimeout;

function queueMessage(msg) {
  messageQueue.push(msg);
  
  clearTimeout(batchTimeout);
  batchTimeout = setTimeout(() => {
    ws.send(JSON.stringify({
      type: 'batch',
      messages: messageQueue,
      timestamp: new Date().toISOString()
    }));
    messageQueue = [];
  }, 100); // Send every 100ms or when queue has 10 items
}
```

### Selective Subscriptions
Only subscribe to needed updates:

```javascript
// Subscribe only to metrics for specific session
ws.send(JSON.stringify({
  type: 'subscribe',
  data: {
    channels: ['metrics', 'participants'],
    session_id: 1
  }
}));
```

---

## Examples

### Real-time Transcript Display

```javascript
const sessionId = 1;
const ws = new WebSocket(
  `wss://teachsense.up.railway.app/ws/sessions/${sessionId}/?token=${token}`
);

ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'transcript.update') {
    const transcriptDiv = document.getElementById('transcript');
    transcriptDiv.innerHTML += `
      <p>
        <strong>${data.transcript_segment.speaker}:</strong>
        ${data.transcript_segment.text}
        <small>(${new Date(data.timestamp).toLocaleTimeString()})</small>
      </p>
    `;
    transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
  }
});
```

### Dashboard Metrics Display

```javascript
const dashboardWs = new WebSocket(
  `wss://teachsense.up.railway.app/ws/dashboard/?token=${token}`
);

dashboardWs.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'metrics.update') {
    document.getElementById('participants').textContent = 
      data.data.active_participants;
    document.getElementById('engagement').textContent = 
      data.data.avg_engagement.toFixed(1);
    document.getElementById('pending-questions').textContent = 
      data.data.questions_pending;
  }
});
```

---

## Troubleshooting

### Connection Fails
- Check token is valid and not expired
- Verify URL is correct
- Check CORS and firewall settings
- Ensure wss:// protocol is used (not ws://)

### Messages Not Received
- Verify connection state: `ws.readyState === WebSocket.OPEN`
- Check message format is valid JSON
- Monitor network tab in browser devtools

### High Latency
- Check network conditions
- Reduce message frequency
- Consider message batching
- Monitor Redis logs on backend
