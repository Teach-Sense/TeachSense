# Multi-LLM Ensemble System Implementation Guide

## Overview

TeachSense implements a **hybrid multi-LLM ensemble architecture** that maximizes accuracy in AI-driven lecture processing by:

1. **Pre-processing** raw transcript data to ensure quality
2. **Parallel inference** across multiple LLM models
3. **Intelligent response merging** using task-specific consensus strategies
4. **Confidence scoring** and human escalation for uncertain results

---

## Architecture Components

### 1. **Transcript Validator** (`apps/transcripts/services/transcript_validator.py`)

Ensures data quality before LLM processing.

**Responsibilities:**
- Clean filler words, stutters, artifacts
- Normalize whitespace and formatting
- Validate length constraints
- Compute quality score (0-1 scale)
- Chunk long transcripts for processing

**Example:**
```python
from apps.transcripts.services.transcript_validator import TranscriptValidator

validator = TranscriptValidator()
result = validator.validate(raw_transcript)

if result.is_valid:
    print(f"Quality: {result.quality_score}")
    print(f"Cleaned: {result.cleaned_text}")
else:
    print(f"Issues: {result.issues}")
```

**Quality Scoring:**
- Content presence (minimum meaningful text)
- Average word length (optimal: 4-7 chars)
- Sentence diversity (unique vs. repeated)
- Readability (ratio of filler removal)

---

### 2. **Multi-LLM Orchestrator** (`infrastructure/integrations/multi_llm_orchestrator.py`)

Manages parallel execution across multiple LLM providers.

**Model Pool:**
- **GPT-4**: Highest quality, ~2-3s latency (weight: 0.40)
- **GPT-4-mini**: Fast & cost-efficient (~1s latency, weight: 0.30)
- **Claude**: Alternative reasoning (weight: 0.20)
- **Llama-2 Local**: Fallback option (weight: 0.10)

**Execution Model:**
```
Validated Transcript
    ↓
[GPT-4] [GPT-4-mini] [Claude] [Local]
    ↓         ↓          ↓        ↓
Responses → Merger Engine → Final Output
```

**Key Features:**
- Async/await execution via asyncio
- Configurable model pool per task
- Automatic fallback on failure
- Timeout handling

---

### 3. **Response Mergers** (`apps/integrations/services/response_mergers.py`)

Task-specific strategies for combining LLM outputs.

#### A. **Summary Merging** (Semantic Consensus Voting)

```python
from apps.integrations.services.response_mergers import SummaryMerger, LLMResponse

summaries = [
    ("gpt-4", gpt4_summary_text),
    ("claude", claude_summary_text),
    ("gpt-4-mini", mini_summary_text),
]

merger = SummaryMerger()
merged = merger.merge(summaries)

# Result:
# - merged.text: Consensus summary with unique insights
# - merged.confidence: 0-1 confidence score
# - merged.agreement_level: How much models agreed
```

**Algorithm:**
1. Embed all summaries using sentence-transformer
2. Compute cosine similarity matrix
3. Group similar summaries (threshold: 0.85)
4. Select largest group as consensus base
5. Enrich with unique points from other summaries
6. Score: `(agreement_level) × (avg_model_weight)`

#### B. **Question Merging** (Quality Filtering + Aggregation)

```python
from apps.integrations.services.response_mergers import QuestionMerger, Question

question_sets = [
    ("gpt-4", [q1, q2, q3, ...]),
    ("gpt-4-mini", [q1', q2', q3', ...]),
]

merger = QuestionMerger()
merged = merger.merge(question_sets)

# Result:
# - merged.questions: Top-k deduplicated questions
# - merged.confidence: Composite confidence
# - merged.agreement_score: Model agreement %
```

**Algorithm:**
1. Filter by relevance (TF-IDF + semantic relevance to transcript)
2. Deduplicate using semantic matching (threshold: 0.90)
3. Rank by: `(quality_score × model_weight + diversity_bonus)`
4. Merge from top-k across models
5. Confidence: `(model_agreement % + relevance_score) / 2`

#### C. **Answer Evaluation** (Majority Voting)

