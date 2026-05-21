# TeachSense Unified Architecture

## Overview

TeachSense is a real-time classroom intelligence platform that orchestrates multi-LLM inference, preprocessing, and analytics to process lecture content and evaluate student responses in an integrated pipeline.

**Core strengths:**
- **Multi-LLM Orchestration**: Runs inference across GPT-4, Claude, and Mistral in parallel with consensus merging.
- **Preprocessing Engine**: Cleans transcripts, removes noise, normalizes speech patterns before LLM processing.
- **Session State Management**: Explicit processing stages tracked in the database (transcript → summary → questions → evaluations → results).
- **Analytics Layer**: Real-time aggregation of session metrics and historical tracking.
- **Deterministic Fallback**: Works offline or without API keys using local generation.

---

## System Architecture

### Layer 1: Data Ingestion & Preprocessing

```
Raw Transcript (STT Output)
    ↓
TranscriptPreprocessor (common/utils/preprocessing.py)
    - Removes filler words (um, uh, like, etc.)
    - Fixes common STT errors
    - Normalizes punctuation & whitespace
    - Confidence scoring
    ↓
DataValidator
    - Validates length, structure
    - Quality thresholds
    ↓
Cleaned Transcript (ready for LLM)
```

**Files:**
- [common/utils/preprocessing.py](../common/utils/preprocessing.py) - Preprocessing engine
- [apps/transcripts/services/transcript_validator.py](../apps/transcripts/services/transcript_validator.py) - Validation rules

---

### Layer 2: LLM Provider Layer

**Provider Architecture:**
```
LLMProvider (Abstract)
    ├── OpenAIProvider (GPT-4, GPT-4-mini)
    ├── ClaudeProvider (Claude-3-sonnet)
    └── MistralProvider (Mistral-medium)

Each provider supports:
1. Remote Mode: Real API calls (if credentials available)
2. Fallback Mode: Deterministic local generation (structured JSON output)
```

**Key Files:**
- [apps/integrations/llm/providers.py](../apps/integrations/llm/providers.py) - Provider implementations
- Helper functions:
  - `_extract_section()` - Parse prompt structure
  - `_keywords_from_text()` - Extract content keywords
  - `_local_summary_response()` - Generate fallback summary
  - `_local_questions_response()` - Generate fallback questions
  - `_local_evaluation_response()` - Generate fallback evaluation

---

### Layer 3: Multi-LLM Ensemble

**Unified Orchestration:**
```
EnsembleConfig
    - primary_models: ["gpt-4-mini", "claude-3-sonnet"]
    - fallback_models: ["gpt-3.5-turbo"]
    - merge_strategy: WEIGHTED_AVERAGE
    - timeout_per_model: 30s
    ↓
LLMEnsemble.run_ensemble()
    ↓
Parallel Inference
    - Model 1: OpenAI (fast response + confidence)
    - Model 2: Claude (thorough response + reasoning)
    - Fallback: Local (if timeout/error)
    ↓
Response Merging
    - Agreement Score: How well models aligned
    - Confidence Score: Averaged model confidence
    - Merged Response: Best-confidence selection
```

**Task-Specific Methods:**
- `process_lecture_summary()` - Generate structured summary
- `generate_assessment_questions()` - Create question set
- `evaluate_student_response()` - Score response

**Files:**
- [apps/integrations/llm/ensemble.py](../apps/integrations/llm/ensemble.py) - Ensemble orchestrator
- [apps/integrations/llm/providers.py](../apps/integrations/llm/providers.py) - Provider implementation
- [apps/integrations/ensemble_config.py](../apps/integrations/ensemble_config.py) - Configuration

---

### Layer 4: Lecture Processing Orchestrator

**Complete Pipeline:**
```
Session Created
    ↓
[STAGE 1: PREPROCESSING]
LectureProcessingOrchestrator._stage_preprocessing()
    - Clean transcript
    - Validate structure
    - Confidence scoring
    - Results: cleaned_text, confidence_score
    ↓ [STAGE 2: SUMMARIZATION]
LectureProcessingOrchestrator._stage_summarization()
    - Run ensemble on cleaned transcript
    - Returns: summary, agreement_score, confidence_score
    ↓ [STAGE 3: QUESTION GENERATION]
LectureProcessingOrchestrator._stage_generate_questions()
    - Run ensemble on summary
    - Returns: questions[], agreement_score, confidence_score
    ↓ [STAGE 4: EVALUATION]
LectureProcessingOrchestrator.evaluate_student_responses()
    - Score responses via ensemble
    - Returns: evaluations[], agreement_scores
    ↓
LectureProcessingResult (complete)
    - overall_success
    - processing_stages (detailed results)
    - total_processing_time_ms
    - errors (if any)
```

