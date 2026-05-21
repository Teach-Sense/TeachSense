# Multi-LLM Ensemble & Data Processing Architecture

## Overview
TeachSense uses a **hybrid ensemble approach** combining data validation, multi-LLM inference, and intelligent response merging to maximize accuracy in:
- Lecture summarization
- Question generation
- Answer evaluation
- Teaching effectiveness scoring

## 1. Pre-Processing Pipeline

### Data Validation Stage
```
Raw Transcript → Cleaning → Chunking → Quality Check → Vetted Data
```

**Responsibilities:**
- Remove artifacts (filler words, stutters, silence markers)
- Chunk long transcripts into semantic units
- Validate input format and length constraints
- Language detection & consistency checks
- Noise filtering (audio quality scores from STT provider)

**Location:** `apps/transcripts/services/transcript_validator.py`

---

## 2. Multi-LLM Ensemble Strategy

### Model Pool
- **Primary:** GPT-4 (best quality, slower)
- **Secondary:** GPT-4-mini (fast, cost-efficient)
- **Tertiary:** Claude (alternative semantic understanding)
- **Fallback:** Local open-source model (if API fails)

### Parallel Execution
All LLMs run in parallel via Celery tasks; results merged asynchronously.

```
Validated Transcript
    ↓
[LLM-1: GPT-4]  [LLM-2: GPT-4-mini]  [LLM-3: Claude]  [LLM-4: Local]
    ↓                ↓                    ↓                ↓
Response-1       Response-2          Response-3       Response-4
    ↓_________________↓__________________↓________________↓
           Merger Engine (consensus + voting)
                     ↓
            Final Merged Output
```

---

## 3. Response Merging Strategies

### A. For Summarization (Text Output)
**Algorithm:** Semantic Consensus Voting
1. Embed all summaries via sentence-transformer
2. Compute cosine similarity matrix
3. Group highly similar summaries (>0.85 threshold)
4. Select summary from largest group as "consensus"
5. Enrich with unique high-quality points from other summaries
6. Confidence score = (agreement level) × (model weight)

### B. For Question Generation (Structured JSON)
**Algorithm:** Quality Filtering + Aggregation
1. Each LLM generates `n` questions with scores
2. Filter by relevance (TF-IDF + semantic relevance to transcript)
3. Deduplicate questions using semantic matching
4. Rank by: (quality_score × model_weight + diversity_bonus)
5. Merge from top-k across models
6. Confidence = (model_agreement % + relevance score) / 2

### C. For Answer Evaluation (Boolean + Reasoning)
**Algorithm:** Majority Voting + Confidence Thresholding
1. Each LLM evaluates: `correct: boolean`, `confidence: 0-100`, `reasoning: str`
2. **Voting rule:**
   - If 3+ models agree (±1 point margin): Use majority + highest confidence reasoning
   - If models disagree: Flag for human review; output: "uncertain"
3. Confidence threshold: Accept if ≥ 70% model consensus + avg confidence ≥ 0.75
4. Output: `{correct, confidence, merged_reasoning, model_votes}`

---

## 4. Implementation Details

### Celery Task Orchestration
```python
@celery_app.task
async def ensemble_summarize(transcript_id):
    """Run summarization across all LLM models in parallel."""
    validated_transcript = fetch_transcript(transcript_id)
    
    tasks = [
        summarize_with_gpt4.delay(validated_transcript),
        summarize_with_gpt4_mini.delay(validated_transcript),
        summarize_with_claude.delay(validated_transcript),
    ]
    
    responses = await gather_results(tasks)
    merged_summary = merge_summaries(responses)
    store_result(transcript_id, merged_summary)
```

### Model Weights
Configure per-model reliability weights based on:
- Historical accuracy (track error rates per task)
- Cost vs quality trade-off
- Latency SLAs

Example:
```python
MODEL_WEIGHTS = {
    "gpt-4": 0.40,          # Most accurate
    "gpt-4-mini": 0.30,     # Good speed/quality
    "claude-opus": 0.20,    # Alternative perspective
    "local-llama": 0.10,    # Fallback
}
```

---

## 5. Confidence & Fallback Rules

### Confidence Scoring
- **High (≥0.85):** Use merged output directly
- **Medium (0.65-0.84):** Add human review flag; cache for QA
- **Low (<0.65):** Flag for human review; retry with different model set

### Fallback Strategy
1. If LLM fails: Retry with lighter weight model
2. If >1 fail: Use ensemble from remaining models
3. If >50% fail: Escalate to manual processing

---

## 6. Per-Task Configuration

### Summarization
- Merge strategy: Semantic consensus voting
- Model pool: [GPT-4, GPT-4-mini, Claude]
- Min consensus: 2/3 models
- Timeout: 30s per model

### Question Generation
- Merge strategy: Quality filtering + aggregation
- Model pool: [GPT-4, GPT-4-mini]
- Questions to merge: Top 10 per model
- Timeout: 45s per model

### Answer Evaluation
- Merge strategy: Majority voting
- Model pool: [GPT-4, Claude]
- Min agreement: 2/2 models
- Timeout: 15s per model

---

## 7. Monitoring & Metrics

Track per-LLM:
- Inference latency (p50, p95, p99)
- Error rates
- Confidence distribution
- Merge disagreement rates (flag for retraining)

Dashboard metrics:
- Ensemble speed vs accuracy trade-off curve
- Cost per task (weighted by model usage)
- Human review escalation rate

---

## 8. Future Enhancements

1. **Active Learning:** Train classifier to predict when ensemble should escalate to humans
2. **Model Adaptation:** Dynamically adjust weights based on live accuracy feedback
3. **Domain-Specific Models:** Fine-tune models on TeachSense lecture domain
4. **Multi-Modal:** Extend to video frames + audio for richer context