```python
from apps.integrations.services.response_mergers import EvaluationMerger, EvaluationResult

evaluations = [
    EvaluationResult(
        correct=True,
        confidence=0.92,
        reasoning="Student correctly identified...",
        model_name="gpt-4"
    ),
    EvaluationResult(
        correct=True,
        confidence=0.85,
        reasoning="Response matches expected answer...",
        model_name="claude"
    ),
]

merger = EvaluationMerger()
merged = merger.merge(evaluations)

# Result:
# - merged.correct: Boolean consensus
# - merged.confidence: Avg confidence from agreeing models
# - merged.model_votes: {model_name: vote}
# - merged.requires_human_review: Flag if low agreement
```

**Algorithm:**
1. Count votes for `correct: True/False`
2. Consensus: `correct_votes > total_votes / 2`
3. Agreement score: `max(correct_votes, total_votes - correct_votes) / total_votes`
4. Average confidence from agreeing models
5. Flag for human review if:
   - Agreement < 70%
   - Confidence < 0.75
   - Tie vote (even split)

---

### 4. **Celery Task Orchestration** (`apps/integrations/tasks/ensemble_tasks.py`)

Asynchronous, distributed task execution via Celery + Redis.

**Task Chain for Session Processing:**

```
Session Started
    ↓
[Validate Transcripts]
    ↓
[Parallel Summarization] → GPT-4, GPT-4-mini, Claude
    ↓
[Merge Summaries]
    ↓
[Parallel Question Generation] → GPT-4, GPT-4-mini
    ↓
[Merge Questions]
    ↓
[Parallel Answer Evaluation] → GPT-4, Claude (per student response)
    ↓
[Merge Evaluations + Score Aggregation]
    ↓
[Calculate Teaching Effectiveness]
    ↓
[Publish Dashboards]
```

**Key Tasks:**

| Task | Input | Parallel Models | Timeout | Output |
|------|-------|---|---|---|
| `validate_transcript` | Raw transcript | N/A | 10s | Cleaned text, quality score |
| `run_parallel_summarization` | Transcript | GPT-4, GPT-4-mini, Claude | 60s | Summary responses |
| `merge_and_store_summary` | Summary responses | N/A | 10s | Stored summary + confidence |
| `run_parallel_question_generation` | Summary | GPT-4, GPT-4-mini | 90s | Question sets |
| `merge_and_store_questions` | Question responses | N/A | 10s | Stored merged questions |
| `run_parallel_evaluation` | Student response + question | GPT-4, Claude | 30s | Evaluation votes |
| `merge_and_store_evaluation` | Evaluation votes | N/A | 10s | Stored evaluation + human review flag |

**Usage Example:**

```python
from apps.integrations.tasks.ensemble_tasks import EnsembleTaskOrchestrator

orchestrator = EnsembleTaskOrchestrator()

# Trigger summarization ensemble for a session
orchestrator.create_summarization_job(
    session_id="sess_12345",
    transcript_id="trans_67890"
)

# Trigger question generation
orchestrator.create_question_generation_job(
    session_id="sess_12345",
    summary_id="summ_11111"
)

# Trigger answer evaluation
orchestrator.create_evaluation_job(
    session_id="sess_12345",
    student_response_id="resp_22222"
)
```

---

### 5. **Ensemble Configuration** (`apps/integrations/ensemble_config.py`)

Centralized configuration for ensemble system.

**Default Settings:**

```python
from apps.integrations.ensemble_config import EnsembleConfig, TaskEnsembleConfig

config = EnsembleConfig()

# Timeouts
config.SUMMARIZATION_TIMEOUT_SECONDS = 60
config.QUESTION_GENERATION_TIMEOUT_SECONDS = 90
config.ANSWER_EVALUATION_TIMEOUT_SECONDS = 30

# Quality thresholds
config.TRANSCRIPT_QUALITY_THRESHOLD = 0.50
config.SUMMARY_CONFIDENCE_THRESHOLD = 0.65
config.EVALUATION_CONFIDENCE_THRESHOLD = 0.75

# Merge thresholds
config.SUMMARY_SIMILARITY_THRESHOLD = 0.85
config.QUESTION_DUPLICATE_SIMILARITY = 0.90
config.EVALUATION_AGREEMENT_THRESHOLD = 0.70

# Escalation rules
config.ESCALATE_TO_HUMAN_IF_CONFIDENCE_BELOW = 0.70
config.ESCALATE_TO_HUMAN_IF_DISAGREEMENT_ABOVE = 0.30

# Get task-specific config
task_config = EnsembleConfig.for_task("answer_evaluation")
# → TaskEnsembleConfig(
#     timeout=30,
#     confidence_threshold=0.75,
#     max_models=2,
#     require_consensus=True
# )
```

