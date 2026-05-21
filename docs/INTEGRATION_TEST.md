# TeachSense Integration Test Guide

This guide helps verify that the unified architecture is working end-to-end.

## Prerequisites

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Start Celery worker (separate terminal)
celery -A config worker -l info
```

---

## Test 1: Provider Fallback Mode (No API Keys)

**Purpose:** Verify that providers work without credentials.

```bash
# Shell into Django
python manage.py shell
```

```python
from apps.integrations.llm.providers import OpenAIProvider, ClaudeProvider, MistralProvider
from dataclasses import dataclass

# Test OpenAI provider without API key
provider = OpenAIProvider(api_key=None)
print(f"OpenAI available: {provider.is_available()}")  # Should be True

# Test summarization fallback
result = provider._local_infer(
    task="summarization",
    prompt="This is a lecture about photosynthesis. Plants convert sunlight into energy."
)
print(f"OpenAI fallback result:\n{result}")

# Test Claude provider
claude = ClaudeProvider(api_key=None)
print(f"Claude available: {claude.is_available()}")  # Should be True

# Test question generation fallback
result = claude._local_infer(
    task="question_generation",
    prompt="Key concepts: photosynthesis, chlorophyll, ATP"
)
print(f"Claude fallback result:\n{result}")

# Test Mistral provider
mistral = MistralProvider(api_key=None)
print(f"Mistral available: {mistral.is_available()}")  # Should be True

# Test evaluation fallback
result = mistral._local_infer(
    task="evaluation",
    prompt="""Question: What is photosynthesis?
Student Answer: It's when plants make food from sunlight.
Model Answer: Photosynthesis is the process by which plants convert light energy into chemical energy."""
)
print(f"Mistral fallback result:\n{result}")

exit()
```

**Expected Output:**
- All providers report `available: True`
- All fallback results are valid JSON with proper structure
- Confidence scores in 0.76-0.84 range

---

## Test 2: Ensemble Self-Configuration

**Purpose:** Verify that LLMEnsemble auto-builds providers.

```python
from apps.integrations.llm.ensemble import LLMEnsemble, EnsembleConfig

# Create ensemble without explicit providers
# This will automatically create OpenAI, Claude, Mistral with fallback mode
config = EnsembleConfig(
    primary_models=["gpt-4-mini", "claude-3-sonnet", "open-mistral"],
    merge_strategy="WEIGHTED_AVERAGE"
)

ensemble = LLMEnsemble(config=config, providers=None)  # None triggers auto-build

print(f"Ensemble has {len(ensemble.providers)} providers:")
for model_id, provider in ensemble.providers.items():
    print(f"  - {model_id}: {type(provider).__name__}")

# Test summarization
summary_result = ensemble.process_lecture_summary(
    lecture_text="This lecture covers enzyme kinetics and cofactors."
)
print(f"\nSummary result:")
print(f"  Merged response: {summary_result.merged_response[:100]}...")
print(f"  Agreement score: {summary_result.agreement_score}")
print(f"  Confidence score: {summary_result.confidence_score}")

exit()
```

**Expected Output:**
- 3 providers auto-created (OpenAI, Claude, Mistral)
- Summary generated successfully
- Agreement and confidence scores present and non-zero

---

## Test 3: Lecture Processing Pipeline

**Purpose:** End-to-end processing from transcript to questions.

```bash
# Shell into Django
python manage.py shell
```

```python
from apps.lectures.models import Session, Lecture
from apps.transcripts.models import Transcript
from apps.lectures.tasks import process_lecture_session
from apps.questions.models import Question

# Create test data
lecture = Lecture.objects.create(title="Test Lecture", description="Testing ensemble")
session = Session.objects.create(lecture=lecture, title="Test Session")

# Create transcript
transcript_text = """
In today's lecture we're going to talk about cellular respiration.
Cellular respiration is the process by which cells extract energy from nutrients.
There are three main stages: glycolysis, the Krebs cycle, and the electron transport chain.
Each stage releases energy that gets stored in ATP molecules.
Questions to consider: why is ATP important? What's the role of mitochondria?
"""

transcript = Transcript.objects.create(
    session=session,
    transcript_text=transcript_text,
    confidence_score=0.95
)

