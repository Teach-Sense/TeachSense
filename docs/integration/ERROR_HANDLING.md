# TeachSense Error Handling Guide

Complete reference for error codes, HTTP status codes, and error handling strategies.

---

## HTTP Status Codes

### 2xx Success

| Code | Name | Meaning |
|------|------|---------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing |
| 204 | No Content | Success with no response body |

### 4xx Client Errors

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| 400 | Bad Request | Invalid request parameters | Check request format |
| 401 | Unauthorized | Authentication required/failed | Provide valid token |
| 403 | Forbidden | No permission for resource | Check user permissions |
| 404 | Not Found | Resource doesn't exist | Verify resource ID |
| 409 | Conflict | Resource conflict (e.g., duplicate) | Retry with unique data |
| 429 | Too Many Requests | Rate limit exceeded | Wait and retry |

### 5xx Server Errors

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| 500 | Internal Server Error | Backend error | Check logs, retry later |
| 502 | Bad Gateway | Upstream error | Try again soon |
| 503 | Service Unavailable | Server down/maintenance | Try again later |

---

## Error Response Format

### Standard Error Response

```json
{
  "detail": "User with this email already exists.",
  "code": "DUPLICATE_EMAIL",
  "status": 400,
  "timestamp": "2024-05-23T10:00:00Z"
}
```

### Validation Error Response

```json
{
  "detail": "Validation failed",
  "errors": {
    "email": ["This field is required.", "Invalid email format."],
    "password": ["Password must be at least 8 characters."]
  },
  "code": "VALIDATION_ERROR",
  "status": 400
}
```

### Context-Specific Error

```json
{
  "detail": "You do not have permission to perform this action.",
  "code": "PERMISSION_DENIED",
  "status": 403,
  "resource": "sessions/1",
  "action": "update"
}
```

---

## Error Codes Reference

### Authentication Errors (4xx)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `INVALID_CREDENTIALS` | 401 | Unable to log in with provided credentials | Check email/password |
| `TOKEN_EXPIRED` | 401 | Token has expired | Use refresh endpoint |
| `TOKEN_INVALID` | 401 | Token is invalid or malformed | Provide valid token |
| `TOKEN_NOT_PROVIDED` | 401 | Authentication credentials not provided | Add Authorization header |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh token is invalid | Login again |
| `ACCOUNT_DISABLED` | 401 | User account is disabled | Contact admin |

### Permission/Authorization Errors (403)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `PERMISSION_DENIED` | 403 | You do not have permission | Check user role |
| `INSUFFICIENT_PERMISSIONS` | 403 | Missing required permissions | Request admin access |
| `NOT_SESSION_OWNER` | 403 | Only session owner can modify | Use authorized account |
| `STUDENT_CANNOT_DELETE_QUESTION` | 403 | Only lecturer can delete | Use lecturer account |
| `DEVICE_NOT_REGISTERED` | 403 | Device not registered properly | Register device first |

### Not Found Errors (404)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist | Check resource ID |
| `SESSION_NOT_FOUND` | 404 | Session not found | Verify session ID |
| `USER_NOT_FOUND` | 404 | User not found | Check user ID |
| `DEVICE_NOT_FOUND` | 404 | Device not found | Register device first |
| `ENDPOINT_NOT_FOUND` | 404 | Endpoint does not exist | Check URL path |

### Validation Errors (400)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters | See `errors` field |
| `INVALID_JSON` | 400 | Request body is not valid JSON | Check JSON format |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing | Include all required fields |
| `INVALID_FIELD_VALUE` | 400 | Field value invalid type/format | Check field type |
| `DUPLICATE_ENTRY` | 409 | Entry already exists | Use unique value |
| `INVALID_ENUM_VALUE` | 400 | Value not in allowed options | Use valid enum value |

### Rate Limiting Errors (429)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `RATE_LIMITED` | 429 | Request rate limit exceeded | Wait and retry |
| `AUTH_RATE_LIMITED` | 429 | Too many login attempts | Wait 15 minutes |
| `API_QUOTA_EXCEEDED` | 429 | Monthly quota exceeded | Upgrade plan |

### Server/Database Errors (5xx)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error | Check server logs |
| `DATABASE_ERROR` | 500 | Database connection error | Retry after delay |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable | Try again soon |
| `EXTERNAL_SERVICE_ERROR` | 502 | External service failed | Retry or contact support |

