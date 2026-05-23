"""
Multi-LLM Ensemble system for accurate lecture processing.
Runs inference on multiple LLM models in parallel and merges responses using consensus/voting.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging


logger = logging.getLogger(__name__)


class MergeStrategy(Enum):
    """Response merging approaches for ensemble."""
    CONSENSUS = "consensus"  # All models must agree
    MAJORITY_VOTE = "majority_vote"  # 50%+ agreement required
    WEIGHTED_AVERAGE = "weighted_average"  # Weighted by model confidence
    HIGHEST_CONFIDENCE = "highest_confidence"  # Take highest-confidence response


@dataclass
class EnsembleConfig:
    """Configuration for LLM ensemble."""
    # Models to include in ensemble
    primary_models: List[str] = field(
        default_factory=lambda: ["claude-3-sonnet", "mistral-medium"]
    )
    fallback_models: List[str] = field(
        default_factory=lambda: ["mistral-small"]
    )
    # Merging strategy
    merge_strategy: MergeStrategy = MergeStrategy.WEIGHTED_AVERAGE
    # Required agreement level for final response (0-100%)
    required_agreement: float = 0.70
    # Parallelize requests
    use_parallelization: bool = True
    # Timeout per model (seconds)
    timeout_per_model: float = 30.0
    # Retry failed requests
    max_retries: int = 2


@dataclass
class ModelInference:
    """Single model's inference result."""
    model_id: str
    response: str
    confidence_score: float  # 0-1
    processing_time_ms: float
    error: Optional[str] = None
    was_fallback: bool = False


@dataclass
class EnsembleResult:
    """Final merged result from ensemble."""
    merged_response: str
    agreement_score: float  # 0-1, how well models agreed
    confidence_score: float  # 0-1, overall confidence
    model_inferences: List[ModelInference] = field(default_factory=list)
    merge_strategy_used: MergeStrategy = MergeStrategy.WEIGHTED_AVERAGE
    processing_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    def __init__(self, model_id: str, api_key: str = ""):
        self.model_id = model_id
        self.api_key = api_key

    @abstractmethod
    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """
        Run inference and return response + confidence score.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: LLM temperature (0-1)
            
        Returns:
            (response_text, confidence_score)
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI/ChatGPT LLM provider."""

    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """Run OpenAI inference."""
        # TODO: Implement OpenAI API call
        # This will use OpenAI client from config
        pass

    async def is_available(self) -> bool:
        """Check OpenAI API availability."""
        # TODO: Implement availability check
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """Run Claude inference."""
        # TODO: Implement Claude API call
        pass

    async def is_available(self) -> bool:
        """Check Claude API availability."""
        # TODO: Implement availability check
        pass


class MistralProvider(LLMProvider):
    """Mistral LLM provider."""

    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """Run Mistral inference."""
        # TODO: Implement Mistral API call
        pass

    async def is_available(self) -> bool:
        """Check Mistral API availability."""
        # TODO: Implement availability check
        pass