**Files:**
- [apps/summaries/services/orchestration.py](../apps/summaries/services/orchestration.py) - Processing orchestrator
- [apps/summaries/services/response_mergers.py](../apps/integrations/services/response_mergers.py) - Response aggregation

---

### Layer 5: Celery Task Pipeline

#### Main Processing Chain

**1. `process_lecture_session()` [apps/lectures/tasks.py]**
```
Input: session_id (transcript already exists)
Process:
  1. Mark transcript_ready = True
  2. Initialize ensemble (auto-providers if not supplied)
  3. Run LectureProcessingOrchestrator.process_lecture()
  4. Store results:
     - Create/update Summary record
     - Create Question records with scores
     - Mark summary_ready, questions_ready
  5. Queue TTS task
  6. Save session.status = "completed"
Output: {session_id, success, errors, total_time_ms}
```

**2. `run_tts_for_questions()` [apps/lectures/tasks.py]**
```
Input: session_id
Process:
  1. Fetch all questions for session
  2. Generate TTS audio for each question
  3. Store audio file references
Output: {session_id, success}
```

**3. `evaluate_session_responses()` [apps/evaluations/tasks.py]**
```
Input: session_id
Process:
  1. Fetch all Response objects for session
  2. Initialize ensemble
  3. For each response:
     - Run ensemble.evaluate_student_response()
     - Parse JSON evaluation
     - Create Evaluation record
     - Update Response with scores
       - accuracy_score, completeness_score, clarity_score
       - overall_score, feedback
       - ensemble_agreement_score, ensemble_confidence_score
     - Mark evaluation_status = "evaluated"
  4. Mark session.evaluation_ready = True
  5. Queue downstream tasks:
     - compute_teaching_effectiveness()
     - publish_results_to_student_view()
     - refresh_session_analytics()
Output: {session_id, evaluated, success}
```

**4. `compute_teaching_effectiveness()` [apps/lectures/tasks.py]**
```
Input: session_id
Process:
  1. Calculate score based on:
     - Summary quality
     - Student comprehension (avg response scores)
     - Engagement (response rate)
  2. Store in session.teaching_effectiveness_score
Output: {session_id, effectiveness_score}
```

**5. `refresh_session_analytics()` [apps/analytics/tasks.py]**
```
Input: session_id
Process:
  1. Aggregate metrics:
     - total_questions (from Question count)
     - evaluated_responses (from Response count)
     - average_accuracy, completeness, clarity
     - overall_effectiveness (from session or response avg)
     - summary_confidence (from Summary)
     - engagement_score (response rate %)
  2. Build insights list
  3. Store/update SessionAnalytics record
Output: {session_id, analytics_id, success}
```

**6. `publish_results_to_student_view()` [apps/lectures/tasks.py]**
```
Input: session_id
Process:
  1. Verify all stages complete:
     - transcript_ready, summary_ready, questions_ready, evaluation_ready
  2. Mark results_published = True
  3. (TODO: WebSocket broadcast to connected students)
Output: {session_id, published}
```

---

### Layer 6: Data Models

#### Session State Tracking
```python
# apps/lectures/models.py - Session
Fields:
  - transcript_ready (default: False)
  - summary_ready (default: False)
  - questions_ready (default: False)
  - evaluation_ready (default: False)
  - results_published (default: False)
  - teaching_effectiveness_score
  - average_student_comprehension
```

#### Summary & Quality Metrics
```python
# apps/summaries/models.py - Summary
Fields:
  - structured_summary (preprocessed + ensemble merged)
  - key_concepts (extracted keywords)
  - important_points (pedagogical highlights)
  - accuracy_score, model_agreement_score
  - models_used (which LLMs generated this)

# apps/questions/models.py - Question
Fields:
  - question_text, model_answer, difficulty_level
  - ensemble_agreement_score (how well LLMs agreed on this question)
  - ensemble_confidence_score (overall quality certainty)

# apps/responses/models.py - Response
Fields:
  - response_text, audio_file
  - evaluation_status (pending, evaluated, skipped)
  - accuracy_score, completeness_score, clarity_score, overall_score
  - feedback
  - ensemble_agreement_score, ensemble_confidence_score

# apps/evaluations/models.py - Evaluation
Fields:
  - evaluator_model ("multi-llm-ensemble")
  - accuracy_assessment, completeness_assessment, clarity_assessment
  - strengths, areas_for_improvement
  - evaluation_agreement_score (consensus level)
```

#### Analytics Storage
```python
# apps/analytics/models.py - SessionAnalytics
Fields:
  - session (OneToOne)
  - total_questions
  - evaluated_responses
  - average_accuracy, average_completeness, average_clarity
  - overall_effectiveness
  - summary_confidence
  - engagement_score
  - insights (list of strings)
```

---

### Layer 7: API Endpoints