### Business Logic Errors (400/409)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `SESSION_ALREADY_STARTED` | 409 | Cannot modify started session | Use different session |
| `SESSION_ALREADY_ENDED` | 409 | Cannot modify ended session | Use different session |
| `QUESTION_ALREADY_ANSWERED` | 409 | Cannot answer already answered | Use different question |
| `INVALID_STATE_TRANSITION` | 400 | Invalid status transition | Check allowed states |
| `INSUFFICIENT_PARTICIPANTS` | 400 | Minimum participants required | Wait for more to join |

### Device/Hardware Errors (4xx/5xx)

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| `DEVICE_DISCONNECTED` | 502 | Device lost connection | Reconnect device |
| `DEVICE_TIMEOUT` | 504 | Device not responding | Check device status |
| `AUDIO_PROCESSING_ERROR` | 500 | Audio processing failed | Retry or restart |
| `STT_SERVICE_ERROR` | 502 | Speech-to-text service down | Try again later |
| `TTS_SERVICE_ERROR` | 502 | Text-to-speech service down | Try again later |

---

## Error Handling Strategies

### Frontend Error Handling

**Basic Pattern:**
```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      handleApiError(error);
      throw new ApiError(error.detail, error.code);
    }
    
    return await response.json();
  } catch (error) {
    handleError(error);
  }
}

function handleApiError(error) {
  switch(error.code) {
    case 'TOKEN_EXPIRED':
      // Refresh token and retry
      refreshToken().then(() => location.reload());
      break;
    
    case 'PERMISSION_DENIED':
      // Show permission denied message
      showAlert('You do not have permission to perform this action', 'error');
      break;
    
    case 'VALIDATION_ERROR':
      // Show validation errors
      showFormErrors(error.errors);
      break;
    
    case 'RATE_LIMITED':
      // Show rate limit message
      showAlert('Too many requests. Please wait a moment.', 'warning');
      break;
    
    case 'RESOURCE_NOT_FOUND':
      // Redirect to not found page
      window.location.href = '/404';
      break;
    
    default:
      // Show generic error
      showAlert(error.detail || 'An error occurred', 'error');
  }
}

function handleError(error) {
  if (error instanceof TypeError) {
    // Network error
    showAlert('Network error. Check your connection.', 'error');
  } else if (error instanceof ApiError) {
    // Already handled
  } else {
    // Unknown error
    showAlert('An unexpected error occurred', 'error');
    console.error('Unexpected error:', error);
  }
}

class ApiError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
  }
}
```

### Retry Logic