print(f"Created session {session.id} with transcript {transcript.id}")
print(f"Initial state:")
print(f"  transcript_ready: {session.transcript_ready}")
print(f"  summary_ready: {session.summary_ready}")
print(f"  questions_ready: {session.questions_ready}")

# Run processing synchronously (for testing)
result = process_lecture_session(session.id)
print(f"\nProcessing result: {result}")

# Refresh session from DB
session.refresh_from_db()
print(f"\nAfter processing:")
print(f"  transcript_ready: {session.transcript_ready}")
print(f"  summary_ready: {session.summary_ready}")
print(f"  questions_ready: {session.questions_ready}")
print(f"  status: {session.status}")

# Check generated questions
questions = Question.objects.filter(session=session)
print(f"\nGenerated {questions.count()} questions:")
for q in questions:
    print(f"  Q{q.order}: {q.question_text[:60]}...")
    print(f"    Difficulty: {q.difficulty_level}")
    print(f"    Agreement: {q.ensemble_agreement_score}")
    print(f"    Confidence: {q.ensemble_confidence_score}")

exit()
```

**Expected Output:**
- Session created successfully
- Processing completes without error
- All boolean flags transition to True
- 3-5 questions generated with scores
- Difficulty levels are valid (easy/medium/hard)
- Agreement and confidence scores range 0.0-1.0

---

## Test 4: Response Evaluation

**Purpose:** Evaluate student responses and create Evaluation records.

```python
from apps.responses.models import Response
from apps.evaluations.models import Evaluation
from apps.evaluations.tasks import evaluate_session_responses

# Get existing session with questions and responses
session_id = 1  # Or use the session from Test 3

# Create test responses (if they don't exist)
from apps.questions.models import Question
questions = Question.objects.filter(session_id=session_id)

for question in questions[:2]:  # Test with 2 questions
    Response.objects.get_or_create(
        question=question,
        defaults={
            'response_text': 'ATP is the energy currency of the cell that stores chemical energy from food molecules.',
            'evaluation_status': 'pending'
        }
    )

# Run evaluation
result = evaluate_session_responses(session_id)
print(f"Evaluation result: {result}")

# Check evaluations were created
session = Session.objects.get(id=session_id)
evaluations = Evaluation.objects.filter(response__question__session=session)
print(f"\nCreated {evaluations.count()} evaluations:")
for e in evaluations:
    print(f"  Evaluator: {e.evaluator_model}")
    print(f"  Accuracy: {e.response.accuracy_score}")
    print(f"  Completeness: {e.response.completeness_score}")
    print(f"  Clarity: {e.response.clarity_score}")
    print(f"  Overall: {e.response.overall_score}")
    print(f"  Status: {e.response.evaluation_status}")

# Check session state
session.refresh_from_db()
print(f"\nSession after evaluation:")
print(f"  evaluation_ready: {session.evaluation_ready}")

exit()
```

**Expected Output:**
- Evaluation records created successfully
- Response scores populated (0.0-100.0)
- Feedback text present
- evaluation_status changed to 'evaluated'
- ensemble_agreement_score and ensemble_confidence_score populated
- session.evaluation_ready = True

---

## Test 5: Analytics Aggregation

**Purpose:** Compute session analytics from aggregated metrics.

```python
from apps.analytics.services.service import get_analytics_service
from apps.sessions.models import Session

session_id = 1  # Use existing session with evaluations

# Get analytics service (singleton)
service = get_analytics_service()

# Compute analytics
analytics = service.compute_session_analytics(session_id)

print(f"Session {session_id} Analytics:")
print(f"  Total Questions: {analytics.total_questions}")
print(f"  Evaluated Responses: {analytics.evaluated_responses}")
print(f"  Average Accuracy: {analytics.average_accuracy}")
print(f"  Average Completeness: {analytics.average_completeness}")
print(f"  Average Clarity: {analytics.average_clarity}")
print(f"  Overall Effectiveness: {analytics.overall_effectiveness}")
print(f"  Summary Confidence: {analytics.summary_confidence}")
print(f"  Engagement Score: {analytics.engagement_score}")
print(f"  Insights: {analytics.insights}")

