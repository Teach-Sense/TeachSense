# TeachSense Authentication Guide

## Overview

TeachSense uses JWT (JSON Web Token) authentication for all API and WebSocket connections. This guide covers the complete authentication flow.

---

## JWT Token Structure

A JWT token consists of three parts separated by dots:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Header:** Algorithm and token type
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:** Claims (user info, permissions, expiry)
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "role": "lecturer",
  "exp": 1716462000,
  "iat": 1716375600
}
```

**Signature:** HMAC encrypted header.payload

---

## Login Flow

### Step 1: Submit Credentials

**Endpoint:** `POST /api/auth/login/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "lecturer",
    "avatar_url": "https://..."
  }
}
```

### Step 2: Store Tokens

**Frontend (Browser):**
```javascript
// Store tokens (localStorage or sessionStorage)
localStorage.setItem('accessToken', response.data.access);
localStorage.setItem('refreshToken', response.data.refresh);

// Or use secure HttpOnly cookies
document.cookie = `accessToken=${response.data.access}; HttpOnly; Secure; SameSite=Strict`;
```

**Mobile/Desktop:**
```swift
// iOS Keychain
let queryAdd: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrAccount as String: "accessToken",
    kSecValueData as String: tokenData.data(using: .utf8)!
]
SecItemAdd(queryAdd as CFDictionary, nil)
```

### Step 3: Use in Requests

**REST API:**
```javascript
fetch('https://teachsense.up.railway.app/api/sessions/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
    'Content-Type': 'application/json'
  }
});
```

**WebSocket:**
```javascript
const token = localStorage.getItem('accessToken');
const ws = new WebSocket(
  `wss://teachsense.up.railway.app/ws/sessions/1/?token=${token}`
);
```

---

## Token Expiry & Refresh

### Access Token Expiry

Access tokens expire after **24 hours** (configurable).

When expired, API returns `401 Unauthorized`:
```json
{
  "detail": "Token is invalid or expired"
}
```

### Refresh Token Flow

**Endpoint:** `POST /api/auth/refresh/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Automatic Token Refresh

**JavaScript:**
```javascript
class ApiClient {
  async request(url, options = {}) {
    let response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.getAccessToken()}`,
        ...options.headers
      }
    });

    // If 401, try to refresh token
    if (response.status === 401) {
      await this.refreshToken();
      response = await fetch(url, {
        ...options,
        headers: {
          'Authorization': `Bearer ${this.getAccessToken()}`,
          ...options.headers
        }
      });
    }

    return response;
  }

  async refreshToken() {
    const response = await fetch(
      'https://teachsense.up.railway.app/api/auth/refresh/',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          refresh: localStorage.getItem('refreshToken')
        })
      }
    );

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
    } else {
      // Refresh failed, user needs to login again
      this.logout();
    }
  }

  getAccessToken() {
    return localStorage.getItem('accessToken');
  }

  logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login';
  }
}

const api = new ApiClient();
```

---

## Logout

### Endpoint: POST /api/auth/logout/

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

### Logout Implementation

```javascript
async function logout() {
  // Call API logout endpoint
  await fetch('https://teachsense.up.railway.app/api/auth/logout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      refresh: localStorage.getItem('refreshToken')
    })
  });

  // Clear local storage
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');

  // Redirect to login
  window.location.href = '/login';
}
```

---

## Device Authentication

### Device Token

Devices receive special tokens for hardware communication.

**Registration:**
```bash
curl -X POST https://teachsense.up.railway.app/api/devices/ \
  -H "Authorization: Bearer <user_token>" \
  -d '{
    "name":"Classroom Microphone",
    "type":"audio_input",
    "device_key":"device_secret"
  }'
