# TeachSense API Endpoints Documentation

## Base URL
```
https://teachsense.up.railway.app/api
```

## Authentication

All endpoints (except login) require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## 1. Authentication Endpoints

### POST `/auth/login/`
Login user and receive JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "lecturer"
  }
}
```

### POST `/auth/refresh/`
Refresh expired JWT token.

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### POST `/auth/logout/`
Logout and invalidate token.

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

## 2. Sessions (Lecture) Endpoints

### GET `/sessions/`
List all lecture sessions.

**Query Parameters:**
- `status` - Filter by status: `ongoing`, `completed`, `scheduled`
- `lecturer_id` - Filter by lecturer
- `limit` - Results per page (default: 20)
- `offset` - Pagination offset

**Response (200):**
```json
{
  "count": 42,
  "next": "https://...?offset=20",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Advanced Python",
      "started_at": "2024-05-23T10:00:00Z",
      "ended_at": null,
      "status": "ongoing",
      "participant_count": 25
    }
  ]
}
```

### POST `/sessions/`
Create a new lecture session.

**Request:**
```json
{
  "title": "Introduction to Django",
  "description": "Learn Django basics",
  "scheduled_at": "2024-05-23T14:00:00Z"
}
```

**Response (201):**
```json
{
  "id": 43,
  "title": "Introduction to Django",
  "status": "scheduled",
  "session_code": "ABC123XYZ",
  "ws_url": "wss://teachsense.up.railway.app/ws/sessions/43/"
}
```

### GET `/sessions/{id}/`
Get specific session details.

**Response (200):**
```json
{
  "id": 1,
  "title": "Advanced Python",
  "status": "ongoing",
  "started_at": "2024-05-23T10:00:00Z",
  "participant_count": 25,
  "questions_count": 12,
  "responses_count": 35,
  "transcript": "Lorem ipsum...",
  "ws_url": "wss://teachsense.up.railway.app/ws/sessions/1/"
}
```

### PATCH `/sessions/{id}/`
Update session (lecturer only).

**Request:**
```json
{
  "status": "completed"
}
```

**Response (200):**
```json
{
  "id": 1,
  "status": "completed",
  "ended_at": "2024-05-23T11:00:00Z"
}
```

---

## 3. Transcripts Endpoints

### GET `/transcripts/`
List transcripts for current user's sessions.

**Query Parameters:**
- `session_id` - Filter by session
- `status` - `pending`, `processing`, `completed`

**Response (200):**
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "session_id": 1,
      "content": "Today we'll discuss...",
      "timestamp": "2024-05-23T10:05:00Z",
      "speaker": "lecturer",
      "status": "completed"
    }
  ]
}
```

### POST `/transcripts/`
Create new transcript entry.

**Request:**
```json
{
  "session_id": 1,
  "content": "Transcript text",
  "speaker": "lecturer",
  "timestamp": "2024-05-23T10:05:00Z"
}
```

**Response (201):**
```json
{
  "id": 101,
  "session_id": 1,
  "content": "Transcript text",
  "created_at": "2024-05-23T10:05:30Z"
}
```

---

## 4. Questions Endpoints

### GET `/questions/`
List questions in sessions.

**Query Parameters:**
- `session_id` - Filter by session
- `status` - `pending`, `answered`, `archived`

