# TeachSense Backend

## Audio Data Format

Audio is streamed from the device to the backend as **raw PCM 16-bit little-endian, 16kHz, mono**.

### Required parameters
- `sample_rate`: 16000
- `channels`: 1
- `encoding`: `pcm_s16le`

### Optional parameters
- `frame_duration_ms`: 20 (default)

### Frame size
```
frame_size = sample_rate * channels * 2 bytes * (frame_duration_ms / 1000)
           = 16000 * 1 * 2 * 0.02
           = 640 bytes
```

## Backend Flow

1. Device connects to `ws/sessions/<session_id>/`
2. Frontend sends `{"type": "start_recording", "topic": "...", "class_taught": "..."}`
3. Device streams binary PCM audio chunks
4. Frontend sends `{"type": "stop_recording"}`
5. Backend transcribes audio via OpenAI Whisper
6. Backend generates questions via OpenAI GPT-4o-mini (max 5)
7. Backend waits ~1 minute
8. Backend sends questions one-by-one over WebSocket
9. Device speaks question, listens to response, sends response back
10. Backend receives all responses
11. Backend calculates scores:
    - Student Comprehension: 70%
    - Teaching Scope: 30%
12. Backend generates tips
13. Backend sends final results (scores + tips) to device