exit()
```

**Expected Output:**
- All metric fields populated
- Scores in reasonable ranges (0.0-100.0)
- Insights list contains 3-5 items describing processing stages
- Analytics record saved to SessionAnalytics table

---

## Test 6: API Endpoints

**Purpose:** Verify REST endpoints work correctly.

```bash
# In separate terminal with server running
python manage.py runserver

# Test analytics endpoint
curl -X GET http://localhost:8000/api/analytics/sessions/1/

# Should return:
# {
#   "session_id": 1,
#   "total_questions": 5,
#   "evaluated_responses": 3,
#   "average_accuracy": 75.5,
#   "average_completeness": 72.0,
#   "average_clarity": 78.0,
#   "overall_effectiveness": 75.0,
#   "summary_confidence": 0.88,
#   "engagement_score": 60.0,
#   "insights": [...]
# }

# Test dashboard endpoint
curl -X GET http://localhost:8000/api/dashboards/overview/

# Should return:
# {
#   "sessions": [
#     {
#       "id": 1,
#       "title": "Test Session",
#       "status": "completed",
#       "transcript_ready": true,
#       "summary_ready": true,
#       ...
#       "analytics": {...}
#     }
#   ]
# }
```

**Expected Output:**
- Analytics endpoint returns 200 with full metrics
- Dashboard endpoint returns 200 with session list
- Analytics object nested in each session
- All fields present and properly formatted

---

## Test 7: State Machine Verification

**Purpose:** Verify processing state transitions are correct.

```python
from apps.sessions.models import Session

session = Session.objects.get(id=1)

print("Session state machine:")
print(f"  transcript_ready: {session.transcript_ready}")        # Should be True after process_lecture_session
print(f"  summary_ready: {session.summary_ready}")             # Should be True after process_lecture_session
print(f"  questions_ready: {session.questions_ready}")         # Should be True after process_lecture_session
print(f"  evaluation_ready: {session.evaluation_ready}")       # Should be True after evaluate_session_responses
print(f"  results_published: {session.results_published}")     # Should be True after publish_results

# All should be True for a completed session
all_ready = all([
    session.transcript_ready,
    session.summary_ready,
    session.questions_ready,
    session.evaluation_ready,
    session.results_published
])
print(f"\nAll states ready: {all_ready}")
```

**Expected Output:**
- All boolean flags set to True in sequence
- Final state represents complete processing pipeline

---

## Troubleshooting

### Problem: "No module named 'openai'" when running tests

**Solution:** Providers lazy-load SDKs. They're optional. Test should still pass with local fallback.

### Problem: Ensemble returns None for merged_response

**Solution:** All models must return valid JSON. Check that fallback functions are being called:
```python
provider = OpenAIProvider(api_key=None)
provider._local_infer(task="summarization", prompt="test")
```

### Problem: Celery tasks not executing

**Solution:** Ensure Celery worker is running in separate terminal:
```bash
celery -A config worker -l info
```

For testing without Celery, call task functions directly:
```python
from apps.lectures.tasks import process_lecture_session
result = process_lecture_session(session_id)  # Runs synchronously
```

### Problem: Analytics returning empty insights

**Solution:** Make sure responses are marked `evaluation_status='evaluated'`. Check:
```python
Response.objects.filter(question__session_id=1).values('evaluation_status').distinct()
```

---

## Performance Benchmarks

| Test | Expected Time |
|------|----------------|
| Provider fallback (single model) | <100ms |
| Ensemble (3 models parallel) | 3-10s |
| Processing pipeline (30-min lecture, 1 question) | 10-15s |
| Evaluation pipeline (5 responses) | 10-20s |
| Analytics aggregation (20 questions, 15 responses) | 200-500ms |
| API response (analytics endpoint) | <100ms |

---

## Success Criteria

✅ **Integration test passes if:**
- [ ] Providers work without API keys (Test 1)
- [ ] Ensemble auto-configures (Test 2)
- [ ] Lecture processing completes with questions persisted (Test 3)
- [ ] Response evaluation creates Evaluation records (Test 4)
- [ ] Analytics computed and stored (Test 5)
- [ ] API endpoints return 200 with correct data (Test 6)
- [ ] All session state flags transition correctly (Test 7)

---

