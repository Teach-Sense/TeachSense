# TeachSense Integration Checklist: Frontend + Hardware

Before connecting frontend and hardware, implement these remaining pieces:

---

## Priority 1: Core REST Endpoints

### Missing Lecturer/Session Management
```
POST   /api/sessions/                    Create new session
GET    /api/sessions/                    List lecturer's sessions
GET    /api/sessions/<id>/               Get session details
PUT    /api/sessions/<id>/               Update session metadata
POST   /api/sessions/<id>/transcripts/   Upload transcript
```

### Missing Question/Response Endpoints
```
GET    /api/sessions/<id>/questions/     List session questions
POST   /api/sessions/<id>/responses/     Submit student response
GET    /api/sessions/<id>/responses/     Get session responses
GET    /api/sessions/<id>/evaluations/   Get all evaluations
```

**Required Files to Create:**
- `apps/sessions/api/views.py` → SessionViewSet (CRUD)
- `apps/sessions/api/urls.py`
- `apps/questions/api/views.py` → QuestionViewSet (list)
- `apps/responses/api/views.py` → ResponseViewSet (create/list)

---

## Priority 2: Authentication & Authorization

### Current State: ❓ (Need to verify)
```bash
grep -r "class.*Authentication" config/ common/
grep -r "TokenAuthentication\|JWTAuthentication" requirements.txt
```

### Add If Missing:
```python
# requirements.txt
djangorestframework-simplejwt>=5.0.0
```

### Implement:
- `common/permissions.py` → IsLecturer, IsStudent, IsDeviceAuthenticated
- `config/settings.py` → REST_FRAMEWORK auth classes
- `apps/users/api/views.py` → LoginView, RefreshTokenView

**Files to Add:**
```
apps/users/
├─ api/
│  ├─ views.py        (LoginView, RefreshTokenView)
│  ├─ serializers.py  (UserSerializer, TokenSerializer)
│  └─ urls.py
```

---

## Priority 3: Transcript Upload Endpoint

### Current: `apps/transcripts/` exists but need full REST integration

**Create:**
```python
# apps/transcripts/api/views.py
class TranscriptUploadView(APIView):
    """
    POST /api/sessions/<session_id>/transcripts/
    Body: {"transcript_text": "...", "confidence_score": 0.95}
    Returns: {"id": 1, "status": "received", "processing_at": "2026-05-21T10:00:00Z"}
    """
    def post(self, request, session_id):
        # Validate session ownership (lecturer)
        # Create Transcript record
        # Queue process_lecture_session task
        # Return success with task ID for polling

# apps/transcripts/api/urls.py
path("sessions/<int:session_id>/transcripts/", TranscriptUploadView.as_view())
```

---

## Priority 4: Response Submission Endpoint

### Create:
```python
# apps/responses/api/views.py
class ResponseCreateView(APIView):
    """
    POST /api/sessions/<session_id>/questions/<question_id>/responses/
    Body: {"response_text": "...", "audio_file": <file>}
    Returns: {"id": 1, "question_id": 1, "status": "submitted"}
    """
    def post(self, request, session_id, question_id):
        # Validate student is enrolled in session
        # Validate question belongs to session
        # Create Response record
        # Return success

# apps/responses/api/urls.py
path("sessions/<int:session_id>/questions/<int:question_id>/responses/", ResponseCreateView.as_view())
```

---

## Priority 5: Device Registration & Sync

### Create Device Management
```python
# apps/devices/models.py (or create if missing)
class Device(models.Model):
    """Physical classroom device"""
    device_id = models.CharField(unique=True)  # MAC address or serial
    device_name = models.CharField()
    location = models.CharField()
    device_token = models.CharField()  # For auth
    last_sync = models.DateTimeField()
    
    class Meta:
        verbose_name = "Classroom Device"

# apps/devices/api/views.py
class DeviceRegisterView(APIView):
    """
    POST /api/devices/register/
    Body: {"device_id": "...", "device_name": "Classroom-01"}
    Returns: {"device_token": "...", "sync_interval": 30}
    """
    def post(self, request):
        # Register new device
        # Generate device token
        # Return config

class DevicePullView(APIView):
    """
    GET /api/devices/sync/
    Returns: {"sessions": [...], "transcripts_to_upload": [...], "last_sync": "..."}
    """
    def get(self, request):
        # Poll for new data to process
        # Return any pending sessions/questions
```

---

## Priority 6: CORS Configuration

