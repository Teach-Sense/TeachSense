# Setup & Deployment Instructions

## Pre-Deployment Checklist

- [x] API endpoints implemented (15 endpoints, 8 views)
- [x] WebSocket consumers created (Session + Dashboard)
- [x] Database models defined (Device, DeviceSyncLog)
- [x] Authentication configured (JWT)
- [x] CORS configured (frontend dev ports)
- [x] Error handling standardized
- [x] Pagination integrated
- [x] Permissions implemented
- [ ] Database migrations applied
- [ ] Environment variables set (.env)
- [ ] Redis running
- [ ] Services started

---

## Step 1: Apply Database Migrations

```bash
cd /home/sulayman/teachsense-backend

# Create migrations for Device model
python manage.py makemigrations devices

# Apply all migrations (including existing ones)
python manage.py migrate

# Run custom seed (if available)
python manage.py seed_db  # optional
```

**Expected output**:
```
Migrations for 'devices':
  devices/migrations/0001_initial.py
    - Create model Device
    - Create model DeviceSyncLog

Running migrations:
  ...
  devices.0001_initial ... OK
```

**Validates**:
- Device table created with 12 columns
- DeviceSyncLog table created with 8 columns
- Foreign key relationships intact
- Indexes created for fast queries

---

## Step 2: Configure Environment Variables

Create `.env` file in project root:

```bash
# .env
DEBUG=False
SECRET_KEY=your-secret-key-here  # Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Database (if using PostgreSQL in production)
DATABASE_URL=postgresql://user:password@localhost:5432/teachsense

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# LLM Services (optional; fallback providers included)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
COHERE_API_KEY=...

# Frontend URLs (CORS)
FRONTEND_URL=http://localhost:3000
```

Load in Django with:
```python
from django.conf import settings
import os

DEBUG = os.getenv('DEBUG', 'True') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
```

---

## Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements (includes channels-redis)
pip install -r requirements.txt

# Verify WebSocket support
python -c "import channels; print(f'Channels: {channels.__version__}')"
```

---

## Step 4: Start Services (Development)

### Terminal 1: Redis
```bash
redis-server --port 6379
```

**Verify Redis running**:
```bash
redis-cli PING
# Output: PONG
```

---

### Terminal 2: Celery Worker
```bash
cd /home/sulayman/teachsense-backend

# Standard worker
celery -A config worker -l info

# Or with auto-reload (development)
celery -A config worker -l info --autoscale=10,3
```

**Expected startup**:
```
 -------------- celery@hostname v5.3.0 (emerald-rush)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ----------
- *** --- * --- [queues]
                - celery
[tasks]
  - apps.lectures.tasks.process_lecture_session
  - apps.lectures.tasks.generate_questions
  - apps.lectures.tasks.evaluate_responses
  - ...
```

---

### Terminal 3: Django + WebSocket (ASGI)

**Option A: Daphne (Recommended for WebSocket)**
```bash
cd /home/sulayman/teachsense-backend

# Run ASGI server with WebSocket support
python -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Expected output**:
```
Daphne running, listening on ('0.0.0.0', 8000)
```

---

**Option B: Standard Django (WebSocket fallback to polling)**
```bash
cd /home/sulayman/teachsense-backend

python manage.py runserver 0.0.0.0:8000
```

**Expected output**:
```
Starting development server at http://0.0.0.0:8000/
Django version 5.1.10, using settings 'config.settings'
```

---

## Step 5: Verify Installation

### Check Database
```bash
python manage.py shell

# In shell:
from apps.devices.models import Device, DeviceSyncLog
print(f"Device model: {Device}")
print(f"SyncLog model: {DeviceSyncLog}")
Device.objects.count()  # Should return 0 initially
exit()
```

### Check API Schema
```bash
curl http://localhost:8000/api/schema/
# Returns OpenAPI 3.0 schema JSON

curl http://localhost:8000/api/docs/
# Opens Swagger UI in browser
```

### Test Authentication
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "password_confirm": "TestPass123",
    "is_lecturer": false
  }'