**Response (200):**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "session_id": 1,
      "text": "How do I...?",
      "asker_name": "John Doe",
      "status": "pending",
      "upvotes": 5,
      "created_at": "2024-05-23T10:10:00Z"
    }
  ]
}
```

### POST `/questions/`
Submit a new question.

**Request:**
```json
{
  "session_id": 1,
  "text": "How do I implement caching?"
}
```

**Response (201):**
```json
{
  "id": 51,
  "session_id": 1,
  "text": "How do I implement caching?",
  "status": "pending",
  "created_at": "2024-05-23T10:15:00Z"
}
```

### PUT `/questions/{id}/`
Answer a question (lecturer only).

**Request:**
```json
{
  "answer": "Caching can be implemented using...",
  "status": "answered"
}
```

**Response (200):**
```json
{
  "id": 1,
  "answer": "Caching can be implemented using...",
  "answer_timestamp": "2024-05-23T10:20:00Z",
  "status": "answered"
}
```

---

## 5. Responses Endpoints

### GET `/responses/`
List student responses.

**Query Parameters:**
- `session_id` - Filter by session
- `question_id` - Filter by question

**Response (200):**
```json
{
  "count": 120,
  "results": [
    {
      "id": 1,
      "question_id": 5,
      "student_id": 10,
      "text": "I think the answer is...",
      "status": "submitted",
      "feedback": null,
      "created_at": "2024-05-23T10:25:00Z"
    }
  ]
}
```

### POST `/responses/`
Submit a response to a question.

**Request:**
```json
{
  "question_id": 5,
  "text": "I think the answer is..."
}
```

**Response (201):**
```json
{
  "id": 121,
  "question_id": 5,
  "text": "I think the answer is...",
  "status": "submitted"
}
```

### PATCH `/responses/{id}/`
Provide feedback on a response.

**Request:**
```json
{
  "feedback": "Great attempt!",
  "score": 8
}
```

---

## 6. Devices Endpoints

### GET `/devices/`
List connected devices.

**Response (200):**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Lecture Hall Microphone",
      "type": "audio_input",
      "status": "connected",
      "protocol": "websocket",
      "last_heartbeat": "2024-05-23T10:59:00Z"
    }
  ]
}
```

### POST `/devices/`
Register a new device.

**Request:**
```json
{
  "name": "Student Mic",
  "type": "audio_input",
  "protocol": "websocket",
  "device_key": "device_secret_key"
}
```

**Response (201):**
```json
{
  "id": 6,
  "name": "Student Mic",
  "status": "pending",
  "auth_token": "device_auth_token_abc123"
}
```

### PATCH `/devices/{id}/`
Update device status.

**Request:**
```json
{
  "status": "active"
}
```

---

## 7. Analytics Endpoints

### GET `/analytics/`
Get session analytics and metrics.

**Query Parameters:**
- `session_id` - Required
- `metric_type` - `engagement`, `performance`, `participation`

**Response (200):**
```json
{
  "session_id": 1,
  "total_participants": 25,
  "avg_engagement_score": 7.8,
  "questions_asked": 12,
  "responses_submitted": 35,
  "avg_response_time": 45,
  "participation_rate": 0.92
}
```

---

## 8. Dashboards Endpoints

### GET `/dashboards/`
Get user dashboards.

**Response (200):**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "My Teaching Dashboard",
      "type": "lecturer",
      "widgets": [...]
    }
  ]
}
```

### GET `/dashboards/{id}/metrics/`
Get real-time metrics for dashboard.

**Response (200):**
```json
{
  "current_sessions": 3,
  "active_participants": 95,
  "avg_engagement": 8.2,
  "system_health": "green"
}
```

---

## 9. Health & Status

### GET `/health/`
Check backend health status.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-05-23T11:00:00Z",
  "database": "connected",
  "cache": "connected",
  "version": "1.0.0"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "errors": {
    "email": ["This field is required."]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 429 Too Many Requests
```json
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}
```

### 500 Server Error
```json
{
  "detail": "Internal server error. Please try again later."
}
```

---

## Rate Limiting

- **General Endpoints**: 100 requests/minute
- **Authentication**: 5 requests/minute
- **File Upload**: 10 requests/minute

Rate limit headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1716462000
```

---

## Pagination

List endpoints support pagination:
```
GET /api/sessions/?limit=20&offset=40
```

Response includes:
```json
{
  "count": 1000,
  "next": "https://...?offset=60",
  "previous": "https://...?offset=20",
  "results": [...]
}
```
