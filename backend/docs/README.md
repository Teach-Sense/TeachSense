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

1. Frontend creates a `Session` via `POST /api/sessions/` with `title` and optional `class_taught`.
2. Device connects to `ws/sessions/<session_id>/`
3. Frontend sends `{"type": "start_recording", "topic": "...", "class_taught": "..."}`
4. Device streams binary PCM audio chunks
5. Frontend sends `{"type": "stop_recording"}`
6. Backend transcribes audio via OpenAI Whisper (`whisper-1`)
7. Backend generates questions via OpenAI GPT-4o-mini (max 5, default 3)
8. Backend waits ~5 seconds, then sends questions one-by-one over WebSocket with 2-second gaps
9. Device speaks question, listens to response, sends response back (text or base64 audio)
10. Backend optionally transcribes response audio with Whisper
11. Backend receives all responses
12. Backend calculates scores via GPT-4o-mini:
    - Student Comprehension: 70%
    - Teaching Scope: 30%
    - total = comprehension * 0.7 + scope * 0.3
13. Backend generates tips via GPT-4o-mini:
    - `topics_to_revisit`: topics students struggled with
    - `explanation_tips`: ways to explain difficult concepts better
    - `top_three`: exactly 3 actionable things to do next lecture
14. Backend sends final results (scores + tips) to device

## Architecture

### Session Lifecycle

- REST API: `POST /api/sessions/` creates a session
- WebSocket: `ws/sessions/<session_id>/` handles the full recording and AI pipeline
- Session states: `draft` → `recording` → `processing` → `awaiting_responses` → `completed`

### Audio Pipeline

- Device streams raw PCM 16-bit LE, 16 kHz, mono as binary WebSocket frames
- On `stop_recording`, chunks are assembled into a WAV file
- WAV is sent to OpenAI Whisper for transcription
- Transcript is returned to frontend and used for AI question generation

### AI Processing (OpenAI)

- **Questions**: Transcript → GPT-4o-mini → JSON array of strings (max 5)
- **Sequential delivery**: Backend sends questions one-by-one over WebSocket
- **Responses**: Device sends back text or base64 audio per question
- **Scoring**: All responses + transcript → GPT-4o-mini → comprehension/scope/total
- **Tips**: All responses + transcript → GPT-4o-mini → topics_to_revisit/explanation_tips/top_three

### Data Model Changes

- `Session`: Added `class_taught`, `teaching_scope_score`, `tips` (JSONField); `lecturer` FK nullable
- `Device`: Simplified to `device_id`, `device_name`, `device_type` only
- Auth removed from device and session endpoints (`AllowAny`)

### Key Files

- `backend/config/consumers.py`: WebSocket state machine for recording, transcription, questions, responses, scoring
- `backend/apps/sessions/services/audio_service.py`: PCM validation and WAV conversion
- `backend/apps/sessions/services/ai_service.py`: OpenAI wrappers for questions, scores, tips
- `backend/apps/sessions/api/views.py`: Simplified session CRUD
- `backend/apps/sessions/api/serializers.py`: Session serializers with new fields
- `backend/apps/summaries/api/views.py`: Results endpoint for scores + tips
- `backend/apps/devices/api/views.py`: Simplified device views
- `backend/common/permissions.py`: Simplified device auth
- `backend/docs/README.md`: This file
