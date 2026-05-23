# TeachSense Hardware Integration Guide

## Overview

Hardware integration enables TeachSense to connect with various devices for audio capture, processing, and real-time interaction. The system supports:

- **Audio Input Devices** (microphones, headsets)
- **Audio Output Devices** (speakers)
- **Processing Devices** (dedicated audio processors)
- **IoT Devices** (cameras, sensors)

---

## Device Types

### 1. Audio Input Devices

**Purpose:** Capture lecturer/student audio

**Supported Models:**
- USB Microphones
- Wireless Headsets
- Array Microphones
- Built-in Device Microphones

**Protocols:** WebSocket, HTTP REST

**Example Registration:**
```json
{
  "name": "Lecture Hall Primary Mic",
  "type": "audio_input",
  "model": "Blue Yeti USB",
  "protocol": "websocket",
  "device_key": "device_secret_123",
  "specs": {
    "channels": 2,
    "sample_rate": 48000,
    "bit_depth": 24
  }
}
```

### 2. Audio Output Devices

**Purpose:** Broadcast audio to participants

**Supported Models:**
- USB Speakers
- PA Systems
- Built-in Speakers
- Headphones

**Example:**
```json
{
  "name": "Lecture Hall Speakers",
  "type": "audio_output",
  "model": "Bose Professional",
  "protocol": "rest",
  "device_key": "device_secret_456"
}
```

### 3. Video Devices

**Purpose:** Capture visual content

**Supported Models:**
- USB Cameras
- PTZ Cameras
- Screen Capture
- 360 Cameras

**Example:**
```json
{
  "name": "Lecture Camera",
  "type": "video_input",
  "model": "Logitech 4K",
  "protocol": "http_stream",
  "device_key": "device_secret_789"
}
```

### 4. Processing Devices

**Purpose:** Pre-process audio/video

**Supported Types:**
- Acoustic Echo Cancellation (AEC)
- Noise Suppression
- Audio Enhancement
- Video Processing

**Example:**
```json
{
  "name": "Audio Processor",
  "type": "audio_processor",
  "model": "NVIDIA A100",
  "protocol": "rest",
  "device_key": "device_secret_aaa"
}
```

---

## Device Registration

### Step 1: Create Device

**Endpoint:** `POST /api/devices/`

**Request:**
```json
{
  "name": "My Microphone",
  "type": "audio_input",
  "protocol": "websocket",
  "device_key": "your_device_secret"
}
```

**Response:**
```json
{
  "id": 15,
  "name": "My Microphone",
  "type": "audio_input",
  "status": "pending",
  "protocol": "websocket",
  "auth_token": "device_token_xyz123",
  "created_at": "2024-05-23T10:00:00Z",
  "ws_url": "wss://teachsense.onrender.com/ws/devices/device_xyz123/"
}
```

### Step 2: Connect Device

**WebSocket Connection:**
```
wss://teachsense.onrender.com/ws/devices/<device_id>/?token=<auth_token>
```

**HTTP Headers:**
```
Authorization: Bearer device_token_xyz123
Content-Type: application/json
```

### Step 3: Send Handshake

**WebSocket Message:**
```json
{
  "type": "handshake",
  "device_id": 15,
  "device_type": "audio_input",
  "protocol_version": "1.0",
  "timestamp": "2024-05-23T10:00:15Z"
}
```

**Backend Response:**
```json
{
  "type": "handshake_response",
  "status": "accepted",
  "device_status": "connected",
  "timestamp": "2024-05-23T10:00:16Z"
}
```

---

## Communication Protocols

### Protocol 1: WebSocket (Real-time)

**Best for:** Audio streaming, real-time processing

**Connection:**
```javascript
const deviceToken = 'device_token_xyz123';
const deviceWs = new WebSocket(
  `wss://teachsense.onrender.com/ws/devices/audio_input_01/?token=${deviceToken}`
);
```

**Message Types:**

#### Audio Data Stream
```json
{
  "type": "audio_frame",
  "device_id": 15,
  "frame_number": 1024,
  "timestamp": "2024-05-23T10:00:30.123Z",
  "sample_rate": 48000,
  "channels": 2,
  "bit_depth": 16,
  "data_base64": "//AAAv//AAD//wAA..."
}
```

#### Device Status
```json
{
  "type": "device_status",
  "device_id": 15,
  "status": "active",
  "cpu_usage": 15.2,
  "memory_usage": 256,
  "temperature": 45,
  "timestamp": "2024-05-23T10:00:35Z"
}
```

#### Error Report
```json
{
  "type": "error",
  "device_id": 15,
  "error_code": "AUDIO_BUFFER_OVERFLOW",
  "message": "Input buffer overflow detected",
  "timestamp": "2024-05-23T10:00:40Z"
}
```

### Protocol 2: HTTP REST

**Best for:** File uploads, periodic updates

**Endpoint:** `POST /api/devices/{id}/data/`

**Request:**
```
Content-Type: multipart/form-data