### Add to `config/settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",        # Frontend dev
    "http://frontend.local:3000",
    "https://app.teachsense.io",    # Production
    "https://devices.teachsense.io", # Device network
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-device-token",  # Custom header for device auth
]
```

**Install:**
```bash
pip install django-cors-headers
```

---

## Priority 7: WebSocket for Real-Time Updates (Optional but Recommended)

### Add Real-Time Dashboard Updates:
```python
# infrastructure/channels/consumers.py
class SessionConsumer(AsyncWebsocketConsumer):
    """
    ws://localhost/ws/sessions/<session_id>/
    Broadcasts updates when:
    - Questions ready
    - Response submitted
    - Evaluation complete
    - Session status changed
    """
    async def connect(self):
        # Accept connection
        # Join group: session_<id>
        
    async def session_update(self, event):
        # Send to frontend
        await self.send(json.dumps(event['data']))

# config/asgi.py (Update existing)
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/sessions/<int:session_id>/", SessionConsumer.asgi()),
        ])
    ),
})
```

**Install:**
```bash
pip install channels>=4.0.0
pip install channels-redis>=4.0.0
```

---

## Priority 8: Standard Response Format

### Create Response Wrapper:
```python
# common/responses.py
from rest_framework.response import Response
from rest_framework import status

class APIResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        return Response({
            "success": True,
            "message": message,
            "data": data,
        }, status=status_code)
    
    @staticmethod
    def error(message="Error", status_code=status.HTTP_400_BAD_REQUEST, errors=None):
        return Response({
            "success": False,
            "message": message,
            "errors": errors,
        }, status=status_code)

# Usage in views:
def post(self, request):
    try:
        # ... process
        return APIResponse.success(data={"id": 1}, message="Session created")
    except Exception as e:
        return APIResponse.error(message=str(e))
```

---

## Priority 9: Pagination for List Endpoints

### Add to `config/settings.py`:
```python
REST_FRAMEWORK = {
    # ... existing
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20
}
```

### Create:
```python
# common/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

---

## Priority 10: Error Handling Middleware

### Create:
```python
# common/middleware/exception_handler.py
from rest_framework.views import exception_handler as drf_exception_handler

def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "message": str(exc),
            "errors": response.data,
        }
    return response

# config/settings.py
REST_FRAMEWORK = {
    # ...
    'EXCEPTION_HANDLER': 'common.middleware.exception_handler.custom_exception_handler'
}
```

---

## File Structure to Add

```
TeachSense Backend (Updated)
├─ apps/
│  ├─ sessions/
│  │  ├─ api/
│  │  │  ├─ views.py       (NEW: SessionViewSet)
│  │  │  ├─ serializers.py (NEW)
│  │  │  ├─ urls.py        (NEW)
│  │  │  └─ permissions.py (NEW)
│  │  ├─ models.py
│  │  └─ ...
│  │
│  ├─ questions/
│  │  ├─ api/
│  │  │  ├─ views.py       (NEW: QuestionViewSet)
│  │  │  ├─ serializers.py (NEW)
│  │  │  └─ urls.py        (NEW)
│  │  └─ ...
│  │
│  ├─ responses/
│  │  ├─ api/
│  │  │  ├─ views.py       (NEW: ResponseViewSet)
│  │  │  ├─ serializers.py (NEW)
│  │  │  └─ urls.py        (NEW)
│  │  └─ ...
│  │
│  ├─ transcripts/
│  │  ├─ api/
│  │  │  ├─ views.py       (NEW: TranscriptUploadView)
│  │  │  └─ urls.py        (NEW)
│  │  └─ ...
│  │
│  ├─ devices/             (NEW: Device management)
│  │  ├─ models.py         (NEW: Device model)
│  │  ├─ api/
│  │  │  ├─ views.py       (NEW: Register, Sync endpoints)
│  │  │  ├─ serializers.py (NEW)
│  │  │  ├─ urls.py        (NEW)
│  │  │  └─ permissions.py (NEW: DeviceAuthenticated)
│  │  └─ ...
│  │
│  └─ users/
│     ├─ api/
│     │  ├─ views.py       (NEW: LoginView, RefreshView)
│     │  ├─ serializers.py (NEW)
│     │  └─ urls.py        (NEW)
│     └─ ...
│
├─ common/
│  ├─ responses.py         (NEW: APIResponse wrapper)
│  ├─ pagination.py        (NEW: StandardResultsSetPagination)
│  ├─ permissions.py       (NEW or UPDATE: IsLecturer, IsStudent, etc.)
│  └─ middleware/
│     └─ exception_handler.py (NEW)
│
├─ infrastructure/
│  ├─ channels/
│  │  └─ consumers.py      (NEW: SessionConsumer, ResponseConsumer)
│  └─ ...
│
├─ config/
│  ├─ urls.py              (UPDATE: Register new endpoints)
│  ├─ settings.py          (UPDATE: CORS, Channels, Auth)
│  ├─ asgi.py              (UPDATE: WebSocket routing)
│  └─ wsgi.py
│
└─ requirements.txt        (UPDATE: Add djangorestframework-simplejwt, channels, etc.)
```