#### Analytics API
```
GET /api/analytics/sessions/<session_id>/
Response:
{
  "session_id": 1,
  "total_questions": 5,
  "evaluated_responses": 3,
  "average_accuracy": 75.5,
  "average_completeness": 72.0,
  "average_clarity": 78.0,
  "overall_effectiveness": 75.0,
  "summary_confidence": 0.88,
  "engagement_score": 60.0,
  "insights": [
    "Lecture summary completed successfully.",
    "5 questions were generated for the session.",
    "3 responses were evaluated.",
    "Results were published to the student view."
  ]
}
```

#### Dashboard API
```
GET /api/dashboards/overview/
Response:
{
  "sessions": [
    {
      "id": 1,
      "title": "Photosynthesis Basics",
      "status": "completed",
      "transcript_ready": true,
      "summary_ready": true,
      "questions_ready": true,
      "evaluation_ready": true,
      "results_published": true,
      "teaching_effectiveness_score": 78.5,
      "average_student_comprehension": 75.0,
      "analytics": {
        "total_questions": 5,
        "evaluated_responses": 4,
        "average_accuracy": 76.0,
        ...
      },
      "started_at": "2026-05-21T10:00:00Z"
    },
    ...
  ]
}
```

**Files:**
- [apps/analytics/api/views.py](../apps/analytics/api/views.py) - Analytics endpoints
- [apps/dashboards/views.py](../apps/dashboards/views.py) - Dashboard overview

---

## Execution Flow: End-to-End Example

### Scenario: Lecturer records a 30-minute session

**1. Session Setup**
```
Lecturer starts recording → Session created in database
Audio captured + STT service runs → Transcript generated
Transcript stored in DB → session.transcript_ready = False (initially)
```

**2. Preprocessing Triggered**
```
celery: process_lecture_session(session_id=1)
    ↓
Fetch transcript text
Initialize ensemble with fallback providers
    ↓
LectureProcessingOrchestrator.process_lecture()
    Stage 1: Clean transcript
        Remove: "Um, like, you know" → "Clean text"
        Confidence: 0.87
    ↓
    Stage 2: Generate summary
        Ensemble runs on cleaned text
        GPT-4-mini: "This lecture covers X, Y, Z..."
        Claude: "The core topics are..."
        Merge: Weighted average → final summary
        Agreement: 0.91, Confidence: 0.89
    ↓
    Stage 3: Generate questions
        Ensemble extracts key concepts from summary
        GPT-4-mini generates 5 potential questions
        Claude validates + refines
        Merge: Top 5 questions (agreement, confidence)
    ↓
Database saves:
    Transcript.preprocessed = True
    Summary created (structured_summary, models_used, accuracy_score)
    5 Question records (with ensemble scores)
    session.summary_ready = True, questions_ready = True
    ↓
Queue: run_tts_for_questions(session_id=1)
```

**3. TTS Generation**
```
celery: run_tts_for_questions(session_id=1)
    ↓
For each question:
    Call TTS service
    Save audio file → Question.audio_file
    ↓
All done
```

**4. Student Responses Submitted**
```
Students see questions on device
Each student records audio response
Audio transcribed → Response record created
    response_text, audio_file
    evaluation_status = "pending"
```

**5. Evaluation Triggered**
```
celery: evaluate_session_responses(session_id=1)
    ↓
For each Response:
    ensemble.evaluate_student_response(
        question="What is photosynthesis?",
        student_answer="It's when plants use sunlight...",
        model_answer="Photosynthesis is the process..."
    )
    ↓
    GPT-4: {"score": 72, "feedback": "Good start..."}
    Claude: {"score": 75, "feedback": "Covers main points..."}
    Merge: score=73, agreement=0.88, confidence=0.81
    ↓
    Evaluation record created
    Response updated:
        accuracy_score=73, completeness_score=70, clarity_score=75
        overall_score=73
        evaluation_status="evaluated"
    ↓
session.evaluation_ready = True
```

**6. Teaching Effectiveness Calculation**
```
celery: compute_teaching_effectiveness(session_id=1)
    ↓
Calculate:
    Content quality (summary agreement/confidence)
    Student comprehension (avg response scores)
    Engagement (% questions answered)
    ↓
    teaching_effectiveness_score = 76.5
```

**7. Analytics Aggregation**
```
celery: refresh_session_analytics(session_id=1)
    ↓
SessionAnalytics created:
    total_questions: 5
    evaluated_responses: 4 (1 student absent)
    average_accuracy: 72.5
    average_completeness: 69.0
    average_clarity: 73.0
    overall_effectiveness: 76.5
    engagement_score: 80.0
    insights: ["Summary complete", "5 questions", "4 evaluated", "Results published"]
```

**8. Results Published**
```
celery: publish_results_to_student_view(session_id=1)
    ↓
Verify all stages complete
session.results_published = True
(TODO: WebSocket → student dashboards)
    ↓
Lecturer + students see results instantly
```

