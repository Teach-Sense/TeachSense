"""Response merging strategies for different LLM tasks."""

from dataclasses import dataclass
from typing import Any
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class MergedSummary:
    """Merged summary result."""
    text: str
    confidence: float
    agreement_level: float  # How much LLMs agreed (0-1)
    sources: list[str]  # Which models contributed


class SummaryMerger:
    """Merge summaries using semantic consensus voting."""
    
    SIMILARITY_THRESHOLD = 0.85  # Threshold for grouping similar summaries
    
    def merge(self, summaries: list[tuple[str, str]]) -> MergedSummary:
        """
        Merge multiple summaries using semantic consensus.
        
        Args:
            summaries: List of (provider_name, summary_text) tuples
        
        Returns:
            MergedSummary with merged text and confidence score
        """
        if not summaries:
            return MergedSummary(
                text="",
                confidence=0.0,
                agreement_level=0.0,
                sources=[],
            )
        
        if len(summaries) == 1:
            return MergedSummary(
                text=summaries[0][1],
                confidence=0.8,
                agreement_level=1.0,
                sources=[summaries[0][0]],
            )
        
        # TODO: Implement semantic embedding & clustering
        # For now, return first summary with lower confidence
        providers = [p for p, _ in summaries]
        return MergedSummary(
            text=summaries[0][1],
            confidence=0.6,
            agreement_level=1.0 / len(summaries),  # Low agreement with few models
            sources=providers,
        )


@dataclass
class Question:
    """Single generated question."""
    text: str
    options: list[str]  # For multiple choice
    correct_answer: str
    difficulty: str  # easy, medium, hard
    relevance_score: float  # 0-1
    quality_score: float  # 0-1


@dataclass
class MergedQuestions:
    """Merged questions result."""
    questions: list[Question]
    total_questions: int
    confidence: float
    agreement_score: float  # How much LLMs agreed on question quality


class QuestionMerger:
    """Merge questions using quality filtering + aggregation."""
    
    RELEVANCE_THRESHOLD = 0.6
    QUALITY_THRESHOLD = 0.6
    DUPLICATE_SIMILARITY = 0.9
    
    def merge(self, question_sets: list[tuple[str, list[Question]]]) -> MergedQuestions:
        """
        Merge multiple sets of questions using quality filtering.
        
        Args:
            question_sets: List of (provider_name, questions_list) tuples
        
        Returns:
            MergedQuestions with deduplicated, quality-filtered questions
        """
        if not question_sets:
            return MergedQuestions(
                questions=[],
                total_questions=0,
                confidence=0.0,
                agreement_score=0.0,
            )
        
        # Flatten all questions
        all_questions = []
        for provider, questions in question_sets:
            for q in questions:
                all_questions.append((*q, provider))
        
        # TODO: Implement deduplication via semantic matching
        # TODO: Filter by relevance and quality thresholds
        # TODO: Rank by combined score
        
        # For now, return top questions by quality
        sorted_questions = sorted(
            all_questions,
            key=lambda q: (q.quality_score, q.relevance_score),
            reverse=True,
        )[:10]
        
        agreement = len(question_sets) / max(len(question_sets), 1)
        
        return MergedQuestions(
            questions=[q for q in sorted_questions],
            total_questions=len(sorted_questions),
            confidence=0.6,
            agreement_score=agreement,
        )


@dataclass
class EvaluationResult:
    """Answer evaluation result."""
    correct: bool
    confidence: float  # 0-1
    reasoning: str
    model_name: str


@dataclass
class MergedEvaluation:
    """Merged answer evaluation result."""
    correct: bool
    confidence: float  # Final confidence
    reasoning: str  # Merged reasoning
    model_votes: dict[str, bool]  # {model_name: vote}
    agreement_score: float  # How much models agreed
    requires_human_review: bool


class EvaluationMerger:
    """Merge answer evaluations using majority voting + confidence."""
    
    MIN_AGREEMENT_FOR_AUTO_ACCEPT = 0.70  # 70% of models must agree
    
    def merge(self, evaluations: list[EvaluationResult]) -> MergedEvaluation:
        """
        Merge evaluations using majority voting.
        
        Args:
            evaluations: List of EvaluationResult from different models
        
        Returns:
            MergedEvaluation with consensus result
        """
        if not evaluations:
            return MergedEvaluation(
                correct=False,
                confidence=0.0,
                reasoning="No evaluations provided",
                model_votes={},
                agreement_score=0.0,
                requires_human_review=True,
            )
        
        if len(evaluations) == 1:
            return MergedEvaluation(
                correct=evaluations[0].correct,
                confidence=evaluations[0].confidence,
                reasoning=evaluations[0].reasoning,
                model_votes={evaluations[0].model_name: evaluations[0].correct},
                agreement_score=1.0,
                requires_human_review=evaluations[0].confidence < 0.75,
            )
        
        # Majority voting
        votes = {e.model_name: e.correct for e in evaluations}
        correct_votes = sum(1 for v in votes.values() if v)
        total_votes = len(votes)
        
        consensus = correct_votes > total_votes / 2
        agreement_score = max(correct_votes, total_votes - correct_votes) / total_votes
        
        # Merge reasoning from agreeing models
        agreeing_reasonings = [
            e.reasoning for e in evaluations
            if e.correct == consensus
        ]
        merged_reasoning = self._merge_reasonings(agreeing_reasonings)
        
        # Average confidence from agreeing models
        avg_confidence = sum(
            e.confidence for e in evaluations if e.correct == consensus
        ) / len(agreeing_reasonings) if agreeing_reasonings else 0.0
        
        # Require human review if:
        # 1. Low agreement (<70%)
        # 2. Low confidence (<0.75)
        # 3. Split decision (any tie)
        requires_review = (
            agreement_score < self.MIN_AGREEMENT_FOR_AUTO_ACCEPT
            or avg_confidence < 0.75
            or total_votes % 2 == 0 and correct_votes == total_votes / 2
        )
        
        return MergedEvaluation(
            correct=consensus,
            confidence=avg_confidence,
            reasoning=merged_reasoning,
            model_votes=votes,
            agreement_score=agreement_score,
            requires_human_review=requires_review,
        )
    
    def _merge_reasonings(self, reasonings: list[str]) -> str:
        """Merge multiple reasoning explanations."""
        if not reasonings:
            return "Multiple models evaluated but provided no reasoning."
        
        if len(reasonings) == 1:
            return reasonings[0]
        
        # Simple merge: combine unique sentences
        combined = "\n".join(reasonings)
        
        # TODO: Implement smarter merging:
        # - Remove duplicate sentences
        # - Prioritize most insightful explanations
        # - Reorder for clarity
        
        return combined