Headers:
- Authorization: Bearer device_token_xyz123

Body:
- audio_file: <binary audio data>
- metadata: {"timestamp": "2024-05-23T10:00:45Z"}
```

**Response:**
```json
{
  "status": "received",
  "frame_id": 1025,
  "processed_at": "2024-05-23T10:00:46Z",
  "result": {
    "quality_score": 0.95,
    "processing_time_ms": 150
  }
}
```

### Protocol 3: HTTP Streaming

**Best for:** Continuous media streams

**Connection:**
```
GET /api/devices/{id}/stream/
Authorization: Bearer device_token_xyz123
Accept: audio/mpeg
```

**Response:** Continuous HTTP stream with audio/video data

---

## Audio Processing Pipeline

### STT (Speech-to-Text) Integration

**Endpoint:** `POST /api/devices/{id}/transcribe/`

**Request:**
```json
{
  "audio_data": "base64_encoded_audio",
  "language": "en-US",
  "session_id": 1,
  "timestamp": "2024-05-23T10:00:50Z"
}
```

**Response:**
```json
{
  "transcript": "Today we'll discuss advanced concepts",
  "confidence": 0.98,
  "processing_time_ms": 250,
  "language": "en-US",
  "timestamp": "2024-05-23T10:00:52Z",
  "segments": [
    {
      "text": "Today",
      "start_time": 0.0,
      "end_time": 0.3,
      "confidence": 0.99
    }
  ]
}
```

### TTS (Text-to-Speech) Integration

**Endpoint:** `POST /api/devices/{id}/speak/`

**Request:**
```json
{
  "text": "Response acknowledged",
  "language": "en-US",
  "voice": "natural_female",
  "speed": 1.0,
  "output_device_id": 20
}
```

**Response:**
```json
{
  "audio_url": "https://teachsense.onrender.com/media/tts/audio_abc123.mp3",
  "duration_seconds": 2.5,
  "status": "generated",
  "timestamp": "2024-05-23T10:01:00Z"
}
```

### Audio Enhancement

**Endpoint:** `POST /api/devices/{id}/enhance/`

**Request:**
```json
{
  "audio_data": "base64_encoded_audio",
  "enhancement_type": "noise_suppression",
  "intensity": 0.8
}
```

**Response:**
```json
{
  "enhanced_audio": "base64_encoded_enhanced_audio",
  "processing_time_ms": 180,
  "enhancement_applied": "noise_suppression",
  "noise_reduction_db": 12.5
}
```

---

## Device Status Management

### Get Device Status

**Endpoint:** `GET /api/devices/{id}/`

**Response:**
```json
{
  "id": 15,
  "name": "Lecture Hall Microphone",
  "type": "audio_input",
  "status": "connected",
  "last_heartbeat": "2024-05-23T10:01:05Z",
  "uptime_seconds": 3600,
  "data_points_received": 14400,
  "error_count": 2,
  "battery_level": null,
  "signal_strength": 95,
  "temperature": 42,
  "cpu_usage": 18.5,
  "memory_usage": 512
}
```

### Update Device Status

**Endpoint:** `PATCH /api/devices/{id}/`

**Request:**
```json
{
  "status": "inactive",
  "reason": "maintenance"
}
```

### Device Health Check

**Endpoint:** `GET /api/devices/{id}/health/`

**Response:**
```json
{
  "device_id": 15,
  "overall_health": "good",
  "checks": {
    "connectivity": {
      "status": "ok",
      "latency_ms": 12
    },
    "cpu": {
      "status": "ok",
      "usage_percent": 18.5
    },
    "memory": {
      "status": "ok",
      "usage_percent": 35
    },
    "storage": {
      "status": "warning",
      "usage_percent": 85
    },
    "temperature": {
      "status": "ok",
      "celsius": 42
    }
  },
  "last_check": "2024-05-23T10:01:10Z"
}
```

---

## WebSocket Event Management

### Device Connection Flow

```
Device → [Handshake] → Backend
Device ← [Accepted] ← Backend