# Should return:
# {
#   "success": true,
#   "data": {
#     "user": {...},
#     "tokens": {"access": "...", "refresh": "..."}
#   }
# }
```

### Test WebSocket
```javascript
// In browser console (or Node.js):
const ws = new WebSocket('ws://localhost:8000/ws/sessions/1/');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
```

---

## Step 6: Create Initial Data (Optional)

### Create Superuser (for admin panel)
```bash
python manage.py createsuperuser
# Follow prompts for username, email, password
```

### Seed Test Data
```bash
# If seed script exists
python manage.py seed_db

# Or via shell:
python manage.py shell
# In shell:
from django.contrib.auth import get_user_model
from apps.core.models import Lecture

User = get_user_model()

# Create lecturer
lecturer = User.objects.create_user(
    username='lecturer1',
    email='lecturer@example.com',
    password='TestPass123',
    is_lecturer=True
)

# Create lecture
lecture = Lecture.objects.create(
    title='Python Basics',
    description='Introduction to Python'
)

print(f"Created: {lecturer} and {lecture}")
exit()
```

---

## Step 7: Connect Frontend

### In Frontend Code

**Set API URL**:
```javascript
// src/config.js or .env
export const API_URL = 'http://localhost:8000/api';
export const WS_URL = 'ws://localhost:8000';
```

**Install HTTP client**:
```bash
npm install axios
# or
npm install node-fetch
```

**Create API service**:
```javascript
// src/api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh token on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        // Call refresh endpoint
        try {
          const res = await apiClient.post('/auth/token/refresh/', {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', res.data.data.access);
          // Retry original request
          return apiClient(error.config);
        } catch {
          // Redirect to login
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

**Use in components**:
```javascript
// src/pages/Login.jsx
import apiClient from '../api/client';

async function handleLogin(username, password) {
  try {
    const res = await apiClient.post('/auth/login/', {
      username,
      password,
    });
    
    localStorage.setItem('access_token', res.data.data.tokens.access);
    localStorage.setItem('refresh_token', res.data.data.tokens.refresh);
    
    // Redirect to dashboard
    navigate('/dashboard');
  } catch (error) {
    console.error('Login failed:', error.response?.data?.message);
  }
}
```

---

## Step 8: Connect Hardware Devices

### Device Registration Flow

**1. Device calls register endpoint**:
```bash
curl -X POST http://api-server:8000/api/devices/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ABC-123-DEF",
    "device_name": "Classroom-1-Tablet",
    "device_type": "tablet",
    "os_type": "iOS",
    "os_version": "17.0",
    "app_version": "1.0.0"
  }'

# Response:
# {
#   "success": true,
#   "data": {
#     "id": "uuid-...",
#     "device_token": "device-token-xyz",
#     "sync_interval_seconds": 30,
#     "api_endpoint": "http://api-server:8000/api"
#   }
# }
```

**2. Device stores device_token locally**

**3. Device polls sync endpoint every 30 seconds**:
```bash
# Pull new questions/sessions
curl -X GET http://api-server:8000/api/devices/sync/ \
  -H "X-Device-Token: device-token-xyz"

# Response:
# {
#   "success": true,
#   "data": {
#     "sessions": [...],
#     "questions": [...],
#     "responses_to_process": [...]
#   }
# }
```

**4. Device pushes student responses**:
```bash
curl -X POST http://api-server:8000/api/devices/sync/ \
  -H "X-Device-Token: device-token-xyz" \
  -H "Content-Type: application/json" \
  -d '{
    "responses": [
      {
        "question_id": 1,
        "student_id": 1,
        "response_text": "My answer",
        "audio_file": "base64-encoded"
      }
    ]
  }'
```

---

## Production Deployment

### Using Gunicorn + Daphne

```bash
# Install production servers
pip install gunicorn whitenoise

# Run with Gunicorn (HTTP only)
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync

# Run with Daphne (HTTP + WebSocket)
daphne -b 0.0.0.0 -p 8000 \
  -u /tmp/daphne.sock \
  config.asgi:application

# Or with supervisor for auto-restart:
# See deployments/systemd/ or deployments/docker/
```

### Using Docker Compose

```bash
# Update docker-compose.yml with new services
docker-compose up -d

# Verify:
docker-compose ps
# Shows: db, redis, web (Django), celery, ...
```

### Environment Variables (Production)
```bash
# .env.production
DEBUG=False
ALLOWED_HOSTS=api.example.com,www.example.com

DATABASE_URL=postgresql://prod_user:secure_pass@prod-db:5432/teachsense_prod

REDIS_URL=redis://redis:6379/0

CORS_ALLOWED_ORIGINS=https://example.com,https://app.example.com

SECRET_KEY=generate-secure-key-here
```

---

## Monitoring & Debugging

### Check API Health
```bash
curl http://localhost:8000/api/
# Returns list of available endpoints
```

### View Celery Tasks
```bash
# In Celery terminal, check logs for task execution
celery -A config inspect active
# Shows currently running tasks

celery -A config inspect scheduled
# Shows queued tasks
```

### Monitor Redis
```bash
redis-cli

MEMORY STATS      # Check memory usage
DBSIZE            # Count keys
FLUSHDB           # Clear database (dev only!)
```

### Django Admin Panel
```
http://localhost:8000/admin/
# Login with superuser credentials
# Manage users, devices, sessions, etc.
```

### API Documentation
```
http://localhost:8000/api/docs/     # Swagger UI (interactive)
http://localhost:8000/api/schema/   # OpenAPI JSON
```

---

## Common Issues & Solutions

### Redis Connection Error
```
ConnectionError: Error 111 connecting to localhost:6379
```
**Solution**: Start Redis
```bash
redis-server
```

---

### WebSocket Connection Failed
```
Error: WebSocket is closed before the connection is established
```
**Solution**: Use Daphne instead of runserver
```bash
python -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

---

### CORS Error
```
Access to XMLHttpRequest has been blocked by CORS policy
```
**Solution**: Add frontend URL to CORS_ALLOWED_ORIGINS in settings.py
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
```

---

### JWT Token Expired
```
{
  "success": false,
  "message": "Token is invalid or expired"
}
```
**Solution**: Refresh token using refresh endpoint
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "refresh-token-here"}'
```

---

### Device Sync Error
```
{
  "success": false,
  "message": "Invalid device token"
}
```
**Solution**: Ensure device sends X-Device-Token header
```bash
curl -X GET http://localhost:8000/api/devices/sync/ \
  -H "X-Device-Token: your-device-token"
```

---

## Performance Optimization

### Database Query Optimization
```python
# In serializers, use select_related/prefetch_related
class SessionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'title', 'created_at']
    
    def get_queryset(self):
        return Session.objects.select_related('lecture__lecturer').prefetch_related('questions')
```

### Caching
```python
# Cache frequently accessed data
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def get_sessions(request):
    ...
```

### Database Indexing
```python
# Already added for common queries:
# - Device.device_id
# - Device.status
# - DeviceSyncLog.device, created_at
# - Session.lecture, created_at
```

---

## Next Steps

1. ✅ **Apply migrations** - Creates Device tables
2. ✅ **Configure .env** - Set environment variables
3. ✅ **Start Redis** - Required for Celery + Channels
4. ✅ **Start Celery** - Task queue for processing
5. ✅ **Start Django** - API server
6. ✅ **Test endpoints** - Verify all working
7. ✅ **Connect frontend** - Start integration
8. ✅ **Register devices** - Hardware can now sync
9. ✅ **Monitor/debug** - Use logs and admin panel

---

## Support

See documentation:
- [API_IMPLEMENTATION_COMPLETE.md](./API_IMPLEMENTATION_COMPLETE.md) - Feature overview
- [ARCHITECTURE_UNIFIED.md](./ARCHITECTURE_UNIFIED.md) - System architecture
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) - Implementation details

---

*Last Updated: 2025-05-21*