---

## Installation & Setup Commands

```bash
# Install new dependencies
pip install djangorestframework-simplejwt>=5.0.0
pip install django-cors-headers>=4.0.0
pip install channels>=4.0.0
pip install channels-redis>=4.0.0

# Save to requirements.txt
pip freeze > requirements.txt

# Run migrations (if creating Device model)
python manage.py makemigrations devices
python manage.py migrate devices

# Create admin user if not exists
python manage.py createsuperuser

# Start development servers
# Terminal 1: Celery
celery -A config worker -l info

# Terminal 2: Django with Channels
python -m daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Terminal 3: Redis (if using Channels)
redis-server
```

---

## Frontend Integration Quick Start

### Example: Create Session from Frontend
```javascript
// Frontend (React/Vue/Angular)
const createSession = async (lectureTitle) => {
  const response = await fetch('http://localhost:8000/api/sessions/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      lecture_title: lectureTitle,
      description: 'Class session',
    }),
  });
  
  return response.json();
};

// Upload transcript
const uploadTranscript = async (sessionId, transcriptText) => {
  const response = await fetch(`http://localhost:8000/api/sessions/${sessionId}/transcripts/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      transcript_text: transcriptText,
      confidence_score: 0.95,
    }),
  });
  
  return response.json();
};

// Get session with analytics
const getSessionAnalytics = async (sessionId) => {
  const response = await fetch(`http://localhost:8000/api/analytics/sessions/${sessionId}/`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  
  return response.json();
};

// WebSocket: Real-time updates
const connectWebSocket = (sessionId) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${sessionId}/`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Session update:', data);
    // Update UI in real-time
  };
};
```

---

## Hardware Integration Quick Start

### Example: Device Registration
```python
# Device firmware / edge agent
import requests

DEVICE_ID = "device-classroom-01"  # MAC or serial
API_URL = "http://teachsense-cloud.io"

# 1. Register device
response = requests.post(f"{API_URL}/api/devices/register/", json={
    "device_id": DEVICE_ID,
    "device_name": "Classroom 01",
    "location": "Building A, Room 101",
})

device_token = response.json()["device_token"]
save_token_to_file(device_token)

# 2. Sync with cloud every 30s
while True:
    response = requests.get(
        f"{API_URL}/api/devices/sync/",
        headers={"X-Device-Token": device_token}
    )
    
    data = response.json()
    
    # Download sessions to process
    for session in data["sessions"]:
        process_locally(session)
    
    # Upload responses
    for response_file in get_local_responses():
        upload_response(response_file, device_token)
    
    time.sleep(30)
```

---

## Priority Order for Implementation

1. **Session CRUD endpoints** (30 min) — Core functionality
2. **Authentication/JWT** (20 min) — Security
3. **Transcript upload** (20 min) — Data ingestion
4. **Response submission** (20 min) — Student interaction
5. **CORS configuration** (10 min) — Frontend connectivity
6. **Device registration** (30 min) — Hardware integration
7. **Response format standardization** (15 min) — UX consistency
8. **Pagination** (10 min) — Scalability
9. **WebSocket (optional)** (45 min) — Real-time UX
10. **Error handling** (15 min) — Robustness

**Total: ~3-4 hours of development**

---

## Testing After Implementation

```bash
# Test session creation
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"lecture_title": "Test"}'

# Test transcript upload
curl -X POST http://localhost:8000/api/sessions/1/transcripts/ \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "..."}'

# Test analytics
curl -X GET http://localhost:8000/api/analytics/sessions/1/ \
  -H "Authorization: Bearer token"

# Test device registration
curl -X POST http://localhost:8000/api/devices/register/ \
  -H "Content-Type: application/json" \
  -d '{"device_id": "...", "device_name": "..."}'
```

---

## Summary

**You have a complete backend now. To connect frontend + hardware:**

✅ Already built:
- Lecture processing pipeline
- Analytics aggregation
- Dashboard overview
- Admin endpoints

❌ Still need:
- Session CRUD (30 min)
- Authentication (20 min)
- Transcript upload (20 min)
- Response submission (20 min)
- Device management (30 min)
- CORS setup (10 min)

**Recommended: Implement Priority 1-6 before connecting frontend.**

---

