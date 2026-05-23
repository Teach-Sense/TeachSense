# TeachSense Frontend + Hardware Integration Guide

This guide explains how to connect the frontend, lecturer/student clients, and ESP32 hardware devices to the TeachSense backend.

## 1) What the backend exposes

TeachSense exposes three major integration surfaces:

1. **REST API** for authentication, sessions, transcripts, questions, responses, devices, analytics, and dashboards.
2. **WebSocket endpoints** configured in ASGI for real-time session/dashboard updates.
3. **Hardware sync endpoints** for device registration and device-to-cloud synchronization.

---

## 2) Base URLs and environments

### Local development
- Backend: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Health check: `http://127.0.0.1:8000/api/health/`

### Frontend origins
Typical local frontend ports:
- Lecturer frontend: `http://localhost:3000`
- Student frontend: `http://localhost:3001`

### WebSocket base
- Local WebSocket: `ws://127.0.0.1:8000`
- Secure WebSocket in production: `wss://your-domain.com`

---

## 3) Authentication model

TeachSense uses **JWT Bearer tokens** for authenticated REST requests.

### JWT flow
1. User registers or logs in.
2. Backend returns `access` and `refresh` tokens.
3. Frontend stores the tokens securely.
4. Frontend sends the access token in the `Authorization` header.
5. When the access token expires, use the refresh token to get a new access token.

### Required header for authenticated REST calls
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Role model
The backend uses `user.role` as the canonical role field:
- `lecturer`
- `student`

Some compatibility helpers still exist, but frontend code should rely on `role`.

---

## 4) Frontend integration pattern

### Lecturer frontend responsibilities
The lecturer frontend should handle:
- registration/login
- session creation and management
- transcript upload
- question review
- response review
- analytics and dashboard overview
- live session monitoring through websocket updates

### Student frontend responsibilities
The student frontend should handle:
- JWT login/session state
- viewing assigned sessions
- answering questions
- reading published responses or summaries
- live updates through websocket subscription when available

### Hardware frontend responsibilities
The hardware device or device firmware should handle:
- device registration
- device token storage
- periodic sync pull from backend
- response submission to backend
- heartbeat/status updates

---

## 5) REST API endpoint catalogue

All endpoints below are rooted at `/api/` unless otherwise stated.

### 5.1 Health and status

#### `GET /api/health/`
Returns a runtime readiness snapshot for:
- database
- Redis
- Celery
- storage
- active Anthropic/Mistral modes
- rate limit configuration

Use this endpoint for:
- frontend startup health checks
- deployment readiness checks
- hardware gateway health checks
- monitoring dashboards

Example response fields:
- `ok`
- `environment`
- `database_engine`
- `services.database`
- `services.redis`
- `services.celery`
- `services.storage`
- `modes.anthropic`
- `modes.mistral`
- `rate_limits.*`

---

### 5.2 Authentication and user profile

#### `POST /api/auth/register/`
Create a new user account.

Use from frontend:
- lecturer sign-up form
- student sign-up form

Request body typically includes:
- name fields
- email/username
- password
- role

Returns:
- user profile
- access token
- refresh token

#### `POST /api/auth/login/`
Authenticate user and return tokens.

Use from frontend:
- login page

Returns:
- `access`
- `refresh`
- user details depending on serializer response

#### `POST /api/auth/token/`
Standard JWT obtain pair endpoint.

Use when frontend wants the standard SimpleJWT obtain flow.

#### `POST /api/auth/token/refresh/`
Exchange a refresh token for a new access token.

#### `POST /api/auth/logout/`
Client-side logout placeholder.

Use from frontend to clear local session state and tokens.

#### `GET /api/auth/profile/`
Get current authenticated user profile.

#### `PUT /api/auth/profile/`
Update current authenticated user profile.

#### `POST /api/auth/change-password/`
Change the current user password.

Headers required:
```http
Authorization: Bearer <access_token>
```

---

### 5.3 Sessions

#### `GET /api/sessions/`
List sessions visible to the authenticated user.

Behavior:
- lecturer sees their own sessions
- student sees sessions assigned through lecturer profile

#### `POST /api/sessions/`
Create a new session.

Allowed for:
- lecturers only

#### `GET /api/sessions/<session_id>/`
Read session details.

#### `PUT /api/sessions/<session_id>/`
Update session details.

Allowed for:
- lecturers only

#### `DELETE /api/sessions/<session_id>/`
Delete a session.

Allowed for:
- lecturers only

---

### 5.4 Transcripts

#### `GET /api/sessions/<session_id>/transcripts/`
List transcripts for a session.

Allowed for:
- session lecturer

#### `POST /api/sessions/<session_id>/transcripts/`
Upload a transcript for a session.

Allowed for:
- session lecturer

Used by:
- lecturer frontend when an audio file or transcript payload is submitted
- post-processing workflows after lecture capture

#### `GET /api/transcripts/<transcript_id>/`
Read transcript details.

Allowed for:
- lecturer with access to the session

