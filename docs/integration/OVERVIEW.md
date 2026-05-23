# TeachSense: Backend-to-Frontend Integration Guide

## Overview

TeachSense is a comprehensive lecture analytics and real-time engagement platform that bridges frontend applications with a sophisticated Django REST backend, leveraging WebSocket technology for real-time communication and hardware device integration.

## Architecture

```
Frontend Application (React/Vue/etc)
        ↕️ (HTTP + WebSocket)
    Django REST API
        ├─ REST Endpoints (/api/*)
        ├─ WebSocket Consumer (ws://*)
        └─ Hardware Device Integration
        ↕️
    Database (PostgreSQL/SQLite)
    Cache Layer (Redis)
    Background Jobs (Celery)
    Message Broker (Redis)
```

## Key Integration Points

### 1. **REST API** (HTTP)
- Standard CRUD operations
- Authentication via JWT tokens
- Request/Response via JSON
- Base URL: `https://teachsense.onrender.com/api/`

### 2. **WebSocket** (Real-time)
- Live transcript updates
- Question/Response interactions
- Dashboard metrics streaming
- Base URL: `wss://teachsense.onrender.com/ws/`

### 3. **Hardware Integration**
- Device registration and management
- Protocol support (WebSocket, REST)
- Real-time device status
- Audio processing (STT/TTS)

### 4. **Documentation**
- Interactive Swagger UI at `https://teachsense.onrender.com/docs/`
- OpenAPI schema at `/api/schema/`
- This integration guide

## Quick Start

### Frontend Setup

```javascript
// Initialize API client
const API_BASE = 'https://teachsense.onrender.com/api';
const WS_BASE = 'wss://teachsense.onrender.com/ws';

// Authenticate
const token = await loginUser(email, password);
localStorage.setItem('authToken', token);

// Connect to WebSocket for live updates
const sessionWs = new WebSocket(
  `${WS_BASE}/sessions/${sessionId}/?token=${token}`
);
```

## Documentation Structure

- **[API_ENDPOINTS.md](./API_ENDPOINTS.md)** - Complete REST endpoint documentation
- **[WEBSOCKET.md](./WEBSOCKET.md)** - Real-time WebSocket integration guide
- **[HARDWARE.md](./HARDWARE.md)** - Device integration and hardware protocols
- **[AUTHENTICATION.md](./AUTHENTICATION.md)** - JWT authentication flow
- **[ERROR_HANDLING.md](./ERROR_HANDLING.md)** - Error codes and handling strategies

## Common Workflows

### 1. Starting a Lecture Session
1. Lecturer creates session via REST API
2. Frontend receives session ID and WebSocket URL
3. Students connect to session WebSocket
4. Real-time updates stream to all connected clients
5. Questions and responses flow in real-time
6. Dashboard aggregates metrics

### 2. Device Registration
1. Device authenticates with REST API
2. Backend validates device credentials
3. Device connects to appropriate WebSocket stream
4. Status updates propagate to dashboard

### 3. Real-time Transcript Processing
1. Frontend captures audio from hardware device
2. Sends to backend (REST or WebSocket)
3. Backend processes via STT service
4. Broadcasts to all connected sessions
5. Frontend updates UI in real-time

## Performance Considerations

- **Connection Pooling**: Reuse HTTP connections
- **WebSocket Heartbeat**: Ping/pong every 30 seconds
- **Batch Requests**: Group API calls when possible
- **Caching**: Frontend caching for reference data
- **Compression**: Enable gzip for HTTP responses

## Security

- All endpoints require HTTPS in production
- JWT tokens valid for 24 hours (configurable)
- WebSocket authentication via token query parameter
- CORS enabled for approved domains
- Rate limiting: 100 requests/minute per user

## Environment Configuration

```env
# Backend
DEBUG=False
ALLOWED_HOSTS=teachsense.onrender.com,localhost
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:pass@host/db

# Cache & Message Broker
REDIS_URL=redis://host:port/0

# Device Integration
HARDWARE_API_KEY=your-hardware-api-key
DEVICE_AUTH_SECRET=your-device-secret
```

## Support & Resources

- **API Documentation**: Visit `/docs/` endpoint
- **OpenAPI Schema**: Available at `/api/schema/`
- **Status Page**: `/api/health/` for system health
- **Issues & Support**: Contact development team

---

*Last Updated: May 2026*
*Version: 1.0*
