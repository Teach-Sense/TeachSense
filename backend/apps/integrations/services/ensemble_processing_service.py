"""Integration layer for ensemble system into Django application."""

from typing import Optional
import logging

from apps.integrations.ensemble_config import EnsembleConfig
from apps.transcripts.services.transcript_validator import TranscriptValidator
from infrastructure.integrations.multi_llm_orchestrator import MultiLLMOrchestrator
from apps.integrations.services.response_mergers import (
    SummaryMerger,
    QuestionMerger,
    EvaluationMerger,
)

logger = logging.getLogger(__name__)


class EnsembleProcessingService:
    """
    High-level service for using the ensemble system.
    
    This is the main integration point for application code.
    """
    
    def __init__(self):
        self.config = EnsembleConfig()
        self.validator = TranscriptValidator()
        self.orchestrator = MultiLLMOrchestrator()
        self.summary_merger = SummaryMerger()
        self.question_merger = QuestionMerger()
        self.evaluation_merger = EvaluationMerger()
    
    def process_lecture_transcript(
        self,
        session_id: str,
        raw_transcript: str,
    ) -> Optional[dict]:
        """
        End-to-end processing of lecture transcript.
        
        Flow:
        1. Validate transcription quality
        2. Clean and prepare data
        3. Trigger parallel LLM tasks via Celery
        
        Args:
            session_id: Lecture session ID
            raw_transcript: Raw audio transcription output
        
        Returns:
            Dict with {session_id, validated, quality_score, job_id}
            or None if validation fails
        """
        # Step 1: Validate transcript
        validation_result = self.validator.validate(raw_transcript)
        
        if not validation_result.is_valid:
            logger.warning(
                f"Transcript validation failed for session {session_id}: "
                f"{validation_result.issues}"
            )
            return {
                "session_id": session_id,
                "validated": False,
                "quality_score": validation_result.quality_score,
                "issues": validation_result.issues,
            }
        
        logger.info(
            f"Transcript validated for session {session_id}, "
            f"quality: {validation_result.quality_score:.2f}"
        )
        
        # Step 2: Trigger ensemble processing via Celery
        from apps.integrations.tasks.ensemble_tasks import EnsembleTaskOrchestrator
        
        orchestrator = EnsembleTaskOrchestrator()
        
        # This returns immediately; processing happens asynchronously
        orchestrator.create_summarization_job(session_id, transcript_id="auto")
        
        return {
            "session_id": session_id,
            "validated": True,
            "quality_score": validation_result.quality_score,
            "estimated_duration_seconds": validation_result.estimated_duration_seconds,
        }
    
    def get_task_config(self, task: str) -> dict:
        """Get configuration for a specific task."""
        config = EnsembleConfig.for_task(task)
        return {
            "timeout": config.timeout,
            "confidence_threshold": config.confidence_threshold,
            "max_models": config.max_models,
            "require_consensus": config.require_consensus,
        }


# Singleton instance
_ensemble_service: Optional[EnsembleProcessingService] = None


def get_ensemble_service() -> EnsembleProcessingService:
    """Get or create singleton ensemble service."""
    global _ensemble_service
    if _ensemble_service is None:
        _ensemble_service = EnsembleProcessingService()
    return _ensemble_service


# ============ Usage Examples ============

def example_transcript_processing():
    """Example: Process a lecture transcript."""
    service = get_ensemble_service()
    
    raw_transcript = """
    Um, okay, so today we're gonna talk about photosynthesis, you know?
    So like, photosynthesis is this, uh, process where plants convert light energy
    into chemical energy, kind of like a solar panel but, uh, biological, you know?
    """
    
    result = service.process_lecture_transcript(
        session_id="sess_001",
        raw_transcript=raw_transcript,
    )
    
    if result["validated"]:
        print(f"✓ Transcript validated (quality: {result['quality_score']:.2%})")
        print(f"  Processing triggered asynchronously...")
    else:
        print(f"✗ Validation failed: {result['issues']}")


def example_custom_merging():
    """Example: Custom merging of LLM responses."""
    from apps.integrations.services.response_mergers import (
        EvaluationResult,
        EvaluationMerger,
    )
    
    # Simulated responses from two models
    evaluations = [
        EvaluationResult(
            correct=True,
            confidence=0.92,
            reasoning="The student correctly identified the key concept...",
            model_name="gpt-4",
        ),
        EvaluationResult(
            correct=True,
            confidence=0.85,
            reasoning="Accurate response; demonstrates understanding...",
            model_name="claude",
        ),
    ]
    
    merger = EvaluationMerger()
    merged = merger.merge(evaluations)
    
    print(f"Consensus: {'CORRECT' if merged.correct else 'INCORRECT'}")
    print(f"Confidence: {merged.confidence:.2%}")
    print(f"Agreement: {merged.agreement_score:.2%}")
    print(f"Reasoning: {merged.reasoning}")
    print(f"Human review needed: {merged.requires_human_review}")


def example_task_retry_with_fallback():
    """Example: Automatic retry with fallback models."""
    from infrastructure.integrations.multi_llm_orchestrator import (
        MultiLLMOrchestrator,
        LLMProvider,
    )
    
    orchestrator = MultiLLMOrchestrator()
    config = orchestrator.config
    
    # If GPT-4 fails, try GPT-4-mini
    fallback = config.get_fallback(LLMProvider.GPT4)
    print(f"Fallback for GPT-4: {fallback}")  # gpt-4-mini
    
    # Get model weights
    weight = config.get_weight("answer_evaluation", LLMProvider.GPT4)
    print(f"Weight for GPT-4 on answer_evaluation: {weight}")  # 0.45


def example_ensemble_execution_flow():
    """Example: Full ensemble execution flow."""
    import asyncio
    from infrastructure.integrations.multi_llm_orchestrator import (
        MultiLLMOrchestrator,
    )
    
    orchestrator = MultiLLMOrchestrator()
    
    # Run ensemble
    result = asyncio.run(
        orchestrator.execute_ensemble(
            task="answer_evaluation",
            prompt="Grade this student answer: {answer}\nCorrect answer: {expected}",
            input_data="...",
            timeout_seconds=30,
        )
    )
    
    print(f"Merged output: {result.merged_output}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Agreement: {result.agreement_score:.2%}")
    print(f"Requires review: {result.requires_human_review}")


def example_configuration_access():
    """Example: Access ensemble configuration."""
    from apps.integrations.ensemble_config import EnsembleConfig
    
    # Global config
    config = EnsembleConfig()
    print(f"Summary confidence threshold: {config.SUMMARY_CONFIDENCE_THRESHOLD}")
    
    # Task-specific config
    task_config = EnsembleConfig.for_task("question_generation")
    print(f"\nQuestion generation config:")
    print(f"  Timeout: {task_config.timeout}s")
    print(f"  Confidence threshold: {task_config.confidence_threshold}")
    print(f"  Max models: {task_config.max_models}")
    print(f"  Require consensus: {task_config.require_consensus}")


if __name__ == "__main__":
    print("=== TeachSense Multi-LLM Ensemble System ===\n")
    
    print("1. Transcript Processing:")
    example_transcript_processing()
    
    print("\n2. Custom Merging:")
    example_custom_merging()
    
    print("\n3. Task Retry with Fallback:")
    example_task_retry_with_fallback()
    
    print("\n4. Configuration Access:")
    example_configuration_access()
