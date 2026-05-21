"""Multi-LLM ensemble orchestrator for parallel model inference."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import asyncio
import logging

from apps.integrations.llm.ensemble import LLMEnsemble, EnsembleConfig as SharedEnsembleConfig, MergeStrategy
from apps.integrations.llm.providers import ProviderFactory

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GPT4 = "gpt-4"
    GPT4_MINI = "gpt-4-mini"
    CLAUDE = "claude-opus"
    LOCAL = "llama-2-local"


@dataclass
class LLMResponse:
    """Single LLM model response."""
    provider: LLMProvider
    content: str
    tokens_used: int
    latency_ms: int
    confidence: float = 0.5  # Model self-confidence in output
    error: Optional[str] = None
    

@dataclass
class EnsembleResult:
    """Final merged result from ensemble."""
    merged_output: str
    confidence: float
    model_responses: list[LLMResponse] = field(default_factory=list)
    merge_strategy: str = ""
    agreement_score: float = 0.0  # How much models agreed (0-1)
    requires_human_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelWeightConfig:
    """Configuration for LLM model weights and priorities."""
    
    def __init__(self):
        # Task-specific weights
        self.weights = {
            "summarization": {
                LLMProvider.GPT4: 0.40,
                LLMProvider.GPT4_MINI: 0.30,
                LLMProvider.CLAUDE: 0.20,
                LLMProvider.LOCAL: 0.10,
            },
            "question_generation": {
                LLMProvider.GPT4: 0.50,
                LLMProvider.GPT4_MINI: 0.35,
                LLMProvider.CLAUDE: 0.15,
            },
            "answer_evaluation": {
                LLMProvider.GPT4: 0.45,
                LLMProvider.CLAUDE: 0.45,
                LLMProvider.GPT4_MINI: 0.10,
            },
        }
        
        # Model priorities (order to try)
        self.priorities = {
            "summarization": [
                LLMProvider.GPT4,
                LLMProvider.GPT4_MINI,
                LLMProvider.CLAUDE,
            ],
            "question_generation": [
                LLMProvider.GPT4,
                LLMProvider.GPT4_MINI,
            ],
            "answer_evaluation": [
                LLMProvider.GPT4,
                LLMProvider.CLAUDE,
            ],
        }
        
        # Fallback models if primary fails
        self.fallback_chain = {
            LLMProvider.GPT4: LLMProvider.GPT4_MINI,
            LLMProvider.GPT4_MINI: LLMProvider.CLAUDE,
            LLMProvider.CLAUDE: LLMProvider.LOCAL,
            LLMProvider.LOCAL: None,
        }
    
    def get_weight(self, task: str, provider: LLMProvider) -> float:
        """Get weight for a model on a specific task."""
        return self.weights.get(task, {}).get(provider, 0.0)
    
    def get_priority_models(self, task: str) -> list[LLMProvider]:
        """Get prioritized model list for a task."""
        return self.priorities.get(task, [LLMProvider.GPT4])
    
    def get_fallback(self, provider: LLMProvider) -> Optional[LLMProvider]:
        """Get fallback model if primary fails."""
        return self.fallback_chain.get(provider)


class MultiLLMOrchestrator:
    """Orchestrates parallel execution across multiple LLM models."""
    
    def __init__(self, weights_config: Optional[ModelWeightConfig] = None):
        self.config = weights_config or ModelWeightConfig()
        self.logger = logger
    
    async def execute_ensemble(
        self,
        task: str,
        prompt: str,
        input_data: str,
        timeout_seconds: int = 60,
    ) -> EnsembleResult:
        """
        Execute task across ensemble of LLM models in parallel.
        
        Args:
            task: Task type (summarization, question_generation, answer_evaluation)
            prompt: System/instruction prompt
            input_data: Input data for the task
            timeout_seconds: Max time to wait for all models
        
        Returns:
            EnsembleResult with merged output and metadata
        """
        try:
            models = self.config.get_priority_models(task)
            model_ids = [model.value for model in models]
            providers = ProviderFactory.create_ensemble_providers(model_ids, api_keys={})

            shared_config = SharedEnsembleConfig(
                primary_models=model_ids,
                fallback_models=[self.config.get_fallback(models[-1]).value] if models and self.config.get_fallback(models[-1]) else [],
                merge_strategy=MergeStrategy.WEIGHTED_AVERAGE,
                timeout_per_model=float(timeout_seconds),
                use_parallelization=True,
            )
            ensemble = LLMEnsemble(config=shared_config, providers=providers)

            if task == "summarization":
                shared_result = await ensemble.process_lecture_summary(
                    cleaned_transcript=input_data,
                )
            elif task == "question_generation":
                shared_result = await ensemble.generate_assessment_questions(
                    lecture_summary=input_data,
                    num_questions=max(1, min(10, len(input_data.split()) // 40 or 5)),
                )
            elif task == "answer_evaluation":
                # For this orchestrator, `input_data` is expected to contain a compact evaluation payload.
                shared_result = await ensemble.run_ensemble(
                    system_prompt=prompt,
                    user_prompt=input_data,
                )
            else:
                shared_result = await ensemble.run_ensemble(
                    system_prompt=prompt,
                    user_prompt=input_data,
                )

            return self._convert_shared_result(shared_result)

        except Exception as exc:
            self.logger.exception(f"Ensemble execution failed for task {task}: {exc}")
            return EnsembleResult(
                merged_output="",
                confidence=0.0,
                model_responses=[],
                merge_strategy="failed",
                agreement_score=0.0,
                requires_human_review=True,
                metadata={"task": task, "error": str(exc)},
            )
    
    def _convert_shared_result(self, shared_result: Any) -> EnsembleResult:
        """Convert the shared ensemble result into the compatibility result type."""
        responses = []
        for inference in getattr(shared_result, "model_inferences", []):
            responses.append(
                LLMResponse(
                    provider=self._resolve_provider_enum(getattr(inference, "model_id", "")),
                    content=getattr(inference, "response", ""),
                    tokens_used=0,
                    latency_ms=int(getattr(inference, "processing_time_ms", 0.0)),
                    confidence=float(getattr(inference, "confidence_score", 0.0)),
                    error=getattr(inference, "error", None),
                )
            )

        return EnsembleResult(
            merged_output=getattr(shared_result, "merged_response", ""),
            confidence=float(getattr(shared_result, "confidence_score", 0.0)),
            model_responses=responses,
            merge_strategy=getattr(getattr(shared_result, "merge_strategy_used", None), "value", "weighted_average"),
            agreement_score=float(getattr(shared_result, "agreement_score", 0.0)),
            requires_human_review=(
                float(getattr(shared_result, "confidence_score", 0.0)) < 0.7
                or float(getattr(shared_result, "agreement_score", 0.0)) < 0.6
            ),
            metadata=getattr(shared_result, "details", {}),
        )

    def _resolve_provider_enum(self, model_id: str) -> LLMProvider:
        """Map shared model ids back to compatibility enums."""
        for provider in LLMProvider:
            if provider.value == model_id:
                return provider
        return LLMProvider.LOCAL
    
    async def _merge_responses(
        self,
        task: str,
        responses: list[LLMResponse],
    ) -> EnsembleResult:
        """Compatibility merge helper kept for older call sites."""
        if not responses:
            return EnsembleResult(
                merged_output="",
                confidence=0.0,
                model_responses=[],
                merge_strategy="empty",
                agreement_score=0.0,
                requires_human_review=True,
            )

        best = max(responses, key=lambda response: response.confidence)
        average_confidence = sum(response.confidence for response in responses) / len(responses)
        agreement_score = average_confidence if len(responses) > 1 else 1.0

        return EnsembleResult(
            merged_output=best.content,
            confidence=average_confidence,
            model_responses=responses,
            merge_strategy=f"compatibility_{task}",
            agreement_score=agreement_score,
            requires_human_review=average_confidence < 0.7,
            metadata={"task": task, "compatibility_mode": True},
        )