Frontend usage:
- transcript viewer page
- transcript inspection and correction UI

---

### 5.5 Questions

#### `GET /api/sessions/<session_id>/questions/`
List questions belonging to a session.

Allowed for:
- lecturer with access to the session

#### `GET /api/questions/<question_id>/`
Read a single question.

Allowed for:
- lecturer with access to the question/session

Frontend usage:
- lecturer question management page
- student question display page if needed

---

### 5.6 Responses

#### `GET /api/sessions/<session_id>/questions/<question_id>/responses/`
List responses for a specific question in a session.

Access pattern:
- lecturer can inspect all responses
- student access is constrained by the backend rules

#### `POST /api/sessions/<session_id>/questions/<question_id>/responses/`
Create a response for a question.

Allowed for:
- student role

#### `GET /api/responses/<response_id>/`
Read a response.

#### `PUT /api/responses/<response_id>/`
Update a response.

#### `DELETE /api/responses/<response_id>/`
Delete a response.

#### `GET /api/sessions/<session_id>/responses/`
List all responses for a session.

Allowed for:
- session lecturer

Frontend usage:
- student answer form
- lecturer response review panel
- analytics aggregation

---

### 5.7 Devices

#### `POST /api/devices/register/`
Register a new hardware device.

Request body is validated by the device serializer and returns:
- `device_id`
- `device_token`
- `sync_interval_seconds`
- `status`

This is the first step for any hardware device.

#### `GET /api/devices/sync/`
Pull cloud data to the device.

Requires device authentication, not JWT.

Use this for:
- firmware polling
- pulling active session metadata
- pulling questions that need to be shown or processed

Returns:
- active sessions
- questions
- sync metadata

#### `POST /api/devices/sync/`
Push device data to the cloud.

Use this for:
- response uploads from device firmware
- hardware event reporting
- future command acknowledgements

#### `GET /api/devices/`
List all registered devices.

Allowed for:
- admin users only

#### `GET /api/devices/<device_id>/`
Get device details.

Allowed for:
- admin users only

#### `GET /api/devices/<device_id>/status/`
Get current device status.

Allowed for:
- admin users only

---

### 5.8 Analytics

#### `GET /api/analytics/sessions/<session_id>/`
Fetch analytics for a single session.

Use from:
- lecturer dashboard
- analytics screen

Returns:
- question counts
- response counts
- accuracy/completeness/clarity metrics
- effectiveness score
- insights

---

### 5.9 Dashboards

#### `GET /api/dashboards/overview/`
Return a compact overview of recent sessions.

Use from:
- lecturer dashboard home
- admin overview panel

Returns fields like:
- session title
- status
- transcript readiness
- summary readiness
- question readiness
- evaluation readiness
- published state
- teaching effectiveness score
- analytics summary

---

## 6) WebSocket integration

The ASGI layer configures the following websocket paths:

- `ws/sessions/<session_id>/`
- `ws/dashboard/`

### Important note
The websocket routes are configured in ASGI, but the consumer implementation must also be present and imported correctly for live websocket traffic to work.

### Recommended frontend usage
Use websockets for:
- real-time session state updates
- live question delivery
- result publishing notifications
- dashboard refresh events

### Example connection flow
1. Frontend opens websocket after JWT login.
2. Frontend subscribes to session-specific path.
3. Backend pushes session state or scoring updates.
4. Frontend updates the UI without reloading.

### Browser websocket example
```javascript
const socket = new WebSocket(`ws://127.0.0.1:8000/ws/sessions/${sessionId}/`);

socket.onopen = () => {
  console.log('Session websocket connected');
};

socket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  console.log('Received update:', payload);
};