```javascript
async function apiCallWithRetry(url, options = {}, maxRetries = 3) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Add retry header
      options.headers = {
        ...options.headers,
        'X-Retry-Attempt': attempt
      };
      
      const response = await fetch(url, options);
      
      if (response.ok) {
        return await response.json();
      }
      
      // Don't retry on client errors (except rate limit)
      if (response.status >= 400 && response.status < 500) {
        if (response.status !== 429) {
          const error = await response.json();
          throw new ApiError(error.detail, error.code);
        }
      }
      
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
      
      if (attempt < maxRetries) {
        // Exponential backoff
        const delay = Math.pow(2, attempt - 1) * 1000;
        console.log(`Retry attempt ${attempt}/${maxRetries} after ${delay}ms`);
        await sleep(delay);
      }
    }
  }
  
  throw lastError;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### WebSocket Error Recovery

```javascript
class RobustWebSocket {
  constructor(url, onMessage, maxRetries = 5) {
    this.url = url;
    this.onMessage = onMessage;
    this.maxRetries = maxRetries;
    this.retryCount = 0;
    this.ws = null;
    this.heartbeatTimeout = null;
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.addEventListener('open', () => {
        console.log('WebSocket connected');
        this.retryCount = 0;
        this.startHeartbeat();
      });
      
      this.ws.addEventListener('message', (event) => {
        this.onMessage(JSON.parse(event.data));
      });
      
      this.ws.addEventListener('error', (event) => {
        console.error('WebSocket error:', event);
        this.handleError(event);
      });
      
      this.ws.addEventListener('close', () => {
        console.log('WebSocket disconnected');
        this.reconnect();
      });
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.reconnect();
    }
  }

  handleError(event) {
    clearTimeout(this.heartbeatTimeout);
    
    if (event.code === 1008) {
      // Policy violation (usually auth error)
      console.error('Authentication error');
      // Trigger logout
    } else if (event.code === 1006) {
      // Abnormal closure
      console.error('Connection abnormally closed');
      this.reconnect();
    }
  }

  reconnect() {
    if (this.retryCount >= this.maxRetries) {
      console.error('Max retries reached');
      return;
    }
    
    this.retryCount++;
    const delay = Math.pow(2, this.retryCount - 1) * 1000;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.retryCount})`);
    setTimeout(() => this.connect(), delay);
  }

  startHeartbeat() {
    this.heartbeatTimeout = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  close() {
    clearTimeout(this.heartbeatTimeout);
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.close(1000, 'Normal closure');
    }
  }
}

// Usage
const ws = new RobustWebSocket(
  `wss://teachsense.up.railway.app/ws/sessions/1/?token=${token}`,
  (data) => console.log('Message:', data)
);
ws.connect();
```

### Backend Error Handling (Django)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SessionDetailView(APIView):
    def get(self, request, id):
        try:
            session = Session.objects.get(id=id)
            
            # Check permissions
            if not request.user.has_perm('view_session', session):
                return Response(
                    {
                        "detail": "You do not have permission to view this session",
                        "code": "PERMISSION_DENIED",
                        "status": 403
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = SessionSerializer(session)
            return Response(serializer.data)
            
        except Session.DoesNotExist:
            return Response(
                {
                    "detail": "Session not found",
                    "code": "RESOURCE_NOT_FOUND",
                    "status": 404
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response(
                {
                    "detail": "An unexpected error occurred",
                    "code": "INTERNAL_SERVER_ERROR",
                    "status": 500
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, id):
        try:
            session = Session.objects.get(id=id)
            
            # Validate state
            if session.status == 'ended':
                return Response(
                    {
                        "detail": "Cannot modify ended session",
                        "code": "SESSION_ALREADY_ENDED",
                        "status": 409
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            serializer = SessionSerializer(
                session,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(
                    {
                        "detail": "Validation failed",
                        "errors": serializer.errors,
                        "code": "VALIDATION_ERROR",
                        "status": 400
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response(
                {
                    "detail": "An unexpected error occurred",
                    "code": "INTERNAL_SERVER_ERROR",
                    "status": 500
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

## Common Scenarios & Solutions

### Scenario: Session 401 (Token Expired)

**Problem:** WebSocket connection drops with 401

```javascript
ws.addEventListener('close', async (event) => {
  if (event.code === 1008) { // Policy violation
    // Try to refresh token and reconnect
    try {
      const newToken = await refreshToken();
      ws = new WebSocket(
        `wss://teachsense.up.railway.app/ws/sessions/1/?token=${newToken}`
      );
    } catch (error) {
      // Force logout
      window.location.href = '/login';
    }
  }
});
```

### Scenario: Network Timeout

**Problem:** API call hangs with no response

```javascript
async function requestWithTimeout(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}
```

### Scenario: Rate Limited (429)

**Problem:** Getting 429 Too Many Requests

```javascript
async function requestWithRateLimit(url, options = {}) {
  const response = await fetch(url, options);
  
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After') || '60';
    console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
    await sleep(parseInt(retryAfter) * 1000);
    return requestWithRateLimit(url, options); // Retry
  }
  
  return response;
}
```

---

## Logging Best Practices

```javascript
// Client-side logging
const logger = {
  error: (message, error, context = {}) => {
    console.error(message, error);
    // Send to backend logging service
    fetch('/api/logs/', {
      method: 'POST',
      body: JSON.stringify({
        level: 'error',
        message,
        error: error.message,
        stack: error.stack,
        context,
        timestamp: new Date().toISOString()
      })
    });
  },
  
  warning: (message, context = {}) => {
    console.warn(message);
    // Similar logging
  }
};

// Usage
try {
  await apiCall('/sessions/');
} catch (error) {
  logger.error('Failed to load sessions', error, {
    url: '/api/sessions/',
    userId: user.id
  });
}
```

---

*Last Updated: May 2026*