---

## Data Flow Example: Answer Evaluation

**Scenario:** Student answers a comprehension question.

```
1. SUBMISSION
   ├─ Student response captured
   ├─ Question context retrieved
   └─ Task ID generated: "eval_uuid"

2. PARALLEL EVALUATION
   ├─ Task: evaluate_response_with_model(model="gpt-4")
   │  └─ Latency: ~2.5s, Tokens: 450, Confidence: 0.92
   ├─ Task: evaluate_response_with_model(model="claude")
   │  └─ Latency: ~1.8s, Tokens: 380, Confidence: 0.88
   └─ Both run in parallel (max time: 2.5s)

3. MERGING (Majority Voting)
   ├─ Votes: {gpt-4: True, claude: True}
   ├─ Consensus: True (2/2 agree)
   ├─ Agreement score: 100%
   ├─ Avg confidence: (0.92 + 0.88) / 2 = 0.90
   └─ Requires human review: False (>70% agreement, >75% confidence)

4. STORAGE
   ├─ Evaluation created with: correct=True, confidence=0.90
   └─ No escalation needed

5. AGGREGATION
   ├─ Update student comprehension score
   ├─ Update teaching effectiveness metrics
   └─ Publish to student dashboard
```

---

## Confidence & Escalation Rules

### Confidence Thresholds

| Confidence | Action |
|---|---|
| **≥0.85** | Auto-accept, use merged output |
| **0.65–0.84** | Cache result, flag for audit |
| **<0.65** | Mark for human review |

### Automatic Escalation Triggers

1. **Low Agreement**: <70% of models agree
2. **Low Confidence**: Model avg confidence <0.75
3. **Split Decision**: Tie vote (e.g., 2v2)
4. **Model Failure**: >50% of models fail
5. **Quality Issues**: Transcript quality <50%

**Escalation Workflow:**
```
Ensemble Result
    ↓
Check: confidence >= 0.75 AND agreement >= 70%?
    ├─ YES → Auto-accept, store result
    └─ NO  → Create human review task
            ├─ Flag in dashboard
                └─ Route to educator/admin
                └─ Collect human judgment
                └─ Record for model retraining
```

---

## Performance & Monitoring

### Metrics Tracked Per Model

- **Latency**: p50, p95, p99 (ms)
- **Throughput**: requests/sec
- **Error rate**: % of failed requests
- **Accuracy**: vs. consensus ground truth
- **Cost**: $ per inference token
- **Confidence**: Average reported confidence

### Optimization Strategies

**For Speed:**
- Run faster (cheaper) models in parallel with slower ones
- Cache results for identical inputs (TTL: 1 hour)
- Use lighter model for retry fallbacks

**For Accuracy:**
- Weight models by historical accuracy
- Require consensus for high-stakes tasks
- Enforce minimum agreement thresholds

**For Cost:**
- Use GPT-4-mini for 80% of requests
- Reserve GPT-4 for complex, high-stakes queries
- Local LLM fallback for non-critical tasks

---

## Implementation Checklist

- [x] Transcript validator implemented
- [x] Multi-LLM orchestrator scaffolded
- [x] Response mergers designed (TODO: semantic embedding)
- [x] Celery task orchestration designed (TODO: actual LLM API calls)
- [x] Configuration system in place
- [ ] LLM API client implementations (OpenAI, Anthropic)
- [ ] Semantic embedding service (sentence-transformers)
- [ ] Database models for storing ensemble metadata
- [ ] Human review task workflow
- [ ] Monitoring & alerting integration
- [ ] A/B testing framework for model weights
- [ ] Fine-tuning pipeline for domain adaptation

---

## Next Steps

1. **Implement LLM API clients** in `apps/integrations/llm/`
2. **Set up semantic embeddings** for intelligent merging
3. **Create database models** to store evaluation metadata
4. **Build human review dashboard** for escalated items
5. **Deploy monitoring** to track per-model performance
6. **Run production A/B tests** to optimize model weights

---

## References

- Architecture doc: [docs/architecture/multi-llm-ensemble.md](../multi-llm-ensemble.md)
- Celery docs: https://docs.celeryproject.org
- OpenAI API: https://platform.openai.com/docs/
- Anthropic Claude: https://docs.anthropic.com/
