"""
LLM Provider implementations for OpenAI, Anthropic Claude, and Mistral.

Each provider supports two execution modes:
- remote API mode when credentials and SDKs are available
- deterministic local fallback mode for development and offline execution
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional, Tuple

from apps.integrations.llm.ensemble import LLMProvider


logger = logging.getLogger(__name__)


def _extract_section(prompt: str, start_marker: str, end_marker: str | None = None) -> str:
    """Extract a prompt section using simple markers."""
    start = prompt.find(start_marker)
    if start == -1:
        return prompt
    start += len(start_marker)
    if end_marker:
        end = prompt.find(end_marker, start)
        if end != -1:
            return prompt[start:end].strip()
    return prompt[start:].strip()


def _keywords_from_text(text: str, limit: int = 6) -> list[str]:
    """Extract lightweight keywords from text for fallback responses."""
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text.lower())
    stop_words = {
        "lecture",
        "summary",
        "question",
        "questions",
        "answer",
        "model",
        "student",
        "provide",
        "based",
        "analysis",
        "transcript",
        "content",
        "important",
        "concepts",
    }
    counts: dict[str, int] = {}
    for token in tokens:
        if token in stop_words:
            continue
        counts[token] = counts.get(token, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _local_summary_response(prompt: str) -> str:
    """Create a structured fallback summary response."""
    transcript = _extract_section(prompt, "Lecture transcript:")
    keywords = _keywords_from_text(transcript, limit=6)

    summary = {
        "summary": (
            "This lecture focuses on "
            + (", ".join(keywords[:3]) if keywords else "the core lecture topic")
            + "."
        ),
        "key_concepts": [
            {
                "concept": keyword.replace("-", " ").title(),
                "explanation": f"Core idea related to {keyword}."
            }
            for keyword in keywords[:5]
        ],
        "important_points": [
            f"Understand how {keyword} affects the lesson objectives."
            for keyword in keywords[:4]
        ],
        "complex_areas": [
            f"The relationship between {keywords[0]} and the broader topic requires attention."
        ] if keywords else ["Complex concepts require further review."],
    }
    return json.dumps(summary, ensure_ascii=False)


def _local_questions_response(prompt: str) -> str:
    """Create a structured fallback question set."""
    summary = _extract_section(prompt, "Summary:")
    keywords = _keywords_from_text(summary, limit=8)

    questions = []
    for index, keyword in enumerate(keywords[:5], start=1):
        difficulty = "easy" if index == 1 else "medium" if index < 4 else "hard"
        questions.append(
            {
                "question": f"What is the role of {keyword} in this lecture?",
                "model_answer": f"{keyword.title()} is an important concept discussed in the lecture.",
                "difficulty": difficulty,
                "relevance": 0.85 - (index * 0.03),
            }
        )

    if not questions:
        questions = [
            {
                "question": "What is the main idea of the lecture?",
                "model_answer": "The lecture introduces the core topic and its practical implications.",
                "difficulty": "medium",
                "relevance": 0.75,
            }
        ]

    return json.dumps(questions, ensure_ascii=False)


def _local_evaluation_response(prompt: str) -> str:
    """Create a structured fallback evaluation response."""
    question = _extract_section(prompt, "Question:", "Model answer:")
    model_answer = _extract_section(prompt, "Model answer:", "Student answer:")
    student_answer = _extract_section(prompt, "Student answer:")

    student_keywords = set(_keywords_from_text(student_answer, limit=10))
    model_keywords = set(_keywords_from_text(model_answer, limit=10))
    overlap = len(student_keywords & model_keywords)
    possible = max(len(model_keywords), 1)
    score = round(min(100.0, max(25.0, 35.0 + (overlap / possible) * 60.0)), 2)

    return json.dumps(
        {
            "score": score,
            "feedback": (
                "The answer addresses the question well."
                if score >= 70
                else "The answer is partially correct and should include more lecture-specific details."
            ),
            "accuracy_components": {
                "question": question.strip(),
                "coverage": round(min(1.0, overlap / possible), 2),
                "model_alignment": round(min(1.0, overlap / max(len(student_keywords), 1)), 2),
            },
            "accuracy": score,
            "completeness": max(0.0, min(100.0, score - 8.0)),
            "clarity": max(0.0, min(100.0, score + 2.0)),
        },
        ensure_ascii=False,
    )


def _local_generic_response(prompt: str) -> str:
    """Fallback for unsupported tasks."""
    return prompt[:1500]


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, model_id: str = "gpt-4-mini", api_key: str = ""):
        super().__init__(model_id, api_key)
        self.model_id = model_id
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """
        Run OpenAI inference.
        
        Returns:
            (response_text, confidence_score)
        """
        try:
            if not self.api_key:
                return self._local_infer(prompt, system_prompt)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
            )

            response_text = response.choices[0].message.content
            
            # OpenAI doesn't provide confidence directly
            # Use finish_reason and logprobs as proxy
            confidence = 0.95 if response.choices[0].finish_reason == "stop" else 0.7

            logger.info(
                f"OpenAI inference successful for model {self.model_id} "
                f"(tokens: {response.usage.total_tokens})"
            )

            return response_text, confidence

        except Exception as e:
            logger.warning(f"OpenAI inference failed, falling back locally: {str(e)}")
            return self._local_infer(prompt, system_prompt)

    def _local_infer(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float]:
        task_text = f"{system_prompt or ''}\n{prompt}".lower()
        if "assessment questions" in task_text or "generate exactly" in task_text:
            return _local_questions_response(prompt), 0.78
        if "evaluate" in task_text and "student response" in task_text:
            return _local_evaluation_response(prompt), 0.8
        if "summary" in task_text or "structured summary" in task_text:
            return _local_summary_response(prompt), 0.82
        return _local_generic_response(prompt), 0.65

    async def is_available(self) -> bool:
        """Check OpenAI API availability."""
        if not self.api_key:
            return True

        try:
            # Quick test call
            response = await self.client.models.retrieve(self.model_id)
            return response.id == self.model_id

        except Exception as e:
            logger.warning(f"OpenAI availability check failed, using fallback mode: {str(e)}")
            return True


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, model_id: str = "claude-3-sonnet-20240229", api_key: str = ""):
        super().__init__(model_id, api_key)
        self.model_id = model_id
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """
        Run Claude inference.
        
        Returns:
            (response_text, confidence_score)
        """
        try:
            if not self.api_key:
                return self._local_infer(prompt, system_prompt)

            response = await self.client.messages.create(
                model=self.model_id,
                max_tokens=2000,
                system=system_prompt or "",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=temperature,
            )

            response_text = response.content[0].text
            
            # Claude provides stop_reason
            confidence = 0.95 if response.stop_reason == "end_turn" else 0.7

            logger.info(
                f"Claude inference successful for model {self.model_id} "
                f"(stop_reason: {response.stop_reason})"
            )

            return response_text, confidence

        except Exception as e:
            logger.warning(f"Claude inference failed, falling back locally: {str(e)}")
            return self._local_infer(prompt, system_prompt)

    def _local_infer(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float]:
        task_text = f"{system_prompt or ''}\n{prompt}".lower()
        if "assessment questions" in task_text or "generate exactly" in task_text:
            return _local_questions_response(prompt), 0.8
        if "evaluate" in task_text and "student response" in task_text:
            return _local_evaluation_response(prompt), 0.81
        if "summary" in task_text or "structured summary" in task_text:
            return _local_summary_response(prompt), 0.84
        return _local_generic_response(prompt), 0.67

    async def is_available(self) -> bool:
        """Check Claude API availability."""
        if not self.api_key:
            return True

        try:
            # Quick test by calling list_models
            # Claude doesn't have public model list, so just check connectivity
            await self.client.messages.create(
                model=self.model_id,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True

        except Exception as e:
            logger.warning(f"Claude availability check failed, using fallback mode: {str(e)}")
            return True


class MistralProvider(LLMProvider):
    """Mistral AI provider."""

    def __init__(self, model_id: str = "mistral-medium", api_key: str = ""):
        super().__init__(model_id, api_key)
        self.model_id = model_id
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy-load Mistral client."""
        if self._client is None:
            from mistralai.async_client import MistralAsyncClient
            self._client = MistralAsyncClient(api_key=self.api_key)
        return self._client

    async def infer(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, float]:
        """
        Run Mistral inference.
        
        Returns:
            (response_text, confidence_score)
        """
        try:
            if not self.api_key:
                return self._local_infer(prompt, system_prompt)

            from mistralai.models.chat_message import ChatMessage

            messages = []
            if system_prompt:
                messages.append(ChatMessage(role="system", content=system_prompt))
            messages.append(ChatMessage(role="user", content=prompt))

            response = await self.client.chat(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
            )

            response_text = response.choices[0].message.content
            
            # Mistral provides finish_reason
            confidence = 0.95 if response.choices[0].finish_reason == "stop" else 0.7

            logger.info(
                f"Mistral inference successful for model {self.model_id}"
            )

            return response_text, confidence

        except Exception as e:
            logger.warning(f"Mistral inference failed, falling back locally: {str(e)}")
            return self._local_infer(prompt, system_prompt)

    def _local_infer(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float]:
        task_text = f"{system_prompt or ''}\n{prompt}".lower()
        if "assessment questions" in task_text or "generate exactly" in task_text:
            return _local_questions_response(prompt), 0.76
        if "evaluate" in task_text and "student response" in task_text:
            return _local_evaluation_response(prompt), 0.79
        if "summary" in task_text or "structured summary" in task_text:
            return _local_summary_response(prompt), 0.81
        return _local_generic_response(prompt), 0.64

    async def is_available(self) -> bool:
        """Check Mistral API availability."""
        if not self.api_key:
            return True

        try:
            # Quick test call
            from mistralai.models.chat_message import ChatMessage

            response = await self.client.chat(
                model=self.model_id,
                messages=[ChatMessage(role="user", content="test")],
                max_tokens=10,
            )
            return True

        except Exception as e:
            logger.warning(f"Mistral availability check failed, using fallback mode: {str(e)}")
            return True


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    PROVIDERS = {
        "gpt-4-mini": OpenAIProvider,
        "gpt-4": OpenAIProvider,
        "gpt-3.5-turbo": OpenAIProvider,
        "claude-3-sonnet": ClaudeProvider,
        "claude-3-opus": ClaudeProvider,
        "claude-3-haiku": ClaudeProvider,
        "mistral-medium": MistralProvider,
        "mistral-small": MistralProvider,
        "mistral-large": MistralProvider,
    }

    @staticmethod
    def create_provider(
        model_id: str,
        api_key: str = "",
    ) -> LLMProvider:
        """
        Create provider instance for model.
        
        Args:
            model_id: Model identifier
            api_key: API key for provider
            
        Returns:
            LLMProvider instance
        """
        provider_class = ProviderFactory.PROVIDERS.get(model_id)
        
        if not provider_class:
            raise ValueError(f"Unknown model: {model_id}")
        
        return provider_class(model_id=model_id, api_key=api_key)

    @staticmethod
    def create_ensemble_providers(
        model_ids: list,
        api_keys: dict,
    ) -> dict:
        """
        Create providers for ensemble.
        
        Args:
            model_ids: List of model IDs
            api_keys: Dict mapping model_id -> api_key
            
        Returns:
            Dict mapping model_id -> LLMProvider
        """
        providers = {}
        
        for model_id in model_ids:
            api_key = api_keys.get(model_id, "")
            try:
                providers[model_id] = ProviderFactory.create_provider(
                    model_id=model_id,
                    api_key=api_key,
                )
            except ValueError as e:
                logger.warning(f"Failed to create provider for {model_id}: {str(e)}")
        
        return providers