**9. Retrieve Analytics Via API**
```
GET /api/analytics/sessions/1/
Response: {full analytics payload}

GET /api/dashboards/overview/
Response: [session records with embedded analytics]
```

---

## Key Design Decisions

### 1. Preprocessing Before LLM Inference
**Why:** Raw STT output is noisy and costs more to process. Cleaning first improves:
- Context quality (less noise)
- Hallucination reduction (clearer intent)
- LLM efficiency (fewer tokens)
- Cost (shorter prompts)

### 2. Multi-LLM Specialization
**Why:** Different models excel at different tasks:
- GPT-4: Fast, consistent question generation
- Claude: Deep reasoning, nuanced evaluation
- Mistral: Cost-effective summarization
- Local fallback: Always available, deterministic

### 3. Explicit Session State Tracking
**Why:** Avoids partial/inconsistent results:
- `transcript_ready` → transcript processed
- `summary_ready` → summary generated
- `questions_ready` → questions created
- `evaluation_ready` → all responses scored
- `results_published` → visible to users

### 4. Deferred Result Publishing
**Why:** Better UX than fragmented real-time updates:
- Complete all processing first
- Publish as atomic bundle
- Students see final state all at once
- No incomplete interim dashboards

### 5. Ensemble Agreement & Confidence Tracking
**Why:** Quality assurance:
- Low agreement → multiple models disagree (red flag)
- Low confidence → model expressed uncertainty (review needed)
- Both stored: enables human review, improves over time

### 6. Local Fallback Mode
**Why:** Offline/demo capability:
- Works without API keys
- Deterministic JSON output (testable)
- Structured responses (not plain text)
- Develops locally, scales to cloud

---

## Integration with Existing Systems

### Incoming: Device/STT
```
Device records audio
      ↓
STT service transcribes
      ↓
Transcript POST /api/lectures/<id>/transcripts/
      ↓
Backend stores + queues process_lecture_session
      ↓
(System wires from here)
```

### Outgoing: Student Dashboard
```
session.results_published = True
      ↓
WebSocket → StudentDashboardConsumer
      ↓
Student sees:
  - Summary
  - Questions
  - Their responses + scores
  - Feedback
  - Overall session metrics
```

---

## Future Extensibility

### 1. Hardware-to-Cloud Workflow
- Device queues tasks locally
- Syncs results when connected
- Cloud processes + stores analytics

### 2. Edge Preprocessing
- On-device transcript cleaning (reduce bandwidth)
- Local fallback inference (offline mode)

### 3. Advanced Merging Strategies
- Semantic clustering (group similar responses)
- Confidence weighting (trust higher-confidence models more)
- Task-specific routing (different models per task)

### 4. Historical Learning
- Track model accuracy over time
- Adjust weights based on historical agreement
- Identify patterns (e.g., Claude better at evaluation)

---

## Deployment Checklist

- [ ] Install dependencies: `pip install openai anthropic mistralai`
- [ ] Set environment variables:
  ```
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  MISTRAL_API_KEY=...
  ```
- [ ] Run migrations:
  ```
  python manage.py migrate analytics
  ```
- [ ] Start Celery worker:
  ```
  celery -A config worker -l info
  ```
- [ ] Test ensemble locally (no API keys):
  ```python
  from apps.integrations.llm.ensemble import LLMEnsemble, EnsembleConfig
  ensemble = LLMEnsemble(config=EnsembleConfig(), providers={})
  result = ensemble.process_lecture_summary("cleaned transcript")
  ```

---

## Monitoring & Observability

### Logs
- `LectureProcessingOrchestrator`: Stage timing, errors
- Provider fallbacks: Warning logs when API unavailable
- Analytics: Aggregation completion

### Metrics to Track
- **Preprocessing**: Confidence scores over time
- **Ensemble**: Agreement rates per model, agreement vs confidence
- **Evaluations**: Score distributions, human review rate
- **Analytics**: Effectiveness trends, engagement patterns

### Dashboard Integration
- `/api/analytics/sessions/<id>/` → Real-time metrics
- `/api/dashboards/overview/` → Historical trends
- Admin panel: Monitor all sessions, review low-confidence evaluations

---

## Context Window & Performance

| Component | Typical Size | Time |
|-----------|--------------|------|
| Preprocessing | 10-30KB text → 8-25KB cleaned | 100-500ms |
| Summarization (GPT-4) | Ensemble (2-3 models parallel) | 3-8s |
| Question Generation | Ensemble (2 models parallel) | 4-10s |
| Evaluation (per response) | Ensemble (2 models parallel) | 2-5s per response |
| Analytics Aggregation | 5-50 responses in transaction | 200-500ms |
| End-to-end (30 min lecture, 20 responses) | Full pipeline | ~1-3 min |

---