Device → [Register Session] → Backend
Device ← [Session Confirmed] ← Backend

Device ⇄ [Continuous Data Stream] ⇄ Backend

Device → [Health Report] → Backend (every 60s)

Device → [Disconnect] → Backend
Device ← [Disconnected] ← Backend
```

### Message Handling Code Example

**JavaScript:**
```javascript
class DeviceManager {
  async connectDevice(deviceId, deviceToken) {
    this.ws = new WebSocket(
      `wss://teachsense.onrender.com/ws/devices/${deviceId}/?token=${deviceToken}`
    );

    this.ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);
      this.handleMessage(msg);
    });
  }

  handleMessage(msg) {
    switch(msg.type) {
      case 'handshake_response':
        console.log('Device connected:', msg);
        this.sendAudioData();
        break;
      case 'acknowledge':
        console.log('Data received by backend');
        break;
      case 'error':
        console.error('Backend error:', msg);
        break;
    }
  }

  async sendAudioData() {
    const audioContext = new AudioContext();
    const mediaStream = await navigator.mediaDevices.getUserMedia({ 
      audio: true 
    });
    const source = audioContext.createMediaStreamAudioSource(mediaStream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      const audioData = e.inputBuffer.getChannelData(0);
      const frame = {
        type: 'audio_frame',
        data_base64: btoa(new Uint8Array(audioData).join(',')),
        timestamp: new Date().toISOString()
      };
      this.ws.send(JSON.stringify(frame));
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
  }
}
```

---

## Device Commands

### Remote Control

**Endpoint:** `POST /api/devices/{id}/command/`

**Request:**
```json
{
  "command": "start_recording",
  "parameters": {
    "session_id": 1,
    "quality": "high"
  }
}
```

**Response:**
```json
{
  "command_id": "cmd_12345",
  "status": "executed",
  "result": "Recording started",
  "timestamp": "2024-05-23T10:01:15Z"
}
```

### Supported Commands

| Command | Parameter | Effect |
|---------|-----------|--------|
| `start_recording` | quality | Start capturing audio |
| `stop_recording` | - | Stop capturing |
| `pause_stream` | - | Pause data stream |
| `resume_stream` | - | Resume data stream |
| `restart_device` | - | Restart device |
| `reset_buffer` | - | Clear buffers |
| `update_config` | config_data | Update device config |
| `trigger_diagnostics` | - | Run self-test |

---

## Error Handling

### Common Device Errors

```json
{
  "type": "error",
  "error_code": "DEVICE_DISCONNECTED",
  "message": "Device lost connection",
  "timestamp": "2024-05-23T10:01:20Z"
}
```

### Error Recovery

**Automatic Reconnection:**
```javascript
function autoReconnect(deviceId, deviceToken, maxRetries = 5) {
  let retryCount = 0;

  function connect() {
    try {
      deviceManager.connectDevice(deviceId, deviceToken);
      retryCount = 0;
    } catch (error) {
      if (retryCount < maxRetries) {
        retryCount++;
        setTimeout(connect, Math.pow(2, retryCount) * 1000);
      }
    }
  }

  connect();
}
```

---

## Best Practices

1. **Connection Management**
   - Implement heartbeat/keep-alive (30-second intervals)
   - Auto-reconnect with exponential backoff
   - Clean disconnection on shutdown

2. **Audio Quality**
   - Use appropriate sample rate (44.1kHz or 48kHz minimum)
   - Maintain consistent bit depth (16-bit minimum)
   - Buffer audio appropriately

3. **Error Handling**
   - Log all errors with timestamps
   - Implement graceful degradation
   - Alert operators on critical failures

4. **Security**
   - Rotate device tokens regularly
   - Use HTTPS/WSS always
   - Validate all incoming data
   - Encrypt sensitive audio data at rest

5. **Performance**
   - Monitor CPU and memory usage
   - Implement data compression
   - Use appropriate batch sizes
   - Profile and optimize loops

---

## Troubleshooting

### Device Won't Connect
- Check device key is correct
- Verify IP/hostname resolution
- Check firewall rules
- Ensure device certificate is valid

### Audio Stuttering
- Reduce buffer size
- Check network latency
- Increase device CPU priority
- Enable network optimization

### Connection Drops
- Implement more robust heartbeat
- Check WiFi signal strength
- Verify network stability
- Review backend logs