class LLMEnsemble:
    """
    Multi-LLM ensemble for accurate text processing.
    Runs models in parallel, computes agreement, and merges responses.
    """

    def __init__(self, config: EnsembleConfig, providers: Optional[Dict[str, LLMProvider]] = None):
        """
        Initialize ensemble.
        
        Args:
            config: Ensemble configuration
            providers: Dict mapping model_id -> LLMProvider instance
        """
        self.config = config
        self.providers = providers or self._build_default_providers()
        self.logger = logging.getLogger(__name__)

    def _build_default_providers(self) -> Dict[str, LLMProvider]:
        """Build default providers using the shared provider factory."""
        from apps.integrations.llm.providers import ProviderFactory

        model_ids = list(dict.fromkeys(self.config.primary_models + self.config.fallback_models))
        return ProviderFactory.create_ensemble_providers(model_ids=model_ids, api_keys={})

    async def process_lecture_summary(
        self,
        cleaned_transcript: str,
        num_questions: int = 5,
    ) -> EnsembleResult:
        """
        Generate lecture summary using LLM ensemble.
        
        Args:
            cleaned_transcript: Preprocessed lecture transcript
            num_questions: Target question count
            
        Returns:
            EnsembleResult with merged response
        """
        system_prompt = self._get_summary_system_prompt()
        user_prompt = self._get_summary_user_prompt(cleaned_transcript, num_questions)

        return await self.run_ensemble(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    async def generate_assessment_questions(
        self,
        lecture_summary: str,
        num_questions: int = 5,
    ) -> EnsembleResult:
        """
        Generate assessment questions using LLM ensemble.
        
        Args:
            lecture_summary: Summarized lecture
            num_questions: Number of questions to generate
            
        Returns:
            EnsembleResult with merged questions
        """
        system_prompt = self._get_question_system_prompt()
        user_prompt = self._get_question_user_prompt(lecture_summary, num_questions)

        return await self.run_ensemble(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    async def evaluate_student_response(
        self,
        question: str,
        student_answer: str,
        model_answer: str,
    ) -> EnsembleResult:
        """
        Evaluate student response using LLM ensemble.
        
        Args:
            question: Assessment question
            student_answer: Student's verbal answer
            model_answer: Expected/model answer
            
        Returns:
            EnsembleResult with evaluation and score
        """
        system_prompt = self._get_evaluation_system_prompt()
        user_prompt = self._get_evaluation_user_prompt(
            question, student_answer, model_answer
        )

        return await self.run_ensemble(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    async def run_ensemble(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> EnsembleResult:
        """
        Run ensemble inference across all models.
        
        Args:
            system_prompt: System instruction
            user_prompt: User prompt
            temperature: LLM temperature
            
        Returns:
            EnsembleResult with merged response
        """
        import time
        start_time = time.time()

        # Get available models
        available_models = await self._get_available_models()

        if not available_models:
            raise RuntimeError("No LLM providers available")

        # Run parallel inference
        inferences = await self._run_parallel_inference(
            available_models,
            system_prompt,
            user_prompt,
            temperature,
        )

        # Merge responses
        merged_response, agreement_score, confidence_score = self._merge_responses(
            inferences,
            self.config.merge_strategy,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return EnsembleResult(
            merged_response=merged_response,
            agreement_score=agreement_score,
            confidence_score=confidence_score,
            model_inferences=inferences,
            merge_strategy_used=self.config.merge_strategy,
            processing_time_ms=processing_time_ms,
            details={
                "strategy": self.config.merge_strategy.value,
                "required_agreement": self.config.required_agreement,
                "models_used": [inf.model_id for inf in inferences],
            },
        )

    async def _get_available_models(self) -> List[str]:
        """Get list of available models."""
        available = []
        for model_id in self.config.primary_models:
            if model_id in self.providers:
                provider = self.providers[model_id]
                if await provider.is_available():
                    available.append(model_id)

        # Fall back to secondary models if needed
        if not available:
            for model_id in self.config.fallback_models:
                if model_id in self.providers:
                    provider = self.providers[model_id]
                    if await provider.is_available():
                        available.append(model_id)

        return available

    async def _run_parallel_inference(
        self,
        model_ids: List[str],
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> List[ModelInference]:
        """Run inference in parallel across all models."""
        import time

        tasks = []
        for model_id in model_ids:
            provider = self.providers[model_id]
            tasks.append(
                self._infer_with_timeout(
                    provider, system_prompt, user_prompt, temperature
                )
            )

        inferences = []
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for model_id, result in zip(model_ids, results):
            if isinstance(result, Exception):
                inferences.append(
                    ModelInference(
                        model_id=model_id,
                        response="",
                        confidence_score=0.0,
                        processing_time_ms=0.0,
                        error=str(result),
                    )
                )
            else:
                response, confidence = result
                inferences.append(
                    ModelInference(
                        model_id=model_id,
                        response=response,
                        confidence_score=confidence,
                        processing_time_ms=0.0,
                    )
                )

        return inferences

    async def _infer_with_timeout(
        self,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> Tuple[str, float]:
        """Run inference with timeout."""
        try:
            response, confidence = await asyncio.wait_for(
                provider.infer(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                ),
                timeout=self.config.timeout_per_model,
            )
            return response, confidence
        except asyncio.TimeoutError:
            raise TimeoutError(f"Model {provider.model_id} timed out")

    def _merge_responses(
        self,
        inferences: List[ModelInference],
        strategy: MergeStrategy,
    ) -> Tuple[str, float, float]:
        """
        Merge responses from multiple models.
        
        Returns:
            (merged_response, agreement_score, confidence_score)
        """
        # Filter out failed inferences
        valid_inferences = [inf for inf in inferences if inf.response and not inf.error]

        if not valid_inferences:
            return "", 0.0, 0.0

        if strategy == MergeStrategy.HIGHEST_CONFIDENCE:
            return self._merge_highest_confidence(valid_inferences)
        elif strategy == MergeStrategy.WEIGHTED_AVERAGE:
            return self._merge_weighted_average(valid_inferences)
        elif strategy == MergeStrategy.MAJORITY_VOTE:
            return self._merge_majority_vote(valid_inferences)
        elif strategy == MergeStrategy.CONSENSUS:
            return self._merge_consensus(valid_inferences)
        else:
            return self._merge_weighted_average(valid_inferences)

    def _merge_highest_confidence(
        self,
        inferences: List[ModelInference],
    ) -> Tuple[str, float, float]:
        """Take response from highest-confidence model."""
        best = max(inferences, key=lambda x: x.confidence_score)

        # Agreement is 1/num_models if it's the only good one
        agreement_score = 1.0 / len(inferences) * best.confidence_score

        return best.response, agreement_score, best.confidence_score

    def _merge_weighted_average(
        self,
        inferences: List[ModelInference],
    ) -> Tuple[str, float, float]:
        """Weight responses by model confidence."""
        # For text, use highest-confidence response weighted by others' confidence
        best_inference = max(inferences, key=lambda x: x.confidence_score)

        # Calculate agreement as average confidence across models
        avg_confidence = sum(inf.confidence_score for inf in inferences) / len(inferences)

        # Agreement score: how similar are confidences?
        confidence_variance = sum(
            (inf.confidence_score - avg_confidence) ** 2 for inf in inferences
        ) / len(inferences)
        agreement_score = max(0.0, 1.0 - (confidence_variance * 2))

        return best_inference.response, agreement_score, avg_confidence

    def _merge_majority_vote(
        self,
        inferences: List[ModelInference],
    ) -> Tuple[str, float, float]:
        """Take response with majority agreement."""
        # TODO: Implement similarity-based majority voting
        # For now, similar to weighted average
        return self._merge_weighted_average(inferences)

    def _merge_consensus(
        self,
        inferences: List[ModelInference],
    ) -> Tuple[str, float, float]:
        """All models must have high confidence for consensus."""
        min_confidence = min(inf.confidence_score for inf in inferences)

        if min_confidence < self.config.required_agreement:
            # Below threshold, return best attempt with low confidence
            best = max(inferences, key=lambda x: x.confidence_score)
            return best.response, min_confidence, min_confidence

        # All models agree above threshold
        best = max(inferences, key=lambda x: x.confidence_score)
        return best.response, min_confidence, min(min_confidence, best.confidence_score)

    def _get_summary_system_prompt(self) -> str:
        """System prompt for lecture summarization."""
        return """You are an expert educational content analyst. 
        Your task is to create structured, accurate summaries of lecture content 
        that help students understand key concepts and important points. 
        Focus on clarity, accuracy, and pedagogical value."""

    def _get_summary_user_prompt(self, transcript: str, num_questions: int) -> str:
        """User prompt for lecture summarization."""
        return f"""Analyze this lecture transcript and provide:
        1. A structured summary of main topics
        2. List of 5-10 key concepts with brief explanations
        3. Most important points students should remember
        4. Any areas of complexity that need careful attention
        
        Format as JSON with keys: summary, key_concepts, important_points, complex_areas
        
        Lecture transcript:
        {transcript[:5000]}"""  # Limit to 5000 chars for context window

    def _get_question_system_prompt(self) -> str:
        """System prompt for question generation."""
        return """You are an expert educational assessment designer.
        Create clear, unambiguous assessment questions that test understanding 
        of lecture content at appropriate cognitive levels."""

    def _get_question_user_prompt(self, summary: str, num_questions: int) -> str:
        """User prompt for question generation."""
        return f"""Based on this lecture summary, generate exactly {num_questions} 
        assessment questions. For each question, provide:
        - The question text (clear and specific)
        - Expected/model answer
        - Difficulty level (easy/medium/hard)
        
        Format as JSON array with objects containing: question, model_answer, difficulty
        
        Summary:
        {summary[:3000]}"""

    def _get_evaluation_system_prompt(self) -> str:
        """System prompt for student response evaluation."""
        return """You are an expert educator evaluating student responses.
        Compare student answers to model answers, scoring for:
        1. Accuracy of core concepts
        2. Completeness of explanation
        3. Clarity of expression
        
        Be fair but rigorous."""

    def _get_evaluation_user_prompt(
        self, question: str, student_answer: str, model_answer: str
    ) -> str:
        """User prompt for student evaluation."""
        return f"""Evaluate this student response:
        
        Question: {question}
        
        Model answer: {model_answer}
        
        Student answer: {student_answer}
        
        Provide JSON with: score (0-100), feedback, accuracy_components
        """