```

**Response:**
```json
{
  "id": 15,
  "name": "Classroom Microphone",
  "auth_token": "device_auth_token_abc123",
  "ws_url": "wss://teachsense.up.railway.app/ws/devices/audio_01/"
}
```

### Device WebSocket Connection

```javascript
const deviceToken = 'device_auth_token_abc123';
const deviceWs = new WebSocket(
  `wss://teachsense.up.railway.app/ws/devices/audio_01/?token=${deviceToken}`
);
```

---

## Security Best Practices

### 1. Token Storage

❌ **Don't:**
```javascript
// Don't store in localStorage if information is sensitive
localStorage.setItem('token', token); // Vulnerable to XSS
```

✅ **Do:**
```javascript
// Use HttpOnly cookies for maximum security
// Set by backend in response headers
Set-Cookie: accessToken=...; HttpOnly; Secure; SameSite=Strict

// Or use memory + sessionStorage (cleared on browser close)
sessionStorage.setItem('token', token);
```

### 2. HTTPS Only

Always use HTTPS to prevent token interception:
```javascript
// ✅ Good
ws = new WebSocket('wss://teachsense.up.railway.app/ws/...');

// ❌ Bad
ws = new WebSocket('ws://teachsense.up.railway.app/ws/...');
```

### 3. Token Rotation

```javascript
// Refresh token periodically (before expiry)
setInterval(() => {
  refreshToken();
}, 23 * 60 * 60 * 1000); // 23 hours
```

### 4. Validate Token Claims

```python
# Backend validates these claims
import jwt

def verify_token(token, secret):
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Verify expiry
        if payload['exp'] < time.time():
            raise jwt.ExpiredSignatureError
        
        # Verify user has access
        user_id = payload['user_id']
        user = User.objects.get(id=user_id)
        
        return user
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")
```

### 5. Rate Limiting on Auth

Prevent brute force attacks:
- Max 5 login attempts per minute
- Max 10 token refresh attempts per minute
- IP-based throttling

---

## Error Handling

### Invalid Credentials

```json
{
  "non_field_errors": [
    "Unable to log in with provided credentials."
  ]
}
```

### Invalid Token Format

```json
{
  "detail": "Given token not valid for any token type"
}
```

### Token Expired

```json
{
  "detail": "Token is invalid or expired"
}
```

### Insufficient Permissions

```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Multi-Device Logout

### Logout from All Devices

**Endpoint:** `POST /api/auth/logout-all/`

**Response:**
```json
{
  "message": "Logged out from all devices",
  "sessions_terminated": 3
}
```

---

## API Key Authentication (Alternative)

For backend-to-backend communication:

**Header:**
```
X-API-Key: your_api_key_here
```

**Request:**
```bash
curl https://teachsense.up.railway.app/api/health/ \
  -H "X-API-Key: your_api_key_here"
```

---

## OAuth2 Integration (Future)

Coming soon: GitHub, Google, Microsoft sign-in

---

## Troubleshooting

### "Token not found"
- Ensure localStorage has token saved
- Check token wasn't deleted
- Cookie might be blocked (check browser settings)

### "Token expired after just created"
- Check server time sync
- Verify system clock is correct
- Review token expiry settings

### "Invalid token for WebSocket"
- Token must be passed as query parameter: `?token=xxx`
- Can't use Authorization header in WebSocket URL
- Token must match REST API token

### WebSocket disconnects after ~1 minute
- May need to implement ping/pong for keep-alive
- Token may have expired (check logs)
- Network firewall may be closing idle connections

---

## Password Reset

### Request Reset Email

**Endpoint:** `POST /api/auth/password-reset/`

```json
{
  "email": "user@example.com"
}
```

### Reset Token Email

User receives email with reset link containing token.

### Set New Password

**Endpoint:** `POST /api/auth/password-reset-confirm/`

```json
{
  "token": "reset_token_from_email",
  "new_password": "new_secure_password_123"
}
```

---

## Two-Factor Authentication (Optional)

### Enable 2FA

**Endpoint:** `POST /api/auth/2fa/enable/`

**Response:**
```json
{
  "qr_code": "data:image/png;base64,iVBORw0...",
  "secret": "JBSWY3DPEBLW64TMMQ====",
  "backup_codes": ["code1", "code2", "code3"]
}
```

### Login with 2FA

**Endpoint:** `POST /api/auth/login/`

```json
{
  "email": "user@example.com",
  "password": "password123",
  "otp": "123456"
}
```

---

## Security Headers

Backend sends these security headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

---

*Last Updated: May 2026*