socket.onclose = () => {
  console.log('Session websocket closed');
};
```

---

## 7) Authentication storage recommendations for frontend

### Browser apps
Store tokens carefully:
- prefer secure, httpOnly cookies if you add that flow later
- if using local storage during development, treat it as temporary only
- refresh access tokens before expiry

### Recommended request wrapper
Every authenticated request should:
- attach the access token
- detect `401 Unauthorized`
- refresh token when needed
- retry once after refresh

---

## 8) Hardware integration guide

### 8.1 Device registration
Each device must first register with:

`POST /api/devices/register/`

The backend returns a `device_token`. The device should store it securely and reuse it for all subsequent sync requests.

### 8.2 Device authentication
Hardware requests should use the device token via the backend's expected device auth mechanism.

If your firmware sends custom headers, keep them consistent with the backend device authenticator.

Typical pattern:
- device ID in payload or header
- device token in header
- JSON payload for sync data

### 8.3 Sync behavior
Use `GET /api/devices/sync/` to pull data from the cloud.

Use `POST /api/devices/sync/` to push data back.

The backend currently expects device sync traffic to support:
- polling
- live data pull
- pushing responses/results
- status updates

### 8.4 Heartbeat / status
A device should call sync regularly to stay online. The backend tracks:
- `last_sync`
- `last_sync_status`
- online/offline state

### 8.5 Suggested firmware loop
1. Boot device.
2. Register once.
3. Save `device_id` and `device_token`.
4. Periodically call sync pull.
5. Process returned sessions/questions.
6. Push results back.
7. Repeat on interval.

### 8.6 Example device sync payload
```json
{
  "responses": [
    {
      "question_id": 12,
      "session_id": 4,
      "student_id": 7,
      "answer": "Student answer text",
      "score": 0.82
    }
  ]
}
```

---

## 9) Frontend implementation checklist

### Lecturer frontend
- login/register screen
- token storage and refresh handler
- session list page
- session create/edit page
- transcript upload page
- question review page
- response review page
- dashboard overview page
- analytics page
- websocket listener for live updates

### Student frontend
- login/register screen
- session list page
- question answer page
- response submission form
- websocket listener for live session announcements

### Shared frontend utilities
- API client with JWT injection
- refresh-token retry logic
- global error handler
- pagination helper
- loading and retry states

---

## 10) Request/response conventions

### Success responses
The backend uses a standardized response wrapper in many places.
Expect responses to include:
- `success` or `ok` style flags
- `message`
- `data`
- pagination metadata when applicable

### Common error codes
- `400` validation failure
- `401` unauthorized
- `403` forbidden
- `404` not found
- `429` rate limit exceeded
- `500` server error

### Rate limiting
The backend includes rate limit settings and a rate limit decorator.
For frontend behavior:
- show a friendly message on `429`
- respect the `Retry-After` header
- do not aggressively retry

---

## 11) Suggested frontend request examples

### Login
```javascript
await fetch('/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password }),
});
```

### Authenticated request
```javascript
await fetch('/api/sessions/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
});
```

### Device registration
```javascript
await fetch('/api/devices/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ device_name: 'ESP32 Classroom Unit 1' }),
});
```

---

## 12) Recommended integration order

1. Verify `/api/health/` is green.
2. Implement auth flow in frontend.
3. Fetch `/api/auth/profile/` after login.
4. Build session list/detail screens.
5. Build transcript upload flow for lecturers.
6. Build question and response screens.
7. Register hardware devices.
8. Wire device sync loop.
9. Add websocket listeners for live updates.
10. Add analytics and dashboard views.

---

## 13) Deployment notes

### Local development
- use SQLite
- use local Redis
- keep `USE_B2=false`
- run backend on port `8000`

### Production
- use PostgreSQL or MySQL
- use Upstash Redis or another production Redis instance
- set `USE_B2=true` if using Backblaze B2 storage
- ensure CORS and CSRF origins are correctly set
- ensure websocket host supports `wss://`

---

## 14) Important caveats

- The backend currently exposes websocket paths in ASGI, but websocket consumers must be present for live traffic.
- Device synchronization is implemented as a polling/sync model, not yet as a fully event-driven device push model.
- Device admin endpoints are restricted to superusers.
- Some workflows are intentionally lecturer-only to protect session data.

---

## 15) Quick endpoint summary

### Auth
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/logout/`
- `GET /api/auth/profile/`
- `PUT /api/auth/profile/`
- `POST /api/auth/change-password/`

### Sessions
- `GET /api/sessions/`
- `POST /api/sessions/`
- `GET /api/sessions/<session_id>/`
- `PUT /api/sessions/<session_id>/`
- `DELETE /api/sessions/<session_id>/`

### Transcripts
- `GET /api/sessions/<session_id>/transcripts/`
- `POST /api/sessions/<session_id>/transcripts/`
- `GET /api/transcripts/<transcript_id>/`

### Questions
- `GET /api/sessions/<session_id>/questions/`
- `GET /api/questions/<question_id>/`

### Responses
- `GET /api/sessions/<session_id>/questions/<question_id>/responses/`
- `POST /api/sessions/<session_id>/questions/<question_id>/responses/`
- `GET /api/responses/<response_id>/`
- `PUT /api/responses/<response_id>/`
- `DELETE /api/responses/<response_id>/`
- `GET /api/sessions/<session_id>/responses/`

### Devices
- `POST /api/devices/register/`
- `GET /api/devices/sync/`
- `POST /api/devices/sync/`
- `GET /api/devices/`
- `GET /api/devices/<device_id>/`
- `GET /api/devices/<device_id>/status/`

### Analytics and dashboards
- `GET /api/analytics/sessions/<session_id>/`
- `GET /api/dashboards/overview/`

### Health
- `GET /api/health/`

---

## 16) Final recommendation

If you are wiring the frontend first, start with:
1. `POST /api/auth/login/`
2. `GET /api/auth/profile/`
3. `GET /api/sessions/`
4. `GET /api/dashboards/overview/`
5. `GET /api/health/`

If you are wiring the hardware first, start with:
1. `POST /api/devices/register/`
2. `GET /api/devices/sync/`
3. `POST /api/devices/sync/`
4. `GET /api/health/`

This order gives you the fastest path to a working end-to-end integration.
